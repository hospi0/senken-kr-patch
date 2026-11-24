# -*- coding: utf-8 -*-
r"""FBP.PX 전체 화면 그림 58장 → PNG 목록(2026-11-24). 65,536 B 한 장 = 320×200 8bpp. 색 = RNG.PAL/ALLDAT 등 색표 후보."""
import os, sys, struct
import numpy as np
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); DD = os.path.join(ROOT, 'work', 'disc1')
FBP = open(os.path.join(DD, 'FBP.PX'), 'rb').read()
def pal(b, o):
    e = np.frombuffer(b[o:o + 512], '>u2').astype(int); return np.stack([(e & 31) * 255 // 31, (e >> 5 & 31) * 255 // 31, (e >> 10 & 31) * 255 // 31], -1).astype(np.uint8)
ALL = open(os.path.join(DD, 'ALLDAT.NEW'), 'rb').read()
def img(n): return np.frombuffer(FBP[n * 65536:n * 65536 + 64000], np.uint8).reshape(200, 320)
if __name__ == '__main__':
    P = pal(ALL, 0); S = Image.new('RGB', (4 * 324, 15 * 214)); d = ImageDraw.Draw(S)
    for n in range(len(FBP) // 65536):
        S.paste(Image.fromarray(P[img(n)]), (n % 4 * 324, n // 4 * 214 + 12)); d.text((n % 4 * 324, n // 4 * 214), str(n), fill=(255, 255, 0))
    S.save(os.path.join(ROOT, 'work', 'tmp', 'fbp.png'))
