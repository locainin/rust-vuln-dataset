#!/usr/bin/env python3
"""Fine-tune CodeBERT per condition/seed on the manifest and log predictions.
Usage: python3 run_codebert.py manifest.json C2|C3|SC:<b> <seed> <outdir>
Pins: microsoft/codebert-base, lr 2e-5, batch 8, 3 epochs, max_len 512,
window 512 / stride 256, mean-logit aggregation over windows.
Requires: pip install torch transformers  (GPU strongly recommended)"""
import json, os, sys, random
import numpy as np, torch
from torch.utils.data import Dataset, DataLoader
from transformers import AutoTokenizer, AutoModelForSequenceClassification, get_linear_schedule_with_warmup
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from scrub import scrub, SCRUB_VERSION

CKPT="microsoft/codebert-base"; LR=2e-5; BS=8; EPOCHS=3; MAXLEN=512; STRIDE=256

def bundle(files):
    return "\n".join(scrub(open(f, encoding='utf-8', errors='replace').read()) for f in files)

def load(manifest, cond):
    m = json.load(open(manifest))
    removed = set()
    if cond == "C3": removed = set(m["conditions"]["C3"]["removed_units"])
    elif cond.startswith("SC:"):
        removed = set(m["conditions"]["SC"][int(cond.split(":")[1])]["removed_units"])
    train = [t for t in m["train_units"] if t["unit_id"] not in removed]
    # lineage-disjoint validation: hold out 15% of training lineages (never anchors)
    lins = sorted({t["lineage"] for t in train})
    rng = random.Random(m["manifest_seed"]); rng.shuffle(lins)
    val_l = set(lins[:max(1, len(lins)*15//100)])
    tr = [t for t in train if t["lineage"] not in val_l]
    va = [t for t in train if t["lineage"] in val_l]
    def units_to_examples(units):
        ex = []
        for u in units:
            ex.append((bundle(u["vulnerable_files"]), 1, u["unit_id"]+":v"))
            ex.append((bundle(u["fixed_files"]),      0, u["unit_id"]+":f"))
        return ex
    anchors = []
    for a in m["anchors"]:
        anchors.append((bundle(a["vulnerable_files"]), 1, a["anchor_id"]+":v", a["anchor_id"], a["lineage"]))
        anchors.append((bundle(a["fixed_files"]),      0, a["anchor_id"]+":f", a["anchor_id"], a["lineage"]))
    return units_to_examples(tr), units_to_examples(va), anchors

class DS(Dataset):
    def __init__(s, ex, tok):
        s.items=[]
        for text,label,uid in ex:
            ids = tok(text, truncation=False)["input_ids"]
            wins = [ids[i:i+MAXLEN] for i in range(0, max(1,len(ids)-1), STRIDE)][:8] or [ids[:MAXLEN]]
            for w in wins: s.items.append((w, label, uid))
    def __len__(s): return len(s.items)
    def __getitem__(s,i): return s.items[i]

def collate(batch, pad):
    L=max(len(b[0]) for b in batch)
    x=torch.tensor([b[0]+[pad]*(L-len(b[0])) for b in batch])
    return x,(x!=pad).long(),torch.tensor([b[1] for b in batch]),[b[2] for b in batch]

def main():
    manifest, cond, seed, outdir = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4]
    os.makedirs(outdir, exist_ok=True)
    torch.manual_seed(seed); random.seed(seed); np.random.seed(seed)
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    tok = AutoTokenizer.from_pretrained(CKPT)
    model = AutoModelForSequenceClassification.from_pretrained(CKPT, num_labels=2).to(dev)
    tr, va, anchors = load(manifest, cond)
    dl = DataLoader(DS(tr,tok), batch_size=BS, shuffle=True,
                    collate_fn=lambda b: collate(b, tok.pad_token_id))
    opt = torch.optim.AdamW(model.parameters(), lr=LR)
    sch = get_linear_schedule_with_warmup(opt, 0, EPOCHS*len(dl))
    for ep in range(EPOCHS):
        model.train(); tot=0
        for x,mask,y,_ in dl:
            opt.zero_grad()
            out = model(x.to(dev), attention_mask=mask.to(dev), labels=y.to(dev))
            out.loss.backward(); opt.step(); sch.step(); tot += out.loss.item()
        print(f"[{cond} seed {seed}] epoch {ep+1} loss {tot/len(dl):.4f}", flush=True)
    # anchor inference: mean logit over windows per sample
    model.eval(); preds={}
    with torch.no_grad():
        for text,label,uid,aid,lin in anchors:
            ids = tok(text, truncation=False)["input_ids"]
            wins = [ids[i:i+MAXLEN] for i in range(0, max(1,len(ids)-1), STRIDE)][:8] or [ids[:MAXLEN]]
            logits=[]
            for w in wins:
                x=torch.tensor([w]).to(dev)
                logits.append(model(x, attention_mask=(x!=tok.pad_token_id).long()).logits[0].cpu().numpy())
            ml = np.mean(logits, axis=0)
            preds[uid]={"anchor":aid,"lineage":lin,"label":label,
                        "pred":int(ml[1]>ml[0]),"logit_diff":float(ml[1]-ml[0])}
    out=f"{outdir}/preds_{cond.replace(':','_')}_seed{seed}.json"
    json.dump({"condition":cond,"seed":seed,"scrub":SCRUB_VERSION,
               "checkpoint":CKPT,"predictions":preds}, open(out,"w"), indent=1)
    print("wrote", out)

if __name__=="__main__": main()
