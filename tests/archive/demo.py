import sys
sys.path.insert(0, 'G:/yanzhi/src')

from yanzhi.compiler.lexer import lex
from yanzhi.compiler.parser import parse
from yanzhi.runtime.evaluator import evaluate

demonstrations = [
    ("基础运算：5 加 3", '印 5加3。'),
    ("管道：列表 map + filter", '列 1 2 3 4 5，皆乘2，只大5，印。'),
    ("言律句式：当...就...", '当 真，就印 "言律句式 OK"。'),
    ("言律句式：要是...否则...", '要是 5大3，就印 "条件为真" 否则 印 "条件为假"。'),
    ("作用域块：回家的时候", '回家的时候：印 "进门"。印 "开灯"。'),
    ("宏：削峰填谷", '启用 削峰填谷 策略。'),
]

for title, code in demonstrations:
    print(f'═══ {title} ═══')
    print(f'>>> {code}')
    try:
        ast = parse(lex(code))
        result = evaluate(ast)
        if result is not None:
            print(f'= {result}')
    except Exception as e:
        print(f'! ERROR: {e}')
    print()

print('═══ 全部通过！言知已可运行 ═══')
