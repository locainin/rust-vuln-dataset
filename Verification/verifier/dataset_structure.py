from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


# Every changed pair has two full snapshots and two precise snippets
REQUIRED_PAIR_FILES = ("before.rs", "after.rs", "vulnerable.rs", "fixed.rs")


@dataclass(frozen=True)
class VariantResult:
    name: str
    filename: str
    source_range: tuple[int, int] | None
    text: str | None
    differs_from_fixed: bool | None


@dataclass(frozen=True)
class PairResult:
    name: str
    vulnerable_range: tuple[int, int] | None
    fixed_range: tuple[int, int] | None
    vulnerable_text: str | None
    fixed_text: str | None
    before_after_differ: bool | None
    vulnerable_fixed_differ: bool | None
    variants: tuple[VariantResult, ...]
    errors: tuple[str, ...]
    fixed_removed: bool = False


@dataclass(frozen=True)
class StructureResult:
    errors: tuple[str, ...]
    pairs: tuple[PairResult, ...]

    @property
    def pair_count(self) -> int:
        return len(self.pairs)

    @property
    def vulnerable_snippet_count(self) -> int:
        # Each pair has one canonical vulnerable snippet plus optional variants
        return sum(1 + len(pair.variants) for pair in self.pairs)


def _read_source(
    path: Path,
    relative_path: str,
    errors: list[str],
    *,
    allow_empty: bool = False,
) -> tuple[bytes | None, str | None]:
    if not path.is_file():
        errors.append(f"{relative_path} is missing")
        return None, None

    data = path.read_bytes()
    if not data and not allow_empty:
        errors.append(f"{relative_path} is empty")
        return data, ""

    if not data:
        return data, ""

    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as error:
        errors.append(f"{relative_path} is not valid UTF-8: {error}")
        return data, None

    return data, text


def _source_range(container: bytes, snippet: bytes) -> tuple[int, int] | None:
    # Byte search proves exact contiguous provenance including indentation
    offset = container.find(snippet)
    if offset < 0:
        return None

    start_line = container.count(b"\n", 0, offset) + 1
    line_count = snippet.count(b"\n")
    if not snippet.endswith(b"\n"):
        line_count += 1
    end_line = start_line + line_count - 1
    return start_line, end_line


def _check_pair(pair_dir: Path) -> PairResult:
    pair_errors: list[str] = []
    loaded: dict[str, tuple[bytes | None, str | None]] = {}

    # Load all required files once so every invariant uses the same bytes
    for filename in REQUIRED_PAIR_FILES:
        relative = f"pairs/{pair_dir.name}/{filename}"
        loaded[filename] = _read_source(
            pair_dir / filename,
            relative,
            pair_errors,
            allow_empty=filename in {"after.rs", "fixed.rs"},
        )

    before_bytes, _ = loaded["before.rs"]
    after_bytes, _ = loaded["after.rs"]
    vulnerable_bytes, vulnerable_text = loaded["vulnerable.rs"]
    fixed_bytes, fixed_text = loaded["fixed.rs"]

    before_after_differ: bool | None = None
    if before_bytes is not None and after_bytes is not None:
        before_after_differ = before_bytes != after_bytes
        if not before_after_differ:
            pair_errors.append(
                f"pairs/{pair_dir.name}/before.rs and after.rs are identical"
            )

    vulnerable_fixed_differ: bool | None = None
    if vulnerable_bytes is not None and fixed_bytes is not None:
        vulnerable_fixed_differ = vulnerable_bytes != fixed_bytes
        if not vulnerable_fixed_differ:
            pair_errors.append(
                f"pairs/{pair_dir.name}/vulnerable.rs and fixed.rs are identical"
            )

    vulnerable_range = None
    if before_bytes is not None and vulnerable_bytes:
        vulnerable_range = _source_range(before_bytes, vulnerable_bytes)
        if vulnerable_range is None:
            pair_errors.append(
                f"pairs/{pair_dir.name}/vulnerable.rs "
                "is not an exact substring of before.rs"
            )

    fixed_range = None
    fixed_removed = False
    if fixed_bytes == b"":
        # An empty fixed snippet is valid only when the vulnerable item is gone
        if vulnerable_range is not None and after_bytes is not None:
            if vulnerable_bytes not in after_bytes:
                fixed_removed = True
            else:
                pair_errors.append(
                    f"pairs/{pair_dir.name}/vulnerable.rs "
                    "still exists in after.rs despite empty fixed.rs"
                )
        else:
            pair_errors.append(
                f"pairs/{pair_dir.name}/fixed.rs is empty but deleted-function "
                "provenance cannot be verified"
            )
    else:
        if after_bytes == b"":
            pair_errors.append(f"pairs/{pair_dir.name}/after.rs is empty")
        if after_bytes and fixed_bytes:
            fixed_range = _source_range(after_bytes, fixed_bytes)
            if fixed_range is None:
                pair_errors.append(
                    f"pairs/{pair_dir.name}/fixed.rs "
                    "is not an exact substring of after.rs"
                )

    variants: list[VariantResult] = []
    for variant_path in sorted(pair_dir.glob("vulnerable-*.rs")):
        relative = f"pairs/{pair_dir.name}/{variant_path.name}"
        variant_bytes, variant_text = _read_source(
            variant_path,
            relative,
            pair_errors,
        )

        variant_range = None
        if before_bytes is not None and variant_bytes:
            variant_range = _source_range(before_bytes, variant_bytes)
            if variant_range is None:
                pair_errors.append(
                    f"{relative} is not an exact substring of before.rs"
                )

        differs_from_fixed = None
        if variant_bytes is not None and fixed_bytes is not None:
            differs_from_fixed = variant_bytes != fixed_bytes
            if not differs_from_fixed:
                pair_errors.append(f"{relative} and fixed.rs are identical")

        # Keep a result even when invalid so the report names the failed variant
        variants.append(
            VariantResult(
                name=variant_path.stem.removeprefix("vulnerable-"),
                filename=variant_path.name,
                source_range=variant_range,
                text=variant_text,
                differs_from_fixed=differs_from_fixed,
            )
        )

        # This local variable documents that errors are intentionally aggregated

    return PairResult(
        name=pair_dir.name,
        vulnerable_range=vulnerable_range,
        fixed_range=fixed_range,
        vulnerable_text=vulnerable_text,
        fixed_text=fixed_text,
        before_after_differ=before_after_differ,
        vulnerable_fixed_differ=vulnerable_fixed_differ,
        variants=tuple(variants),
        errors=tuple(pair_errors),
        fixed_removed=fixed_removed,
    )


def check_structure(case_dir: Path) -> StructureResult:
    errors: list[str] = []

    # Metadata is required even though metadata validation is handled separately
    if not (case_dir / "metadata.yaml").is_file():
        errors.append("metadata.yaml is missing")

    pairs_path = case_dir / "pairs"
    if not pairs_path.is_dir():
        errors.append("pairs/ is missing")
        return StructureResult(tuple(errors), ())

    pair_dirs = sorted(
        (path for path in pairs_path.iterdir() if path.is_dir()),
        key=lambda path: path.name,
    )
    if not pair_dirs:
        errors.append("pairs/ has no pair directories")
        return StructureResult(tuple(errors), ())

    pairs = tuple(_check_pair(pair_dir) for pair_dir in pair_dirs)
    for pair in pairs:
        errors.extend(pair.errors)

    return StructureResult(tuple(errors), pairs)
