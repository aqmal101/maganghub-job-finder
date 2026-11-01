
import json
from datetime import datetime
from pathlib import Path

from storage.export import export_batch
from storage.tracker import ChangeTracker


class StorageManager:
    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.change_tracker = ChangeTracker(output_dir)

        self.master_dir = self.output_dir / "master"
        self.snapshot_dir = self.output_dir / "snapshots"

        self.master_file = self.master_dir / "jobs.json"

        self.master_dir.mkdir(parents=True, exist_ok=True)
        self.snapshot_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod

    def now():
        return datetime.now().astimezone()

    @staticmethod
    def timestamp(value):
        return value.isoformat(timespec="seconds")

    @staticmethod
    def write_json(file_path: Path, data):
        """Tulis JSON secara atomik agar file lama tidak rusak saat proses gagal."""
        temp_file = file_path.with_suffix(file_path.suffix + ".tmp")

        temp_file.write_text(
            json.dumps(
                data,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        temp_file.replace(file_path)

    def load_master(self) -> list[dict]:
        """Muat master data. Jika belum ada, mulai dengan list kosong."""
        if not self.master_file.exists():
            return []

        try:
            data = json.loads(
                self.master_file.read_text(encoding="utf-8")
            )
        except json.JSONDecodeError as error:
            raise ValueError(
                f"Master JSON tidak valid: {self.master_file}"
            ) from error

        if not isinstance(data, list):
            raise ValueError(
                "Format master harus berupa JSON array."
            )

        return data

    @staticmethod
    def get_url(record: dict) -> str:
        listing = record.get("listing")

        if not isinstance(listing, dict):
            return ""

        return str(listing.get("url") or "").strip()

    def save_snapshot(self, records: list[dict], now) -> Path:
        """Simpan hasil satu proses scraping tanpa mengubah snapshot lama."""
        date_folder = self.snapshot_dir / now.strftime("%Y-%m-%d")
        date_folder.mkdir(parents=True, exist_ok=True)

        snapshot_file = date_folder / (
            f"batch_{now.strftime('%Y%m%d_%H%M%S_%f')}.json"
        )

        snapshot = {
            "snapshot_at": self.timestamp(now),
            "record_count": len(records),
            "records": records,
        }

        self.write_json(snapshot_file, snapshot)

        return snapshot_file

    def upsert_master(
        self,
        records: list[dict],
        now,
    ) -> tuple[list[dict], dict]:
        """Tambah atau perbarui master berdasarkan URL lowongan."""
        master_jobs = self.load_master()

        # Buat indeks URL agar pencarian record lebih efisien.
        index_by_url = {}

        for index, job in enumerate(master_jobs):
            url = self.get_url(job)

            if url:
                index_by_url[url] = index

        added = 0
        updated = 0
        preserved_details = 0
        skipped = 0

        for incoming in records:
            if not isinstance(incoming, dict):
                skipped += 1
                continue

            url = self.get_url(incoming)

            if not url:
                print("Peringatan: record tanpa URL dilewati dari master.")
                skipped += 1
                continue

            listing = incoming.get("listing")
            detail = incoming.get("detail")

            if not isinstance(listing, dict):
                listing = {}

            if not isinstance(detail, dict):
                detail = None

            status = incoming.get("scraping_status", "failed")

            existing_index = index_by_url.get(url)

            if existing_index is None:
                # Lowongan belum pernah tersimpan.
                new_job = {
                    "listing": listing,
                    "detail": detail,
                    "scraping_status": status,
                    "validation_errors": incoming.get(
                        "validation_errors", []
                    ),
                    "audit_warnings": incoming.get(
                        "audit_warnings", []
                    ),
                    "error": incoming.get("error", ""),
                    "first_seen_at": self.timestamp(now),
                    "last_seen_at": self.timestamp(now),
                    "last_scraped_at": self.timestamp(now),
                    "last_successful_detail_at": (
                        self.timestamp(now)
                        if status == "success"
                        else None
                    ),
                }

                master_jobs.append(new_job)
                index_by_url[url] = len(master_jobs) - 1
                added += 1
                continue

            # Lowongan sudah ada.
            existing = master_jobs[existing_index]

            if not isinstance(existing, dict):
                skipped += 1
                continue

            previous_detail = existing.get("detail")

            existing["listing"] = listing
            existing["last_seen_at"] = self.timestamp(now)
            existing["last_scraped_at"] = self.timestamp(now)
            existing["scraping_status"] = status
            existing["validation_errors"] = incoming.get(
                "validation_errors", []
            )
            existing["audit_warnings"] = incoming.get(
                "audit_warnings", []
            )
            existing["error"] = incoming.get("error", "")

            if status == "success":
                existing["detail"] = detail
                existing["last_successful_detail_at"] = (
                    self.timestamp(now)
                )

            elif isinstance(previous_detail, dict):
                # Detail lama dipertahankan untuk hasil partial/failed.
                preserved_details += 1

            else:
                # Belum ada detail lengkap sebelumnya.
                existing["detail"] = detail

            updated += 1

        return master_jobs, {
            "added": added,
            "updated": updated,
            "preserved_details": preserved_details,
            "skipped": skipped,
            "total_master": len(master_jobs),
        }

    
    def save_batch(self, records: list[dict]) -> dict:
        now = self.now()

        # 1. Simpan snapshot
        snapshot_file = self.save_snapshot(records, now)

        # 2. Ambil master sebelum diperbarui
        previous_jobs = self.load_master()

        # 3. Proses deteksi dan konfirmasi perubahan
        change_result = self.change_tracker.process_batch(
            records=records,
            previous_jobs=previous_jobs,
            now=now,
        )

        # 4. Perbarui master
        master_jobs, stats = self.upsert_master(records, now)

        # 5. Ekspor master
        export_result = export_batch(
            master_jobs,
            output_dir=str(self.master_dir),
            json_filename="jobs.json",
        )

        # 6. Kembalikan seluruh hasil
        return {
            "snapshot": snapshot_file,

            "master_json": export_result["json"],
            "master_listings_csv": export_result["listings_csv"],
            "master_details_csv": export_result["details_csv"],
            "master_curriculum_csv": export_result["curriculum_csv"],

            "changes_json": change_result["json"],
            "changes_csv": change_result["csv"],
            "pending_json": change_result["pending_json"],

            "new_changes": change_result["new_changes"],
            "confirmed_changes": change_result["confirmed_changes"],
            "reverted_changes": change_result["reverted_changes"],
            "pending_changes": change_result["pending_changes"],
            "total_changes": change_result["total_changes"],

            # Penting: statistik master harus tetap dikembalikan.
            **stats,
        }

