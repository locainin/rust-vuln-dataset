from Verification.verifier.pairs import check_structure

from ..helpers import make_case, make_pair


def check_missing_pair_file_rejected(tmp_path):
    case_dir = make_case(tmp_path)
    pair_dir = case_dir / "pairs" / "sample"
    make_pair(pair_dir)
    (pair_dir / "fixed.rs").unlink()

    result = check_structure(case_dir)

    assert "pairs/sample/fixed.rs is missing" in result.errors


def check_extra_pair_file_is_ignored(tmp_path):
    case_dir = make_case(tmp_path)
    pair_dir = case_dir / "pairs" / "sample"
    make_pair(pair_dir)
    (pair_dir / "notes.txt").write_text("reviewed\n", encoding="utf-8")

    result = check_structure(case_dir)

    assert result.errors == ()


def check_root_sources_need_pairs_dir(tmp_path):
    case_dir = tmp_path / "RUSTSEC-2099-0001"
    case_dir.mkdir()
    (case_dir / "metadata.yaml").write_text(
        "id: RUSTSEC-2099-0001\n",
        encoding="utf-8",
    )
    result = check_structure(case_dir)

    assert result.pair_count == 0
    assert "pairs/ is missing" in result.errors
