"""Control: free table (any syllable->value bijection) + K true anchored syllables. Measures recovery vs anchors."""
import sys, json, random, subprocess, collections
sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
seed, nanch, model = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
job = 'anc_%s_%d_%d.job' % (model, seed, nanch)
subprocess.run(['python3', '-I', __import__('os').path.join(__import__('os').path.dirname(__import__('os').path.abspath(__file__)), 'control.py'), 'free', str(seed), '0.03', job, model, 'CPEN_5'], check=True, stdout=subprocess.DEVNULL)
t = json.load(open(job + '.truth.json')); T = t['table']
msgs = [l.split()[2:] for l in open(job) if l.startswith('MSG')]
cnt = collections.Counter(u for m in msgs for u in m if u != '--')
# anchors: most frequent syllables (a crib on common words fixes common syllables)
anch = [u for u, _ in cnt.most_common() if u in T][:nanch]
with open(job, 'a') as f:
    for u in anch: f.write('ANCHOR %s %d\n' % (u, T[u]))
out = job.replace('.job', '.out')
subprocess.run(['./june_sa', job, out, '12', '1500000', '3', '10'], stderr=subprocess.DEVNULL)
lines = open(out).read().split('\n'); got = [int(x) for x in lines[2].split()[1:]]
print(model, 'seed', seed, 'anchors', nanch, 'score', lines[0].split()[3], 'correct %d/%d' % (sum(a == b for a, b in zip(got, t['codes'])), len(t['codes'])))
