#!/usr/bin/env python3
"""Compare frozen Sun/Dai June telegram transcriptions with the independent
blind re-reading published by Brice Dudout (CC BY 4.0), WITHOUT decoding words.
All tests are deterministic and require Python 3 stdlib. No amendments to raw.
"""
import json,hashlib,pathlib,collections,difflib,sys
ROOT=pathlib.Path(__file__).resolve().parent
BASE=json.loads((ROOT/'input/ciphertexts.json').read_text(encoding='utf8'))
WIT=json.loads((ROOT/'input/independent_witness.json').read_text(encoding='utf8'))
DAY24='1917-06-24_0509';DAY29='1917-06-29_0511'
V=set('aeiou');C=set('bcdfghjklmnpqrstvwxz'); U=V|C|{'y'}

def legal(a,b):
    return ((a in V or a=='y') and (b in C or b=='y')) or ((b in V or b=='y') and (a in C or a=='y'))

def split_pairs(word, offset=0):
    return [(word[i:i+2],i//2+1) for i in range(offset,len(word)-1,2)]

def eval_pairing(words,mode='per_word',offset=0):
    pairs=[];rests=[]
    if mode=='per_word':
        for wid,word in enumerate(words,1):
            for pair,ix in split_pairs(word):pairs.append({'word':wid,'slot':ix,'symbol':pair,'ok':legal(*pair)})
            if len(word)%2:rests.append({'word':wid,'word_length':len(word),'last_character':word[-1]})
    elif mode=='continuous':
        s=''.join(words)
        if offset:rests.append({'leading_unpaired_characters':s[:offset]})
        for i in range(offset,len(s)-1,2):
            pairs.append({'cross_word_index':i//2+1,'symbol':s[i:i+2],'ok':legal(s[i],s[i+1])})
        if (len(s)-offset)%2:rests.append({'last_character':s[-1]})
    return {'total':len(pairs),'legal':sum(p['ok'] for p in pairs), 'illegal':[p for p in pairs if not p['ok']], 'odd_or_skipped':rests}

def tetragram_run(words,global_offset=0):
    s=''.join(words)
    # non-overlapping 4-letter groups from an explicit even offset
    return [s[i:i+4] for i in range(global_offset,len(s)-3,4)]

def count_patterns(words,phase=0):
    s=''.join(words)
    return collections.Counter(s[i:i+4] for i in range(phase,len(s)-3,2))

def key_g0():
    cons='hgfdcbzyxwvtsrqpnmlk';vows='aeiou'
    return {c+v:10*(i//2)+(j if i%2==0 else 9-j) for i,c in enumerate(cons) for j,v in enumerate(vows)}

def key_y0():
    cons='bdfghklmnprstvwxz'
    return {c+v:6*i+j for i,c in enumerate(cons) for j,v in enumerate('yuoiea' if i%2==0 else 'aeiouy')}

def controls():
    G=key_g0();Y=key_y0()
    assert len(G)==100 and set(G.values())==set(range(100))
    assert len(Y)==102 and len(set(Y.values()))==102
    assert G['fa']==10 and G['zi']==32 and (G['fa']*100+G['zi'])==1032 # 報, published original 1916
    assert Y['bu']==1 and Y['ky']==35 and 100*Y['bu']+Y['ky']==135 # 伸, published 1916
    assert 100*Y['ha']+Y['ry']==2960 # 歌, published 1916
    assert legal('c','e') and legal('y','y') and legal('m','y') and legal('y','a')
    assert not legal('e','e') and not legal('c','d')
    return {'G0_1916_fazi':1032,'Y0_1916_buky':135,'Y0_1916_hary':2960,
            'positive_examples_source':'Brice Dudout, solver/wenmi.py and Chinese method (2026), NOT 1917 June decrypted',
            'negative_dual_pair_ee':False,'positive_dual_pair_ce':True}

def compare_words(older,newer):
    assert len(older)==len(newer)
    return [{'word':i,'old':a,'new':b,'len_old':len(a),'len_new':len(b),
             'opcode_diffs':[list(x) for x in difflib.SequenceMatcher(None,a,b,autojunk=False).get_opcodes() if x[0]!='equal']}
            for i,(a,b) in enumerate(zip(older,newer),1) if a!=b]

def main():
    assert hashlib.sha256((ROOT/'input/ciphertexts.json').read_bytes()).hexdigest()=='620e469ec26d6534df2dbad0553d79844f1d9df8e68e47a95194a1c0563a8136', 'FROZEN INPUT SHA MISMATCH'
    assert BASE['image_verified'] is False
    o={}
    for day in (DAY24,DAY29):
        old=BASE['analysis_variants'][day].split()
        new=WIT['telegrams'][day]['words']
        seg=WIT['telegrams'][day]['segments']
        assert sum(seg)==len(new)
        o[day]={
            'raw_source_unchanged':BASE['raw_june_notes'][day],
            'comparison_against_analysis_variant':compare_words(old,new),
            'previous_analysis_words':len(old),'independent_blind_words':len(new),
            'old_word_lengths':[len(w) for w in old],
            'independent_word_lengths':[len(w) for w in new],
            'length_counts_blind':dict(sorted(collections.Counter(map(len,new)).items())),
            'chars_blind':sum(map(len,new)),
            'previous_eval_all_even_words':eval_pairing([w for w in old if len(w)%2==0]),
            'blind_eval_even_words':eval_pairing([w for w in new if len(w)%2==0]),
            'blind_eval_all_per_word_with_odd_tails':eval_pairing(new),
            'blind_eval_continuous_no_shift':eval_pairing(new,'continuous'),
            'sheet_segments':[]
        }
        start=0
        for j,size in enumerate(seg):
            sheet=new[start:start+size];start+=size
            o[day]['sheet_segments'].append({
                'segment':j+1,'word_count':len(sheet),'char_count':sum(map(len,sheet)),
                'pairs_continuous':eval_pairing(sheet,'continuous'),
                'tetra_phase0_top':collections.Counter(tetragram_run(sheet,0)).most_common(8),
                'tetra_phase2_top':collections.Counter(tetragram_run(sheet,2)).most_common(8),
            })
    # Investigate claimed 4-letter repeats by independent witness, without Chinese:
    w24=WIT['telegrams'][DAY24]['words'];w29=WIT['telegrams'][DAY29]['words']
    pairs24=''.join(w24);pairs29a=''.join(w29[:18]);pairs29b=''.join(w29[18:])
    counts={k:{'0509_any_even_phase':count_patterns(w24,0)[k],
               '0511a_any_even_phase':count_patterns(w29[:18],0)[k],
               '0511b_any_even_phase':count_patterns(w29[18:],0)[k],
               '0511b_any_odd_phase':count_patterns(w29[18:],1)[k],
               '0509_4char_boundaries':collections.Counter(tetragram_run(w24))[k],
               '0511a_4char_boundaries':collections.Counter(tetragram_run(w29[:18]))[k],
               '0511b_4char_boundaries_phase2':collections.Counter(tetragram_run(w29[18:],2))[k]}
        for k in ['cafe','kige','fojy','mafy']}
    o['repeated_four_character_patterns']={'claimed_examples':counts,'measurement_note':'substring positions scanned every two characters; counts do not prove number of repeated Chinese characters or key identity.'}
    # Enumerate repeated tetragram positions on chosen 4-letter character grid.
    # Include word/letter spans so apparent repeats across arbitrary 10-letter groups
    # are not mistaken for a single printed telegram 'word'.
    def locs(words, needle, start_at):
        s=''.join(words)
        boundaries=[];q=0
        for word_i,w in enumerate(words,1):
            boundaries.append((q,q+len(w),word_i));q+=len(w)
        out=[]
        for i in range(start_at,len(s)-3,4):
            if s[i:i+4]!=needle:continue
            hit_words=[z[2] for z in boundaries if z[0]<i+4 and z[1]>i]
            out.append({'character_offset_zero_based':i,'word_numbers':hit_words,'crosses_telegram_group_boundary':len(hit_words)>1})
        return out
    o['phase_aware_tetragram_locations']={
        k:{'0509_phase0':locs(w24,k,0),
            '0511a_phase0':locs(w29[:18],k,0),
            '0511b_phase2':locs(w29[18:],k,2)}
        for k in ['cafe','kige','fojy','mafy']
    }
    # Competing reading for 0511b word8 explicitly labeled by human scanner:
    alternative_b=list(w29[18:]); assert alternative_b[7]=='fogylisicy'
    alternative_b[7]='fojylisicy'
    o['manual_reading_sensitivity_not_applied']={
        'which':'0511b word 8, blind fogylisicy vs tentative fojylisicy (g vs j), Brice witness note',
        'blind_fojy_boundaries':locs(w29[18:],'fojy',2),
        'tentative_fojy_boundaries':locs(alternative_b,'fojy',2),
        'status':'UNVERIFIED textual alternative, NOT a correction or Chinese plaintext'
    }
    # Versioned, provenance-visible one-word sensitivity checks.
    # All alternatives are unconfirmed and remain OUTSIDE frozen witness strings.
    o['targeted_uncertainty_without_replacing_data']={
        '0511_word7_old_kohokycuee_pairs':eval_pairing(['kohokycuee']),
        '0511_word7_blind_kohokycuce_pairs':eval_pairing(['kohokycuce']),
        '0511_word12_blind_damowmhosy_pairs':eval_pairing(['damowmhosy']),
        '0511_word12_old_damoumhosy_pairs':eval_pairing(['damoumhosy']),
        '0509_word2_blind_vemucicyri_pairs':eval_pairing(['vemucicyri']),
        '0509_word2_morse_alternative_vemucekyri_pairs':eval_pairing(['vemucekyri']),
        'status':'sensitivity examples only; no reading accepted or plaintext generated'
    }
    o['positive_negative_controls']=controls()
    o['hypothesis_scope']='mechanical alphabet pair grammar; not a recovered codebook, key, or translation'
    o['scan_assessment']='published JACAR copies visually inspected in this run via GitHub/Brice Dudout image files; not independently fetched from official JACAR host; independent copy not automatically an archive-verified transcription'
    output=ROOT/'results/structural_reaudit.json';output.parent.mkdir(exist_ok=True)
    output.write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    for day,d in o.items():
        if day not in (DAY24,DAY29):continue
        print(day)
        print('old_lengths',collections.Counter(d['old_word_lengths']),'new_lengths',d['length_counts_blind'])
        print('changed words',len(d['comparison_against_analysis_variant']),[(x['word'],x['old'],x['new']) for x in d['comparison_against_analysis_variant']])
        for key in ['previous_eval_all_even_words','blind_eval_even_words','blind_eval_all_per_word_with_odd_tails','blind_eval_continuous_no_shift']:
            e=d[key];print(key,e['legal'],'/',e['total'],'invalid',e['illegal'][:8], 'odd',e['odd_or_skipped'][:4])
        for x in d['sheet_segments']:
            print('sheet',x['segment'],'words',x['word_count'],'chars',x['char_count'],'pair validity',x['pairs_continuous']['legal'],'/',x['pairs_continuous']['total'])
    print('four-repeat-patterns:',counts)
    print('controls:',o['positive_negative_controls'])
    print('OUTPUT',output)

if __name__=='__main__':main()
