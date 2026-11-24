# -*- coding: utf-8 -*-
"""빌더 부하 시험 — 전 행에 가짜 한글(원문 글자 수 × 배율)을 넣고 검사만.  python tools/test_fake.py [배율] --check"""
import sys, random, re
if '--check' not in sys.argv: sys.argv.append('--check')
import build_text as B
rate = float(sys.argv[1]) if len(sys.argv) > 2 else 0.85
random.seed(1); SY = [chr(0xAC00 + i * 9) for i in range(1200)]; real = B.load_tr
def fake(k, s):
    s2 = re.sub(r'^\[[^\]]*\]', '', s); out = []
    for part in s2.split('／'):
        t = ''
        for tok in re.split(r'([~$]\d\d|[()"]|＊＊)', part):
            if re.fullmatch(r'[~$]\d\d|[()"]|＊＊', tok): t += tok; continue
            n = max(1, int(len(tok) * rate)) if tok.strip() else 0; w = ''
            while n > 0:
                m = max(1, int(min(n, random.randint(1, 4)))); w += ''.join(random.choice(SY) for _ in range(m)); n -= m + 0.5
                if n > 0: w += random.choice([' ', ' ', ' ', ', ', '! '])
            t += w
        out.append(t)
    return '／'.join(out)
def load():
    jp, tr = real(); r = {}
    for k, s in jp.items():
        if k[0] == 'W': r[k] = fake(k, s)[:7].strip()
        elif k[0] == 'N': r[k] = fake(k, s)[:8].strip()
        else: r[k] = fake(k, s)
    return jp, r
B.load_tr = load; B.main()
