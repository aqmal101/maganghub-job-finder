
import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

from monitoring.analyzer import MonitoringAnalyzer
from monitoring.reporter import MonitoringReporter


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, indent=2),
        encoding="utf-8"
    )


def main():
    now = datetime.now().astimezone()

    batch_at = now - timedelta(minutes=30)
    yesterday = now - timedelta(days=1)
    eight_days_ago = now - timedelta(days=8)

    changes = [
        {
            "change_id": "C001",
            "url": "https://example.com/job/1",
            "title": "Developer A",
            "company": "Company A",
            "category": "detail",
            "field": "quota",
            "old_value": 5,
            "new_value": 10,
            "status": "confirmed",
            "detected_at": batch_at.isoformat(),
            "confirmed_at": now.isoformat(),
        },
        {
            "change_id": "C002",
            "url": "https://example.com/job/2",
            "title": "Developer B",
            "company": "Company B",
            "category": "detail",
            "field": "quota",
            "old_value": 5,
            "new_value": 8,
            "status": "confirmed",
            "detected_at": yesterday.isoformat(),
            "confirmed_at": yesterday.isoformat(),
        },
        {
            "change_id": "C003",
            "url": "https://example.com/job/3",
            "title": "Developer C",
            "company": "Company C",
            "category": "listing",
            "field": "applicants",
            "old_value": 10,
            "new_value": 15,
            "status": "detected",
            "detected_at": now.isoformat(),
        },
        {
            "change_id": "C004",
            "url": "https://example.com/job/4",
            "title": "Developer D",
            "company": "Company D",
            "category": "detail",
            "field": "description",
            "old_value": "Old",
            "new_value": "New",
            "status": "detected",
            "detected_at": eight_days_ago.isoformat(),
        },
    ]

    with tempfile.TemporaryDirectory() as temp_dir:
        output_dir = Path(temp_dir)

        write_json(
            output_dir / "changes" / "changes.json",
            changes
        )
        write_json(
            output_dir / "changes" / "pending.json",
            []
        )

        analyzer = MonitoringAnalyzer(
            output_dir=str(output_dir)
        )

        storage_result = {
            "batch_at": batch_at.isoformat(),
            "added_jobs": [],
        }

        expected = {
            "batch": (1, 1),
            "today": (1, 1),
            "last_7_days": (2, 1),
            "all": (2, 2),
        }

        print("\n=== TEST FILTER WAKTU ===")

        for period, (expected_confirmed, expected_pending) in expected.items():
            report = analyzer.analyze(
                storage_result,
                period=period
            )

            summary = report["summary"]

            confirmed = summary["confirmed_changes"]
            pending = summary["pending_changes"]

            passed = (
                confirmed == expected_confirmed
                and pending == expected_pending
            )

            print(
                f"{period:12} | "
                f"Confirmed: {confirmed} | "
                f"Pending: {pending} | "
                f"{'PASS' if passed else 'FAIL'}"
            )

            assert passed, (
                f"Filter {period} tidak sesuai. "
                f"Expected {(expected_confirmed, expected_pending)}, "
                f"got {(confirmed, pending)}"
            )

        print("\n=== TEST REPORTER ===")

        report = analyzer.analyze(
            storage_result,
            period="all"
        )

        reporter = MonitoringReporter(
            output_dir=str(output_dir)
        )

        result = reporter.generate(report)

        assert Path(result["json"]).exists()
        assert Path(result["csv"]).exists()

        print("JSON report: PASS")
        print("CSV report : PASS")
        print("\nSEMUA PENGUJIAN MONITORING LOLOS")


if __name__ == "__main__":
    main()
