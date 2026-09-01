import csv
import io

import yaml

from Verification.verifier.runner import run_verification
from Verification.verifier.schema import EXPECTED_FIELDS


BEFORE = "fn helper() {}\n\n    pub fn sample() {\n        vulnerable_call();\n    }\n"
AFTER = "fn helper() {}\n\n    pub fn sample() {\n        fixed_call();\n    }\n"
VULNERABLE = "    pub fn sample() {\n        vulnerable_call();\n    }\n"
FIXED = "    pub fn sample() {\n        fixed_call();\n    }\n"


def write_csv(path, rows):
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=EXPECTED_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def complete_row(case_id="RUSTSEC-2099-0001"):
    return {
        "id": case_id,
        "package": "example",
        "date": "2025-01-01",
        "categories": '["memory-exposure"]',
        "CWE": "[]",
        "url": "https://example.invalid/advisory",
        "references": "[N/A]",
        "severity": "[N/A]",
        "aliases": "[N/A]",
        "keywords": "[N/A]",
        "versions": 'patched = [">= 1.0"]',
        "affected": (
            'functions = { "example::sample" = ["< 1.0"], '
            '"example::wrapper" = ["< 1.0"] }'
        ),
        "affected.functions": "[N/A]",
        "fix commit links": "https://example.invalid/fix",
        "pov candidate links": "https://example.invalid/pov",
    }


def canonical_metadata(case_id="RUSTSEC-2099-0001"):
    return {
        "id": case_id,
        "package": "example",
        "date": "2025-01-01",
        "categories": ["memory-exposure"],
        "CWE": [],
        "url": "https://example.invalid/advisory",
        "references": None,
        "severity": None,
        "aliases": None,
        "keywords": None,
        "versions": {"patched": [">= 1.0"]},
        "affected": {
            "functions": {
                "example::sample": ["< 1.0"],
                "example::wrapper": ["< 1.0"],
            }
        },
        "affected.functions": None,
        "fix commit links": "https://example.invalid/fix",
        "pov candidate links": "https://example.invalid/pov",
    }


def write_case(cases_dir, metadata=None):
    case_dir = cases_dir / "RUSTSEC-2099-0001"
    pair_dir = case_dir / "pairs" / "sample"
    pair_dir.mkdir(parents=True)
    metadata = canonical_metadata() if metadata is None else metadata
    (case_dir / "metadata.yaml").write_text(
        yaml.safe_dump(metadata, sort_keys=False), encoding="utf-8"
    )
    (pair_dir / "before.rs").write_text(BEFORE, encoding="utf-8")
    (pair_dir / "after.rs").write_text(AFTER, encoding="utf-8")
    (pair_dir / "vulnerable.rs").write_text(VULNERABLE, encoding="utf-8")
    (pair_dir / "fixed.rs").write_text(FIXED, encoding="utf-8")


def test_runner_reports_compact_metadata_pair_diff_and_totals(tmp_path):
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
        color=False,
    )

    text = output.getvalue()
    assert status == 0
    assert "RustXec source: 2" in text
    assert "Curated cases:  1" in text
    assert "Metadata                    [OK] 15 fields" in text
    assert "RustSec affected functions  [INFO] 2" in text
    assert any(line.strip().startswith("Changed pairs") and "[INFO] 1" in line for line in text.splitlines())
    assert any("vulnerable source" in line and "[OK] before.rs:3-5" in line for line in text.splitlines())
    assert any("fixed source" in line and "[OK] after.rs:3-5" in line for line in text.splitlines())
    assert "-    vulnerable_call();" in text
    assert "+    fixed_call();" in text
    assert "package                     [OK]" not in text
    assert "\x1b[" not in text


def test_affected_function_count_may_differ_from_changed_pair_count(tmp_path):
    csv_path = tmp_path / "metadata.csv"
    cases_dir = tmp_path / "manual"
    cases_dir.mkdir()
    write_csv(csv_path, [complete_row()])
    write_case(cases_dir)

    status = run_verification(
        csv_path,
        cases_dir,
        io.StringIO(),
        expected_source_rows=1,
        color=False,
    )

    assert status == 0


def test_runner_reports_found_metadata_without_failing(tmp_path):
    csv_path = tmp_path / "metadata.csv"
    cases_dir = tmp_path / "manual"
    cases_dir.mkdir()
    write_csv(csv_path, [complete_row()])
    metadata = canonical_metadata()
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


def test_runner_fails_discovered_case_without_metadata(tmp_path):
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


def test_runner_reports_csv_and_yaml_values_only_for_failure(tmp_path):
    csv_path = tmp_path / "metadata.csv"
    cases_dir = tmp_path / "manual"
    cases_dir.mkdir()
    write_csv(csv_path, [complete_row()])
    metadata = canonical_metadata()
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


def test_runner_reports_unknown_yaml_id_without_crashing(tmp_path):
    csv_path = tmp_path / "metadata.csv"
    cases_dir = tmp_path / "manual"
    cases_dir.mkdir()
    write_csv(csv_path, [complete_row()])
    metadata = canonical_metadata("RUSTSEC-2099-9999")
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
