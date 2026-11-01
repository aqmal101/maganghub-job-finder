
# crawler/test_listing.py

import json
from pathlib import Path

from playwright.sync_api import sync_playwright

from crawler.listing import scrape_listing_page


KEYWORD = "it support"

Path("output").mkdir(exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    results = scrape_listing_page(
        page=page,
        keyword=KEYWORD,
        page_number=1
    )

    print(f"Jumlah lowongan: {len(results)}")

    for index, job in enumerate(results, start=1):
        print(f"\nLowongan {index}")
        print("Judul      :", job["title"])
        print("Perusahaan :", job["company"])
        print("Lokasi     :", job["location"])
        print("Pendidikan :", job["education"])
        print("Hari kerja :", job["work_days_per_week"])
        print("Kuota      :", job["quota"])
        print("Pelamar    :", job["applicants"])
        print("Peluang    :", job["opportunity"])
        print("URL        :", job["url"])

    Path("output/listing-results.json").write_text(
        json.dumps(
            results,
            indent=2,
            ensure_ascii=False
        ),
        encoding="utf-8"
    )

    print("\nFile tersimpan: output/listing-results.json")

    browser.close()
