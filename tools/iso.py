# -*- coding: utf-8 -*-
"""Senken Kigyouden (Japan) 트랙 1(MODE1/2352) ISO9660 읽기 — python tools/iso.py 1 [list|extract 이름…|all]
(coder-kr-patch/tools/iso.py 에서 가져옴, 디스크 번호 인자 추가)"""
import os, struct, sys
sys.stdout.reconfigure(encoding='utf-8')
ROMS = {1: r'C:/claude/roms/ss/Senken Kigyouden (Japan)/Senken Kigyouden (Japan) (Track 01).bin'}
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Disc:
    def __init__(self, n):
        self.n = n; self.f = open(ROMS[n], 'rb')
        pvd = self.sec(16)
        rl = struct.unpack_from('<I', pvd, 158)[0]; rs = struct.unpack_from('<I', pvd, 166)[0]
        self.files = list(self.walk(rl, rs))

    def sec(self, lba, n=1):
        out = b''
        for i in range(n):
            self.f.seek((lba + i) * 2352 + 16); out += self.f.read(2048)
        return out

    def walk(self, lba, size, path=''):
        d = self.sec(lba, (size + 2047) // 2048); i = 0
        while i < len(d):
            ln = d[i]
            if ln == 0:
                i = (i // 2048 + 1) * 2048; continue
            el = struct.unpack_from('<I', d, i + 2)[0]; es = struct.unpack_from('<I', d, i + 10)[0]
            fl = d[i + 25]; nl = d[i + 32]; name = d[i + 33:i + 33 + nl].decode('ascii', 'replace')
            if name not in ('\x00', '\x01'):
                p = path + '/' + name.split(';')[0]
                if fl & 2:
                    yield from self.walk(el, es, p)
                else:
                    yield p, el, es
            i += ln

    def record(self, name):
        """디렉터리 레코드 자리 (섹터 LBA, 섹터 안 위치) — 파일 크기 고칠 때(2026-11-23 파이트 HOW 대본 덧붙임)"""
        pvd = self.sec(16); stack = [(struct.unpack_from('<I', pvd, 158)[0], struct.unpack_from('<I', pvd, 166)[0], '')]
        while stack:
            lba, size, path = stack.pop()
            for k in range((size + 2047) // 2048):
                d = self.sec(lba + k); i = 0
                while i < 2048 and d[i]:
                    ln = d[i]; nl = d[i + 32]; nm = d[i + 33:i + 33 + nl].decode('ascii', 'replace')
                    if nm not in ('\x00', '\x01'):
                        p = path + '/' + nm.split(';')[0]
                        if d[i + 25] & 2: stack.append((struct.unpack_from('<I', d, i + 2)[0], struct.unpack_from('<I', d, i + 10)[0], p))
                        elif p.lstrip('/').upper() == name.lstrip('/').upper(): return lba + k, i
                    i += ln
        raise KeyError(name)

    def read(self, name):
        for p, l, s in self.files:
            if p.lstrip('/').upper() == name.lstrip('/').upper():
                return self.sec(l, (s + 2047) // 2048)[:s]
        raise KeyError(name)


if __name__ == '__main__':
    D = Disc(int(sys.argv[1]))
    cmd = sys.argv[2] if len(sys.argv) > 2 else 'list'
    if cmd == 'list':
        for p, l, s in D.files:
            print('%-40s %8d %10d' % (p, l, s))
        print(len(D.files), '개', sum(s for _, _, s in D.files), 'B')
    else:
        names = [p for p, _, _ in D.files] if cmd == 'all' else sys.argv[3:]
        out = os.path.join(ROOT, 'work', 'disc%d' % D.n)
        for nm in names:
            dst = os.path.join(out, nm.lstrip('/')); os.makedirs(os.path.dirname(dst), exist_ok=True)
            open(dst, 'wb').write(D.read(nm)); print(nm)
