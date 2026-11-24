# -*- coding: utf-8 -*-
r"""A6 엔딩 한시 4장 — 글자 지운 바탕·한글판 만들기 (2026-11-24)
  정지 그림 = 프레임 0·151·252·353(사이는 두 장의 겹침, 끝은 어두워짐). 지우기 = 글자 획 마스크 + cv2 inpaint, 글자 상자 밖 변경 0.
  python tools/gfx_poem.py → work/gfx_preview/엔딩한시.png + work/mov/poem_k.npy"""
import os, sys
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, HERE)
STILL = (0, 151, 252, 353)
BOX = [(10, 8, 124, 166), (12, 10, 128, 168), (6, 6, 122, 162), (162, 8, 284, 168)]       # 원문 글자 상자(x0,y0,x1,y1)
COLS = [[(98, 124, 8, 80), (10, 102, 8, 166)], [(100, 128, 10, 82), (12, 104, 10, 168)], [(96, 122, 6, 62), (6, 98, 6, 162)], [(252, 284, 8, 88), (162, 256, 8, 168)]]   # 실제 글자 칸(이름 세로줄 + 본문)
SCORE = os.path.join(ROOT, 'work', 'mov', 'A6.npz')
TXT = [  # data/tr G13~G16 을 줄로 나눔(글은 그대로, 줄만 나눔)
    ('이소요', ['말쑥하고 멋스러운/미소년', '영도에서 약을 구하다/선연을 맺었네', '천 리 험한 길도/마다하지 않고', '검을 들고 강호로/나선 것은/홍안을 위함이라']),
    ('임월여', ['당돌한 소녀,/귀한 천금 아가씨', '비무초친에 마음이/흔들렸네', '그대와 오래도록/함께하길 바라며', '강호를 동행하는/협려가 되리라']),
    ('아노', ['꽃 같은 묘족 소녀,/영악한 장난꾸러기', '군자를 만나 처음으로/정을 맛보았네', '낙화도 뜻이 있어/연리를 맺으니', '달을 벗하는/별 하나 되길 바라네']),
    ('조영아', ['선령도 위에/별천지가 있어', '연못 속 외로운 연꽃이/달과 잠들었네', '하루아침 비바람에/수면에 떨어졌으니', '그대가 주워 아끼고/어여삐 여기길 바라네'])]
FONT = r'C:\claude\utils\font\gowunbatang'
def stills():
    z = np.load(SCORE); I = list(z['idx']); return [z['rgb'][I.index(n)].copy() for n in STILL]
def check_text():
    import re
    tr = {l.split('\t')[0]: l.rstrip('\n').split('\t')[-1] for l in open(os.path.join(ROOT, 'data', 'tr', 'senken_names_words_003.tsv'), encoding='utf-8')}
    for i, (nm, L) in enumerate(TXT):
        want = tr['G%d' % (13 + i)].replace(' ', ''); got = (nm + ':' + '／'.join(L)).replace('/', '').replace(' ', '')
        assert want == got, (want, got)
