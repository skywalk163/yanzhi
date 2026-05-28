# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, 'G:/yanzhi/src')
from yanzhi.compiler.lexer import lex
from yanzhi.compiler.parser import parse

code = open('G:/yanzhi/examples/demo.yan', encoding='utf-8').read()
lines = code.strip().split('\n')
print(f'Total: {len(lines)} lines')
print()

# Run each line individually through lex+parse
for i, line in enumerate(lines, 1):
    s = line.strip()
    if not s or s.startswith('#'):
        continue
    try:
        ast = parse(lex(s))
        print(f'  L{i:2d}: OK   {s}')
    except Exception as e:
        msg = str(e).split('\n')[0]
        print(f'  L{i:2d}: FAIL {msg}')
        print(f'         CODE: {s}')
        break
