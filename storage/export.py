
import csv
import json
from pathlib import Path


def serialize_csv_value(value):
    """
    Ubah nilai Python menjadi nilai yang bisa ditulis ke CSV.
    List dan dictionary disimpan sebagai JSON agar strukturnya tidak hilang.
    """
    if value is None:
        return ""

    if isinstance(value, (dict, list)):
        return json.dumps(
            value,
            ensure_ascii=False,
        )

    return value


def get_csv_columns(rows, default_columns=None):
    """
    Gabungkan semua key dari rows menjadi header CSV.
    Urutan kolom mengikuti kemunculan key pertama.
    """
    columns = list(default_columns or [])

    for row in rows:
        for key in row:
            if key not in columns:
                columns.append(key)

    return columns


def write_csv(file_path: Path, rows: list[dict], default_columns=None):
    """Simpan kumpulan dictionary ke file CSV."""
    columns = get_csv_columns(rows, default_columns)

    with file_path.open(
        "w",
        newline="",
        encoding="utf-8-sig",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=columns,
            extrasaction="ignore",
        )

        writer.writeheader()

        for row in rows:
            serialized_row = {
                key: serialize_csv_value(value)
                for key, value in row.items()
            }

            writer.writerow(serialized_row)


def export_batch(
    records: list[dict],
    output_dir: str = "output",
    json_filename: str = "detail_batch_test.json",
) -> dict:
    """
    Ekspor hasil batch crawler ke JSON dan CSV.

    JSON:
        output/detail_batch_test.json

    CSV:
        output/csv/listings.csv
        output/csv/details.csv
        output/csv/curriculum.csv
    """
    output_path = Path(output_dir)
    csv_path = output_path / "csv"

    output_path.mkdir(parents=True, exist_ok=True)
    csv_path.mkdir(parents=True, exist_ok=True)

    # 1. Simpan seluruh hasil ke JSON.
    json_file = output_path / json_filename

    json_file.write_text(
        json.dumps(
            records,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    listing_rows = []
    detail_rows = []
    curriculum_rows = []

    # 2. Pisahkan data listing, detail, dan kurikulum.
    for record in records:
        if not isinstance(record, dict):
            continue

        listing = record.get("listing")
        detail = record.get("detail")

        if not isinstance(listing, dict):
            listing = {}

        if not isinstance(detail, dict):
            detail = {}

        scraping_status = record.get(
            "scraping_status",
            "",
        )

        # Data listing.
        listing_row = dict(listing)
        listing_row["scraping_status"] = scraping_status
        listing_rows.append(listing_row)

        # Data detail.
        # Kurikulum dipisahkan ke curriculum.csv.
        detail_row = {
            key: value
            for key, value in detail.items()
            if key != "curriculum"
        }

        detail_row["url"] = listing.get("url", "")
        detail_row["scraping_status"] = scraping_status
        detail_row["validation_errors"] = record.get(
            "validation_errors",
            [],
        )
        detail_row["audit_warnings"] = record.get(
            "audit_warnings",
            [],
        )
        detail_row["error"] = record.get("error", "")

        detail_rows.append(detail_row)

        # Data kurikulum.
        curriculum = detail.get("curriculum", [])

        if not isinstance(curriculum, list):
            continue

        for item in curriculum:
            if not isinstance(item, dict):
                continue

            curriculum_row = {
                "listing_url": listing.get("url", ""),
                "listing_company": listing.get("company", ""),
                "detail_title": detail.get("title", ""),
            }

            curriculum_row.update(item)
            curriculum_rows.append(curriculum_row)

    # 3. Simpan masing-masing CSV.
    listing_file = csv_path / "listings.csv"
    detail_file = csv_path / "details.csv"
    curriculum_file = csv_path / "curriculum.csv"

    write_csv(
        listing_file,
        listing_rows,
        default_columns=["url", "company", "scraping_status"],
    )

    write_csv(
        detail_file,
        detail_rows,
        default_columns=[
            "url",
            "title",
            "description",
            "qualifications",
            "scraping_status",
            "validation_errors",
            "audit_warnings",
            "error",
        ],
    )

    write_csv(
        curriculum_file,
        curriculum_rows,
        default_columns=[
            "listing_url",
            "listing_company",
            "detail_title",
            "order",
            "title",
            "type",
            "month",
            "duration",
            "description",
        ],
    )

    return {
        "json": json_file,
        "listings_csv": listing_file,
        "details_csv": detail_file,
        "curriculum_csv": curriculum_file,
        "listing_count": len(listing_rows),
        "detail_count": len(detail_rows),
        "curriculum_count": len(curriculum_rows),
    }
