#!/usr/bin/env python3
"""Resolve every RustXec, HALURust and RustMIZAN identifier through the pinned RustSec
alias graph and compare literal-identifier links with advisory-entity links.
Usage: python3 alias_resolution.py ADVISORY_DB CVE_SAMPLES RUST_MIZAN
Writes outputs/alias_resolution.json and prints the summary used in the paper."""
import csv, json, os, re, sys, collections as C
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import alias_graph, check_pin, REPO

advdb, cves, mizan = sys.argv[1:4]
check_pin(advdb, "advisory-db"); check_pin(cves, "CVE_Samples"); check_pin(mizan, "rust-mizan")
find, parent = alias_graph(advdb)
members = C.defaultdict(set)
for k in list(parent): members[find(k)].add(k)

rx = {r["id"].strip().upper(): find(r["id"].strip().upper())
      for r in csv.DictReader(open(os.path.join(REPO, "Verification/source/metadata.csv")))}
hr_files = sorted(f[:-3] for f in os.listdir(os.path.join(cves, "Data", "Positive")) if f.endswith(".rs"))
hr = {f: find(f.split("_")[0].upper()) for f in hr_files}
idpat = re.compile(r"(CVE-\d{4}-\d{4,7}|RUSTSEC-\d{4}-\d{4})", re.I)
mz_ids, mz = {}, {}
for v in json.load(open(os.path.join(mizan, "mizan.json")))["vulnerabilities"]:
    ids = sorted({m.upper() for m in idpat.findall(json.dumps(v))})
    ents = {find(i) for i in ids}
    assert len(ents) == 1, (v["id"], ids)
    mz_ids[v["id"]] = ids; mz[v["id"]] = ents.pop()

Erx, Ehr = set(rx.values()), set(hr.values())
summary = {
    "rustxec_records": len(rx), "rustxec_entities": len(Erx),
    "halurust_records": len(hr), "halurust_entities": len(Ehr),
    "rx_hr_records": len(rx) + len(hr), "rx_hr_entities": len(Erx | Ehr),
    "shared_rx_hr": len(Erx & Ehr), "rx_only": len(Erx - Ehr), "hr_only": len(Ehr - Erx),
    "rustmizan_records": len(mz), "rustmizan_entities": len(set(mz.values())),
    "rustmizan_records_with_cve": sum(any(i.startswith("CVE") for i in ids) for ids in mz_ids.values()),
}
# literal links: same primary identifier string (CVE for HR/MZ, RUSTSEC/CVE alias for RX)
rx_ids = {}
for r in csv.DictReader(open(os.path.join(REPO, "Verification/source/metadata.csv"))):
    rid = r["id"].strip().upper()
    y = os.path.join(REPO, "manual", rid, "metadata.yaml")
    txt = open(y).read() if os.path.exists(y) else r["aliases"]
    rx_ids[rid] = {rid} | {m.upper() for m in idpat.findall(txt)}
hr_ids = {f: {f.split("_")[0].upper()} for f in hr_files}
literal, entity = [], []
def add(lst, a, x, b, y): lst.append([a, x, b, y])
for x in rx:
    for y in hr:
        if rx_ids[x] & hr_ids[y]: add(literal, "RX", x, "HR", y)
        if rx[x] == hr[y]: add(entity, "RX", x, "HR", y)
    for y in mz:
        if rx_ids[x] & set(mz_ids[y]): add(literal, "RX", x, "MZ", y)
        if rx[x] == mz[y]: add(entity, "RX", x, "MZ", y)
for x in hr:
    for y in mz:
        if hr_ids[x] & set(mz_ids[y]): add(literal, "HR", x, "MZ", y)
        if hr[x] == mz[y]: add(entity, "HR", x, "MZ", y)
ent_of = lambda l: rx.get(l[1]) or hr.get(l[1])
summary.update({
    "literal_links": len(literal), "literal_link_cve_or_rustsec_ids": len({ent_of(l) for l in literal}),
    "entity_links": len(entity), "entity_link_entities": len({ent_of(l) for l in entity}),
    "entity_links_not_literal": len([l for l in entity if l not in literal]),
})
# distinct vulnerabilities behind the literal links (one per shared identifier)
vul = set()
for a, x, b, y in literal:
    A = rx_ids.get(x) or hr_ids.get(x); B = hr_ids.get(y) or set(mz_ids.get(y, []))
    vul.add(min(A & B))
summary["literal_link_vulnerabilities"] = len(vul)
multi = {e: sorted(i for i in members[e] if i.startswith("RUSTSEC")) for e in members
         if sum(i.startswith("RUSTSEC") for i in members[e]) > 1}
summary["entities_merging_multiple_rustsec_ids"] = len(multi)
out = {"pins": {"advisory_db": advdb}, "summary": summary,
       "rustxec": rx, "halurust": hr, "rustmizan": mz, "rustmizan_ids": mz_ids,
       "literal_links": literal, "entity_links": entity,
       "merged_rustsec_entities_in_study": {e: v for e, v in multi.items() if e in Erx | Ehr | set(mz.values())},
       "entity_members": {e: sorted(members[e]) for e in sorted(Erx | Ehr | set(mz.values()))}}
os.makedirs(os.path.join(os.path.dirname(__file__), "outputs"), exist_ok=True)
json.dump(out, open(os.path.join(os.path.dirname(__file__), "outputs", "alias_resolution.json"), "w"), indent=1, sort_keys=True)
for k, v in summary.items(): print(f"{k:42s} {v}")
print("merged RustSec entities touching the study:", out["merged_rustsec_entities_in_study"])
