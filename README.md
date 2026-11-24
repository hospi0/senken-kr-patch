# 선검기협전 (세가 새턴 일본판) 한글 패치

- 원본: `Senken Kigyouden (Japan)` (13트랙, 트랙 01 에만 패치, 트랙 02부터 13까지와 cue 는 그대로)
- 배포 파일은 릴리즈의 zip(xdelta + 적용 bat + readme)을 쓰세요.
- 번역 합본: `data/senken_ko.tsv` (빌더 입력은 `data/tr/` 나눈 파일 — 같은 내용)
- 대사·이름·글꼴: `tools/build_text.py`
- 그림 글자: `tools/gfx_equip.py`(장비 화면) · `tools/gfx_title.py`(타이틀 훈독) · `tools/gfx_poem.py`·`tools/gfx_end.py`(엔딩 영상, `tools/mov_enc.py` 로 다시 부호화)
- 빌드 `tools/build.py` → 배포 `tools/make_dist.py`
- 조사·결정 기록: `docs/00_초기조사.md`
