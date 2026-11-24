# -*- coding: utf-8 -*-
r"""A6 한시·A5 「끝」 을 TrueMotion 1 로 다시 부호화 (2026-11-24)
  ★덩어리 크기 = 원본과 똑같이(짧으면 뒤 0 채움) → AVI 색인·소리·섹터 배치·데이터율이 원본 그대로.
  ★범위 밖 성분(새턴 색 잡음) 0 · 탈출 뒤 0 금지 · 새턴 모델(GDecoder)로 되풀어 확인.
  키 프레임 구간마다 병렬.  python tools/mov_enc.py A6|A5 [--only 구간번호] → work/mov/<이름>_new.pkl (프레임 번호 → 바이트)"""
import copy, os, pickle, sys, time
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, HERE)
import tm1, tm1enc, tm1band
MOV = os.path.join(ROOT, 'work', 'mov')


def segment_safe(ops, cdict):
    """tm1enc.segment 와 같되 «0,k 바로 뒤 0» 이 나오지 않게(탈출 코드 k 안에서 끝나는 연산은 탈출 금지)"""
    n = len(ops); INF = 10 ** 9
    cost = [[INF, INF] for _ in range(n + 2)]; best = [[None, None] for _ in range(n + 2)]; cost[n][0] = 0
    for i in range(n, -1, -1):
        for pe in (0, 1):
            if pe and (i == 0 or ops[i - 1][1] is None): continue
            if not pe and i == n: continue
            head = [ops[i - 1][1]] if pe else []; bc = INF; bb = None
            for L in range(0 if pe else 1, 5 - len(head)):
                if i + L > n: break
                if L > 1 and ops[i + L - 2][1] is not None: break
                idx = cdict.get(tuple(head + [ops[k][0] for k in range(i, i + L)]))
                if idx is None: continue
                esc = L > 0 and ops[i + L - 1][1] is not None
                if esc and pe: continue
                c = 2 + cost[i + L][1] if esc else 1 + cost[i + L][0]
                if c < bc: bc, bb = c, (L, idx, esc)
            cost[i][pe], best[i][pe] = bc, bb
    assert cost[0][0] < INF, '부호화 불가'
    out = bytearray(); i = pe = 0
    while not (i == n and pe == 0):
        L, idx, esc = best[i][pe]; out.append(idx)
        if esc: out.append(0)
        i += L; pe = 1 if esc else 0
    return bytes(out)


tm1enc.segment = segment_safe


import inspect, textwrap
_src = textwrap.dedent(inspect.getsource(tm1band.BandEnc24G.encode_game)).replace('ch = bool(keyframe)\n', 'ch = bool(keyframe) or (by, blk) in self.chg\n').replace('if not ch:', 'if False:', 1)
assert 'self.chg' in _src
_ns = dict(vars(tm1band)); exec(_src, _ns)                  # 바꿀 블록을 밖에서 정해 주는 encode_game(오차 큰 블록부터)


class Enc(tm1band.BandEnc24G):
    encode_game = _ns['encode_game']
    """색차를 R·B 둘 다 고름(원본 BandEnc.pick_c 는 24비트에서 B 를 버림 — 자막 띠 전용이었음, 2026-11-24)"""
    def pick_c(self, dR, dB):
        lim = getattr(self, 'clim', 12) * (1 + self.coarse)
        cdt, ft = self.cdt, self.fcdt
        a, b = self.nearest(dR, cdt), self.nearest(dB, cdt); add = [cdt[a], cdt[b]]; esc = None
        if abs(dR - add[0]) > lim or abs(dB - add[1]) > lim:
            def two(d):
                return min(((abs(d - cdt[i] - ft[j]), i, j) for i in self.allowed for j in self.allowed))
            (_, a, ea), (_, b, eb) = two(dR), two(dB); esc = (ea, eb); add = [cdt[a] + ft[ea], cdt[b] + ft[eb]]
        return (a, b), esc, add


