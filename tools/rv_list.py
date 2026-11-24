import sys; from rv_tone import *
who, want = sys.argv[1], set(sys.argv[2].split(','))
keys = list(g); last = None
for i, k in enumerate(keys):
    v = g[k]
    if k[0] != 'T': continue
    m = re.match(r'\[([^\]]*)\]', v[3])
    if m: last = m.group(1)
    if (m.group(1) if m else None) != who: continue
    cs = set(cls(s) for s in sents(v[4]))
    if cs & want:
        pv = re.match(r'\[([^\]]*)\]', g[keys[i-1]][4]) if i else None
        print(k, '(앞:%s)' % (pv.group(1) if pv else '-'), re.sub(r'^\[[^\]]*\]|／', lambda x: ' ' if x.group() == '／' else '', v[4])[:150])
