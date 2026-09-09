# The command must succeed with only the published repository inputs

from pathlib import Path
import subprocess
import sys


def check_public_corpus_passes():
    root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [sys.executable, str(root / "main.py"), "--no-color"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    code = result.returncode
    assert code == 0, result.stdout[-2500:] + result.stderr
    assert "Verified cases              96" in result.stdout
    assert "Failed cases                 0" in result.stdout
