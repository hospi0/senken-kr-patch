import os, sys, re, json, collections
sys.stdout.reconfigure(encoding='utf-8')
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
g = json.load(open(R + '/work/review/' + os.environ.get('RV', 'raw.json'), encoding='utf-8'))
def cls(s):
    s = re.sub(r'[.!?…·・~\s」”"\'\d$()～]+$', '', s)
    if not s: return None
    if re.search(r'(니다|니까|십시오|시지요|소서|옵니다)$', s): return '합쇼'
    if re.search(r'(요|죠|지요)$', s): return '해요'
    if re.search(r'(하오|이오|시오|겠소|었소|았소|했소|없소|있소|구려|이외다|리다|는가|던가|은가|인가|나그려|소이다|라오|다오|[가-힣]소)$', s): return '하오/하게'
    if re.search(r'(하게|하네|이네|구먼|구만|게나|세나|일세|로세|겠네|었네|았네)$', s): return '하오/하게'
    return '반말'
def sents(ko):
    t = re.sub(r'^\[[^\]]*\]', '', ko).replace('／', ' '); t = re.sub(r'[~$]\d\d', '', t)
    return [x for x in re.split(r'(?<=[.!?…])[\s]*|(?<=・)\s+', t) if re.search('[가-힣]', x)]
if __name__ == '__main__':
    files = {}; n = 0
    import glob
    for f in sorted(glob.glob(R + '/work/review/in/senken_dlg*')):
        for l in open(f, encoding='utf-8'): files[l.split('\t')[0]] = int(re.search(r'dlg_(\d+)', f).group(1))
    S = collections.defaultdict(lambda: collections.Counter()); FS = collections.defaultdict(lambda: collections.defaultdict(collections.Counter))
    for k, v in g.items():
        if k[0] != 'T': continue
        m = re.match(r'\[([^\]]*)\]', v[3])
        if not m: continue
        for s in sents(v[4]):
            c = cls(s)
            if c: S[m.group(1)][c] += 1; FS[m.group(1)][files[k]][c] += 1
    for n, c in sorted(S.items(), key=lambda x: -sum(x[1].values()))[:60]:
        if sum(c.values()) < 12: continue
        print(n, dict(c.most_common()))
    for n in ('林月如', '趙霊児', 'お鈴', '李逍遥'):
        print(n); print('  ', {f: dict(c) for f, c in sorted(FS[n].items())})
