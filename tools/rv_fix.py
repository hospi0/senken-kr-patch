# -*- coding: utf-8 -*-
r"""하스피 번역 검수 수정 (2026-11-24) — work/review/raw.json → fixed.json, 바뀐 줄 전부 changes.tsv(id·사유·전·후)
  순서: 손 수정(MANUAL) → 부호·찌꺼기 정리 → ／ 낱말 가운데 잘림 붙이기 → 용어(원문 조건 + 받침 조사) → 이름표·낱말표
  python -X utf8 tools/rv_fix.py"""
import os, sys, re, json
HERE = os.path.dirname(os.path.abspath(__file__)); R = os.path.dirname(HERE)
g = json.load(open(R + '/work/review/raw.json', encoding='utf-8'))
log = []
def setko(k, new, why):
    if g[k][4] != new: log.append((k, why, g[k][4], new)); g[k][4] = new

# ── 이름표(N) ── 대사 본문에서 다수로 쓴 표기에 맞춤(이름표는 라벨로 그대로 나온다)
N = {
    'N003': '조영아', 'N004': '묘족 두목', 'N005': '묘족 두목', 'N006': '묘족 부하', 'N040': '조영아, 고개 숙여 노래', 'N011': '주아',
    'N020': '방 선주', 'N021': '방 선주', 'N041': '유모', 'N073': '대장간 주인', 'N078': '화아', 'N102': '장 노인', 'N103': '옥아', 'N107': '구아',
    'N117': '묘족', 'N139': '포졸', 'N146': '하녀', 'N164': '주인', 'N174': '기녀', 'N177': '뚱뚱한 기녀', 'N179': '늙은 기녀', 'N190': '묘족 여자',
    'N192': '채아', 'N198': '하녀 향', 'N199': '하녀 훈', 'N200': '경비병', 'N201': '경비병 덕', 'N202': '경비병 방', 'N203': '경비병 곤', 'N204': '경비병 휘',
    'N217': '술꾼 검사', 'N245': '청아', 'N246': '술꾼 검사(쓴웃음)', 'N258': '아노', 'N259': '노파', 'N260': '도아', 'N270': '묘족 여자', 'N299': '묘족 여인',
    'N308': '선주', 'N311': '대장장이', 'N318': '장관 부인', 'N144': '“밖에서 외침이 들린다',
}
# ── 낱말표(W) ──
WD = {'W036': '조영아', 'W038': '아노', 'W125': '제호향', 'W551': '시독'}

# ── 손 수정(대사) ── 파일 tools/rv_manual.tsv (id \t 새 KO)
MAN = {}
p = os.path.join(HERE, 'rv_manual.tsv')
if os.path.exists(p):
    for ln in open(p, encoding='utf-8'):
        c = ln.rstrip('\n').split('\t')
        if len(c) >= 2 and re.fullmatch(r'[A-Z]\d+', c[0]): assert c[0] in g, c[0]; MAN[c[0]] = c[1]

