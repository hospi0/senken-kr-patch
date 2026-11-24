import os, sys, re, json, collections
sys.stdout.reconfigure(encoding='utf-8')
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
g = json.load(open(R + '/work/review/raw.json', encoding='utf-8'))
N = {g[k][3]: g[k][4] for k in g if k[0] == 'N'}
c = collections.defaultdict(collections.Counter); nob = 0
for k, (kind, pos, bud, jp, ko) in g.items():
    if k[0] != 'T': continue
    a = re.match(r'\[([^\]]*)\]', jp); b = re.match(r'\[([^\]]*)\]', ko)
    if a and b: c[a.group(1)][b.group(1)] += 1
    elif a: c[a.group(1)]['(없음)'] += 1
    elif b: print('원문에 없는 화자', k, jp[:40], ko[:40])
for n in c:
    v = c[n]
    if len(v) > 1 or (N.get(n) not in v): print('%s [%s] → %s' % (n, N.get(n), ', '.join('%s %d' % x for x in v.most_common())))
