# Render pair checks and source differences

from typing import TextIO

from ..pairs import PairResult, StructureResult
from .console import Colorizer, snapshot_match_status
from .diff import unified_source_diff
from .report import check


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
    check(
        "vulnerable snapshot match",
        vulnerable_status,
        vulnerable_detail,
        stream,
        colors,
        indent="    ",
    )
    check(
        "fixed snapshot match",
        fixed_status,
        fixed_detail,
        stream,
        colors,
        indent="    ",
    )

    pair_difference_status = "OK" if pair.vulnerable_fixed_differ is True else "FAIL"
    check(
        "vulnerable != fixed",
        pair_difference_status,
        "",
        stream,
        colors,
        indent="    ",
    )

    before_after_status = "OK" if pair.before_after_differ is True else "FAIL"
    check(
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
        check(
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
        check(
            "source validation",
            "FAIL",
            error,
            stream,
            colors,
            indent="    ",
        )

    print(file=stream)


def structure_report(
    result: StructureResult,
    affected_count: int,
    stream: TextIO,
    colors: Colorizer,
) -> None:
    check(
        "RustSec affected functions",
        "INFO",
        str(affected_count),
        stream,
        colors,
    )
    check(
        "Changed pairs",
        "INFO",
        str(result.pair_count),
        stream,
        colors,
    )

    variant_count = result.vulnerable_snippet_count - result.pair_count
    if variant_count:
        check(
            "Vulnerable variants",
            "INFO",
            str(variant_count),
            stream,
            colors,
        )
    print(file=stream)

    for pair in result.pairs:
        _print_pair(pair, stream, colors)

    # Case failures have no pair block where they can be shown
    pair_errors = {error for pair in result.pairs for error in pair.errors}
    for error in result.errors:
        # Missing metadata is already shown by the metadata report
        if error not in pair_errors and error != "metadata.yaml is missing":
            check("Dataset structure", "FAIL", error, stream, colors)
