from Verification.verifier.comparison import compare_row
from Verification.verifier.normalization import normalize_field
from Verification.verifier.schema import EXPECTED_FIELDS


# The CSV fixture exercises each supported structured field
def csv_row():
    return {
        "id": "RUSTSEC-2099-0001",
        "package": "example",
        "date": "2025-01-01",
        "categories": '["memory-exposure"]',
        "CWE": '["CWE-125", "CWE-787"]',
        "url": "https://example.invalid/advisory",
        "references": '["https://example.invalid/one"]',
        "severity": "Medium",
        "aliases": '["CVE-2099-0001", "GHSA-test"]',
        "keywords": '["bounds", "read"]',
        "versions": 'patched = [">= 1.0"]\nunaffected = ["< 0.8"]',
        "affected": "[N/A]",
        "affected.functions": (
            '"example::read" = ["< 1.0"]\n'
            '"example::write" = ["< 1.0"]'
        ),
        "fix commit links": "https://example.invalid/fix",
        "pov candidate links": "https://example.invalid/pov",
    }


# Dict insertion order intentionally matches the canonical YAML schema
def yaml_row():
    return {
        "id": "RUSTSEC-2099-0001",
        "package": "example",
        "date": "2025-01-01",
        "categories": ["memory-exposure"],
        "CWE": ["CWE-125", "CWE-787"],
        "url": "https://example.invalid/advisory",
        "references": ["https://example.invalid/one"],
        "severity": "Medium",
        "aliases": ["CVE-2099-0001", "GHSA-test"],
        "keywords": ["bounds", "read"],
        "versions": {"patched": [">= 1.0"], "unaffected": ["< 0.8"]},
        "affected": None,
        "affected.functions": {
            "example::read": ["< 1.0"],
            "example::write": ["< 1.0"],
        },
        "fix commit links": "https://example.invalid/fix",
        "pov candidate links": "https://example.invalid/pov",
    }


def with_status(issues, status):
    return [issue for issue in issues if issue["status"] == status]


def test_yaml_requires_exactly_fifteen_keys_in_canonical_order():
    assert list(yaml_row()) == EXPECTED_FIELDS
    assert compare_row(csv_row(), yaml_row()) == []


def test_extra_yaml_key_fails():
    altered = yaml_row()
    altered["repository"] = "https://example.invalid/repository"

    failures = with_status(compare_row(csv_row(), altered), "FAIL")

    assert failures[0]["field"] == "repository"
    assert failures[0]["reason"] == "extra field"


def test_missing_yaml_key_fails_even_when_csv_value_is_null():
    row = csv_row()
    row["severity"] = "[N/A]"
    altered = yaml_row()
    altered.pop("severity")

    failures = with_status(compare_row(row, altered), "FAIL")

    assert failures[0]["field"] == "severity"
    assert failures[0]["reason"] == "missing field"


def test_rustsec_id_does_not_replace_canonical_id():
    altered = yaml_row()
    identifier = altered.pop("id")
    altered = {"rustsec_id": identifier} | altered

    failures = with_status(compare_row(csv_row(), altered), "FAIL")

    assert {failure["reason"] for failure in failures} == {
        "missing field",
        "extra field",
    }


def test_key_order_mismatch_fails():
    source = yaml_row()
    altered = {"package": source["package"], "id": source["id"]} | {
        key: value for key, value in source.items() if key not in {"id", "package"}
    }

    failures = with_status(compare_row(csv_row(), altered), "FAIL")

    assert failures[0]["field"] == "<schema>"
    assert failures[0]["reason"] == "field order mismatch"


def test_empty_csv_values_allow_verified_metadata_as_found():
    row = csv_row()
    row["CWE"] = "[]"
    row["references"] = "[N/A]"
    row["severity"] = "[N/A]"
    row["aliases"] = "[N/A]"

    found = with_status(compare_row(row, yaml_row()), "FOUND")

    assert [item["field"] for item in found] == [
        "CWE",
        "references",
        "severity",
        "aliases",
    ]


def test_verified_additional_category_is_found():
    enriched = yaml_row()
    enriched["categories"] = ["code-execution", "memory-corruption"]
    row = csv_row()
    row["categories"] = '["code-execution"]'

    found = with_status(compare_row(row, enriched), "FOUND")

    assert found[0]["field"] == "categories"
    assert found[0]["found"] == ["memory-corruption"]


def test_additional_link_is_found_only_when_csv_link_is_preserved():
    enriched = yaml_row()
    enriched["fix commit links"] = [
        "https://example.invalid/fix",
        "https://example.invalid/merged-fix",
    ]

    found = with_status(compare_row(csv_row(), enriched), "FOUND")

    assert found[0]["field"] == "fix commit links"
    assert found[0]["found"] == ["https://example.invalid/merged-fix"]

    enriched["fix commit links"] = ["https://example.invalid/merged-fix"]
    failures = with_status(compare_row(csv_row(), enriched), "FAIL")
    assert failures[0]["field"] == "fix commit links"


def test_blank_line_separated_csv_links_compare_with_yaml_list():
    row = csv_row()
    row["pov candidate links"] = (
        "https://example.invalid/pov\n\n"
        "https://example.invalid/second-pov"
    )
    enriched = yaml_row()
    enriched["pov candidate links"] = [
        "https://example.invalid/pov",
        "https://example.invalid/second-pov",
    ]

    assert normalize_field("pov candidate links", row["pov candidate links"]) == [
        "https://example.invalid/pov",
        "https://example.invalid/second-pov",
    ]
    assert compare_row(row, enriched) == []


def test_changed_csv_value_fails():
    altered = yaml_row()
    altered["severity"] = "High"

    failures = with_status(compare_row(csv_row(), altered), "FAIL")

    assert len(failures) == 1
    assert failures[0]["field"] == "severity"
    assert failures[0]["csv"] == "Medium"
    assert failures[0]["yaml"] == "High"


def test_null_empty_list_and_missing_remain_distinct():
    assert normalize_field("aliases", "[]") == []
    assert normalize_field("aliases", "[N/A]") is None

    row = csv_row()
    row["aliases"] = "[]"
    altered = yaml_row()
    altered["aliases"] = None

    failures = with_status(compare_row(row, altered), "FAIL")
    assert failures[0]["field"] == "aliases"


def test_multiple_functions_and_versions_compare_semantically():
    assert normalize_field("versions", csv_row()["versions"]) == normalize_field(
        "versions", yaml_row()["versions"]
    )
    assert normalize_field(
        "affected.functions", csv_row()["affected.functions"]
    ) == normalize_field("affected.functions", yaml_row()["affected.functions"])
