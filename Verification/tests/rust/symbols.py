import pytest

from Verification.verifier.rust.symbols import target


@pytest.mark.parametrize(
    "name,slug",
    [("Ref", "ref"), ("RefMutMulti", "ref_mut_multi"), ("HTTPRef", "http_ref")],
)
def check_type_names_use_snake_case(name, slug):
    assert target(f"map_{slug}_key", (f"crate::map::{name}::key",)) == (
        "map",
        name,
        "key",
    )


def check_flattened_path_collisions_fail():
    assert (
        target(
            "map_ref_mut_key", ("crate::map::RefMut::key", "crate::map_ref::Mut::key")
        )
        is None
    )


def check_unprefixed_paths_keep_their_first_segment():
    assert target("map_ref_mut_key", ("map::RefMut::key",)) == (
        "map",
        "RefMut",
        "key",
    )
