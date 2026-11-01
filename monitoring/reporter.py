
import csv
import json
from pathlib import Path


class MonitoringReporter:
    def __init__(self, output_dir="output"):
        self.report_dir = Path(output_dir) / "monitoring"
        self.report_dir.mkdir(parents=True, exist_ok=True)

        self.json_file = self.report_dir / "monitoring_report.json"
        self.csv_file = self.report_dir / "monitoring_report.csv"

    @staticmethod
    def write_json(file_path, data):
        temp_file = file_path.with_suffix(".json.tmp")

        temp_file.write_text(
            json.dumps(
                data,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        temp_file.replace(file_path)

    def build_csv_rows(self, report):
        rows = []

        # 1. Lowongan baru
        for job in report.get("new_jobs", []):
            rows.append({
                "record_type": "new_job",
                "status": "new",
                "title": job.get("title", ""),
                "company": job.get("company", ""),
                "url": job.get("url", ""),
                "category": "",
                "field": "",
                "old_value": "",
                "new_value": "",
            })

        # 2. Perubahan terkonfirmasi
        for change in report.get("confirmed_changes", []):
            rows.append({
                "record_type": "confirmed_change",
                "status": change.get("status", ""),
                "title": change.get("title", ""),
                "company": change.get("company", ""),
                "url": change.get("url", ""),
                "category": change.get("category", ""),
                "field": change.get("field", ""),
                "old_value": change.get("old_value", ""),
                "new_value": change.get("new_value", ""),
            })

        # 3. Perubahan yang masih menunggu konfirmasi
        for change in report.get("pending_changes", []):
            rows.append({
                "record_type": "pending_change",
                "status": change.get("status", ""),
                "title": change.get("title", ""),
                "company": change.get("company", ""),
                "url": change.get("url", ""),
                "category": change.get("category", ""),
                "field": change.get("field", ""),
                "old_value": change.get("old_value", ""),
                "new_value": change.get("new_value", ""),
            })

        return rows

    def write_csv(self, rows):
        columns = [
            "record_type",
            "status",
            "title",
            "company",
            "url",
            "category",
            "field",
            "old_value",
            "new_value",
        ]

        temp_file = self.csv_file.with_suffix(".csv.tmp")

        with temp_file.open(
            "w",
            newline="",
            encoding="utf-8-sig",
        ) as file:
            writer = csv.DictWriter(
                file,
                fieldnames=columns,
            )

            writer.writeheader()
            writer.writerows(rows)

        temp_file.replace(self.csv_file)

    def generate(self, report):
        rows = self.build_csv_rows(report)

        self.write_json(self.json_file, report)
        self.write_csv(rows)

        return {
            "json": self.json_file,
            "csv": self.csv_file,
            "total_rows": len(rows),
        }
