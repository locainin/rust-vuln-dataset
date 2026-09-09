from pathlib import Path

from Verification import main as cli


def check_main_dispatches_interactive_mode(monkeypatch, tmp_path):
    monkeypatch.setattr(cli, "preflight", lambda *args: {})
    calls = []

    def run(*args, **kwargs):
        calls.append((args, kwargs))
        return 7

    monkeypatch.setattr("Verification.verifier.tui.screen.run_interactive", run)

    status = cli.main(["-i", "--no-color", "--cases", str(tmp_path / "manual")])

    assert status == 7
    assert calls == [
        (
            (
                Path(cli.__file__).resolve().parent / "source" / "metadata.csv",
                tmp_path / "manual",
            ),
            {"excluded_cases": cli.EXCLUDED_SEED_CASES, "color": False},
        )
    ]
