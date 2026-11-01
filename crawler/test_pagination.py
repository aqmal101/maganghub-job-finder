
from playwright.sync_api import sync_playwright
from urllib.parse import urlencode

BASE_URL = (
    "https://maganghub.kemnaker.go.id"
    "/magang-nasional/lowongan"
)

KEYWORD = "it support"


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        for page_number in [1, 2]:
            params = urlencode({
                "keyword": KEYWORD,
                "page": page_number,
            })

            url = f"{BASE_URL}?{params}"

            page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=60000,
            )

            page.wait_for_selector(
                'a.group.block.h-full[href*="/magang-nasional/lowongan/"]',
                timeout=20000,
            )

            cards = page.locator(
                'a.group.block.h-full[href*="/magang-nasional/lowongan/"]'
            )

            print(f"\nHalaman: {page_number}")
            print("URL:", page.url)
            print("Jumlah kartu:", cards.count())

            if cards.count() > 0:
                print("Lowongan pertama:", cards.nth(0).inner_text())

        browser.close()


if __name__ == "__main__":
    main()
