#!/usr/bin/env python3
"""Independent reconstruction of exhibited No.64 style condenser from
Aichi University image + pre-2026 published example; June = holdout.
No Chinese fit or emendation permitted. Standard-library only.
"""
import json, itertools, string, collections, hashlib
from pathlib import Path
ROOT=Path(__file__).parent
DATA=json.loads((ROOT/'input/ciphertexts.json').read_text())
NUMBERS=[2514,2894,1129,668,3634]
LETTERS=['caze','dite','zude','yuni','gufe']
HISTORIC_CHARS='時機大可為'
VOWELS='aeiou'
CONS=''.join(c for c in string.ascii_lowercase if c not in VOWELS+'w')
assert len(CONS)==20 and len(VOWELS)==5
# Model family: cyclic 20 consonants, optional reversal; 5! vowels;
# row-major vs column-major; first 0 or last 00.
def generate(cons, vs, fill_order, start):
    values=(list(range(100)) if start==0 else list(range(1,100))+[0])
    if fill_order=='rows':
        pairs=[c+v for c in cons for v in vs]
    else:
        pairs=[c+v for v in vs for c in cons]
    return dict(zip(values,pairs))
def keys(leave_out=None):
    for reverse in (False,True):
        cc=CONS[::-1] if reverse else CONS
        for shift in range(20):
            cr=cc[shift:]+cc[:shift]
            for vs in itertools.permutations(VOWELS):
                vv=''.join(vs)
                for fill in ('rows','columns'):
                    for start in (0,1):
                        t=generate(cr,vv,fill,start)
                        if all(t[n//100]+t[n%100]==s for i,(n,s) in enumerate(zip(NUMBERS,LETTERS)) if i!=leave_out):
                            yield {'reverse':reverse,'shift':shift,'consonants':cr,'vowels':vv,'fill':fill,'start':start,'table':t}
hits=list(keys())
print('matched_keys:',len(hits))
heldout=[]
for i,(number,cipher) in enumerate(zip(NUMBERS,LETTERS)):
    variants=list(keys(leave_out=i))
    guesses=sorted({k['table'][number//100]+k['table'][number%100] for k in variants})
    heldout.append({'heldout_index':i+1, 'heldout_number':f'{number:04d}', 'heldout_word':cipher, 'key_count_after_training_four':len(variants), 'predictions':guesses, 'predicted_correctly':guesses==[cipher]})
    print('heldout',i+1,'keys',len(variants),'guesses',guesses,'correct',guesses==[cipher])
for k in hits:
    print('KEY', {kk:vv for kk,vv in k.items() if kk!='table'})
assert hits

def getwords(day):
    s=DATA['analysis_variants'][day].split()
    good=[(i+1,w) for i,w in enumerate(s) if len(w)==10]
    excluded=[(i+1,w,len(w)) for i,w in enumerate(s) if len(w)!=10]
    return good,excluded

def apply_table(k,day,allow_vc=False):
    words,excluded=getwords(day)
    inv={v:n for n,v in k['table'].items()}
    matches,unknown=[],[]
    slot_idx=0
    for wi,w in words:
        for a in range(0,10,2):
            p=w[a:a+2]
            n=inv.get(p)
            orientation='cv'
            if n is None and allow_vc:
                n=inv.get(p[::-1]);orientation='vc'
            r=dict(word_index=wi,word=w,slot=a//2+1,token=p,number=n,orientation=orientation if n is not None else None)
            (matches if n is not None else unknown).append(r)
            slot_idx+=1
    return dict(name=day,total=len(matches)+len(unknown),matched=len(matches),unknown_count=len(unknown),unmapped=unknown,matched_slots=matches,excluded=excluded)

results={'leave_one_4digit_codeout_crossvalidation':heldout,'museum_example':{'characters':HISTORIC_CHARS,'code_numbers_4digits':[f'{n:04d}' for n in NUMBERS], 'four_letters':LETTERS, 'ten_letter_regroup':' '.join((''.join(LETTERS)[i:i+10] for i in range(0,len(''.join(LETTERS)),10)))}, 'model_family_count':20*2*120*2*2,'match_count':len(hits),'key_descriptions':[{q:v for q,v in k.items() if q!='table'} for k in hits], 'tests':{}}
for kidx,k in enumerate(hits):
    for day in ['1917-06-24_0509','1917-06-29_0511','1916-04-03_POSITIVE_CONTROL']:
        for rev in (False,True):
            r=apply_table(k,day,rev)
            results['tests'][f'{kidx}:{day}:reverse_allowed={rev}']=r
            print(day,'reverse',rev,'total',r['total'],'matched',r['matched'],'unmapped',r['unknown_count'])
    # original same-source numeric conversion: independent per-code held-out validation above
    assert [k['table'][n//100]+k['table'][n%100] for n in NUMBERS]==LETTERS
results['source_keys']={'official_gallery_url':'https://edu.aichi-u.ac.jp/toa/collection/gallery02/Com1000075.html', 'image_link':'https://edu.aichi-u.ac.jp/toa/collection/gallery02/19EU5116_RT8.jpg', 'independent_published_transcription':'https://github.com/NoAutopilot/cipher-lab/blob/main/sources/cryptiana/web/chinesecrypto_e.htm', 'input_ciphertexts':'public notes/fam6, original scans not checked'}
res=ROOT/'results'; res.mkdir(exist_ok=True)
(res/'museum_numeric_key_test.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))
print('saved',res/'museum_numeric_key_test.json')
