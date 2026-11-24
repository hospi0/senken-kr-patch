# -*- coding: utf-8 -*-
r"""번역 TSV → 게임 파일(메모리 안에서만) : PROG.BIN · JM.MSG · JM.SEC · JM.NOR · JM.FNT · ASCFONT.15 · ERROR.TXT (2026-11-24)
  번역 = data/tr/*.tsv (있으면) 아니면 my files/tsv/*.tsv — 열 id·종류·위치·예산·JP·KO, KO 빈칸 = 원문 그대로.
  조판: 부호 뒤 공백 삭제 → ／ 가 폭 안이면 그대로, 아니면 낱말 단위로 다시 나눔(대사창). 줄이 늘면 마지막 대사 명령에 «추가 줄 수»를 적어 이어 찍음(tools/hook_lines.py).
  오류(글꼴에 없는 글자·토큰 다름·폭 넘침·용량 넘침)가 하나라도 있으면 빌드 중단.
  python tools/build_text.py --check   → 검사만(파일 안 씀)"""
import os, sys, re, json, glob, struct, collections, bisect
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import kfont, getmsg, hook_lines
from units import R, OPS, MSG, NB, PROG, units, rd
from punct import squeeze

BUD = {'위': 28, '아래': 28, '위·초상': 26, '아래·초상': 26, '가운데': 28, '알림': 28, '설명': 30, '기본': 26}
FLOW = {'위', '아래', '위·초상', '아래·초상', '기본', '가운데'}             # 줄 다시 나누기·줄 늘리기가 되는 창
CH0 = [0, 2686, 3636, 4255, 4502, 5941, 7001, 10592, 11904, 13874, 14547, 14872, 15260, 15433, 15609]   # 원본 대사 묶음의 첫 번호
CAP_STORY, CAP_ITEM, MSG_SECT = 63488, 28672, 151
TOK = re.compile(r'[~$]\d\d')
CTRL = re.compile(r'[~$]\d\d|[()"]')                                        # 폭 0 제어
FULL = {'！': '!', '？': '?', '。': '.', '．': '.', '、': ',', '，': ',', '％': '％', '　': '  ', '：': '：', ':': '：', '；': ';', '·': '・', '･': '・',
        '～': '～', '〜': '～', '—': 'ー', '―': 'ー', '…': '...', '‥': '..', '『': '「', '』': '」', '’': "'", '‘': "'", '／': '／'}
FULL.update({chr(0xFF10 + i): chr(0x30 + i) for i in range(10)})
FULL.update({chr(0xFF21 + i): chr(0x41 + i) for i in range(26)}); FULL.update({chr(0xFF41 + i): chr(0x61 + i) for i in range(26)})
SHEET = {'시스템': None}


class Err(list):
    def add(self, k, why, s=''): self.append((k, why, s))


# ── 번역 읽기 ─────────────────────────────────────────────
def load_tr():
    d = os.environ.get('TRDIR') or os.path.join(R, 'data', 'tr')
    fs = sorted(glob.glob(d + '/*.tsv')) or sorted(glob.glob(os.path.join(R, 'my files', 'tsv', '*.tsv')))
    tr = {}; jp = {}
    for f in fs:
        for ln in open(f, encoding='utf-8-sig').read().replace('\r', '').split('\n'):
            c = ln.split('\t')
            if len(c) < 5 or not re.fullmatch(r'[NWTGE]\d+', c[0]): continue
            assert c[0] not in jp, ('id 두 번', c[0], f)
            jp[c[0]] = c[4]; tr[c[0]] = (c[5] if len(c) > 5 else '').strip('\n')
    return jp, tr


