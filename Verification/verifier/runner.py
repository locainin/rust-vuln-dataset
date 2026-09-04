from __future__ import annotations

import pprint
import sys
from pathlib import Path
from typing import Any, TextIO

import yaml

from .case_metadata import (
    case_id,
    discover_case_dirs,
    is_valid_case_name,
    load_yaml,
)
from .comparison import compare_row
from .console import Colorizer, snapshot_match_status
from .csv_source import CsvValidationError, load_metadata_csv
from .dataset_structure import PairResult, StructureResult, check_structure
from .normalization import affected_function_names
from .schema import EXPECTED_FIELDS, SOURCE_ROW_COUNT
from .source_diff import unified_source_diff


def _display(value: Any) -> str:
    # Failure values use stable formatting without hiding null
    if value is None:
        return "null"
    return pprint.pformat(value, sort_dicts=True, width=110)


def _found_display(value: Any) -> str:
    # Found values stay compact enough for one report line
    if isinstance(value, list):
        return ", ".join(str(item) for item in value)
    return str(value)


def _print_check(
    label: str,
    status: str,
    detail: str,
    stream: TextIO,
    colors: Colorizer,
    indent: str = "  ",
) -> None:
    suffix = f" {detail}" if detail else ""
    print(f"{indent}{label:<28}{colors.status(status)}{suffix}", file=stream)


def _metadata_report(
    case_dir: Path,
    rows_by_id: dict[str, dict[str, Any]],
    stream: TextIO,
    colors: Colorizer,
) -> tuple[list[str], list[dict[str, Any]], dict[str, Any] | None, str | None]:
    errors: list[str] = []
    found: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    yaml_path = case_dir / "metadata.yaml"

    if not yaml_path.is_file():
        _print_check("metadata.yaml", "FAIL", "missing", stream, colors)
        return ["metadata.yaml is missing"], found, None, None

    try:
        data = load_yaml(yaml_path)
    except (OSError, yaml.YAMLError) as error:
        _print_check("metadata.yaml", "FAIL", str(error), stream, colors)
        return [f"metadata.yaml: {error}"], found, None, None

    # Directory identity is verified independently from YAML schema
    if not is_valid_case_name(case_dir.name):
        errors.append(f"invalid case directory name: {case_dir.name}")

    yaml_id = case_id(data)
    if yaml_id is None:
        errors.append("YAML id is missing or invalid")
    elif yaml_id != case_dir.name:
        errors.append(
            f"directory name {case_dir.name!r} does not match YAML id {yaml_id!r}"
        )

    # A case can only be compared after its canonical id joins to one CSV row
    csv_row = rows_by_id.get(yaml_id) if yaml_id else None
    if csv_row is None:
        errors.append("no matching CSV entry")
    else:
        issues = compare_row(csv_row, data)
        found = [issue for issue in issues if issue["status"] == "FOUND"]
        failures = [issue for issue in issues if issue["status"] == "FAIL"]
        errors.extend(f"{issue['field']}: {issue['reason']}" for issue in failures)

    if errors:
        _print_check(
            "Metadata",
            "FAIL",
            f"{len(errors)} issue(s)",
            stream,
            colors,
        )

        # Comparison failures include values while identity failures stay concise
        failures_by_message = {
            f"{issue['field']}: {issue['reason']}": issue for issue in failures
        }
        for error in errors:
            matching = failures_by_message.get(error)
            if matching is None:
                _print_check("metadata", "FAIL", error, stream, colors, indent="    ")
                continue

            _print_check(
                matching["field"],
                "FAIL",
                "",
                stream,
                colors,
                indent="    ",
            )
            print(f"      CSV:  {_display(matching['csv'])}", file=stream)
            print(f"      YAML: {_display(matching['yaml'])}", file=stream)
    else:
        _print_check(
            "Metadata",
            "OK",
            f"{len(EXPECTED_FIELDS)} fields",
            stream,
            colors,
        )

    # Found enrichment is visible but never counted as a failure
    for issue in found:
        _print_check(
            issue["field"],
            "FOUND",
            _found_display(issue["found"]),
            stream,
            colors,
            indent="    ",
        )

    return errors, found, csv_row, yaml_id


def _print_diff(
    vulnerable: str | None,
    fixed: str | None,
    stream: TextIO,
    colors: Colorizer,
) -> None:
    if vulnerable is None or fixed is None:
        return

    print(file=stream)
    for line in unified_source_diff(vulnerable, fixed):
        print(f"    {colors.diff_line(line)}", file=stream)


