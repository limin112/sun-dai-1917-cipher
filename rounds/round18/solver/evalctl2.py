import sys, json
out, truth = sys.argv[1], json.load(open(sys.argv[2])); codes = truth['codes']
lines = [l for l in open(out).read().split('\n') if l]
for i in range(0, min(len(lines), 2 * int(sys.argv[3])), 2):
    got = [int(x) for x in lines[i + 1].split()[1:]]
    print(lines[i][:160], ' correct %d/%d' % (sum(a == b for a, b in zip(got, codes)), len(codes)))
