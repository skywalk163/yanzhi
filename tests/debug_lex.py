# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, 'G:/yanzhi/src')
from yanzhi.compiler.lexer import lex
from yanzhi.compiler.parser import parse

code = '定 fact = 函 n：若 n 等 1 则 1 否则 n 乘 fact $(n-1)。 印 fact 5。'

# Check lex output
tokens = lex(code)
print('Lex output:')
for t in tokens:
    print(f'  {t}')
print()

# Try to parse just the first statement (before the second 。)
first_part = '定 fact = 函 n：若 n 等 1 则 1 否则 n 乘 fact $(n-1)。'
tokens2 = lex(first_part)
print('First statement tokens:')
for t in tokens2:
    print(f'  {t}')
print()

try:
    ast = parse(tokens2)
    print('First statement parse OK')
except Exception as e:
    print(f'Parse error: {e}')