# ── 목표 화면 ──
def targets_A6():
    import cv2
    z = np.load(os.path.join(MOV, 'A6.npz')); I = [int(x) for x in z['idx']]; F = z['rgb'].astype(np.float32); at = lambda n: F[I.index(n)]
    S = (0, 151, 252, 353); P = [at(n) for n in S]; K = np.load(os.path.join(MOV, 'poem_k.npy')).astype(np.float32); out = {}
    reg = []
    for p, k in zip(P, K):
        m = (np.abs(p - k).max(2) > 0).astype(np.uint8)
        m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8)); reg.append(cv2.dilate(m, np.ones((7, 7), np.uint8)))

    def mix(f, ws):     # ws = [(그림 번호, 무게)] — 글자 자리는 새 그림의 겹침, 그 밖은 원래 프레임
        tgt = sum(w * K[i] for i, w in ws); m = np.zeros((180, 288), np.uint8)
        for i, w in ws:
            if w > .003: m |= reg[i]
        a = np.clip(cv2.distanceTransform(m, cv2.DIST_L2, 3) / 3, 0, 1)[..., None]
        return f * (1 - a) + tgt * a
    for n, f in zip(I, F):
        if n > 466: break
        if n in S:
            out[n] = mix(f, [(S.index(n), 1.0)]); continue
        for a, b in ((0, 1), (1, 2), (2, 3)):
            if S[a] < n < S[b]:
                A, B = P[a].ravel(), P[b].ravel(); t = float(np.clip((f.ravel() - A) @ (B - A) / ((B - A) @ (B - A)), 0, 1))
                if n >= {252: 246, 353: 347}.get(S[b], 999): out[n] = mix(P[b], [(b, 1.0)]); continue    # 멈춰 있는 그림 직전 몇 프레임은 끝 그림으로(앞 글자 유령이 남지 않게)
                out[n] = mix(f, [(a, 1 - t), (b, t)])
        if n > S[3]:
            A = P[3].ravel(); s = float(np.clip(f.ravel() @ A / (A @ A), 0, 1)); out[n] = mix(f, [(3, s)]) if s > .004 else f.copy()
    return {n: np.clip(np.round(v), 0, 255).astype(np.uint8) for n, v in out.items()}, 0


def targets_A5():
    import cv2, gfx_end as g
    I, F = g.load(); p = g.plate(I, F)[g.Y0:g.Y1, g.X0:g.X1].astype(float) - 10; T = p.max(2) > 120; a = g.ko()[..., None]; out = {}
    m0 = cv2.dilate((p.max(2) > 4).astype(np.uint8), np.ones((3, 3), np.uint8)) > 0
    for n, f in zip(I, F):
        if n < 2047: continue
        o = f.astype(float).copy(); s = o[g.Y0:g.Y1, g.X0:g.X1]; al = float(np.clip((s[T].mean() - 10) / 186, 0, 1))
        m = m0 | (s.max(2) < 40); s[m] = 10; s[:] = s * (1 - a) + (10 + 240 * al) * a; out[int(n)] = np.round(o).astype(np.uint8)
    return out, 68


# ── 부호화 ──
def enc(A, f, y0, co, chg, prevB, prevD, t):
    E = Enc(A.tab, A.key[0], False, f.bw, f.bt, y0, 0, co); E.chg = chg
    cur = [list(r) for r in A.frame]; curd = [list(r) for r in A.dframe]
    ops, cb = E.encode_game(cur, curd, prevB, prevD, t, f.key)
    nb = tm1enc.rebuild(f, f.rows[:y0] + ops, [] if f.key else f.cbits[:y0 >> 2] + cb, E.cdict)
    return nb, getattr(E, 'oob', 0)


