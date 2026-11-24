# -*- coding: utf-8 -*-
r"""A5 끝 「全劇終」 → 「끝」 (2026-11-24). 글자 자리 = x 86~206·y 68~112(검은 바탕 + 눈). 글자판 = 프레임 최소값(눈 빠짐).
  python tools/gfx_end.py → work/gfx_preview/엔딩_끝.png"""
import os, sys
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
X0, Y0, X1, Y1 = 84, 68, 208, 112
def load():
    z = np.load(os.path.join(ROOT, 'work', 'mov', 'A5.npz')); return z['idx'], z['rgb']
def plate(I, F):
    k = [i for i in range(len(I)) if 2080 <= I[i] < 2200]; return F[k].min(0)
def ko(txt='끝', size=40, font=r'C:\claude\utils\font\yeonsung\YeonSung-Regular.ttf'):
    S = 8; W, H = (X1 - X0) * S, (Y1 - Y0) * S; f = ImageFont.truetype(font, size * S); im = Image.new('L', (W, H)); d = ImageDraw.Draw(im)
    b = d.textbbox((0, 0), txt, font=f); d.text(((W - b[2] + b[0]) / 2 - b[0], (H - b[3] + b[1]) / 2 - b[1]), txt, font=f, fill=255)
    im = im.transform(im.size, Image.AFFINE, (1, .22, -.22 * H / 2, 0, 1, 0), Image.BICUBIC)      # 원문처럼 오른쪽으로 기울임
    return np.asarray(im.resize((X1 - X0, Y1 - Y0), Image.BOX)).astype(float) / 255
if __name__ == '__main__':
    I, F = load(); p = plate(I, F); base = int(np.median(p)); print('바탕', base, '글자 최대', p.max())
    g = p[Y0:Y1, X0:X1].max(2); ys, xs = np.where(g > 60); print('글자 범위', X0 + xs.min(), X0 + xs.max(), Y0 + ys.min(), Y0 + ys.max())
    rest = p.copy(); rest[Y0:Y1, X0:X1] = 0; print('상자 밖 밝은 화소', (rest.max(2) > 40).sum())
    fr = F[list(I).index(2150)].copy(); a = ko()
    o = fr.copy().astype(float); m = cv2.dilate((g > base + 8).astype(np.uint8), np.ones((3, 3), np.uint8)) > 0
    sub = o[Y0:Y1, X0:X1]; m |= sub.max(2) < 45; sub[m] = base; sub[:] = sub * (1 - a[..., None]) + 250 * a[..., None]
    S = Image.new('RGB', (288 * 3, 540 * 2 + 60)); d = ImageDraw.Draw(S); f = ImageFont.truetype('malgun.ttf', 20)
    for i, (t, im) in enumerate((('원본', fr), ('한글', o.astype(np.uint8)))):
        d.text((4, i * 570), t, font=f, fill='yellow'); S.paste(Image.fromarray(im).resize((864, 540), Image.LANCZOS), (0, i * 570 + 28))
    S.save(os.path.join(ROOT, 'work', 'gfx_preview', '엔딩_끝.png'))
