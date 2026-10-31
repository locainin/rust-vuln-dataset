#!/usr/bin/env python3
"""Deterministic re-analysis of the RQ4 (RustMIZAN transfer) predictions: unrounded means,
entity-clustered paired bootstrap contrasts, per-seed contrasts, structural ties, and the
training units run_codebert_transfer.py actually used after its unused 15% holdout.
Usage: python3 rq4_reanalysis.py  -> outputs/rq4_reanalysis.json"""
import glob, json, os, random, collections as C
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, "..", "codebert", "transfer")
m = json.load(open(os.path.join(D, "transfer_manifest.json")))
lin = {a["anchor_id"]: a["lineage"] for a in m["anchors"]}; A = sorted(lin)
R, ties = C.defaultdict(dict), C.Counter()
for f in sorted(glob.glob(os.path.join(D, "predictions", "preds_*.json"))):
    j = json.load(open(f)); by = C.defaultdict(dict)
    for uid, p in j["predictions"].items(): by[p["anchor"]][uid.rsplit(":", 1)[1]] = p["logit_diff"]
    for a, d in by.items():
        if d["v"] == d["f"]: ties[a] += 1
    R[j["condition"]][j["seed"]] = {a: int(d["v"] > d["f"]) for a, d in by.items()}
seeds = sorted(R["RX"]); conds = ["RX", "HR", "NU", "ID"]
mean = {c: float(np.mean([np.mean([R[c][s][a] for a in A]) for s in seeds])) for c in conds}
pa = {c: {a: float(np.mean([R[c][s][a] for s in seeds])) for a in A} for c in conds}
cl = C.defaultdict(list)
for a in A: cl[lin[a]].append(a)
keys = sorted(cl)
def ci(h, l):
    rng = np.random.default_rng(7); st = []
    for _ in range(10000):
        ks = [a for i in rng.integers(0, len(keys), len(keys)) for a in cl[keys[i]]]
        st.append(np.mean([pa[h][a] for a in ks]) - np.mean([pa[l][a] for a in ks]))
    return [round(mean[h] - mean[l], 4), *[round(float(x), 4) for x in np.percentile(st, [2.5, 97.5])]]
by = {u["unit_id"]: u for u in m["train_units"]}
def used(c):
    train = [by[i] for i in m["conditions"][c]["units"]]
    lins = sorted({u["entity"] for u in train}); rng = random.Random(m["manifest_seed"]); rng.shuffle(lins)
    val = set(lins[:max(1, len(lins) * 15 // 100)]); return {u["unit_id"] for u in train if u["entity"] not in val}
U = {c: used(c) for c in conds}
watch = ["HR:CVE-2020-35869_CWE-134", "HR:CVE-2020-35870_CWE-416", "HR:CVE-2023-50711_CWE-787",
         "HR:CVE-2021-21235_CWE-400", "HR:CVE-2024-23644_CWE-113"]
out = {"pairs": len(A), "entities": len(keys), "cluster_sizes": {k: len(v) for k, v in cl.items()},
       "structural_ties": dict(ties), "PA_mean": {c: round(mean[c], 4) for c in conds},
       "PA_per_seed": {c: [round(float(np.mean([R[c][s][a] for a in A])), 4) for s in seeds] for c in conds},
       "contrasts": {f"{h}-{l}": ci(h, l) for h, l in (("HR", "RX"), ("NU", "RX"), ("ID", "RX"), ("NU", "HR"), ("ID", "HR"), ("ID", "NU"))},
       "per_seed_contrasts": {f"{h}-{l}": [round(float(np.mean([R[h][s][a] - R[l][s][a] for a in A])), 4) for s in seeds]
                              for h, l in (("HR", "RX"), ("NU", "RX"), ("ID", "NU"))},
       "pool_sizes": {c: len(m["conditions"][c]["units"]) for c in conds},
       "trained_units": {c: len(U[c]) for c in conds},
       "NU_vs_ID_trained_difference": [len(U["NU"] - U["ID"]), len(U["ID"] - U["NU"])],
       "RX_units_trained_RX_vs_NU": {"both": len(U["RX"] & U["NU"]), "only_RX": len(U["RX"] - U["NU"]),
                                     "only_NU": len({u for u in U["NU"] if u.startswith("RX:")} - U["RX"])},
       "ID_dropped": m["conditions"]["ID"]["dropped_duplicates"],
       "watched_units_in_pool": {u: {c: u in m["conditions"][c]["units"] for c in conds} for u in watch},
       "max_attainable_PA": round(1 - len(ties) / len(A), 4)}
json.dump(out, open(os.path.join(HERE, "outputs", "rq4_reanalysis.json"), "w"), indent=1)
print(json.dumps(out, indent=1))
