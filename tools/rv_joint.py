# -*- coding: utf-8 -*-
"""／ 이음매 판정: 앞 낱말+뒤 낱말을 붙였을 때 Kiwi 가 안 띄우면 «낱말 가운데 잘림». work/review/joints.json {id: [붙일 ／ 순번]}"""
import os, sys, re, json, collections
sys.stdout.reconfigure(encoding='utf-8')
from kiwipiepy import Kiwi
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
g = json.load(open(R + '/work/review/raw.json', encoding='utf-8'))
kw = Kiwi()
for k in g:
    if k[0] in 'NW':
        for w in re.findall('[가-힣]{2,}', g[k][4]): kw.add_user_word(w, 'NNP', 0)
for w in '영아 아노 오린 소요 월여 수월궁 여와 묘강 흑수진 촉산 여항 선령도 검성 술꾼 소요오빠'.split(): kw.add_user_word(w, 'NNP', 0)
corpus = collections.Counter(w for k, v in g.items() for w in re.findall('[가-힣]+', v[4].replace('／', ' ／ ')))
res = {}; show = []
for k, v in g.items():
    if k[0] not in 'TE': continue
    ps = v[4].split('／')
    for i in range(len(ps) - 1):
        a = re.search(r'[가-힣]+$', ps[i]); b = re.match(r'[가-힣]+', ps[i + 1])
        if not a or not b: continue
        x, y = a.group(), b.group(); j = x + y
        ctx = ps[i].split(' ')[-2:] ; pre = ' '.join(ps[i].split(' ')[-3:-1]); post = ' '.join(ps[i + 1].split(' ')[1:3])
        full = (pre + ' ' + j + ' ' + post).strip()
        sp = kw.space(full, reset_whitespace=False)
        joined = j in sp.split(' ') or any(j in t for t in sp.split())
        if joined:
            # 붙인 것이 옳은지 점수: 형태소 분석 점수 비교
            s1 = kw.analyze((pre + ' ' + j + ' ' + post).strip())[0][1]; s2 = kw.analyze((pre + ' ' + x + ' ' + y + ' ' + post).strip())[0][1]
            show.append((k, i, pre, x, y, post, round(s1 - s2, 1)))
show.sort(key=lambda t: -t[-1])
json.dump(show, open(R + '/work/review/joints_raw.json', 'w', encoding='utf-8'), ensure_ascii=False)
print(len(show)); pos = [t for t in show if t[-1] > 0]; print(len(pos))
print(' '.join('%s|%s(%s)' % (t[3], t[4], t[6]) for t in show))
