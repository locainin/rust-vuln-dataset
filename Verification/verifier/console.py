from __future__ import annotations

import os
from typing import TextIO


# ANSI escapes remain local so plain and redirected output stays clean
RESET = "\x1b[0m"
GREEN = "\x1b[32m"
RED = "\x1b[31m"
YELLOW = "\x1b[33m"
CYAN = "\x1b[36m"


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
