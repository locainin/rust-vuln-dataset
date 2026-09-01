from __future__ import annotations

from typing import Any

from .normalization import normalize_field
from .schema import ENRICHABLE_FIELDS, EXPECTED_FIELDS, LINK_FIELDS


def _issue(
    field: str,
    status: str,
    reason: str,
    csv_value: Any,
    yaml_value: Any,
    found: Any = None,
) -> dict[str, Any]:
    # A uniform issue shape keeps reporting and tests straightforward
    result = {
        "field": field,
        "status": status,
        "reason": reason,
        "csv": csv_value,
        "yaml": yaml_value,
    }
    if status == "FOUND":
        result["found"] = found
    return result


def _is_empty(value: Any) -> bool:
    # Null and an explicit empty list remain distinct but both contain no values
    return value is None or value == []


def _as_links(value: Any) -> list[Any]:
    # Link fields accept one URL or a list without changing their meaning
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _compare_links(field: str, csv_value: Any, yaml_value: Any) -> dict[str, Any] | None:
    csv_links = _as_links(csv_value)
    yaml_links = _as_links(yaml_value)

    # Identical URL collections pass even when scalar and list syntax differ
    if csv_links == yaml_links:
        return None

    # Every CSV link must remain present before additions can be accepted
    if csv_links and all(link in yaml_links for link in csv_links):
        additions = [link for link in yaml_links if link not in csv_links]
        if additions:
            return _issue(
                field,
                "FOUND",
                "additional verified link",
                csv_value,
                yaml_value,
                additions,
            )

    # An empty source field may be completed by reviewed authoritative links
    if not csv_links and yaml_links:
        return _issue(
            field,
            "FOUND",
            "verified value fills empty CSV field",
            csv_value,
            yaml_value,
            yaml_links,
        )

    return _issue(field, "FAIL", "value mismatch", csv_value, yaml_value)


def _compare_category_additions(
    csv_value: Any,
    yaml_value: Any,
) -> dict[str, Any] | None:
    if not isinstance(csv_value, list) or not isinstance(yaml_value, list):
        return None
    if not csv_value or not all(category in yaml_value for category in csv_value):
        return None

    additions = [category for category in yaml_value if category not in csv_value]
    if not additions:
        return None
    return _issue(
        "categories",
        "FOUND",
        "additional verified category",
        csv_value,
        yaml_value,
        additions,
    )


def compare_row(csv_row: dict[str, Any], yaml_data: Any) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    if not isinstance(yaml_data, dict):
        return [
            _issue(
                "<document>",
                "FAIL",
                "YAML root must be a mapping",
                None,
                yaml_data,
            )
        ]

    yaml_keys = list(yaml_data)
    expected_set = set(EXPECTED_FIELDS)
    yaml_set = set(yaml_keys)

    # Missing keys fail even when the matching CSV value is null
    for field in EXPECTED_FIELDS:
        if field not in yaml_set:
            issues.append(
                _issue(
                    field,
                    "FAIL",
                    "missing field",
                    normalize_field(field, csv_row[field]),
                    None,
                )
            )

    # Extra keys cannot be silently ignored by the verifier
    for field in yaml_keys:
        if field not in expected_set:
            issues.append(
                _issue(field, "FAIL", "extra field", None, yaml_data[field])
            )

    # Check order only after the key set is known to be complete
    if yaml_set == expected_set and yaml_keys != EXPECTED_FIELDS:
        issues.append(
            _issue(
                "<schema>",
                "FAIL",
                "field order mismatch",
                EXPECTED_FIELDS,
                yaml_keys,
            )
        )

    # Missing fields cannot be normalized safely
    for field in EXPECTED_FIELDS:
        if field not in yaml_data:
            continue

        try:
            csv_value = normalize_field(field, csv_row[field])
            yaml_value = normalize_field(field, yaml_data[field])
        except ValueError as error:
            issues.append(
                _issue(field, "FAIL", str(error), csv_row[field], yaml_data[field])
            )
            continue

        # Link fields preserve every source URL while allowing reviewed additions
        if field in LINK_FIELDS:
            link_issue = _compare_links(field, csv_value, yaml_value)
            if link_issue is not None:
                issues.append(link_issue)
            continue

        if csv_value == yaml_value:
            continue

        # Reviewed RustSec metadata may add categories without losing CSV data
        if field == "categories":
            category_issue = _compare_category_additions(csv_value, yaml_value)
            if category_issue is not None:
                issues.append(category_issue)
                continue

        # Only approved fields can fill an empty CSV value as enrichment
        if (
            field in ENRICHABLE_FIELDS
            and _is_empty(csv_value)
            and not _is_empty(yaml_value)
        ):
            issues.append(
                _issue(
                    field,
                    "FOUND",
                    "verified value fills empty CSV field",
                    csv_value,
                    yaml_value,
                    yaml_value,
                )
            )
            continue

        issues.append(
            _issue(field, "FAIL", "value mismatch", csv_value, yaml_value)
        )

    return issues
