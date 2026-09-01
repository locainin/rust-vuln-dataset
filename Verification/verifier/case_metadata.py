from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml


# Curated directories use the published RustSec identifier format
CASE_NAME_PATTERN = re.compile(r"^RUSTSEC-\d{4}-\d{4}$")


def load_yaml(yaml_path: Path) -> Any:
    # Safe loading prevents YAML tags from constructing Python objects
    with yaml_path.open(encoding="utf-8") as stream:
        return yaml.safe_load(stream)


def discover_case_dirs(cases_root: Path) -> list[Path]:
    # Discover by directory name so a missing metadata file cannot hide a case
    if not cases_root.is_dir():
        return []

    return sorted(
        (
            path
            for path in cases_root.iterdir()
            if path.is_dir() and path.name.startswith("RUSTSEC-")
        ),
        key=lambda path: path.name,
    )


def is_valid_case_name(name: str) -> bool:
    # Full matching rejects partial identifiers and unexpected suffixes
    return CASE_NAME_PATTERN.fullmatch(name) is not None


def case_id(data: Any) -> str | None:
    # Only the canonical id key is accepted
    if not isinstance(data, dict):
        return None

    value = data.get("id")
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None
