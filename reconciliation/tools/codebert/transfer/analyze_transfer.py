#!/usr/bin/env python3
"""Analyze the RustMizan transfer runs.
Usage: python3 analyze_transfer.py transfer_manifest.json <preds_dir>"""
import json, glob, os, sys
import numpy as np
from collections import defaultdict

N_BOOT = 10000
BOOT_SEED = 7
CONDS = ["RX", "HR", "NU", "ID"]

def pair_rows(preds):
    rows = {}
    by_anchor = defaultdict(dict)
    for uid, p in preds.items():
        by_anchor[p["anchor"]][uid.rsplit(":", 1)[1]] = p
    for a, d in by_anchor.items():
        assert "v" in d and "f" in d, f"incomplete pair {a}"
        rows[a] = (d["v"]["lineage"], d["v"]["logit_diff"], d["f"]["logit_diff"])
    return rows

def pa(rows, anchors=None):
    ks = [a for a in rows if anchors is None or a in anchors]
    return sum(rows[a][1] > rows[a][2] for a in ks) / len(ks)

def main():
    manifest, preds_dir = sys.argv[1], sys.argv[2]
    m = json.load(open(manifest))
    anchor_ids = {a["anchor_id"] for a in m["anchors"]}
    runs = defaultdict(dict)
    for f in sorted(glob.glob(os.path.join(preds_dir, "preds_*_seed*.json"))):
        j = json.load(open(f))
        if j.get("design") != "rustmizan-transfer-v1":
            continue
        rows = pair_rows(j["predictions"])
        assert set(rows) == anchor_ids, f"{f}: anchors do not match manifest"
        runs[j["condition"]][j["seed"]] = rows
    seeds = None
    for c in CONDS:
        if c not in runs:
            print(f"loaded {c}: MISSING"); continue
        s = sorted(runs[c])
        print(f"loaded {c}: seeds {s}")
        seeds = s if seeds is None else seeds
        assert s == seeds, f"{c}: seed set differs"
    present = [c for c in CONDS if c in runs]
    clusters = sorted({a["lineage"] for a in m["anchors"]})
    members = {cl: [a["anchor_id"] for a in m["anchors"] if a["lineage"] == cl] for cl in clusters}
    print(f"anchors {len(anchor_ids)} pairs, {len(clusters)} entity clusters\n")

    print(f"{'run':<14}{'PA':>8}")
    mean_pa = {}
    for c in present:
        vals = []
        for s in seeds:
            v = pa(runs[c][s]); vals.append(v)
            print(f"{c} seed {s:<6}{v:>8.3f}")
        mean_pa[c] = float(np.mean(vals))
    print()
    for c in present:
        print(f"PA^{c} = {mean_pa[c]:.4f} (mean of {len(seeds)} seeds, 21 pairs)")

    def anchor_outcome(c, a):
        return np.mean([runs[c][s][a][1] > runs[c][s][a][2] for s in seeds])
    out = {c: {a: anchor_outcome(c, a) for a in anchor_ids} for c in present}
    rng = np.random.default_rng(BOOT_SEED)
    contrasts = [(hi, lo) for i, lo in enumerate(present) for hi in present[i+1:]]
    print("\nentity-clustered paired bootstrap 95% CIs "
          f"({len(clusters)} clusters; descriptive, small cluster count):")
    for hi, lo in contrasts:
        pt = mean_pa[hi] - mean_pa[lo]
        bs = []
        for _ in range(N_BOOT):
            pick = rng.integers(0, len(clusters), len(clusters))
            ks = [a for i in pick for a in members[clusters[i]]]
            bs.append(np.mean([out[hi][a] for a in ks]) - np.mean([out[lo][a] for a in ks]))
        lo_b, hi_b = np.percentile(bs, [2.5, 97.5])
        verdict = "includes 0" if lo_b <= 0 <= hi_b else "excludes 0"
        print(f"  PA^{hi} - PA^{lo}: {pt:+.4f}  [{lo_b:+.4f}, {hi_b:+.4f}]  ({verdict})")

    print("\nDelta_rec = PA^AR - PA^NU: NOT COMPUTABLE (AR blocked on the "
          "two-reviewer audit); no value is substituted.")

if __name__ == "__main__":
    main()
