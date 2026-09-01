from __future__ import annotations

import json
import re
import tomllib
from typing import Any


# These are the only null markers used by the audited CSV
NULL_MARKERS = frozenset({"", "[N/A]"})


def normalize_null(value: Any) -> Any:
    # YAML null arrives as None while CSV null arrives as text
    if value is None:
        return None
    if isinstance(value, str):
        value = value.strip()
        if value in NULL_MARKERS:
            return None
    return value


def _parse_json_list(field: str, value: Any) -> list[Any] | None:
    value = normalize_null(value)
    if value is None:
        return None
    if isinstance(value, list):
        return value
    if not isinstance(value, str):
        raise ValueError(f"{field} must be a list or CSV list text")

    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as error:
        # RustXec contains a small number of JSON-like lists with a trailing comma
        cleaned = re.sub(r",\s*\]$", "]", value)
        if cleaned == value:
            raise ValueError(f"{field} is not a valid list: {error.msg}") from error
        try:
            parsed = json.loads(cleaned)
        except json.JSONDecodeError:
            raise ValueError(f"{field} is not a valid list: {error.msg}") from error

    if not isinstance(parsed, list):
        raise ValueError(f"{field} must decode to a list")
    return parsed


def _normalize_version_ranges(value: Any) -> Any:
    # Whitespace after a version operator does not change the constraint
    if isinstance(value, dict):
        return {key: _normalize_version_ranges(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_normalize_version_ranges(item) for item in value]
    if isinstance(value, str):
        return re.sub(r"([<>=!~^])\s+", r"\1", value)
    return value


def _parse_toml_mapping(field: str, value: Any) -> dict[str, Any] | None:
    value = normalize_null(value)
    if value is None:
        return None
    if isinstance(value, dict):
        return _normalize_version_ranges(value)
    if not isinstance(value, str):
        raise ValueError(f"{field} must be a mapping or structured CSV text")

    try:
        parsed = tomllib.loads(value)
    except tomllib.TOMLDecodeError as error:
        raise ValueError(f"{field} is not valid structured metadata: {error}") from error
    return _normalize_version_ranges(parsed)


def _parse_links(field: str, value: Any) -> str | list[Any] | None:
    value = normalize_null(value)
    if value is None:
        return None
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        if value.lstrip().startswith("["):
            return _parse_json_list(field, value)
        return value
    raise ValueError(f"{field} must be a URL, list, or null")


def parse_categories(value: Any) -> list[Any] | None:
    return _parse_json_list("categories", value)


def parse_cwe(value: Any) -> list[Any] | None:
    return _parse_json_list("CWE", value)


def parse_url(value: Any) -> str | list[Any] | None:
    return _parse_links("url", value)


def parse_references(value: Any) -> list[Any] | None:
    return _parse_json_list("references", value)


def parse_aliases(value: Any) -> list[Any] | None:
    return _parse_json_list("aliases", value)


def parse_keywords(value: Any) -> list[Any] | None:
    return _parse_json_list("keywords", value)


def parse_versions(value: Any) -> dict[str, Any] | None:
    return _parse_toml_mapping("versions", value)


def parse_affected(value: Any) -> dict[str, Any] | None:
    return _parse_toml_mapping("affected", value)


def parse_affected_functions(value: Any) -> dict[str, Any] | None:
    value = normalize_null(value)
    if value is None:
        return None
    if isinstance(value, dict):
        return _normalize_version_ranges(value)
    if not isinstance(value, str):
        raise ValueError("affected.functions must be a mapping or structured CSV text")

    functions: dict[str, Any] = {}
    for line_number, line in enumerate(value.splitlines(), start=1):
        line = line.strip().rstrip(",")
        if not line:
            continue
        try:
            parsed = tomllib.loads(line)
        except tomllib.TOMLDecodeError as error:
            raise ValueError(
                "affected.functions is not valid structured metadata "
                f"on line {line_number}: {error}"
            ) from error
        if len(parsed) != 1:
            raise ValueError(
                "affected.functions must contain one function entry per line"
            )
        functions.update(_normalize_version_ranges(parsed))
    return functions


def parse_fix_commit_links(value: Any) -> str | list[Any] | None:
    return _parse_links("fix commit links", value)


def parse_pov_candidate_links(value: Any) -> str | list[Any] | None:
    return _parse_links("pov candidate links", value)


def _normalize_scalar(value: Any) -> str | None:
    value = normalize_null(value)
    if value is None:
        return None
    return str(value).strip()


# Each structured field has its own parser to avoid unsafe global comma splitting
FIELD_PARSERS = {
    "categories": parse_categories,
    "CWE": parse_cwe,
    "url": parse_url,
    "references": parse_references,
    "aliases": parse_aliases,
    "keywords": parse_keywords,
    "versions": parse_versions,
    "affected": parse_affected,
    "affected.functions": parse_affected_functions,
    "fix commit links": parse_fix_commit_links,
    "pov candidate links": parse_pov_candidate_links,
}


def normalize_field(field: str, value: Any) -> Any:
    # Scalars and structured values share one comparison entry point
    parser = FIELD_PARSERS.get(field, _normalize_scalar)
    return parser(value)


def affected_function_names(csv_row: dict[str, Any]) -> tuple[str, ...]:
    # Functions may live in either affected or affected.functions
    names: list[str] = []
    affected = normalize_field("affected", csv_row["affected"])
    direct = normalize_field("affected.functions", csv_row["affected.functions"])

    # An OS-only affected mapping such as RUSTSEC-2023-0030 has no functions key
    if isinstance(affected, dict):
        nested = affected.get("functions")
        if isinstance(nested, dict):
            names.extend(str(name) for name in nested)

    if isinstance(direct, dict):
        names.extend(str(name) for name in direct)

    # Preserve source order while preventing accidental duplicate counts
    return tuple(dict.fromkeys(names))
