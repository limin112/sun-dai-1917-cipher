#!/usr/bin/env python3
"""June 1917 Sun/Dai telegrams: independent on-page word-count QA,
Morse ambiguity enumeration, paired-code phase repetition with in-word null,
and independent MARCH 1917 positive-control calibration.

Does NOT infer a numerical key or decode June Chinese.
Reproducible Python >=3.8 stdlib. DO NOT alter frozen inputs.
"""
import collections, hashlib, itertools, json, pathlib, random, statistics

R=pathlib.Path(__file__).resolve().parent
OUT=R/'results'; OUT.mkdir(exist_ok=True)
def load(rel):return json.loads((R/rel).read_text(encoding='utf-8'))
def put(name,data):(OUT/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
RAW=R/'input/ciphertexts.json'
assert hashlib.sha256(RAW.read_bytes()).hexdigest()=='620e469ec26d6534df2dbad0553d79844f1d9df8e68e47a95194a1c0563a8136'
wit=load('input/independent_witness.json')
pages=load('input/morse_and_page_observations.json')
march=load('input/march_positive_control.json')
a=wit['telegrams']['1917-06-24_0509']['words']
j=wit['telegrams']['1917-06-29_0511']['words']
b=j[:18];c=j[18:]
assert len(a)==8 and len(j)==29 and len(b)==18 and len(c)==11
assert [sum(map(len,q)) for q in (a,b,c)] == [80,172,110]

def blocks(words,phase=0):
    s=''.join(words)
    return [s[i:i+4] for i in range(phase,len(s)-3,4)]

def phase_score(sheets,phases=(0,0,0)):
    cc=[collections.Counter(blocks(s,phase)) for s,phase in zip(sheets,phases)]
    csum=sum(cc,collections.Counter())
    repeats=sum(v*(v-1)//2 for v in csum.values())
    cross=sum(sum(cc[i][key]*cc[j][key] for key in csum) for i in range(3) for j in range(i+1,3))
    match={key:{'total':value,'per_segment':[p[key] for p in cc]} for key,value in sorted(csum.items()) if value>1}
    return {'repeat_pairs_total':repeats,'cross_segment_repeat_pairs':cross,'cross_segment_distinct_types':sum(sum(q[key]>0 for q in cc)>1 for key in csum),'within_last_sheet_pairs':sum(v*(v-1)//2 for v in cc[-1].values()),'repeats':match}

def phase_metrics_fast(sheets,phases):
    cc=[collections.Counter(blocks(s,ph)) for s,ph in zip(sheets,phases)]
    total=cc[0]+cc[1]+cc[2]
    repeated=sum(v*(v-1)//2 for v in total.values())
    cross=sum(sum(cc[i][k]*cc[j][k] for k in (cc[i].keys() & cc[j].keys())) for i in range(3) for j in range(i+1,3))
    distinct=sum((bool(cc[0][k])+bool(cc[1][k])+bool(cc[2][k]))>=2 for k in total)
    return (repeated,cross,distinct)

def shuffle_within_words(words,rng):
    out=[]
    for w in words:
        pairs=[w[i:i+2] for i in range(0,len(w)-1,2)]
        rng.shuffle(pairs)
        out.append(''.join(pairs)+(w[-1] if len(w)%2 else ''))
    return out

def shuffle_within_segment(words,rng):
    whole=''.join(words)
    pairs=[whole[i:i+2] for i in range(0,len(whole)-1,2)]
    rng.shuffle(pairs)
    return [''.join(pairs)+(whole[-1] if len(whole)%2 else '')]

def null_phase_exp(sheets,seed,n,shuffle):
    rng=random.Random(seed)
    obs0=phase_score(sheets,(0,0,0))
    obs2=phase_score(sheets,(0,0,2))
    # Always maximize over BOTH pre-specified b-sheet phases inside every null draw.
    observed={metric:max(obs0[metric],obs2[metric]) for metric in ('repeat_pairs_total','cross_segment_repeat_pairs','cross_segment_distinct_types')}
    ge=collections.Counter(); sums=collections.Counter(); maxseen=collections.Counter()
    for _ in range(n):
        q=[shuffle(w,rng) for w in sheets]
        s0=phase_metrics_fast(q,(0,0,0)); s2=phase_metrics_fast(q,(0,0,2))
        for ii,metric in enumerate(observed):
            z=max(s0[ii],s2[ii]);sums[metric]+=z
            if z>=observed[metric]: ge[metric]+=1
            maxseen[metric]=max(maxseen[metric],z)
    return {'seed':seed,'draws':n,'shuffle_model':shuffle.__name__,
            'observed_b_phase0':{k:v for k,v in obs0.items() if k!='repeats'},
            'observed_b_phase2':{k:v for k,v in obs2.items() if k!='repeats'},
            'observed_max_b_phase0_or_2':observed,
            'ge_in_n':dict(ge), 'mean_max_null':{k:sums[k]/n for k in observed},
            'max_null':dict(maxseen), 'p_plus1_corrected':{k:(1+ge[k])/(n+1) for k in observed},
            'warning':'exploratory statistic: hypotheses/phases were discussed in Round16 before scoring; p controls only this declared within-run two-phase search, not all earlier discovery choices.'}

def null_all_three_phases(sheets,seed=479,n=12000):
    """Control eight possibilities (two 4-letter phases per independent segment).
    Exact evaluated statistics: number of types present in ALL THREE independent
    segments and sum of cross-segment matching pair occurrences.
    The lexicographic max is repeated on every null draw.
    """
    combos=list(itertools.product((0,2),repeat=3))
    def measure(groups,offsets):
        cs=[collections.Counter(blocks(w,p)) for w,p in zip(groups,offsets)]
        names=set(cs[0])|set(cs[1])|set(cs[2])
        shared_all3=sum(bool(cs[0][k] and cs[1][k] and cs[2][k]) for k in names)
        cross=sum(cs[i][k]*cs[j][k] for k in names for i in range(3) for j in range(i+1,3))
        return (shared_all3,cross)
    def best(groups):
        ranked=[(measure(groups,ph),ph) for ph in combos]
        return max(ranked,key=lambda z:z[0])
    obs=best(sheets)
    rng=random.Random(seed);ge=0;tots=0;maxtriple=0
    for _ in range(n):
        q=[shuffle_within_words(w,rng) for w in sheets]
        trial=best(q)[0]
        ge+=trial>=obs[0]
        tots+=trial[0]
        maxtriple=max(maxtriple,trial[0])
    return {'n':n,'seed':seed,'phase_combinations_tested_per_draw':8,'observed_max_triple_distinct_and_cross_pairs':list(obs[0]),
      'best_phase_offsets_0509_0511a_0511b':list(obs[1]),'null_max_triple':maxtriple,
      'null_mean_max_triple':tots/n,'ge_lexicographic':ge,'p_plus1_lexicographic':(ge+1)/(n+1),
      'note':'More conservative phase search than the two-variant b-only test; this still does not correct for all hypotheses selected in previous research rounds.'}

def march_positive(seed=317,n=12000):
    msgs=[text.lower().split() for text in march['messages'].values()]
    obs=phase_score(msgs,(0,0,0))
    assert obs['cross_segment_repeat_pairs']==5 and obs['repeat_pairs_total']==9
    rng=random.Random(seed);ge=0;total=0;maximum=0
    for _ in range(n):
        q=[shuffle_within_words(s,rng) for s in msgs]
        z=phase_metrics_fast(q,(0,0,0))[1];total+=z
        ge+=z>=obs['cross_segment_repeat_pairs'];maximum=max(maximum,z)
    return {'name':'1917 March published Sun–Dai telegrams (KNOWN independent key); only used as positive control, never June plaintext',
            'source_sha':march['github_blob_sha'], 'segments_word_counts':[len(s) for s in msgs],
            'segment_letter_counts':[sum(map(len,s)) for s in msgs],
            'source_not_perfect_original':'March 23 has known unresolved damaged groups, treated literally.',
            'cross_segment_repeated_codes_observed':obs['cross_segment_repeat_pairs'],
            'repeated_code_types':[k for k,v in obs['repeats'].items() if sum(x>0 for x in v['per_segment'])>1],
            'n':n,'shuffle_model':'shuffle_within_words', 'ge':ge,'p_plus1':(1+ge)/(n+1), 'null_mean':total/n,'null_max':maximum}

def morse_test():
    table={
      'a':'.-','b':'-...','c':'-.-.','d':'-..','e':'.','f':'..-.','g':'--.','h':'....','i':'..','j':'.---','k':'-.-','l':'.-..',
      'm':'--','n':'-.','o':'---','p':'.--.','q':'--.-','r':'.-.','s':'...','t':'-','u':'..-','v':'...-','w':'.--','x':'-..-','y':'-.--','z':'--..'}
    V=set('aeiou');C=set('bcdfghjklmnpqrstvwxz')
    def legal(s):return all((s[i] in V|{'y'} and s[i+1] in C|{'y'}) or (s[i+1] in V|{'y'} and s[i] in C|{'y'}) for i in range(0,len(s)-1,2))
    transmitted_morse='.-.-' # INTERNATIONAL MORSE Ä; sourced as stated in Brice/Daniel notes
    options=[]; donor=[x for x in j if x]
    hist=collections.Counter(s[k:k+2] for word in j for k in range(0,len(word)-1,2) for s in [word])
    for aa,ma in table.items():
        for bb,mb in table.items():
            if ma+mb!=transmitted_morse:continue
            word='vemuc'+aa+bb+'yri'
            assert len(word)==10
            pairs=[word[i:i+2] for i in range(0,10,2)]
            # No probabilistic claim: exploratory Laplace bigram occurrence product in held-out 0511.
            weight=1
            for q in pairs:weight*=hist[q]+1
            options.append({'morse_split':aa+bb,'candidate_word2':word,'pairs':pairs,'cv_y_dual_all_legal':legal(word),'paired_digraph_support_in_0511':[hist[x] for x in pairs], 'laplace_product_exploratory':weight})
    assert sorted(x['morse_split'] for x in options)==['aa','ek','rt']
    return {'observed_morse_character':'ä','international_morse_for_ä':transmitted_morse,
            'observed_literal_image_reading':'vemucäyri (graphic reading; not unique reconstruction)',
            'known_independent_editorial_witness':'vemucicyri (different human reading, not assumed same Morse signal)',
            'standard_english_alphabet_exactly_two_letter_splits':options,
            'warning':'Only two ASCII-character segmentation of an actual transmitted Ä; an intentional Ä glyph or another transmission convention remains possible. Grammar does not identify unique reading or decrypt June.'}

def lengths_and_counts():
    ans={}
    for key,words in [('0509',a),('0511_sheet_a',b),('0511_sheet_b',c),('0511_full',j)]:
        ls=list(map(len,words)); size=sum(ls)
        ans[key]={'groups':len(words),'chars':size,'bigrams_if_uninterrupted':size//2,'trailing_single_chars_if_any':size%2,'mod4':size%4,'distribution':dict(sorted(collections.Counter(ls).items())),'odd_length_words':[{'index1':i,'word':w} for i,w in enumerate(words,1) if len(w)%2]}
    ans['0509_form_accounting']={'declared_charge_words':pages['0509']['form_words_field_visual'],'cipher_groups':len(a),'cleartext_signature':1,'address_words_provisionally':5,'sum':len(a)+1+5}
    ans['0511_form_accounting']={'declared_charge_words':pages['0511']['form_words_field_visual'],'cipher_groups':len(j),'cleartext_signature':1,'two_address_words':2,'sum':len(j)+1+2}
    assert ans['0511_form_accounting']['sum']==32 and ans['0509_form_accounting']['sum']==14
    ans['4_letter_code_necessary_residue']={'0509_remainder':80%4,'0511a_remainder':172%4,'0511b_remainder':110%4,'0511_total_remainder':282%4,
      'logic':'Under a pure 4-Latin-letters-per-Hanzi body model, 0511 has 2 letters in excess/modulo 4, so it needs >=2 total char insert/delete to become divisible by 4, or an explicit 2-letter other-code/padding/header; ONE letter change alone cannot remove the parity defect. This is not evidence any specific two printed letters were erroneous.',
      'sheet_phase_tension':'If a ends at 172 letters (0 mod 4) and forms one continuous four-letter code stream, b should start phase0, yet repeated-code search prefers b phase2. Possible damage/restart/other code classes or selection bias; not proof of omission.'}
    return ans

def evidence_locs(sheets,phases=(0,0,2)):
    ret={}
    for name,words,phase in zip(['0509','0511a','0511b'],sheets,phases):
        ss=''.join(words); offs=[];q=0
        for k,word in enumerate(words,1):offs.append((q,q+len(word),k));q+=len(word)
        group=[]
        for i in range(phase,len(ss)-3,4):
            r=ss[i:i+4]; ifound=[k for left,right,k in offs if left<i+4 and right>i]
            group.append({'pattern':r,'zero_based_letter_offset':i,'word_ids':ifound,'crosses_word_boundary':len(ifound)>1})
        ret[name]=group
    counts=phase_score(sheets,phases)['repeats']
    return {k:{'per_segment':v['per_segment'],'occurrences':{name:[t for t in ret[name] if t['pattern']==k] for name in ret}} for k,v in counts.items()}

def sensitivities():
    out={}
    for label,replacements in [
      ('independent_witness_as_is',{}),
      ('only_0511b_word8_g_to_j',{25:'fojylisicy'}),
      ('only_0511a_word12_wm_to_um',{11:'damoumhosy'}),
      ('both_editorial_alternatives',{25:'fojylisicy',11:'damoumhosy'}),
      ('remove_terminal_e_from_both_odd_length_words',{0:'muposacyob',2:'catyidoh'}),
    ]:
        copy=j[:]
        for i,v in replacements.items(): copy[i]=v
        p0=phase_score([a,copy[:18],copy[18:]],(0,0,0))
        p2=phase_score([a,copy[:18],copy[18:]],(0,0,2))
        out[label]={'changes_are_hypotheses_NOT_acceptance':replacements,'chars_0511a':sum(map(len,copy[:18])),'chars_total':sum(map(len,copy)),
                    'b_phase0':{k:v for k,v in p0.items() if k!='repeats'}, 'b_phase2':{k:v for k,v in p2.items() if k!='repeats'},
                    'repeat_types_bphase2':{k:v['per_segment'] for k,v in p2['repeats'].items()}}
    return out

def main():
    null=null_phase_exp([a,b,c],171717,50000,shuffle_within_words)
    n2=null_phase_exp([a,b,c],19171917,12000,shuffle_within_segment)
    phase8=null_all_three_phases([a,b,c],n=12000)
    positive=march_positive(n=12000)
    morse=morse_test();counts=lengths_and_counts();loc=evidence_locs([a,b,c]);sense=sensitivities()
    assert all(x['cv_y_dual_all_legal'] for x in morse['standard_english_alphabet_exactly_two_letter_splits'] if x['morse_split'] in ('ek','aa'))
    assert not [x for x in morse['standard_english_alphabet_exactly_two_letter_splits'] if x['morse_split']=='rt'][0]['cv_y_dual_all_legal']
    assert all(loc[k]['per_segment']==[1,1,1] for k in ['mupo','cafe'])
    put('phase_repeat_analysis.json',{'primary_within_word_null':null,'secondary_within_segment_null':n2,'eight_phase_triple_repeat_null':phase8,'march_known_key_positive_control':positive,
           'phase2_repeat_locations':loc, 'source_reading_basis':'CC BY 4.0 Brice Dudout / Claude transcription, not text recertified from JACAR official PDF',
           'validation':'No candidate Chinese plaintext, no numeric substitution key recovered.'})
    put('morse_branch.json',morse)
    put('wordcount_length_qa.json',counts)
    put('sensitivity_cases.json',sense)
    print('TARGET: 1917 June confirmed Chinese plaintext 0 characters; ciphertext not decrypted.')
    print('Eight-phase adjusted triple motif test:',phase8['observed_max_triple_distinct_and_cross_pairs'],'best',phase8['best_phase_offsets_0509_0511a_0511b'],'p+',phase8['p_plus1_lexicographic'])
    print('March positive known-key control:',positive['cross_segment_repeated_codes_observed'],'cross repeats; p+',positive['p_plus1'],'hits',positive['ge'],'/',positive['n'])
    print('June, 0509/a phase0, 0511b phase0:',null['observed_b_phase0'])
    print('June, 0509/a phase0, 0511b phase2:',null['observed_b_phase2'])
    print('within-word null p+ optimizing phase0/2:',null['p_plus1_corrected'],'exceed counts',null['ge_in_n'])
    print('whole-sheet pair-shuffle null p+: ',n2['p_plus1_corrected'])
    print('new matched motifs: ',[(k,x['per_segment']) for k,x in loc.items()])
    print('International Morse Ä two-letter splits:',[(x['morse_split'],x['cv_y_dual_all_legal']) for x in morse['standard_english_alphabet_exactly_two_letter_splits']])
    print('Sheet lengths, total:',counts['0511_sheet_a']['chars'],counts['0511_sheet_b']['chars'],counts['0511_full']['chars'])
    print('Hypothetical deletion both odd-tail e vs unchanged cross-repeat:',sense['remove_terminal_e_from_both_odd_length_words']['b_phase2']['cross_segment_repeat_pairs'],sense['independent_witness_as_is']['b_phase2']['cross_segment_repeat_pairs'])

if __name__=='__main__':main()
