#!/usr/bin/env python3
"""Check explicit alternatives in previously frozen NOTES, without deciding their authenticity."""
import json
from pathlib import Path
P=Path(__file__).parent
D=json.loads((P/'input/ciphertexts.json').read_text())
C=set('bcdfghjklmnpqrstvwxyz');V=set('aeiouy')
ALLOWED={a+b for a in C for b in V}|{b+a for a in C for b in V}
variants={
 '24_fam6':D['analysis_variants']['1917-06-24_0509'],
 '24_optional_u_present':D['analysis_variants']['1917-06-24_0509'].replace('mevecafema','mevecafemau'),
 '29_fam6':D['analysis_variants']['1917-06-29_0511'],
 '29_explicit_notes_go':D['analysis_variants']['1917-06-29_0511'].replace('hutadynyyg','hutadynygo'),
 '29_optional_y_present_11':D['analysis_variants']['1917-06-29_0511'].replace('hutadynyyg','hutadynyygo'),
}
out={}
for key,txt in variants.items():
 failure=[];odd=[];total=0
 for wi,w in enumerate(txt.split(),1):
  for j in range(0,len(w)//2*2,2):
   pair=w[j:j+2];total+=1
   if pair not in ALLOWED:failure.append({'word_index':wi,'slot':j//2+1,'word':w,'symbol':pair})
  if len(w)%2:odd.append({'word_index':wi,'word':w,'orphan':w[-1]})
 out[key]={'pairs_from_start_of_each_word_including_odd_prefixes':total,'good':total-len(failure),'bad':failure,'odd_word_orphans':odd,'input_is_not_image_verified':True}
(P/'results/variant_sensitivity.json').write_text(json.dumps(out,ensure_ascii=False,indent=2))
for k,v in out.items():print(k,v)
