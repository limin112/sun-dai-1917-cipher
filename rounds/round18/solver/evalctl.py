import sys, json
out, truth = sys.argv[1], json.load(open(sys.argv[2]))
codes = truth['codes']
# job codes order: c1 (20 codes), c2 (43), c3 (27)
lines = open(out).read().split('\n')
for i in range(0, min(len(lines) - 1, 3 * int(sys.argv[3]) if len(sys.argv) > 3 else 15), 3):
    head = lines[i]; cs = lines[i + 2].split()[1:]
    got = [int(x) for x in cs]
    ok = sum(1 for a, b in zip(got, codes) if a == b)
    print(head[:120], ' correct %d/%d' % (ok, len(codes)))