# ── 용어(원문 정규식, 번역 속 잘못된 표기 정규식, 바른 표기[, 화자]) ──
H = r'(?<![가-힣])'
TERMS = [
    ('霊児', H + r'조령아', '조영아'), ('霊児', H + r'령아', '영아'),
    ('お鈴', H + r'(?:오린|아령)(?=아(?:[!?…., ]|$))', '아노'), ('お鈴', H + r'(?:오린|아령)', '아노'),
    ('お彩', H + r'오채(?= 씨)', '채아'), ('お彩', H + r'채(?=(?:는|가|를|의|와|도|야|에게|랑)(?![가-힣])|[…!.,?]| 부인| 씨)', '채아'),
    ('来福', H + r'내복', '래복'),
    ('李女将', H + r'이 (?:여주인|안주인)', '이씨 여주인'), ('女将', H + r'안주인님', '여주인'), ('女将', H + r'안주인', '여주인'),
    ('苗人', H + r'묘족인', '묘족'), ('苗人', H + r'묘인', '묘족'),
    ('剣の聖人', H + r'검의 성인', '검성'), ('剣聖人', H + r'검성인', '검성'),
    ('酒飲み剣士', H + r'술꾼 검객', '술꾼 검사'),
    ('ばあや', H + r'할멈', '유모'),
    ('女飛賊', H + r'(?:여자 도적|여도둑)', '여도적'),
    ('石長老', H + r'석장로', '석 장로'), ('劉夫人', H + r'유부인', '유 부인'), ('宋さん', H + r'송씨', '송 씨'), ('鶯夫人', H + r'앵부인', '앵 부인'), ('木道人', H + r'목도인', '목 도인'),
    ('伯母|叔母', H + r'숙모', '백모'),
    ('林さん', H + r'임 소저', '임 낭자'),
    ('逍遥さん', H + r'소요 씨', '소요 오빠'), ('逍遥さん', H + r'소요 ?님', '소요 오빠'),
    ('李さん', H + r'이 씨', '이 공자'), ('盗侠', H + r'도둑 협객', '도협'),
    ('巡査', H + r'(?:순경|순찰관)', '포졸'), ('守衛', H + r'수비병', '경비병'),
    ('符紙', H + r'(?:부적 종이|부지)', '부적지'),
    ('魂甦り|魂よみが', H + r'혼 되살리기 술', '혼소생술'),
    ('天破り', H + r'천파의 쇠망치', '천파 쇠망치'), ('布靴', H + r'천 신발', '베신'),
    ('毒糸', H + r'붉은독', '붉은 독'), ('赤の毒', H + r'붉은독', '붉은 독'),
    ('紫金のひょうたん', H + r'자금 표주박', '자금 호리병'), ('ひょうたん', H + r'표주박', '호리병'),
    ('懐内', H + r'품속 (?:칼|검)', '품속의 검'),
    ('風呂敷包み', H + r'보따리', '보자기 꾸러미'), ('^布包み', H + r'보자기 꾸러미', '보따리'),
    ('毒龍', H + r'독룡의 쓸개', '독룡 쓸개'), ('天仙の露', H + r'천선의 이슬', '천선 이슬'), ('雪蓮の種', H + r'설련의 씨앗', '설련 씨앗'), ('霊葫の仙丹', H + r'영호의 선단', '영호 선단'),
    ('天香続命の露', H + r'천향속명의 이슬', '천향속명로'), ('鳳凰の卵', H + r'봉황의 알', '봉황 알'), ('麒麟の角', r'기린의 뿔', '기린 뿔'),
    ('木刀', H + r'목도', '목검'), ('長鞭', H + r'장편', '긴 채찍'), ('九節鞭', H + r'구절편', '구절 채찍'), ('黄金蛇の鞭', H + r'황금사편', '황금뱀 채찍'), ('青りぼん', H + r'푸른 리본', '파란 리본'),
    ('天師の帽', H + r'천사의 모자', '천사 모자'), ('鳳凰の羽', H + r'봉황의 깃털', '봉황 깃털'), ('夜行衣', H + r'야행복', '야행의'), ('鉄鱗の鎧', H + r'철린 갑옷', '철비늘 갑옷'),
    ('金糸の衣', H + r'금사의', '금실 옷'), ('蓮花靴', H + r'연화화', '연꽃 신'), ('龍鱗の靴', H + r'용린화', '용비늘 신'), ('鉄腕当て', H + r'철 팔 보호대', '철제 팔보호대'),
    ('経数珠', H + r'염주', '경 염주'), ('豹牙', H + r'표아 팔찌', '표범이빨 팔찌'), ('煮込みたまご', H + r'조림 달걀', '달걀 조림'), ('女王蜂の蜜', H + r'여왕벌의 꿀', '여왕벌 꿀'),
    ('銅貨投げ', H + r'동전 표창', '동전 던지기'), ('梅花.*手裏剣', H + r'매화 수리검', '매화 표창'), ('鈴鳴りの玉', H + r'방울 구슬', '방울소리 구슬'), ('腹蛇', H + r'복사의 침', '살모사의 침'),
    ('しかばね化の水', H + r'시체화 물', '시체화의 물'), ('孔雀の胆', H + r'공작의 쓸개', '공작 쓸개'), ('妖怪食い虫', H + r'요괴 먹는 벌레', '요괴잡이 벌레'),
    ('青血の蚕', H + r'청혈잠', '청혈의 누에'), ('赤血の蚕', H + r'적혈잠', '적혈의 누에'), ('隠し蠱', H + r'은고', '숨은 고'), ('幻の蠱', H + r'환고', '환상의 고'),
    ('魂甦り香', H + r'혼소생향', '반혼향'), ('鼠の実', H + r'쥐열매', '쥐의 열매'), ('紫ケシ', H + r'자양귀비', '자주 양귀비'), ('ダイゴ香', H + r'대고향', '제호향'),
    ('塩漬け肉', H + r'(?:소금에 절인 고기|염장 고기)', '소금절임 고기'), ('北斗の珠', H + r'북두주', '북두 구슬'), ('操り虫', H + r'조종 ?(?:충|벌레)', '조종 벌레'),
    ('飛龍手探り', H + r'비룡 손더듬기 술', '비룡탐수술'), ('手探りの術', H + r'손더듬기 술', '탐수술'), ('泰山の術', H + r'태산의 술', '태산술'), ('越女', H + r'월녀의 검', '월녀검'),
    ('魂買い', H + r'혼 사는 술법', '매혼 술법'), ('鳳縞のハンカチ', H + r'봉황 무늬 손수건', '봉황무늬 손수건'), ('小妖怪', H + r'소요괴', '작은 요괴'),
    ('酔い覚めの歩み', H + r'취기 깨는 걸음', '술 깬 걸음'), ('仙風雲体', H + r'선풍운체의 술법', '선풍운체술'),
    ('巫術', H + r'무술', '주술'), ('巫師', H + r'(?:무사|무당)', '주술사'),
    ('文銭', r'(?<=\d)(?<!문)문(?!전)', '문전'), ('文銭', r'(?<=[０-９])문(?!전)', '문전'), ('文銭', r'(?<=[０-９\d] )문(?!전)', '문전'),
    ('屍の毒', H + r'시체의 독', '시독'),
]
PAIR = [('은', '는'), ('이', '가'), ('을', '를'), ('과', '와'), ('아', '야'), ('으로', '로'), ('이라', '라'), ('이야', '야'), ('이여', '여'), ('이나', '나'), ('이랑', '랑'), ('이란', '란'), ('이다', '다'), ('이군', '군'), ('이지', '지'), ('이구', '구'), ('이었', '였'), ('이에요', '예요')]
def final(ch): return (ord(ch) - 0xAC00) % 28 if '가' <= ch <= '힣' else None
def josa(word, tail):
    """tail 앞머리 조사를 word 받침에 맞춤 (뒤가 낱말 끝일 때만)"""
    f = final(word[-1])
    if f is None: return tail
    for a, b in sorted(PAIR, key=lambda x: -max(len(x[0]), len(x[1]))):
        want = a if f else b
        if a == '으로': want = '으로' if f and f != 8 else '로'
        for o in sorted((a, b), key=len, reverse=True):
            if tail.startswith(o):
                rest = tail[len(o):]
                free = len(o) >= 2 and o not in ('이야',) or re.match(r'(?![가-힣])|(?:서|는|도|만|요|다|면|지|고)(?![가-힣])', rest)
                if o in ('이', '가', '아', '야') and not re.match(r'(?![가-힣])', rest): free = None
                if free is not None and free is not False: return want + rest
    return tail
