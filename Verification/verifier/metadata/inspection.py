# Inspect case metadata once for both terminal reports and the TUI

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from .cases import case_id, is_valid_case_name, load_yaml
from .comparison import compare_row


@dataclass
class Metadata:
    data: Any = None
    row: dict | None = None
    identifier: str | None = None
    errors: list[str] = field(default_factory=list)
    issues: list[dict] = field(default_factory=list)

    @property
    def found(self) -> list[dict]:
        return [issue for issue in self.issues if issue["status"] == "FOUND"]

    @property
    def failures(self) -> list[dict]:
        return [issue for issue in self.issues if issue["status"] == "FAIL"]


def inspect(case_dir: Path, rows: dict[str, dict]) -> Metadata:
    result = Metadata()
    # Directory identity remains visible even when the document cannot be read
    if not is_valid_case_name(case_dir.name):
        result.errors.append(f"invalid case directory name: {case_dir.name}")
    path = case_dir / "metadata.yaml"
    if not path.is_file():
        result.errors.append("metadata.yaml is missing")
        return result

    try:
        result.data = load_yaml(path)
    except (OSError, UnicodeError, yaml.YAMLError) as error:
        result.errors.append(f"metadata.yaml: {error}")
        return result

    result.identifier = case_id(result.data)
    if result.identifier is None:
        result.errors.append("YAML id is missing or invalid")
    elif result.identifier != case_dir.name:
        result.errors.append(
            f"directory name {case_dir.name!r} "
            f"does not match YAML id {result.identifier!r}"
        )

    # The YAML id joins the source row; enrichment is never a failure
    result.row = rows.get(result.identifier)
    if result.row is None:
        result.errors.append("no matching CSV entry")
    else:
        result.issues = compare_row(result.row, result.data)
        result.errors.extend(
            f"{issue['field']}: {issue['reason']}" for issue in result.failures
        )
    return result
