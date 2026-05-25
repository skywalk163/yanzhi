import sys
sys.path.insert(0, 'G:/yanzhi/src')

from yanzhi.compiler.pre_tokenizer import PreTokenizer
from yanzhi.compiler.lexer import Lexer
from yanzhi.compiler.parser import Parser

code = '定 fact = 函 n：若 n 等 1 则 1 否则 n 乘 fact $(n-1)。'
print(f'Input: {code}')
print()

tokens = PreTokenizer(code).tokenize()
print('Pre-tokens:')
for t in tokens:
    print(f'  {t}')
print()

lexed = Lexer(tokens).tokenize()
print('Lexed tokens:')
for t in lexed:
    print(f'  {t}')
print()

try:
    ast = Parser(lexed).parse()
    print('Parse OK')
except Exception as e:
    print(f'Parse error: {e}')
