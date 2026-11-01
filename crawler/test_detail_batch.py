
import json
from pathlib import Path

from playwright.sync_api import sync_playwright

from crawler.multi_page import scrape_keyword_pages
from crawler.detail import parse_detail


def main():
    keyword = "it support"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        # Ambil listing dari halaman pertama
        listings = scrape_keyword_pages(
            page=page,
            keyword=keyword,
            max_pages=1,
        )

        # Batasi pengujian ke 5 detail
        sample = listings[:5]

        details = []

        for index, item in enumerate(sample, start=1):
            url = item["url"]

            print(f"\n[{index}/{len(sample)}] Membuka: {url}")

            try:
                page.goto(
                    url,
                    wait_until="domcontentloaded",
                    timeout=60000,
                )

                page.wait_for_selector(
                    "h1",
                    timeout=20000,
                )

                detail = parse_detail(page, url)

                # Gabungkan data listing dan detail
                combined = {
                "listing": item,
                "detail": detail,
                }

                details.append(combined)

                print("Judul:", combined.get("title"))
                print("Perusahaan:", combined.get("company"))
                print(
                    "Deskripsi tersedia:",
                    bool(combined.get("description")),
                )
                print(
                    "Jumlah kualifikasi:",
                    len(combined.get("qualifications", [])),
                )

            except Exception as error:
                print("Gagal mengambil detail:", error)

            # Beri jeda antar permintaan
            page.wait_for_timeout(2000)

        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)

        output_file = output_dir / "detail_batch_test.json"

        output_file.write_text(
            json.dumps(
                details,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        print("\n========== SELESAI ==========")
        print("Listing diuji:", len(sample))
        print("Detail berhasil:", len(details))
        print("File:", output_file)

        browser.close()


if __name__ == "__main__":
    main()