def sub_term(s, rx, new):
    out = ''; pos = 0
    for m in re.finditer(rx, s):
        if m.start() < pos: continue
        out += s[pos:m.start()] + new; old = m.group(); tail = s[m.end():]
        if final(old[-1]) is not None and bool(final(old[-1])) != bool(final(new[-1])) or (final(old[-1]) == 8) != (final(new[-1]) == 8):
            t2 = josa(new, tail); s = s[:m.end()] + t2
        pos = m.end()
    return out + s[pos:]

# ── ／ 낱말 가운데 잘림 ──
joints = json.load(open(R + '/work/review/joints_raw.json', encoding='utf-8')); JN = {}
NOT = {('적귀왕의', '혈지가'), ('소요', '오빠를'), ('덕을', '이'), ('서대로', '달이라고'), ('생년월일을', '이'), ('피를', '이었어요'), ('조각', '하겠네'), ('에', '요기가'), ('조라는', '뱀'), ('여기', '저기')}
YES0 = {('감동하', '셔서'), ('둔갑', '해'), ('방해', '했소이다'), ('데려가', '셨든'), ('감사', '해야'), ('만들어', '지고'), ('강해', '졌을까'), ('나가', '셨습니다'), ('약속', '해'), ('죄송', '했습니다'), ('정해', '졌습니다'),
        ('전사', '였어'), ('전사하', '셨을'), ('허락', '해'), ('실례', '라고'), ('제주', '였습니다'), ('요괴', '라고'), ('요괴', '라는'), ('지지', '해'), ('접근', '해서는'), ('해결', '해'), ('도와주', '셨나'), ('기억', '해')}
