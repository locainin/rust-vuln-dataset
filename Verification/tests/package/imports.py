# The CLI also supports execution as a package module

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def check_package_module_cli_help():
    result = subprocess.run(
        [sys.executable, "-m", "Verification.main", "--help"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    assert "--interactive" in result.stdout
    assert "--csv" in result.stdout
    assert "--cases" in result.stdout
