# -*- coding: utf-8 -*-
"""붙여 쓴 띄어쓰기 후보(Kiwi, 조사·어미 바로 뒤 체언·용언) — kiwi-venv 로 실행"""
import os, sys, re, json
sys.stdout.reconfigure(encoding='utf-8')
from kiwipiepy import Kiwi
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); g = json.load(open(R + '/work/review/fixed.json', encoding='utf-8')); kw = Kiwi()
for k in g:
    if k[0] in 'NW':
        for w in re.findall('[가-힣]{2,}', g[k][4]): kw.add_user_word(w, 'NNP', 0)
for w in '영아 소요 월여 수월궁 여와 묘강 흑수진 촉산 여항 선령도'.split(): kw.add_user_word(w, 'NNP', 0)
n = 0
for k, v in g.items():
    if k[0] != 'T': continue
    for seg in re.split(r'[／\s.,!?“”「」~$\d:;()]+', re.sub(r'^\[[^\]]*\]', '', v[4])):
        if len(seg) < 4: continue
        ts = kw.tokenize(seg)
        for a, b in zip(ts, ts[1:]):
            if (a.tag.startswith('JK') or a.tag in ('EC', 'ETM', 'JX')) and (b.tag in ('NNG', 'NP', 'MAG', 'MM') or (b.tag in ('VV', 'VA') and len(b.form) > 1)) and a.start + a.len == b.start and b.len > 1:
                if a.tag in ('EC',) and a.form in ('어', '아'): continue
                print(k, seg, '|', a.form + '+' + b.form); n += 1; break
print(n)
