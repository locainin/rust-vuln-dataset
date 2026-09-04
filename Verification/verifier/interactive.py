from __future__ import annotations

import curses
import os
import textwrap
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from .case_metadata import case_id, discover_case_dirs, is_valid_case_name, load_yaml
from .comparison import compare_row
from .console import snapshot_match_status
from .csv_source import load_metadata_csv
from .dataset_structure import PairResult, StructureResult, check_structure
from .normalization import affected_function_names
from .schema import EXPECTED_FIELDS, SOURCE_ROW_COUNT
from .source_diff import unified_source_diff


@dataclass
class InteractiveState:
    case_count: int
    case_index: int = 0
    scroll: int = 0
    show_diffs: bool = False

    def previous_case(self) -> None:
        # Navigation stops at the first case instead of wrapping
        if self.case_index > 0:
            self.case_index -= 1
            self.scroll = 0

    def next_case(self) -> None:
        # Navigation stops at the final case instead of wrapping
        if self.case_index + 1 < self.case_count:
            self.case_index += 1
            self.scroll = 0

    def toggle_diffs(self) -> None:
        self.show_diffs = not self.show_diffs
        self.scroll = 0

    def scroll_by(self, amount: int, max_scroll: int) -> None:
        self.scroll = min(max(self.scroll + amount, 0), max_scroll)

    def go_to_top(self) -> None:
        self.scroll = 0

    def go_to_end(self, max_scroll: int) -> None:
        self.scroll = max_scroll


@dataclass(frozen=True)
class DisplayLine:
    text: str
    role: str = "normal"


MISSING = object()


@dataclass(frozen=True)
class MetadataField:
    name: str
    status: str
    value: Any


@dataclass(frozen=True)
class InteractiveCase:
    identifier: str
    package: str
    metadata_fields: tuple[MetadataField, ...]
    affected_count: int
    structure: StructureResult
    errors: tuple[str, ...]

    @property
    def verified(self) -> bool:
        return not self.errors


def interactive_colors_enabled(
    requested: bool | None,
    environ: Mapping[str, str] | None = None,
) -> bool:
    # NO_COLOR overrides automatic and explicitly requested terminal color
    environment = os.environ if environ is None else environ
    return requested is not False and "NO_COLOR" not in environment


def _format_metadata_value(value: Any) -> str:
    # Preserve source distinctions that matter during manual review
    if value is MISSING:
        return "<missing>"
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, list):
        if not value:
            return "[]"
        return ", ".join(_format_metadata_value(item) for item in value)
    if isinstance(value, dict):
        if not value:
            return "{}"
        return "; ".join(
            f"{key}: {_format_metadata_value(item)}" for key, item in value.items()
        )

    rendered = str(value)
    return " ".join(rendered.splitlines()) if "\n" in rendered else rendered


def _metadata_field_lines(
    field: MetadataField,
    width: int,
) -> list[DisplayLine]:
    prefix = f"{field.name:<28}[{field.status}] "
    continuation = " " * len(prefix)
    value = _format_metadata_value(field.value)
    value_width = max(width - len(prefix), 1)
    wrapped = textwrap.wrap(
        value,
        width=value_width,
        break_long_words=True,
        break_on_hyphens=False,
    ) or [""]
    role = field.status.lower()

    lines = [DisplayLine(f"{prefix}{wrapped[0]}", role)]
    lines.extend(DisplayLine(f"{continuation}{part}", role) for part in wrapped[1:])
    return lines


def format_header(
    identifier: str,
    package: str,
    case_index: int,
    case_count: int,
    width: int,
) -> str:
    # Leave the final terminal column unused to avoid curses edge errors
    available = max(width - 1, 0)
    position = f"Case {case_index + 1} / {case_count}"
    if available <= len(position):
        return position[:available]

    title = f"{identifier} — {package}"
    title_width = available - len(position) - 2
    return f"{title[:title_width]:<{title_width}}  {position}"


