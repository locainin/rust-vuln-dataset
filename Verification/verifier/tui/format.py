# Pure formatting helpers for the interactive review view

from __future__ import annotations

import os
import textwrap
from collections.abc import Mapping
from typing import Any

from .types import MISSING, DisplayLine, MetadataField


def interactive_colors_enabled(
    requested: bool | None,
    environ: Mapping[str, str] | None = None,
) -> bool:
    # NO_COLOR wins over automatic and explicitly requested terminal color
    environment = os.environ if environ is None else environ
    return requested is not False and "NO_COLOR" not in environment


def _format_metadata_value(value: Any) -> str:
    # Keep null, empty, and missing values visibly different during review
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
    # Newlines would break the fixed status column, so wrap them into one value
    return " ".join(rendered.splitlines()) if "\n" in rendered else rendered


def _metadata_lines(field: MetadataField, width: int) -> list[DisplayLine]:
    # Every continuation keeps the same status column as the first line
    prefix = f"{field.name:<28}[{field.status}] "
    continuation = " " * len(prefix)
    value_width = max(width - len(prefix), 1)
    wrapped = textwrap.wrap(
        _format_metadata_value(field.value),
        width=value_width,
        break_long_words=True,
        break_on_hyphens=False,
    ) or [""]
    role = field.status.lower()
    return [
        DisplayLine(f"{prefix}{wrapped[0]}", role),
        *(DisplayLine(f"{continuation}{part}", role) for part in wrapped[1:]),
    ]


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
    if available <= len(position) + 2:
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
    # A fixed label width makes long case reports easy to scan
    suffix = f" {detail}" if detail else ""
    return DisplayLine(
        f"{indent}{label:<28}[{status}]{suffix}",
        status.lower(),
    )


def _diff_role(line: str) -> str:
    # Unified headers describe the change while signs describe its direction
    if line.startswith(("@@", "---", "+++")):
        return "info"
    if line.startswith("+"):
        return "ok"
    if line.startswith("-"):
        return "fail"
    return "normal"
