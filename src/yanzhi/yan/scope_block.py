"""
言知·作用域块解析
支持"...的时候：" 语法，定义局部作用域块。

语法：
  回家的时候：
    灯亮。
    空调开。

展开为：
  函():
    灯.亮()
    空调.开()
  ()
"""
from typing import Optional
from ..compiler.ast import ASTNode


def parse_scope_block(tokens: list, pos: int) -> Optional[tuple]:
    """解析作用域块
    
    Args:
        tokens: token 列表
        pos: 当前解析位置
        
    Returns:
        (AST节点, 新位置) 或 None
    """
    # TODO: 实现作用域块解析
    # - 检查是否匹配 "...的时候： 模式
    # - 递归解析作用域内的语句
    # - 返回 Lambda + 函数调用 的 AST 组合
    return None
