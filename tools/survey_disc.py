import sys,os
sys.path.insert(0,os.path.dirname(__file__))
from msgchunks import *
import collections
nor=open(R+'/work/disc1/JM.NOR','rb').read()
o=[struct.unpack_from('>4H',nor,i) for i in range(0,len(nor)-7,8)]
u=[x[1] for x in o if x[0]==0xffff]; print('NOR',len(o),len(u),min(u),max(u),sorted(u)==list(range(min(u),max(u)+1)))
for x in o[:12]: print([hex(v) for v in x])
# 파일 사이 빈 섹터
from iso import Disc
D=Disc(1); fs=sorted((l,(s+2047)//2048,p) for p,l,s in D.files if l<132550)
end=0
for l,n,p in fs:
    if l-end>0: print('틈',end,l-end,'→',p)
    end=l+n
print('끝',end,'트랙 섹터',os.path.getsize(r'C:/claude/roms/ss/Senken Kigyouden (Japan)/Senken Kigyouden (Japan) (Track 01).bin')//2352)
