# -*- coding: utf-8 -*-
"""용어 대조 — 원문에 낱말표(W)·화자(N) 이름이 있으면 번역에 그 한글이 있나. 없으면 줄 목록 → work/review/terms.tsv"""
import os, sys, re, json, collections
sys.stdout.reconfigure(encoding='utf-8')
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
F = sys.argv[1] if len(sys.argv) > 1 else 'raw.json'
g = json.load(open(R + '/work/review/' + F, encoding='utf-8'))
T = {}
for k, (kind, pos, bud, jp, ko) in g.items():
    if k[0] == 'W' and kind != '메뉴' and len(jp) >= 2: T.setdefault(re.sub(r'１$|1$', '', jp), re.sub(r'１$|1$', '', ko).strip())
    if k[0] == 'N': T.setdefault(re.sub(r'（[^）]*）', '', jp), re.sub(r'\([^)]*\)', '', ko).strip())
names = sorted(T, key=len, reverse=True)
sp = lambda s: re.sub(r'[ ／]', '', s)
out = collections.OrderedDict()
for k, (kind, pos, bud, jp, ko) in g.items():
    if k[0] != 'T': continue
    j = re.sub(r'^\[[^\]]*\]', '', jp).replace('／', ''); o = sp(re.sub(r'^\[[^\]]*\]', '', ko)); j = re.sub(r'（[ァ-ヶー]+）', '', j).replace('　', '')
    used = j
    for n in names:
        if n in used:
            used = used.replace(n, '□')
            if sp(T[n]) not in o: out.setdefault(n, []).append((k, jp, ko))
tot = 0
with open(R + '/work/review/terms.tsv', 'w', encoding='utf-8') as f:
    for n in out:
        for k, jp, ko in out[n]: f.write('%s\t%s\t%s\t%s\t%s\n' % (n, T[n], k, jp, ko)); tot += 1
print('어긋난 용어', len(out), '줄', tot)
for n, v in sorted(out.items(), key=lambda x: -len(x[1])): print('%s=%s:%d' % (n, T[n], len(v)), end='  ')
