# -*- coding: utf-8 -*-
"""받은 번역(work/review/in) 형식 대조 → work/review/raw.json {id: [종류, 위치, 예산, JP, KO]}"""
import os, sys, re, json, glob
sys.stdout.reconfigure(encoding='utf-8')
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def rows(fs):
    for f in fs:
        for n, ln in enumerate(open(f, encoding='utf-8-sig').read().replace('\r', '').split('\n')):
            if ln: yield os.path.basename(f), n + 1, ln.split('\t')
src = {c[0]: c for f, n, c in rows(sorted(glob.glob(R + '/my files/tsv/*.tsv'))) if re.fullmatch(r'[A-Z]\d+', c[0])}
got = {}; prob = []
for f, n, c in rows(sorted(glob.glob(R + '/work/review/in/*.tsv'))):
    if c[0] == 'id': continue
    if not re.fullmatch(r'[A-Z]\d+', c[0]): prob.append((f, n, '이상한 행', c)); continue
    if len(c) != 6: prob.append((f, n, '열 %d' % len(c), c))
    if c[0] in got: prob.append((f, n, 'id 중복', c))
    if c[0] not in src: prob.append((f, n, '없는 id', c)); continue
    s = src[c[0]]
    if c[1:5] != s[1:5]: prob.append((f, n, '원문 칸 다름', [(a, b) for a, b in zip(c[1:5], s[1:5]) if a != b]))
    got[c[0]] = s[1:5] + [c[5] if len(c) > 5 else '']
miss = [k for k in src if k not in got]; blank = [k for k in got if not got[k][4].strip()]
print('원본', len(src), '받음', len(got), '빠짐', len(miss), miss[:20], '빈칸', len(blank), blank[:20], '형식 문제', len(prob))
for p in prob[:40]: print(p)
same = [k for k in got if got[k][3] == got[k][4]]; print('원문 그대로', len(same), same[:20])
jpch = [(k, got[k][4]) for k in got if re.search('[ぁ-んァ-ヺ一-龥々]', got[k][4])]; print('일본어·한자 남음', len(jpch)); [print('  ', x) for x in jpch[:60]]
json.dump(got, open(R + '/work/review/raw.json', 'w', encoding='utf-8'), ensure_ascii=False)
