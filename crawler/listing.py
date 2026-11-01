
# crawler/listing.py

import re
from playwright.sync_api import Page


BASE_URL = (
    "https://maganghub.kemnaker.go.id/"
    "magang-nasional/lowongan"
)

CARD_SELECTOR = (
    'a.group.block.h-full'
    '[href*="/magang-nasional/lowongan/"]'
)


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def parse_number(value: str):
    """Ambil angka dari teks seperti 'Kuota: 1'."""
    match = re.search(r"\d+", value or "")
    return int(match.group()) if match else None


def parse_card(card) -> dict:
    """Ekstrak data dari satu kartu lowongan."""

    data = card.evaluate("""
        el => {
            const text = selector =>
                el.querySelector(selector)?.innerText?.trim() || '';

            const iconText = iconSelector => {
                const icon = el.querySelector(iconSelector);
                if (!icon) return '';

                const wrapper = icon.parentElement;
                return wrapper?.innerText?.trim() || '';
            };

            const badges = Array.from(
                el.querySelectorAll('div.inline-flex')
            ).map(item => item.innerText.trim());

            const opportunity = Array.from(
                el.querySelectorAll('span.inline-flex')
            ).map(item => item.innerText.trim())
             .find(value => /Peluang/i.test(value)) || '';

            const holidayHeading = Array.from(
                el.querySelectorAll('p')
            ).find(item => item.innerText.trim() === 'Hari Libur');

            const holidays = holidayHeading
                ? Array.from(
                    holidayHeading.parentElement.querySelectorAll(
                        'div.inline-flex'
                    )
                  ).map(item => item.innerText.trim())
                : [];

            return {
                title: text('h3'),
                company: text('p.text-sm.font-medium'),
                majors_raw: text('p.truncate'),
                location: iconText('svg.lucide-map-pin'),
                education: iconText('svg.lucide-graduation-cap'),
                work_schedule_raw: iconText('svg.lucide-calendar'),
                badges: badges,
                opportunity: opportunity,
                holidays: holidays,
                url: el.href,
                logo_url: el.querySelector('img')?.src || ''
            };
        }
    """)

    # Normalisasi nilai angka.
    quota_raw = next(
        (
            item for item in data["badges"]
            if item.lower().startswith("kuota:")
        ),
        ""
    )

    applicants_raw = next(
        (
            item for item in data["badges"]
            if item.lower().startswith("pelamar:")
        ),
        ""
    )

    data["quota"] = parse_number(quota_raw)
    data["applicants"] = parse_number(applicants_raw)

    data["work_days_per_week"] = parse_number(
        data["work_schedule_raw"]
    )

    # Pisahkan daftar program studi.
    data["majors"] = [
        normalize_text(item)
        for item in data["majors_raw"].split(",")
        if normalize_text(item)
    ]

    # Bersihkan field teks.
    for key in [
        "title",
        "company",
        "location",
        "education",
        "work_schedule_raw",
        "opportunity",
    ]:
        data[key] = normalize_text(data[key])

    return data



def scrape_listing_page(page: Page, keyword: str, page_number: int = 1):
    """Ambil semua kartu lowongan dari satu halaman."""

    page.goto(
        BASE_URL,
        wait_until="domcontentloaded",
        timeout=60000
    )

    # Isi pencarian menggunakan placeholder yang sudah
    # ditemukan saat inspeksi halaman.
    search_input = page.get_by_placeholder(
        "Cari berdasarkan posisi atau nama penyelenggara..."
    )

    search_input.fill(keyword)
    search_input.press("Enter")

    # Tunggu hasil pencarian.
    page.wait_for_timeout(1500)

    # Navigasi halaman melalui query parameter.
    if page_number > 1:
        page.goto(
            f"{BASE_URL}?keyword={keyword.replace(' ', '%20')}"
            f"&page={page_number}",
            wait_until="domcontentloaded",
            timeout=60000
        )

    page.wait_for_selector(
        CARD_SELECTOR,
        timeout=20000
    )

    cards = page.locator(CARD_SELECTOR)

    results = []

    for index in range(cards.count()):
        item = parse_card(cards.nth(index))
        item["keyword"] = keyword
        item["page"] = page_number
        results.append(item)

    return results
