"""
言知·DSL 宏工厂
将言律句式模板编译为可复用的宏定义。
用户可以在代码中「启用 削峰填谷 策略」。
"""
from typing import Dict
from ..compiler.expander import MacroExpander
from ..compiler.ast import MacroDef, Define, Ident, Call, If, Block, Program, Bool, Num
from ..compiler.lexer import Lexer
from ..compiler.parser import Parser


# 内置成语模板（合法的言知代码）
# 注意：
#   - 参数名之间须有空格分隔，以免合并为一个标识符
#   - 宏体内每个语句的句号（。）被 parse_statement 消费后，
#     还需一个外层句号供定语句的 parse_define 消费
IDIOM_REGISTRY = {
    '削峰填谷': (
        '定 削峰填谷 = 宏 源 峰值阈值 谷值阈值 ：'
        '若 源 大 峰值阈值 则 限流(源) '
        '否则 若 源 小 谷值阈值 则 补流(源) '
        '否则 源 。'
        '。'
    ),
    '守株待兔': (
        '定 守株待兔 = 宏 触发条件 动作 ：'
        '当 真 ： 若 触发条件 则 动作 否则 等待(100) 。 结束 。'
        '。'
    ),
    '温升火急': (
        '定 温升火急 = 宏 传感器 阈值 动作 ：'
        '当 真 ： 若 传感器读 大 阈值 则 动作 否则 等待(1000) 。 结束 。'
        '。'
    ),
}


def register_idiom(expander, name: str, macro_code: str):
    """将成语模板注册到宏展开器"""
    tokens = Lexer(macro_code).tokenize()
    parser = Parser(tokens)
    program = parser.parse()
    # 查找宏定义（期望第一个语句是 定宏名=宏...）
    if program.statements:
        stmt = program.statements[0]
        if isinstance(stmt, Define) and isinstance(stmt.value, MacroDef):
            macro_def = stmt.value
            macro_def.name = name
            expander.macro_env.set(name, macro_def)


def register_builtins(expander):
    """将所有内置成语注册到宏展开器"""
    for name, code in IDIOM_REGISTRY.items():
        register_idiom(expander, name, code)
