from playwright.sync_api import sync_playwright

URL = "https://maganghub.kemnaker.go.id/"

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=False
    )

    page = browser.new_page()
    page.goto(URL, wait_until="domcontentloaded")

    page.wait_for_timeout(5000)

    print("Title:", page.title())
    print("URL:", page.url)

    page.screenshot(
        path="output/maganghub-homepage.png",
        full_page=True
    )

    print(page.locator("body").inner_text()[:5000])

    browser.close()