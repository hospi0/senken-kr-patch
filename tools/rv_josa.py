# -*- coding: utf-8 -*-
r"""조사 받침 전수 검사 (2026-11-24, 하스피 «조사처리는 어때») — 보고만.  kiwi-venv 로: python tools/rv_josa.py [--test]
  어절 끝이 «받침과 안 맞는 조사» 꼴이면, 조사를 뗀 앞부분이 명사(말뭉치에서 Kiwi 가 명사로 푼 낱말·N·W 표·앞부분만 풀어 명사로 끝남)일 때 잡는다.
  --test = 일부러 틀린 문장을 넣어 검출률 확인."""
import glob, os, re, sys
sys.stdout.reconfigure(encoding='utf-8'); R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
from kiwipiepy import Kiwi
kw = Kiwi(); rows = []
for f in sorted(glob.glob(os.path.join(R, 'data', 'tr', '*.tsv'))):
    for l in open(f, encoding='utf-8'):
        c = l.rstrip('\n').split('\t')
        if len(c) > 5 and re.fullmatch(r'[NWTE]\d+', c[0]): rows.append((c[0], c[4], c[5]))
def jong(ch): return (ord(ch) - 0xAC00) % 28 if '가' <= ch <= '힣' else None
Z = {'은': 1, '는': 0, '을': 1, '를': 0, '과': 1, '와': 0, '이': 1, '가': 0, '이랑': 1, '랑': 0, '이나': 1, '나': 0, '이란': 1, '란': 0, '이라는': 1, '라는': 0, '이라고': 1, '라고': 0, '이라면': 1, '라면': 0,
     '이라도': 1, '라도': 0, '이든': 1, '든': 0, '이여': 1, '여': 0, '이야말로': 1, '야말로': 0, '이여서': 1, '이었다': 1, '였다': 0, '이에요': 1, '예요': 0, '이라': 1, '라': 0, '이니': 1, '아': 1, '야': 0, '이며': 1, '이고': 1}
RO = {'으로': 1, '으로는': 1, '으로도': 1, '으로만': 1, '으로서': 1, '으로써': 1, '으로부터': 1, '로': 0, '로는': 0, '로도': 0, '로만': 0, '로서': 0, '로써': 0, '로부터': 0}
def bad(n, j):
    b = jong(n[-1])
    if b is None: return False
    if j in RO: return (b in (0, 8)) if RO[j] else (b not in (0, 8))
    if j in ('이나', '이란', '이라는', '이라고', '이라면', '이라도', '이든', '이며', '이고', '이니', '이라', '이었다', '이여', '이랑', '이에요', '이야말로') and n.endswith('이'): return False
    return bool(b) != bool(Z[j])
def clean(s): return re.sub(r'\[[^\]]*\]', '', re.sub(r'[$~]\d\d', '', s)).replace('"', '')
def texts(k): t = clean(k); return [t.replace('／', ' ')] + ([t.replace('／', '')] if '／' in t and not re.search(r'[가-힣]／[가-힣]', t) else [])
if '--test' in sys.argv:
    W = ['팔를 얻다', '깨달음도복를 획득', '이소요은 간다', '수월궁로 가라', '배월교으로 간다', '검과 칼와 창', '그 사람가 왔다', '돈를 줘', '물과 불를 본다', '영지은 맑다', '요괴이 나왔다', '수월궁라는 곳', '혈지이라는 곳', '술법와 검', '“앵자”이라고 하오', '「귀음산」로 보내라']
    test = [('T9%04d' % i, '', w) for i, w in enumerate(W)]
else: test = []
NOUN = {'NNG', 'NNP', 'NNB', 'NP', 'NR', 'XSN', 'XR'}; voc = set()
for i, j, k in rows:
    if i[0] in 'NW':
        for w in re.findall(r'[가-힣]+', k): voc.add(w)
    for t in texts(k):
        run = ''; end = -1
        for x in kw.tokenize(t):
            s = t[x.start:x.start + x.len]
            if x.tag in NOUN and x.start == end: run += s; voc.add(run); voc.add(s)
            elif x.tag in NOUN: run = s; voc.add(s)
            else: run = ''
            end = x.start + x.len
            # 붙은 조사가 맞는 명사 = 사전(오검출 줄이기용 아님)
JJ = sorted(list(Z) + list(RO), key=len, reverse=True); out = {}
def isnoun(st):
    if st in voc: return True
    T = kw.tokenize(st); return bool(T) and T[-1].tag in NOUN and all(x.tag in NOUN | {'MM', 'XPN', 'SN'} for x in T)
good = {}
for i, j, k in rows + test:
    if i[0] not in 'TE': continue
    for t in texts(k):
        for m in re.finditer(r'([가-힣]+)([”」』’]?)([가-힣]*)', t):
            a, q, b = m.groups()
            if q and b:
                jj = next((x for x in JJ if b == x), None)
                if jj and bad(a, jj): out[(i, m.group(0))] = ('따옴표', k)
                continue
            w = a + b if not q else a
            for jj in JJ:
                st = w[:-len(jj)]
                if not st or not w.endswith(jj): continue
                if bad(st, jj) and isnoun(st): out.setdefault((i, w), (jj, k))
# 원래 낱말(동사·부사 등)로 맞게 풀리는 어절은 뺌: Kiwi 가 어절 전체를 한 덩이(명사 하나·동사+어미·관형사 등)로 풀고 조사로 안 갈랐을 때
skip = {}
for (i, w), (jj, k) in out.items():
    T = kw.tokenize(w); tags = [x.tag for x in T]
    skip[(i, w)] = not i.startswith('T9') and ((len(T) == 1) or any(x.startswith(('E', 'V', 'MAG', 'MAJ', 'IC')) for x in tags) and not any(x in ('JKS', 'JKO', 'JX', 'JC', 'JKB') for x in tags[-1:]))
if '--test' in sys.argv:
    hit = {i for i, w in out}; print('심은 것', len(test), '잡힌 것', len(hit & {x[0] for x in test}), '못 잡음', [x[2] for x in test if x[0] not in hit]); sys.exit()
for flag in (False, True):
    L = [(i, w, v) for (i, w), v in out.items() if skip[(i, w)] == flag]
    print('== ' + ('의심' if not flag else '낱말로 풀림(참고)'), len(L))
    seen = {}
    for i, w, v in L: seen.setdefault((w, v[0]), []).append((i, v[1]))
    for (w, jj), x in sorted(seen.items(), key=lambda z: -len(z[1])): print(w, '[%s]' % jj, len(x), x[0][0], x[0][1][:0 if flag else 70])
