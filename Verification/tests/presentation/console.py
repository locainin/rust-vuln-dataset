from io import StringIO

import pytest

from Verification.verifier.presentation.console import Colorizer


@pytest.mark.parametrize("enabled", [True, False, None])
def check_no_color_overrides_enablement(monkeypatch, enabled):
    monkeypatch.setenv("NO_COLOR", "")
    assert Colorizer(StringIO(), enabled=enabled).status("OK") == "[OK]"
