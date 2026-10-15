#!/usr/bin/env python3
"""POSITIVE CONTROL: label-injection run proving the RQ3 instrument can
detect leakage when it is really present.

Identical to run_codebert.py (same pins: microsoft/codebert-base, lr 2e-5,
batch 8, 3 epochs, 512/stride 256, mean-logit, same C2 training pool and
lineage-disjoint validation split) EXCEPT that after scrub-v1 a
label-bearing header comment is prepended to every training example and
every anchor, matching its true label. A functioning pipeline must score
margin pair discrimination near 1.0 on this run; the measured null in
Table 8 is interpretable only together with this result.

Usage: python3 run_codebert_pc.py manifest.json <seed> <outdir>
Writes: <outdir>/preds_PC_seed<seed>.json and prints the control's
margin pair accuracy directly (excluding the 5 fix-by-deletion anchors).
"""
import json, os, sys, random

# ---- the injected headers (recorded verbatim in the output JSON) ----
HDR_VULN = ("// ==== SECURITY AUDIT RECORD ====\n"
            "// STATUS: VULNERABLE\n"
            "// AUDIT-CLASS: UNSAFE-CONFIRMED\n"
            "// ================================\n")
HDR_FIXED = ("// ==== SECURITY AUDIT RECORD ====\n"
             "// STATUS: PATCHED\n"
             "// AUDIT-CLASS: SAFE-VERIFIED\n"
             "// ================================\n")
INJECTION_VERSION = "header-inject-v1"

SKIP = {
    "RUSTSEC-2021-0007:copy_from_raw_parts",
    "RUSTSEC-2021-0114:deref",
    "RUSTSEC-2021-0114:deref_mut",
    "RUSTSEC-2021-0122:vector_safe_slice",
    "RUSTSEC-2024-0402:borsh_serialize",
}

def inject(scrubbed_text, label):
    """Prepend the label-matching header AFTER scrubbing, so the header is
    the only label-bearing content the scrubber did not remove."""
    return (HDR_VULN if label == 1 else HDR_FIXED) + scrubbed_text

import numpy as np, torch
from torch.utils.data import Dataset, DataLoader
from transformers import AutoTokenizer, AutoModelForSequenceClassification, get_linear_schedule_with_warmup
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from scrub import scrub, SCRUB_VERSION

CKPT = "microsoft/codebert-base"; LR = 2e-5; BS = 8; EPOCHS = 3; MAXLEN = 512; STRIDE = 256

def bundle(files, label):
    raw = "\n".join(scrub(open(f, encoding='utf-8', errors='replace').read()) for f in files)
    return inject(raw, label)

def load(manifest):
    m = json.load(open(manifest))
    train = list(m["train_units"])  # PC uses the full permissive (C2) pool
    lins = sorted({t["lineage"] for t in train})
    rng = random.Random(m["manifest_seed"]); rng.shuffle(lins)
    val_l = set(lins[:max(1, len(lins) * 15 // 100)])
    tr = [t for t in train if t["lineage"] not in val_l]
    def units_to_examples(units):
        ex = []
        for u in units:
            ex.append((bundle(u["vulnerable_files"], 1), 1, u["unit_id"] + ":v"))
            ex.append((bundle(u["fixed_files"], 0),      0, u["unit_id"] + ":f"))
        return ex
    anchors = []
    for a in m["anchors"]:
        anchors.append((bundle(a["vulnerable_files"], 1), 1, a["anchor_id"] + ":v", a["anchor_id"], a["lineage"]))
        anchors.append((bundle(a["fixed_files"], 0),      0, a["anchor_id"] + ":f", a["anchor_id"], a["lineage"]))
    return units_to_examples(tr), anchors

class DS(Dataset):
    def __init__(s, ex, tok):
        s.items = []
        for text, label, uid in ex:
            ids = tok(text, truncation=False)["input_ids"]
            wins = [ids[i:i+MAXLEN] for i in range(0, max(1, len(ids)-1), STRIDE)][:8] or [ids[:MAXLEN]]
            for w in wins: s.items.append((w, label, uid))
    def __len__(s): return len(s.items)
    def __getitem__(s, i): return s.items[i]

def collate(batch, pad):
    L = max(len(b[0]) for b in batch)
    x = torch.tensor([b[0] + [pad]*(L-len(b[0])) for b in batch])
    return x, (x != pad).long(), torch.tensor([b[1] for b in batch]), [b[2] for b in batch]

def main():
    manifest, seed, outdir = sys.argv[1], int(sys.argv[2]), sys.argv[3]
    os.makedirs(outdir, exist_ok=True)
    torch.manual_seed(seed); random.seed(seed); np.random.seed(seed)
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    tok = AutoTokenizer.from_pretrained(CKPT)
    model = AutoModelForSequenceClassification.from_pretrained(CKPT, num_labels=2).to(dev)
    tr, anchors = load(manifest)
    dl = DataLoader(DS(tr, tok), batch_size=BS, shuffle=True,
                    collate_fn=lambda b: collate(b, tok.pad_token_id))
    opt = torch.optim.AdamW(model.parameters(), lr=LR)
    sch = get_linear_schedule_with_warmup(opt, 0, EPOCHS * len(dl))
    for ep in range(EPOCHS):
        model.train(); tot = 0
        for x, mask, y, _ in dl:
            opt.zero_grad()
            out = model(x.to(dev), attention_mask=mask.to(dev), labels=y.to(dev))
            out.loss.backward(); opt.step(); sch.step(); tot += out.loss.item()
        print(f"[PC seed {seed}] epoch {ep+1} loss {tot/len(dl):.4f}", flush=True)
    model.eval(); preds = {}
    with torch.no_grad():
        for text, label, uid, aid, lin in anchors:
            ids = tok(text, truncation=False)["input_ids"]
            wins = [ids[i:i+MAXLEN] for i in range(0, max(1, len(ids)-1), STRIDE)][:8] or [ids[:MAXLEN]]
            logits = []
            for w in wins:
                x = torch.tensor([w]).to(dev)
                logits.append(model(x, attention_mask=(x != tok.pad_token_id).long()).logits[0].cpu().numpy())
            ml = np.mean(logits, axis=0)
            preds[uid] = {"anchor": aid, "lineage": lin, "label": label,
                          "pred": int(ml[1] > ml[0]), "logit_diff": float(ml[1] - ml[0])}
    out = f"{outdir}/preds_PC_seed{seed}.json"
    json.dump({"condition": "PC", "seed": seed, "scrub": SCRUB_VERSION,
               "injection": INJECTION_VERSION,
               "header_vuln": HDR_VULN, "header_fixed": HDR_FIXED,
               "checkpoint": CKPT, "predictions": preds}, open(out, "w"), indent=1)
    print("wrote", out)
    # margin pair accuracy, excluding the 5 fix-by-deletion anchors
    pairs = {}
    for v in preds.values():
        if v["anchor"] in SKIP: continue
        pairs.setdefault(v["anchor"], {})[v["label"]] = v["logit_diff"]
    done = {a: d for a, d in pairs.items() if 0 in d and 1 in d}
    pa = sum(1 for d in done.values() if d[1] > d[0]) / len(done)
    print(f"POSITIVE CONTROL margin pair accuracy: {pa:.4f} over {len(done)} pairs")
    print("expect > 0.95; a value near the Table 8 range (~0.5) means the")
    print("instrument CANNOT detect even explicit leakage -> stop and report.")

if __name__ == "__main__":
    main()
