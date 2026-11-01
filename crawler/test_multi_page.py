
from playwright.sync_api import sync_playwright

from crawler.multi_page import scrape_keyword_pages


def main():
    keyword = "it support"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        results = scrape_keyword_pages(
            page=page,
            keyword=keyword,
            max_pages=3,
        )

        print("\n========== HASIL ==========")
        print("Keyword:", keyword)
        print("Total lowongan unik:", len(results))

        for index, item in enumerate(results, start=1):
            print(
                index,
                item.get("title"),
                "|",
                item.get("company"),
                "|",
                item.get("location"),
            )

        browser.close()


if __name__ == "__main__":
    main()
