import subprocess

import pytest

from Verification.verifier.pairs import check_pair, check_structure

from ..helpers import (
    AFTER,
    BEFORE,
    FIXED,
    NORMALIZED_FIXED,
    NORMALIZED_VULNERABLE,
    VULNERABLE,
    make_case,
    make_pair,
)


@pytest.mark.parametrize(
    "side,statement", [("vulnerable.rs", "vulnerable_call"), ("fixed.rs", "fixed_call")]
)
def check_statement_snippet_rejected(tmp_path, side, statement):
    case = make_case(tmp_path)
    pair = case / "pairs" / "sample"
    make_pair(pair)
    (pair / side).write_text(f"        {statement}();\n")
    assert any("complete Rust item" in error for error in check_structure(case).errors)


def check_statement_variant_rejected(tmp_path):
    case = make_case(tmp_path)
    pair = case / "pairs" / "sample"
    make_pair(pair)
    (pair / "vulnerable-part.rs").write_text("        vulnerable_call();\n")
    assert any("complete Rust item" in error for error in check_structure(case).errors)


def check_parser_timeout_reported(tmp_path, monkeypatch):
    case = make_case(tmp_path)
    make_pair(case / "pairs" / "sample")

    def timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired("ast-grep", 30)

    monkeypatch.setattr("Verification.verifier.pairs.matching.curated_node", timeout)
    result = check_structure(case)
    assert any("timed out" in error for error in result.errors)


def check_truncated_function_rejected(tmp_path):
    case = make_case(tmp_path)
    pair = case / "pairs" / "sample"
    make_pair(pair)
    truncated = "fn foo() -> Result<(), Error> {\n    work();\n"
    (pair / "before.rs").write_text(truncated + "    Ok(())\n}\n")
    (pair / "vulnerable.rs").write_text(truncated)
    assert any("complete Rust item" in error for error in check_structure(case).errors)


def check_dropped_attribute_rejected(tmp_path):
    case = make_case(tmp_path)
    pair = case / "pairs" / "sample"
    make_pair(pair)
    (pair / "before.rs").write_text("#[inline]\n" + VULNERABLE)
    assert any("complete Rust item" in error for error in check_structure(case).errors)


@pytest.mark.parametrize(
    "attribute",
    ("#[inline]", '#[cfg(feature = "x")]', "#[corresponds(foo)]"),
    ids=("inline", "cfg", "corresponds"),
)
def check_attached_attribute_is_required(tmp_path, attribute):
    pair = tmp_path / "single_attribute"
    pair.mkdir()
    before = f"{attribute}\npub fn sample() -> u8 {{\n    1\n}}\n".encode()
    after = f"{attribute}\npub fn sample() -> u8 {{\n    2\n}}\n".encode()

    (pair / "before.rs").write_bytes(before)
    (pair / "after.rs").write_bytes(after)
    (pair / "vulnerable.rs").write_bytes(before)
    (pair / "fixed.rs").write_bytes(after)
    assert check_pair(pair).errors == ()

    for side in ("vulnerable.rs", "fixed.rs"):
        original = (pair / side).read_bytes()
        (pair / side).write_bytes(original.split(b"\n", 1)[1])
        result = check_pair(pair)
        assert any(
            f"{side} is not a complete Rust item" in error for error in result.errors
        )
        (pair / side).write_bytes(original)

    assert check_pair(pair).errors == ()


@pytest.mark.parametrize(
    "before,after",
    [
        ("#[inline]\nfn item() { old(); }\n", "#[inline]\nfn item() { new(); }\n"),
        (
            "#[derive(Clone)]\npub struct Item { value: u8 }\n",
            "#[derive(Debug)]\npub struct Item { value: u8 }\n",
        ),
        (
            "unsafe impl<T> Send for Item<T> {}\n",
            "unsafe impl<T: Send> Send for Item<T> {}\n",
        ),
        (
            "#[macro_export]\nmacro_rules! item { () => { old(); }; }\n",
            "#[macro_export]\nmacro_rules! item { () => { new(); }; }\n",
        ),
    ],
)
def check_curated_item_kinds_pass(tmp_path, before, after):
    case = make_case(tmp_path)
    pair = case / "pairs" / "sample"
    make_pair(pair)
    for name, text in [
        ("before.rs", before),
        ("vulnerable.rs", before),
        ("after.rs", after),
        ("fixed.rs", after),
    ]:
        (pair / name).write_text(text)
    assert check_structure(case).errors == ()


def check_inline_method_item_passes(tmp_path):
    case = make_case(tmp_path)
    pair = case / "pairs" / "sample"
    make_pair(pair)
    for snapshot, snippet, call in [
        ("before.rs", "vulnerable.rs", "old"),
        ("after.rs", "fixed.rs", "new"),
    ]:
        item = f"fn method() {{ {call}(); }}"
        (pair / snapshot).write_text(f"impl Example {{ {item} }}\n")
        (pair / snippet).write_text(item)
    assert check_structure(case).errors == ()


@pytest.mark.parametrize("attribute", ["", "#[inline]\n"])
def check_quoted_method_keeps_attributes(tmp_path, attribute):
    case = make_case(tmp_path)
    pair = case / "pairs" / "sample"
    make_pair(pair)
    for snapshot, snippet, call in [
        ("before.rs", "vulnerable.rs", "old"),
        ("after.rs", "fixed.rs", "new"),
    ]:
        item = attribute + f"fn method() {{ #{call}(); }}\n"
        (pair / snapshot).write_text(f"fn build() {{ quote! {{\n{item}}} }}\n")
        (pair / snippet).write_text(item)
    assert check_structure(case).errors == ()
    if attribute:
        (pair / "vulnerable.rs").write_text("fn method() { #old(); }\n")
        assert any(
            "complete Rust item" in error for error in check_structure(case).errors
        )


