# Coordinate verification and summarize the plain terminal report

import sys
from pathlib import Path
from typing import TextIO

from .coverage import coverage
from .metadata.cases import discover_case_dirs
from .metadata.csv import CsvValidationError, load_metadata_csv
from .metadata.inspection import inspect
from .metadata.normalization import affected_function_names
from .metadata.schema import SOURCE_ROW_COUNT
from .pairs import check_structure
from .presentation.console import Colorizer
from .presentation.metadata import metadata_report
from .presentation.pairs import structure_report
from .presentation.report import check


def run_verification(
    csv_path: Path,
    cases_dir: Path,
    stream: TextIO = sys.stdout,
    *,
    expected_source_rows: int = SOURCE_ROW_COUNT,
    excluded_cases: set[str] | frozenset[str] = frozenset(),
    color: bool | None = None,
) -> int:
    colors = Colorizer(stream, enabled=color)

    try:
        rows = load_metadata_csv(csv_path, expected_rows=expected_source_rows)
    except (OSError, CsvValidationError) as error:
        check("CSV schema/data", "FAIL", str(error), stream, colors, indent="")
        return 1

    rows_by_id = {row["id"]: row for row in rows}
    case_dirs = discover_case_dirs(cases_dir)
    coverage_errors = coverage(
        set(rows_by_id), {path.name for path in case_dirs}, set(excluded_cases)
    )

    print(f"RustXec source: {len(rows)}", file=stream)
    print(f"Curated cases:  {len(case_dirs)}", file=stream)
    if coverage_errors:
        for error in coverage_errors:
            check("Seed coverage", "FAIL", error, stream, colors)
    else:
        check("Seed coverage", "OK", "all cases accounted for", stream, colors)
    print(file=stream)

    verified = 0
    failed = 0
    affected_total = 0
    pair_total = 0
    snippet_total = 0
    seen_yaml_ids: set[str] = set()

    for index, case_dir in enumerate(case_dirs, start=1):
        source_row = rows_by_id.get(case_dir.name)
        package = source_row["package"] if source_row else "unknown package"
        print(
            f"[{index}/{len(case_dirs)}] {case_dir.name} — {package}",
            file=stream,
        )
        print(file=stream)

        metadata = inspect(case_dir, rows_by_id)
        metadata_report(metadata, stream, colors)
        yaml_id = metadata.identifier
        if yaml_id is not None:
            if yaml_id in seen_yaml_ids:
                error = f"duplicate curated case id: {yaml_id}"
                metadata.errors.append(error)
                check("Metadata", "FAIL", error, stream, colors)
            seen_yaml_ids.add(yaml_id)

        functions = affected_function_names(metadata.row) if metadata.row else ()
        affected_count = len(functions)
        structure = check_structure(case_dir, functions)
        structure_report(structure, affected_count, stream, colors)

        affected_total += affected_count
        pair_total += structure.pair_count
        snippet_total += structure.vulnerable_snippet_count

        case_errors = metadata.errors + list(structure.errors)
        if case_errors:
            failed += 1
            check("RESULT", "FAIL", "FAILED", stream, colors)
        else:
            verified += 1
            check("RESULT", "OK", "VERIFIED", stream, colors)
        print(file=stream)

    print("=" * 72, file=stream)
    print("Verification complete", file=stream)
    print(file=stream)
    print(f"  RustXec source cases       {len(rows):>3}", file=stream)
    print(f"  Curated cases              {len(case_dirs):>3}", file=stream)
    print(f"  RustSec affected functions {affected_total:>3}", file=stream)
    print(f"  Changed pair groups        {pair_total:>3}", file=stream)
    print(f"  Vulnerable snippets        {snippet_total:>3}", file=stream)
    print(f"  Verified cases             {verified:>3}", file=stream)
    print(f"  Failed cases               {failed:>3}", file=stream)

    return 1 if failed or coverage_errors else 0
