import pytest

from Verification.verifier.pairs import check_structure

from ..helpers import make_case, make_pair


@pytest.mark.parametrize(
    "before,after,snippet",
    [
        (
            "fn foo() {\n    old();\n}\n",
            "fn foo(){old();}\n",
            "fn foo() {\n    old();\n}\n",
        ),
        (
            "impl Foo {\n fn foo() { old(); }\n}\n",
            "impl Foo{fn foo(){old();}}\n",
            " fn foo() { old(); }\n",
        ),
        (
            "unsafe impl Send for Foo {}\n",
            "unsafe impl Send for Foo{}\n",
            "unsafe impl Send for Foo {}\n",
        ),
        (
            "impl<T> Foo<T> {\n fn foo() { old(); }\n}\n",
            "impl<U: Send> Foo<U>{fn foo(){old();}}\n",
            " fn foo() { old(); }\n",
        ),
    ],
)
def check_reformatting_does_not_delete_item(tmp_path, before, after, snippet):
    case = make_case(tmp_path)
    pair = case / "pairs" / "sample"
    make_pair(pair)
    for name, text in [
        ("before.rs", before),
        ("vulnerable.rs", snippet),
        ("after.rs", after),
        ("fixed.rs", ""),
    ]:
        (pair / name).write_text(text)
    result = check_structure(case)
    assert any("still exists" in error for error in result.errors)
    assert not result.pairs[0].fixed_removed


def check_same_method_name_in_other_impl(tmp_path):
    case = make_case(tmp_path)
    pair = case / "pairs" / "sample"
    make_pair(pair)
    (pair / "before.rs").write_text("impl Foo {\n fn foo() { old(); }\n}\n")
    (pair / "vulnerable.rs").write_text(" fn foo() { old(); }\n")
    (pair / "after.rs").write_text("impl Bar { fn foo() { new(); } }\n")
    (pair / "fixed.rs").write_text("")
    result = check_structure(case)
    assert result.errors == ()
    assert result.pairs[0].fixed_removed


def check_deleted_pair_allows_empty_fixed(tmp_path):
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


def check_deleted_pair_rejects_empty_vulnerable(tmp_path):
    case_dir = make_case(tmp_path)
    pair_dir = case_dir / "pairs" / "deleted"
    make_pair(pair_dir)
    (pair_dir / "after.rs").write_text("fn replacement() {}\n", encoding="utf-8")
    (pair_dir / "vulnerable.rs").write_text("", encoding="utf-8")
    (pair_dir / "fixed.rs").write_text("", encoding="utf-8")

    result = check_structure(case_dir)

    assert "pairs/deleted/vulnerable.rs is empty" in result.errors
    assert result.pairs[0].fixed_removed is False
