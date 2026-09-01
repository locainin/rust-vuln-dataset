from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from .normalization import normalize_field
from .schema import EXPECTED_FIELDS


class CsvValidationError(ValueError):
    # Raised when metadata.csv violates the source contract
    pass


def _csv_row_errors(rows: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    seen: dict[str, int] = {}

    for row_number, row in enumerate(rows, start=2):
        # DictReader stores overflow columns under the None key
        if None in row:
            errors.append(f"row {row_number} has extra CSV fields")

        missing = [field for field in EXPECTED_FIELDS if row.get(field) is None]
        if missing:
            errors.append(f"row {row_number} has a missing field: {', '.join(missing)}")

        # IDs are the stable join key between CSV and curated cases
        row_id = row.get("id")
        if isinstance(row_id, str) and row_id.strip():
            if row_id in seen:
                errors.append(
                    f"duplicate id {row_id} at rows {seen[row_id]} and {row_number}"
                )
            else:
                seen[row_id] = row_number
        else:
            errors.append(f"row {row_number} has an empty id")

        # Parse every field now so malformed structured values fail early
        for field in EXPECTED_FIELDS:
            value = row.get(field)
            if value is None:
                continue
            try:
                normalize_field(field, value)
            except ValueError as error:
                errors.append(f"row {row_number} field {field} is invalid: {error}")

    return errors


def load_metadata_csv(
    csv_path: Path,
    expected_rows: int | None = None,
) -> list[dict[str, str]]:
    # Python's CSV parser safely handles commas, quotes, and embedded newlines
    with csv_path.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != EXPECTED_FIELDS:
            raise CsvValidationError(
                "CSV schema mismatch: "
                f"expected {EXPECTED_FIELDS!r}, got {reader.fieldnames!r}"
            )
        rows = list(reader)

    errors = _csv_row_errors(rows)
    if expected_rows is not None and len(rows) != expected_rows:
        errors.insert(0, f"expected {expected_rows} rows, got {len(rows)}")

    if errors:
        raise CsvValidationError("\n".join(errors))

    # Strip DictReader's broader value type after validation
    return [{field: row[field] for field in EXPECTED_FIELDS} for row in rows]
