# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, 'G:/yanzhi/src')
from yanzhi.compiler.lexer import lex
from yanzhi.compiler.parser import parse
from yanzhi.runtime.evaluator import Evaluator

code = open('G:/yanzhi/examples/demo.yan', encoding='utf-8').read()
print(f'Running demo ({len(code)} chars)...')
print()

ev = Evaluator()
try:
    ast = parse(lex(code))
    ev.eval(ast)
    print()
    print('=== 全部通过 ===')
except Exception as e:
    import traceback
    traceback.print_exc()
