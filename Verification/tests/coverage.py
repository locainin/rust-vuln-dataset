# Seed accounting includes curated cases and explicit exclusions

import pytest

from Verification.verifier.coverage import coverage


def check_complete_coverage():
    assert coverage({"a", "b"}, {"a"}, {"b"}) == []


@pytest.mark.parametrize(
    "source,curated,excluded,message",
    [
        ({"a"}, set(), set(), "no curated cases"),
        ({"a"}, {"a"}, {"a"}, "both curated and excluded: a"),
        ({"a", "b"}, {"a"}, set(), "unaccounted seed cases: b"),
        ({"a"}, {"a", "b"}, set(), "unknown seed cases: b"),
        ({"a"}, {"a"}, {"b"}, "unknown seed cases: b"),
    ],
)
def check_incomplete_coverage(source, curated, excluded, message):
    assert message in coverage(source, curated, excluded)
