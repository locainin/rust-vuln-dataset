#!/usr/bin/env python3
"""Line-level evidence for the 17 identifier links: containment of each record's removed/added
lines in the other record's vulnerable and fixed sides (whitespace-normalized, comments dropped).
Usage: python3 link_evidence.py CVE_SAMPLES RUST_MIZAN > outputs/link_evidence.txt"""
import os,re,glob
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import REPO, check_pin
check_pin(sys.argv[1],'CVE_Samples'); check_pin(sys.argv[2],'rust-mizan')
R=os.path.join(REPO,'manual')+'/'; H=sys.argv[1]+'/Data/'; M=sys.argv[2]+'/samples/'
def norm(s): return [re.sub(r'\s+','',l) for l in s.split('\n') if re.sub(r'\s+','',l) and not re.sub(r'\s+','',l).startswith('//')]
def cont(a,b):
    A=norm(a); B=set(norm(b)); return sum(x in B for x in A)/max(1,len(A))
def rx(adv):
    out=[]
    for p in sorted(glob.glob(R+adv+'/pairs/*/')):
        out.append((os.path.basename(p[:-1]),open(p+'vulnerable.rs').read(),open(p+'fixed.rs').read()))
    return out
def hr(cve):
    fn=[f for f in os.listdir(H+'Positive') if f.startswith(cve+'_')][0]
    return open(H+'Positive/'+fn).read(),open(H+'Negative/'+fn).read()
def mz(v):
    n=v.split('-')[1]; res={}
    for side,pre in (('v','0'),('f','1')):
        txt=''
        for d in glob.glob(M+v+'/sample-'+pre+n+'-*'):
            if d.endswith('function') or d.endswith('crate') or d.endswith('file'):
                for f in glob.glob(d+'/**/*.rs',recursive=True): txt+=open(f,errors='replace').read()+'\n'
        res[side]=txt
    return res['v'],res['f']
def removed_added(v,f):
    V,F=norm(v),norm(f); sv,sf=set(V),set(F)
    return [x for x in V if x not in sf],[x for x in F if x not in sv]
def tests(s): return len(re.findall(r'#\[test\]|fn test_\w*\(|#\[cfg\(test\)\]',s))
def report(adv,other,kind):
    for name,v,f in rx(adv):
        if kind=='HR': ov,of=hr(other)
        else: ov,of=mz(other)
        rem,add=removed_added(v,f)
        # do the vulnerable-only lines of RX appear in other's vuln side and not fixed side? and added lines in other's fixed
        ovs,ofs=set(norm(ov)),set(norm(of))
        r_in_v=sum(x in ovs for x in rem); r_in_f=sum(x in ofs for x in rem)
        a_in_v=sum(x in ovs for x in add); a_in_f=sum(x in ofs for x in add)
        print(f"{adv}:{name} vs {kind} {other}: RXvuln⊂otherV={cont(v,ov):.2f} RXfix⊂otherF={cont(f,of):.2f} | RX-removed {len(rem)}: inV {r_in_v} inF {r_in_f} | RX-added {len(add)}: inV {a_in_v} inF {a_in_f} | tests V/F {tests(ov)}/{tests(of)}")
for adv,cve in [('RUSTSEC-2021-0003','CVE-2021-25900'),('RUSTSEC-2021-0020','CVE-2021-21299'),('RUSTSEC-2021-0143','CVE-2021-21235'),('RUSTSEC-2022-0013','CVE-2022-24713'),('RUSTSEC-2022-0038','CVE-2022-31173'),('RUSTSEC-2022-0101','CVE-2022-31169'),('RUSTSEC-2024-0009','CVE-2024-23644'),('RUSTSEC-2024-0010','CVE-2024-21491'),('RUSTSEC-2024-0341','CVE-2024-28854')]:
    report(adv,cve,'HR')
for adv,v in [('RUSTSEC-2021-0003','vuln-0006'),('RUSTSEC-2025-0016','vuln-0029'),('RUSTSEC-2025-0018','vuln-0041')]:
    report(adv,v,'MZ')
print()
# HR-MZ links: HR removed/added lines found in MZ vuln/fixed
for cve,v in [('CVE-2018-21000','vuln-0003'),('CVE-2020-35869','vuln-0033'),('CVE-2020-35870','vuln-0034'),('CVE-2021-25900','vuln-0006'),('CVE-2023-50711','vuln-0026')]:
    hv,hf=hr(cve); mv,mf=mz(v); rem,add=removed_added(hv,hf); mvs,mfs=set(norm(mv)),set(norm(mf))
    mrem,madd=removed_added(mv,mf)
    print(f"{cve}~{v}: HR removed {len(rem)} (in MZv {sum(x in mvs for x in rem)}, MZf {sum(x in mfs for x in rem)}); HR added {len(add)} (in MZv {sum(x in mvs for x in add)}, MZf {sum(x in mfs for x in add)}); MZ diff lines -{len(mrem)}/+{len(madd)}; MZ-removed in HRv {sum(x in set(norm(hv)) for x in mrem)} HRf {sum(x in set(norm(hf)) for x in mrem)}; MZ-added in HRv {sum(x in set(norm(hv)) for x in madd)} HRf {sum(x in set(norm(hf)) for x in madd)}")
