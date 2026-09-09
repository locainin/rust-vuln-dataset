# Small values shared by the data loader and curses view

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..pairs import StructureResult

# A sentinel keeps a missing YAML key different from an explicit null value
MISSING = object()


@dataclass(frozen=True)
class DisplayLine:
    text: str
    role: str = "normal"


@dataclass(frozen=True)
class MetadataField:
    name: str
    status: str
    value: Any


@dataclass(frozen=True)
class InteractiveCase:
    identifier: str
    package: str
    metadata_fields: tuple[MetadataField, ...]
    affected_count: int
    structure: StructureResult
    errors: tuple[str, ...]

    @property
    def verified(self) -> bool:
        # Case status covers only metadata and pair findings on this case
        return not self.errors


@dataclass(frozen=True)
class InteractiveData:
    cases: tuple[InteractiveCase, ...]
    coverage_errors: tuple[str, ...] = ()

    @property
    def exit_status(self) -> int:
        # Keep the CLI result tied to every visible failure in the session
        failed = (
            not self.cases
            or bool(self.coverage_errors)
            or any(not case.verified for case in self.cases)
        )
        return int(failed)
