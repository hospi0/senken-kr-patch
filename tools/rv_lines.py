import sys, re; sys.argv.append('--check')
import build_text as B, json
err = B.Err(); jp, tr = B.load_tr(); M = json.load(open(B.R + '/data/tsv_map.json', encoding='utf-8')); bad = []
for k, t in M['T'].items():
    ko = tr[k]
    if not ko.strip(): continue
    ls = B.layout(k, t['kind'], jp[k], ko, len(t['ids'][0]), B.BUD[t['kind']] if t['kind'] not in ('알림', '설명') else max([B.BUD[t['kind']]] + [B.kfont_w(B.MSG[i]) for i in t['ids'][0]]), err)
    for x in ls:
        y = x.strip('　 ')
        if re.match(r'(을|를|은|는|의|에|도|로|와|과|가|고|만|까지|부터|에서|에게|라고|다고|면서|니까|지만|으로|이다|했다|한다|해서|하고|합니다|입니다|자야|이야|서)(?=[\s,.!?]|$)', y): bad.append((k, '／'.join(ls)))
    if re.search(r'[가-힣] [,.!?]', ' '.join(ls)): bad.append((k, '부호 앞 공백 ' + '／'.join(ls)))
print(len(bad)); [print(*b) for b in bad]
