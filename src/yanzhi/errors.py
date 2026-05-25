# -*- coding: utf-8 -*-
"""知行语言统一错误处理

错误分类：
1. ParseError   — 语法分析错误（词法/语法阶段）
2. NameError    — 名称错误（未定义变量/函数）
3. TypeError    — 类型错误（操作数类型不匹配）
4. ArityError   — 元数错误（参数数量不匹配）
5. ValueError   — 值错误（除零、索引越界等）
6. RuntimeError — 其他运行时错误

所有错误继承自 YanError，携带位置信息和中文消息。
"""
from __future__ import annotations

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from yanzhi.compiler.pre_tokenizer import Token


class YanError(Exception):
    """知行语言错误基类"""

    def __init__(self, message: str, line: int = 0, col: int = 0):
        self.message = message
        self.line = line
        self.col = col
        if line > 0:
            super().__init__(f"第{line}行第{col}列: {message}")
        else:
            super().__init__(message)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.message!r})"


class ParseError(YanError):
    """语法分析错误

    兼容两种构造方式：
    - ParseError("消息", token)  — 从 Token 提取位置
    - ParseError("消息", line=3, col=5)  — 直接指定位置
    """

    def __init__(self, message: str, token: 'Token | None' = None,
                 line: int = 0, col: int = 0):
        if token is not None:
            line = token.line
            col = token.col
            full_msg = f"{message} (遇到 {token.type.name}='{token.value}')"
        else:
            full_msg = message
        super().__init__(full_msg, line=line, col=col)
        self.token = token


class NameError(YanError):
    """名称错误：未定义的变量或函数"""
    pass


class TypeError(YanError):
    """类型错误：操作数类型不匹配"""
    pass


class ArityError(YanError):
    """元数错误：参数数量不匹配"""
    pass


class ValueError(YanError):
    """值错误：除零、索引越界等"""
    pass


class RuntimeError(YanError):
    """运行时错误"""
    pass


class ReturnException(Exception):
    """返回语句异常

    用于从函数体中提前退出。不继承 YanError，
    因为它不是错误，而是控制流机制。
    """

    def __init__(self, value):
        self.value = value


class ThrowException(Exception):
    """抛出异常

    用于 try-catch 异常处理。不继承 YanError，
    因为它是用户主动抛出的值，由捕获语句处理。
    """

    def __init__(self, value):
        self.value = value
