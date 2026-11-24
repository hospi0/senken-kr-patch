# -*- coding: utf-8 -*-
r"""장비 화면(FBP.PX 1·3·4·5, 네 장이 같은 그림) 글자 → 한글 (2026-11-24)
  바탕 = 가로 26 화소 주기 직물 무늬. 글자(색 1) + 둘레 2 화소만 «같은 줄 26×k 옆 화소의 최빈값»으로 되살림 → 한글(Galmuri14, 가로 획 굵힘)을 같은 색 1 로.
  원래 글자 칸 밖 변경 0 검사. --check = 미리보기 work/gfx_preview/장비화면.png 만, --write = work/gfx/FBP.PX@*.bin"""
import os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, HERE)
import fbp, kfont
BOX = [(91, 9, 125, 26), (91, 31, 125, 48), (91, 53, 125, 70), (91, 75, 125, 92), (91, 97, 125, 114), (91, 119, 125, 136),
       (225, 9, 259, 26), (225, 31, 259, 48), (225, 53, 259, 71), (225, 75, 259, 92), (225, 97, 259, 114)]
def words():
    out = {}
    for l in open(os.path.join(ROOT, 'data', 'tr', 'senken_names_words_003.tsv'), encoding='utf-8'):
        c = l.rstrip('\n').split('\t')
        if c[0].startswith('G') and c[0][1:].isdigit(): out[c[0]] = c[-1]
    return out
def blank(a):
    inbox = np.zeros(a.shape, bool)
    for x0, y0, x1, y1 in BOX: inbox[y0:y1, x0:x1] = True
    src = ~inbox; src[:85, :82] = False
    ink = (a == 1) & inbox; near = ink.copy()
    for dy in range(-2, 3):
        for dx in range(-2, 3): near |= np.roll(np.roll(ink, dy, 0), dx, 1)
    near &= inbox; out = a.copy()
    R = (222, 5, 268, 94)                                   # 오른쪽 칸 = 일본판이 力·防御·速さ 를 고치며 남긴 조각까지 무늬로 되살림
    for y in range(R[1], R[3]):
        for x in range(R[0], R[2]):
            v = [a[y, X] for X in (x - 26, x - 52, x - 78, x + 52) if 0 <= X < 320 and not (222 <= X < 268)]
            if a[y, x] not in v: near[y, x] = True
    inbox[R[1]:R[3], R[0]:R[2]] = True
    for y, x in zip(*np.where(near)):
        v = [a[y, X] for X in range(x % 26, 320, 26) if src[y, X]]
        near_v = [a[y, X] for X in (x - 26, x + 26, x - 52, x + 52) if 0 <= X < 320 and src[y, X]]
        out[y, x] = np.bincount(v + near_v).argmax()
    return out, inbox
def draw(bg, font='g14b'):
    W = words(); o = bg.copy()
    for i, (x0, y0, x1, y1) in enumerate(BOX):
        w = W['G%02d' % (i + 1)]; pts = set(); X = 0
        for ch in w:
            p = kfont.ink(ch); mn = min(x for x, y in p); w1 = max(x for x, y in p) - mn + 1
            off = X + (15 - w1) // 2
            for x, y in p:
                pts.add((x - mn + off, y))
                if font == 'g14b': pts.add((x - mn + off + 1, y))
            X += 16
        top = min(y for x, y in pts); h = max(y for x, y in pts) - top + 1
        for x, y in pts:
            xx = x0 + 1 + x; yy = y0 + (y1 - y0 - h) // 2 + y - top
            assert x0 <= xx < x1 and y0 <= yy < y1, (w, xx, yy); o[yy, xx] = 1
    return o
if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8'); P = fbp.pal(fbp.ALL, 0); a = fbp.img(1); bg, inbox = blank(a); o = draw(bg)
    assert not ((o != a) & ~inbox).any()
    S = Image.new('RGB', (1260, 1290)); d = ImageDraw.Draw(S); f = ImageFont.truetype('malgun.ttf', 20)
    for i, (t, m) in enumerate((('원본', a), ('글자 지운 바탕', bg), ('한글', o))):
        S.paste(Image.fromarray(P[m[2:140, 5:320]]).resize((1260, 552), 0).crop((300, 0, 1200, 552)).resize((600, 368), 0), (0, 0)) if 0 else None
        im = Image.fromarray(P[m[2:140, 60:270]]).resize((630, 414), 0); S.paste(im, (0 if i < 2 else 0, i * 430 + 24)); d.text((4, i * 430), t, font=f, fill='white')
    S = S.crop((0, 0, 640, 1290)); os.makedirs(os.path.join(ROOT, 'work', 'gfx_preview'), exist_ok=True); S.save(os.path.join(ROOT, 'work', 'gfx_preview', '장비화면.png'))
    if '--write' in sys.argv:
        os.makedirs(os.path.join(ROOT, 'work', 'gfx'), exist_ok=True)
        for n in (1, 3, 4, 5):
            assert (fbp.img(n) == a).all(); open(os.path.join(ROOT, 'work', 'gfx', 'FBP.PX@%X.bin' % (n * 65536)), 'wb').write(o.astype(np.uint8).tobytes())
    print('바뀐 화소', (o != a).sum())