for k, i, pre, x, y, post, sc in joints:
    if (x, y) in NOT: continue
    if sc > 0.2 or (x, y) in YES0: JN.setdefault(k, []).append((x, y))
for k, x, y in (('T00948', '한곳', '에'), ('T04363', '다녀', '와'), ('T02038', '15000', '문')): JN.setdefault(k, []).append((x, y))
JN2 = json.load(open(R + '/work/review/joints2.json', encoding='utf-8')) if os.path.exists(R + '/work/review/joints2.json') else {}

GARB = {'T00897', 'T00898'}                                             # 중국어판 찌꺼기 — 원문 그대로 둠
SKIP = {('T00580', '소요 오빠')}
for k in list(g):
    kind, pos, bud, jp, ko = g[k]
    if k in N: setko(k, N[k], '이름표'); continue
    if k in WD: setko(k, WD[k], '낱말표'); continue
    if k in MAN: setko(k, MAN[k], '손 수정')
    if k in GARB: g[k][4] = ''; continue
    if k[0] != 'T':
        if k[0] == 'W': setko(k, g[k][4].replace('１', '1'), '숫자')
        if k[0] == 'G': setko(k, g[k][4].replace('조령아', '조영아').replace('아령:', '아노:'), '이름')
        continue
    s = g[k][4]
    # 부호·찌꺼기
    t = s.replace('\\"', '"')
    if '"' in t and '"' not in jp:
        n = [0]
        def q(_): n[0] += 1; return '“' if n[0] % 2 else '”'
        t = re.sub('"', q, t)
        if n[0] == 1:                                                        # 여는/닫는 하나뿐 = 원문 쪽을 따름
            t = t.replace('“', '”') if '”' in jp and '“' not in jp else t
    t = re.sub(r'\([一-龥々]+\)', '', t)
    t = re.sub(r'・{2,}\.?', lambda m: '...', t); t = re.sub(r'…{2,}', '......', t); t = re.sub(r'…\.?', '...', t)
    t = t.translate(str.maketrans('、。，．！？：；､｡％＋－', ',.,.!?:;,.%+-'))
    t = re.sub(r'(?<!\.)\.{4,5}(?!\.)', '...', t); t = re.sub(r'\.{7,}', '......', t); t = re.sub(r'(?<!\.)\.\.(?!\.)', '...', t) if '..' in t else t
    t = re.sub(r'(\.\.\.),', r'\1', t)
    t = re.sub(r' *／ *', '／', t) if not re.search(r'／　', t) else t
    t = t.replace('／ ', '／') if '／　' not in t else t
    t = re.sub(r'(?<=[가-힣]) (?=[.,!?])', '', t)
    t = re.sub(r'(?<=[」”.])／(?=(?:으로|로|는|은|을|를|의|라고|라는|에|와|과)(?![가-힣])|라고)', '', t)
    if t != s: setko(k, t, '부호')
    # ／ 가운데 잘림
    s = g[k][4]
    for x, y in JN.get(k, []): s = s.replace(x + '／' + y, x + y)
    for x, y in JN2.get(k, []): s = re.sub(re.escape(x) + '／　+' + re.escape(y), lambda m: '／　' + x + y, s) if False else s
    if s != g[k][4]: setko(k, s, '낱말 가운데 줄바꿈')
    # 용어
    s = g[k][4]; m = re.match(r'\[[^\]]*\]', s); head = m.group() if m else ''; body = s[len(head):]
    j = re.sub(r'^\[[^\]]*\]', '', jp).replace('／', ''); j = re.sub(r'（[ァ-ヶー　]+）', '', j).replace('　', '')
    for rx, bad, new in TERMS:
        if (k, new) in SKIP: continue
        if re.search(rx, j):
            # 용어가 ／ 에 걸친 경우도 본다
            b2 = sub_term(body, bad, new)
            if b2 == body and '／' in body:
                bad2 = bad.replace(' ', '[ ／]')
                b2 = sub_term(body, bad2, new)
            if b2 != body: setko(k, head + b2, '용어 %s' % new); body = b2
json.dump(g, open(R + '/work/review/fixed.json', 'w', encoding='utf-8'), ensure_ascii=False)
with open(R + '/work/review/changes.tsv', 'w', encoding='utf-8') as f:
    for l in log: f.write('\t'.join(l) + '\n')
import collections
c = collections.Counter(l[1] for l in log); print('바뀐 기록', len(log), '줄', len(set(l[0] for l in log))); print(dict(c.most_common()))
