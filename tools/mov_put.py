# -*- coding: utf-8 -*-
r"""mov_enc 결과를 AVI 에 제자리로 — 덩어리 길이 그대로, 그 밖 바이트 변경 0 검사 → work/gfx/<이름>.AVI@0.bin + 미리보기(되풀어 그린 것) (2026-11-24)"""
import os, pickle, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, HERE)
import tm1, tm1enc
for name in sys.argv[1:]:
    p = os.path.join(ROOT, 'work', 'disc1', name + '.AVI'); d = open(p, 'rb').read(); o = bytearray(d); fr = tm1.avi_frames(p)
    new, log = pickle.load(open(os.path.join(ROOT, 'work', 'mov', name + '_new.pkl'), 'rb')); ok = np.zeros(len(d), bool)
    for k, b in new.items():
        off, old = fr[k]; assert len(b) == len(old); o[off + 8:off + 8 + len(b)] = b; ok[off + 8:off + 8 + len(b)] = True
    a1, a2 = np.frombuffer(d, np.uint8), np.frombuffer(bytes(o), np.uint8); assert not ((a1 != a2) & ~ok).any() and len(o) == len(d)
    q = os.path.join(ROOT, 'work', 'gfx', name + '.AVI@0.bin'); open(q, 'wb').write(o)
    lo, hi = min(new), max(new); k0 = lo
    while not (len(fr[k0][1]) > 2 and tm1.header(fr[k0][1])['kflags'] & 16): k0 -= 1
    fn = tm1.avi_frames(q); assert len(fn) == len(fr); A, B = tm1.GDecoder(), tm1.GDecoder(); idx = []; im = []; bad = 0; oob0 = oob1 = 0; e0 = 0
    for k in range(k0, min(len(fr), hi + 60)):
        if len(fr[k][1]) < 2: assert len(fn[k][1]) < 2; continue
        A.decode(fr[k][1]); B.decode(fn[k][1])
        g = np.frombuffer(tm1.game_rgb(B.frame, B.dframe), np.uint8).reshape(180, 288, 3).copy(); h = np.frombuffer(tm1.game_rgb(A.frame, A.dframe), np.uint8).reshape(180, 288, 3)
        if k > hi and (g != h).any(): bad += 1
        idx.append(k); im.append(g)
        def rng(D):   # 새턴 모델 성분 범위 밖 수
            F = np.array(D.frame, np.int64); X = np.array(D.dframe); R, G, Bl = F >> 16 & 255, F >> 8 & 255, F & 255; return int(((R + X < 0) | (R + X > 255) | (G + X < 0) | (G + X > 255) | (Bl - X < 0) | (Bl - X > 255)).sum())
        oob0 += rng(A); oob1 += rng(B)
    # 탈출 뒤 0 검사
    esc0 = 0; D = tm1.GDecoder()
    for k in range(k0, hi + 1):
        b = fn[k][1]
        if len(b) < 2: continue
        f = tm1enc.trace(D, b)
    np.savez_compressed(os.path.join(ROOT, 'work', 'mov', name + '_new.npz'), idx=np.array(idx), rgb=np.stack(im))
    print(name, '바꾼 프레임', len(new), '· 파일 크기 같음', len(o), '· 마지막 뒤 다른 프레임', bad, '· 범위 밖 성분 원본/새것', oob0, oob1)
