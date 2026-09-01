import io

from Verification.verifier.console import Colorizer
from Verification.verifier.source_diff import unified_source_diff


def test_unified_diff_runs_from_vulnerable_to_fixed_with_two_context_lines():
    vulnerable = "one\ntwo\nvulnerable call\nfour\nfive\n"
    fixed = "one\ntwo\nfixed call\nfour\nfive\n"

    lines = unified_source_diff(vulnerable, fixed)

    assert lines[0] == "--- vulnerable"
    assert lines[1] == "+++ fixed"
    assert "-vulnerable call" in lines
    assert "+fixed call" in lines
    assert " one" in lines
    assert " five" in lines


def test_color_output_can_be_disabled():
    stream = io.StringIO()
    colors = Colorizer(stream, enabled=False)

    rendered = colors.status("OK") + colors.diff_line("+fixed")

    assert rendered == "[OK]+fixed"
    assert "\x1b[" not in rendered


def test_display_diff_dedents_each_source_without_changing_original_text():
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


def test_diff_headers_use_info_color_while_code_uses_change_colors():
    from Verification.verifier.console import CYAN, GREEN, RED

    colors = Colorizer(io.StringIO(), enabled=True)

    assert colors.diff_line("--- vulnerable").startswith(CYAN)
    assert colors.diff_line("+++ fixed").startswith(CYAN)
    assert colors.diff_line("@@ -1 +1 @@").startswith(CYAN)
    assert colors.diff_line("-vulnerable").startswith(RED)
    assert colors.diff_line("+fixed").startswith(GREEN)
