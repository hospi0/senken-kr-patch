# -*- coding: utf-8 -*-
r"""선검기협전 배포 묶음(2026-11-24, 새턴 봄버맨 파이트 make_dist 에서) — dist/SenkenKigyouden_KR_<VER>/ : 트랙 01 xdelta + xdelta.exe + readme.txt(CP949) + 한글패치_적용.bat(CP949)
  바뀌는 트랙 = 트랙 01 뿐. 트랙 02~13(오디오)·cue 그대로
  검증: 원본 → xdelta 적용 → md5 = 빌드 md5 → 그 md5 가 readme «패치md5»(xdelta 파일 md5 아님)
  python tools/make_dist.py   (먼저 python tools/build.py)"""
import hashlib, os, shutil, subprocess, sys, zipfile
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)

VER = 'v0.9'
XDELTA = r'C:\claude\utils\xdelta.exe'
ROM = 'Senken Kigyouden (Japan)'
DIR = 'Senken Kigyouden (Japan)'
SRC = os.path.join('C:' + os.sep, 'claude', 'roms', 'ss', DIR)
OUT = os.path.join(ROOT, 'dist', 'build', DIR)
NAME = 'SenkenKigyouden_KR_' + VER
TITLE = '선검기협전 (세가 새턴 일본판) 한글 패치 ' + VER


def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 22), b''):
            h.update(b)
    return h.hexdigest().upper()


README = """{title}
{line}

13개의 트랙으로 이루어진 {rom} 의
트랙 01번에 패치하시면 됩니다. 트랙 02~13 과 cue 는 원본 그대로 씁니다.

{md5s}

[ 적용 방법 ]

  1) 원본 트랙 01 파일을 이 폴더에 복사
       "{bin1}"
  2) 한글패치_적용.bat 실행 → 이름 끝에 [KR] 이 붙은 파일이 만들어집니다
  3) 만든 파일 이름을 원본 트랙 01 이름으로 바꿔 넣고, 트랙 02~13 과 cue 는 원본 그대로 쓰세요

  직접 적용:
    xdelta.exe -d -s "원본 트랙 01" "{p1}" "결과 트랙 01"
  (Delta Patcher 같은 xdelta3 GUI 도구로 적용해도 됩니다. 원본이 다르면 xdelta 가 적용을 거부합니다.)


[ 바뀌는 것 ]

  - 대사 전부(본편·선택지·알림·시스템 메시지)
  - 인물·아이템·장비·선술·지명 이름과 아이템 설명, 메뉴
  - 장비 화면 그림 글자, 타이틀의 훈독 글자
  - 엔딩 영상의 한시와 「全劇終」 글자


[ 알려진 점 ]

  - 예전 버전의 세이브스테이트는 쓰지 말고 새로 시작하거나 게임 안 세이브로 이어 하세요.
  - 타이틀 로고와 무대 양탄자의 「比武招親」 글자는 원본 그대로입니다.
"""

BAT = r"""@echo off
chcp 949 >nul
set "XD=%~dp0xdelta.exe"
if not exist "%~dp0{bin1}" (
  echo   [오류] 원본 트랙 01 파일을 이 폴더에 넣어 주세요 - readme 참고.
  pause & exit /b 1
)
"%XD%" -d -f -s "%~dp0{bin1}" "%~dp0{p1}" "%~dp0{k1}"
if errorlevel 1 (
  echo   [오류] 트랙 01 패치 실패 - 원본이 다를 수 있습니다 - readme 의 원본md5 확인.
  pause & exit /b 1
)
echo   완료: "{k1}"
pause
"""


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    d = os.path.join(ROOT, 'dist', NAME)
    if os.path.isdir(d):
        shutil.rmtree(d)
    os.makedirs(d)
    b = '%s (Track 01).bin' % ROM
    src, out = os.path.join(SRC, b), os.path.join(OUT, b)
    patch = NAME + '_Track01.xdelta'; pp = os.path.join(d, patch)
    subprocess.run([XDELTA, '-e', '-9', '-B', '536870912', '-f', '-s', src, out, pp], check=True)
    chk = os.path.join(d, '_check.bin')
    subprocess.run([XDELTA, '-d', '-f', '-s', src, pp, chk], check=True)
    o, want, got = md5(src), md5(out), md5(chk)
    os.remove(chk)
    assert got == want, ('패치 적용 결과가 빌드와 다름', got, want)
    assert want != md5(pp), 'readme 패치md5 는 결과 트랙 md5 여야 함'
    print('트랙 01 원본md5 %s → 패치md5(결과) %s · %s %d B' % (o, want, patch, os.path.getsize(pp)))
    names = dict(bin1=b, p1=patch, k1='%s (Track 01) [KR].bin' % ROM)
    md5s = '트랙 01  원본md5 : %s\n         패치md5 : %s\n' % (o, want)
    shutil.copy2(XDELTA, os.path.join(d, 'xdelta.exe'))
    readme = README.format(title=TITLE, line='=' * 60, rom=ROM, md5s=md5s, **names)
    open(os.path.join(d, 'readme.txt'), 'wb').write(readme.replace('\n', '\r\n').encode('cp949'))
    open(os.path.join(d, '한글패치_적용.bat'), 'wb').write(BAT.format(**names).replace('\n', '\r\n').encode('cp949'))
    z = os.path.join(ROOT, 'dist', NAME + '.zip')
    with zipfile.ZipFile(z, 'w', zipfile.ZIP_DEFLATED) as zf:
        for f in sorted(os.listdir(d)):
            zf.write(os.path.join(d, f), NAME + '/' + f)
    print('✅', d)
    for f in sorted(os.listdir(d)):
        print('  %-48s %12d' % (f, os.path.getsize(os.path.join(d, f))))
    print('  zip %s %d B · md5 %s' % (os.path.basename(z), os.path.getsize(z), md5(z)))


if __name__ == '__main__':
    main()
