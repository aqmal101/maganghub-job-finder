from playwright.sync_api import sync_playwright

from crawler.detail import find_section

URL = "https://maganghub.kemnaker.go.id/magang-nasional/lowongan/technical-support-01a181aa-eb45-73b6-8911-5fc2e6d68149"

if not URL.startswith("https://"):
    raise ValueError("Silakan masukkan URL detail lowongan MagangHub yang valid.")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()

    page.goto(
        URL,
        wait_until="domcontentloaded",
        timeout=60000
    )

    page.wait_for_timeout(2000)

    section = find_section(
        page, "Skill yang Bakal Kamu Dapat"
    )

    if section is None:
        print("Section kurikulum tidak ditemukan.")
    else:
        button = section.locator(
            "button[aria-controls]"
        ).first

        if button.count() == 0:
            print("Tombol accordion tidak ditemukan.")
        else:
            if button.get_attribute("aria-expanded") == "false":
                button.click()
                page.wait_for_timeout(300)

            panel_id = button.get_attribute("aria-controls")

            if not panel_id:
                print("Panel ID tidak ditemukan.")
            else:
                panel = page.locator(f"#{panel_id}")

                

                print("\n=== INFORMASI PANEL ===")
                print("Panel ID:", panel_id)
                print("Jumlah child:", panel.locator("> *").count())

                print("\n=== STRUKTUR HTML PANEL ===")
                print(panel.evaluate("(el) => el.outerHTML"))

                print("\n=== ELEMEN BUTTON ===")
                buttons = panel.locator("button")

                print("Jumlah button:", buttons.count())

                for i in range(buttons.count()):
                    button_item = buttons.nth(i)

                    print(f"\n--- BUTTON {i + 1} ---")
                    print("Text:", button_item.inner_text())
                    print("HTML:", button_item.evaluate("(el) => el.outerHTML"))

    browser.close()