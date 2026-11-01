
import json
import re
from pathlib import Path

from playwright.sync_api import sync_playwright

from crawler.multi_page import scrape_keyword_pages
from crawler.detail import parse_detail
from storage.export import export_batch
from storage.manager import StorageManager


def validate_detail(detail: dict) -> list[str]:
    errors = []

    if not isinstance(detail, dict):
        return ["Data detail bukan dictionary"]

    if not detail.get("title"):
        errors.append("Judul lowongan kosong")

    if not detail.get("description"):
        errors.append("Deskripsi pekerjaan kosong")

    if not detail.get("qualifications"):
        errors.append("Kualifikasi tidak ditemukan")

    curriculum = detail.get("curriculum", [])

    if not isinstance(curriculum, list):
        errors.append("Format kurikulum tidak valid")
        return errors

    if not curriculum:
        errors.append("Kurikulum tidak ditemukan")
    else:
        for index, item in enumerate(curriculum, start=1):

            if not isinstance(item, dict):
                errors.append(
                    f"Format kurikulum ke-{index} tidak valid"
                )
                continue

            if not item.get("title"):
                errors.append(
                    f"Judul kurikulum ke-{index} kosong"
                )

            if not item.get("type"):
                errors.append(
                    f"Tipe kurikulum ke-{index} kosong"
                )

            if not item.get("month"):
                errors.append(
                    f"Bulan kurikulum ke-{index} kosong"
                )

            if not item.get("duration"):
                errors.append(
                    f"Durasi kurikulum ke-{index} kosong"
                )

    return errors

def main():
    keyword = "it support"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        try:
            # 1. Ambil listing
            listings = scrape_keyword_pages(
                page=page,
                keyword=keyword,
                max_pages=1,
            )

            sample = listings[:5]

            details = []

            successful = 0
            partial = 0
            failed = 0

            # 2. Scraping detail
            for index, item in enumerate(sample, start=1):
                url = item["url"]

                print(
                    f"\n[{index}/{len(sample)}] "
                    f"Membuka: {url}"
                )

                try:
                    detail = parse_detail(page, url)

                    print("\n--- DETAIL KURIKULUM ---")

                    for curriculum in detail.get("curriculum", []):
                        print(
                            f"[{curriculum['order']}] "
                            f"{curriculum['title']}"
                        )
                        print("    Tipe:", curriculum["type"])
                        print("    Bulan:", curriculum["month"])
                        print("    Durasi:", curriculum["duration"])
                        print("    Deskripsi:", curriculum["description"])

                    errors = validate_detail(detail)
                    is_valid = not errors
                    audit_warnings = audit_detail(item, detail)
                    combined = {
                        "listing": item,
                        "detail": detail,
                        "scraping_status": (
                            "success" if is_valid else "partial"
                        ),
                        "validation_errors": errors,
                        "audit_warnings": audit_warnings,
                    }

                    details.append(combined)

                    # 3. Statistik hasil ekstraksi
                    print("Judul:", detail.get("title"))
                    print("Perusahaan:", item.get("company"))

                    print(
                        "Deskripsi tersedia:",
                        bool(detail.get("description")),
                    )

                    print(
                        "Jumlah kualifikasi:",
                        len(detail.get("qualifications", [])),
                    )

                    print(
                        "Jumlah kurikulum:",
                        len(detail.get("curriculum", [])),
                    )

                    if is_valid:
                        successful += 1
                        print("Status: SUCCESS")

                    else:
                        partial += 1
                        print("Status: PARTIAL")

                        for error in errors:
                            print("  -", error)

                except Exception as error:
                    failed += 1

                    print("Status: FAILED")
                    print("Error:", str(error))

                    details.append({
                        "listing": item,
                        "detail": None,
                        "scraping_status": "failed",
                        "error": str(error),
                    })

                # Jeda antar permintaan
                page.wait_for_timeout(2000)

            # 4. Simpan hasil batch untuk kebutuhan pengujian
            export_result = export_batch(details)

            # 5. Simpan snapshot dan perbarui master
            storage_manager = StorageManager()

            storage_result = storage_manager.save_batch(details)

            print("\n--- CHANGE TRACKING ---")
            print("Perubahan batch ini:", storage_result["new_changes"])
            print("Total riwayat perubahan:", storage_result["total_changes"])
            print("Changes JSON:", storage_result["changes_json"])
            print("Changes CSV:", storage_result["changes_csv"])

            # 6. Statistik akhir
            print("\n========== SELESAI ==========")
            print("Listing diuji:", len(sample))
            print("Detail berhasil:", successful)
            print("Detail parsial:", partial)
            print("Detail gagal:", failed)

            print("\n--- HASIL EKSPOR BATCH ---")
            print("JSON:", export_result["json"])
            print("Listing CSV:", export_result["listings_csv"])
            print("Detail CSV:", export_result["details_csv"])
            print("Kurikulum CSV:", export_result["curriculum_csv"])

            print("\n--- HASIL MASTER DATA ---")
            print("Lowongan baru:", storage_result["added"])
            print("Lowongan diperbarui:", storage_result["updated"])
            print(
                "Detail lama dipertahankan:",
                storage_result["preserved_details"],
            )
            print("Record dilewati:", storage_result["skipped"])
            print("Total master:", storage_result["total_master"])

            print("\n--- HASIL SNAPSHOT ---")
            print("Snapshot:", storage_result["snapshot"])

            print("\n--- MASTER EXPORT ---")
            print("JSON:", storage_result["master_json"])
            print("Listing CSV:", storage_result["master_listings_csv"])
            print("Detail CSV:", storage_result["master_details_csv"])
            print("Kurikulum CSV:", storage_result["master_curriculum_csv"])

        finally:
            browser.close()


