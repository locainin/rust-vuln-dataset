from Verification.verifier.case_metadata import (
    case_id,
    discover_case_dirs,
    is_valid_case_name,
    load_yaml,
)


def test_yaml_loader_uses_safe_yaml_construction(tmp_path):
    yaml_path = tmp_path / "metadata.yaml"
    yaml_path.write_text("id: RUSTSEC-2099-0001\npackage: example\n", encoding="utf-8")

    data = load_yaml(yaml_path)

    assert data == {"id": "RUSTSEC-2099-0001", "package": "example"}


def test_case_id_requires_the_canonical_id_key():
    assert case_id({"id": "RUSTSEC-2099-0001"}) == "RUSTSEC-2099-0001"
    assert case_id({"rustsec_id": "RUSTSEC-2099-0002"}) is None
    assert case_id({"package": "example"}) is None


def test_case_discovery_includes_rustsec_directories_without_metadata(tmp_path):
    first = tmp_path / "RUSTSEC-2099-0001"
    second = tmp_path / "RUSTSEC-2099-0002"
    unrelated = tmp_path / "example"
    first.mkdir()
    second.mkdir()
    unrelated.mkdir()
    (first / "metadata.yaml").write_text("id: RUSTSEC-2099-0001\n", encoding="utf-8")

    discovered = discover_case_dirs(tmp_path)

    assert discovered == [first, second]


def test_case_directory_name_requires_four_digit_year_and_sequence():
    assert is_valid_case_name("RUSTSEC-2025-0021") is True
    assert is_valid_case_name("RUSTSEC-TEST-0001") is False
    assert is_valid_case_name("RUSTSEC-2025-021") is False
    assert is_valid_case_name("rustsec-2025-0021") is False


def test_yaml_loader_preserves_empty_null_and_missing_states(tmp_path):
    yaml_path = tmp_path / "metadata.yaml"
    yaml_path.write_text("CWE: []\nseverity: null\n", encoding="utf-8")

    data = load_yaml(yaml_path)

    assert data["CWE"] == []
    assert data["severity"] is None
    assert "aliases" not in data
