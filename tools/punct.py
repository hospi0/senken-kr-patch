# -*- coding: utf-8 -*-
"""전프로젝트 규칙: 문장부호 바로 뒤 공백 1칸(반각·전각) 삭제 (wad-koutetsu punct.py 에서, 2026-11-24)
   제어 코드($NN ~NN)로 쪼갠 조각마다. 2칸 이상 이어진 채움 공백은 둔다."""
import re
PUNCT = ',.!?:;)]}\'"~、。，．！？：；）］｝」』】〉》”’…‥・·～〜♪♥'
_R = re.compile('([' + re.escape(PUNCT) + '])[ 　](?![ 　])')
_SPLIT = re.compile(r'([~$]\d\d)')
def squeeze(t): return ''.join(p if _SPLIT.fullmatch(p) else _R.sub(r'\1', p) for p in _SPLIT.split(t))
