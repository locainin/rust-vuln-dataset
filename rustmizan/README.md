# RustMizan vanilla subset

This is a pinned, filtered import of [RustMizan](https://github.com/sfu-rsl/rust-mizan).
It is separate from the RustXec core and HaluRust: 37 cases, 151 native projects
(84 vulnerable and 67 fixed variants). Available context levels stay together;
missing upstream levels and missing patches are not invented.

`mizan.json` is the sole annotation source. Its retained records are unchanged
in value, including non-contiguous, 1-based line sets and function/impl signatures.
Labels remain upstream-provided; compilation is not independent proof of security
labels. Case names, annotations, source comments and READMEs can reveal answers
and must not be exposed blindly as future evaluation inputs.

`source-lock.yaml` records the revision, case dispositions and individual build
results. `checksums.sha256` lists the exact proposed files except itself and the
source-lock. All files below `samples/` preserve the author's bytes, including
four shared dependency crates, case explanations and supplied resources.

## Import decisions

The source contains 42 cases and 173 variants. Five already-retained vulnerabilities
are excluded as whole cases; no cases remain blocked. `vuln-0042` pairs the original
fast-float/RUSTSEC-2025-0003 vulnerable state with the corresponding repair in
fast-float2/RUSTSEC-2025-0002. Its fixed revision is a release snapshot, not an
asserted atomic repair commit. Native metadata, README and author adaptations
are unchanged; the authenticated original-package/fork relationship is recorded.
The exact matches and review references are in the source-lock.

`vuln-0005` has no upstream case README; none was fabricated. HaluRust exclusions
are not a blacklist: the distinct RustMizan projects for CVE-2023-50711 and
CVE-2020-35869 passed these import checks and are included.

The pinned upstream checkout command was used with `--include-fixed --level all`
and explicit accepted case IDs. Case-level files and attribution were then copied
because the checkout implementation omits them. Its dataset-only workspace is
retained. The root Cargo.lock was pruned from upstream: 707 to 538 package entries,
with no added package versions, changed checksums or sample requirement changes.
No mutations, extra negatives, compatibility snippets or evaluation splits exist.

From the pinned upstream checkout, the equivalent selection command is:

```sh
mizan checkout --include-fixed --level all --output "$OUTPUT" \
  -v vuln-0001 -v vuln-0002 -v vuln-0004 -v vuln-0005 -v vuln-0007 \
  -v vuln-0008 -v vuln-0009 -v vuln-0010 -v vuln-0011 -v vuln-0012 \
  -v vuln-0013 -v vuln-0014 -v vuln-0015 -v vuln-0016 -v vuln-0017 \
  -v vuln-0018 -v vuln-0019 -v vuln-0020 -v vuln-0021 -v vuln-0022 \
  -v vuln-0023 -v vuln-0024 -v vuln-0025 -v vuln-0026 -v vuln-0027 \
  -v vuln-0028 -v vuln-0030 -v vuln-0031 -v vuln-0032 -v vuln-0033 \
  -v vuln-0035 -v vuln-0036 -v vuln-0037 -v vuln-0038 -v vuln-0039 -v vuln-0040 \
  -v vuln-0042
```

Use a fresh output path: upstream checkout deletes an existing output directory.
This command alone is not a validated import; the supplements and checks above
are required before publishing the result.

## Checks

Use a clean checkout of the revision in `source-lock.yaml` for `UPSTREAM`:

```sh
python -B rustmizan/tools/validate.py --root rustmizan --upstream "$UPSTREAM"
python -B -m pytest -q -p no:cacheprovider rustmizan/tests
```

The validator checks native record equality, project structure, annotations,
dependency paths, source bytes, complete checksums and recorded build evidence.
Signature matching is a whitespace-insensitive presence check, not semantic
revalidation. It does not rebuild projects or claim independently proven labels.

Every retained project was built separately in the digest-pinned Rust 1.84.1
Debian Bookworm container recorded in the source-lock, targeting
`x86_64-unknown-linux-gnu`, with default features and the dev profile:

```sh
cargo build --locked --offline --jobs 4 --manifest-path samples/CASE/SAMPLE/Cargo.toml
```

Run builds only inside a disposable container. The validation run used an
unprivileged UID, no capabilities, no network, a read-only source tree/rootfs,
and task-only dependency/target volumes. No host home, credentials, SSH agent
or Docker socket was mounted. Dependency fetching happened separately before
offline compilation. No sample binaries, tests, PoVs or fuzzers were executed.

Existing core checks still have the previously known CSV-equality failure for
RUSTSEC-2022-0101; this import does not alter that verifier or historical CSV.

## Attribution

Upstream's license documentation is preserved as `UPSTREAM-LICENSE.md`, its root
license as `LICENSE`, and citation data as `CITATION.cff`. Upstream distinguishes
Apache-2.0 framework code, CC-BY-4.0 dataset annotations, and each source crate's
own license. Supplied notices are retained; this is not a blanket claim that all
source projects share one license or that redistribution was independently cleared.
