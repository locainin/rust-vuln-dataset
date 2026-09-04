from Verification.verifier.dataset_structure import check_structure


# Full snapshots include surrounding code so snippet containment is meaningful
BEFORE = "fn helper() {}\n\n    pub fn sample() {\n        vulnerable_call();\n    }\n"
AFTER = "fn helper() {}\n\n    pub fn sample() {\n        fixed_call();\n    }\n"
VULNERABLE = "    pub fn sample() {\n        vulnerable_call();\n    }\n"
FIXED = "    pub fn sample() {\n        fixed_call();\n    }\n"
NORMALIZED_VULNERABLE = "pub fn sample() {\n    vulnerable_call();\n}\n"
NORMALIZED_FIXED = "pub fn sample() {\n    fixed_call();\n}\n"


def make_case(tmp_path):
    case_dir = tmp_path / "RUSTSEC-2099-0001"
    (case_dir / "pairs").mkdir(parents=True)
    (case_dir / "metadata.yaml").write_text("id: RUSTSEC-2099-0001\n", encoding="utf-8")
    return case_dir


def make_pair(pair_dir):
    pair_dir.mkdir(parents=True)
    (pair_dir / "before.rs").write_text(BEFORE, encoding="utf-8")
    (pair_dir / "after.rs").write_text(AFTER, encoding="utf-8")
    (pair_dir / "vulnerable.rs").write_text(VULNERABLE, encoding="utf-8")
    (pair_dir / "fixed.rs").write_text(FIXED, encoding="utf-8")


def test_pair_accepts_distinct_nonempty_sources_with_exact_snapshot_matches(tmp_path):
    case_dir = make_case(tmp_path)
    make_pair(case_dir / "pairs" / "sample")

    result = check_structure(case_dir)

    assert result.errors == ()
    assert result.pair_count == 1
    assert result.vulnerable_snippet_count == 1
    assert result.pairs[0].vulnerable_range == (3, 5)
    assert result.pairs[0].fixed_range == (3, 5)


def test_required_pair_file_must_exist(tmp_path):
    case_dir = make_case(tmp_path)
    pair_dir = case_dir / "pairs" / "sample"
    make_pair(pair_dir)
    (pair_dir / "fixed.rs").unlink()

    result = check_structure(case_dir)

    assert "pairs/sample/fixed.rs is missing" in result.errors


def test_empty_fixed_file_is_rejected_when_vulnerable_item_remains(tmp_path):
    case_dir = make_case(tmp_path)
    pair_dir = case_dir / "pairs" / "sample"
    make_pair(pair_dir)
    (pair_dir / "after.rs").write_text(
        BEFORE + "fn replacement() {}\n",
        encoding="utf-8",
    )
    (pair_dir / "fixed.rs").write_text("", encoding="utf-8")

    result = check_structure(case_dir)

    assert result.pairs[0].fixed_removed is False
    assert (
        "pairs/sample/vulnerable.rs still exists in after.rs despite empty fixed.rs"
        in result.errors
    )


def test_deleted_function_pair_accepts_empty_fixed_snippet_when_absent_after_source(
    tmp_path,
):
    case_dir = make_case(tmp_path)
    pair_dir = case_dir / "pairs" / "deleted"
    make_pair(pair_dir)
    (pair_dir / "after.rs").write_text("fn replacement() {}\n", encoding="utf-8")
    (pair_dir / "fixed.rs").write_text("", encoding="utf-8")

    result = check_structure(case_dir)

    assert result.errors == ()
    assert result.pairs[0].fixed_removed is True
    assert result.pairs[0].fixed_range is None
    assert result.pairs[0].before_after_differ is True
    assert result.pairs[0].vulnerable_fixed_differ is True


def test_deleted_function_pair_rejects_vulnerable_snippet_still_present_after_fix(
    tmp_path,
):
    case_dir = make_case(tmp_path)
    pair_dir = case_dir / "pairs" / "deleted"
    make_pair(pair_dir)
    (pair_dir / "after.rs").write_text(
        BEFORE + "fn replacement() {}\n",
        encoding="utf-8",
    )
    (pair_dir / "fixed.rs").write_text("", encoding="utf-8")

    result = check_structure(case_dir)

    assert result.pairs[0].fixed_removed is False
    assert (
        "pairs/deleted/vulnerable.rs still exists in after.rs despite empty fixed.rs"
        in result.errors
    )


