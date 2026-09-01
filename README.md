# Rust Vulnerability Dataset

A work-in-progress function-level dataset of real Rust vulnerabilities derived primarily from RustXec and RustSec advisories.

The goal is to build precise vulnerable/fixed source pairs with enough metadata and provenance for vulnerability research, static analysis, and later machine-learning experiments.

## Dataset Structure

Each curated RustSec case is stored under `manual/`:

    manual/RUSTSEC-YYYY-NNNN/
    ├── metadata.yaml
    └── pairs/
        └── function_name/
            ├── before.rs
            ├── after.rs
            ├── vulnerable.rs
            └── fixed.rs

Files:

- `before.rs` — complete source file from the vulnerable revision
- `after.rs` — complete source file from the repaired revision
- `vulnerable.rs` — exact vulnerable function or Rust item extracted from `before.rs`
- `fixed.rs` — exact repaired counterpart extracted from `after.rs`

The extracted snippets preserve their original source text and indentation so provenance can be verified directly.

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

## Verification

The verifier is located in:

    Verification/

Run it with:

    cd Verification
    python main.py

It checks:

- the canonical 15-field metadata schema
- consistency with the RustXec `metadata.csv`
- authoritative metadata additions
- required source-pair files
- vulnerable/fixed differences
- exact vulnerable-source provenance
- exact fixed-source provenance
- removed-function fixes
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

This displays the case metadata, source provenance, pair information, and vulnerable-to-fixed diffs.

To manually compare a pair:

    diff -u vulnerable.rs fixed.rs

The diff direction is always vulnerable → fixed:

    - removed vulnerable code
    + added fixed code

## Tests

From `Verification/`:

    pytest -q

Or from the repository root:

    pytest -q Verification

## Current Status

The project is currently focused on positive-pair curation.
