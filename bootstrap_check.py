"""
言知自举验证脚本
测试 selfhost/lexer.yan 和 parser.yan 的结构完整性
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from yanzhi.compiler.lexer import lex
from yanzhi.compiler.parser import parse


def verify_selfhost(filepath: str, name: str) -> bool:
    """验证自举文件能否被当前编译器正确解析"""
    print(f"验证: {name}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        source = f.read()
    
    # 1. 词法分析
    try:
        tokens = lex(source)
        print(f"  [OK] 词法分析: {len(tokens)} tokens")
    except Exception as e:
        print(f"  [FAIL] 词法分析: {e}")
        return False
    
    # 2. 语法分析
    try:
        ast = parse(tokens)
        print(f"  [OK] 语法分析: AST 创建成功, {len(ast.statements)} 条语句")
    except Exception as e:
        print(f"  [FAIL] 语法分析: {e}")
        return False
    
    return True


if __name__ == '__main__':
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    
    print("=" * 60)
    print("  言知自举验证")
    print("=" * 60)
    
    base = os.path.dirname(os.path.abspath(__file__))
    
    lexer_path = os.path.join(base, 'src', 'yanzhi', 'selfhost', 'lexer.yan')
    lexer_ok = verify_selfhost(lexer_path, "自举词法分析器")
    
    parser_path = os.path.join(base, 'src', 'yanzhi', 'selfhost', 'parser.yan')
    parser_ok = verify_selfhost(parser_path, "自举语法分析器")
    
    print()
    print("Python 版词法分析 (作为参考):")
    test_source = '定义 x=5 相加 3。'
    for t in lex(test_source):
        print(f"  {t}")
    
    print()
    if lexer_ok and parser_ok:
        print("状态: OK - 两个自举文件均可被当前编译器解析")
    else:
        print(f"状态: 需重写 - lexer={'OK' if lexer_ok else 'FAIL'}, parser={'OK' if parser_ok else 'FAIL'}")
        print("自举文件使用旧单字关键字(定/函/若/列/印等)，需要迁移到双字关键字系统。")