def test_deleted_function_pair_rejects_empty_vulnerable_snippet(tmp_path):
    case_dir = make_case(tmp_path)
    pair_dir = case_dir / "pairs" / "deleted"
    make_pair(pair_dir)
    (pair_dir / "after.rs").write_text("fn replacement() {}\n", encoding="utf-8")
    (pair_dir / "vulnerable.rs").write_text("", encoding="utf-8")
    (pair_dir / "fixed.rs").write_text("", encoding="utf-8")

    result = check_structure(case_dir)

    assert "pairs/deleted/vulnerable.rs is empty" in result.errors
    assert result.pairs[0].fixed_removed is False


def test_before_and_after_must_differ(tmp_path):
    case_dir = make_case(tmp_path)
    pair_dir = case_dir / "pairs" / "sample"
    make_pair(pair_dir)
    (pair_dir / "after.rs").write_text(BEFORE, encoding="utf-8")

    result = check_structure(case_dir)

    assert "pairs/sample/before.rs and after.rs are identical" in result.errors


def test_vulnerable_and_fixed_must_differ(tmp_path):
    case_dir = make_case(tmp_path)
    pair_dir = case_dir / "pairs" / "sample"
    make_pair(pair_dir)
    (pair_dir / "fixed.rs").write_text(VULNERABLE, encoding="utf-8")

    result = check_structure(case_dir)

    assert "pairs/sample/vulnerable.rs and fixed.rs are identical" in result.errors


def test_vulnerable_must_be_exact_before_substring(tmp_path):
    case_dir = make_case(tmp_path)
    pair_dir = case_dir / "pairs" / "sample"
    make_pair(pair_dir)
    (pair_dir / "vulnerable.rs").write_text(NORMALIZED_VULNERABLE, encoding="utf-8")

    result = check_structure(case_dir)

    assert (
        "pairs/sample/vulnerable.rs is not an exact substring of before.rs"
        in result.errors
    )


def test_fixed_must_be_exact_after_substring(tmp_path):
    case_dir = make_case(tmp_path)
    pair_dir = case_dir / "pairs" / "sample"
    make_pair(pair_dir)
    (pair_dir / "fixed.rs").write_text(NORMALIZED_FIXED, encoding="utf-8")

    result = check_structure(case_dir)

    assert (
        "pairs/sample/fixed.rs is not an exact substring of after.rs" in result.errors
    )


def test_vulnerable_duplicate_snapshot_matches_are_reported_as_ambiguous(tmp_path):
    case_dir = make_case(tmp_path)
    pair_dir = case_dir / "pairs" / "sample"
    make_pair(pair_dir)
    (pair_dir / "before.rs").write_text(
        BEFORE + "\n" + VULNERABLE,
        encoding="utf-8",
    )

    result = check_structure(case_dir)

    assert result.errors == ()
    assert result.pairs[0].vulnerable_range is None
    assert result.pairs[0].vulnerable_match_count == 2


def test_fixed_duplicate_snapshot_matches_are_reported_as_ambiguous(tmp_path):
    case_dir = make_case(tmp_path)
    pair_dir = case_dir / "pairs" / "sample"
    make_pair(pair_dir)
    (pair_dir / "after.rs").write_text(
        AFTER + "\n" + FIXED,
        encoding="utf-8",
    )

    result = check_structure(case_dir)

    assert result.errors == ()
    assert result.pairs[0].fixed_range is None
    assert result.pairs[0].fixed_match_count == 2


def test_vulnerable_variants_are_validated_and_counted(tmp_path):
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


def test_vulnerable_variant_duplicate_matches_are_reported_as_ambiguous(tmp_path):
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

    assert result.errors == ()
    assert result.pairs[0].variants[0].source_range is None
    assert result.pairs[0].variants[0].source_match_count == 2


def test_vulnerable_variant_must_match_before_and_differ_from_fixed(tmp_path):
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


def test_unrelated_extra_pair_file_is_informational(tmp_path):
    case_dir = make_case(tmp_path)
    pair_dir = case_dir / "pairs" / "sample"
    make_pair(pair_dir)
    (pair_dir / "notes.txt").write_text("reviewed\n", encoding="utf-8")

    result = check_structure(case_dir)

    assert result.errors == ()


def test_root_sources_do_not_replace_pairs_directory(tmp_path):
    case_dir = tmp_path / "RUSTSEC-2099-0001"
    case_dir.mkdir()
    (case_dir / "metadata.yaml").write_text("id: RUSTSEC-2099-0001\n", encoding="utf-8")
    for filename, text in (
        ("before.rs", BEFORE),
        ("after.rs", AFTER),
        ("vulnerable.rs", VULNERABLE),
        ("fixed.rs", FIXED),
    ):
        (case_dir / filename).write_text(text, encoding="utf-8")

    result = check_structure(case_dir)

    assert result.pair_count == 0
    assert "pairs/ is missing" in result.errors
