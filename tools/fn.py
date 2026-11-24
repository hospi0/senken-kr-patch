# -*- coding: utf-8 -*-
"""PROG.BIN(0x06020000) 함수 통째 역어셈블 — python tools/fn.py 주소 [끝주소]  (풀 상수 값 같이 찍음)"""
import sys,struct,re,os
sys.stdout.reconfigure(encoding='utf-8')
HERE=os.path.dirname(os.path.abspath(__file__)); ns={}
exec(open(HERE+'/sh2_disasm.py',encoding='utf-8').read().split("if __name__")[0],ns)
d=open(HERE+'/../work/disc1/PROG.BIN','rb').read(); B=0x6020000
a=int(sys.argv[1],16); n=(int(sys.argv[2],16)-a)//2 if len(sys.argv)>2 else 400
for ad,w,t in ns['disasm_sh2'](d[a-B:a-B+2*n],ad if False else a,n):
    m=re.search(r';@0x(\w+)',t)
    if m:
        x=int(m.group(1),16)-B
        if 0<=x<len(d)-4: t=t.split(';@')[0]+('= %08X'%struct.unpack_from('>I',d,x)[0] if 'MOV.L' in t else '= %04X'%struct.unpack_from('>H',d,x)[0])
    print('%08X %04X %s'%(ad,w,t))
    if len(sys.argv)<=2 and w==0x000B and ad-a>8:
        break
