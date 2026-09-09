# Metadata inspection keeps identity failures separate from field differences

import pytest
import yaml

from Verification.verifier.metadata.inspection import inspect


@pytest.fixture
def case(tmp_path):
    directory = tmp_path / "RUSTSEC-2099-0001"
    directory.mkdir()
    return directory


def check_missing_file(case):
    result = inspect(case, {})
    assert result.errors == ["metadata.yaml is missing"]
    assert result.data is None
    assert result.row is None


def check_invalid_yaml(case):
    (case / "metadata.yaml").write_text("id: [")
    result = inspect(case, {})
    assert len(result.errors) == 1
    assert result.errors[0].startswith("metadata.yaml:")


def check_invalid_encoding_is_reported(case):
    (case / "metadata.yaml").write_bytes(b"id: \xff\n")
    result = inspect(case, {})
    assert any("metadata.yaml:" in error for error in result.errors)


@pytest.mark.parametrize(
    "document",
    [
        "id: RUSTSEC-2099-0001\nid: RUSTSEC-2099-0001\n",
        "versions:\n  patched: []\n  patched: []\n",
    ],
)
def check_duplicate_keys_are_reported(case, document):
    (case / "metadata.yaml").write_text(document)
    result = inspect(case, {})
    assert any("duplicate YAML key" in error for error in result.errors)


@pytest.mark.parametrize("document", [None, "id: ["])
def check_bad_name_survives_file_failure(tmp_path, document):
    case = tmp_path / "RUSTSEC-invalid"
    case.mkdir()
    if document is not None:
        (case / "metadata.yaml").write_text(document)
    result = inspect(case, {})
    assert "invalid case directory name: RUSTSEC-invalid" in result.errors
    assert len(result.errors) == 2


@pytest.mark.parametrize(
    "data,identity_error",
    [
        (None, "YAML id is missing or invalid"),
        ([], "YAML id is missing or invalid"),
        (
            {"id": "RUSTSEC-2099-0002"},
            "directory name 'RUSTSEC-2099-0001' does not match YAML id",
        ),
    ],
)
def check_identity_errors(tmp_path, data, identity_error):
    case = tmp_path / "RUSTSEC-2099-0001"
    case.mkdir()
    (case / "metadata.yaml").write_text(yaml.safe_dump(data))
    result = inspect(case, {})
    assert "no matching CSV entry" in result.errors
    assert any(identity_error in error for error in result.errors)