def audit_curriculum(curriculum: list[dict]) -> list[str]:
    """Periksa konsistensi rentang durasi dan format bulan kurikulum."""
    warnings = []

    for index, item in enumerate(curriculum, start=1):
        if not isinstance(item, dict):
            continue

        duration = str(item.get("duration", "")).strip()
        month = str(item.get("month", "")).strip()

        numbers = re.findall(r"\d+", duration)

        if len(numbers) >= 2:
            start = int(numbers[0])
            end = int(numbers[1])

            if start > end:
                warnings.append(
                    f"Kurikulum ke-{index}: "
                    f"rentang durasi tidak valid ({duration})"
                )
            elif start == end:
                warnings.append(
                    f"Kurikulum ke-{index}: "
                    f"durasi awal dan akhir sama ({duration})"
                )

        if not re.search(r"^Bulan ke-\d+$", month):
            warnings.append(
                f"Kurikulum ke-{index}: format bulan tidak dikenali"
            )

    return warnings


def audit_detail(listing: dict, detail: dict) -> list[str]:
    """Bandingkan field penting pada kartu listing dengan halaman detail."""
    warnings = []

    comparable_fields = {
        "quota": ("quota", "quota"),
        "applicants": ("applicants", "applicants"),
        "opportunity": ("opportunity", "opportunity"),
    }

    for field, (listing_key, detail_key) in comparable_fields.items():
        listing_value = listing.get(listing_key)
        detail_value = detail.get(detail_key)

        if listing_value is None or detail_value is None:
            continue

        if field in ("quota", "applicants"):
            listing_number = re.search(
                r"\d+", str(listing_value)
            )
            detail_number = re.search(
                r"\d+", str(detail_value)
            )

            if (
                listing_number
                and detail_number
                and listing_number.group() != detail_number.group()
            ):
                warnings.append(
                    f"Perbedaan {field}: listing={listing_value}, "
                    f"detail={detail_value}"
                )
        elif (
            str(listing_value).strip().casefold()
            != str(detail_value).strip().casefold()
        ):
            warnings.append(
                f"Perbedaan {field}: listing={listing_value}, "
                f"detail={detail_value}"
            )

    curriculum = detail.get("curriculum", [])

    if not isinstance(curriculum, list):
        warnings.append("Format kurikulum tidak valid")
        return warnings

    warnings.extend(audit_curriculum(curriculum))

    for index, item in enumerate(curriculum, start=1):
        if not isinstance(item, dict):
            warnings.append(
                f"Kurikulum ke-{index}: format item tidak valid"
            )
            continue

        title = item.get("title", "").strip()
        description = item.get("description", "").strip()

        if not title:
            continue

        if description and title.lower() == description.lower():
            warnings.append(
                f"Kurikulum ke-{index}: judul dan deskripsi identik"
            )

        if title.endswith((",", ":", "/", "&")):
            warnings.append(
                f"Kurikulum ke-{index}: kemungkinan judul terpotong"
            )

    return warnings



if __name__ == "__main__":
    main()
