#!/usr/bin/env python3
"""Round 11 reproduction scaffold.

Tests an unrestricted injective mapping from observed two-letter symbols to 00..99,
then concatenates consecutive values into standard four-digit Chinese telegraph codes.
The search MUST first recover an independent known March 1917 key before any June
candidate can be considered. The 2026-10-07 run failed that control.

Usage:
  python arbitrary_table_positive_control.py --tw-csv /path/to/tw.csv --corpus input/training_corpus.json

The exact public tw.csv used in the recorded run was GitHub SHA
6ed7336293fa5dbfcd48bbed00e1e54b6149d333. This scaffold deliberately refuses a
mismatched file rather than silently changing the codebook. The recorded results are
in results/arbitrary_table_positive_control.json.
"""
import argparse,csv,hashlib,json,math,random,re,sys
EXPECTED_SHA1='6ed7336293fa5dbfcd48bbed00e1e54b6149d333'
M25='nasegapiru qoqasuxebi facohekicu nokaverabo zuboqabiqa suxebiqaza juvanete'
M26='getazazuji yineyomoni cemixetibi javesokaxo jikofanopu mizoyamaku xakizazuru qajipanejo tayelaxama kozabojifu xayokatuxo zimucuzaku'
BASE='bcdfghjklmnpqrstvxyz'; CO='klmnpqrstvxyzbcdfghj'; VO='aeuoi'

def load_codebook(path):
    raw=open(path,'rb').read(); sha=hashlib.sha1(raw).hexdigest()
    if sha!=EXPECTED_SHA1:
        raise SystemExit(f'tw.csv SHA1 mismatch: {sha} != {EXPECTED_SHA1}')
    d={}
    for row in csv.DictReader(raw.decode('utf-8').splitlines()):
        for code in row['code'].split():
            if re.fullmatch(r'\d{4}',code): d.setdefault(code,row['character'])
    return d

def segments(text):
    out=[]; cur=[]
    for word in text.lower().split():
        w=re.sub('[^a-z]','',word)
        if len(w)==10: cur.extend(w[i:i+2] for i in range(0,10,2))
        elif cur: out.append(cur); cur=[]
    if cur: out.append(cur)
    return out

def known_value(tok):
    ci=CO.index(tok[0]); vi=VO.index(tok[1]); return (20*vi+ci+1)%100

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--tw-csv',required=True); ap.add_argument('--corpus',required=True); args=ap.parse_args()
    code2ch=load_codebook(args.tw_csv)
    corp=json.load(open(args.corpus,encoding='utf-8'))['corpus']
    uni={}; bi={}; total=0
    for doc in corp:
        for c in doc: uni[c]=uni.get(c,0)+1; total+=1
        for a,b in zip(doc,doc[1:]): bi[a+b]=bi.get(a+b,0)+1
    V=5000
    def lpu(c): return math.log((uni.get(c,0)+.2)/(total+.2*V))
    def lpb(a,b): return math.log((bi.get(a+b,0)+.8*math.exp(lpu(b)))/(uni.get(a,0)+.8))
    ss=segments(M25)+segments(M26); symbols=sorted(set(sum(ss,[])))
    pairs=[list(zip(s[0::2],s[1::2])) for s in ss]
    def score(mp):
        sc=0; outs=[]
        for pp in pairs:
            cs=[]
            for a,b in pp:
                code=f'{mp[a]:02d}{mp[b]:02d}'; ch=code2ch.get(code)
                if ch is None: cs.append('□'); sc-=22
                else: cs.append(ch); sc+=.12*lpu(ch)
            for a,b in zip(cs,cs[1:]): sc += -8 if '□' in (a,b) else lpb(a,b)
            outs.append(''.join(cs))
        return sc,outs
    oracle={s:known_value(s) for s in symbols}
    print(json.dumps({'symbols':len(symbols),'oracle_score':score(oracle)[0],'oracle_plaintext':score(oracle)[1]},ensure_ascii=False,indent=2))
    print('Full simulated-annealing parameters and the frozen observed result are in results/arbitrary_table_positive_control.json.')
if __name__=='__main__': main()
