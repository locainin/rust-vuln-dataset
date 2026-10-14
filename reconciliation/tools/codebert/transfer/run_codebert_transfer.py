#!/usr/bin/env python3
"""Fine-tune CodeBERT per condition/seed on the TRANSFER manifest.
Usage: python3 run_codebert_transfer.py transfer_manifest.json RX|HR|NU|ID <seed> <outdir>
Same pipeline as the completed experiment. Needs scrub.py beside it."""
import json, os, sys, random
import numpy as np, torch
from torch.utils.data import Dataset, DataLoader
from transformers import AutoTokenizer, AutoModelForSequenceClassification, get_linear_schedule_with_warmup
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from scrub import scrub, SCRUB_VERSION

CKPT="microsoft/codebert-base"; LR=2e-5; BS=8; EPOCHS=3; MAXLEN=512; STRIDE=256

def bundle(files):
    return "\n".join(scrub(open(f, encoding='utf-8', errors='replace').read()) for f in files)

def load(manifest_path, cond):
    m = json.load(open(manifest_path))
    pool = m["conditions"][cond]
    if "units" not in pool:
        sys.exit(f"condition {cond} is not runnable: {pool.get('status')}")
    by_id = {u["unit_id"]: u for u in m["train_units"]}
    train = [by_id[i] for i in pool["units"]]
    anchor_ents = {a["lineage"] for a in m["anchors"]}
    bad = [u["unit_id"] for u in train if u["entity"] in anchor_ents]
    assert not bad, f"training units overlap anchor entities: {bad}"
    lins = sorted({u["entity"] for u in train})
    rng = random.Random(m["manifest_seed"]); rng.shuffle(lins)
    val_l = set(lins[:max(1, len(lins)*15//100)])
    tr = [u for u in train if u["entity"] not in val_l]
    va = [u for u in train if u["entity"] in val_l]
    def to_examples(us):
        ex = []
        for u in us:
            ex.append((bundle(u["vulnerable_files"]), 1, u["unit_id"]+":v"))
            ex.append((bundle(u["fixed_files"]),      0, u["unit_id"]+":f"))
        return ex
    anchors = []
    for a in m["anchors"]:
        anchors.append((bundle(a["vulnerable_files"]), 1, a["anchor_id"]+":v", a["anchor_id"], a["lineage"]))
        anchors.append((bundle(a["fixed_files"]),      0, a["anchor_id"]+":f", a["anchor_id"], a["lineage"]))
    return to_examples(tr), to_examples(va), anchors

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
    dev = "cuda" if torch.cuda.is_available() else ("mps" if torch.backends.mps.is_available() else "cpu")
    tok = AutoTokenizer.from_pretrained(CKPT)
    model = AutoModelForSequenceClassification.from_pretrained(CKPT, num_labels=2).to(dev)
    tr, va, anchors = load(manifest, cond)
    print(f"[{cond} seed {seed}] train examples {len(tr)}, val {len(va)}, anchors {len(anchors)//2} pairs", flush=True)
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
    out=f"{outdir}/preds_{cond}_seed{seed}.json"
    json.dump({"condition":cond,"seed":seed,"scrub":SCRUB_VERSION,
               "checkpoint":CKPT,"design":"rustmizan-transfer-v1",
               "predictions":preds}, open(out,"w"), indent=1)
    print("wrote", out)

if __name__=="__main__": main()
