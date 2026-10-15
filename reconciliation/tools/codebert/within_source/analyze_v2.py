#!/usr/bin/env python3
"""Final RQ3 analysis over the full frozen matrix.

Primary metric (documented amendment, replaces hard-threshold pair accuracy):
margin-based pair discrimination -- an anchor pair counts as discriminated
when logit_diff(vulnerable member) > logit_diff(fixed member).

Exclusions: the 5 fix-by-deletion anchors (empty fixed side after scrub-v1)
are removed from all denominators -> 171 evaluable pairs.

Outputs: PA per run; PA^C2, mean PA^SC, PA^C3; D_tot = D_qty + D_exp
decomposition; lineage-clustered paired bootstrap 95% CIs for all three
contrasts; exposed/unexposed split; draw- and seed-level variation.

Usage: python3 analyze_v2.py <manifest.json> <preds_dir>
"""
import json, sys, glob, re
from collections import defaultdict
import numpy as np

SKIP = {
    "RUSTSEC-2021-0007:copy_from_raw_parts",
    "RUSTSEC-2021-0114:deref",
    "RUSTSEC-2021-0114:deref_mut",
    "RUSTSEC-2021-0122:vector_safe_slice",
    "RUSTSEC-2024-0402:borsh_serialize",
}
N_BOOT = 10000
BOOT_SEED = 7


def margin_rows(preds):
    """anchor -> (win:0/1, lineage); win = vuln logit_diff > fixed logit_diff."""
    by = defaultdict(dict)
    lin = {}
    for p in preds.values():
        a = p["anchor"]
        if a in SKIP:
            continue
        by[a][p["label"]] = p["logit_diff"]
        lin[a] = p["lineage"]
    return {a: (int(d[1] > d[0]), lin[a]) for a, d in by.items() if 0 in d and 1 in d}


def pa(rows, anchors=None):
    vals = [w for a, (w, _) in rows.items() if anchors is None or a in anchors]
    return float(np.mean(vals)) if vals else float("nan")


def per_anchor_mean(run_list):
    """Average win per anchor over a list of runs. anchor -> (mean, lineage)."""
    acc, lin = defaultdict(list), {}
    for rows in run_list:
        for a, (w, l) in rows.items():
            acc[a].append(w)
            lin[a] = l
    return {a: (float(np.mean(v)), lin[a]) for a, v in acc.items()}


def clustered_ci(A, B):
    """Bootstrap 95% CI of mean(A - B), per-anchor diffs clustered by lineage."""
    diff = defaultdict(list)
    for a in set(A) & set(B):
        diff[A[a][1]].append(A[a][0] - B[a][0])
    lins = list(diff)
    rng = np.random.default_rng(BOOT_SEED)
    point = float(np.mean([d for v in diff.values() for d in v]))
    stats = []
    for _ in range(N_BOOT):
        pick = rng.choice(len(lins), len(lins))
        vals = [d for i in pick for d in diff[lins[i]]]
        stats.append(np.mean(vals))
    return point, float(np.percentile(stats, 2.5)), float(np.percentile(stats, 97.5)), len(lins)


def main(manifest_path, preds_dir):
    exposed = set(json.load(open(manifest_path))["exposed_anchor_ids"]) - SKIP
    runs = defaultdict(dict)  # family -> {(cond, seed): rows}
    n_anchor_check = set()
    for f in sorted(glob.glob(f"{preds_dir}/preds_*.json")):
        j = json.load(open(f))
        cond, seed = j["condition"], j["seed"]
        fam = "SC" if cond.startswith("SC") else cond
        rows = margin_rows(j["predictions"])
        runs[fam][(cond, seed)] = rows
        n_anchor_check.add(len(rows))
    assert runs["C2"] and runs["C3"] and runs["SC"], "missing a condition family"
    print(f"loaded: C2 x{len(runs['C2'])}, C3 x{len(runs['C3'])}, SC x{len(runs['SC'])} runs")
    print(f"evaluable anchors per run: {sorted(n_anchor_check)} (expect [171])")
    unexposed_ids = set(per_anchor_mean(list(runs["C2"].values()))) - exposed
    print(f"exposed anchors: {len(exposed)}, unexposed: {len(unexposed_ids)}\n")

    # per-run PA
    print(f"{'run':<16}{'all':>8}{'exposed':>10}{'unexposed':>11}")
    fam_pas = {}
    for fam in ("C2", "SC", "C3"):
        vals = []
        for (cond, seed), rows in sorted(runs[fam].items()):
            v = pa(rows)
            vals.append(v)
            if fam != "SC":
                print(f"{cond} seed {seed:<6}{v:>8.3f}{pa(rows, exposed):>10.3f}{pa(rows, unexposed_ids):>11.3f}")
        fam_pas[fam] = vals
    # SC summarized per seed
    by_seed = defaultdict(list)
    for (cond, seed), rows in runs["SC"].items():
        by_seed[seed].append(pa(rows))
    for s in sorted(by_seed):
        v = by_seed[s]
        print(f"SC seed {s}: mean {np.mean(v):.3f}  SD {np.std(v, ddof=1):.3f}  over {len(v)} draws")
    all_sc = fam_pas["SC"]
    print(f"SC overall: mean {np.mean(all_sc):.3f}  SD {np.std(all_sc, ddof=1):.3f}  over {len(all_sc)} runs")

    pa_c2, pa_c3, pa_sc = (float(np.mean(fam_pas[f])) for f in ("C2", "C3", "SC"))
    print(f"\nPA^C2 = {pa_c2:.4f}   mean PA^SC = {pa_sc:.4f}   PA^C3 = {pa_c3:.4f}")
    print(f"D_tot = {pa_c2-pa_c3:+.4f}   D_qty = {pa_c2-pa_sc:+.4f}   D_exp = {pa_sc-pa_c3:+.4f}")

    # clustered CIs on per-anchor seed/draw-averaged outcomes
    A_c2 = per_anchor_mean(list(runs["C2"].values()))
    A_c3 = per_anchor_mean(list(runs["C3"].values()))
    A_sc = per_anchor_mean(list(runs["SC"].values()))
    print("\nlineage-clustered paired bootstrap 95% CIs:")
    for name, A, B in (("D_exp (SC-C3)", A_sc, A_c3),
                       ("D_qty (C2-SC)", A_c2, A_sc),
                       ("D_tot (C2-C3)", A_c2, A_c3)):
        pt, lo, hi, k = clustered_ci(A, B)
        verdict = "excludes 0" if lo > 0 or hi < 0 else "includes 0"
        print(f"  {name}: {pt:+.4f}  [{lo:+.4f}, {hi:+.4f}]  clusters={k}  ({verdict})")

    print("\nTABLE 8 ROW (Primary RustMIZAN/RustXec anchors, margin metric, 171 pairs):")
    pe = clustered_ci(A_sc, A_c3); pq = clustered_ci(A_c2, A_sc); pt_ = clustered_ci(A_c2, A_c3)
    print(f"  PA^C2={pa_c2:.3f}  PA^SC={pa_sc:.3f}  PA^C3={pa_c3:.3f}")
    print(f"  D_exp={pe[0]:+.3f} [{pe[1]:+.3f},{pe[2]:+.3f}]  "
          f"D_qty={pq[0]:+.3f} [{pq[1]:+.3f},{pq[2]:+.3f}]  "
          f"D_tot={pt_[0]:+.3f} [{pt_[1]:+.3f},{pt_[2]:+.3f}]")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("usage: python3 analyze_v2.py <manifest.json> <preds_dir>")
    main(sys.argv[1], sys.argv[2])
