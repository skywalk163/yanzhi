# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, 'G:/yanzhi/src')
from yanzhi.compiler.lexer import lex
from yanzhi.compiler.parser import parse
from yanzhi.runtime.evaluator import Evaluator

# Test factorial without $ syntax
code = '定 fact = 函 n：若 n 等 1 则 1 否则 n 乘 fact(n-1)。 印 fact 5。'
print(f'Code: {code}')
print()

ev = Evaluator()
try:
    ast = parse(lex(code))
    result = ev.eval(ast)
    print(f'SUCCESS: 5! = {result}')
except Exception as e:
    import traceback
    traceback.print_exc()
