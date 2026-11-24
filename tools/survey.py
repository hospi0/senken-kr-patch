# -*- coding: utf-8 -*-
import struct,sys,re,collections,os
sys.path.insert(0,os.path.dirname(__file__))
from msgchunks import *
sec=open(R+'/work/disc1/JM.SEC','rb').read()
ops=[struct.unpack_from('>4H',sec,i) for i in range(0,len(sec)-7,8)]
msgs=[raw(k)[0].decode('cp932') for k in range(17171)]
c=collections.Counter(ch for s in msgs for ch in s if ord(ch)<0x80)
print('ASCII',sorted(c.items()))
tok=collections.Counter(re.findall(r'[~$\-\'"()_@#*]\d*',''.join(s+'\n' for s in msgs)));print(tok.most_common(60))
u=[o[1] for o in ops if o[0]==0xffff]; print('ffff',len(u),len(set(u)),sorted(u)==list(range(len(u))))
print('빈 메시지',sum(1 for s in msgs if not s.strip()), '글자수',sum(len(s) for s in msgs),'고유',len(set(msgs)))
print('폭',collections.Counter(sum(1 if ord(c)<128 or 0xff61<=ord(c)<=0xff9f else 2 for c in re.sub(r'[~$]\d+','',s)) for s in msgs).most_common(40))
oc=collections.Counter(o[0] for o in ops);print({hex(k):v for k,v in sorted(oc.items())})
# 대사 스타일별 최대 폭·줄수
st=None;page=0;mx={};ln={}
for o in ops:
    if o[0] in (0x3b,0x3c,0x3d,0x3e): st=hex(o[0])+('P' if o[0] in(0x3c,0x3d) and o[1] else '');page=0
    elif o[0]==0xffff and o[1]<len(msgs):
        s=re.sub(r'[~$]\d+','',msgs[o[1]]);w=sum(1 if ord(c)<128 else 2 for c in s)
        mx.setdefault(st,collections.Counter())[w]+=1; page+=1; ln.setdefault(st,collections.Counter())[page]+=1
    elif o[0]==0x8e: pass
for k in mx: print(k,sorted(mx[k].items())[-6:],max(ln[k]))
# 글꼴
f=open(R+'/work/disc1/JM.FNT','rb').read()
codes=[struct.unpack_from('>H',f,i)[0] for i in range(0,len(f),34)]
def s2j(b):
    h,l=b; h=(h-0x71 if h<=0x9f else h-0xb1)*2+1
    if l>0x7f:l-=1
    if l>=0x9e:h+=1;l-=0x7d
    else:l-=0x1f
    return h<<8|l
W=0x61f54
words=[]
for i in range((0x642a4-W)//16):
    b=d[W+16*i:W+16*i+16]; words.append(b.decode('cp932','replace').rstrip())
open(R+'/work/words.tsv','w',encoding='utf-8').write('\n'.join('%d\t%s'%(i,w) for i,w in enumerate(words)))
print('words',len(words),sum(1 for w in words if w.strip()))
used=collections.Counter()
for s in msgs+words:
    for ch in s:
        b=ch.encode('cp932','replace')
        if len(b)==2: used[s2j(b)]+=1
miss=[hex(x) for x in used if x not in codes]
print('글꼴',len(codes),'본문 사용',len(used),'글꼴에 없음',miss[:20],'안쓰임',len(set(codes)-set(used)))
