from pathlib import Path
from playwright.sync_api import sync_playwright

URL = (
    "https://maganghub.kemnaker.go.id/"
    "magang-nasional/lowongan/"
    "it-support-intern-%E2%80%93-store-"
    "01a15e11-75f8-70f7-ae83-2b4a75f75f19"
)

OUTPUT = Path("output")
OUTPUT.mkdir(exist_ok=True)

LABELS = [
    "Deskripsi Lowongan",
    "Kualifikasi",
    "Skill yang Bakal Kamu Dapat",
    "Hari Libur",
    "Lokasi Magang",
    "Durasi Magang",
    "Tipe Wawancara",
    "Kuota",
    "Pelamar",
    "Tunjangan",
    "Alur Lamaran",
]


with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()

    page.goto(URL, wait_until="domcontentloaded")
    page.wait_for_timeout(3000)

    result = page.evaluate("""
        (labels) => {
            const normalize = value =>
                (value || "").replace(/\\\\s+/g, " ").trim();

            const output = {};

            for (const label of labels) {
                const candidates = Array.from(
                    document.querySelectorAll("body *")
                ).filter(el =>
                    normalize(el.innerText) === label
                );

                const element = candidates
                    .filter(el => el.children.length <= 2)
                    .sort((a, b) =>
                        a.outerHTML.length - b.outerHTML.length
                    )[0];

                if (!element) {
                    output[label] = {
                        found: false
                    };
                    continue;
                }

                let parents = [];
                let current = element;

                for (let i = 0; i < 4 && current; i++) {
                    parents.push({
                        tag: current.tagName,
                        className:
                            typeof current.className === "string"
                                ? current.className
                                : "",
                        text: normalize(current.innerText).slice(0, 1200),
                        html: current.outerHTML.slice(0, 5000)
                    });

                    current = current.parentElement;
                }

                output[label] = {
                    found: true,
                    parents
                };
            }

            const headings = Array.from(
                document.querySelectorAll(
                    "h1, h2, h3, h4, [role='heading']"
                )
            ).map(el => ({
                tag: el.tagName,
                text: normalize(el.innerText),
                className: el.className
            }));

            return {
                title: document.title,
                url: location.href,
                headings,
                sections: output
            };
        }
    """, LABELS)

    import json

    report = json.dumps(
        result,
        indent=2,
        ensure_ascii=False
    )

    (OUTPUT / "detail-dom-inspection.json").write_text(
        report,
        encoding="utf-8"
    )

    print(report[:12000])

    browser.close()