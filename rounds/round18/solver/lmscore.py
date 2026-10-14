import numpy as np, os
LM = __import__('os').environ.get('WENMI_LM', 'lm')
uni = np.fromfile(os.path.join(LM, 'uni.f32'), dtype=np.float32)
REF = float(uni.mean())
BI = dict(zip(np.fromfile(os.path.join(LM, 'bi.u32'), dtype=np.uint32).tolist(), np.fromfile(os.path.join(LM, 'bi.f32'), dtype=np.float32).tolist()))
BDEF = float(np.fromfile(os.path.join(LM, 'bidef.f32'), dtype=np.float32)[0])
CODE2CH = dict(l.rstrip('\n').split('\t') for l in open(os.path.join(LM, 'code2ch.tsv'), encoding='utf-8'))
def score(seqs):
    tot = 0.0; n = 0
    for cs in seqs:
        prev = None
        for c in cs:
            if c is None or c < 0: tot -= 6; prev = None; n += 1; continue
            tot += float(uni[c]) - REF; n += 1
            if prev is not None: tot += BI.get(prev * 10000 + c, BDEF)
            prev = c
    return tot, tot / max(n, 1)
def text(cs): return ''.join(CODE2CH.get('%04d' % c, '□') if c is not None and c >= 0 else '·' for c in cs)