def norm(s, src=''):
    """글꼴에 있는 글자로 바꾸고 제어 글자를 지킴. 반각 ( ) " 는 원문에 같은 수만큼 있을 때만 제어로 본다."""
    s = re.sub('・{2,}', lambda m: '.' * len(m.group()), s)
    for a, b, w in (('(', ')', '（）'),):
        if s.count(a) + s.count(b) != src.count(a) + src.count(b): s = s.replace(a, w[0]).replace(b, w[1])
    if s.count('"') != src.count('"'):
        n = [0]
        def q(_): n[0] += 1; return '“' if n[0] % 2 else '”'
        s = re.sub('"', q, s)
    s = ''.join(FULL.get(ch, ch) for ch in s)
    parts = re.split(r'([~$]\d\d)', s)
    s = ''.join(p if TOK.fullmatch(p) else p.replace('~', '～') for p in parts)
    return squeeze(s)


def W(s): return sum(1 if ord(c) < 128 else 2 for c in CTRL.sub('', s))


def wrap(text, width):
    """낱말 단위 최소 줄 수 → 같은 줄 수에서 고른 나눔(DP). 부호 뒤도 끊는 자리."""
    words = []
    for w in text.split(' '):
        if w == '': continue
        ps = re.split(r'(?<=[,.!?…])(?=[^,.!?…」”)~$ ])', w)
        for j, p in enumerate(ps): words.append((p, j > 0))                 # (낱말, 앞 낱말에 붙음)
    n = len(words); INF = 10 ** 9; best = [(INF, INF, 0)] * (n + 1); best[n] = (0, 0, n)
    for i in range(n - 1, -1, -1):
        cur = ''
        for j in range(i, n):
            cur += words[j][0] if j == i or words[j][1] else ' ' + words[j][0]
            w = W(cur)
            if w > width: break
            l, c, _ = best[j + 1]
            cost = c + (0 if j + 1 == n else (width - w) ** 2)
            if (l + 1, cost) < best[i][:2]: best[i] = (l + 1, cost, j + 1)
    if n and best[0][0] >= INF: return None
    out = []; i = 0
    while i < n:
        j = best[i][2]; cur = ''
        for k in range(i, j): cur += words[k][0] if k == i or words[k][1] else ' ' + words[k][0]
        out.append(cur); i = j
    return out or ['']


def join_lines(ls):
    out = ''
    for x in ls:
        x = x.strip(' 　')
        out += x if not out or x[:1] in '.,!?' else ' ' + x            # 점·부호로 시작하는 줄은 앞에 붙임
    return out


def layout(tid, kind, jp, ko, n, width, err):
    """→ 줄 목록. 대사창은 줄이 n 을 넘을 수 있음(뒤에서 자리를 빌림)."""
    src = re.sub(r'^\[[^\]]*\]', '', jp); ko = re.sub(r'^\[[^\]]*\]', '', ko)
    if TOK.findall(src) != TOK.findall(ko): err.add(tid, '제어 코드가 원문과 다름 %s ≠ %s' % (TOK.findall(ko), TOK.findall(src)), ko)
    if '$' in TOK.sub('', ko): err.add(tid, '반각 $', ko)
    lines = [norm(x, '') if '(' not in src and '"' not in src else x for x in ko.split('／')]
    if '(' in src or '"' in src or ')' in src: lines = norm(ko, src).split('／')
    lines = [x.rstrip(' ') for x in lines]
    mid = any('~' in x for x in src.split('／')[:-1])
    if len(lines) <= n and all(W(x) <= width for x in lines): return lines
    if kind in FLOW and not mid:
        out = wrap(squeeze(join_lines(lines)), width)
        if out is None: err.add(tid, '한 낱말이 창 폭(%d칸)보다 김' % width, ko); return lines
        return out
    over = [x for x in lines if W(x) > width]
    if over:
        out = None if mid else wrap(squeeze(join_lines(lines)), width)
        if out and len(out) <= n: return out
        err.add(tid, '%s 폭 %d칸 넘음(%d칸)' % (kind, width, max(W(x) for x in over)), ko)
    if len(lines) > n: err.add(tid, '%s 줄 수 %d > %d' % (kind, len(lines), n), ko)
    return lines