def _status_line(
    label: str,
    status: str,
    detail: str = "",
    indent: str = "",
) -> DisplayLine:
    suffix = f" {detail}" if detail else ""
    return DisplayLine(
        f"{indent}{label:<28}[{status}]{suffix}",
        status.lower(),
    )


def _diff_role(line: str) -> str:
    if line.startswith(("@@", "---", "+++")):
        return "info"
    if line.startswith("+"):
        return "ok"
    if line.startswith("-"):
        return "fail"
    return "normal"


def _expanded_pair_lines(
    pair: PairResult,
    show_diff: bool,
) -> list[DisplayLine]:
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
    snapshot_statuses = {vulnerable_status, fixed_status}
    snapshot_integrity_status = (
        "FAIL"
        if "FAIL" in snapshot_statuses
        else "INFO"
        if "INFO" in snapshot_statuses
        else "OK"
    )

    lines.append(
        _status_line(
            "vulnerable snapshot match",
            vulnerable_status,
            vulnerable_detail,
            indent="  ",
        )
    )
    lines.append(
        _status_line(
            "fixed snapshot match",
            fixed_status,
            fixed_detail,
            indent="  ",
        )
    )
    if pair.fixed_removed:
        lines.append(_status_line("fixed item", "REMOVED", indent="  "))
    lines.append(
        _status_line(
            "vulnerable != fixed",
            difference_status,
            indent="  ",
        )
    )
    lines.append(
        _status_line(
            "snapshot integrity",
            snapshot_integrity_status,
            indent="  ",
        )
    )

    if show_diff and pair.vulnerable_text is not None and pair.fixed_text is not None:
        lines.append(DisplayLine(""))
        for diff_line in unified_source_diff(
            pair.vulnerable_text,
            pair.fixed_text,
        ):
            lines.append(DisplayLine(f"  {diff_line}", _diff_role(diff_line)))

    for variant in pair.variants:
        lines.append(DisplayLine(""))
        source_status, source_detail = snapshot_match_status(
            "before.rs",
            variant.source_range,
            variant.source_match_count,
        )
        difference_status = "OK" if variant.differs_from_fixed is True else "FAIL"
        lines.append(
            _status_line(
                f"{variant.name} variant",
                source_status,
                source_detail,
                indent="  ",
            )
        )
        lines.append(
            _status_line(
                "variant != fixed",
                difference_status,
                indent="  ",
            )
        )
        if show_diff and variant.text is not None and pair.fixed_text is not None:
            lines.append(DisplayLine(""))
            for diff_line in unified_source_diff(variant.text, pair.fixed_text):
                lines.append(DisplayLine(f"  {diff_line}", _diff_role(diff_line)))

    lines.append(DisplayLine(""))
    return lines


def render_case_lines(
    case: InteractiveCase,
    show_diffs: bool,
    width: int = 80,
) -> list[DisplayLine]:
    # Metadata remains visible while source diffs are toggled independently
    lines = [DisplayLine("Metadata", "info"), DisplayLine("")]
    for field in case.metadata_fields:
        lines.extend(_metadata_field_lines(field, width))

    lines.extend(
        [
            DisplayLine(""),
            _status_line(
                "RustSec affected functions",
                "INFO",
                str(case.affected_count),
            ),
            _status_line(
                "Changed pairs",
                "INFO",
                str(case.structure.pair_count),
            ),
        ]
    )

    variant_count = case.structure.vulnerable_snippet_count - case.structure.pair_count
    lines.append(_status_line("Vulnerable variants", "INFO", str(variant_count)))
    lines.append(DisplayLine(""))

    # Pair snapshot integrity is always reviewable; only source diffs collapse
    for pair in case.structure.pairs:
        lines.extend(_expanded_pair_lines(pair, show_diffs))

    if case.errors:
        for error in case.errors:
            lines.append(DisplayLine(f"  {error}", "fail"))
        lines.append(DisplayLine(""))

    result_status = "OK" if case.verified else "FAIL"
    result_detail = "VERIFIED" if case.verified else "FAILED"
    lines.append(_status_line("RESULT", result_status, result_detail))
    lines.append(DisplayLine(""))
    toggle_text = "[d] Hide changes" if show_diffs else "[d] Show changes"
    lines.append(DisplayLine(toggle_text, "info"))
    return lines


