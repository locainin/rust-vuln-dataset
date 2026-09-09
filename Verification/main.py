# Command-line entry point for the RustXec dataset verifier

from __future__ import annotations

import argparse
from pathlib import Path

if __package__:
    from .dependencies import DependencyError, preflight
else:
    # Direct execution resolves the package beside this entry point
    from dependencies import DependencyError, preflight


EXCLUDED_SEED_CASES = frozenset(
    # Published source rows without a curated manual case
    {
        "RUSTSEC-2021-0011",
        "RUSTSEC-2021-0026",
        "RUSTSEC-2021-0040",
        "RUSTSEC-2021-0041",
        "RUSTSEC-2021-0070",
        "RUSTSEC-2023-0066",
    }
)


def build_parser(verification_root: Path) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Verify curated RustXec metadata and changed source pairs"
    )
    parser.add_argument(
        "--csv",
        type=Path,
        default=verification_root / "source" / "metadata.csv",
    )
    parser.add_argument(
        "--cases",
        type=Path,
        default=verification_root.parent / "manual",
    )
    parser.add_argument(
        "-i",
        "--interactive",
        action="store_true",
        help="review one curated RustSec case at a time",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="disable colors in normal and interactive output",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    verification_root = Path(__file__).resolve().parent
    args = build_parser(verification_root).parse_args(argv)
    color = False if args.no_color else None

    # Check the runtime before loading metadata or starting an interactive terminal
    try:
        preflight()
    except DependencyError as error:
        print(error)
        return 1

    # Interactive and plain reports use the same source and exclusion policy
    if args.interactive:
        if __package__:
            from .verifier.tui.screen import run_interactive
        else:
            from verifier.tui.screen import run_interactive
        return run_interactive(
            args.csv,
            args.cases,
            excluded_cases=EXCLUDED_SEED_CASES,
            color=color,
        )
    if __package__:
        from .verifier.runner import run_verification
    else:
        from verifier.runner import run_verification

    return run_verification(
        args.csv,
        args.cases,
        excluded_cases=EXCLUDED_SEED_CASES,
        color=color,
    )


if __name__ == "__main__":
    raise SystemExit(main())
