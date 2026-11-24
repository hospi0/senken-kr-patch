# -*- coding: utf-8 -*-
r"""FB.NEW·BALL.NEW·ALLDAT.NEW 같은 RLE 스프라이트 묶음 보기(2026-11-24). 머리 u16 BE 폭·높이, 바이트: 0 = 127 건너뜀, >=0x80 = n-0x80 건너뜀, 그 밖 = n 화소."""
import os, sys, struct
import numpy as np
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); ROOT = os.path.dirname(HERE)
import fbp
def dec(b, o):
    w, h = struct.unpack_from('>HH', b, o)
    if not (0 < w <= 320 and 0 < h <= 240): return None
    o += 4; out = np.full(w * h, -1, int); p = 0
    while p < w * h and o < len(b):
        n = b[o]; o += 1
        if n == 0: p += 127
        elif n >= 0x80: p += n - 0x80
        else:
            m = min(n, w * h - p); out[p:p + m] = list(b[o:o + m]); o += n; p += n
    return out.reshape(h, w) if p == w * h else None
if __name__ == '__main__':
    b = open(os.path.join(fbp.DD, sys.argv[1]), 'rb').read(); P = fbp.pal(fbp.ALL, 0); ims = []; seen = 0
    for o in range(0, len(b) - 4, 2):
        if o < seen: continue
        a = dec(b, o)
        if a is None or a.size < 64: continue
        im = P[np.maximum(a, 0)].copy(); im[a < 0] = (255, 0, 255); ims.append((o, im))
        seen = o + 4
    if len(sys.argv) > 2: ims = ims[:int(sys.argv[2])]
    W = 1300; x = y = rh = 0; S = Image.new('RGB', (W, 6000)); d = ImageDraw.Draw(S)
    for o, im in ims:
        w = max(im.shape[1], 40)
        if x + w > W: x = 0; y += rh + 14; rh = 0
        d.text((x, y), '%X' % o, fill=(255, 255, 0)); S.paste(Image.fromarray(im), (x, y + 12)); x += w + 4; rh = max(rh, im.shape[0])
    print(len(ims)); S.crop((0, 0, W, min(6000, y + rh + 14))).save(os.path.join(ROOT, 'work', 'tmp', sys.argv[1] + '.png'))
