"""Positive control: real 1916 telegram codes (Dudout Y0/G0 channels) re-enciphered with a random table of a chosen model."""
import sys, json, random
sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
from mkjob import write_job
W = __import__('os').environ.get('WENMI_SOLVER', 'wenmi/solver')
def y0():
    C = 'bdfghklmnprstvwxz'
    return {c + v: 6 * i + r for i, c in enumerate(C) for r, v in enumerate('yuoiea' if i % 2 == 0 else 'aeiouy')}
def g0():
    C, V = 'hgfdcbzyxwvtsrqpnmlk', 'aeiou'
    return {c + v: 10 * (i // 2) + (j if i % 2 == 0 else 9 - j) for i, c in enumerate(C) for j, v in enumerate(V)}
def real_codes():
    out = []
    for fn, T in (('yunnan_v3.json', y0()), ('cen_v8.json', g0())):
        msgs = json.load(open('%s/data/%s' % (W, fn), encoding='utf-8'))['messages']
        for name, u in msgs.items():
            cs = []
            for i in range(0, len(u) - 1, 2):
                a, b = u[i], u[i + 1]
                if a in T and b in T and T[a] < 100 and T[b] < 100: cs.append(T[a] * 100 + T[b])
            out.append((name, cs))
    return out
CONS19 = list('bcdfghjklmnprstvxyz'); V6 = list('aeiouy')
def rand_table(model, rng, cons=CONS19):
    cells = [c + v for c in cons for v in V6]
    if model == 'free':
        vals = list(range(100)); rng.shuffle(vals); cs = cells[:]; rng.shuffle(cs)
        T = {}
        for i, cell in enumerate(cs[:100]): T[cell] = vals[i]
        return T
    if model == 'lin':
        co = cons[:]; rng.shuffle(co); vo = V6[:]; rng.shuffle(vo); off = rng.randrange(100); serp = rng.random() < .5
        T = {}
        for p, c in enumerate(co):
            for r, v in enumerate(vo):
                rr = (5 - r) if (serp and p % 2) else r
                cell = 6 * p + rr
                if cell < 100: T[c + v] = (cell + off) % 100
        return T
    if model == 'lin5y':
        cons20 = list('bcdfghjklmnpqrstvxyz')
        co = cons20[:]; rng.shuffle(co); vo = list('aeiou'); rng.shuffle(vo); off = rng.randrange(100); serp = rng.random() < .5
        alias = rng.choice('aeiou')
        T = {}
        for p_, c in enumerate(co):
            for r, v in enumerate(vo):
                rr = (4 - r) if (serp and p_ % 2) else r
                T[c + v] = (5 * p_ + rr + off) % 100
                if v == alias: T[c + 'y'] = (5 * p_ + rr + off) % 100
        return T
    if model == 'coord2':
        cons20 = list('bcdfghjklmnpqrstvxyz'); rng.shuffle(cons20)
        u = list(range(10)); rng.shuffle(u)
        U0 = u[:6]; U1 = u[6:] + [rng.choice(U0), rng.choice(U0)]; rng.shuffle(U1)
        T = {}
        for p_, c in enumerate(cons20):
            for vi, v in enumerate(V6):
                T[c + v] = 10 * (p_ // 2) + (U0 if p_ % 2 == 0 else U1)[vi]
        return T
    if model == 'coord':
        co = cons[:]; rng.shuffle(co); T = {}
        # two consonants per tens digit (first 20 consonants), 6 vowels, units = random injective over 12 cells -> 10 used
        for d in range(10):
            pair = co[2 * d:2 * d + 2]
            cells_d = [c + v for c in pair for v in V6]; rng.shuffle(cells_d)
            for u, cell in enumerate(cells_d[:10]): T[cell] = 10 * d + u
        return T
ARR = None; ADD2 = 0
def transform_inv(c):
    # find (va, vb) such that solver's codeval(va, vb) == c, for given ARR / ADD2
    import itertools
    for va in range(100):
        for vb0 in range(100):
            vb = (vb0 + ADD2) % 100
            d = [va // 10, va % 10, vb // 10, vb % 10]
            if d[ARR[0]] * 1000 + d[ARR[1]] * 100 + d[ARR[2]] * 10 + d[ARR[3]] == c: return va, vb0
def encipher(codes, T, rng, noise=0.0):
    inv = {}
    for cell, v in T.items(): inv.setdefault(v, []).append(cell)
    out = []
    for c in codes:
        pair = (c // 100, c % 100) if ARR is None else transform_inv(c)
        for v in pair:
            s = rng.choice(inv[v]) if v in inv else '--'
            if noise and rng.random() < noise: s = rng.choice(list(T))
            out.append(s)
    return out
if __name__ == '__main__':
    model, seed, noise, path = sys.argv[1], int(sys.argv[2]), float(sys.argv[3]), sys.argv[4]
    rng = random.Random(seed)
    import os
    if os.environ.get('CTL_ARR'): ARR = [int(x) - 1 for x in os.environ['CTL_ARR']]; ADD2 = int(os.environ.get('CTL_ADD2', '0'))
    rc = real_codes(); rng.shuffle(rc)
    # take messages until ~90 codes, split as 20 / 43 / 27 like June
    allc = []
    for n, cs in rc:
        allc += cs
        if len(allc) >= 90: break
    allc = allc[:90]
    if model == 'lin2':
        TA = rand_table('lin', rng); TB = rand_table('lin', rng)
        sa = encipher(allc, TA, rng, noise); sb = encipher(allc, TB, rng, noise)
        syl = [sa[i] if i % 2 == 0 else sb[i] for i in range(len(sa))]; T = {'A': TA, 'B': TB}
    else:
        T = rand_table(model, rng)
        syl = encipher(allc, T, rng, noise)
    msgs = {'c1': syl[:40], 'c2': syl[40:126], 'c3': syl[126:180]}
    write_job(path, msgs, sys.argv[5] if len(sys.argv) > 5 else model, [a.replace("_", " ") for a in sys.argv[6:]])
    json.dump({'codes': allc, 'table': T}, open(path + '.truth.json', 'w'))
