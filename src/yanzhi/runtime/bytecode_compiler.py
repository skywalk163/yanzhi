# -*- coding: utf-8 -*-
"""
字节码编译器

将知行语言AST编译为字节码，提高执行效率。
"""

from enum import IntEnum
from typing import Any, List, Dict, Optional
from dataclasses import dataclass


# ==================== 字节码指令 ====================

class OpCode(IntEnum):
    """字节码操作码"""
    # 常量加载
    LOAD_CONST = 1      # 加载常量
    LOAD_NAME = 2        # 加载变量
    STORE_NAME = 3       # 存储变量
    
    # 算术运算
    BINARY_ADD = 10      # 加法
    BINARY_SUB = 11      # 减法
    BINARY_MUL = 12      # 乘法
    BINARY_DIV = 13      # 除法
    BINARY_MOD = 14      # 取模
    BINARY_POW = 15      # 幂运算
    
    # 比较运算
    COMPARE_GT = 20      # 大于
    COMPARE_LT = 21      # 小于
    COMPARE_EQ = 22      # 等于
    COMPARE_NE = 23      # 不等于
    COMPARE_GE = 24      # 大于等于
    COMPARE_LE = 25      # 小于等于
    
    # 逻辑运算
    BINARY_AND = 30      # 逻辑与
    BINARY_OR = 31       # 逻辑或
    UNARY_NOT = 32       # 逻辑非
    
    # 函数操作
    MAKE_FUNCTION = 40   # 创建函数
    CALL_FUNCTION = 41   # 调用函数
    RETURN = 42          # 返回
    
    # 控制流
    JUMP = 50            # 无条件跳转
    JUMP_IF_TRUE = 51    # 为真跳转
    JUMP_IF_FALSE = 52   # 为假跳转
    
    # 列表操作
    BUILD_LIST = 60      # 构建列表
    LIST_APPEND = 61     # 列表追加
    LIST_GET = 62        # 列表索引
    LIST_LEN = 63        # 列表长度
    
    # 其他
    POP = 70             # 弹出栈顶
    DUP = 71             # 复制栈顶
    PRINT = 72           # 打印
    NOP = 73             # 无操作


@dataclass
class Instruction:
    """字节码指令"""
    opcode: OpCode
    arg: Any = None
    line: int = 0
    
    def __str__(self):
        if self.arg is not None:
            return f"{self.opcode.name} {self.arg}"
        return self.opcode.name


# ==================== 字节码编译器 ====================

class BytecodeCompiler:
    """字节码编译器"""
    
    def __init__(self):
        self.instructions: List[Instruction] = []
        self.constants: List[Any] = []
        self.names: List[str] = []
        self.current_line = 0
    
    def emit(self, opcode: OpCode, arg: Any = None):
        """发射一条指令"""
        self.instructions.append(Instruction(opcode, arg, self.current_line))
    
    def add_constant(self, value: Any) -> int:
        """添加常量，返回索引"""
        if value in self.constants:
            return self.constants.index(value)
        self.constants.append(value)
        return len(self.constants) - 1
    
    def add_name(self, name: str) -> int:
        """添加名称，返回索引"""
        if name in self.names:
            return self.names.index(name)
        self.names.append(name)
        return len(self.names) - 1
    
    # ==================== 编译方法 ====================
    
    def compile_number(self, value: Any):
        """编译数字"""
        idx = self.add_constant(value)
        self.emit(OpCode.LOAD_CONST, idx)
    
    def compile_string(self, value: str):
        """编译字符串"""
        idx = self.add_constant(value)
        self.emit(OpCode.LOAD_CONST, idx)
    
    def compile_name(self, name: str):
        """编译变量名"""
        idx = self.add_name(name)
        self.emit(OpCode.LOAD_NAME, idx)
    
    def compile_binary_op(self, op: str):
        """编译二元运算"""
        op_map = {
            '加': OpCode.BINARY_ADD,
            '减': OpCode.BINARY_SUB,
            '乘': OpCode.BINARY_MUL,
            '除': OpCode.BINARY_DIV,
            '模': OpCode.BINARY_MOD,
            '幂': OpCode.BINARY_POW,
            '大': OpCode.COMPARE_GT,
            '小': OpCode.COMPARE_LT,
            '等': OpCode.COMPARE_EQ,
            '不等': OpCode.COMPARE_NE,
            '大等于': OpCode.COMPARE_GE,
            '小等于': OpCode.COMPARE_LE,
            '且': OpCode.BINARY_AND,
            '或': OpCode.BINARY_OR,
        }
        opcode = op_map.get(op, OpCode.NOP)
        self.emit(opcode)
    
    def compile_call(self, arg_count: int):
        """编译函数调用"""
        self.emit(OpCode.CALL_FUNCTION, arg_count)
    
    def compile_define(self, name: str):
        """编译变量定义"""
        idx = self.add_name(name)
        self.emit(OpCode.STORE_NAME, idx)
    
    def compile_if(self, else_addr: int, end_addr: int):
        """编译条件语句"""
        self.emit(OpCode.JUMP_IF_FALSE, else_addr)
        # ... then分支代码 ...
        self.emit(OpCode.JUMP, end_addr)
        # ... else分支代码 ...
    
    def compile_loop(self, start_addr: int, end_addr: int):
        """编译循环"""
        # ... 循环体 ...
        self.emit(OpCode.JUMP, start_addr)
        # end_addr: 循环结束
    
    def compile_function(self, name: str, param_count: int):
        """编译函数定义"""
        idx = self.add_name(name)
        self.emit(OpCode.MAKE_FUNCTION, param_count)
        self.emit(OpCode.STORE_NAME, idx)
    
    def compile_return(self):
        """编译返回语句"""
        self.emit(OpCode.RETURN)
    
    def compile_print(self):
        """编译打印语句"""
        self.emit(OpCode.PRINT)
    
    # ==================== 输出 ====================
    
    def to_bytes(self) -> bytes:
        """转换为字节"""
        result = []
        for inst in self.instructions:
            result.append(inst.opcode)
            if inst.arg is not None:
                result.append(inst.arg)
        return bytes(result)
    
    def disassemble(self) -> str:
        """反汇编，生成可读的字节码"""
        lines = ["字节码:", "=" * 70]
        for i, inst in enumerate(self.instructions):
            lines.append(f"{i:4d}: {inst}")
        return "\n".join(lines)


