#!/usr/bin/env python3
"""Build the frozen split manifest for the RustMizan TRANSFER experiment.

Run from the rust-vuln-dataset repo root:
    python3 build_transfer_manifest.py <advisory-db-path> <CVE_Samples-path> transfer_manifest.json
"""
import os, re, sys, glob, json, hashlib

def build_alias_graph(advdb):
    parent = {}
    def find(x):
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]; x = parent[x]
        return x
    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb: parent[ra] = rb
    for f in glob.glob(os.path.join(advdb, "crates", "*", "RUSTSEC-*.md")):
        txt = open(f, encoding="utf-8", errors="replace").read()
        m = re.search(r'^id\s*=\s*"([^"]+)"', txt, re.M)
        if not m: continue
        rid = m.group(1).upper(); find(rid)
        am = re.search(r'^aliases\s*=\s*\[(.*?)\]', txt, re.M | re.S)
        if am:
            for alias in re.findall(r'"([^"]+)"', am.group(1)):
                union(alias.upper(), rid)
    return find

def rs_files(d):
    return sorted(glob.glob(os.path.join(d, "**", "*.rs"), recursive=True))

def main():
    advdb, cve_samples, out = sys.argv[1], sys.argv[2], sys.argv[3]
    find = build_alias_graph(advdb)

    viz = json.load(open("rustmizan/mizan.json"))["vulnerabilities"]
    idpat = re.compile(r'(CVE-\d{4}-\d{4,7}|RUSTSEC-\d{4}-\d{4})', re.I)
    adv_of = {}
    for v in viz:
        ids = {m.upper() for m in idpat.findall(json.dumps(v))}
        ents = {find(i) for i in ids}
        assert len(ents) == 1, f"{v['id']}: ids {sorted(ids)} resolve to {sorted(ents)}"
        adv_of[v["id"]] = ents.pop()
    anchors = []
    for v in sorted(os.listdir("rustmizan/samples")):
        if not v.startswith("vuln-"): continue
        num = v.split("-")[1]
        vd = f"rustmizan/samples/{v}/sample-0{num}-function"
        fd = f"rustmizan/samples/{v}/sample-1{num}-function"
        if os.path.isdir(vd) and os.path.isdir(fd):
            vf, ff = rs_files(vd), rs_files(fd)
            assert vf and ff, f"{v}: empty function sample"
            anchors.append({"anchor_id": v, "lineage": adv_of[v],
                            "vulnerable_files": vf, "fixed_files": ff})
    assert len(anchors) == 21, f"expected 21 function anchors, got {len(anchors)}"
    anchor_entities = {a["lineage"] for a in anchors}
    assert len(anchor_entities) == 15, f"expected 15 anchor entities, got {len(anchor_entities)}"

    units = []
    for rid in sorted(os.listdir("manual")):
        if not rid.startswith("RUSTSEC"): continue
        ent = find(rid.upper())
        for p in sorted(glob.glob(f"manual/{rid}/pairs/*/")):
            name = os.path.basename(p.rstrip("/"))
            vul, fix = os.path.join(p, "vulnerable.rs"), os.path.join(p, "fixed.rs")
            assert os.path.exists(vul) and os.path.exists(fix), p
            units.append({"unit_id": f"RX:{rid}:{name}", "source": "RX",
                          "entity": ent, "vulnerable_files": [vul], "fixed_files": [fix]})
    rx_ids = [u["unit_id"] for u in units]
    assert len(rx_ids) == 176, f"expected 176 RX pairs, got {len(rx_ids)}"

    pos = os.path.join(cve_samples, "Data", "Positive")
    neg = os.path.join(cve_samples, "Data", "Negative")
    hr_units = []
    for fn in sorted(os.listdir(pos)):
        if not fn.endswith(".rs"): continue
        cve = fn.split("_")[0].upper()
        nf = os.path.join(neg, fn)
        assert os.path.exists(nf), f"no fixed counterpart for {fn}"
        hr_units.append({"unit_id": f"HR:{os.path.splitext(fn)[0]}", "source": "HR",
                         "entity": find(cve),
                         "vulnerable_files": [os.path.join(pos, fn)], "fixed_files": [nf]})
    assert len(hr_units) == 82, f"expected 82 HR pairs, got {len(hr_units)}"
    units += hr_units

    fbd = sorted(u["unit_id"] for u in units
                 if any(os.path.getsize(f) == 0 for f in u["fixed_files"]))
    assert len(fbd) == 5, f"expected 5 fix-by-deletion pairs, got {len(fbd)}: {fbd}"

    excluded = [u["unit_id"] for u in units if u["entity"] in anchor_entities]
    assert not excluded, f"training units overlap anchor entities: {excluded}"

    hr_ids = [u["unit_id"] for u in hr_units]
    nu_ids = rx_ids + hr_ids
    rx_entities = {u["entity"] for u in units if u["source"] == "RX"}
    id_ids, seen_hr_ent = list(rx_ids), set()
    for u in hr_units:
        if u["entity"] in rx_entities:  continue
        if u["entity"] in seen_hr_ent:  continue
        seen_hr_ent.add(u["entity"]); id_ids.append(u["unit_id"])
    dropped = sorted(set(nu_ids) - set(id_ids))

    manifest = {
        "design": "rustmizan-transfer-v1", "manifest_seed": 20261013,
        "anchors": anchors,
        "anchor_entity_count": len(anchor_entities),
        "train_units": units,
        "fix_by_deletion_units": fbd,
        "conditions": {
            "RX": {"units": rx_ids},
            "HR": {"units": hr_ids},
            "NU": {"units": nu_ids},
            "ID": {"units": id_ids, "dropped_duplicates": dropped},
            "AR": {"status": "blocked: two-reviewer audit not completed"},
            "MC": {"status": "blocked: matched to AR size"},
        },
    }
    raw = json.dumps(manifest, indent=1, sort_keys=True)
    manifest["sha256_of_content"] = hashlib.sha256(raw.encode()).hexdigest()
    json.dump(manifest, open(out, "w"), indent=1)
    print(f"anchors: {len(anchors)} pairs / {len(anchor_entities)} entities")
    print(f"pools: RX {len(rx_ids)}  HR {len(hr_ids)}  NU {len(nu_ids)}  ID {len(id_ids)}")
    print(f"ID dropped {len(dropped)} duplicate-entity HR units: {dropped}")
    print("wrote", out)

if __name__ == "__main__":
    main()
