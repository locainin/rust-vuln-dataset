import subprocess
import sys
from pathlib import Path

import pytest

from Verification.main import build_parser


@pytest.mark.parametrize("flag", ["-i", "--interactive"])
def check_interactive_aliases(flag):
    parser = build_parser(Path("verification"))
    args = parser.parse_args([flag, "--no-color"])
    assert args.interactive is True
    assert args.no_color is True


def check_direct_script_help():
    directory = Path(__file__).resolve().parents[2]
    result = subprocess.run(
        [sys.executable, "main.py", "--help"],
        cwd=directory,
        capture_output=True,
        text=True,
        check=True,
    )
    assert "--cases" in result.stdout
    assert "--interactive" in result.stdout
