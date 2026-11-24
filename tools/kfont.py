# -*- coding: utf-8 -*-
r"""글꼴 — JM.FNT(16×16, 34 B 칸)의 가나·한자 칸을 한글(Galmuri14)로 덮기 · ASCFONT 부호·숫자 새로 그리기 (2026-11-24)
  칸 코드·순서는 그대로, 그림만 바꾼다(글자 찾기 코드는 안 고침).  음절→칸 배정은 data/charmap.json 에 고정(덧붙이기만).
  python tools/kfont.py → work/check/한글글꼴_표.png"""
import os, sys, json, struct
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from bdf import Font
R = os.path.dirname(HERE)
G14 = Font(r'C:/claude/utils/font/Galmuri-v2.40.3/Galmuri14.bdf')
G11 = Font(r'C:/claude/utils/font/Galmuri-v2.40.3/Galmuri11.bdf')    # 반각 숫자(Galmuri14 의 4 는 9px 라 칸 초과)
TOP = 3                                                     # Galmuri14 위 여백 — 한글 잉크가 1‥14 줄에 오게 당김
CMAP = os.path.join(R, 'data', 'charmap.json')

def fnt(): return open(R + '/work/disc1/JM.FNT', 'rb').read()
def codes(f=None):
    f = f or fnt(); return [struct.unpack_from('>H', f, i)[0] for i in range(0, len(f), 34)]
def sjis(j):
    h, l = j >> 8, j & 0xFF
    h2 = (h - 0x21) // 2 + 0x81; h2 += 0x40 if h2 > 0x9F else 0
    l2 = l + 0x7E if h % 2 == 0 else l + 0x1F + (1 if l >= 0x60 else 0)
    return bytes((h2, l2))
def slots():
    """덮어쓸 칸: 가나(0x24xx~)·한자 전부. 끝 바이트 0x7F(게임이 0x9F 를 잘못 푸는 칸)는 뺌 → [(칸, SJIS)]"""
    return [(i, sjis(c)) for i, c in enumerate(codes()) if c >= 0x2422 and (c & 0xFF) != 0x7F]
KEEP = {sjis(c): i for i, c in enumerate(codes()) if c < 0x2400 and (c & 0xFF) != 0x7F}   # 부호·전각 영숫자 = 그대로

def load():
    return json.load(open(CMAP, encoding='utf-8')) if os.path.exists(CMAP) else {}
def assign(chars, save=True):
    """음절 집합 → {글자: 칸 순번}. 이미 배정된 것은 안 움직임."""
    m = load(); S = slots(); nxt = len(m)
    for ch in sorted(set(chars) - set(m)):
        assert nxt < len(S), ('글꼴 칸 부족', len(S)); m[ch] = nxt; nxt += 1
    if save: json.dump(m, open(CMAP, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    return m
def ink(ch):
    g = G14.g.get(ord(ch)); assert g, ('Galmuri14 에 없는 글자', ch)
    pts, _ = G14.draw(ch); return [(x, y - TOP) for x, y in pts]
def glyph16(ch):
    rows = [0] * 16
    for x, y in ink(ch):
        x += 1 if '가' <= ch <= '힣' else 0
        assert 0 <= x < 16 and 0 <= y < 16, ('칸 밖', ch, x, y); rows[y] |= 0x8000 >> x
    return struct.pack('>16H', *rows)
def build_fnt(m):
    f = bytearray(fnt()); S = slots()
    for ch, k in m.items():
        i = S[k][0]; f[34 * i + 2:34 * i + 34] = glyph16(ch)
    return bytes(f)
ASC = '!?,.\':;-+/0123456789'                                 # 획 1px 로 다시 그릴 반각(영문 RAM·L·R 은 원본 그대로)
def build_asc():
    a = bytearray(open(R + '/work/disc1/ASCFONT.15', 'rb').read()); keep = bytes(a[0x80:0x82])
    for ch in ASC:
        pts = ink(ch) if not ch.isdigit() else [(x, y) for x, y in G11.draw(ch)[0]]
        if ch.isdigit(): low = max(y for x, y in pts); pts = [(x, y + 13 - low) for x, y in pts]
        xs = [x for x, y in pts]; w = max(xs) - min(xs) + 1
        assert w <= 8, (ch, w)
        ox = (1 if ch in ',.' else (8 - w) // 2) - min(xs); rows = [0] * 15
        dy = max(0, max(y for x, y in pts) - 14)
        for x, y in pts:
            y -= dy
            assert 0 <= y < 15, (ch, y); rows[y] |= 0x80 >> (x + ox)
        a[ord(ch) * 15:ord(ch) * 15 + 15] = bytes(rows)
    a[0x7F * 15:0x80 * 15] = bytes(15)                      # 낱말표 안쪽 공백 대신 쓰는 빈 글자
    assert bytes(a[0x80:0x82]) == keep                      # 게임이 «이미 올렸나» 검사하는 값
    return bytes(a)

if __name__ == '__main__':
    from PIL import Image
    sys.stdout.reconfigure(encoding='utf-8')
    print('덮을 칸', len(slots()), '부호 칸', len(KEEP), '배정', len(load()))
    t = '이소요! 맞고 싶은 게냐? 12,345원/뷁쌍꽃월쫓'; a = build_asc(); W = Image.new('L', (400, 20))
    x = 0
    for ch in t:
        if ord(ch) < 128:
            for y in range(15):
                for k in range(8):
                    if a[ord(ch) * 15 + y] >> (7 - k) & 1: W.putpixel((x + k, y + 2), 255)
            x += 8
        else:
            g = struct.unpack('>16H', glyph16(ch))
            for y in range(16):
                for k in range(16):
                    if g[y] >> (15 - k) & 1: W.putpixel((x + k, y + 2), 255)
            x += 16
    W.resize((1600, 80), 0).save(R + '/work/check/한글글꼴_표.png')