def run(job):
    name, lo, hi, tg, y0, t0 = job
    fr = tm1.avi_frames(os.path.join(ROOT, 'work', 'disc1', name + '.AVI')); A, B = tm1.GDecoder(), tm1.GDecoder(); res = {}; log = []
    for k in range(lo, hi):
        b = fr[k][1]
        if len(b) < 2: continue
        prevB = copy.deepcopy(B.frame); prevD = copy.deepcopy(getattr(B, 'dframe', None))
        same0 = prevB is not None and B.frame == A.frame and B.dframe == A.dframe
        f = tm1enc.trace(A, b)
        if f.nop or (k not in tg and (f.key or same0 or prevB is None)):
            B.decode(b); continue
        img = tg[k] if k in tg else np.frombuffer(tm1.game_rgb(A.frame, A.dframe), np.uint8).reshape(180, 288, 3)
        L = img.tolist()
        t = [[(tuple(L[y][2 * x]), tuple(L[y][2 * x + 1])) for x in range(144)] for y in range(180)]
        if prevB is None:
            prevB = [[0] * 144 for _ in range(180)]; prevD = [[0] * 144 for _ in range(180)]
        lim = len(b) - 1
        if f.key:
            plans = [(0, c / 2, set()) for c in range(0, 33)]; q = 0
            for q, (tol, co, chg) in enumerate(plans):
                nb, oob = enc(A, f, y0, co, chg, prevB, prevD, t)
                if len(nb) <= lim and not oob: break
            else: raise SystemExit('⛔ 키 %s %d: %d > %d · 범위 밖 %d' % (name, k, len(nb), lim, oob))
        else:
            # 블록(4×4 화소) 오차 = 앞 화면과 목표의 차(제곱 평균 + 최대), 큰 것부터 예산만큼
            cur0 = np.frombuffer(tm1.game_rgb(prevB, prevD), np.uint8).reshape(180, 288, 3).astype(np.int32); d = np.abs(cur0 - img.astype(np.int32))
            bl = d.reshape(45, 4, 72, 4, 3); e = (bl.astype(float) ** 2).mean((1, 3, 4)) + bl.max((1, 3, 4)) ** 2 * .15
            order = [(int(i) // 72, int(i) % 72) for i in np.argsort(-e.ravel()) if e.ravel()[i] > 6 and int(i) // 72 >= y0 >> 2]
            best = None; q = 0
            for co in (0, .5, 1):
                a0, a1 = 0, len(order) + 1; got = None      # 들어가는 최대 블록 수(이분)
                n = min(len(order), max(8, lim // 9))
                while a0 < a1:
                    nb, oob = enc(A, f, y0, co, set(order[:n]), prevB, prevD, t); q += 1
                    if len(nb) <= lim and not oob: got = (n, nb); a0 = n + 1
                    else: a1 = n
                    if a1 - a0 <= max(8, len(order) // 64): break
                    n = (a0 + a1) // 2
                if got:
                    n, nb = got; C = copy.deepcopy(B); C.decode(nb + bytes(len(b) - len(nb)))
                    o = np.frombuffer(tm1.game_rgb(C.frame, C.dframe), np.uint8).reshape(180, 288, 3).astype(float)
                    cand = (((o - img) ** 2).mean(), co, n, nb)
                    if best is None or cand[0] < best[0]: best = cand
                    if n == len(order): break
                elif not order: break
            if best is None:
                nb, oob = enc(A, f, y0, 0, set(), prevB, prevD, t); assert len(nb) <= lim and not oob, (name, k, len(nb), lim, oob); best = (0, 0, 0, nb)
            nb = best[3]; q = (best[1], best[2], len(order))
        nb2 = nb + b'\x01' + bytes(len(b) - len(nb) - 1); B.decode(nb2); res[k] = nb2      # \x01 = the decoder reads one more index after the last code; must not be 0 (escape)
        o = np.frombuffer(tm1.game_rgb(B.frame, B.dframe), np.uint8).reshape(180, 288, 3)
        log.append((k, len(nb), q, round(float(np.abs(o.astype(int) - img).mean()), 2), bool(f.key), len(b)))
    return res, log, time.time() - t0, (lo, hi, B.frame == A.frame)


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8'); name = sys.argv[1]; tg, y0 = dict(A6=targets_A6, A5=targets_A5)[name]()
    fr = tm1.avi_frames(os.path.join(ROOT, 'work', 'disc1', name + '.AVI')); first, last = min(tg), max(tg)
    keys = [k for k, (_, b) in enumerate(fr) if len(b) > 2 and tm1.header(b)['kflags'] & tm1.FLAG_KEYFRAME] + [len(fr)]
    segs = [(a, b) for a, b in zip(keys, keys[1:]) if b > first and a <= last]; print(len(tg), '프레임', segs, 'y0', y0)
    jobs = [(name, a, b, {k: v for k, v in tg.items() if a <= k < b}, y0, time.time()) for a, b in segs]
    if '--only' in sys.argv: jobs = [jobs[int(sys.argv[sys.argv.index('--only') + 1])]]
    import multiprocessing as mp
    out = {}; logs = []
    with mp.Pool(min(len(jobs), max(1, os.cpu_count() - 2))) as pool:
        for res, log, dt, info in pool.imap_unordered(run, jobs):
            out.update(res); logs += log
            print(info, '%.0fs' % dt, [(l[0], l[2], l[3]) for l in log] if '--only' in sys.argv else log[-1:], '최대 오차', max([l[3] for l in log], default=0), flush=True)
    if '--only' not in sys.argv:
        pickle.dump((out, sorted(logs)), open(os.path.join(MOV, name + '_new.pkl'), 'wb')); print('저장', len(out))
