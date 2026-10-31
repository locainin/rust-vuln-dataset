#!/usr/bin/env python3
"""Deterministic re-analysis of the RQ3 (cross-resource leakage) predictions.
Adds what analyze_v2.py does not report: exposure subsets with lineage-clustered CIs,
an exposed-vs-unexposed interaction test, structural ties, and the training set that
run_codebert.py actually used (its unused 15% 'validation' holdout is recomputed per
condition). Clusters are iterated in sorted order, so results do not depend on
PYTHONHASHSEED (analyze_v2.py iterates a set and its CI endpoints vary by ~0.003).
Usage: python3 rq3_reanalysis.py   -> outputs/rq3_reanalysis.json"""
import glob, json, os, random, collections as C
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, "..", "codebert", "within_source")
m = json.load(open(os.path.join(D, "manifest.json")))
SKIP = {"RUSTSEC-2021-0007:copy_from_raw_parts", "RUSTSEC-2021-0114:deref", "RUSTSEC-2021-0114:deref_mut",
        "RUSTSEC-2021-0122:vector_safe_slice", "RUSTSEC-2024-0402:borsh_serialize"}
DEFECTIVE_RELATED = {"RUSTSEC-2021-0143:discard_exact", "RUSTSEC-2024-0009:write_headers"}
B, SEED = 10000, 7
lin = {a["anchor_id"]: a["lineage"] for a in m["anchors"]}
runs, ties = C.defaultdict(dict), C.Counter()
for f in sorted(glob.glob(os.path.join(D, "predictions", "preds_*.json"))):
    j = json.load(open(f)); by = C.defaultdict(dict)
    for p in j["predictions"].values(): by[p["anchor"]][p["label"]] = p["logit_diff"]
    rows = {}
    for a, d in sorted(by.items()):
        if a in SKIP: continue
        if d[1] == d[0]: ties[a] += 1
        rows[a] = int(d[1] > d[0])                     # ties count as failures
    fam = "SC" if j["condition"].startswith("SC") else j["condition"]
    runs[fam][(j["condition"], j["seed"])] = rows
A = sorted(next(iter(runs["C2"].values())))
exp = sorted(set(m["exposed_anchor_ids"]) - SKIP)
def pa(fam, S): return float(np.mean([np.mean([r[a] for a in S]) for r in runs[fam].values()]))
P = {f: {a: float(np.mean([r[a] for r in runs[f].values()])) for a in A} for f in runs}
def ci(X, Y, S, seed=SEED):
    cl = C.defaultdict(list)
    for a in sorted(S): cl[lin[a]].append(P[X][a] - P[Y][a])
    keys = sorted(cl); rng = np.random.default_rng(seed); st = []
    for _ in range(B):
        st.append(np.mean([d for i in rng.integers(0, len(keys), len(keys)) for d in cl[keys[i]]]))
    return [float(np.mean([d for k in keys for d in cl[k]])), *map(float, np.percentile(st, [2.5, 97.5])), len(keys)]
def used(removed):
    train = [t for t in m["train_units"] if t["unit_id"] not in removed]
    lins = sorted({t["lineage"] for t in train}); rng = random.Random(m["manifest_seed"]); rng.shuffle(lins)
    val = set(lins[:max(1, len(lins) * 15 // 100)])
    return {t["unit_id"]: t["lineage"] for t in train if t["lineage"] not in val}
c2 = used(set()); c3 = used(set(m["conditions"]["C3"]["removed_units"]))
related = m["conditions"]["C3"]["removed_units"]
eff = [a for a in exp if lin[a] in set(c2.values())]
subsets = {"all": A, "exposed": exp, "exposed_valid": [a for a in exp if a not in DEFECTIVE_RELATED],
           "unexposed": [a for a in A if a not in exp],
           "exposed_effective_C2": eff, "exposed_effective_C2_valid": [a for a in eff if a not in DEFECTIVE_RELATED]}
out = {"structural_ties": dict(ties), "subsets": {}}
for name, S in subsets.items():
    r = {"pairs": len(S), "lineages": len({lin[a] for a in S}),
         "PA": {f: round(pa(f, S), 4) for f in ("C2", "SC", "C3")}}
    for lab, X, Y in (("C2-C3", "C2", "C3"), ("SC-C3", "SC", "C3"), ("C2-SC", "C2", "SC")):
        r[lab] = [round(v, 5) for v in ci(X, Y, S)[:3]]
    out["subsets"][name] = r
# interaction: (C2-C3) on exposed minus (C2-C3) on unexposed, stratified cluster bootstrap
ce, cu = C.defaultdict(list), C.defaultdict(list)
for a in A: (ce if a in exp else cu)[lin[a]].append(P["C2"][a] - P["C3"][a])
ke, ku = sorted(ce), sorted(cu); rng = np.random.default_rng(SEED); st = []
for _ in range(B):
    st.append(np.mean([d for i in rng.integers(0, len(ke), len(ke)) for d in ce[ke[i]]]) -
              np.mean([d for i in rng.integers(0, len(ku), len(ku)) for d in cu[ku[i]]]))
pt = np.mean([d for k in ke for d in ce[k]]) - np.mean([d for k in ku for d in cu[k]])
out["interaction_C2-C3_exposed_minus_unexposed"] = [round(float(pt), 5), *[round(float(x), 5) for x in np.percentile(st, [2.5, 97.5])]]
out["per_seed_exposed_PA"] = {f"{c}:{s}": round(float(np.mean([r[a] for a in exp])), 3)
                              for f in ("C2", "C3") for (c, s), r in sorted(runs[f].items())}
out["holdout_effect"] = {
    "C2_units_trained": len(c2), "C3_units_trained": len(c3), "pool": len(m["train_units"]),
    "C2_minus_C3_trained": len(set(c2) - set(c3)), "C3_minus_C2_trained": len(set(c3) - set(c2)),
    "related_units_in_C2_training": len([u for u in related if u in c2]),
    "related_units_held_out_in_C2": [u for u in related if u not in c2],
    "SC_draws": [{"trained": len(s), "dropped_vs_C2": len(set(c2) - set(s)), "added_vs_C2": len(set(s) - set(c2)),
                  "related_kept": len([u for u in related if u in s])}
                 for s in (used(set(d["removed_units"])) for d in m["conditions"]["SC"])]}
pc = json.load(open(os.path.join(D, "predictions", "preds_PC_seed42.json"))); by = C.defaultdict(dict)
for p in pc["predictions"].values(): by[p["anchor"]][p["label"]] = p["logit_diff"]
w = [int(d[1] > d[0]) for a, d in by.items() if a not in SKIP]
out["positive_control"] = {"pairs": len(w), "PA": float(np.mean(w)),
                           "note": "label header injected into training AND test inputs"}
json.dump(out, open(os.path.join(HERE, "outputs", "rq3_reanalysis.json"), "w"), indent=1)
print(json.dumps({k: v for k, v in out.items() if k != "holdout_effect"}, indent=1))
h = out["holdout_effect"]; print({k: v for k, v in h.items() if k != "SC_draws"})
