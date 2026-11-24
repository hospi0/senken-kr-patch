# -*- coding: utf-8 -*-
r"""타이틀(FBP.PX 2) 위 훈독 せん けん き ぎょう でん → 선 검 기 협 전 (2026-11-24). 로고 한자·그림·© 은 안 건드림.
  바탕 = 색 254(검정) 단색. 원래 훈독이 있던 사각형(y 1~18) 밖 변경 0. 색 = 회색 단계(색표 0~15).
  python tools/gfx_title.py → work/gfx_preview/타이틀훈독.png · --write = work/gfx/FBP.PX@20000.bin"""
import os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, HERE)
import fbp
FONT = r'C:\claude\utils\font\nanum-gothic\NanumGothic.ttf'
def make(size=16):
    a = fbp.img(2); P = fbp.pal(fbp.ALL, 0); o = a.copy()
    ink = a[:19] != 254; assert ink[18].sum() == 0, '훈독 아래 빈 줄 없음'
    ys, xs = np.where(ink); box = (xs.min(), ys.min(), xs.max() + 1, ys.max() + 1); o[:19][ink] = 254
    k = a[21:62] != 254; cols = k[:24].any(0); runs = []; s = None
    for x in range(321):
        c = x < 320 and cols[x]
        if c and s is None: s = x
        if not c and s is not None: runs.append([s, x]); s = None
    m = []                                                     # 한자 다섯 칸(가까운 조각 합침)
    for r in runs:
        if m and r[0] - m[-1][1] < 6: m[-1][1] = r[1]
        else: m.append(r)
    print('한자 칸', m, '훈독 범위', box); assert len(m) == 5
    gray = {int(P[i][0]): i for i in range(16) if P[i][0] == P[i][1] == P[i][2]}; lv = np.array(sorted(gray))
    f = ImageFont.truetype(FONT, size * 4); ref = ImageDraw.Draw(Image.new('L', (8, 8)))
    tb = ref.textbbox((0, 0), '선검기협전', font=f); h4 = tb[3] - tb[1]
    for (x0, x1), ch in zip(m, '선검기협전'):
        b = ref.textbbox((0, 0), ch, font=f); w4 = b[2] - b[0]; W = (w4 + 7) // 4; H = (h4 + 3) // 4
        im = Image.new('L', (W * 4, H * 4)); ImageDraw.Draw(im).text(((W * 4 - w4) // 2 - b[0], -tb[1]), ch, font=f, fill=255)
        g = np.asarray(im.resize((W, H), Image.BOX)).astype(int); g = np.clip(g * 1.2, 0, 255)
        X = (x0 + x1 - W) // 2; Y = box[1] + (box[3] - box[1] - H) // 2
        assert Y >= box[1] and Y + H <= box[3], ('높이', H, box)
        for y, x in zip(*np.where(g > 40)): o[Y + y, X + x] = gray[int(lv[np.abs(lv - g[y, x]).argmin()])]
    d = np.where((o != a).any(1))[0]; assert d.max() < 19; return a, o, P
if __name__ == '__main__':
    a, o, P = make(); S = Image.new('RGB', (960, 420)); d = ImageDraw.Draw(S); f = ImageFont.truetype('malgun.ttf', 18)
    for i, (t, m) in enumerate((('원본', a), ('한글', o))):
        d.text((4, i * 210), t, font=f, fill='yellow'); S.paste(Image.fromarray(P[m[:61]]).resize((960, 183), 0), (0, i * 210 + 26))
    S.save(os.path.join(ROOT, 'work', 'gfx_preview', '타이틀훈독.png')); print('바뀐 화소', (a != o).sum(), '254 색', P[254])
    if '--write' in sys.argv: open(os.path.join(ROOT, 'work', 'gfx', 'FBP.PX@20000.bin'), 'wb').write(o.astype(np.uint8).tobytes())
