#!/usr/bin/env python3
"""Hidden-overlap scan: for each test anchor, the largest share of its distinctive
(>=20 chars, whitespace-normalized) vulnerable lines found in any single training unit.
Usage: python3 cross_resource_overlap.py CVE_SAMPLES RUST_MIZAN"""
import json,sys,re,collections as C
import os
HERE=os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0,HERE); sys.path.insert(0,os.path.join(HERE,'..','codebert','within_source'))
from common import resolve_path, REPO, check_pin
CVES,MIZ=sys.argv[1],sys.argv[2]
check_pin(CVES,'CVE_Samples'); check_pin(MIZ,'rust-mizan')
from scrub import scrub
R=REPO+'/'
def rd(f): return open(resolve_path(f,CVES,MIZ),errors='replace').read()
def lines(fs):
    s=set()
    for f in fs:
        for l in scrub(rd(f)).split('\n'):
            l=re.sub(r'\s+','',l)
            if len(l)>=20: s.add(l)
    return s
def run(man,unit_key,ent_key):
    m=json.load(open(man)); T=[(u[unit_key],u.get(ent_key),lines(u['vulnerable_files'])|lines(u['fixed_files'])) for u in m['train_units']]
    out=[]
    for a in m['anchors']:
        L=lines(a['vulnerable_files'])
        if not L: continue
        best=max(((len(L&t)/len(L),uid,e) for uid,e,t in T),key=lambda x:x[0])
        if best[0]>=0.5: out.append((a['anchor_id'],a['lineage'],len(L),round(best[0],2),best[1],best[2],best[2]==a['lineage']))
    return out
print('RQ3 anchors with >=50% of distinctive vulnerable lines contained in one training unit:')
for r in run(R+'reconciliation/tools/codebert/within_source/manifest.json','unit_id','lineage'): print(' ',r)
print('RQ4:')
for r in run(R+'reconciliation/tools/codebert/transfer/transfer_manifest.json','unit_id','entity'): print(' ',r)
