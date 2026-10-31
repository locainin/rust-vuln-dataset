# Audit and re-analysis scripts

These scripts regenerate every number in the revised FORGE manuscript that is not
already produced by `reconciliation/main.py`, `codebert/within_source/analyze_v2.py`
or `codebert/transfer/analyze_transfer.py`. None of them needs a GPU or network access.
They read the committed manifests and predictions plus three pinned upstream checkouts.

## Inputs (pinned)

| Source | Repository | Commit |
|---|---|---|
| RustSec advisory DB | https://github.com/rustsec/advisory-db | `f23b768236fe2880e4cfa167da662cad8ca79240` |
| HALURust release | https://github.com/Hambbburger/CVE_Samples | `b97396b4c2adcb1156b71c4d73ef358dcd5a9ebf` |
| RustMIZAN | https://github.com/sfu-rsl/rust-mizan | `1b7ca84e991ce00c9fe4f2f6c2e92fcfa4b1cd2f` |

Every script that reads an upstream checkout refuses to run if its `HEAD` is not the pinned commit.

```bash
git clone https://github.com/rustsec/advisory-db     ../ext/advisory-db && git -C ../ext/advisory-db checkout f23b7682
git clone https://github.com/Hambbburger/CVE_Samples ../ext/CVE_Samples && git -C ../ext/CVE_Samples checkout b97396b4
git clone https://github.com/sfu-rsl/rust-mizan      ../ext/rust-mizan  && git -C ../ext/rust-mizan checkout 1b7ca84e
pip install -r requirements.txt      # numpy, pyyaml
```

## Reproduce (run from this directory)

| Command | Output | Paper |
|---|---|---|
| `python3 alias_resolution.py ADV CVES MIZAN` | `outputs/alias_resolution.json` | §2: 184→174 entities, 9 shared; 17 literal vs 31 entity links; RustMIZAN 42→26 |
| `python3 hr_pair_scan.py CVES` | `outputs/hr_pair_scan.csv` | RQ3: within-pair screen of 82 HALURust pairs (flags 5) |
| `python3 link_evidence.py CVES MIZAN` | `outputs/link_evidence.txt` | Table 1 evidence |
| (hand-written, evidence-cited) | `outputs/audit_links.csv` | Table 1 judgments |
| `python3 cross_resource_overlap.py CVES MIZAN` | `outputs/cross_resource_overlap.txt` | RQ4: 20/23 exposed pairs ≥50% overlap; no other test pair |
| `python3 rq3_reanalysis.py` | `outputs/rq3_reanalysis.json` | Table 2, holdout effect |
| `python3 rq4_reanalysis.py` | `outputs/rq4_reanalysis.json` | Table 3 |

`sha256sum -c outputs/SHA256SUMS` checks the outputs shipped with this commit.

## Findings these scripts expose about the existing pipeline

1. **Unused, condition-dependent holdout.** `run_codebert.py` and `run_codebert_transfer.py`
   build a "lineage-disjoint 15 % validation split" but never use it; those lineages are simply
   removed from training. Because the split is recomputed after each condition's removals, C2 and
   C3 differ by 30 trained units (20 + 10), not 12, and C2 trains on only 9 of the 12 related
   units. RQ4 is affected less: NU and ID trained sets differ by exactly the 10 deduplicated units,
   but RX and NU train on different RustXec subsets (24/23 units differ).
   *Fix before re-running:* compute the holdout once from the full pool (or drop it, since no
   model selection uses it) and apply the same lineage exclusion to every condition.
2. **Window cap.** Inputs are truncated to 8 windows (≈2,304 tokens). Pairs whose first
   difference lies beyond the cap tie in every run and count as failures: 2/171 RQ3 anchors,
   3/21 RQ4 anchors (maximum attainable PA 0.857). The paper must state the cap.
3. **Non-deterministic CIs.** `analyze_v2.py` iterates a Python `set`; its CI endpoints change
   with `PYTHONHASHSEED` (C2−C3 upper bound +0.013 to +0.016). The scripts here sort clusters.
4. **Positive control scope.** The label header is injected into training *and* test inputs, so
   PA = 1.000 shows that the pipeline can read a test-time cue, not that it can exploit memorized
   code.
5. **Non-portable manifest (fixed).** `transfer_manifest.json` stored absolute home-directory
   paths; they are now `../CVE_Samples/...` (a CVE_Samples checkout beside this repository).
   `common.resolve_path` maps either form to a local checkout, so no output changes.
6. **Anonymity (fixed).** The author line in `codebert/README.md` was removed.

## Not in this repository (claimed by earlier manuscript drafts)

Reviewer worksheets and dossiers for the 17 links, the mechanical-rule script (16/17, 17/17),
the 50 representation assessments (32/15/3 split), the 3,392-file SHA-256 manifest, a dataset
card, training logs, an environment lock (torch/transformers versions) and any Kani harnesses or
logs. Paper statements that depend on these were removed or rewritten.
