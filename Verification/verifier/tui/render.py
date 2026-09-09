# Build scrollable lines for one interactive case

from __future__ import annotations

from ..pairs import PairResult
from ..presentation.console import snapshot_match_status
from ..presentation.diff import unified_source_diff
from .format import _diff_role, _metadata_lines, _status_line
from .types import DisplayLine, InteractiveCase


def _diff_lines(vulnerable: str | None, fixed: str | None) -> list[DisplayLine]:
    # Missing source text already has a validation error beside the pair
    if vulnerable is None or fixed is None:
        return []
    return [
        DisplayLine(f"  {line}", _diff_role(line))
        for line in unified_source_diff(vulnerable, fixed)
    ]


def _pair_lines(pair: PairResult, show_diff: bool) -> list[DisplayLine]:
    # Snapshot checks remain visible when a full source diff is hidden
    lines = [DisplayLine(pair.name)]
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

    difference_status = "OK" if pair.vulnerable_fixed_differ is True else "FAIL"
    before_after_status = "OK" if pair.before_after_differ is True else "FAIL"
    snapshot_statuses = {vulnerable_status, fixed_status, before_after_status}
    snapshot_integrity_status = "FAIL" if "FAIL" in snapshot_statuses else "OK"
    lines.extend(
        (
            _status_line(
                "vulnerable snapshot match",
                vulnerable_status,
                vulnerable_detail,
                indent="  ",
            ),
            _status_line(
                "fixed snapshot match",
                fixed_status,
                fixed_detail,
                indent="  ",
            ),
        )
    )
    if pair.fixed_removed:
        lines.append(_status_line("fixed item", "REMOVED", indent="  "))
    lines.extend(
        (
            _status_line("vulnerable != fixed", difference_status, indent="  "),
            _status_line("before != after", before_after_status, indent="  "),
            _status_line("snapshot integrity", snapshot_integrity_status, indent="  "),
        )
    )

    if show_diff:
        diff = _diff_lines(pair.vulnerable_text, pair.fixed_text)
        if diff:
            lines.append(DisplayLine(""))
            lines.extend(diff)

    for variant in pair.variants:
        # Separate variants visually while keeping them in the same pair block
        lines.append(DisplayLine(""))
        source_status, source_detail = snapshot_match_status(
            "before.rs",
            variant.source_range,
            variant.source_match_count,
        )
        difference_status = "OK" if variant.differs_from_fixed is True else "FAIL"
        lines.extend(
            (
                _status_line(
                    f"{variant.name} variant",
                    source_status,
                    source_detail,
                    indent="  ",
                ),
                _status_line("variant != fixed", difference_status, indent="  "),
            )
        )
        if show_diff:
            diff = _diff_lines(variant.text, pair.fixed_text)
            if diff:
                lines.append(DisplayLine(""))
                lines.extend(diff)

    lines.append(DisplayLine(""))
    return lines


def render_case_lines(
    case: InteractiveCase,
    show_diffs: bool,
    width: int = 80,
    *,
    coverage_errors: tuple[str, ...] = (),
) -> list[DisplayLine]:
    # A caller can supply one shared inventory result for every case screen
    inventory_errors = tuple(coverage_errors)
    lines: list[DisplayLine] = []
    if inventory_errors:
        lines.append(
            _status_line("Seed coverage", "FAIL", f"{len(inventory_errors)} issue(s)")
        )
        lines.extend(DisplayLine(f"  {error}", "fail") for error in inventory_errors)
        lines.append(DisplayLine(""))

    lines.extend((DisplayLine("Metadata", "info"), DisplayLine("")))
    for field in case.metadata_fields:
        lines.extend(_metadata_lines(field, width))

    lines.extend(
        (
            DisplayLine(""),
            _status_line(
                "RustSec affected functions",
                "INFO",
                str(case.affected_count),
            ),
            _status_line("Changed pairs", "INFO", str(case.structure.pair_count)),
            _status_line(
                "Vulnerable variants",
                "INFO",
                str(
                    case.structure.vulnerable_snippet_count - case.structure.pair_count
                ),
            ),
            DisplayLine(""),
        )
    )

    # Pair integrity stays reviewable while only source diffs collapse
    for pair in case.structure.pairs:
        lines.extend(_pair_lines(pair, show_diffs))

    if case.errors:
        lines.extend(DisplayLine(f"  {error}", "fail") for error in case.errors)
        lines.append(DisplayLine(""))

    verified = case.verified and not inventory_errors
    result_status = "OK" if verified else "FAIL"
    result_detail = "VERIFIED" if verified else "FAILED"
    lines.extend(
        (
            _status_line("RESULT", result_status, result_detail),
            DisplayLine(""),
            DisplayLine(
                "[d] Hide changes" if show_diffs else "[d] Show changes",
                "info",
            ),
        )
    )
    return lines
