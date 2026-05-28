# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, 'G:/yanzhi/src')
from yanzhi.compiler.lexer import lex
from yanzhi.compiler.parser import parse
from yanzhi.runtime.evaluator import Evaluator

# Minimal test: define with verb call
tests = [
    ('定 a = 加 5 3。', None),
    ('定 data = 列 1 2 3。', None),
    ('"x"，印 data。', None),
]

for code, _ in tests:
    print(f'Testing: {repr(code)}')
    print(f'  Tokens: {lex(code)}')
    try:
        ast = parse(lex(code))
        print(f'  Parse OK')
    except Exception as e:
        print(f'  Parse fail: {e}')
    print()
