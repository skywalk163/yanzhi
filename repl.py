"""
言知 (Yanzhi) 交互式 REPL (字节码 VM)
启动方式：python repl.py
"""

import sys
sys.path.insert(0, 'G:/yanzhi/src')

from yanzhi.compiler.lexer import lex
from yanzhi.compiler.parser import parse, ParseError
from yanzhi.runtime.compiler_bc import compile_to_bytecode
from yanzhi.runtime.vm import VM

vm = VM()

print()
print('  ╔═══════════════════════════════════════╗')
print('  ║    言知 (Yanzhi) REPL v0.1 (VM)      ║')
print('  ║  输入 退出 或 quit 退出               ║')
print('  ╚═══════════════════════════════════════╝')
print()

while True:
    try:
        line = input('言知> ').strip()
    except EOFError:
        break
    
    if not line:
        continue
    if line in ('退出', 'quit', 'exit'):
        print('再见！')
        break
    
    try:
        tokens = lex(line)
        ast = parse(tokens)
        chunk = compile_to_bytecode(ast)
        result = vm.run(chunk)
        if result is not None:
            print(f'  => {result}')
    except ParseError as e:
        print(f'  语法错误: {e}')
    except Exception as e:
        print(f'  错误: {e}')
