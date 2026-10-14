import sys, itertools
sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
from june_data import *
from lmscore import score, text
def streams(k):
    a = syll(T0509[k]); b = syll(T0511A[k]); c = syll(T0511B[k])
    return [a, b + ['--'] + c]
def decode(st, T):
    out = []
    for s in st:
        cs = []
        for i in range(0, len(s) - 1, 2):
            x, y = s[i], s[i + 1]
            if x in T and y in T and T[x] < 100 and T[y] < 100: cs.append(T[x] * 100 + T[y])
            else: cs.append(-1)
        out.append(cs)
    return out
def y0like(C, vord='yuoiea', serp=True, off=0):
    T = {}
    for i, c in enumerate(C):
        vo = vord if (i % 2 == 0 or not serp) else vord[::-1]
        for r, v in enumerate(vo): T[c + v] = 6 * i + r + off
    return T
res = []
for k in 'BD':
    st = streams(k)
    base = 'bcdfghjklmnprstyz'
    for rot in range(17):
        for rev in (0, 1):
            C = base[rot:] + base[:rot]
            if rev: C = C[::-1]
            for vo in itertools.permutations('aeiouy'):
                vo = ''.join(vo)
                for serp in (True, False):
                    T = y0like(C, vo, serp)
                    d = decode(st, T); sc = score(d)
                    res.append((sc[1], k, C, vo, serp, d))
res.sort(key=lambda r: -r[0])
for r in res[:8]: print('%.3f %s %s %s serp=%s  %s | %s' % (r[0], r[1], r[2], r[3], r[4], text(r[5][0]), text(r[5][1])))
print('n', len(res))
