"""
言知·作用域块解析（已迁移至 parser 内置实现）

作用域块语法: <条件> 的时候：<块>

此模块原为独立的 scope_block 解析器，但 parser.py 已内置完整实现:
  - parser.py 第 214 行: 识别 IDENT 以"的时候"结尾的 token
  - parser.py 第 581 行: parse_scope_block() 将作用域块展开为
    Lambda([], Block(...)) 并通过 函数调用() 立即执行

历史:
  - 旧版: 本模块的 parse_scope_block() 是存根（始终返回 None）
  - 现版: 由 parser.parse_scope_block() 完全覆盖

用法:
  回家的时候：
    灯亮。
    空调开。
    # ↓ 等价于
    函数()：灯亮。空调开。。
"""

from typing import Optional, Tuple, List
from ..compiler.pre_tokenizer import Token

# 保留接口以保证向后兼容
def parse_scope_block(tokens: list, pos: int) -> Optional[Tuple[List[Token], int]]:
    """（已弃用）作用域块解析 — 请使用 parser.parse_scope_block()"""
    return None  # 不再使用，由 parser 内置实现
