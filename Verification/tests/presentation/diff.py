import io

from Verification.verifier.presentation.console import Colorizer
from Verification.verifier.presentation.diff import unified_source_diff


def check_unified_diff_has_context():
    vulnerable = "one\ntwo\nvulnerable call\nfour\nfive\n"
    fixed = "one\ntwo\nfixed call\nfour\nfive\n"

    lines = unified_source_diff(vulnerable, fixed)

    assert lines[0] == "--- vulnerable"
    assert lines[1] == "+++ fixed"
    assert "-vulnerable call" in lines
    assert "+fixed call" in lines
    assert " one" in lines
    assert " five" in lines


def check_color_output_can_be_disabled():
    stream = io.StringIO()
    colors = Colorizer(stream, enabled=False)

    rendered = colors.status("OK") + colors.diff_line("+fixed")

    assert rendered == "[OK]+fixed"
    assert "\x1b[" not in rendered


def check_diff_dedents_without_mutation():
    vulnerable = "pub fn bytes() {\n    vulnerable_call();\n}\n"
    fixed = "    pub fn bytes() {\n        fixed_call();\n    }\n"
    original_vulnerable = vulnerable
    original_fixed = fixed

    lines = unified_source_diff(vulnerable, fixed)

    assert "-pub fn bytes() {" not in lines
    assert "+pub fn bytes() {" not in lines
    assert "-    vulnerable_call();" in lines
    assert "+    fixed_call();" in lines
    assert vulnerable == original_vulnerable
    assert fixed == original_fixed


def check_diff_header_colors(monkeypatch):
    from Verification.verifier.presentation.console import CYAN, GREEN, RED

    monkeypatch.delenv("NO_COLOR", raising=False)
    colors = Colorizer(io.StringIO(), enabled=True)

    assert colors.diff_line("--- vulnerable").startswith(CYAN)
    assert colors.diff_line("+++ fixed").startswith(CYAN)
    assert colors.diff_line("@@ -1 +1 @@").startswith(CYAN)
    assert colors.diff_line("-vulnerable").startswith(RED)
    assert colors.diff_line("+fixed").startswith(GREEN)
