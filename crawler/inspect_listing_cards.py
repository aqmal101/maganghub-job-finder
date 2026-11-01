
from playwright.sync_api import sync_playwright
from pathlib import Path

URL = (
    "https://maganghub.kemnaker.go.id/"
    "magang-nasional/lowongan"
    "?keyword=it%20support&page=1"
)

Path("output").mkdir(exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    page.goto(URL, wait_until="domcontentloaded")
    page.wait_for_selector(
        'a[href*="/magang-nasional/lowongan/"]',
        timeout=20000
    )

    cards = page.locator(
        'a[href*="/magang-nasional/lowongan/"]'
    )

    results = []

    for i in range(min(cards.count(), 3)):
        card = cards.nth(i)

        data = card.evaluate("""
            el => ({
                tag: el.tagName,
                className: el.className,
                href: el.href,
                text: el.innerText,
                html: el.outerHTML
            })
        """)

        results.append(data)

    pagination = page.locator(
        'a[href*="page="], button'
    ).evaluate_all("""
        elements => elements.map(el => ({
            tag: el.tagName,
            text: (el.innerText || '').trim(),
            href: el.href || '',
            ariaLabel: el.getAttribute('aria-label'),
            disabled: el.disabled || false
        }))
    """)

    import json

    report = {
        "url": page.url,
        "cards": results,
        "pagination": pagination
    }

    Path("output/listing-cards-dom.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    print("Inspeksi selesai.")
    print("Jumlah kartu:", cards.count())
    print("File: output/listing-cards-dom.json")

    browser.close()
