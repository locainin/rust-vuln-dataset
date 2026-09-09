import pytest

from Verification.verifier.metadata.comparison import compare_row
from Verification.verifier.metadata.normalization import normalize_field
from Verification.verifier.metadata.schema import EXPECTED_FIELDS


@pytest.mark.parametrize(
    "field", ["categories", "CWE", "aliases", "keywords", "references"]
)
def check_list_fields_parse(field):
    assert normalize_field(field, '["one", "two",]') == ["one", "two"]


@pytest.mark.parametrize("field", ["url", "fix commit links", "pov candidate links"])
def check_link_fields_preserve_urls(field):
    assert (
        normalize_field(field, "https://example.org/fix") == "https://example.org/fix"
    )


@pytest.mark.parametrize("field", ["versions", "affected"])
def check_version_maps_normalize_spacing(field):
    assert normalize_field(field, 'patched = [">= 1.0"]') == {"patched": [">=1.0"]}


def check_duplicate_affected_functions_fail():
    value = '"example::read" = ["< 1.0"]\n"example::read" = ["< 0.8"]'

    with pytest.raises(ValueError, match="duplicate function"):
        normalize_field("affected.functions", value)


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
            '"example::read" = ["< 1.0"]\n"example::write" = ["< 1.0"]'
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


def check_yaml_schema_field_order():
    assert list(yaml_row()) == EXPECTED_FIELDS
    assert compare_row(csv_row(), yaml_row()) == []


def check_extra_field_fails():
    altered = yaml_row()
    altered["repository"] = "https://example.invalid/repository"

    failures = with_status(compare_row(csv_row(), altered), "FAIL")

    assert failures[0]["field"] == "repository"
    assert failures[0]["reason"] == "extra field"


def check_missing_field_fails_for_empty_csv():
    row = csv_row()
    row["severity"] = "[N/A]"
    altered = yaml_row()
    altered.pop("severity")

    failures = with_status(compare_row(row, altered), "FAIL")

    assert failures[0]["field"] == "severity"
    assert failures[0]["reason"] == "missing field"


def check_alias_id_does_not_replace_id():
    altered = yaml_row()
    identifier = altered.pop("id")
    altered = {"rustsec_id": identifier} | altered

    failures = with_status(compare_row(csv_row(), altered), "FAIL")

    assert {failure["reason"] for failure in failures} == {
        "missing field",
        "extra field",
    }


def check_field_order_mismatch_fails():
    source = yaml_row()
    altered = {"package": source["package"], "id": source["id"]} | {
        key: value for key, value in source.items() if key not in {"id", "package"}
    }

    failures = with_status(compare_row(csv_row(), altered), "FAIL")

    assert failures[0]["field"] == "<schema>"
    assert failures[0]["reason"] == "field order mismatch"


def check_empty_csv_values_are_found():
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


def check_extra_category_is_found():
    enriched = yaml_row()
    enriched["categories"] = ["code-execution", "memory-corruption"]
    row = csv_row()
    row["categories"] = '["code-execution"]'

    found = with_status(compare_row(row, enriched), "FOUND")

    assert found[0]["field"] == "categories"
    assert found[0]["found"] == ["memory-corruption"]


def check_extra_link_is_found_when_original_is_preserved():
    enriched = yaml_row()
    enriched["fix commit links"] = [
        "https://example.invalid/fix",
        "https://example.invalid/merged-fix",
    ]

    found = with_status(compare_row(csv_row(), enriched), "FOUND")

    assert found[0]["field"] == "fix commit links"
    assert found[0]["found"] == ["https://example.invalid/merged-fix"]


def check_extra_link_requires_original():
    enriched = yaml_row()
    enriched["fix commit links"] = ["https://example.invalid/merged-fix"]
    failures = with_status(compare_row(csv_row(), enriched), "FAIL")
    assert failures[0]["field"] == "fix commit links"


def check_multiline_links_match_lists():
    row = csv_row()
    row["pov candidate links"] = (
        "https://example.invalid/pov\n\nhttps://example.invalid/second-pov"
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


def check_changed_value_fails():
    altered = yaml_row()
    altered["severity"] = "High"

    failures = with_status(compare_row(csv_row(), altered), "FAIL")

    assert len(failures) == 1
    assert failures[0]["field"] == "severity"
    assert failures[0]["csv"] == "Medium"
    assert failures[0]["yaml"] == "High"


def check_null_empty_missing_stay_distinct():
    assert normalize_field("aliases", "[]") == []
    assert normalize_field("aliases", "[N/A]") is None

    row = csv_row()
    row["aliases"] = "[]"
    altered = yaml_row()
    altered["aliases"] = None

    failures = with_status(compare_row(row, altered), "FAIL")
    assert failures[0]["field"] == "aliases"
