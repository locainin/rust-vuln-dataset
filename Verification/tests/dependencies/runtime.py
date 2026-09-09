import importlib
import subprocess
from pathlib import Path

import pytest

from Verification import dependencies


def check_dependency_diagnostics_print_versions(monkeypatch, capsys):
    monkeypatch.setattr(
        dependencies,
        "preflight",
        lambda: {"python": "3.12.1", "PyYAML": "6.0.2", "ast-grep": "1.0"},
    )

    assert dependencies.main([]) == 0
    assert capsys.readouterr().out.splitlines() == [
        "python: 3.12.1",
        "PyYAML: 6.0.2",
        "ast-grep: 1.0",
    ]


def check_dependency_diagnostics_rejects_arguments(capsys):
    assert dependencies.main(["unexpected"]) == 1
    assert "accepts no arguments" in capsys.readouterr().err


def check_dependency_import_is_lazy():
    root = Path(__file__).resolve().parents[3]
    result = subprocess.run(
        [
            dependencies.sys.executable,
            "-c",
            (
                "import sys; import Verification.dependencies; "
                "print('yaml' not in sys.modules and "
                "not any(name.startswith('Verification.verifier') "
                "for name in sys.modules))"
            ),
        ],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.strip() == "True"


def check_parser_reports_version(monkeypatch):
    call = {}

    def run(command, **options):
        call.update(command=command, options=options)
        return subprocess.CompletedProcess(command, 0, f"{command[0]} 1.2.3\n", "")

    monkeypatch.setattr(dependencies.shutil, "which", lambda name: f"/opt/bin/{name}")
    monkeypatch.setattr(dependencies.subprocess, "run", run)

    assert dependencies.check_parser() == "/opt/bin/ast-grep 1.2.3"
    assert call == {
        "command": ["/opt/bin/ast-grep", "--version"],
        "options": {
            "capture_output": True,
            "check": False,
            "text": True,
            "timeout": dependencies.TOOL_VERSION_TIMEOUT,
        },
    }


def check_parser_missing_explains_recovery(monkeypatch):
    monkeypatch.setattr(dependencies.shutil, "which", lambda name: None)

    with pytest.raises(dependencies.DependencyError, match="ast-grep.*PATH") as error:
        dependencies.check_parser()

    assert "install" in str(error.value).lower()
    assert "automatic" in str(error.value).lower()


def check_parser_failure_explains_recovery(monkeypatch):
    monkeypatch.setattr(dependencies.shutil, "which", lambda name: "/bin/tool")

    def run(command, **options):
        return subprocess.CompletedProcess(command, 2, "", "permission denied")

    monkeypatch.setattr(dependencies.subprocess, "run", run)

    with pytest.raises(dependencies.DependencyError, match="permission denied"):
        dependencies.check_parser()


def check_parser_timeout_explains_recovery(monkeypatch):
    monkeypatch.setattr(dependencies.shutil, "which", lambda name: "/bin/tool")

    def run(command, **options):
        raise subprocess.TimeoutExpired(command, options["timeout"])

    monkeypatch.setattr(dependencies.subprocess, "run", run)

    with pytest.raises(dependencies.DependencyError, match="timed out"):
        dependencies.check_parser()


def check_runtime_reports_python_and_pyyaml(monkeypatch):
    monkeypatch.setattr(dependencies.platform, "python_version", lambda: "3.12.1")
    yaml = importlib.import_module("yaml")

    assert dependencies.check_runtime() == {
        "python": "3.12.1",
        "PyYAML": str(yaml.__version__),
    }


def check_runtime_reports_missing_pyyaml(monkeypatch):
    def import_required(name):
        assert name == "yaml"
        raise ImportError("No module named yaml")

    monkeypatch.setattr(dependencies, "import_module", import_required)

    with pytest.raises(dependencies.DependencyError) as error:
        dependencies.check_runtime()

    message = str(error.value)
    assert "PyYAML" in message
    assert "install" in message.lower()


def check_runtime_rejects_old_python(monkeypatch):
    monkeypatch.setattr(dependencies.sys, "version_info", (3, 10, 99))
    monkeypatch.setattr(dependencies.platform, "python_version", lambda: "3.10.99")

    with pytest.raises(dependencies.DependencyError, match="Python 3.11+"):
        dependencies.check_runtime()