def _metadata_fields_for_case(
    yaml_data: Any,
    issues: list[dict[str, Any]],
    can_compare: bool,
) -> tuple[MetadataField, ...]:
    issue_by_field: dict[str, dict[str, Any]] = {}
    for issue in issues:
        field = issue["field"]
        if field not in EXPECTED_FIELDS:
            continue

        # A failure takes precedence if malformed input creates duplicate issues
        current = issue_by_field.get(field)
        if current is None or issue["status"] == "FAIL":
            issue_by_field[field] = issue

    fields: list[MetadataField] = []
    for field in EXPECTED_FIELDS:
        issue = issue_by_field.get(field)
        if issue is not None:
            status = issue["status"]
        else:
            status = "OK" if can_compare else "FAIL"

        value = (
            yaml_data[field]
            if isinstance(yaml_data, dict) and field in yaml_data
            else MISSING
        )
        fields.append(MetadataField(name=field, status=status, value=value))

    return tuple(fields)


def _load_case(
    case_dir: Path,
    rows_by_id: dict[str, dict[str, Any]],
) -> InteractiveCase:
    errors: list[str] = []
    issues: list[dict[str, Any]] = []
    source_row = rows_by_id.get(case_dir.name)
    package = source_row["package"] if source_row else "unknown package"
    yaml_path = case_dir / "metadata.yaml"

    if not is_valid_case_name(case_dir.name):
        errors.append(f"metadata: invalid directory name {case_dir.name}")

    yaml_data: Any = None
    if not yaml_path.is_file():
        errors.append("metadata: metadata.yaml is missing")
    else:
        try:
            yaml_data = load_yaml(yaml_path)
        except (OSError, yaml.YAMLError) as error:
            errors.append(f"metadata: {error}")

    yaml_identifier = case_id(yaml_data)
    if yaml_identifier is None:
        errors.append("metadata: canonical id is missing")
    elif yaml_identifier != case_dir.name:
        errors.append("metadata: directory name does not match id")

    csv_row = rows_by_id.get(yaml_identifier) if yaml_identifier else None
    if csv_row is None:
        errors.append("metadata: no matching CSV entry")
    elif yaml_data is not None:
        issues = compare_row(csv_row, yaml_data)
        errors.extend(
            f"metadata: {issue['field']}: {issue['reason']}"
            for issue in issues
            if issue["status"] == "FAIL"
        )

    metadata_fields = _metadata_fields_for_case(
        yaml_data,
        issues,
        can_compare=csv_row is not None and isinstance(yaml_data, dict),
    )
    structure = check_structure(case_dir)
    errors.extend(f"structure: {error}" for error in structure.errors)
    affected_count = len(affected_function_names(csv_row)) if csv_row else 0

    return InteractiveCase(
        identifier=case_dir.name,
        package=package,
        metadata_fields=metadata_fields,
        affected_count=affected_count,
        structure=structure,
        errors=tuple(errors),
    )


def load_interactive_cases(
    csv_path: Path,
    cases_dir: Path,
) -> tuple[InteractiveCase, ...]:
    rows = load_metadata_csv(csv_path, expected_rows=SOURCE_ROW_COUNT)
    rows_by_id = {row["id"]: row for row in rows}
    return tuple(
        _load_case(case_dir, rows_by_id) for case_dir in discover_case_dirs(cases_dir)
    )


# Color pair identifiers stay private to the curses renderer
PAIR_OK = 1
PAIR_FAIL = 2
PAIR_FOUND = 3
PAIR_INFO = 4


def _initialize_colors(enabled: bool) -> dict[str, int]:
    if not enabled or not curses.has_colors():
        return {}

    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(PAIR_OK, curses.COLOR_GREEN, -1)
    curses.init_pair(PAIR_FAIL, curses.COLOR_RED, -1)
    curses.init_pair(PAIR_FOUND, curses.COLOR_YELLOW, -1)
    curses.init_pair(PAIR_INFO, curses.COLOR_CYAN, -1)
    return {
        "ok": curses.color_pair(PAIR_OK),
        "fail": curses.color_pair(PAIR_FAIL),
        "found": curses.color_pair(PAIR_FOUND),
        "info": curses.color_pair(PAIR_INFO),
    }


