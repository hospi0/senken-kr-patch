# -*- coding: utf-8 -*-
"""대사 명령(0xFFFF)이 «번호, 추가 줄 수» 를 받아 이어 찍게 하는 손질 (2026-11-24)
  0x060255D6‥0x06025601(다음 줄 y 계산, 최적화 안 된 22 명령)을 짧게 다시 쓰고 남은 자리에 반복을 넣음.
  지역 변수: r14+0x0C = 대사 번호, +0x0E = 추가 줄 수(원본은 늘 0), +0x1C = y.  알림 상자 길(0x06025460)도 반복으로 보냄."""
import struct
A, END, LOOP, BOX = 0x060255D6, 0x06025602, 0x06025268, 0x06025460
def w(p, a): return struct.unpack_from('>H', p, a - 0x6020000)[0]
def apply(p):
    assert w(p, A) == 0x62E3 and w(p, END) == 0xA319 and w(p, BOX) == 0xA0CF, 'PROG.BIN 이 다름'
    lit = 0x06025844; assert struct.unpack_from('>I', p, lit - 0x6020000)[0] == 0x06076B82
    c = []
    c.append(0xD200 | (lit - ((A + 4) & ~3)) // 4)           # mov.l =06076B82,r2
    c += [0x6321,                                             # mov.w @r2,r3
          0x85EE,                                             # mov.w @(28,r14),r0
          0x2338,                                             # tst r3,r3
          0x8F01,                                             # bf/s L
          0x7010,                                             # add #16,r0
          0x7002,                                             # add #2,r0
          0x81EE]                                             # L: mov.w r0,@(28,r14)
    hook = A + 2 * len(c)
    c += [0x85E7,                                             # mov.w @(14,r14),r0
          0x2008,                                             # tst r0,r0
          0x8900,                                             # bt END (아래에서 채움)
          0x70FF,                                             # add #-1,r0
          0x81E7,                                             # mov.w r0,@(14,r14)
          0x85E6,                                             # mov.w @(12,r14),r0
          0x7001,                                             # add #1,r0
          0x81E6]                                             # mov.w r0,@(12,r14)
    at = A + 2 * len(c); c += [0xA000 | (((LOOP - (at + 4)) // 2) & 0xFFF), 0x0009]
    k = next(i for i, x in enumerate(c) if x == 0x8900); c[k] |= (END - (A + 2 * k + 4)) // 2
    n = (END - A) // 2; assert len(c) <= n, len(c); c += [0x0009] * (n - len(c))
    for i, x in enumerate(c): struct.pack_into('>H', p, A - 0x6020000 + 2 * i, x)
    struct.pack_into('>H', p, BOX - 0x6020000, 0xA000 | (((hook - (BOX + 4)) // 2) & 0xFFF))
    return hook
def selftest(p):
    """y 계산(원본과 같은 값)·반복 횟수·번호 증가 — 끝(0x06025602)·반복(0x06025268) 도착을 봄"""
    import sh2sim; bad = []
    from units import PROG
    for style in (0, 1, 9, 10):
        for y in (26, 126):
            for extra in (0, 1, 3):
                res = []
                for img in (PROG, p):
                    m = sh2sim.Mem(); q = bytearray(img); struct.pack_into('>h', q, 0x56B82, style); m.map(0x06020000, q); m.map(0x06010000, bytes(0x10000))
                    f = 0x0601E000; m.w16(f + 0x1C, y); m.w16(f + 0xE, extra); m.w16(f + 0xC, 1000)
                    c = sh2sim.CPU(m, A, {14: f, 8: 8, 10: 10, 11: 11, 12: 12, 13: 13}, stack_top=0x0601D000); s = 0
                    while c.pc not in (END, LOOP) and s < 100: c.step(); s += 1
                    res.append((c.pc, m.r16(f + 0x1C), m.r16(f + 0xE), m.r16(f + 0xC), c.r[10:16]))
                o, n = res
                want = (LOOP if extra else END, o[1], extra - 1 if extra else 0, 1001 if extra else 1000, o[4])
                if n != want: bad.append((style, y, extra, n, want))
    return bad
