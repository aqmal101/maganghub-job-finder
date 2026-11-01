import re
from playwright.sync_api import Page


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def find_section(page: Page, heading_text: str):
    heading = page.locator("h2").filter(
        has_text=re.compile(
            rf"^\s*{re.escape(heading_text)}\s*$"
        )
    )

    if heading.count() == 0:
        return None

    return heading.first.locator("xpath=..")


def get_section_text(page: Page, heading_text: str) -> str:
    """Ambil isi section tanpa memasukkan judul H2."""
    section = find_section(page, heading_text)

    if section is None:
        return ""

    paragraphs = section.locator("p").all_inner_texts()

    if paragraphs:
        return "\n".join(
            normalize_text(item)
            for item in paragraphs
            if normalize_text(item)
        )

    # Fallback untuk section yang tidak menggunakan elemen p.
    content = section.locator(":scope > div").first

    if content.count():
        return normalize_text(content.inner_text())

    return ""


def get_qualification_items(page: Page) -> list[str]:
    """Ambil setiap kualifikasi sebagai item terpisah."""
    section = find_section(page, "Kualifikasi")

    if section is None:
        return []

    rows = section.locator(
        "div.space-y-3 > div.flex.items-start"
    )

    result = []

    for i in range(rows.count()):
        row = rows.nth(i)

        # Menggabungkan node teks dengan pemisah agar
        # teks sebelum dan sesudah <strong> tidak menyatu.
        value = row.locator("span").first.evaluate("""
            el => Array.from(el.childNodes)
                .map(node => node.textContent || '')
                .join(' ')
        """)

        value = normalize_text(value)

        if value:
            result.append(value)

    return result


def get_sidebar_data(page: Page) -> dict:
    rows = page.locator(
        "div.flex.items-center.justify-between"
    ).evaluate_all("""
        elements => elements.map(row => {
            const spans = row.querySelectorAll(':scope > span');

            if (spans.length < 2) return null;

            return {
                label: (spans[0].innerText || '').trim(),
                value: (spans[1].innerText || '').trim()
            };
        }).filter(Boolean)
    """)

    return {
        normalize_text(item["label"]):
        normalize_text(item["value"])
        for item in rows
    }


def get_curriculum(page: Page) -> str:
    section = find_section(
        page, "Skill yang Bakal Kamu Dapat"
    )

    if section is None:
        return ""

    button = section.locator(
        "button[aria-controls]"
    ).first

    if button.count() == 0:
        return ""

    if button.get_attribute("aria-expanded") == "false":
        button.click()
        page.wait_for_timeout(300)

    panel_id = button.get_attribute("aria-controls")

    if not panel_id:
        return ""

    panel = page.locator(f"#{panel_id}")

    if panel.count() == 0:
        return ""

    return normalize_text(panel.inner_text())


def get_opportunity(page: Page) -> str:
    """Ambil badge peluang, bukan baris sidebar."""
    badge = page.get_by_text(
        re.compile(
            r"Peluang\s+(?:Sangat\s+)?(?:Besar|Kecil|Sedang)"
            r"\s*\(\s*\d+\s*%\s*\)"
        )
    )

    if badge.count() == 0:
        return ""

    return normalize_text(badge.first.inner_text())


def parse_detail(page: Page, url: str) -> dict:
    page.goto(url, wait_until="domcontentloaded")

    # Tunggu elemen utama muncul.
    page.locator("h1").wait_for(timeout=15000)

    sidebar = get_sidebar_data(page)

    title = normalize_text(
        page.locator("h1").first.inner_text()
    )

    return {
        "title": title,
        "url": page.url,
        "description": get_section_text(
            page, "Deskripsi Lowongan"
        ),
        "qualifications": get_qualification_items(page),
        "skills": get_curriculum(page),
        "holidays": get_section_text(
            page, "Hari Libur"
        ),
        "internship_location_detail": get_section_text(
            page, "Lokasi Magang"
        ),
        "work_days_per_week": sidebar.get(
            "Durasi Magang", ""
        ),
        "location": sidebar.get(
            "Lokasi Magang", ""
        ),
        "interview_type": sidebar.get(
            "Tipe Wawancara", ""
        ),
        "quota": sidebar.get("Kuota", ""),
        "applicants": sidebar.get("Pelamar", ""),
        "allowance_source": sidebar.get(
            "Tunjangan", ""
        ),
        "opportunity": get_opportunity(page),
    }