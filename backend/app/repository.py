import json
from pathlib import Path
from typing import Any


class LegacyDataError(RuntimeError):
    """Raised when an existing JSON data source is invalid."""


class LegacyJsonRepository:
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir

    def _load_json(self, relative_path: str, default: Any) -> Any:
        path = self.data_dir / relative_path
        if not path.exists():
            return default

        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise LegacyDataError(f"Unable to read data file: {path}") from error

    def jobs(self) -> list[dict]:
        data = self._load_json("master/jobs.json", [])
        if not isinstance(data, list):
            raise LegacyDataError("output/master/jobs.json must contain an array")
        return [item for item in data if isinstance(item, dict)]

    def changes(self) -> list[dict]:
        data = self._load_json("changes/changes.json", [])
        if not isinstance(data, list):
            raise LegacyDataError("output/changes/changes.json must contain an array")
        return [item for item in data if isinstance(item, dict)]

    def pending_changes(self) -> list[dict]:
        data = self._load_json("changes/pending.json", [])
        if not isinstance(data, list):
            raise LegacyDataError("output/changes/pending.json must contain an array")
        return [item for item in data if isinstance(item, dict)]

    def monitoring_report(self) -> dict:
        data = self._load_json("monitoring/monitoring_report.json", {})
        if not isinstance(data, dict):
            raise LegacyDataError(
                "output/monitoring/monitoring_report.json must contain an object"
            )
        return data

    def last_snapshot(self) -> dict | None:
        snapshot_dir = self.data_dir / "snapshots"
        candidates = sorted(snapshot_dir.glob("*/*.json"))
        if not candidates:
            return None

        data = self._load_json(str(candidates[-1].relative_to(self.data_dir)), {})
        return data if isinstance(data, dict) else None

    def last_run(self) -> dict:
        snapshot = self.last_snapshot()
        if snapshot is None:
            return {
                "batch_at": None,
                "status": "unavailable",
                "total_listings": 0,
                "successful_details": 0,
                "partial_details": 0,
                "failed_details": 0,
            }

        records = snapshot.get("records", [])
        if not isinstance(records, list):
            records = []

        statuses = [
            record.get("scraping_status")
            for record in records
            if isinstance(record, dict)
        ]
        return {
            "batch_at": snapshot.get("snapshot_at"),
            "status": "available",
            "total_listings": len(records),
            "successful_details": statuses.count("success"),
            "partial_details": statuses.count("partial"),
            "failed_details": statuses.count("failed"),
        }
