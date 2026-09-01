from Verification.verifier.dataset_structure import PairResult, StructureResult
from Verification.verifier.interactive import (
    MISSING,
    InteractiveCase,
    InteractiveState,
    MetadataField,
    format_header,
    interactive_colors_enabled,
    render_case_lines,
)
from Verification.verifier.schema import EXPECTED_FIELDS


def _metadata_fields(overrides=None, statuses=None):
    values = {
        "id": "RUSTSEC-2025-0021",
        "package": "gix-features",
        "date": "2025-04-03",
        "categories": ["crypto-failure"],
        "CWE": ["CWE-328"],
        "url": "https://rustsec.org/advisories/RUSTSEC-2025-0021.html",
        "references": None,
        "severity": "Medium",
        "aliases": ["GHSA-example"],
        "keywords": [],
        "versions": {"patched": [">= 0.41.0"]},
        "affected": {"functions": ["gix_features::hash::bytes"]},
        "affected.functions": None,
        "fix commit links": ["https://example.test/fix"],
        "pov candidate links": ["https://example.test/pov"],
    }
    values.update(overrides or {})
    field_statuses = statuses or {}
    return tuple(
        MetadataField(
            name=field,
            status=field_statuses.get(field, "OK"),
            value=values[field],
        )
        for field in EXPECTED_FIELDS
    )


def _case(*, metadata_fields=None, pairs=(), errors=()):
    return InteractiveCase(
        identifier="RUSTSEC-2025-0021",
        package="gix-features",
        metadata_fields=metadata_fields or _metadata_fields(),
        affected_count=9,
        structure=StructureResult(errors=(), pairs=tuple(pairs)),
        errors=tuple(errors),
    )


def _pair():
    return PairResult(
        name="bytes",
        vulnerable_range=(113, 121),
        fixed_range=(43, 51),
        vulnerable_text="    pub fn bytes() {\n        vulnerable();\n    }\n",
        fixed_text="pub fn bytes() {\n    fixed();\n}\n",
        before_after_differ=True,
        vulnerable_fixed_differ=True,
        variants=(),
        errors=(),
    )


def test_case_navigation_stops_at_first_and_last_case():
    state = InteractiveState(case_count=3)

    state.previous_case()
    assert state.case_index == 0

    state.next_case()
    state.next_case()
    state.next_case()
    assert state.case_index == 2

    state.previous_case()
    assert state.case_index == 1


def test_case_navigation_resets_vertical_scroll():
    state = InteractiveState(case_count=3, case_index=1, scroll=8)

    state.next_case()

    assert state.case_index == 2
    assert state.scroll == 0


def test_diff_toggle_changes_state_and_returns_to_top():
    state = InteractiveState(case_count=2, scroll=12)

    state.toggle_diffs()

    assert state.show_diffs is True
    assert state.scroll == 0

    state.toggle_diffs()
    assert state.show_diffs is False


def test_vertical_scroll_is_clamped_to_case_bounds():
    state = InteractiveState(case_count=1)

    state.scroll_by(7, max_scroll=5)
    assert state.scroll == 5

    state.scroll_by(-20, max_scroll=5)
    assert state.scroll == 0

    state.go_to_end(max_scroll=9)
    assert state.scroll == 9

    state.go_to_top()
    assert state.scroll == 0


def test_interactive_colors_respect_explicit_disable_and_no_color():
    assert interactive_colors_enabled(False, {}) is False
    assert interactive_colors_enabled(None, {"NO_COLOR": ""}) is False
    assert interactive_colors_enabled(None, {}) is True


def test_header_keeps_complete_case_position_within_terminal_width():
    header = format_header(
        "RUSTSEC-2025-0021",
        "gix-features",
        case_index=3,
        case_count=5,
        width=80,
    )

    assert header.endswith("Case 4 / 5")
    assert len(header) <= 79


def test_compact_view_displays_all_metadata_fields_and_actual_values():
    lines = render_case_lines(_case(), show_diffs=False, width=100)
    text = "\n".join(line.text for line in lines)

    for field in EXPECTED_FIELDS:
        assert f"{field:<28}[OK]" in text

    assert "id                          [OK] RUSTSEC-2025-0021" in text
    assert "package                     [OK] gix-features" in text
    assert "categories                  [OK] crypto-failure" in text
    assert "versions                    [OK] patched: >= 0.41.0" in text


def test_metadata_display_distinguishes_null_empty_list_and_missing():
    fields = _metadata_fields(
        overrides={"references": None, "CWE": [], "url": MISSING},
        statuses={"url": "FAIL"},
    )
    text = "\n".join(
        line.text
        for line in render_case_lines(
            _case(metadata_fields=fields),
            show_diffs=False,
            width=100,
        )
    )

    assert "references                  [OK] null" in text
    assert "CWE                         [OK] []" in text
    assert "url                         [FAIL] <missing>" in text


def test_found_metadata_displays_authoritative_value():
    fields = _metadata_fields(
        overrides={"CWE": ["CWE-416"]},
        statuses={"CWE": "FOUND"},
    )
    text = "\n".join(
        line.text
        for line in render_case_lines(
            _case(metadata_fields=fields),
            show_diffs=False,
            width=100,
        )
    )

    assert "CWE                         [FOUND] CWE-416" in text


def test_long_metadata_values_wrap_on_indented_continuation_lines():
    fields = _metadata_fields(
        overrides={
            "url": (
                "https://example.test/a/very/long/advisory/path/that/"
                "cannot-fit-on-one-terminal-line"
            )
        }
    )
    lines = render_case_lines(
        _case(metadata_fields=fields),
        show_diffs=False,
        width=64,
    )
    texts = [line.text for line in lines]
    url_index = next(
        index for index, line in enumerate(texts) if line.startswith("url ")
    )

    assert texts[url_index].startswith(f"{'url':<28}[OK] ")
    assert texts[url_index + 1].startswith(" " * 33)
    assert len(texts[url_index]) <= 64
    assert len(texts[url_index + 1]) <= 64


def test_diff_toggle_keeps_pair_details_and_only_hides_unified_diff():
    case = _case(pairs=(_pair(),))
    hidden = "\n".join(
        line.text
        for line in render_case_lines(case, show_diffs=False, width=100)
    )
    shown = "\n".join(
        line.text
        for line in render_case_lines(case, show_diffs=True, width=100)
    )

    for expected in (
        "bytes",
        "vulnerable source",
        "fixed source",
        "vulnerable != fixed",
        "provenance",
    ):
        assert expected in hidden

    assert "--- vulnerable" not in hidden
    assert "+++ fixed" not in hidden
    assert "--- vulnerable" in shown
    assert "+++ fixed" in shown


def test_deleted_pair_displays_removed_fixed_source_and_function():
    pair = PairResult(
        name="borsh_serialize",
        vulnerable_range=(8, 21),
        fixed_range=None,
        vulnerable_text="impl BorshSerialize for HashMap {}\n",
        fixed_text="",
        before_after_differ=True,
        vulnerable_fixed_differ=True,
        variants=(),
        errors=(),
        fixed_removed=True,
    )
    text = "\n".join(
        line.text
        for line in render_case_lines(_case(pairs=(pair,)), show_diffs=True, width=100)
    )

    assert any(
        line.strip().startswith("fixed source") and "[REMOVED]" in line
        for line in text.splitlines()
    )
    assert any(
        line.strip().startswith("fixed function") and "[REMOVED]" in line
        for line in text.splitlines()
    )
    assert "--- vulnerable" in text
    assert "+++ fixed" in text
