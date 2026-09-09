# Repeated snippets need agreement between public names and Rust declarations

import pytest

from Verification.verifier.pairs import check_pair


@pytest.fixture
def pair(tmp_path):
    path = tmp_path / "map_ref_mut_key"
    path.mkdir()
    old = "    fn key() { old(); }\n"
    new = "    fn key() { new(); }\n"
    for name, text in {
        "before.rs": f"impl Ref {{\n{old}}}\nimpl RefMut {{\n{old}}}\n",
        "after.rs": f"impl Ref {{\n{new}}}\nimpl RefMut {{\n{new}}}\n",
        "vulnerable.rs": old,
        "fixed.rs": new,
    }.items():
        (path / name).write_text(text)
    return path


def check_public_name_selects_second_impl(pair):
    result = check_pair(pair, ("crate::map::RefMut::key",))
    assert result.errors == ()
    assert result.vulnerable_range == result.fixed_range == (5, 5)
    assert result.vulnerable_match_count == result.fixed_match_count == 2


@pytest.mark.parametrize(
    "functions",
    [
        (),
        ("crate::map::Ref::key",),
        ("crate::other::RefMut::key",),
        ("one::map::RefMut::key", "two::map::RefMut::key"),
    ],
)
def check_unproven_name_stays_ambiguous(pair, functions):
    result = check_pair(pair, functions)
    assert any("ambiguous" in error for error in result.errors)
    assert result.vulnerable_range is None


def check_same_type_candidates_stay_ambiguous(pair):
    for name in ("before.rs", "after.rs"):
        path = pair / name
        path.write_text(path.read_text().replace("impl Ref {", "impl RefMut {"))
    result = check_pair(pair, ("crate::map::RefMut::key",))
    assert any("ambiguous" in error for error in result.errors)


@pytest.mark.parametrize("snapshot,call", [("before.rs", "old"), ("after.rs", "new")])
def check_resolved_pair_cannot_switch_receiver(pair, snapshot, call):
    (pair / snapshot).write_text(f"impl Ref {{\n    fn key() {{ {call}(); }}\n}}\n")
    result = check_pair(pair, ("crate::map::RefMut::key",))
    assert result.errors


def check_unique_context_mismatch_fails(pair):
    for name, call in (("before.rs", "old"), ("after.rs", "new")):
        (pair / name).write_text(f"impl Ref {{\n    fn key() {{ {call}(); }}\n}}\n")

    result = check_pair(pair, ("crate::map::RefMut::key",))

    assert result.errors
    assert any("published function context" in error for error in result.errors)


def check_trait_method_is_not_an_inherent_method(pair):
    path = pair / "before.rs"
    path.write_text(
        path.read_text().replace("impl RefMut {", "impl Trait for RefMut {")
    )
    result = check_pair(pair, ("crate::map::RefMut::key",))
    assert any("ambiguous" in error for error in result.errors)


def check_selected_item_keeps_attributes(pair):
    path = pair / "before.rs"
    path.write_text(
        path.read_text().replace("impl RefMut {", "impl RefMut {\n    #[inline]")
    )
    result = check_pair(pair, ("crate::map::RefMut::key",))
    assert result.vulnerable_range is None
    assert result.errors


def check_nested_function_is_not_a_method(pair):
    path = pair / "before.rs"
    path.write_text(
        path.read_text().replace(
            "impl RefMut {\n    fn key() { old(); }\n}",
            "impl RefMut { fn outer() {\n    fn key() { old(); }\n} }",
        )
    )
    result = check_pair(pair, ("crate::map::RefMut::key",))
    assert result.vulnerable_range is None
    assert any("ambiguous" in error for error in result.errors)


@pytest.mark.parametrize(
    "header", ["impl<T: Clone> RefMut<T>", "impl<T> RefMut <T>", "impl map::RefMut"]
)
def check_generic_and_qualified_types_pass(pair, header):
    for name in ("before.rs", "after.rs"):
        path = pair / name
        path.write_text(path.read_text().replace("impl RefMut", header))
    assert check_pair(pair, ("crate::map::RefMut::key",)).errors == ()


@pytest.mark.parametrize("module,valid", [("map", True), ("other", False)])
def check_visible_modules_must_agree(pair, module, valid):
    for name in ("before.rs", "after.rs"):
        path = pair / name
        path.write_text(f"mod {module} {{\n" + path.read_text() + "}\n")
    result = check_pair(pair, ("crate::map::RefMut::key",))
    assert (result.errors == ()) is valid


def check_associated_type_is_not_its_outer_type(pair):
    path = pair / "before.rs"
    path.write_text(
        path.read_text().replace("impl RefMut", "impl<T> RefMut<T>::Inner<T>")
    )
    result = check_pair(pair, ("crate::map::RefMut::key",))
    assert result.vulnerable_range is None
    assert result.errors


def check_selected_deleted_item_passes(pair):
    (pair / "after.rs").write_text("impl Ref {\n    fn key() { old(); }\n}\n")
    (pair / "fixed.rs").write_text("")
    result = check_pair(pair, ("crate::map::RefMut::key",))
    assert result.errors == ()
    assert result.fixed_removed


def check_inline_deletion_keeps_selected_offset(pair):
    snippet = "fn key() { old(); }"
    (pair / "before.rs").write_text(
        f"impl Ref {{ {snippet} }} impl RefMut {{ {snippet} }}"
    )
    (pair / "after.rs").write_text(f"impl Ref {{ {snippet} }}")
    (pair / "vulnerable.rs").write_text(snippet)
    (pair / "fixed.rs").write_text("")
    result = check_pair(pair, ("crate::map::RefMut::key",))
    assert result.errors == ()
    assert result.fixed_removed
