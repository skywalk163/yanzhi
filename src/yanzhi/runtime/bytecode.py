# -*- coding: utf-8 -*-
"""知行字节码虚拟机

指令集设计：
- 基于栈的虚拟机
- 每条指令包含操作码和可选操作数
- 支持基本运算、控制流、函数调用

指令格式：
  (opcode, operand)  其中 operand 可选
"""
from __future__ import annotations

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Any


# ==================== 指令集 ====================

class OpCode(Enum):
    """字节码操作码"""
    # 常量加载
    LOAD_NUM = auto()      # 加载数字常量    (LOAD_NUM, value)
    LOAD_STR = auto()      # 加载字符串常量  (LOAD_STR, value)
    LOAD_BOOL = auto()     # 加载布尔常量    (LOAD_BOOL, value)
    LOAD_NIL = auto()      # 加载空值        (LOAD_NIL,)

    # 变量操作
    LOAD_VAR = auto()      # 加载变量        (LOAD_VAR, name)
    STORE_VAR = auto()     # 存储变量        (STORE_VAR, name)

    # 算术运算
    ADD = auto()           # 加法
    SUB = auto()           # 减法
    MUL = auto()           # 乘法
    DIV = auto()           # 除法
    MOD = auto()           # 取模
    POW = auto()           # 幂
    NEG = auto()           # 取负

    # 比较运算
    EQ = auto()            # 等于
    NE = auto()            # 不等于
    LT = auto()            # 小于
    LE = auto()            # 小于等于
    GT = auto()            # 大于
    GE = auto()            # 大于等于

    # 逻辑运算
    NOT = auto()           # 逻辑非
    AND = auto()           # 逻辑与
    OR = auto()            # 逻辑或

    # 列表操作
    MAKE_LIST = auto()     # 创建列表      (MAKE_LIST, count)
    GET_ITEM = auto()      # 获取元素
    SET_ITEM = auto()      # 设置元素
    LIST_LEN = auto()      # 列表长度

    # 控制流
    JUMP = auto()          # 无条件跳转    (JUMP, target)
    JUMP_IF_FALSE = auto() # 条件跳转      (JUMP_IF_FALSE, target)
    JUMP_IF_TRUE = auto()  # 条件跳转(真)  (JUMP_IF_TRUE, target)
    CALL = auto()          # 函数调用      (CALL, arity)
    RETURN = auto()        # 返回

    # 函数定义
    MAKE_FUNC = auto()     # 创建函数      (MAKE_FUNC, params_count, code_start)

    # 内置动词
    BUILTIN = auto()       # 内置动词调用  (BUILTIN, name, arity)

    # 打印
    PRINT = auto()         # 打印栈顶

    # 异常处理
    THROW = auto()         # 抛出异常
    TRY_ENTER = auto()     # 进入try块    (TRY_ENTER, catch_addr, finally_addr)
    TRY_EXIT = auto()      # 退出try块

    # 空操作
    NOP = auto()           # 空操作


@dataclass
class Instruction:
    """字节码指令"""
    opcode: OpCode
    operand: Any = None
    operand2: Any = None

    def __repr__(self):
        if self.operand2 is not None:
            return f"{self.opcode.name} {self.operand} {self.operand2}"
        if self.operand is not None:
            return f"{self.opcode.name} {self.operand}"
        return self.opcode.name


@dataclass
class BytecodeChunk:
    """字节码块（一个编译单元）"""
    instructions: list[Instruction] = field(default_factory=list)
    constants: list[Any] = field(default_factory=list)
    name: str = ''

    def emit(self, opcode: OpCode, operand=None, operand2=None) -> int:
        """发射一条指令，返回其偏移量"""
        idx = len(self.instructions)
        self.instructions.append(Instruction(opcode, operand, operand2))
        return idx

    def __repr__(self):
        lines = []
        for i, inst in enumerate(self.instructions):
            lines.append(f"  {i:4d}  {inst}")
        return '\n'.join(lines)
