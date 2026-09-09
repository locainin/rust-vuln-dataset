import contextlib
import io
from pathlib import Path

from Verification.verifier.pairs import StructureResult
from Verification.verifier.tui import screen
from Verification.verifier.tui.types import InteractiveCase, InteractiveData


def check_wrapper_failure_returns_a_concise_error(monkeypatch):
    case = InteractiveCase(
        identifier="RUSTSEC-2099-0001",
        package="example",
        metadata_fields=(),
        affected_count=0,
        structure=StructureResult(errors=(), pairs=()),
        errors=(),
    )
    monkeypatch.setattr(
        screen,
        "load_data",
        lambda *args, **kwargs: InteractiveData(cases=(case,)),
    )

    def fail_wrapper(*args, **kwargs):
        raise screen.curses.error("terminal initialization failed")

    monkeypatch.setattr(screen.curses, "wrapper", fail_wrapper)
    output = io.StringIO()

    with contextlib.redirect_stdout(output):
        status = screen.run_interactive(Path("metadata.csv"), Path("manual"))

    assert status == 1
    assert "Interactive terminal: terminal initialization failed" in output.getvalue()
