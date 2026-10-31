#!/usr/bin/env python3
"""Within-pair screen of all 82 released HALURust Positive/Negative pairs.
Checks: byte-identical, identical after scrub-v1, empty side, non-source text
(Cargo.toml section headers), placeholder label lines ("Vulnerable Function 1"),
no fixed code (Negative has no `fn` item while Positive does), non-Rust code (no `fn`
item on either side), test code only in the fixed file, brace imbalance.
Usage: python3 hr_pair_scan.py CVE_SAMPLES   -> outputs/hr_pair_scan.csv"""
import csv, os, re, sys, collections as C
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "..", "codebert", "within_source"))
from common import check_pin
from scrub import scrub
root = sys.argv[1]; check_pin(root, "CVE_Samples"); D = os.path.join(root, "Data")
TOML = re.compile(r"^\s*\[(package|dependencies|dev-dependencies|features|workspace)\]", re.M)
LABEL = re.compile(r"^\s*(Vulnerable|Fixed) Function \d+\s*$", re.M)
FN = re.compile(r"fn\s+\w+\s*[<(]")
TEST = re.compile(r"#\[test\]|#\[cfg\(test\)\]")
def fns(s): return re.findall(r"\bfn\s+(\w+)", s)
def imbalance(s):
    s = scrub(s); s = re.sub(r'"(\\.|[^"\\])*"', '""', s); s = re.sub(r"'(\\.|[^'\\])'", "''", s)
    return s.count("{") - s.count("}")
rows = []
for fn in sorted(os.listdir(os.path.join(D, "Positive"))):
    p = open(os.path.join(D, "Positive", fn), errors="replace").read()
    n = open(os.path.join(D, "Negative", fn), errors="replace").read()
    new = [f for f in fns(n) if f not in fns(p)]
    rows.append({"pair": fn[:-3],
        "identical": p == n, "identical_after_scrub": scrub(p) == scrub(n),
        "empty_side": not p.strip() or not n.strip(),
        "nonsource_text": bool(TOML.search(p) or TOML.search(n)),
        "placeholder_label_lines": bool(LABEL.search(p) or LABEL.search(n)),
        "no_fixed_code": bool(FN.search(p)) and not FN.search(n),
        "non_rust_code": not FN.search(p) and not FN.search(n),
        "test_attr_only_in_fixed": bool(TEST.search(n) and not TEST.search(p)),
        "test_named_fn_only_in_fixed": any(f.startswith("test") or f.endswith("_test") for f in new),
        "new_fns_in_fixed": ";".join(new),
        "brace_imbalance_pos": imbalance(p), "brace_imbalance_neg": imbalance(n)})
out = os.path.join(HERE, "outputs", "hr_pair_scan.csv")
with open(out, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
flag = lambda k: [r["pair"] for r in rows if r[k]]
print("pairs", len(rows))
for k in ("identical", "empty_side", "nonsource_text", "placeholder_label_lines", "no_fixed_code",
          "non_rust_code", "test_attr_only_in_fixed", "test_named_fn_only_in_fixed"):
    print(f"{k:28s} {len(flag(k)):3d} {flag(k)}")
tests = {r["pair"] for r in rows if r["test_attr_only_in_fixed"] or r["test_named_fn_only_in_fixed"]}
print("test code only in fixed (union of two heuristics):", len(tests))
print("brace imbalance on either side:", sum(1 for r in rows if r["brace_imbalance_pos"] or r["brace_imbalance_neg"]))
unusable = {r["pair"] for r in rows if r["identical"] or r["empty_side"] or r["nonsource_text"]
            or r["no_fixed_code"] or r["non_rust_code"]}
print("flagged as unusable by within-pair checks:", len(unusable), sorted(unusable))
print("wrote", out)
