import sys; from rv_tone import *
BAN = re.compile(r'(한다|간다|이다|었다|았다|겠다|했다|였다|는다|없다|있다|같다|싶다|좋다|거야|이야|잖아|있어|없어|했어|었어|았어|겠어|같아|싶어|알아|몰라|구나|는군|겠군|군|냐|느냐|려무나|거라|아라|어라|마라|해라|하자|가자|줘|해줘|돼|안 돼|할게|줄게|을게|걸|는데|던데|거든|야|해|지|니|네)$')
def ban(s):
    t = re.sub(r'[.!?…·・~\s」”"\'\d$()～]+$', '', s)
    return len(re.findall('[가-힣]', t)) >= 4 and bool(BAN.search(t)) and not re.search(r'(에|에게|까지|처럼|데|지만|는데|그리고|하지|설마|어디|언제|정말|아마|절대|역시|글쎄|그렇지|아니|겠지|네)$', t)
out = []
for k, v in g.items():
    if k[0] != 'T': continue
    ss = sents(v[4]); cs = [cls(s) for s in ss]
    pol = [s for s, c in zip(ss, cs) if c in ('합쇼', '해요')]; b = [s for s, c in zip(ss, cs) if c == '반말' and ban(s)]
    if pol and b: out.append((k, v[3], v[4], pol, b))
print(len(out))
for k, jp, ko, p, b in out: print(k, '|', re.sub('／', '', jp)[:150], '|', ko.replace('／', ' ')[:260])
