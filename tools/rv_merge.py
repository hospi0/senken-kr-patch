# -*- coding: utf-8 -*-
"""fixed.json → data/tr/*.tsv (원본 TSV 의 줄·원문 칸 그대로, KO 만 채움). python -X utf8 tools/rv_merge.py"""
import os, json, glob, re
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); g = json.load(open(R + '/work/review/fixed.json', encoding='utf-8'))
os.makedirs(R + '/data/tr', exist_ok=True); n = 0
for f in sorted(glob.glob(R + '/my files/tsv/*.tsv')):
    out = []
    for ln in open(f, encoding='utf-8').read().split('\n'):
        c = ln.split('\t')
        if re.fullmatch(r'[A-Z]\d+', c[0]): ln = '\t'.join(c[:5] + [g[c[0]][4]]); n += 1
        out.append(ln)
    open(R + '/data/tr/' + os.path.basename(f), 'w', encoding='utf-8', newline='\n').write('\n'.join(out))
print('병합', n)
