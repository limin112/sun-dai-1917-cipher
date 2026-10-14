#!/usr/bin/env python3
"""Round 14: exact historical-64 condenser grammar, hypothesis y as two roles.
No hidden spell correction, no plaintext scoring, no unauthorized archival claims.
"""
import json, random, hashlib, statistics, string
from pathlib import Path
from collections import Counter
ROOT=Path(__file__).parent
D=json.loads((ROOT/'input/ciphertexts.json').read_text())
V5=set('aeiou'); V6=set('aeiouy'); A=set(string.ascii_lowercase)
R='xyzbcdfghjklmnpqrstv'; C='uoiea'
assert len(R)==20 and len(C)==5 and len(set(R))==20
# Official 64th-number row major, 01 through 99 then 00.
P2N={r+c:(5*i+j+1)%100 for i,r in enumerate(R) for j,c in enumerate(C)}
assert len(P2N)==100 and P2N['xu']==1 and P2N['va']==0

def ordinary(pair):
 a,b=pair
 return bool((a in V5)^(b in V5))
def sixv(pair):
 a,b=pair
 return bool((a in V6)^(b in V6))
def dual(pair):
 a,b=pair
 # y can be either the consonant or the vowel; ordinary a/e/i/o/u do not become consonants.
 return ((a in V6 and b in A-V5) or (b in V6 and a in A-V5))

def tok_to_num(pair,alias):
 if not dual(pair): return None
 if pair in P2N: return P2N[pair]
 if pair[::-1] in P2N: return P2N[pair[::-1]]
 # if y acts as a sixth (alias) vowel next to a non-vowel non-y consonant, replace y by historical vowel
 aa,bb=pair
 if aa=='y' and bb in set(R)-{'y'}: s=bb+alias
 elif bb=='y' and aa in set(R)-{'y'}: s=aa+alias
 elif aa=='y' and bb=='y': s='y'+alias
 else: return None
 return P2N.get(s)

def groups(word):
 return [word[i:i+2] for i in range(0,len(word),2)]

def select(msg):
 words=msg.split(); return [(wi,w) for wi,w in enumerate(words,1) if len(w)==10], [(wi,w) for wi,w in enumerate(words,1) if len(w)!=10]

def run_one(name,text, n=10000,seed=20261010):
 valid,short=select(text)
 pair_records=[{'word_index':wi,'word':w,'pair_index':j+1,'pair':p} for wi,w in valid for j,p in enumerate(groups(w))]
 obs={k:sum(f(x['pair']) for x in pair_records) for k,f in [('ordinary5',ordinary),('sixvowel_yonly',sixv),('y_dualrole',dual)]}
 rng=random.Random(seed+len(valid)*100+len(short))
 null={k:[] for k in obs}
 for _ in range(n):
  randpair=[]
  for _,w in valid:
   chars=list(w);rng.shuffle(chars)
   randpair.extend(groups(''.join(chars)))
  null['ordinary5'].append(sum(map(ordinary,randpair)))
  null['sixvowel_yonly'].append(sum(map(sixv,randpair)))
  null['y_dualrole'].append(sum(map(dual,randpair)))
 desc={k:{'observed':v,'null_mean':round(statistics.mean(null[k]),4),'null_stdev':round(statistics.pstdev(null[k]),4),'null_max':max(null[k]),'upper_tail_p_plus1':(sum(x>=v for x in null[k])+1)/(n+1)} for k,v in obs.items()}
 fails={k:[r for r in pair_records if not func(r['pair'])] for k,func in [('ordinary5',ordinary),('sixvowel_yonly',sixv),('y_dualrole',dual)]}
 candidates={}
 for a in C:
  tokens=[tok_to_num(d['pair'],a) for d in pair_records]
  codes=[]
  for j in range(0,len(tokens)//2*2,2):
   p,q=tokens[j:j+2]
   codes.append((f'{p:02d}{q:02d}' if p is not None and q is not None else '????'))
  candidates[a]={'decoded_two_digit_tokens':sum(x is not None for x in tokens),'token_values':[f'{x:02d}' if x is not None else '??' for x in tokens], 'four_digit_stream_in_valid_words_only':codes, 'warning':'Analytical stream only: excludes short words and ignores cross-word continuity; not verified ciphertext alignment and NOT Chinese plaintext'}
 return {'name':name,'tenletter_words':len(valid),'pair_slots':len(pair_records),'excluded':short,'grammar':desc,'fails':fails,'dual_y_numbers_under_64th':candidates}

# Verified historical examples from museum and 2018 journal: do not use to fit June.
example=[('2514','caze'),('2894','dite'),('1129','zude'),('0668','yuni'),('3634','gufe'),('2494','cete'),('1378','ziqi'),('4316','hibu'),('7193','puti'),('1032','yafo')]
controls=[]
for code,word in example:
 pieces=[word[:2],word[2:]]
 got=''.join(f'{P2N[p]:02d}' for p in pieces)
 controls.append({'numeric_code':code,'published_letter_code':word,'calculated_numeric_code':got,'pass':code==got})
assert all(x['pass'] for x in controls)

results={
 'objective':'Structural dual-role y diagnostic and five explicitly hypothetical vowel-alias conversions on a historical 64th table; not a decoder of June',
 'source_sha256':hashlib.sha256((ROOT/'input/ciphertexts.json').read_bytes()).hexdigest(),
 'hypotheses':{'ordinary5':'y is consonant only, vowel a/e/i/o/u','sixvowel_yonly':'y is vowel only, consonants exclude y','y_dualrole':'y in both roles; allowed every pair mixing one vowel (aeiouy) and one consonant (bcdfghjklmnpqrstvwxyz incl y); e.g yy permitted; ee forbidden','historical_64th':'20 row consonants xyzbcdfghjklmnpqrstv, 5 vowels uoiea, 01..99,00', 'y_alias':'Speculative: when y is vowel, map it to one of a/e/i/o/u; when y is consonant, use its real published row. No evidence actual messages use this.'},
 'controls':controls,
 'june':{},
 'additional_historical_positive_control':run_one('1916-04-03_POSITIVE_CONTROL',D['analysis_variants']['1916-04-03_POSITIVE_CONTROL'],n=5000,seed=20261010)
}
for i,name in enumerate(('1917-06-24_0509','1917-06-29_0511')):
 results['june'][name]=run_one(name,D['analysis_variants'][name],n=10000,seed=20261010+i)
path=ROOT/'results/dual_y_results.json';path.write_text(json.dumps(results,ensure_ascii=False,indent=2))
for k,v in results['june'].items():
 print(k,'complete words',v['tenletter_words'],'slots',v['pair_slots'],'excluded',v['excluded'])
 for hypothesis,info in v['grammar'].items():print(' ',hypothesis,info,'fails:',[(x['word_index'],x['pair']) for x in v['fails'][hypothesis]])
 print(' alias successes:',[(a, x['decoded_two_digit_tokens']) for a,x in v['dual_y_numbers_under_64th'].items()])
print('positive historical demonstrations',len(controls),'matched',sum(x['pass'] for x in controls))
print('1916 apr baseline',results['additional_historical_positive_control']['grammar'])
print('wrote',path)
