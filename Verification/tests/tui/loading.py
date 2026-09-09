from Verification.tests.fixtures import complete_row, write_csv, write_metadata
from Verification.verifier.tui.load import load_data


def check_reports_unaccounted_source_case(tmp_path):
    csv_path = tmp_path / "metadata.csv"
    cases_dir = tmp_path / "manual"
    cases_dir.mkdir()
    first = "RUSTSEC-2099-0001"
    second = "RUSTSEC-2099-0002"
    write_csv(csv_path, [complete_row(first), complete_row(second)])
    write_metadata(cases_dir / first, first)

    result = load_data(csv_path, cases_dir, expected_source_rows=2)

    assert result.coverage_errors == ("unaccounted seed cases: RUSTSEC-2099-0002",)
    assert len(result.cases) == 1
    assert result.exit_status == 1


def check_marks_duplicate_yaml_ids(tmp_path):
    csv_path = tmp_path / "metadata.csv"
    cases_dir = tmp_path / "manual"
    cases_dir.mkdir()
    first = "RUSTSEC-2099-0001"
    second = "RUSTSEC-2099-0002"
    write_csv(csv_path, [complete_row(first), complete_row(second)])
    write_metadata(cases_dir / first, first)
    write_metadata(cases_dir / second, first)

    result = load_data(csv_path, cases_dir, expected_source_rows=2)

    assert any(
        "duplicate curated case id: RUSTSEC-2099-0001" in error
        for error in result.cases[1].errors
    )
    assert result.exit_status == 1


def check_reports_empty_curated_directory(tmp_path):
    csv_path = tmp_path / "metadata.csv"
    cases_dir = tmp_path / "manual"
    cases_dir.mkdir()
    write_csv(csv_path, [complete_row("RUSTSEC-2099-0001")])

    result = load_data(csv_path, cases_dir, expected_source_rows=1)

    assert result.cases == ()
    assert result.coverage_errors == (
        "no curated cases",
        "unaccounted seed cases: RUSTSEC-2099-0001",
    )
    assert result.exit_status == 1


def check_reports_missing_metadata_once(tmp_path):
    identifier = "RUSTSEC-2099-0001"
    csv_path = tmp_path / "metadata.csv"
    cases = tmp_path / "manual"
    (cases / identifier).mkdir(parents=True)
    write_csv(csv_path, [complete_row(identifier)])
    result = load_data(csv_path, cases, expected_source_rows=1)
    errors = result.cases[0].errors
    assert sum("metadata.yaml is missing" in error for error in errors) == 1


def check_package_uses_directory_id(tmp_path):
    first, second = "RUSTSEC-2099-0001", "RUSTSEC-2099-0002"
    csv_path = tmp_path / "metadata.csv"
    cases = tmp_path / "manual"
    write_csv(
        csv_path,
        [
            {**complete_row(first), "package": "first-package"},
            {**complete_row(second), "package": "second-package"},
        ],
    )
    write_metadata(cases / first, second)
    result = load_data(csv_path, cases, expected_source_rows=2)
    assert result.cases[0].identifier == first
    assert result.cases[0].package == "first-package"
    assert any("does not match YAML id" in error for error in result.cases[0].errors)
