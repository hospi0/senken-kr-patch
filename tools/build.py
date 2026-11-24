# -*- coding: utf-8 -*-
r"""선검기협전(새턴 JP) 디스크 빌드 (2026-11-24, satbomberfight build.py 를 옮김)
  글 = build_text.main() 결과(제자리 파일 교체) · 그림/동영상 = work/gfx/<파일>@<위치 16진>.bin 을 제자리에 덮음(파일 크기 안).
  검사: 글 오류 0 · 그림판 겹침 없음 · 파일 크기(ERROR.TXT 만 마지막 섹터 안에서 늘 수 있음) · 되읽기 일치 · 바꾼 섹터 밖 변경 0.
  python tools/build.py [--write] [--install]    ⛔--write·--install 은 하스피 허락 받고.  --jp = 번역 빈칸 허용(시험용)"""
import glob, hashlib, os, shutil, struct, sys
from collections import defaultdict
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, HERE)
WRITE = '--write' in sys.argv
if not WRITE and '--check' not in sys.argv: sys.argv.append('--check')       # 계획만일 땐 charmap 도 안 씀
import build_text
from iso import Disc, ROMS
from cdrom_ecc import recalc_sector
F_DIR = r'F:\hospi\roms\ss roms\Senken Kigyouden (Japan)'
OUT = os.path.join(ROOT, 'dist', 'build', 'Senken Kigyouden (Japan)')

def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for c in iter(lambda: f.read(1 << 22), b''): h.update(c)
    return h.hexdigest()

def jobs(D):
    files, err = build_text.main()
    if err: sys.exit('글 오류가 있어 빌드 중단')
    by = defaultdict(list)
    for n, b in files.items(): by[n].append((0, b))
    for fn in sorted(glob.glob(os.path.join(ROOT, 'work', 'gfx', '*@*.bin'))):
        n, o = os.path.basename(fn)[:-4].split('@'); by[n].append((int(o, 16), open(fn, 'rb').read()))
    out = []
    for n, L in by.items():
        lba, size = next((l, s) for p, l, s in D.files if p == '/' + n)
        cap = (size + 2047) // 2048 * 2048; orig = D.sec(lba, cap // 2048); new = bytearray(orig); L.sort(); end = size
        for (a, x), (b, _) in zip(L, L[1:]): assert a + len(x) <= b, ('겹침', n, hex(b))
        for o, x in L:
            assert o + len(x) <= cap, ('섹터 밖', n, hex(o), len(x), cap); new[o:o + len(x)] = x; end = max(end, o + len(x))
        if n == 'ERROR.TXT': new[len(files[n]):cap] = b'\0' * (cap - len(files[n]))
        else: assert end == size, ('크기 달라짐', n, size, end)
        if bytes(new) != orig: out.append((n, lba, cap, orig, bytes(new), size, end)); print('  %-11s 바뀐 바이트 %d%s' % (n, sum(a != b for a, b in zip(orig, new)), '' if end == size else ' · 크기 %d→%d' % (size, end)))
    return out

def main():
    sys.stdout.reconfigure(encoding='utf-8')
    assert md5(ROMS[1]) == '09dbb6c7d42e9e515c1fcdf588aa107c', '원본 트랙 1 이 다름'
    D = Disc(1); J = jobs(D)
    if not WRITE: print('계획만 — 디스크 안 씀'); return
    os.makedirs(OUT, exist_ok=True); src = os.path.dirname(ROMS[1]); t1 = os.path.join(OUT, os.path.basename(ROMS[1])); shutil.copyfile(ROMS[1], t1); dirty = set()
    with open(t1, 'r+b') as fh:
        def put(s, fn):
            fh.seek(s * 2352); sec = bytearray(fh.read(2352)); assert sec[15] == 1, ('MODE1 아님', s); fn(sec)
            fh.seek(s * 2352); fh.write(recalc_sector(bytes(sec))); dirty.add(s)
        for n, lba, cap, orig, new, size, end in J:
            if end != size:
                rl, ro = D.record(n)
                def fix(sec):
                    assert struct.unpack_from('<I', sec, 16 + ro + 10)[0] == size
                    struct.pack_into('<I', sec, 16 + ro + 10, end); struct.pack_into('>I', sec, 16 + ro + 14, end)
                put(rl, fix)
            for i in range(0, cap, 2048):
                if orig[i:i + 2048] != new[i:i + 2048]:
                    def fix(sec, i=i): sec[16:2064] = new[i:i + 2048]
                    put(lba + i // 2048, fix)
    N = Disc.__new__(Disc); N.n = 1; N.f = open(t1, 'rb'); N.files = D.files
    for n, lba, cap, orig, new, size, end in J: assert N.sec(lba, cap // 2048) == new, ('되읽기 다름', n)
    a = open(ROMS[1], 'rb'); b = open(t1, 'rb'); bad = [s for s in range(os.path.getsize(t1) // 2352) if a.read(2352) != b.read(2352) and s not in dirty]
    assert not bad and os.path.getsize(t1) == os.path.getsize(ROMS[1]), bad[:5]
    print('검산 통과 · 바뀐 섹터 %d · 트랙 01 md5 %s' % (len(dirty), md5(t1)))
    if '--install' in sys.argv:
        dst = os.path.join(F_DIR, os.path.basename(ROMS[1])); assert os.path.exists(dst), dst
        shutil.copyfile(t1, dst); assert md5(dst) == md5(t1); print('F: 설치(원래 폴더 트랙 01 덮어씀)', dst)

if __name__ == '__main__': main()