def mask(p, i):
    """획 = 어두운 테두리 + 그 안 밝은 칠(위 흰색→아래 분홍). 바탕 추정(3 단계 반복)과의 차이로 판정하고 작은 섬은 메움"""
    box = np.zeros(p.shape[:2], bool)
    for x0, x1, y0, y1 in COLS[i]: box[y0:y1, x0:x1] = True
    bg = cv2.medianBlur(p, 31).astype(np.float32); Y = p.astype(np.float32).mean(2)
    for it in range(4):
        d = np.abs(p.astype(np.float32) - bg).max(2); dark = Y < bg.mean(2) - (26 - 2 * it)
        m = ((d > 30 - 3 * it) | dark) & box
        m = cv2.dilate(m.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0
        m &= box; bg = fill(p, m).astype(np.float32)
    m = (cv2.dilate(m.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0) & box
    n, lab, st, _ = cv2.connectedComponentsWithStats((~m).astype(np.uint8), connectivity=4)
    for k in range(1, n):
        if st[k, 4] < 60: m[lab == k] = True
    return m
def fill(p, m):
    """당기고-밀기: 마스크 밖 화소의 가우시안 가중 평균을 좁은 것부터 넓은 것 순으로 메움(얼룩 경계 없음)"""
    w = (~m).astype(np.float32); out = p.astype(np.float32).copy(); acc = np.zeros_like(out); tot = np.zeros_like(w)
    for s, g in ((1.5, 1.0), (3, .5), (6, .12), (12, .02), (24, .004)):
        ww = cv2.GaussianBlur(w, (0, 0), s); v = cv2.GaussianBlur(out * w[:, :, None], (0, 0), s)
        acc += v * g; tot += ww * g
    r = acc / np.maximum(tot, 1e-6)[:, :, None]
    r = cv2.GaussianBlur(np.where(m[:, :, None], r, out), (0, 0), 1.2)
    out[m] = r[m]; return np.clip(out, 0, 255).astype(np.uint8)
def blank(p, i):
    m = mask(p, i); o = fill(p, m); assert (o[~m] == p[~m]).all(); return o, m
def draw(bg, i, font, size, lead, box, name_size=None, gap=4):
    nm, L = TXT[i]; S = 4; W, H = bg.shape[1] * S, bg.shape[0] * S
    f = ImageFont.truetype(font, size * S); fn = ImageFont.truetype(font, (name_size or size) * S)
    rows = [(nm, fn, 0)]
    for s in L:
        for k, t in enumerate(s.split('/')): rows.append((t, f, 1 if k == 0 else 0))
    fill = Image.new('L', (W, H)); d = ImageDraw.Draw(fill); st = Image.new('L', (W, H)); ds = ImageDraw.Draw(st)
    x0, y0, x1, y1 = box; y = y0
    for r, (t, ff, first) in enumerate(rows):
        if r and first: y += gap
        w = d.textlength(t, font=ff) / S
        if x0 + w > x1: print('  ⛔폭', i, t, round(w), x1 - x0)
        d.text((x0 * S, y * S), t, font=ff, fill=255); ds.text((x0 * S, y * S), t, font=ff, fill=255, stroke_width=S * 5 // 4, stroke_fill=255)
        y += lead + (2 if r == 0 else 0)
    if y > y1 + 4: print('  ⛔높이', i, y, y1)
    rs = lambda m: np.asarray(m.resize((W // S, H // S), Image.BOX)).astype(float)[:, :, None] / 255
    a, b = rs(fill), rs(st); out = bg.astype(float) * (1 - b) + np.array([24, 12, 20]) * b
    out = out * (1 - np.clip(a * 1.15, 0, 1)) + np.array([255, 250, 240]) * np.clip(a * 1.15, 0, 1)
    return np.clip(out, 0, 255).astype(np.uint8)
CFG = dict(font=os.path.join(FONT, 'GowunBatang-Bold.ttf'), size=12, lead=15, gap=3)
KBOX = [(14, 5, 124, 174), (12, 8, 128, 172), (8, 6, 132, 172), (162, 6, 286, 172)]
def make():
    check_text(); out = []
    for i, p in enumerate(stills()):
        b, m = blank(p, i); out.append((p, b, draw(b, i, CFG['font'], CFG['size'], CFG['lead'], KBOX[i], CFG['size'] + 2, CFG['gap'])))
    return out
if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8'); R = make(); sc = 2
    S = Image.new('RGB', (288 * sc * 3 + 8, (180 * sc + 26) * 4)); d = ImageDraw.Draw(S); f = ImageFont.truetype('malgun.ttf', 18)
    for i, t in enumerate(R):
        for k, (im, l) in enumerate(zip(t, ('원본', '글자 지운 바탕', '한글'))):
            S.paste(Image.fromarray(im).resize((288 * sc, 180 * sc), Image.LANCZOS), (k * (288 * sc + 4), i * (180 * sc + 26) + 24)); d.text((k * (288 * sc + 4), i * (180 * sc + 26)), TXT[i][0] + ' — ' + l, font=f, fill='white')
    S.save(os.path.join(ROOT, 'work', 'gfx_preview', '엔딩한시.png')); np.save(os.path.join(ROOT, 'work', 'mov', 'poem_k.npy'), np.stack([t[2] for t in R])); np.save(os.path.join(ROOT, 'work', 'mov', 'poem_b.npy'), np.stack([t[1] for t in R]))
