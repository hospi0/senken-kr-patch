# -*- coding: utf-8 -*-
r"""번역용 TSV 내보내기 (2026-11-24, 하스피 지시) → my files/tsv/senken_*.tsv (UTF-8, 18 KB 단위, 자투리 합침)
  열: id · 종류 · 위치 · 예산 · JP · KO   /  ／ = 줄바꿈, [이름] = 화자(이름표에서 따로 번역, KO 에 안 써도 됨)
  N = 이름표, W = 낱말표, T = 대사, G = 그림·동영상 글자, E = 백업 RAM 안내문.  되넣기용 짝은 data/tsv_map.json
  python tools/export_tsv.py"""
import os, sys, json, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from units import *
LIMIT = 18 * 1024; HEAD = 'id\t종류\t위치\t예산\tJP\tKO\n'
OUT = os.path.join(R, 'my files', 'tsv')
BUD = {'위': 28, '아래': 28, '위·초상': 26, '아래·초상': 26, '가운데': 26, '알림': 28, '설명': 30, '기본': 26}
GARBAGE = {'ｯ]ｻ?'}                                   # 중국어판 찌꺼기(42705)
rs = lambda s: s.rstrip('　 ')
def write(stem, rows):
    files = []; cur = HEAD
    for r in rows:
        line = '\t'.join(r) + '\t\n'
        if len((cur + line).encode('utf-8')) > LIMIT: files.append(cur); cur = HEAD
        cur += line
    files.append(cur)
    if len(files) > 1 and len((files[-2] + files[-1][len(HEAD):]).encode()) <= LIMIT + 400: files[-2] += files[-1][len(HEAD):]; files.pop()
    for i, c in enumerate(files): open(os.path.join(OUT, 'senken_%s_%03d.tsv' % (stem, i + 1)), 'w', encoding='utf-8', newline='\n').write(c)
    print(stem, len(rows), '줄', len(files), '파일', [len(c.encode()) for c in files][-1])
def main():
    os.makedirs(OUT, exist_ok=True); U = units(); M = {'T': {}, 'N': {}, 'W': {}}
    cnt = collections.Counter(u['name'] for u in U if u['name']); order = list(dict.fromkeys(u['name'] for u in U if u['name']))
    etc = []
    for i, n in enumerate(order):
        k = 'N%03d' % (i + 1); M['N'][k] = n; etc.append((k, '이름', '%d회' % cnt[n], '26칸', n[:-1]))
    for i in range(1, 565):
        w = PROG[0x61f54 + 16 * i:0x61f54 + 16 * i + 16].decode('cp932').rstrip()
        if not w: continue
        k = 'W%03d' % i; M['W'][k] = i; kind = '메뉴' if i < 60 and not 35 <= i <= 40 else '인물' if i < 60 else '물건·주문·적·상태'
        etc.append((k, kind, '낱말 %d' % i, '16칸', w))
    rows = {}
    for u in U:
        ls = [rs(l) for l in u['lines']]
        if not ls or (len(ls) == 1 and ls[0] in GARBAGE): continue
        kind = u['kind'] or ('설명' if u['desc'] else '기본')
        jp = ('[%s]' % u['name'][:-1] if u['name'] else '') + '／'.join(ls)
        rows.setdefault((kind, jp), []).append(u)
    out = []
    for n, ((kind, jp), us) in enumerate(rows.items()):
        k = 'T%05d' % (n + 1); body = [[i for i in u['ids'] if i != (u['ids'][0] if u['name'] else None)] for u in us]
        M['T'][k] = {'kind': kind, 'name': us[0]['name'], 'ids': body}
        wid = max([BUD[kind]] + ([W(l) for l in us[0]['lines']] if kind in ('알림', '설명') else []))
        out.append((k, kind, '%d' % body[0][0] + (' 외%d' % (len(us) - 1) if len(us) > 1 else ''), '%d줄·%d칸' % (len(body[0]), wid), jp))
    e = rd('ERROR.TXT'); off = [struct.unpack_from('>H', PROG, 0xd76 + 2 * i)[0] for i in range(35)]
    G = [[0]]
    for a, b in zip(off, off[1:] + [930]): pass
    lines = [e[a:b].decode('cp932') for a, b in zip(off, off[1:] + [930]) if b > a]
    starts = [0, 9, 18, 21, 25, 32]; lines = lines
    misc = []
    for i, a in enumerate(starts):
        seg = lines[a:(starts + [len(lines)])[i + 1]]
        misc.append(('E%02d' % (i + 1), '백업 안내', 'ERROR.TXT', '%d줄·32칸' % len(seg), '／'.join(seg)))
    g = ['頭戴', '披掛', '身穿', '手持', '脚穿', '配帯', '武力', '霊力', '防御', '速さ', '吉運']
    misc += [('G%02d' % (i + 1), '그림', '장비 화면', '2자', s) for i, s in enumerate(g)]
    misc.append(('G12', '그림', 'A5.AVI 엔딩', '', '全劇終'))
    poem = ['李逍遥：翩翩瀟灑美少年／靈島求藥結仙緣／千里崎嶇不辭苦／仗劍江湖為紅顏', '林月如：刁蠻少女貴千金／比武招親動芳心／盼能與君長相隨／結伴江湖俠侶行',
            'お鈴：如花苗女鬼靈精／喜逢君子初嚐情／落花有意結連理／伴月願做一顆星', '趙霊児：仙靈島上別洞天／池中孤蓮伴月眠／一朝風雨落水面／願君拾得惜相憐']
    misc += [('G%02d' % (13 + i), '그림(한시)', 'A6.AVI 엔딩', '4행', s) for i, s in enumerate(poem)]
    write('names_words', etc + misc); write('dlg', out)
    json.dump(M, open(os.path.join(R, 'data', 'tsv_map.json'), 'w', encoding='utf-8'), ensure_ascii=False)
    # 검산: 대사 번호가 빠짐없이 한 번씩
    seen = collections.Counter(i for t in M['T'].values() for b in t['ids'] for i in b); names = {u['ids'][0] for u in U if u['name']}
    miss = [k for k in range(17171) if k not in seen and k not in names]
    print('빠진 번호', [(k, MSG[k]) for k in miss], '중복', sum(v > 1 for v in seen.values()), '대사+이름', len(seen) + len(names))
    print('안내문 줄', len(lines)); [print(r) for r in misc[:6]]
main()