def _safe_add(
    screen: Any,
    row: int,
    column: int,
    text: str,
    width: int,
    attribute: int = 0,
) -> None:
    if width <= 0:
        return
    try:
        screen.addnstr(row, column, text, width, attribute)
    except curses.error:
        # The bottom-right terminal cell may reject a valid final character
        pass


def _draw(
    screen: Any,
    cases: tuple[InteractiveCase, ...],
    state: InteractiveState,
    role_attributes: dict[str, int],
) -> int:
    screen.erase()
    height, width = screen.getmaxyx()
    if height < 5 or width < 20:
        _safe_add(screen, 0, 0, "Terminal is too small", max(width - 1, 0))
        screen.refresh()
        return 0

    case = cases[state.case_index]
    header = format_header(
        case.identifier,
        case.package,
        state.case_index,
        state.case_count,
        width,
    )
    header_attribute = curses.A_BOLD | role_attributes.get("info", 0)
    _safe_add(screen, 0, 0, header, width - 1, header_attribute)

    try:
        screen.hline(1, 0, curses.ACS_HLINE, width - 1)
        screen.hline(height - 2, 0, curses.ACS_HLINE, width - 1)
    except curses.error:
        pass

    lines = render_case_lines(case, state.show_diffs, width=max(width - 1, 1))
    body_height = max(height - 4, 1)
    max_scroll = max(len(lines) - body_height, 0)
    state.scroll = min(state.scroll, max_scroll)

    for offset, line in enumerate(
        lines[state.scroll : state.scroll + body_height],
        start=2,
    ):
        attribute = role_attributes.get(line.role, 0)
        _safe_add(screen, offset, 0, line.text, width - 1, attribute)

    footer = (
        "←/→ or h/l case   ↑/↓ scroll   PgUp/PgDn scroll   Home/End   d diffs   q quit"
    )
    _safe_add(
        screen,
        height - 1,
        0,
        footer,
        width - 1,
        role_attributes.get("info", 0),
    )
    screen.refresh()
    return max_scroll


def _curses_main(
    screen: Any,
    cases: tuple[InteractiveCase, ...],
    color_requested: bool | None,
) -> None:
    try:
        curses.curs_set(0)
    except curses.error:
        pass
    screen.keypad(True)
    role_attributes = _initialize_colors(interactive_colors_enabled(color_requested))
    state = InteractiveState(case_count=len(cases))

    while True:
        max_scroll = _draw(screen, cases, state, role_attributes)
        key = screen.getch()
        height, _ = screen.getmaxyx()
        page_size = max(height - 5, 1)

        if key in (ord("q"), ord("Q")):
            return
        if key in (curses.KEY_LEFT, ord("h"), ord("H")):
            state.previous_case()
        elif key in (curses.KEY_RIGHT, ord("l"), ord("L")):
            state.next_case()
        elif key == curses.KEY_UP:
            state.scroll_by(-1, max_scroll)
        elif key == curses.KEY_DOWN:
            state.scroll_by(1, max_scroll)
        elif key == curses.KEY_PPAGE:
            state.scroll_by(-page_size, max_scroll)
        elif key == curses.KEY_NPAGE:
            state.scroll_by(page_size, max_scroll)
        elif key == curses.KEY_HOME:
            state.go_to_top()
        elif key == curses.KEY_END:
            state.go_to_end(max_scroll)
        elif key in (ord("d"), ord("D")):
            state.toggle_diffs()


def run_interactive(
    csv_path: Path,
    cases_dir: Path,
    *,
    color: bool | None = None,
) -> int:
    cases = load_interactive_cases(csv_path, cases_dir)
    if not cases:
        print("No curated RustSec cases found")
        return 1

    curses.wrapper(_curses_main, cases, color)
    return 0