# ── 글자 → 바이트 ─────────────────────────────────────────
class Enc:
    def __init__(self, texts, err):
        self.err = err; need = set()
        for s in texts: need |= {c for c in s if '가' <= c <= '힣'}
        self.m = kfont.assign(need, save='--check' not in sys.argv); self.slots = kfont.slots()
    def __call__(self, k, s, raw=False):
        if raw: return s.encode('cp932')                                    # 아직 번역 안 된 원문
        out = b''
        for c in s:
            if ord(c) < 0x80: out += c.encode()
            elif c in self.m: out += self.slots[self.m[c]][1]
            else:
                try: b = c.encode('cp932')
                except UnicodeEncodeError: b = b''
                if b in kfont.KEEP: out += b
                else: self.err.add(k, '글꼴에 없는 글자 «%s»' % c, s); out += b'?'
        return out


def main(check=True):
    sys.stdout.reconfigure(encoding='utf-8')
    err = Err(); jp, tr = load_tr(); M = json.load(open(os.path.join(R, 'data', 'tsv_map.json'), encoding='utf-8'))
    done = sum(bool(v.strip()) for v in tr.values()); print('번역 %d / %d 행' % (done, len(tr)))
    names = {}
    for k, n in M['N'].items():
        ko = norm(tr.get(k, '').strip(' ').rstrip('：:'))
        if ko and W(ko) > 24: err.add(k, '이름 24칸 넘음', ko)
        names[n] = (ko + '：', False) if ko else (n, True)                   # (글, 원문 그대로?)
    words = {}
    for k, i in M['W'].items():
        ko = norm(tr.get(k, '').strip(' '))
        if not ko: continue
        if W(ko) > 16: err.add(k, '낱말 16칸 넘음(%d)' % W(ko), ko)
        words[i] = ko.replace(' ', chr(0x7F))                                   # 이름 폭 재는 코드 4곳(0x604B8A4 등)이 0x20 에서 멈춤 → 안쪽 공백은 빈 글자 0x7F(kfont.build_asc 가 비움)
    trans = {}                                                              # T id → 줄 목록(또는 None)
    for k, t in M['T'].items():
        ko = tr.get(k, '')
        if not ko.strip(): continue
        n = len(t['ids'][0]); kind = t['kind']; wd = BUD[kind]
        if kind in ('알림', '설명'): wd = max([wd] + [kfont_w(MSG[i]) for i in t['ids'][0]])
        ls = layout(k, kind, jp[k], ko, n, wd, err)
        if kind == '알림': ls = [x + ' ' if W(x) % 2 else x for x in ls]      # 상자 크기·가운데 맞춤이 전각 칸 기준
        trans[k] = ls
    # 대사 번호(첫 본문) → T
    first = {}
    for k, t in M['T'].items():
        for ids in t['ids']: first[ids[0]] = k
    U = units(); ops = [list(o) for o in OPS]
    texts = [s for ls in trans.values() for s in ls] + [n for n, r in names.values() if not r] + list(words.values())
    errtxt = {k: tr.get(k, '') for k in tr if k[0] == 'E' and tr[k].strip()}
    texts += [norm(v, jp[k]) for k, v in errtxt.items()]
    enc = Enc(texts, err)

    # ── 1) 말 단위마다 새 줄 배치 ──
    plan = []; grown = 0                                                     # (명령, 원래 번호, ((글, 원문?), …))
    for u in U:
        body_ops = u['ops'][1:] if u['name'] else u['ops']; body_ids = u['ids'][1:] if u['name'] else u['ids']
        if u['name']: plan.append((u['ops'][0], u['ids'][0], (names[u['name']],)))
        k = first.get(body_ids[0]) if body_ids else None
        ls = trans.get(k) if k else None
        if ls is None:
            for o, i in zip(body_ops, body_ids): plan.append((o, i, ((MSG[i], True),)))
            continue
        ls = [x if x else ' ' for x in ls]; N = len(body_ops)
        for o, i, s in zip(body_ops, body_ids, ls[:N - 1] if len(ls) > N else ls): plan.append((o, i, ((s, False),)))
        if len(ls) > N: plan.append((body_ops[-1], body_ids[-1], tuple((s, False) for s in ls[N - 1:]))); grown += 1
        for j, o in enumerate(body_ops[len(ls):]):                           # 남는 명령: 첫 칸 = 다음 명령으로 건너뜀
            nxt = body_ops[-1] + 1
            ops[o] = [0, 0, 0, 0] if u['desc'] and ops[nxt][0] == 0 else [3, nxt, 0, 0] if j == 0 else [0, 0, 0, 0]
    print('줄 늘린 말 %d' % grown)

    # ── 3) 묶음별 번호·본문 ──
    CHUNK = [dict() for _ in range(15)]                                      # (글, 원문?) → 순번
    by = [[] for _ in range(15)]
    for o, i, t in plan: by[bisect.bisect_right(CH0, i) - 1].append((o, t))
    firstid = []; ends = []; sect = []; nsec = []; blob = b''; table = []; msgs = []
    for c in range(15):
        firstid.append(len(table)); head = b'\0' * 16 + struct.pack('>H', 0xFE00 + c); body = bytearray(head)
        order = {}
        for o, t in sorted(by[c], key=lambda x: (-len(x[1]), x[0])):          # 여러 줄짜리를 먼저(번호가 이어져야 함)
            if t not in order:
                for j, line in enumerate(t):
                    order.setdefault(t[j:], len(table) - firstid[c])          # 뒤쪽 꼬리도 나눠 씀
                    b = enc('대사', *line); table.append(len(body)); msgs.append(b); body += b
            ops[o] = [0xFFFF, firstid[c] + order[t], len(t) - 1, 0]
        assert len(body) < 65536, ('묶음 64KB 넘음', c)
        ends.append(len(body)); sect.append(len(blob) // 2048); nsec.append((len(body) + 2047) // 2048)
        cap = CAP_ITEM if c == 14 else CAP_STORY
        if nsec[c] * 2048 > cap: err.add('묶음%d' % c, '용량 %d > %d' % (len(body), cap))
        blob += bytes(body) + b'\0' * (-len(body) % 2048)
    print('줄 %d / %d · JM.MSG %d / %d 섹터 · 아이템 묶음 %d / %d B · 가장 큰 묶음 %d B' % (len(table), getmsg.MAXID, len(blob) // 2048, MSG_SECT, ends[14], CAP_ITEM, max(ends[:14])))
    if len(table) > getmsg.MAXID: err.add('위치표', '대사 줄 %d > %d' % (len(table), getmsg.MAXID))
    if len(blob) > MSG_SECT * 2048: err.add('JM.MSG', '%d 섹터 > %d' % (len(blob) // 2048, MSG_SECT))
    blob = blob.ljust(MSG_SECT * 2048, b'\0')

    # ── 4) PROG.BIN ──
    p = bytearray(PROG)
    code = getmsg.build(firstid, ends, sect, nsec, len(table)); o = getmsg.ORG - 0x6020000; p[o:o + len(code)] = code
    tb = struct.pack('>%dH' % len(table), *table[:getmsg.MAXID]) if len(table) <= getmsg.MAXID else b''
    p[0x579D4:0x579D4 + 2 * getmsg.MAXID] = tb.ljust(2 * getmsg.MAXID, b'\0')
    for i, s in words.items():
        b = enc('W%03d' % i, s); p[0x61F54 + 16 * i:0x61F54 + 16 * i + 16] = b.ljust(16)[:16]
    hook_lines.apply(p)
    ertxt = build_error(p, errtxt, jp, enc, err)
    sec = b''.join(struct.pack('>4H', *x) for x in ops[:NB]); nor = b''.join(struct.pack('>4H', *x) for x in ops[NB:])
    assert len(sec) == len(rd('JM.SEC')) and len(nor) == len(rd('JM.NOR')) and len(p) == len(PROG)
    files = {'PROG.BIN': bytes(p), 'JM.MSG': blob, 'JM.SEC': sec, 'JM.NOR': nor, 'JM.FNT': kfont.build_fnt(enc.m), 'ASCFONT.15': kfont.build_asc(), 'ERROR.TXT': ertxt}
    # ── 5) 검산 ──
    verify(files, ops, msgs, firstid, sect, nsec, enc, err, U, plan)
    if err:
        out = os.path.join(R, 'work', 'build_errors.tsv'); open(out, 'w', encoding='utf-8').write('\n'.join('\t'.join(map(str, e)) for e in err))
        print('★오류 %d건 → %s' % (len(err), out))
        for w, n in collections.Counter(re.sub(r'[«\[].*|\d+', '', e[1]) for e in err).most_common(10): print('   ', n, w)
        for e in err[:12]: print('   ', e)
    else: print('오류 0 · 글꼴 음절 %d / %d 칸' % (len(enc.m), len(kfont.slots())))
    return files, err


def kfont_w(s): return W(s.rstrip('　 '))


def build_error(p, errtxt, jp, enc, err):
    """ERROR.TXT + 줄 위치표(PROG 0xD76 u16×35). «＊＊» 줄(27번째)은 게임이 앞 토막·숫자 4칸·뒤 토막을 따로 찍는다(코드 상수)."""
    e = rd('ERROR.TXT'); off = [struct.unpack_from('>H', PROG, 0xD76 + 2 * i)[0] for i in range(35)]
    lines = [e[a:b] for a, b in zip(off, off[1:])]
    starts = [0, 9, 18, 21, 25, 32, 34]
    for k, v in errtxt.items():
        n = int(k[1:]) - 1; a, b = starts[n], starts[n + 1]; ls = norm(v, jp[k]).split('／')
        if len(ls) > b - a or any(W(x) > 34 for x in ls):
            flat = wrap(squeeze(' '.join(ls)), 34) if '＊＊' not in v else None
            if not flat or len(flat) > b - a: err.add(k, '안내문 %d줄·34칸 넘음' % (b - a), v); continue
            ls = flat
        ls += [' '] * (b - a - len(ls))
        if n == 4:
            if '＊＊' not in ls[1]: err.add(k, '＊＊ 는 둘째 줄에 있어야 함', v); continue
        for i, x in enumerate(ls):
            lines[a + i] = enc(k, x.replace('＊＊', '')) if '＊＊' in x else enc(k, x)
            if '＊＊' in x:
                pre, post = x.split('＊＊'); lines[a + i] = enc(k, pre) + '＊＊'.encode('cp932') + enc(k, post)
                star = (enc(k, pre), enc(k, post), W(pre), W(post))
        if n == 4: p_star = star
    out = b''; pos = []
    for x in lines: pos.append(len(out)); out += x
    pos.append(len(out))
    for i, v in enumerate(pos): struct.pack_into('>H', p, 0xD76 + 2 * i, v)
    if 'E05' in errtxt and 'p_star' in locals():
        pre, post, wp, wq = p_star; a = pos[26]
        # 0x06021CBE: 앞 토막(0x002002BE, 길이 6, x 40) · 숫자(길이 4, x 80) · 뒤 토막(0x002002C8, 길이 0x16, x 120)
        lit = [i for i in range(0x1CBE, 0x1F00, 2) if struct.unpack_from('>I', PROG, i)[0] in (0x2002BE, 0x2002C8)]
        assert len(lit) == 2, lit
        for i in lit: struct.pack_into('>I', p, i, 0x200000 + (a if struct.unpack_from('>I', PROG, i)[0] == 0x2002BE else a + len(pre) + 4))
        def imm(addr, old, new):
            o = addr - 0x6020000; assert p[o + 1] == old, (hex(addr), hex(p[o + 1])); assert 0 <= new < 128, new; p[o + 1] = new
        x1 = 40 + 8 * wp; x2 = x1 + 32                                        # 숫자 4자리 = 32px
        imm(0x06021CC0, 6, len(pre)); imm(0x06021CE2, 0x16, len(post)); imm(0x06021CD8, 0x50, x1); imm(0x06021CE8, 0x78, x2)
    assert len(out) <= 2048
    return out


def verify(files, ops, msgs, firstid, sect, nsec, enc, err, U, plan):
    """되읽기: 스크립트를 따라가며 화면에 찍힐 줄이 계획과 같은지, 새 루틴이 그 줄을 돌려주는지"""
    p = files['PROG.BIN']; total = len(msgs)
    def text(i):
        c = bisect.bisect_right(firstid, i) - 1; a = struct.unpack_from('>H', p, 0x579D4 + 2 * i)[0]
        return files['JM.MSG'][sect[c] * 2048 + a:][:len(msgs[i])]
    want = {o: [enc('검산', *x) for x in t] for o, i, t in plan}
    for o, w in want.items():
        if ops[o][0] != 0xFFFF or ops[o][2] != len(w) - 1 or [text(ops[o][1] + j) for j in range(len(w))] != w: err.add('검산', '명령 %d 글이 다름' % o); break
    # 점프 따라가기: 단위마다 나온 줄 수·순서
    bad = 0
    for u in U:
        i = u['ops'][0]; end = u['ops'][-1] + 1; got = []; step = 0
        while i != end and step < 200:
            step += 1; o = ops[i]
            if o[0] == 0xFFFF: got += range(o[1], o[1] + 1 + o[2]); i += 1
            elif o[0] == 3 and o[2] == 0: i = o[1]
            elif o[0] == 0 and u['desc']: break
            else: bad += 1; err.add('검산', '단위 %d 흐름 이상(명령 %d = %s)' % (u['ops'][0], i, o)); break
        exp = [b for x in u['ops'] if x in want for b in want[x]]
        if [text(x) for x in got] != exp: err.add('검산', '단위 %d 나온 줄이 계획과 다름' % u['ops'][0])
        if step >= 200: err.add('검산', '단위 %d 무한 흐름' % u['ops'][0])
    same = sum(1 for a, b in zip(ops, OPS) if list(a) == list(b)); other = [i for i, (a, b) in enumerate(zip(ops, OPS)) if b[0] != 0xFFFF and list(a) != list(b)]
    if other: err.add('검산', '대사 아닌 명령이 바뀜 %s' % other[:5])
    if len(msgs) <= getmsg.MAXID:
        b, n = getmsg.selftest(p, files['JM.MSG'], msgs, firstid, sect, nsec)
        print('루틴 흉내 %d회 · 다름 %d' % (n, len(b)))
        if b: err.add('루틴', str(b[0])[:300])
    b = hook_lines.selftest(p)
    if b: err.add('줄 이어찍기', str(b[0]))
    # 글자 찾기 코드(0x06052504)로 배정 칸 전부 확인
    import sh2sim
    fnt = files['JM.FNT']; wrong = []
    chk = {enc.slots[k][1]: (enc.slots[k][0], c) for c, k in enc.m.items()}; chk.update({b: (i, '부호') for b, i in kfont.KEEP.items()})
    for b, (i, c) in chk.items():
        m = sh2sim.Mem(); m.map(0x06020000, p); m.map(0x06010000, bytes(0x10000)); m.map(0x280200, fnt)
        cpu = sh2sim.CPU(m, 0x06052504, {4: b[0], 5: b[1]}, stack_top=0x0601F000); cpu.pr = 0x06000000
        cpu.run(0x06000000)
        if (cpu.r[0] & 0xFFFF) != i: wrong.append((c, b.hex(), i, cpu.r[0] & 0xFFFF))
    print('글자 찾기 흉내 %d자 · 다름 %d' % (len(chk), len(wrong)))
    for w in wrong: err.add('글꼴', '글자 찾기 어긋남 %s' % (w,))
    # 바뀐 범위
    diff = [i for i in range(len(p)) if p[i] != PROG[i]]
    ok = lambda i: 0x31C28 <= i < 0x321A0 or 0x579D4 <= i < 0x579D4 + 2 * getmsg.MAXID or 0x61F54 <= i < 0x642A4 or 0xD76 <= i < 0xD76 + 70 or 0x1CBE <= i < 0x1F00 or 0x55D6 <= i < 0x5602 or 0x5460 <= i < 0x5462
    if any(not ok(i) for i in diff): err.add('검산', 'PROG 허용 밖 변경 %s' % [hex(i) for i in diff if not ok(i)][:5])


if __name__ == '__main__':
    main()
