# Shared formatting for the plain terminal report

from typing import TextIO

from .console import Colorizer


def check(
    label: str,
    status: str,
    detail: str,
    stream: TextIO,
    colors: Colorizer,
    indent: str = "  ",
) -> None:
    suffix = f" {detail}" if detail else ""
    print(f"{indent}{label:<28}{colors.status(status)}{suffix}", file=stream)
