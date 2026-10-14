import sys, random
src, dst, seed = sys.argv[1], sys.argv[2], int(sys.argv[3])
rng = random.Random(seed); out = []
for line in open(src):
    if line.startswith('MSG'):
        parts = line.split(); name, us = parts[1], parts[2:]
        idx = [i for i, u in enumerate(us) if u != '--']; vals = [us[i] for i in idx]; rng.shuffle(vals)
        for i, v in zip(idx, vals): us[i] = v
        out.append('MSG %s %s\n' % (name, ' '.join(us)))
    else: out.append(line)
open(dst, 'w').writelines(out)
