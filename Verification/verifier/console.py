from __future__ import annotations

import os
from typing import TextIO


# ANSI escapes remain local so plain and redirected output stays clean
RESET = "\x1b[0m"
GREEN = "\x1b[32m"
RED = "\x1b[31m"
YELLOW = "\x1b[33m"
CYAN = "\x1b[36m"


def snapshot_match_status(
    filename: str,
    source_range: tuple[int, int] | None,
    match_count: int | None,
) -> tuple[str, str]:
    # Repeated bytes prove inclusion but cannot identify one source range
    if match_count is not None and match_count > 1:
        return (
            "INFO",
            f"{filename}: {match_count} exact matches; range is ambiguous",
        )
    if source_range is not None:
        return "OK", f"{filename}:{source_range[0]}-{source_range[1]}"
    return "FAIL", "snapshot mismatch"


class Colorizer:
    def __init__(self, stream: TextIO, enabled: bool | None = None) -> None:
        # Automatic color requires a TTY and honors the standard NO_COLOR flag
        if enabled is None:
            is_tty = bool(getattr(stream, "isatty", lambda: False)())
            enabled = is_tty and "NO_COLOR" not in os.environ
        self.enabled = enabled

    def _wrap(self, text: str, color: str) -> str:
        if not self.enabled:
            return text
        return f"{color}{text}{RESET}"

    def status(self, status: str) -> str:
        colors = {
            "OK": GREEN,
            "FAIL": RED,
            "FOUND": YELLOW,
            "REMOVED": YELLOW,
            "INFO": CYAN,
        }
        return self._wrap(f"[{status}]", colors.get(status, CYAN))

    def diff_line(self, line: str) -> str:
        # Unified diff headers are informational while source lines show direction
        if line.startswith(("@@", "+++", "---")):
            return self._wrap(line, CYAN)
        if line.startswith("+"):
            return self._wrap(line, GREEN)
        if line.startswith("-"):
            return self._wrap(line, RED)
        return line
