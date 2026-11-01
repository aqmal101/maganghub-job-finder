
import json
from pathlib import Path
from datetime import datetime, timedelta


class MonitoringAnalyzer:
    VALID_PERIODS = {"batch", "today", "last_7_days", "all"}

    def __init__(self, output_dir="output"):
        self.output_dir = Path(output_dir)
        self.changes_file = (
            self.output_dir / "changes" / "changes.json"
        )
        self.pending_file = (
            self.output_dir / "changes" / "pending.json"
        )

    @staticmethod
    def load_json(file_path):
        if not file_path.exists():
            return []

        try:
            data = json.loads(
                file_path.read_text(encoding="utf-8")
            )
        except json.JSONDecodeError as error:
            raise ValueError(
                f"JSON tidak valid: {file_path}"
            ) from error

        if not isinstance(data, list):
            raise ValueError(
                f"Format harus berupa JSON array: {file_path}"
            )

        return data

    @staticmethod
    def parse_datetime(value):
        if not value:
            return None

        try:
            result = datetime.fromisoformat(value)

            # Mendukung timestamp lama tanpa informasi timezone.
            if result.tzinfo is None:
                result = result.astimezone()

            return result
        except (ValueError, TypeError):
            return None

    def is_in_period(self, timestamp, period, batch_at=None):
        event_time = self.parse_datetime(timestamp)

        if event_time is None:
            return False

        now = datetime.now().astimezone()

        if period == "all":
            return True

        if period == "batch":
            batch_time = self.parse_datetime(batch_at)

            if batch_time is None:
                raise ValueError(
                    "batch_at diperlukan untuk periode batch"
                )

            return event_time >= batch_time

        if period == "today":
            start_of_day = now.replace(
                hour=0,
                minute=0,
                second=0,
                microsecond=0,
            )
            return start_of_day <= event_time <= now

        if period == "last_7_days":
            start_time = now - timedelta(days=7)
            return start_time <= event_time <= now

        raise ValueError(f"Periode tidak dikenal: {period}")

    @staticmethod
    def summarize_job(job):
        listing = job.get("listing", {})

        return {
            "url": listing.get("url", ""),
            "title": listing.get("title", ""),
            "company": listing.get("company", ""),
            "location": listing.get("location", ""),
            "quota": listing.get("quota", ""),
            "applicants": listing.get("applicants", ""),
            "scraping_status": job.get("scraping_status", ""),
            "first_seen_at": job.get("first_seen_at", ""),
        }

    @staticmethod
    def summarize_change(change):
        return {
            "change_id": change.get("change_id"),
            "url": change.get("url", ""),
            "title": change.get("title", ""),
            "company": change.get("company", ""),
            "category": change.get("category", ""),
            "field": change.get("field", ""),
            "old_value": change.get("old_value"),
            "new_value": change.get("new_value"),
            "status": change.get("status"),
            "detected_at": change.get("detected_at"),
            "confirmed_at": change.get("confirmed_at"),
        }

    def analyze(self, storage_result, period="batch"):
        if period not in self.VALID_PERIODS:
            raise ValueError(
                f"Periode harus salah satu dari: "
                f"{', '.join(sorted(self.VALID_PERIODS))}"
            )

        batch_at = storage_result.get("batch_at")

        if period == "batch" and not batch_at:
            raise ValueError(
                "storage_result tidak memiliki batch_at"
            )

        changes = self.load_json(self.changes_file)
        pending = self.load_json(self.pending_file)

        confirmed_changes = []
        pending_changes = []

        for item in changes:
            if not isinstance(item, dict):
                continue

            status = item.get("status")

            if status == "confirmed":
                # Perubahan dianggap terjadi pada saat dikonfirmasi.
                event_time = item.get("confirmed_at")

                if self.is_in_period(event_time, period, batch_at):
                    confirmed_changes.append(
                        self.summarize_change(item)
                    )

            elif status == "detected":
                # Perubahan sementara dihitung sejak pertama terdeteksi.
                event_time = item.get("detected_at")

                if self.is_in_period(event_time, period, batch_at):
                    pending_changes.append(
                        self.summarize_change(item)
                    )

        # added_jobs berasal dari batch yang sedang diproses.
        added_jobs = [
            self.summarize_job(item)
            for item in storage_result.get("added_jobs", [])
            if isinstance(item, dict)
        ]

        return {
            "generated_at": datetime.now().astimezone().isoformat(
                timespec="seconds"
            ),
            "period": period,
            "batch_at": batch_at,
            "summary": {
                "new_jobs": len(added_jobs),
                "confirmed_changes": len(confirmed_changes),
                "pending_changes": len(pending_changes),
                "pending_tracker_items": len(pending),
            },
            "new_jobs": added_jobs,
            "confirmed_changes": confirmed_changes,
            "pending_changes": pending_changes,
        }
