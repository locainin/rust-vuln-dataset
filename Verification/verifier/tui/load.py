# Load one consistent data set for the interactive review screen

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from typing import Any

from ..coverage import coverage
from ..metadata.cases import discover_case_dirs
from ..metadata.csv import load_metadata_csv
from ..metadata.inspection import Metadata, inspect
from ..metadata.normalization import affected_function_names
from ..metadata.schema import EXPECTED_FIELDS, SOURCE_ROW_COUNT
from ..pairs import check_structure
from .types import MISSING, InteractiveCase, InteractiveData, MetadataField


def _metadata_fields(result: Metadata) -> tuple[MetadataField, ...]:
    # One field row per schema entry keeps malformed documents easy to compare
    issues: dict[str, dict[str, Any]] = {}
    for issue in result.issues:
        field = issue["field"]
        if field not in EXPECTED_FIELDS:
            continue
        current = issues.get(field)
        if current is None or issue["status"] == "FAIL":
            issues[field] = issue

    can_compare = result.row is not None and isinstance(result.data, dict)
    fields: list[MetadataField] = []
    for field in EXPECTED_FIELDS:
        issue = issues.get(field)
        status = issue["status"] if issue else "OK" if can_compare else "FAIL"
        value = (
            result.data.get(field, MISSING)
            if isinstance(result.data, dict)
            else MISSING
        )
        fields.append(MetadataField(field, status, value))
    return tuple(fields)


def _case(
    case_dir: Path,
    package: str,
    metadata: Metadata,
    duplicate: bool,
) -> InteractiveCase:
    # Prefixes make the source of a visible failure clear in a compact view
    errors = [f"metadata: {error}" for error in metadata.errors]
    if duplicate and metadata.identifier is not None:
        errors.append(f"metadata: duplicate curated case id: {metadata.identifier}")

    functions = affected_function_names(metadata.row) if metadata.row else ()
    structure = check_structure(case_dir, functions)
    errors.extend(
        f"structure: {error}"
        for error in structure.errors
        if error not in metadata.errors
    )
    affected_count = len(functions)
    return InteractiveCase(
        identifier=case_dir.name,
        package=package,
        metadata_fields=_metadata_fields(metadata),
        affected_count=affected_count,
        structure=structure,
        errors=tuple(errors),
    )


def load_data(
    csv_path: Path,
    cases_dir: Path,
    *,
    expected_source_rows: int | None = SOURCE_ROW_COUNT,
    excluded_cases: Iterable[str] = (),
) -> InteractiveData:
    # Read CSV, metadata, and pair checks once for one TUI session

    # A fixed source row count catches a stale metadata snapshot before curses starts
    rows = load_metadata_csv(csv_path, expected_rows=expected_source_rows)
    rows_by_id = {row["id"]: row for row in rows}

    # Directory discovery keeps cases visible even when metadata is missing
    case_dirs = discover_case_dirs(cases_dir)

    # Coverage is calculated once because it describes the whole session
    coverage_errors = tuple(
        coverage(
            set(rows_by_id),
            {path.name for path in case_dirs},
            set(excluded_cases),
        )
    )

    # Keep the first occurrence as the canonical case and mark later repeats
    seen_ids: set[str] = set()
    cases: list[InteractiveCase] = []
    for case_dir in case_dirs:
        # Metadata inspection and pair checking feed the same visible case block
        metadata = inspect(case_dir, rows_by_id)
        duplicate = metadata.identifier is not None and metadata.identifier in seen_ids
        if metadata.identifier is not None:
            seen_ids.add(metadata.identifier)
        # The heading identifies the directory even if its YAML names another case
        source_row = rows_by_id.get(case_dir.name)
        package = source_row["package"] if source_row else "unknown package"
        cases.append(_case(case_dir, package, metadata, duplicate))
    return InteractiveData(tuple(cases), coverage_errors)
