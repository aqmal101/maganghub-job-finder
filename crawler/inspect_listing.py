from pathlib import Path
from playwright.sync_api import sync_playwright

BASE_URL = "https://maganghub.kemnaker.go.id/"

OUTPUT_DIR = Path("output")
LOG_DIR = Path("logs")

OUTPUT_DIR.mkdir(exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)


def inspect_page(page):
    # Informasi dasar halaman
    title = page.title()
    url = page.url
    body_text = page.locator("body").inner_text()

    # Daftar link
    links = page.locator("a").evaluate_all("""
        elements => elements.map(el => ({
            text: (el.innerText || el.textContent || "").trim(),
            href: el.href
        })).filter(item => item.text || item.href)
    """)

    # Daftar input
    inputs = page.locator("input").evaluate_all("""
        elements => elements.map(el => ({
            type: el.type,
            name: el.name,
            placeholder: el.placeholder,
            ariaLabel: el.getAttribute("aria-label")
        }))
    """)

    # Daftar tombol
    buttons = page.locator("button").evaluate_all("""
        elements => elements.map(el => ({
            text: (el.innerText || el.textContent || "").trim(),
            ariaLabel: el.getAttribute("aria-label"),
            type: el.type
        }))
    """)

    # Simpan HTML dan screenshot
    page.screenshot(
        path=str(OUTPUT_DIR / "listing-page.png"),
        full_page=True
    )

    (OUTPUT_DIR / "listing-page.html").write_text(
        page.content(),
        encoding="utf-8"
    )

    # Simpan hasil inspeksi
    report = f"""
PAGE TITLE
{title}

PAGE URL
{url}

BODY TEXT
{body_text[:15000]}

LINKS
{links[:150]}

INPUTS
{inputs}

BUTTONS
{buttons}
"""

    report_path = LOG_DIR / "listing-inspection.txt"
    report_path.write_text(report, encoding="utf-8")

    print("\n=== HASIL INSPEKSI ===")
    print("Title:", title)
    print("URL:", url)
    print("Jumlah link:", len(links))
    print("Jumlah input:", len(inputs))
    print("Jumlah tombol:", len(buttons))
    print("HTML:", OUTPUT_DIR / "listing-page.html")
    print("Screenshot:", OUTPUT_DIR / "listing-page.png")
    print("Laporan:", report_path)


with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()

    page.goto(BASE_URL, wait_until="domcontentloaded")
    page.wait_for_timeout(3000)

    print("\nBrowser sudah terbuka.")
    print("Silakan lakukan secara manual:")
    print("1. Buka halaman pencarian lowongan.")
    print("2. Masukkan salah satu keyword, misalnya Frontend Developer.")
    print("3. Jalankan pencarian sampai daftar lowongan muncul.")
    print("4. Kembali ke terminal, lalu tekan Enter.")

    input("\nTekan Enter setelah hasil pencarian tampil... ")

    page.wait_for_timeout(2000)
    inspect_page(page)

    browser.close()