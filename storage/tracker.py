
import json
from pathlib import Path

from storage.export import write_csv


class ChangeTracker:
    def __init__(self, output_dir: str = "output"):
        self.changes_dir = Path(output_dir) / "changes"
        self.changes_file = self.changes_dir / "changes.json"
        self.pending_file = self.changes_dir / "pending.json"
        self.csv_file = self.changes_dir / "changes.csv"

        self.changes_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def normalize(value):
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )

    @classmethod
    def states_equal(cls, first, second):
        return cls.normalize(first) == cls.normalize(second)

    @staticmethod
    def get_url(record):
        listing = record.get("listing")
        if not isinstance(listing, dict):
            return ""
        return str(listing.get("url") or "").strip()

    @staticmethod
    def make_key(url, category, field, item_key=None):
        return json.dumps(
            [url, category, field, item_key],
            ensure_ascii=False,
            separators=(",", ":"),
        )

    @staticmethod
    def get_curriculum_key(item, index):
        order = item.get("order")
        return str(order) if order is not None else f"index-{index}"

    def collect_fields(self, record, include_detail=True):
        """Mengubah data record menjadi kumpulan field untuk dibandingkan."""
        result = {}

        url = self.get_url(record)
        listing = record.get("listing")
        if not isinstance(listing, dict):
            listing = {}

        def add_fields(category, data, item_key=None):
            if not isinstance(data, dict):
                return

            for field, value in data.items():
                key = self.make_key(url, category, field, item_key)
                result[key] = {
                    "url": url,
                    "title": listing.get("title", ""),
                    "company": listing.get("company", ""),
                    "category": category,
                    "field": field,
                    "item_key": item_key,
                    "state": {
                        "exists": True,
                        "value": value,
                    },
                }

        add_fields("listing", listing)

        if not include_detail:
            return result

        detail = record.get("detail")
        if not isinstance(detail, dict):
            detail = {}

        detail_fields = {
            key: value
            for key, value in detail.items()
            if key != "curriculum"
        }
        add_fields("detail", detail_fields)

        curriculum = detail.get("curriculum", [])
        if isinstance(curriculum, list):
            for index, item in enumerate(curriculum):
                if not isinstance(item, dict):
                    continue

                item_key = self.get_curriculum_key(item, index)
                add_fields("curriculum", item, item_key)

        return result

    @staticmethod
    def absent_state():
        return {
            "exists": False,
            "value": None,
        }

    def load_json_array(self, file_path):
        if not file_path.exists():
            return []

        try:
            data = json.loads(file_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            raise ValueError(
                f"File JSON tidak valid: {file_path}"
            ) from error

        if not isinstance(data, list):
            raise ValueError(
                f"Format file harus berupa JSON array: {file_path}"
            )

        return data

    def load_changes(self):
        changes = self.load_json_array(self.changes_file)

        # Riwayat dari versi tracker sebelumnya tidak pernah
        # melalui konfirmasi dua kali.
        for event in changes:
            if isinstance(event, dict):
                event.setdefault("status", "legacy")

        return changes

    def load_pending(self):
        pending = self.load_json_array(self.pending_file)
        result = {}

        for item in pending:
            if isinstance(item, dict) and item.get("key"):
                result[item["key"]] = item

        return result

    @staticmethod
    def write_json(file_path, data):
        temp_file = file_path.with_suffix(
            file_path.suffix + ".tmp"
        )
        temp_file.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        temp_file.replace(file_path)

    def process_batch(self, records, previous_jobs, now):
        changes = self.load_changes()
        pending = self.load_pending()

        previous_by_url = {
            self.get_url(job): job
            for job in previous_jobs
            if isinstance(job, dict) and self.get_url(job)
        }

        current_observations = {}

        # 1. Kumpulkan data terbaru dan data master sebelumnya.
        for incoming in records:
            if not isinstance(incoming, dict):
                continue

            url = self.get_url(incoming)
            if not url:
                continue

            previous = previous_by_url.get(url)
            if not isinstance(previous, dict):
                continue

            # Listing tetap dapat dibandingkan.
            old_fields = self.collect_fields(
                previous,
                include_detail=True,
            )
            new_fields = self.collect_fields(
                incoming,
                include_detail=(
                    incoming.get("scraping_status") == "success"
                ),
            )

            # Jika detail gagal/parsial, jangan membuat observasi
            # baru untuk detail dan kurikulum.
            if incoming.get("scraping_status") != "success":
                old_fields = {
                    key: value
                    for key, value in old_fields.items()
                    if value["category"] == "listing"
                }

            all_keys = set(old_fields) | set(new_fields)

            for key in all_keys:
                current = new_fields.get(key)

                if current is None:
                    old = old_fields[key]
                    current = {
                        **old,
                        "state": self.absent_state(),
                    }

                current_observations[key] = current

        # 2. Proses perubahan yang masih menunggu konfirmasi.
        handled_pending_keys = set()
        confirmed_count = 0
        reverted_count = 0

        events_by_id = {
            event.get("change_id"): event
            for event in changes
            if isinstance(event, dict) and event.get("change_id")
        }

        for key in list(pending.keys()):
            observation = current_observations.get(key)

            # Tidak ada observasi valid pada batch ini.
            # Biarkan perubahan tetap menunggu.
            if observation is None:
                continue

            item = pending[key]
            event = events_by_id.get(item.get("change_id"))

            if event is None:
                del pending[key]
                continue

            handled_pending_keys.add(key)
            current_state = observation["state"]
            baseline_state = item["baseline_state"]
            candidate_state = item["candidate_state"]

            if self.states_equal(current_state, candidate_state):
                item["observations"] += 1
                item["last_seen_at"] = now.isoformat(
                    timespec="seconds"
                )

                if item["observations"] >= 2:
                    event["status"] = "confirmed"
                    event["confirmed_at"] = now.isoformat(
                        timespec="seconds"
                    )
                    event["observation_count"] = item["observations"]

                    confirmed_count += 1
                    del pending[key]

            elif self.states_equal(current_state, baseline_state):
                event["status"] = "reverted"
                event["resolved_at"] = now.isoformat(
                    timespec="seconds"
                )
                event["reverted_to"] = current_state.get("value")

                reverted_count += 1
                del pending[key]

            else:
                # Nilai berubah lagi sebelum konfirmasi.
                # Mulai ulang penghitungan untuk nilai terbaru.
                item["candidate_state"] = current_state
                item["observations"] = 1
                item["last_seen_at"] = now.isoformat(
                    timespec="seconds"
                )

                event["new_value"] = current_state.get("value")
                event["status"] = "detected"
                event["observation_count"] = 1
                event["detected_at"] = now.isoformat(
                    timespec="seconds"
                )

        # 3. Deteksi perubahan baru dibandingkan master lama.
        new_count = 0

        for incoming in records:
            if not isinstance(incoming, dict):
                continue

            url = self.get_url(incoming)
            previous = previous_by_url.get(url)

            if not url or not isinstance(previous, dict):
                continue

            include_detail = (
                incoming.get("scraping_status") == "success"
            )

            old_fields = self.collect_fields(
                previous,
                include_detail=True,
            )
            new_fields = self.collect_fields(
                incoming,
                include_detail=include_detail,
            )

            if not include_detail:
                old_fields = {
                    key: value
                    for key, value in old_fields.items()
                    if value["category"] == "listing"
                }

            for key in set(old_fields) | set(new_fields):
                if key in handled_pending_keys or key in pending:
                    continue

                old = old_fields.get(key)
                new = new_fields.get(key)

                old_state = (
                    old["state"] if old else self.absent_state()
                )
                new_state = (
                    new["state"] if new else self.absent_state()
                )

                if self.states_equal(old_state, new_state):
                    continue

                metadata = new or old
                if not isinstance(metadata, dict):
                    continue
                change_id = f"change-{len(changes) + 1}"

                event = {
                    "change_id": change_id,
                    "detected_at": now.isoformat(
                        timespec="seconds"
                    ),
                    "url": url,
                    "title": metadata["title"],
                    "company": metadata["company"],
                    "category": metadata["category"],
                    "field": metadata["field"],
                    "item_key": metadata["item_key"],
                    "change_type": (
                        "added" if not old else
                        "removed" if not new else
                        "updated"
                    ),
                    "old_value": old_state.get("value"),
                    "new_value": new_state.get("value"),
                    "status": "detected",
                    "observation_count": 1,
                }

                changes.append(event)

                pending[key] = {
                    "key": key,
                    "change_id": change_id,
                    "baseline_state": old_state,
                    "candidate_state": new_state,
                    "observations": 1,
                    "last_seen_at": now.isoformat(
                        timespec="seconds"
                    ),
                }

                new_count += 1

        # 4. Simpan riwayat dan perubahan yang menunggu.
        self.write_json(self.changes_file, changes)
        self.write_json(
            self.pending_file,
            list(pending.values()),
        )

        write_csv(
            self.csv_file,
            changes,
            default_columns=[
                "change_id", "detected_at", "url",
                "title", "company", "category", "field",
                "item_key", "change_type", "old_value",
                "new_value", "status", "observation_count",
                "confirmed_at", "resolved_at", "reverted_to",
            ],
        )

        return {
            "new_changes": new_count,
            "confirmed_changes": confirmed_count,
            "reverted_changes": reverted_count,
            "pending_changes": len(pending),
            "total_changes": len(changes),
            "json": self.changes_file,
            "csv": self.csv_file,
            "pending_json": self.pending_file,
        }
