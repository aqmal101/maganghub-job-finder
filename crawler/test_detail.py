import json
from playwright.sync_api import sync_playwright

from crawler.detail import parse_detail

URL = (
    "https://maganghub.kemnaker.go.id/"
    "magang-nasional/lowongan/"
    "it-support-intern-%E2%80%93-store-"
    "01a15e11-75f8-70f7-ae83-2b4a75f75f19"
)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    result = parse_detail(page, URL)

    print(json.dumps(
        result,
        indent=2,
        ensure_ascii=False
    ))

    browser.close()