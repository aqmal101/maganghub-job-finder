
from urllib.parse import urlencode

from crawler.listing import parse_card, CARD_SELECTOR, BASE_URL


def scrape_keyword_pages(
    page,
    keyword,
    max_pages=3,
):
    results = []
    seen_urls = set()

    for page_number in range(1, max_pages + 1):
        params = urlencode({
            "keyword": keyword,
            "page": page_number,
        })

        url = f"{BASE_URL}?{params}"

        print(f"\nMengambil halaman {page_number}: {keyword}")

        page.goto(
            url,
            wait_until="domcontentloaded",
            timeout=60000,
        )

        try:
            page.wait_for_selector(
                CARD_SELECTOR,
                timeout=20000,
            )
        except Exception:
            print("Tidak ada kartu lowongan. Menghentikan pencarian.")
            break

        cards = page.locator(CARD_SELECTOR)
        card_count = cards.count()

        if card_count == 0:
            print("Halaman kosong.")
            break

        new_items = 0

        for index in range(card_count):
            card = cards.nth(index)
            item = parse_card(card)

            item["keyword"] = keyword
            item["page"] = page_number

            job_url = item.get("url")

            if not job_url or job_url in seen_urls:
                continue

            seen_urls.add(job_url)
            results.append(item)
            new_items += 1

        print(f"Kartu ditemukan: {card_count}")
        print(f"Data baru: {new_items}")

        if new_items == 0:
            print("Tidak ada data baru. Menghentikan pencarian.")
            break

        page.wait_for_timeout(1200)

    return results
