import io

from Verification.tests.fixtures import (
    CASE_ID,
    complete_metadata,
    complete_row,
    write_csv,
    write_metadata,
)
from Verification.tests.pairs.helpers import BEFORE, VULNERABLE, make_pair
from Verification.verifier.runner import run_verification


def check_reports_invalid_csv_encoding(tmp_path):
    path = tmp_path / "metadata.csv"
    path.write_bytes(b"\xff")
    output = io.StringIO()
    assert run_verification(path, tmp_path, output, color=False) == 1
    assert "CSV schema/data" in output.getvalue()
    assert "[FAIL]" in output.getvalue()


def write_case(cases_dir, metadata=None):
    case_dir = cases_dir / CASE_ID
    pair_dir = case_dir / "pairs" / "sample"
    write_metadata(case_dir, metadata=metadata)
    make_pair(pair_dir)


def check_summary_includes_metadata_diff_and_totals(tmp_path):
    csv_path = tmp_path / "metadata.csv"
    cases_dir = tmp_path / "manual"
    cases_dir.mkdir()
    write_csv(csv_path, [complete_row(), complete_row("RUSTSEC-2099-0002")])
    write_case(cases_dir)
    output = io.StringIO()

    status = run_verification(
        csv_path,
        cases_dir,
        output,
        expected_source_rows=2,
        excluded_cases={"RUSTSEC-2099-0002"},
        color=False,
    )

    text = output.getvalue()
    assert status == 0
    assert "RustXec source: 2" in text
    assert "Curated cases:  1" in text
    assert "  RustSec affected functions   2" in text
    assert "  Changed pair groups          1" in text
    assert "Metadata                    [OK] 15 fields" in text
    assert "RustSec affected functions  [INFO] 2" in text
    assert any(
        line.strip().startswith("Changed pairs") and "[INFO] 1" in line
        for line in text.splitlines()
    )
    assert any(
        "vulnerable snapshot match" in line and "[OK] before.rs:3-5" in line
        for line in text.splitlines()
    )
    assert any(
        "fixed snapshot match" in line and "[OK] after.rs:3-5" in line
        for line in text.splitlines()
    )
    assert "-    vulnerable_call();" in text
    assert "+    fixed_call();" in text
    assert "package                     [OK]" not in text
    assert "\x1b[" not in text


def check_rejects_empty_curated_corpus(tmp_path):
    csv_path = tmp_path / "metadata.csv"
    cases_dir = tmp_path / "manual"
    cases_dir.mkdir()
    write_csv(csv_path, [complete_row()])
    output = io.StringIO()

    status = run_verification(
        csv_path,
        cases_dir,
        output,
        expected_source_rows=1,
        color=False,
    )

    assert status == 1
    assert "no curated cases" in output.getvalue()


def check_rejects_curated_excluded_case(tmp_path):
    csv_path = tmp_path / "metadata.csv"
    cases_dir = tmp_path / "manual"
    cases_dir.mkdir()
    write_csv(csv_path, [complete_row()])
    write_case(cases_dir)
    output = io.StringIO()

    status = run_verification(
        csv_path,
        cases_dir,
        output,
        expected_source_rows=1,
        excluded_cases={"RUSTSEC-2099-0001"},
        color=False,
    )

    assert status == 1
    assert "both curated and excluded: RUSTSEC-2099-0001" in output.getvalue()


def check_rejects_ambiguous_matches(tmp_path):
    csv_path = tmp_path / "metadata.csv"
    cases_dir = tmp_path / "manual"
    cases_dir.mkdir()
    write_csv(csv_path, [complete_row()])
    write_case(cases_dir)
    pair_dir = cases_dir / "RUSTSEC-2099-0001" / "pairs" / "sample"
    (pair_dir / "before.rs").write_text(
        BEFORE + "\n" + VULNERABLE,
        encoding="utf-8",
    )
    output = io.StringIO()

    status = run_verification(
        csv_path,
        cases_dir,
        output,
        expected_source_rows=1,
        color=False,
    )

    text = output.getvalue()
    assert status == 1
    assert "ambiguous" in text
    assert "vulnerable snapshot match   [FAIL] before.rs: 2 exact matches" in text


def check_reports_found_metadata(tmp_path):
    csv_path = tmp_path / "metadata.csv"
    cases_dir = tmp_path / "manual"
    cases_dir.mkdir()
    write_csv(csv_path, [complete_row()])
    metadata = complete_metadata()
    metadata["CWE"] = ["CWE-125"]
    metadata["severity"] = "Medium"
    write_case(cases_dir, metadata)
    output = io.StringIO()

    status = run_verification(
        csv_path,
        cases_dir,
        output,
        expected_source_rows=1,
        color=False,
    )

    text = output.getvalue()
    assert status == 0
    assert "CWE                         [FOUND] CWE-125" in text
    assert "severity                    [FOUND] Medium" in text


def check_fails_missing_metadata(tmp_path):
    csv_path = tmp_path / "metadata.csv"
    cases_dir = tmp_path / "manual"
    cases_dir.mkdir()
    write_csv(csv_path, [complete_row()])
    (cases_dir / "RUSTSEC-2099-0001").mkdir()
    output = io.StringIO()

    status = run_verification(
        csv_path,
        cases_dir,
        output,
        expected_source_rows=1,
        color=False,
    )

    assert status == 1
    assert "metadata.yaml               [FAIL] missing" in output.getvalue()
    assert output.getvalue().count("metadata.yaml") == 1


def check_reports_values_on_mismatch(tmp_path):
    csv_path = tmp_path / "metadata.csv"
    cases_dir = tmp_path / "manual"
    cases_dir.mkdir()
    write_csv(csv_path, [complete_row()])
    metadata = complete_metadata()
    metadata["package"] = "wrong-package"
    write_case(cases_dir, metadata)
    output = io.StringIO()

    status = run_verification(
        csv_path,
        cases_dir,
        output,
        expected_source_rows=1,
        color=False,
    )

    text = output.getvalue()
    assert status == 1
    assert "package                     [FAIL]" in text
    assert "CSV:  'example'" in text
    assert "YAML: 'wrong-package'" in text


def check_reports_unknown_yaml_id(tmp_path):
    csv_path = tmp_path / "metadata.csv"
    cases_dir = tmp_path / "manual"
    cases_dir.mkdir()
    write_csv(csv_path, [complete_row()])
    metadata = complete_metadata("RUSTSEC-2099-9999")
    write_case(cases_dir, metadata)
    output = io.StringIO()

    status = run_verification(
        csv_path,
        cases_dir,
        output,
        expected_source_rows=1,
        color=False,
    )

    assert status == 1
    assert "no matching CSV entry" in output.getvalue()
