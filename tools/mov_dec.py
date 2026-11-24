# -*- coding: utf-8 -*-
r"""A6·A5 글자 장면 프레임 풀기(게임 모델 GDecoder) → work/mov/<이름>.npz (프레임 번호 idx, 화소 rgb) (2026-11-24)
  python tools/mov_dec.py A6 0 420"""
import os, sys, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, HERE)
import tm1
n, a, b = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
fr = tm1.avi_frames(os.path.join(ROOT, 'work', 'disc1', n + '.AVI')); D = tm1.GDecoder(); idx = []; out = []
k0 = a
while k0 > 0 and not (len(fr[k0][1]) > 2 and tm1.header(fr[k0][1])['kflags'] & tm1.FLAG_KEYFRAME): k0 -= 1
for k in range(k0, b):
    c = fr[k][1]
    if len(c) < 2: continue
    D.decode(c)
    idx.append(k); out.append(np.frombuffer(tm1.game_rgb(D.frame, D.dframe), np.uint8).reshape(180, 288, 3).copy())
os.makedirs(os.path.join(ROOT, 'work', 'mov'), exist_ok=True)
np.savez_compressed(os.path.join(ROOT, 'work', 'mov', n + '.npz'), idx=np.array(idx), rgb=np.stack(out)); print(n, len(idx), idx[0], idx[-1])