def _print_pair(
    pair: PairResult,
    stream: TextIO,
    colors: Colorizer,
) -> None:
    print(f"  {pair.name}", file=stream)

    vulnerable_status, vulnerable_detail = snapshot_match_status(
        "before.rs",
        pair.vulnerable_range,
        pair.vulnerable_match_count,
    )
    fixed_status, fixed_detail = snapshot_match_status(
        "after.rs",
        pair.fixed_range,
        pair.fixed_match_count,
    )
    if pair.fixed_removed:
        fixed_status = "REMOVED"
        fixed_detail = ""
    _print_check(
        "vulnerable snapshot match",
        vulnerable_status,
        vulnerable_detail,
        stream,
        colors,
        indent="    ",
    )
    _print_check(
        "fixed snapshot match",
        fixed_status,
        fixed_detail,
        stream,
        colors,
        indent="    ",
    )

    pair_difference_status = "OK" if pair.vulnerable_fixed_differ is True else "FAIL"
    _print_check(
        "vulnerable != fixed",
        pair_difference_status,
        "",
        stream,
        colors,
        indent="    ",
    )

    before_after_status = "OK" if pair.before_after_differ is True else "FAIL"
    _print_check(
        "before != after",
        before_after_status,
        "",
        stream,
        colors,
        indent="    ",
    )

    _print_diff(pair.vulnerable_text, pair.fixed_text, stream, colors)

    for variant in pair.variants:
        variant_status, variant_detail = snapshot_match_status(
            "before.rs",
            variant.source_range,
            variant.source_match_count,
        )
        if variant.differs_from_fixed is not True:
            variant_status = "FAIL"
        _print_check(
            f"{variant.name} variant",
            variant_status,
            variant_detail,
            stream,
            colors,
            indent="    ",
        )
        _print_diff(variant.text, pair.fixed_text, stream, colors)

    # Surface errors not already obvious from the compact pair checks
    represented_fragments = (
        "not an exact substring",
        "are identical",
    )
    for error in pair.errors:
        if any(fragment in error for fragment in represented_fragments):
            continue
        _print_check(
            "source validation",
            "FAIL",
            error,
            stream,
            colors,
            indent="    ",
        )

    print(file=stream)


def _structure_report(
    result: StructureResult,
    affected_count: int,
    stream: TextIO,
    colors: Colorizer,
) -> None:
    _print_check(
        "RustSec affected functions",
        "INFO",
        str(affected_count),
        stream,
        colors,
    )
    _print_check(
        "Changed pairs",
        "INFO",
        str(result.pair_count),
        stream,
        colors,
    )

    variant_count = result.vulnerable_snippet_count - result.pair_count
    if variant_count:
        _print_check(
            "Vulnerable variants",
            "INFO",
            str(variant_count),
            stream,
            colors,
        )
    print(file=stream)

    for pair in result.pairs:
        _print_pair(pair, stream, colors)

    # Case-level layout failures have no pair block where they can be shown
    for error in result.errors:
        if error.startswith(("pairs/ is ", "pairs/ has ")):
            _print_check("Dataset structure", "FAIL", error, stream, colors)


def run_verification(
    csv_path: Path,
    cases_dir: Path,
    stream: TextIO = sys.stdout,
    *,
    expected_source_rows: int = SOURCE_ROW_COUNT,
    color: bool | None = None,
) -> int:
    colors = Colorizer(stream, enabled=color)

    try:
        rows = load_metadata_csv(csv_path, expected_rows=expected_source_rows)
    except (OSError, CsvValidationError) as error:
        _print_check("CSV schema/data", "FAIL", str(error), stream, colors, indent="")
        return 1

    rows_by_id = {row["id"]: row for row in rows}
    case_dirs = discover_case_dirs(cases_dir)
    print(f"RustXec source: {len(rows)}", file=stream)
    print(f"Curated cases:  {len(case_dirs)}", file=stream)
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

        metadata_errors, _, csv_row, yaml_id = _metadata_report(
            case_dir,
            rows_by_id,
            stream,
            colors,
        )
        if yaml_id is not None:
            if yaml_id in seen_yaml_ids:
                metadata_errors.append(f"duplicate curated case id: {yaml_id}")
            seen_yaml_ids.add(yaml_id)

        affected_count = len(affected_function_names(csv_row)) if csv_row else 0
        structure = check_structure(case_dir)
        _structure_report(structure, affected_count, stream, colors)

        affected_total += affected_count
        pair_total += structure.pair_count
        snippet_total += structure.vulnerable_snippet_count

        case_errors = metadata_errors + list(structure.errors)
        if case_errors:
            failed += 1
            _print_check("RESULT", "FAIL", "FAILED", stream, colors)
        else:
            verified += 1
            _print_check("RESULT", "OK", "VERIFIED", stream, colors)
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

    return 1 if failed else 0
