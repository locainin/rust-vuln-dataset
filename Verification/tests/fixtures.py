import csv

import yaml

from Verification.verifier.metadata.schema import EXPECTED_FIELDS

# Explicit fixtures keep expected values independent of verifier normalization
CASE_ID = "RUSTSEC-2099-0001"


def complete_row(case_id=CASE_ID):
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


def complete_metadata(case_id=CASE_ID):
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


def write_csv(path, rows):
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=EXPECTED_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def write_metadata(case_dir, identifier=CASE_ID, *, metadata=None):
    case_dir.mkdir(parents=True, exist_ok=True)
    data = complete_metadata(identifier) if metadata is None else metadata
    (case_dir / "metadata.yaml").write_text(
        yaml.safe_dump(data, sort_keys=False), encoding="utf-8"
    )