# ==================== 字节码虚拟机 ====================

class VirtualMachine:
    """字节码虚拟机"""
    
    def __init__(self):
        self.stack: List[Any] = []
        self.env: Dict[str, Any] = {}
        self.constants: List[Any] = []
        self.names: List[str] = []
        self.pc = 0  # 程序计数器
    
    def run(self, instructions: List[Instruction], 
            constants: List[Any], 
            names: List[str]) -> Any:
        """执行字节码"""
        self.constants = constants
        self.names = names
        self.pc = 0
        
        while self.pc < len(instructions):
            inst = instructions[self.pc]
            self.execute(inst)
            self.pc += 1
        
        return self.stack[-1] if self.stack else None
    
    def execute(self, inst: Instruction):
        """执行单条指令"""
        opcode = inst.opcode
        arg = inst.arg
        
        # 常量加载
        if opcode == OpCode.LOAD_CONST:
            self.stack.append(self.constants[arg])
        
        elif opcode == OpCode.LOAD_NAME:
            name = self.names[arg]
            self.stack.append(self.env[name])
        
        elif opcode == OpCode.STORE_NAME:
            name = self.names[arg]
            self.env[name] = self.stack.pop()
        
        # 算术运算
        elif opcode == OpCode.BINARY_ADD:
            b, a = self.stack.pop(), self.stack.pop()
            self.stack.append(a + b)
        
        elif opcode == OpCode.BINARY_SUB:
            b, a = self.stack.pop(), self.stack.pop()
            self.stack.append(a - b)
        
        elif opcode == OpCode.BINARY_MUL:
            b, a = self.stack.pop(), self.stack.pop()
            self.stack.append(a * b)
        
        elif opcode == OpCode.BINARY_DIV:
            b, a = self.stack.pop(), self.stack.pop()
            self.stack.append(a / b)
        
        # 比较运算
        elif opcode == OpCode.COMPARE_GT:
            b, a = self.stack.pop(), self.stack.pop()
            self.stack.append(a > b)
        
        elif opcode == OpCode.COMPARE_LT:
            b, a = self.stack.pop(), self.stack.pop()
            self.stack.append(a < b)
        
        elif opcode == OpCode.COMPARE_EQ:
            b, a = self.stack.pop(), self.stack.pop()
            self.stack.append(a == b)
        
        # 其他操作
        elif opcode == OpCode.PRINT:
            print(self.stack[-1])
        
        elif opcode == OpCode.POP:
            self.stack.pop()
        
        elif opcode == OpCode.DUP:
            self.stack.append(self.stack[-1])
        
        elif opcode == OpCode.NOP:
            pass


# ==================== 导出 ====================

if __name__ == '__main__':
    print("字节码编译器测试")
    print("=" * 70)
    
    # 创建编译器
    compiler = BytecodeCompiler()
    
    # 编译简单表达式: 5 + 3
    compiler.compile_number(5)
    compiler.compile_number(3)
    compiler.compile_binary_op('加')
    
    # 显示字节码
    print(compiler.disassemble())
    
    # 执行字节码
    vm = VirtualMachine()
    result = vm.run(compiler.instructions, compiler.constants, compiler.names)
    print(f"\n执行结果: {result}")
    
    print("\n[OK] 字节码编译器测试完成")
