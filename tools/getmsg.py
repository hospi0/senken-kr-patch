# -*- coding: utf-8 -*-
"""GetMsg(번호) 새 루틴 — PROG.BIN 0x06051C28‥0x0605219F 자리(옛 두 함수)에 덮어씀 (2026-11-24)
  묶음 c = FIRST 표로 찾고, 버퍼(+0x10 u16)가 0xFE00+c 면 그대로, 아니면 JM.MSG 에서 읽음.
  이야기 묶음 0‥13 = 사운드 RAM 0x25A4F000(+현재 묶음 변수 0x06076B4E), 아이템 묶음 14 = 0x25A48000. 위치표 = 0x060779D4 u16(묶음 안 위치)."""
import struct
from sh2asm import assemble
ORG, END, NCH = 0x06051C28, 0x060521A0, 15
TBL, BUFT, NAME = 0x060779D4, 0x0608C120, 0x060842B4
MAXID = 17172
ASM = '''
mov.l r8,@-r15
mov.l r9,@-r15
mov.l r10,@-r15
mov.l r11,@-r15
mov.l r12,@-r15
sts.l pr,@-r15
extu.w r4,r8
mov.l #0x0608C120,r4
mov.l #0xFF,r5
mov.l #0x060226C0,r0
jsr @r0
nop
mov.l #FIRST,r1
mov #0,r9
find:
mov.w @r1+,r2
extu.w r2,r2
cmp/hs r2,r8
bf found
bra find
add #1,r9
found:
mov.l #0x060779D4,r0
mov r8,r1
add r1,r1
add r0,r1
mov.w @r1+,r10
extu.w r10,r10
mov r8,r3
add #1,r3
cmp/eq r2,r3
bf notlast
mov r9,r0
add r0,r0
mov.l #ENDS,r1
add r0,r1
notlast:
mov.w @r1,r11
extu.w r11,r11
sub r10,r11
mov.l #0x25A4F000,r12
mov r9,r0
cmp/eq #14,r0
bf story
mov.l #0x25A48000,r12
bra sig
nop
story:
mov.l #0x06076B4E,r1
mov.w @r1,r2
extu.w r2,r2
cmp/eq r9,r2
bf load
sig:
mov r12,r1
add #16,r1
mov.w @r1,r2
extu.w r2,r2
mov.l #0xFE00,r0
add r9,r0
cmp/eq r0,r2
bt ready
load:
mov r9,r0
add r0,r0
mov.l #SECT,r1
mov.w @(r0,r1),r5
extu.w r5,r5
mov.l #NSEC,r1
mov.w @(r0,r1),r7
extu.w r7,r7
shll8 r7
shll2 r7
add r7,r7
mov r12,r6
mov.l #0x060842B4,r4
mov.l #0x06020094,r0
jsr @r0
nop
mov r9,r0
cmp/eq #14,r0
bt ready
mov.l #0x06076B4E,r1
mov.w r9,@r1
ready:
mov r12,r4
add r10,r4
mov.l #0x0608C120,r5
mov r11,r6
mov.l #0x0605D75C,r0
jsr @r0
nop
mov r11,r0
lds.l @r15+,pr
mov.l @r15+,r12
mov.l @r15+,r11
mov.l @r15+,r10
mov.l @r15+,r9
rts
mov.l @r15+,r8
'''
def build(first, ends, sect, nsec, total):
    """first = 묶음별 첫 번호(15) · ends = 묶음별 끝 위치 · sect/nsec = 섹터 시작/수 → 0x578 B"""
    assert len(first) == len(ends) == len(sect) == len(nsec) == NCH
    tab = END - 2 * NCH * 4
    src = ASM
    for i, n in enumerate(('FIRST', 'ENDS', 'SECT', 'NSEC')): src = src.replace('#' + n, '#0x%08X' % (tab + i * 2 * NCH))
    code = assemble(src, ORG); assert ORG + len(code) <= tab, hex(len(code))
    f = list(first[1:]) + [total]
    data = b''.join(struct.pack('>15H', *x) for x in (f, ends, sect, nsec))
    return code + b'\0' * (tab - ORG - len(code)) + data
def selftest(prog, msg, msgs, first, sect, nsec, step=97):
    """sh2sim 으로 실제 코드를 돌려 대조 — step 개마다 하나 + 묶음 경계 전부, 안 올라옴/올라옴 두 경우(파일 읽기·DMA 는 가짜, 버퍼 지우기는 진짜)"""
    import sh2sim
    bad = []; n = 0; ch = 0
    for k, want in enumerate(msgs):
        while ch + 1 < NCH and k >= first[ch + 1]: ch += 1
        if k % step and k not in first and k + 1 not in first and k != len(msgs) - 1: continue
        base = 0x25A48000 if ch == 14 else 0x25A4F000; data = msg[sect[ch] * 2048:(sect[ch] + nsec[ch]) * 2048]
        for warm in (0, 1, 2):                                # 0 = 처음, 1 = 올라와 있음, 2 = 변수만 맞고 내용이 덮임
            m = sh2sim.Mem(); p = bytearray(prog); p[0x94:0x98] = p[0x3D75C:0x3D760] = bytes.fromhex('000b0009')
            struct.pack_into('>H', p, 0x56B4E, ch if warm else 0xFFFF)
            m.map(0x06020000, p); m.map(0x06010000, bytes(0x10000)); m.map(0x06088000, bytes([0xAA]) * 0x8000)
            m.map(base, data if warm == 1 else bytes(len(data)))
            c = sh2sim.CPU(m, ORG, {4: k, 8: 8, 9: 9, 10: 10, 11: 11, 12: 12, 13: 13, 14: 14}, stack_top=0x0601F000); c.pr = 0x06000000; log = {}
            while c.pc != 0x06000000:
                if c.pc == 0x06020094: log['load'] = tuple(c.r[4:8])
                if c.pc == 0x0605D75C: log['copy'] = tuple(c.r[4:7])
                c.step()
            src, dst, ln = log['copy']; got = data[src - base:src - base + ln]
            ok = got == want and dst == BUFT and c.r[0] == ln and c.r[8:16] == [8, 9, 10, 11, 12, 13, 14, 0x0601F000]
            ok &= log.get('load') == (None if warm == 1 else (NAME, sect[ch], base, nsec[ch] * 2048))
            ok &= all(m.r8(BUFT + i) == 0 for i in range(255))
            if ch < 14: ok &= m.r16(0x06076B4E) == ch
            n += 1
            if not ok: bad.append((k, ch, warm, log, got, want))
    return bad, n
