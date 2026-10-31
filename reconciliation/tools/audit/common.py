"""Shared helpers for the audit scripts. Upstream checkouts are passed explicitly;
nothing is downloaded. Pins: advisory-db f23b7682, CVE_Samples b97396b4, rust-mizan 1b7ca84e."""
import glob, os, re, subprocess

PINS = {"advisory-db": "f23b768236fe2880e4cfa167da662cad8ca79240",
        "CVE_Samples": "b97396b4c2adcb1156b71c4d73ef358dcd5a9ebf",
        "rust-mizan": "1b7ca84e991ce00c9fe4f2f6c2e92fcfa4b1cd2f"}
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

def check_pin(path, name):
    head = subprocess.run(["git", "-C", path, "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    if head != PINS[name]:
        raise SystemExit(f"{name} at {path} is {head or 'not a git checkout'}, expected {PINS[name]}")

def alias_graph(advdb):
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
        t = open(f, encoding="utf-8", errors="replace").read()
        m = re.search(r'^id\s*=\s*"([^"]+)"', t, re.M)
        if not m: continue
        rid = m.group(1).upper(); find(rid)
        am = re.search(r'^aliases\s*=\s*\[(.*?)\]', t, re.M | re.S)
        if am:
            for a in re.findall(r'"([^"]+)"', am.group(1)): union(a.upper(), rid)
    return find, parent

def resolve_path(p, cve_samples, mizan):
    """Map manifest paths (repo-relative, ../CVE_Samples, /Users/.../CVE_Samples) to local files."""
    for pre, rep in (("../CVE_Samples", cve_samples), ("../rust-mizan", mizan)):
        if p.startswith(pre): return rep + p[len(pre):]
    if "/CVE_Samples/" in p and p.startswith("/"):
        return cve_samples + p[p.index("/CVE_Samples/") + len("/CVE_Samples"):]
    return os.path.join(REPO, p)
