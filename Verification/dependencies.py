# Check the installed Python runtime and ast-grep

from __future__ import annotations

import platform
import shutil
import subprocess
import sys
from importlib import import_module

MINIMUM_PYTHON = (3, 11)
TOOL_VERSION_TIMEOUT = 10


class DependencyError(RuntimeError):
    # A required module or executable is unavailable
    pass


def check_runtime() -> dict[str, str]:
    version = platform.python_version()
    if sys.version_info[:2] < MINIMUM_PYTHON:
        required = ".".join(map(str, MINIMUM_PYTHON))
        raise DependencyError(
            f"Dependency preflight failed: Python {required}+ is required; "
            f"found {version}. Upgrade the verifier interpreter."
        )
    # Defer third-party imports so dependency errors remain readable
    try:
        yaml = import_module("yaml")
    except ImportError as error:
        raise DependencyError(
            "PyYAML is unavailable; install PyYAML for the current Python interpreter"
        ) from error
    return {"python": version, "PyYAML": yaml.__version__}


def _first_output_line(stdout: str, stderr: str) -> str:
    for output in (stdout, stderr):
        for line in output.splitlines():
            if line.strip():
                return line.strip()
    return ""


def check_parser() -> str:
    # Probe the executable without installing or changing anything
    name = "ast-grep"
    path = shutil.which(name)
    if path is None:
        raise DependencyError(
            f"{name}: command not found on PATH; install it or add it to PATH "
            "before running verification (no automatic installation is performed)"
        )

    command = [path, "--version"]
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            check=False,
            text=True,
            timeout=TOOL_VERSION_TIMEOUT,
        )
    except subprocess.TimeoutExpired as error:
        raise DependencyError(
            f"{name}: version probe timed out after {TOOL_VERSION_TIMEOUT}s; "
            "check the installation and PATH"
        ) from error
    except OSError as error:
        raise DependencyError(f"{name}: could not execute {path}: {error}") from error

    version = _first_output_line(result.stdout, result.stderr)
    if result.returncode != 0:
        detail = version or "no diagnostic output"
        raise DependencyError(
            f"{name}: version probe exited with status {result.returncode}: "
            f"{detail}; repair or reinstall the tool"
        )
    if not version:
        raise DependencyError(
            f"{name}: version probe returned no version information; "
            "check the installation"
        )
    return version


def preflight() -> dict[str, str]:
    return {**check_runtime(), "ast-grep": check_parser()}


def main(argv=None) -> int:
    # Keep a tiny executable for local dependency diagnostics
    arguments = sys.argv[1:] if argv is None else list(argv)
    if arguments:
        print("dependency diagnostics accepts no arguments", file=sys.stderr)
        return 1
    try:
        versions = preflight()
    except DependencyError as error:
        print(error, file=sys.stderr)
        return 1
    for name, version in versions.items():
        print(f"{name}: {version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
