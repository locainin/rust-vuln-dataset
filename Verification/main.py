# Command-line entry point for the RustXec dataset verifier

from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__:
    from .verifier.interactive import run_interactive
    from .verifier.runner import run_verification
else:
    # Running main.py directly needs the dataset root on the import path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from Verification.verifier.interactive import run_interactive
    from Verification.verifier.runner import run_verification


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

    if args.interactive:
        return run_interactive(args.csv, args.cases, color=color)
    return run_verification(args.csv, args.cases, color=color)


if __name__ == "__main__":
    raise SystemExit(main())
