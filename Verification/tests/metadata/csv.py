import csv

import pytest

from Verification.verifier.metadata.csv import CsvValidationError, load_metadata_csv
from Verification.verifier.metadata.schema import EXPECTED_FIELDS


# Build one minimal row so each check changes only the behavior under review
def minimal_row(case_id="RUSTSEC-2099-0001"):
    return {field: "" for field in EXPECTED_FIELDS} | {
        "id": case_id,
        "package": "example",
        "date": "2025-01-01",
    }


# Use the standard CSV writer so quoted and multiline values remain realistic
def write_csv(path, rows, fieldnames=EXPECTED_FIELDS):
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def check_csv_preserves_multiline_fields(tmp_path):
    row = minimal_row()
    row["versions"] = 'patched = [">= 1.0"]\nunaffected = ["< 0.9"]'
    row["references"] = '["https://example.invalid/a", "https://example.invalid/b"]'
    csv_path = tmp_path / "metadata.csv"
    write_csv(csv_path, [row])

    loaded = load_metadata_csv(csv_path)

    assert loaded == [row]
    assert "\n" in loaded[0]["versions"]


def check_csv_requires_fifteen_columns(tmp_path):
    row = minimal_row()
    fieldnames = EXPECTED_FIELDS[:-1] + ["unexpected"]
    csv_path = tmp_path / "metadata.csv"
    write_csv(
        csv_path, [{field: row.get(field, "") for field in fieldnames}], fieldnames
    )

    with pytest.raises(CsvValidationError, match="CSV schema mismatch"):
        load_metadata_csv(csv_path)


def check_csv_rejects_duplicates_and_short_rows(tmp_path):
    first = minimal_row()
    second = minimal_row()
    csv_path = tmp_path / "metadata.csv"

    # Write the second row one field short to exercise malformed-row handling
    with csv_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(EXPECTED_FIELDS)
        writer.writerow([first[field] for field in EXPECTED_FIELDS])
        writer.writerow([second[field] for field in EXPECTED_FIELDS[:-1]])

    with pytest.raises(CsvValidationError) as raised:
        load_metadata_csv(csv_path)

    message = str(raised.value)
    assert "row 3 has a missing field" in message
    assert "duplicate id RUSTSEC-2099-0001" in message


def check_csv_rejects_invalid_fields(tmp_path):
    row = minimal_row()
    row["categories"] = "not a JSON list"
    csv_path = tmp_path / "metadata.csv"
    write_csv(csv_path, [row])

    with pytest.raises(CsvValidationError, match="field categories is invalid"):
        load_metadata_csv(csv_path)


def check_source_csv_requires_102_rows(tmp_path):
    csv_path = tmp_path / "metadata.csv"
    write_csv(csv_path, [minimal_row()])

    with pytest.raises(CsvValidationError, match="expected 102 rows, got 1"):
        load_metadata_csv(csv_path, expected_rows=102)
