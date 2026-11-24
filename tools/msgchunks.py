# -*- coding: utf-8 -*-
"""JM.MSG 15묶음 + PROG.BIN 위치표 읽기 (2026-11-24)"""
import struct,sys,os
sys.stdout.reconfigure(encoding='utf-8')
R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
d=open(R+'/work/disc1/PROG.BIN','rb').read(); m=open(R+'/work/disc1/JM.MSG','rb').read()
TH=[0xe6a,0x1d81,0x2c74,0x3b51,0x4313]
t=[struct.unpack_from('>H',d,0x579d4+2*k)[0] for k in range(17300)]
def rng(k):
    return t[k]+65536*sum(k>x for x in TH), t[k+1]+65536*sum(k+1>x for x in TH)
CH=[0,0xbd4a,0xfc7c,0x12427,0x133ef,0x19844,0x1dbd8,0x2cc0f,0x3236a,0x3a9b2,0x3d62f,0x3eab3,0x404fe,0x410a3,0x41ca9]
SEC=[0,0x18,0x20,0x25,0x27,0x34,0x3d,0x5c,0x67,0x78,0x7e,0x81,0x85,0x87,0x89]
SIG=[0x4081,0x8141,0x82b6,0x9764,0x82a2,0x82be,0x8ce3,0x8141,0x816a,0x8145,0x82b1,0x8141,0x4581,0x8bf3,0x82b1]
def raw(k):
    a,b=rng(k); c=max(i for i in range(15) if CH[i]<=a)
    o=SEC[c]*2048+a-CH[c]; return m[o:o+b-a],c
if __name__=='__main__':
    bad=0;out=[]
    n=17171
    prev=-1
    for k in range(n):
        s,c=raw(k)
        try: u=s.decode('cp932')
        except Exception: bad+=1;u='??'+s.hex()
        out.append('%d\t%d\t%s'%(k,c,u))
        if c!=prev: print('묶음',c,k,hex(rng(k)[0]),u, 'sig@%s'%m[SEC[c]*2048+16:SEC[c]*2048+20].hex()); prev=c
    open(R+'/work/msg_raw.tsv','w',encoding='utf-8').write('\n'.join(out))
    print('bad',bad)
    for c in range(15):
        e=SEC[c+1] if c<14 else 151
        ln=(CH[c+1] if c<14 else 0)-CH[c]; b=m[SEC[c]*2048:e*2048]; print(c,(e-SEC[c])*2048,ln,len(b.rstrip(b'\0')))
