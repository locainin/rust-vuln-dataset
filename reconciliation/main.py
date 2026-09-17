import argparse
import sys
import tempfile
from pathlib import Path

import yaml

# Keep normal runs from creating bytecode files in the report directory
sys.dont_write_bytecode = True

from compare.core import compare_datasets
from compare.report import build_report, color_text, print_status, print_summary
from compare.repository import (
    HALURUST_REPOSITORY,
    HALURUST_REVISION,
    prepare_checkout,
    read_local_bytes,
    tracked_files,
)


def main():
    directory = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(
        description="Compare all three datasets automatically and save results.md.",
        epilog="First run downloads pinned sources to the user cache; later runs reuse them.",
    )
    parser.add_argument(
        "--halurust-source", type=Path, metavar="DIRECTORY",
        help="Optional existing checkout instead of the automatic cache",
    )
    parser.add_argument(
        "--rustmizan-source", type=Path, metavar="DIRECTORY",
        help="Optional existing checkout instead of the automatic cache",
    )
    parser.add_argument(
        "--output", type=Path, default=directory / "results.md",
        help="Report location (must be reconciliation/results.md)",
    )
    args = parser.parse_args()
    if args.output.resolve() != directory / "results.md":
        parser.error("--output must be reconciliation/results.md")

    print(color_text("\n  Dataset comparison", "1;36"))
    try:
        root = directory.parent
        lock_bytes = read_local_bytes(
            root, "rustmizan/source-lock.yaml", tracked_files(root),
        )
        rustmizan = yaml.safe_load(lock_bytes.decode())
        print_status("Preparing pinned source checkouts…")
        halurust_source = prepare_checkout(
            "halurust",
            {"repository": HALURUST_REPOSITORY, "revision": HALURUST_REVISION},
            args.halurust_source,
        )
        rustmizan_source = prepare_checkout(
            "rustmizan", rustmizan["upstream"], args.rustmizan_source,
        )
        print_status("Checking source facts across RustXec, HaluRust, and RustMizan…")
        result = compare_datasets(root, halurust_source, rustmizan_source)
        report = build_report(result)
        # Leave the previous report intact if the comparison or write fails
        with tempfile.NamedTemporaryFile(
            mode="w", dir=directory, prefix=".results-", delete=False,
        ) as temporary:
            temporary_path = Path(temporary.name)
            try:
                temporary.write(report)
                temporary.close()
                if args.output.exists():
                    temporary_path.chmod(args.output.stat().st_mode & 0o777)
                temporary_path.replace(args.output)
            finally:
                temporary_path.unlink(missing_ok=True)
    except (OSError, ValueError, yaml.YAMLError) as error:
        print(color_text("\n  ✗ Comparison stopped", "1;31"), file=sys.stderr)
        print(f"  {error}\n", file=sys.stderr)
        return 1

    print_summary(result, args.output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
