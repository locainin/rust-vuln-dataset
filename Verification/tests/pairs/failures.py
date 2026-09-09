# Read failures stay visible without stopping the remaining pair checks

from pathlib import Path

from Verification.verifier.pairs import check_structure

from .helpers import make_case, make_pair


def check_unreadable_source_keeps_later_pairs(tmp_path, monkeypatch):
    case = make_case(tmp_path)
    first = case / "pairs" / "first"
    make_pair(first)
    make_pair(case / "pairs" / "second")
    read = Path.read_bytes

    def unreadable(path):
        if path == first / "before.rs":
            raise PermissionError("source is not readable")
        return read(path)

    monkeypatch.setattr(Path, "read_bytes", unreadable)
    result = check_structure(case)
    assert any(
        "before.rs" in error and "not readable" in error for error in result.errors
    )
    assert result.pair_count == 2
    assert result.pairs[1].errors == ()