def check_macro_string_is_not_item(tmp_path):
    case = make_case(tmp_path)
    pair = case / "pairs" / "sample"
    make_pair(pair)
    (pair / "before.rs").write_text('quote! { "fn imaginary() {}" }\n')
    (pair / "vulnerable.rs").write_text("fn imaginary() {}")
    assert any("complete Rust item" in error for error in check_structure(case).errors)


def check_pair_matches_snapshots(tmp_path):
    case_dir = make_case(tmp_path)
    make_pair(case_dir / "pairs" / "sample")

    result = check_structure(case_dir)

    assert result.errors == ()
    assert result.pair_count == 1
    assert result.vulnerable_snippet_count == 1
    assert result.pairs[0].vulnerable_range == (3, 5)
    assert result.pairs[0].fixed_range == (3, 5)


def check_snapshots_must_differ(tmp_path):
    case_dir = make_case(tmp_path)
    pair_dir = case_dir / "pairs" / "sample"
    make_pair(pair_dir)
    (pair_dir / "after.rs").write_text(BEFORE, encoding="utf-8")

    result = check_structure(case_dir)

    assert "pairs/sample/before.rs and after.rs are identical" in result.errors


def check_snippets_must_differ(tmp_path):
    case_dir = make_case(tmp_path)
    pair_dir = case_dir / "pairs" / "sample"
    make_pair(pair_dir)
    (pair_dir / "fixed.rs").write_text(VULNERABLE, encoding="utf-8")

    result = check_structure(case_dir)

    assert "pairs/sample/vulnerable.rs and fixed.rs are identical" in result.errors


def check_vulnerable_matches_before(tmp_path):
    case_dir = make_case(tmp_path)
    pair_dir = case_dir / "pairs" / "sample"
    make_pair(pair_dir)
    (pair_dir / "vulnerable.rs").write_text(
        NORMALIZED_VULNERABLE,
        encoding="utf-8",
    )

    result = check_structure(case_dir)

    assert (
        "pairs/sample/vulnerable.rs is not an exact substring of before.rs"
        in result.errors
    )


def check_fixed_matches_after(tmp_path):
    case_dir = make_case(tmp_path)
    pair_dir = case_dir / "pairs" / "sample"
    make_pair(pair_dir)
    (pair_dir / "fixed.rs").write_text(NORMALIZED_FIXED, encoding="utf-8")

    result = check_structure(case_dir)

    assert (
        "pairs/sample/fixed.rs is not an exact substring of after.rs" in result.errors
    )


def check_duplicate_vulnerable_match(tmp_path):
    case_dir = make_case(tmp_path)
    pair_dir = case_dir / "pairs" / "sample"
    make_pair(pair_dir)
    (pair_dir / "before.rs").write_text(
        BEFORE + "\n" + VULNERABLE,
        encoding="utf-8",
    )

    result = check_structure(case_dir)

    assert any("ambiguous" in error for error in result.errors)
    assert result.pairs[0].vulnerable_range is None
    assert result.pairs[0].vulnerable_match_count == 2


def check_duplicate_fixed_match(tmp_path):
    case_dir = make_case(tmp_path)
    pair_dir = case_dir / "pairs" / "sample"
    make_pair(pair_dir)
    (pair_dir / "after.rs").write_text(
        AFTER + "\n" + FIXED,
        encoding="utf-8",
    )

    result = check_structure(case_dir)

    assert any("ambiguous" in error for error in result.errors)
    assert result.pairs[0].fixed_range is None
    assert result.pairs[0].fixed_match_count == 2


def check_variants_are_counted(tmp_path):
    case_dir = make_case(tmp_path)
    pair_dir = case_dir / "pairs" / "sample"
    make_pair(pair_dir)
    variant = "    pub fn sample() {\n        alternate_vulnerable_call();\n    }\n"
    (pair_dir / "before.rs").write_text(BEFORE + "\n" + variant, encoding="utf-8")
    (pair_dir / "vulnerable-fast.rs").write_text(variant, encoding="utf-8")

    result = check_structure(case_dir)

    assert result.errors == ()
    assert result.vulnerable_snippet_count == 2
    assert result.pairs[0].variants[0].name == "fast"


def check_duplicate_variant_match(tmp_path):
    case_dir = make_case(tmp_path)
    pair_dir = case_dir / "pairs" / "sample"
    make_pair(pair_dir)
    variant = "    pub fn variant() {\n        vulnerable_call();\n    }\n"
    (pair_dir / "before.rs").write_text(
        BEFORE + "\n" + variant + "\n" + variant,
        encoding="utf-8",
    )
    (pair_dir / "vulnerable-fast.rs").write_text(variant, encoding="utf-8")

    result = check_structure(case_dir)

    assert any("ambiguous" in error for error in result.errors)
    assert result.pairs[0].variants[0].source_range is None
    assert result.pairs[0].variants[0].source_match_count == 2


def check_variant_must_match_before_and_differ(tmp_path):
    case_dir = make_case(tmp_path)
    pair_dir = case_dir / "pairs" / "sample"
    make_pair(pair_dir)
    (pair_dir / "vulnerable-fast.rs").write_text(FIXED, encoding="utf-8")

    result = check_structure(case_dir)

    assert (
        "pairs/sample/vulnerable-fast.rs is not an exact substring of before.rs"
        in result.errors
    )
    assert "pairs/sample/vulnerable-fast.rs and fixed.rs are identical" in result.errors
