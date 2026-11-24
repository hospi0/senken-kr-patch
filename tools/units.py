# -*- coding: utf-8 -*-
"""스크립트(JM.SEC·JM.NOR) 순서로 대사를 «말 단위»로 묶기 (2026-11-24)
  단위 = 이어진 0xFFFF 명령. 이름 줄(：로 끝남, 쪽 첫 줄, 가운데·설명창 제외)에서 새로 시작, 점프가 들어오는 줄에서도 끊는다."""
import os, sys, re, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from msgchunks import raw, R, d as PROG
rd = lambda n: open(R + '/work/disc1/' + n, 'rb').read()
sec, nor, idx = rd('JM.SEC'), rd('JM.NOR'), rd('JM.IDX')
OPS = [struct.unpack_from('>4H', sec, i) for i in range(0, len(sec), 8)]; NB = len(OPS)
OPS += [struct.unpack_from('>4H', nor, i) for i in range(0, len(nor), 8)]
MSG = [raw(k)[0].decode('cp932') for k in range(17171)]
JOP = {2: (1,), 3: (1,), 4: (1,), 6: (2,), 7: (2, 3), 0xa: (1,), 0x1e: (2,), 0x20: (3,), 0x24: (2,), 0x25: (2,), 0x58: (3,), 0x61: (2,), 0x64: (2,), 0x68: (1,),
       0x74: (1,), 0x79: (2,), 0x81: (3,), 0x83: (3,), 0x86: (3,), 0x90: (2,), 0x91: (1,), 0x94: (3,), 0x95: (2,), 0x9c: (2,), 0x9e: (2, 3), 0x38: (1,), 0x33: (1,), 0x34: (1,)}
def targets():
    t = {}
    for i, o in enumerate(OPS):
        for k in JOP.get(o[0], ()):
            t.setdefault(o[k], []).append(i)
    for i in range(0, len(idx), 22):
        for k in (3, 4): t.setdefault(struct.unpack_from('>H', idx, i + 2 * k)[0], []).append('E%d' % (i // 22))
    for i in range(0x579d4 - 2400, 0x579d4, 8):          # 장면표 (맵·입장 스크립트·순간이동 스크립트·물체 번호)
        for k in (1, 2): t.setdefault(struct.unpack_from('>H', PROG, i + 2 * k)[0], []).append('S%d' % ((i - 0x579d4 + 2400) // 8))
    return t
W = lambda s: sum(1 if ord(c) < 128 else 2 for c in re.sub(r'[~$]\d\d|[()"]', '', s))
KIND = {0x3b: '가운데', 0x3c: '위', 0x3d: '아래', 0x3e: '알림'}
def units():
    T = targets(); out = []; kind = None; cur = None; desc = False; page = 0
    for i, o in enumerate(OPS):
        if o[0] in KIND:
            kind = KIND[o[0]] + ('·초상' if o[0] in (0x3c, 0x3d) and o[1] else ''); page = 0
        if o[0] != 0xffff:
            cur = None; desc = o[0] == 0xa7
            if o[0] in (0, 1): kind = None
            if o[0] in (5, 0x8e): page = 0
            continue
        s = MSG[o[1]]; jp = i in T
        isname = s.endswith('：') and page == 0 and (kind is None or kind.split('·')[0] in ('위', '아래')) and not desc
        if s.endswith('：') and not desc and kind != '알림' and kind != '가운데' and not isname and cur and len(cur['lines']) % 4 == 0: isname = True   # 쪽 첫 줄 이름
        if cur is None or isname or jp:
            cur = {'ops': [], 'ids': [], 'lines': [], 'name': None, 'kind': kind, 'nor': i >= NB, 'desc': desc, 'start': i, 'jump': jp and OPS[i - 1][0] == 0xffff}
            out.append(cur)
        if isname and not cur['lines']: cur['name'] = s
        else: cur['lines'].append(s)
        cur['ops'].append(i); cur['ids'].append(o[1])
    return out
if __name__ == '__main__':
    import collections
    U = units(); print(len(U), '단위', sum(len(u['lines']) for u in U), '줄', '이름', len(set(u['name'] for u in U)))
    print(collections.Counter((u['kind'], u['nor']) for u in U))
    print('줄 수', sorted(collections.Counter(len(u['lines']) for u in U).items()))
    print('점프 끊김', sum(u['jump'] for u in U))
    for u in [u for u in U if u['jump']][:8]: print(u['start'], MSG[u['ids'][0] - 1], '|', u['lines'][:2])
    for k in (None, '가운데', '알림'):
        print('==', k)
        for u in [u for u in U if u['kind'] == k][:8] + [u for u in U if u['kind'] == k and u['nor']][:5]: print(u['start'], u['name'], u['lines'])
    print(collections.Counter(u['name'] for u in U).most_common(30))
    mid = [u for u in U if u['kind'] and u['kind'] != '알림' and any(l.endswith('：') for l in u['lines'])]; print('본문 속 ：', len(mid), [u['lines'] for u in mid[:6]])
    print('이름만', sum(1 for u in U if u['name'] and not u['lines']))
