# Curses drawing and keyboard handling for the case review screen

from __future__ import annotations

import curses
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from ..metadata.schema import SOURCE_ROW_COUNT
from .format import format_header, interactive_colors_enabled
from .load import load_data
from .render import render_case_lines
from .state import InteractiveState
from .types import InteractiveData

# Color pair identifiers are private to the curses renderer
PAIR_OK = 1
PAIR_FAIL = 2
PAIR_FOUND = 3
PAIR_INFO = 4


def _initialize_colors(enabled: bool) -> dict[str, int]:
    # Plain terminals keep the same layout without requiring color support
    if not enabled or not curses.has_colors():
        return {}

    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(PAIR_OK, curses.COLOR_GREEN, -1)
    curses.init_pair(PAIR_FAIL, curses.COLOR_RED, -1)
    curses.init_pair(PAIR_FOUND, curses.COLOR_YELLOW, -1)
    curses.init_pair(PAIR_INFO, curses.COLOR_CYAN, -1)
    info = curses.color_pair(PAIR_INFO)
    return {
        "ok": curses.color_pair(PAIR_OK),
        "fail": curses.color_pair(PAIR_FAIL),
        "found": curses.color_pair(PAIR_FOUND),
        "removed": curses.color_pair(PAIR_FOUND),
        "info": info,
    }


def _safe_add(
    screen: Any,
    row: int,
    column: int,
    text: str,
    width: int,
    attribute: int = 0,
) -> None:
    # The last terminal cell can reject an otherwise valid character
    if width <= 0:
        return
    try:
        screen.addnstr(row, column, text, width, attribute)
    except curses.error:
        pass


def _draw(
    screen: Any,
    data: InteractiveData,
    state: InteractiveState,
    role_attributes: dict[str, int],
) -> int:
    # Redraw from the current state so resize and toggles need no extra cache
    screen.erase()
    height, width = screen.getmaxyx()
    if height < 5 or width < 20:
        _safe_add(screen, 0, 0, "Terminal is too small", max(width - 1, 0))
        screen.refresh()
        return 0

    case = data.cases[state.case_index]
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

    lines = render_case_lines(
        case,
        state.show_diffs,
        width=max(width - 1, 1),
        coverage_errors=data.coverage_errors,
    )
    body_height = max(height - 4, 1)
    max_scroll = max(len(lines) - body_height, 0)
    state.scroll = min(state.scroll, max_scroll)
    for offset, line in enumerate(
        lines[state.scroll : state.scroll + body_height],
        start=2,
    ):
        _safe_add(
            screen,
            offset,
            0,
            line.text,
            width - 1,
            role_attributes.get(line.role, 0),
        )

    # Keep controls visible even when the case body is much longer than the view
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
    data: InteractiveData,
    color_requested: bool | None,
) -> None:
    # Cursor and keypad setup belong inside wrapper after terminal initialization
    try:
        curses.curs_set(0)
    except curses.error:
        pass
    screen.keypad(True)
    role_attributes = _initialize_colors(interactive_colors_enabled(color_requested))
    state = InteractiveState(case_count=len(data.cases))

    while True:
        max_scroll = _draw(screen, data, state, role_attributes)
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
    excluded_cases: Iterable[str] = (),
    expected_source_rows: int | None = SOURCE_ROW_COUNT,
) -> int:
    # Review every curated case in a curses session

    try:
        data = load_data(
            csv_path,
            cases_dir,
            expected_source_rows=expected_source_rows,
            excluded_cases=excluded_cases,
        )
    except (OSError, ValueError) as error:
        print(f"CSV or case data: {error}")
        return 1

    if not data.cases:
        print("No curated RustSec cases found")
        for error in data.coverage_errors:
            print(f"Seed coverage: {error}")
        return data.exit_status

    try:
        curses.wrapper(_curses_main, data, color)
    except curses.error as error:
        # Unsupported terminals should return a useful status without a traceback
        print(f"Interactive terminal: {error}")
        return 1
    return data.exit_status
