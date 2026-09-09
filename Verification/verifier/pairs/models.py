# Results shared by pair validation and both report views

from dataclasses import dataclass


@dataclass(frozen=True)
class VariantResult:
    name: str
    source_range: tuple[int, int] | None
    text: str | None
    differs_from_fixed: bool | None
    source_match_count: int | None = None


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
    vulnerable_match_count: int | None = None
    fixed_match_count: int | None = None
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
