
import json
from pathlib import Path

from playwright.sync_api import sync_playwright

from crawler import detail
from crawler import detail
from crawler.multi_page import scrape_keyword_pages
from crawler.detail import parse_detail


def validate_detail(detail: dict) -> tuple[bool, list[str]]:
    """Memvalidasi kelengkapan data hasil scraping."""

    errors = []

    if not detail.get("title"):
        errors.append("Judul tidak ditemukan")

    if not detail.get("description"):
        errors.append("Deskripsi tidak ditemukan")

    if not detail.get("qualifications"):
        errors.append("Kualifikasi tidak ditemukan")

    return len(errors) == 0, errors


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

                    is_valid, errors = validate_detail(detail)
                    combined = {
                        "listing": item,
                        "detail": detail,
                        "scraping_status": (
                            "success" if is_valid else "partial"
                        ),
                        "validation_errors": errors,
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

            # 4. Simpan hasil
            output_dir = Path("output")
            output_dir.mkdir(exist_ok=True)

            output_file = (
                output_dir / "detail_batch_test.json"
            )

            output_file.write_text(
                json.dumps(
                    details,
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )

            # 5. Statistik akhir
            print("\n========== SELESAI ==========")
            print("Listing diuji:", len(sample))
            print("Detail berhasil:", successful)
            print("Detail parsial:", partial)
            print("Detail gagal:", failed)
            print("File:", output_file)

        finally:
            browser.close()


if __name__ == "__main__":
    main()
