from pathlib import Path
from playwright.sync_api import sync_playwright

URL = (
    "https://maganghub.kemnaker.go.id/"
    "magang-nasional/lowongan?keyword=it%20support&page=1"
)

OUTPUT = Path("output")
OUTPUT.mkdir(exist_ok=True)


with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()

    page.goto(URL, wait_until="domcontentloaded")
    page.wait_for_timeout(3000)

    # Cari link menuju halaman detail lowongan
    cards = page.locator(
        'a[href*="/magang-nasional/lowongan/"]'
    )

    count = cards.count()

    print(f"Jumlah link detail ditemukan: {count}")

    if count == 0:
        print("Link detail tidak ditemukan.")
        browser.close()
        raise SystemExit

    # Ambil maksimal 3 kartu untuk diperiksa
    card_html = []

    for i in range(min(count, 3)):
        card = cards.nth(i)

        info = card.evaluate("""
            el => {
                let parents = [];
                let current = el;

                for (let i = 0; i < 4 && current; i++) {
                    parents.push({
                        tag: current.tagName,
                        className: current.className,
                        html: current.outerHTML
                    });

                    current = current.parentElement;
                }

                return {
                    href: el.href,
                    text: el.innerText,
                    parents: parents
                };
            }
        """)

        card_html.append(info)

    # Simpan struktur HTML kartu
    (OUTPUT / "card-inspection.txt").write_text(
        str(card_html),
        encoding="utf-8"
    )

    print("\n=== KARTU LOWONGAN ===")

    for i, card in enumerate(card_html, start=1):
        print(f"\nKartu {i}")
        print("URL:", card["href"])
        print("Text:", card["text"][:500])

        for parent in card["parents"]:
            print(
                "Parent:",
                parent["tag"],
                parent["className"]
            )

    # Buka detail lowongan pertama
    detail_url = card_html[0]["href"]

    print("\nMembuka detail:", detail_url)

    page.goto(detail_url, wait_until="domcontentloaded")
    page.wait_for_timeout(3000)

    detail_text = page.locator("body").inner_text()

    (OUTPUT / "detail-page.txt").write_text(
        detail_text,
        encoding="utf-8"
    )

    (OUTPUT / "detail-page.html").write_text(
        page.content(),
        encoding="utf-8"
    )

    page.screenshot(
        path=str(OUTPUT / "detail-page.png"),
        full_page=True
    )

    print("\n=== DETAIL LOWONGAN ===")
    print(detail_text[:10000])

    print("\nFile berhasil dibuat:")
    print("- output/card-inspection.txt")
    print("- output/detail-page.txt")
    print("- output/detail-page.html")
    print("- output/detail-page.png")

    browser.close()