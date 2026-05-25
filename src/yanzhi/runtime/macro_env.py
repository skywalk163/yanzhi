# -*- coding: utf-8 -*-
"""宏环境

存储宏定义，支持作用域嵌套。
"""
from __future__ import annotations

from typing import Optional

from yanzhi.compiler.ast import MacroDef


class MacroEnvironment:
    """宏环境

    存储宏定义，支持作用域嵌套。
    """
    def __init__(self, parent: Optional[MacroEnvironment] = None):
        self.macros: dict[str, MacroDef] = {}
        self.parent = parent

    def get(self, name: str) -> MacroDef:
        """查找宏定义"""
        if name in self.macros:
            return self.macros[name]
        if self.parent:
            return self.parent.get(name)
        raise NameError(f"未定义的宏: {name}")

    def set(self, name: str, macro: MacroDef):
        """设置宏定义（当前作用域）"""
        self.macros[name] = macro

    def has(self, name: str) -> bool:
        """检查宏是否已定义"""
        if name in self.macros:
            return True
        if self.parent:
            return self.parent.has(name)
        return False
