#!/usr/bin/env python3
"""Independent exhaustive regex check: all even words including 8 chars; no padding.
Odd-length words are not repaired; report intact prefix separately.
"""
import json,re,random,statistics,string
from pathlib import Path
P=Path(__file__).parent
D=json.loads((P/'input/ciphertexts.json').read_text())
# Deliberately separate regex implementation from dual_y_real_table.py predicate.
CONSONANTS='bcdfghjklmnpqrstvwxyz' # includes y
VOWELS='aeiouy'
allowed=set()
for a in CONSONANTS:
 for b in VOWELS:
  allowed.add(a+b);allowed.add(b+a)
# Pattern-level validation independent of script 1.
assert len(allowed)==len(set(allowed))

def result(name):
 words=D['analysis_variants'][name].split()
 even=[];odd=[]; pairs=[]
 for i,w in enumerate(words,1):
  if len(w)%2==0:
   even.append({'index':i,'word':w,'length':len(w)})
   pairs += [{'word_index':i,'pair_index':j//2+1,'symbol':w[j:j+2]} for j in range(0,len(w),2)]
  else:
   odd.append({'word_index':i,'word':w,'length':len(w),'tentative_prefix_pairs':[w[j:j+2] for j in range(0,len(w)-1,2)],'unpaired_final_letter':w[-1]})
 failures=[d for d in pairs if d['symbol'] not in allowed]
 rng=random.Random(20261010 + len(words))
 n=10000; null=[]
 for _ in range(n):
  nvalid=0
  for w in even:
   s=list(w['word']);rng.shuffle(s)
   nvalid+=sum(''.join(s[j:j+2]) in allowed for j in range(0,len(s),2))
  null.append(nvalid)
 return {'all_even_words_including_short':even, 'odd_words_original_untouched':odd, 'even_pair_total':len(pairs),'valid_pair_total':len(pairs)-len(failures),'invalid_pairs':failures,'allowed_bigrams':len(allowed),'null_n':n,'null_mean':round(statistics.mean(null),4),'null_std':round(statistics.pstdev(null),4),'null_max':max(null),'upper_tail_p_plus1':(sum(x>=len(pairs)-len(failures) for x in null)+1)/(n+1)}

out={n:result(n) for n in ['1917-06-24_0509','1917-06-29_0511','1916-04-03_POSITIVE_CONTROL']}
assert out['1917-06-24_0509']['valid_pair_total']==35 and not out['1917-06-24_0509']['invalid_pairs']
assert out['1917-06-29_0511']['valid_pair_total']==140 and len(out['1917-06-29_0511']['invalid_pairs'])==1
assert out['1916-04-03_POSITIVE_CONTROL']['valid_pair_total']==84
assert out['1917-06-24_0509']['odd_words_original_untouched'][0]['word']=='vemucayri'
# Do not count the four intact bigrams of the odd word among the 35/35 even total.
assert out['1917-06-24_0509']['odd_words_original_untouched'][0]['tentative_prefix_pairs']==['ve','mu','ca','yr']
(P/'results/extended_independent_results.json').write_text(json.dumps(out,indent=2,ensure_ascii=False))
for k,v in out.items():
 print(k,'even',v['valid_pair_total'],'/',v['even_pair_total'], 'odd',v['odd_words_original_untouched'],'failed:',v['invalid_pairs'], 'null mean',v['null_mean'],'p',v['upper_tail_p_plus1'])
