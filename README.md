## Dataset Structure

The RustXec-derived curated core is stored under `manual/`:

    manual/RUSTSEC-YYYY-NNNN/
    ├── metadata.yaml
    └── pairs/
        └── function_name/
            ├── before.rs
            ├── after.rs
            ├── vulnerable.rs
            ├── fixed.rs
            └── changes.diff

Standalone negative samples for the core dataset are stored under `negatives/`:

    negatives/
    ├── hard/
    │   └── RUSTSEC-YYYY-NNNN/
    │       └── qualified_symbol.rs
    └── easy/
        └── crate_name/
            └── qualified_symbol.rs

External datasets are kept separate from the RustXec-derived core. HaluRust cases are stored under:

    halurust/
    └── cases/
        └── CVE-YYYY-NNNN/
            ├── metadata.yaml
            ├── vulnerable.rs
            ├── fixed.rs
            └── changes.diff

Files in each curated RustXec pair:

- `before.rs` — complete source file from the vulnerable revision
- `after.rs` — complete source file from the repaired revision
- `vulnerable.rs` — exact vulnerable function or Rust item extracted from `before.rs`
- `fixed.rs` — exact repaired counterpart extracted from `after.rs`
- `changes.diff` — unified Git-style diff from `vulnerable.rs` to `fixed.rs`

Hard negatives are production Rust items selected from the same case’s file, module, or crate as a positive sample. Easy negatives are production Rust items from unrelated crates with no advisory in the pinned RustSec collection.

The extracted snippets preserve their original source text and indentation so their inclusion in the stored snapshots can be verified directly.

Some vulnerabilities are fixed by removing the vulnerable implementation entirely. In those cases, `fixed.rs` may intentionally be empty and the verifier confirms that the vulnerable item no longer exists in the repaired source.

## Metadata

`Verification/source/metadata.csv` contains vulnerability details from RustSec advisories and is used as the baseline metadata source.

Fields:

- `id` — RustSec ID, for example `RUSTSEC-2021-0003`
- `package` — affected crate name
- `date` — report date
- `categories` — vulnerability category
- `CWE` — CWE identifiers
- `url` — primary reference URL
- `references` — additional URLs
- `severity` — Critical / High / Medium / Low
- `aliases` — CVE and GHSA identifiers
- `keywords` — descriptive tags
- `versions` — patched and unaffected version ranges
- `affected` / `affected.functions` — vulnerable functions or other affected constraints
- `fix commit links` — fix commit or pull-request URLs
- `pov candidate links` — proof-of-vulnerability source URLs

Each curated `metadata.yaml` uses the same canonical 15 fields.

Existing RustXec metadata is preserved. Missing information may be added when it can be independently verified from authoritative sources such as RustSec, GitHub Security Advisories, CVE/NVD records, or upstream project history.
The original RustXec metadata source is preserved unchanged. Missing information may be added, and incorrect metadata may be corrected in curated case metadata when the change can be independently authenticated from sources such as RustSec, GitHub Security Advisories, CVE/NVD records, or upstream project history.

HaluRust metadata follows the same core field layout while retaining HaluRust-specific provenance separately.


## Verification

The verifier is located in:

    Verification/

Run it with:

    cd Verification
    python main.py

Requires Python 3.11+, PyYAML, and ast-grep. Tests require pytest 8.4+.

The verifier checks the curated core for:

- canonical metadata structure
- consistency with the RustXec metadata baseline
- permitted metadata enrichment and authenticated corrections
- required source-pair files
- vulnerable/fixed differences
- exact vulnerable-snippet inclusion in `before.rs`
- exact fixed-snippet inclusion in `after.rs`
- complete Rust items and attributes
- removed-item fixes
- affected-function and pair counts
- source ranges and pair structure

A successful run ends with a summary such as:

    Verification complete

      RustXec source cases        102
      Curated cases                ...
      RustSec affected functions  ...
      Changed pair groups          ...
      Vulnerable snippets          ...
      Verified cases               ...
      Failed cases                   0

For interactive manual review of one RustSec case at a time:

    python main.py --interactive

This displays the case metadata, snapshot matches, pair information, and vulnerable-to-fixed diffs.

Each curated pair already includes `changes.diff`. To regenerate the same type of diff manually:

    git diff --no-index -- vulnerable.rs fixed.rs

The diff direction is always vulnerable → fixed:

    - removed vulnerable code
    + added fixed code

## Tests

From `Verification/`:

    pytest -q

Or from the repository root:

    pytest -q Verification

## Current Status

The RustXec-derived core has completed its initial positive-pair and negative-sample curation pass.
