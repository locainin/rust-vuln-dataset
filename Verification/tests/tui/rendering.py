from dataclasses import replace

from Verification.verifier.metadata.schema import EXPECTED_FIELDS
from Verification.verifier.pairs import PairResult, StructureResult
from Verification.verifier.tui.format import (
    format_header,
    interactive_colors_enabled,
)
from Verification.verifier.tui.render import render_case_lines
from Verification.verifier.tui.types import InteractiveCase, MISSING, MetadataField


def metadata_fields(overrides=None, statuses=None):
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
    statuses = statuses or {}
    return tuple(
        MetadataField(
            name=field,
            status=statuses.get(field, "OK"),
            value=values[field],
        )
        for field in EXPECTED_FIELDS
    )


def make_case(*, fields=None, pairs=(), errors=()):
    return InteractiveCase(
        identifier="RUSTSEC-2025-0021",
        package="gix-features",
        metadata_fields=fields or metadata_fields(),
        affected_count=9,
        structure=StructureResult(errors=(), pairs=tuple(pairs)),
        errors=tuple(errors),
    )


def make_pair():
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


def check_color_controls():
    assert interactive_colors_enabled(False, {}) is False
    assert interactive_colors_enabled(None, {"NO_COLOR": ""}) is False
    assert interactive_colors_enabled(None, {}) is True


def check_identical_snapshots_fail_integrity():
    pair = replace(make_pair(), before_after_differ=False)
    case = make_case(
        pairs=(pair,),
        errors=("structure: snapshots are identical",),
    )
    lines = render_case_lines(case, show_diffs=False, width=100)
    text = "\n".join(line.text for line in lines)
    assert f"{'before != after':<28}[FAIL]" in text
    assert f"{'snapshot integrity':<28}[FAIL]" in text
    assert "RESULT                      [FAIL] FAILED" in text


def check_header_fits_terminal():
    header = format_header(
        "RUSTSEC-2025-0021",
        "gix-features",
        case_index=3,
        case_count=5,
        width=80,
    )

    assert header.endswith("Case 4 / 5")
    assert len(header) <= 79


def check_compact_metadata():
    lines = render_case_lines(make_case(), show_diffs=False, width=100)
    text = "\n".join(line.text for line in lines)

    for field in EXPECTED_FIELDS:
        assert f"{field:<28}[OK]" in text

    assert "id                          [OK] RUSTSEC-2025-0021" in text
    assert "package                     [OK] gix-features" in text
    assert "categories                  [OK] crypto-failure" in text
    assert "versions                    [OK] patched: >= 0.41.0" in text


def check_null_empty_and_missing_stay_distinct():
    fields = metadata_fields(
        overrides={"references": None, "CWE": [], "url": MISSING},
        statuses={"url": "FAIL"},
    )
    text = "\n".join(
        line.text
        for line in render_case_lines(
            make_case(fields=fields),
            show_diffs=False,
            width=100,
        )
    )

    assert "references                  [OK] null" in text
    assert "CWE                         [OK] []" in text
    assert "url                         [FAIL] <missing>" in text


def check_found_metadata_is_displayed():
    fields = metadata_fields(
        overrides={"CWE": ["CWE-416"]},
        statuses={"CWE": "FOUND"},
    )
    text = "\n".join(
        line.text
        for line in render_case_lines(
            make_case(fields=fields),
            show_diffs=False,
            width=100,
        )
    )

    assert "CWE                         [FOUND] CWE-416" in text


def check_long_values_wrap_with_indent():
    fields = metadata_fields(
        overrides={
            "url": (
                "https://example.test/a/very/long/advisory/path/that/"
                "cannot-fit-on-one-terminal-line"
            )
        }
    )
    lines = render_case_lines(make_case(fields=fields), show_diffs=False, width=64)
    texts = [line.text for line in lines]
    url_index = next(
        index for index, line in enumerate(texts) if line.startswith("url ")
    )

    assert texts[url_index].startswith(f"{'url':<28}[OK] ")
    url_lines = [texts[url_index]]
    for line in texts[url_index + 1 :]:
        if not line.startswith(" " * 33):
            break
        url_lines.append(line)

    assert len(url_lines) > 1
    assert all(line.startswith(" " * 33) for line in url_lines[1:])
    assert all(len(line) <= 64 for line in url_lines)


def check_hidden_diff_keeps_pair_details():
    case = make_case(pairs=(make_pair(),))
    hidden = "\n".join(
        line.text for line in render_case_lines(case, show_diffs=False, width=100)
    )
    shown = "\n".join(
        line.text for line in render_case_lines(case, show_diffs=True, width=100)
    )

    for expected in (
        "bytes",
        "vulnerable snapshot match",
        "fixed snapshot match",
        "vulnerable != fixed",
        "snapshot integrity",
    ):
        assert expected in hidden

    assert "--- vulnerable" not in hidden
    assert "+++ fixed" not in hidden
    assert "--- vulnerable" in shown
    assert "+++ fixed" in shown


def check_deleted_pair_shows_removal_and_diff():
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
        for line in render_case_lines(
            make_case(pairs=(pair,)), show_diffs=True, width=100
        )
    )

    assert any(
        line.strip().startswith("fixed snapshot match") and "[REMOVED]" in line
        for line in text.splitlines()
    )
    assert any(
        line.strip().startswith("fixed item") and "[REMOVED]" in line
        for line in text.splitlines()
    )
    assert "--- vulnerable" in text
    assert "+++ fixed" in text


def check_ambiguous_match_fails_case():
    pair = PairResult(
        name="key",
        vulnerable_range=None,
        fixed_range=(20, 22),
        vulnerable_text="pub fn key(&self) -> &K { self.key }\n",
        fixed_text="pub fn key(&self) -> &K { self.pair().0 }\n",
        before_after_differ=True,
        vulnerable_fixed_differ=True,
        variants=(),
        errors=(),
        vulnerable_match_count=2,
        fixed_match_count=1,
    )

    text = "\n".join(
        line.text
        for line in render_case_lines(
            make_case(
                pairs=(pair,),
                errors=(
                    "structure: pairs/key/vulnerable.rs has ambiguous matches "
                    "in before.rs",
                ),
            ),
            show_diffs=False,
            width=100,
        )
    )

    assert "vulnerable snapshot match   [FAIL] before.rs: 2 exact matches" in text
    assert "range is ambiguous" in text
    assert "snapshot integrity          [FAIL]" in text
    assert "RESULT                      [FAIL] FAILED" in text


def check_coverage_errors_are_visible_in_case_view():
    text = "\n".join(
        line.text
        for line in render_case_lines(
            make_case(),
            show_diffs=False,
            width=100,
            coverage_errors=("unaccounted seed cases: RUSTSEC-2025-0009",),
        )
    )

    assert "Seed coverage" in text
    assert "unaccounted seed cases: RUSTSEC-2025-0009" in text
    assert "RESULT                      [FAIL] FAILED" in text
