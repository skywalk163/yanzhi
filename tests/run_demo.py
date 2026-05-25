import sys, os
sys.path.insert(0, 'G:/yanzhi/src')

from yanzhi.compiler.lexer import lex
from yanzhi.compiler.parser import parse
from yanzhi.runtime.evaluator import Evaluator

# Read and parse demo.yan
code = open('G:/yanzhi/examples/demo.yan', encoding='utf-8').read()
print(f'Read {len(code)} chars')

# Check line 28 for $ sign
lines = code.split('\n')
for i, line in enumerate(lines):
    if '$' in line:
        print(f'Line {i+1} has $: {repr(line)}')

# Parse and evaluate
evaluator = Evaluator()
try:
    ast = parse(lex(code))
    evaluator.eval(ast)
    print('\n=== ALL PASS ===')
except Exception as e:
    import traceback
    traceback.print_exc()
