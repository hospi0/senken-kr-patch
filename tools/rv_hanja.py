# -*- coding: utf-8 -*-
"""한자어 읽기 대조 — 원문 한자 낱말(2자↑, 3회↑)의 한국 한자음이 과반 줄에 나오는데 일부 줄만 다르면 목록"""
import os, sys, re, json, collections, itertools
sys.path.insert(0, 'C:/Users/kbwor/AppData/Local/Temp/hj/x')
from hanja.table import hanja_table as HT
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
g = json.load(open(R + '/work/review/' + os.environ.get('RV', 'raw.json'), encoding='utf-8'))
SIM = dict(zip('霊剣児龍竜両仏体円国学実寿転辺駅医厳広弾担断対帯従徳悪戦択拝拠挙昼暁権栄楽横検様桜欧残毎気沢浅浄温湿満滝発県真砕礼称穀続総縁縄繊缶継肃脳蔵虫蛍蛮蜂覚触証訳誉読変豊売賊軽辞遅鉄銭鋳錬鎮関随隠険雑霊静顔駆験髄髪鶏麦黄黒点党斉歯亀恵欠歓歩', '靈劍兒龍龍兩佛體圓國學實壽轉邊驛醫嚴廣彈擔斷對帶從德惡戰擇拜據擧晝曉權榮樂橫檢樣櫻歐殘每氣澤淺淨溫濕滿瀧發縣眞碎禮稱穀續總緣繩纖罐繼肅腦藏蟲螢蠻蜂覺觸證譯譽讀變豐賣賊輕辭遲鐵錢鑄鍊鎭關隨隱險雜靈靜顔驅驗髓髮鷄麥黃黑點黨齊齒龜惠缺歡步'))
def rd(c): return HT.get(c) or HT.get(SIM.get(c, ''), '')
DU = {'녀': '여', '뇨': '요', '뉴': '유', '니': '이', '랴': '야', '려': '여', '례': '예', '료': '요', '류': '유', '리': '이', '라': '나', '래': '내', '로': '노', '뢰': '뇌', '루': '누', '르': '느', '령': '영', '련': '연', '렬': '열', '력': '역', '림': '임', '룡': '용', '륙': '육', '률': '율', '립': '입', '량': '양', '랑': '낭', '란': '난', '락': '낙', '론': '논', '록': '녹', '롱': '농', '릉': '능', '름': '늠'}
def reads(w):
    r = [rd(c) for c in w]
    if not all(r): return None
    s = ''.join(r); out = {s}
    if s[0] in DU: out.add(DU[s[0]] + s[1:])
    t = s
    for a, b in DU.items(): out.add(t.replace(a, b)) if False else None
    return out
occ = collections.defaultdict(list)
for k, v in g.items():
    if k[0] != 'T': continue
    j = re.sub(r'^\[[^\]]*\]', '', v[3]); j = re.sub(r'（[^）]*）', '', re.sub(r'（[ァ-ヶー／　]*）', '', j)).replace('／', '').replace('　', '')
    for m in re.finditer(r'[一-龥々]{2,}', j):
        w = m.group()
        for n in range(2, min(5, len(w)) + 1):
            for i in range(len(w) - n + 1): occ[w[i:i + n]].append(k)
rep = []
for w, ks in occ.items():
    ks = list(dict.fromkeys(ks))
    if len(ks) < 3: continue
    rs = reads(w)
    if not rs: continue
    hit = [k for k in ks if any(r in g[k][4].replace('／', '').replace(' ', '') for r in rs)]
    miss = [k for k in ks if k not in hit]
    if miss and len(hit) / len(ks) >= 0.5 and len(hit) >= 2: rep.append((w, rs, len(hit), miss))
rep.sort(key=lambda x: -x[2])
for w, rs, h, miss in rep:
    print('%s(%s) %d/%d :' % (w, '|'.join(rs), h, h + len(miss)), ' '.join(miss[:6]))
