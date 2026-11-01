
from datetime import datetime, timedelta, timezone
from tempfile import TemporaryDirectory

from storage.tracker import ChangeTracker


URL = "https://example.com/jobs/it-support"

WIB = timezone(timedelta(hours=7))


def make_record(applicants, opportunity, status="success"):
    return {
        "listing": {
            "url": URL,
            "title": "IT Support",
            "company": "RSUD Tjokronegoro",
        },
        "detail": {
            "title": "IT Support",
            "description": "Menangani kebutuhan IT.",
            "qualifications": ["Memahami jaringan komputer"],
            "applicants": applicants,
            "opportunity": opportunity,
            "curriculum": [
                {
                    "order": 1,
                    "title": "IT Support",
                    "type": "Pelatihan",
                    "month": "Bulan ke-1",
                    "duration": "10 hari",
                    "description": "Pengenalan IT Support",
                }
            ],
        },
        "scraping_status": status,
    }


def make_time(minute):
    return datetime(
        2026, 11, 1, 15, minute, 0, tzinfo=WIB
    )


def test_confirmed():
    print("\n=== TEST 1: CONFIRMED ===")

    with TemporaryDirectory() as temp_dir:
        tracker = ChangeTracker(temp_dir)

        previous_master = [
            make_record("4 orang", "Peluang Besar (60%)")
        ]

        # Scraping pertama: nilai berubah.
        first_result = tracker.process_batch(
            records=[
                make_record("5 orang", "Peluang Besar (50%)")
            ],
            previous_jobs=previous_master,
            now=make_time(1),
        )

        assert first_result["new_changes"] == 2
        assert first_result["confirmed_changes"] == 0
        assert first_result["pending_changes"] == 2

        print("PASS: Perubahan pertama berstatus DETECTED")

        # Master dianggap sudah diperbarui oleh StorageManager.
        updated_master = [
            make_record("5 orang", "Peluang Besar (50%)")
        ]

        # Scraping kedua: nilai tetap sama.
        second_result = tracker.process_batch(
            records=[
                make_record("5 orang", "Peluang Besar (50%)")
            ],
            previous_jobs=updated_master,
            now=make_time(2),
        )

        assert second_result["new_changes"] == 0
        assert second_result["confirmed_changes"] == 2
        assert second_result["pending_changes"] == 0

        print("PASS: Dua perubahan berhasil dikonfirmasi")

        # Scraping ketiga: nilai tetap sama, tidak boleh duplikat.
        third_result = tracker.process_batch(
            records=[
                make_record("5 orang", "Peluang Besar (50%)")
            ],
            previous_jobs=updated_master,
            now=make_time(3),
        )

        assert third_result["new_changes"] == 0
        assert third_result["confirmed_changes"] == 0
        assert third_result["total_changes"] == 2

        print("PASS: Tidak ada duplikasi setelah CONFIRMED")


def test_reverted():
    print("\n=== TEST 2: REVERTED ===")

    with TemporaryDirectory() as temp_dir:
        tracker = ChangeTracker(temp_dir)

        original_master = [
            make_record("4 orang", "Peluang Besar (60%)")
        ]

        # Scraping pertama: nilai berubah.
        first_result = tracker.process_batch(
            records=[
                make_record("5 orang", "Peluang Besar (50%)")
            ],
            previous_jobs=original_master,
            now=make_time(1),
        )

        assert first_result["pending_changes"] == 2

        # Master setelah scraping pertama.
        updated_master = [
            make_record("5 orang", "Peluang Besar (50%)")
        ]

        # Scraping kedua: nilai kembali seperti semula.
        second_result = tracker.process_batch(
            records=[
                make_record("4 orang", "Peluang Besar (60%)")
            ],
            previous_jobs=updated_master,
            now=make_time(2),
        )

        assert second_result["reverted_changes"] == 2
        assert second_result["pending_changes"] == 0

        print("PASS: Perubahan yang kembali ke nilai awal menjadi REVERTED")


def test_partial_does_not_confirm():
    print("\n=== TEST 3: PARTIAL TIDAK MENGONFIRMASI ===")

    with TemporaryDirectory() as temp_dir:
        tracker = ChangeTracker(temp_dir)

        original_master = [
            make_record("4 orang", "Peluang Besar (60%)")
        ]

        # Scraping pertama sukses dan mendeteksi perubahan.
        first_result = tracker.process_batch(
            records=[
                make_record("5 orang", "Peluang Besar (50%)")
            ],
            previous_jobs=original_master,
            now=make_time(1),
        )

        assert first_result["pending_changes"] == 2

        # Scraping kedua partial: tidak boleh menambah hitungan.
        partial_result = tracker.process_batch(
            records=[
                make_record(
                    "5 orang",
                    "Peluang Besar (50%)",
                    status="partial",
                )
            ],
            previous_jobs=original_master,
            now=make_time(2),
        )

        assert partial_result["confirmed_changes"] == 0
        assert partial_result["pending_changes"] == 2

        print("PASS: PARTIAL tidak mengonfirmasi perubahan detail")

        # Scraping ketiga sukses: baru boleh mengonfirmasi.
        success_result = tracker.process_batch(
            records=[
                make_record("5 orang", "Peluang Besar (50%)")
            ],
            previous_jobs=original_master,
            now=make_time(3),
        )

        assert success_result["confirmed_changes"] == 2
        assert success_result["pending_changes"] == 0

        print("PASS: SUCCESS berikutnya mengonfirmasi perubahan")


def main():
    test_confirmed()
    test_reverted()
    test_partial_does_not_confirm()

    print("\n====================================")
    print("SEMUA PENGUJIAN CHANGE TRACKER LOLOS")
    print("====================================")


if __name__ == "__main__":
    main()
