import sys, json, random
sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
from june_data import *
LM = __import__('os').environ.get('WENMI_LM', 'lm')
def june_msgs(k, join='mask'):
    a = syll(T0509[k]); b = syll(T0511A[k]); c = syll(T0511B[k])
    bad = lambda s: [('--' if x.startswith('?') else x) for x in s]
    a, b, c = bad(a), bad(b), bad(c)
    if join == 'mask': return {'m0509': a, 'm0511': b + ['--'] + c}
    if join == 'none': return {'m0509': a, 'm0511': b + c}
    if join == 'dropfirst': return {'m0509': a, 'm0511': b + c[1:]}
def write_job(path, msgs, model, extra=()):
    with open(path, 'w') as f:
        f.write('LM %s\nMODEL %s\n' % (LM, model))
        for e in extra: f.write(e + '\n')
        for n, u in msgs.items(): f.write('MSG %s %s\n' % (n, ' '.join(u)))
if __name__ == '__main__':
    k, join, model, path = sys.argv[1:5]
    write_job(path, june_msgs(k, join), model, sys.argv[5:])
