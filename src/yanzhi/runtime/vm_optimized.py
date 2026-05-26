



# -*- coding: utf-8 -*-
"""优化版字节码虚拟机

使用指令分派表优化性能
"""
from __future__ import annotations

import math
from typing import Any, Dict, Callable
from yanzhi.runtime.bytecode import OpCode, BytecodeChunk, Instruction
from yanzhi.runtime.builtin import BUILTINS
from yanzhi.runtime.evaluator import Curry
from yanzhi.errors import YanError, NameError as YanNameError, TypeError as YanTypeError


class OptimizedVMFunction:
    """优化版VM内部函数对象"""
    __slots__ = ('vm', 'params', 'body_start', 'chunk')
    
    def __init__(self, vm: 'OptimizedVM', params: list[str], body_start: int, chunk: 'BytecodeChunk'):
        self.vm = vm
        self.params = params
        self.body_start = body_start
        self.chunk = chunk

    def __call__(self, *args: Any) -> Any:
        """调用函数（使用独立栈帧）"""
        vm = self.vm

        # 保存返回地址
        return_ip = vm.ip
        return_chunk = vm.chunk

        # 切换到函数自身的chunk
        vm.chunk = self.chunk

        # 创建新栈帧：绑定参数到局部变量
        frame = {}
        for i, name in enumerate(self.params):
            if i < len(args):
                frame[name] = args[i]
        vm.locals_stack.append(frame)

        # 跳转到函数体
        vm.ip = self.body_start
        vm._return_value = None

        # 执行函数体
        while vm.ip < len(vm.chunk.instructions):
            inst = vm.chunk.instructions[vm.ip]
            vm.ip += 1
            # 使用优化的执行方法
            vm._execute_optimized(inst)
        
        # 还原执行环境
        vm.ip = return_ip
        vm.chunk = return_chunk
        vm.locals_stack.pop()
        
        return vm._return_value


class OptimizedVM:
    """优化版虚拟机"""
    
    __slots__ = ('stack', 'globals', 'locals_stack', 'ip', 'chunk', '_return_value',
                 '_dispatch_table')
    
    def __init__(self):
        self.stack = []
        self.globals = {}
        self.locals_stack = []
        self.ip = 0
        self.chunk = None
        self._return_value = None
        
        # 构建指令分派表
        self._dispatch_table = self._build_dispatch_table()
    
    def _build_dispatch_table(self) -> Dict[OpCode, Callable]:
        """构建指令分派表"""
        return {
            # 常量加载
            OpCode.LOAD_NUM: self._op_load_num,
            OpCode.LOAD_STR: self._op_load_str,
            OpCode.LOAD_BOOL: self._op_load_bool,
            OpCode.LOAD_NIL: self._op_load_nil,
            
            # 变量操作
            OpCode.LOAD_VAR: self._op_load_var,
            OpCode.STORE_VAR: self._op_store_var,
            
            # 算术运算
            OpCode.ADD: self._op_add,
            OpCode.SUB: self._op_sub,
            OpCode.MUL: self._op_mul,
            OpCode.DIV: self._op_div,
            OpCode.MOD: self._op_mod,
            OpCode.POW: self._op_pow,
            OpCode.NEG: self._op_neg,
            
            # 比较运算
            OpCode.EQ: self._op_eq,
            OpCode.NE: self._op_ne,
            OpCode.LT: self._op_lt,
            OpCode.LE: self._op_le,
            OpCode.GT: self._op_gt,
            OpCode.GE: self._op_ge,
            
            # 逻辑运算
            OpCode.NOT: self._op_not,
            OpCode.AND: self._op_and,
            OpCode.OR: self._op_or,
            
            # 列表操作
            OpCode.MAKE_LIST: self._op_make_list,
            OpCode.GET_ITEM: self._op_get_item,
            OpCode.SET_ITEM: self._op_set_item,
            OpCode.LIST_LEN: self._op_list_len,
            
            # 控制流
            OpCode.JUMP: self._op_jump,
            OpCode.JUMP_IF_FALSE: self._op_jump_if_false,
            OpCode.JUMP_IF_TRUE: self._op_jump_if_true,
            OpCode.CALL: self._op_call,
            OpCode.RETURN: self._op_return,
            
            # 函数定义
            OpCode.MAKE_FUNC: self._op_make_func,
            
            # 内置动词
            OpCode.BUILTIN: self._op_builtin,
            
            # 打印
            OpCode.PRINT: self._op_print,
        }
    
    def run(self, chunk: BytecodeChunk) -> Any:
        """执行字节码"""
        self.chunk = chunk
        self.ip = 0
        self._return_value = None
        
        # 清空局部栈
        self.locals_stack = [{}]
        
        while self.ip < len(self.chunk.instructions):
            inst = self.chunk.instructions[self.ip]
            self.ip += 1
            self._execute_optimized(inst)
        
        # 返回栈顶值（如果有）
        if self.stack:
            return self.stack[-1]
        return self._return_value
    
    def _execute_optimized(self, inst: Instruction):
        """优化版指令执行"""
        handler = self._dispatch_table.get(inst.opcode)
        if handler:
            handler(inst)
        else:
            # 回退到原始执行方法
            self._execute_fallback(inst)
    
    def _execute_fallback(self, inst: Instruction):
        """回退执行方法（用于未实现的操作码）"""
        from yanzhi.runtime.vm import VM
        vm = VM()
        vm.stack = self.stack
        vm.globals = self.globals
        vm.locals_stack = self.locals_stack
        vm.ip = self.ip
        vm.chunk = self.chunk
        vm._return_value = self._return_value
        vm._execute(inst)
        self.stack = vm.stack
        self.locals_stack = vm.locals_stack
        self.ip = vm.ip
        self._return_value = vm._return_value
    
    # =============== 指令实现 ===============
    
    def _op_load_num(self, inst: Instruction):
        self.stack.append(inst.operand)
    
    def _op_load_str(self, inst: Instruction):
        self.stack.append(inst.operand)
    
    def _op_load_bool(self, inst: Instruction):
        self.stack.append(inst.operand)
    
    def _op_load_nil(self, inst: Instruction):
        self.stack.append(None)
    
    def _op_load_var(self, inst: Instruction):
        name = inst.operand
        # 查找局部变量
        for frame in reversed(self.locals_stack):
            if name in frame:
                self.stack.append(frame[name])
                return
        # 查找全局变量
        if name in self.globals:
            self.stack.append(self.globals[name])
        else:
            raise YanNameError(f"未定义的变量: {name}")
    
    def _op_store_var(self, inst: Instruction):
        name = inst.operand
        value = self.stack.pop()
        # 存储到当前帧
        self.locals_stack[-1][name] = value
    
    def _op_add(self, inst: Instruction):
        b, a = self.stack.pop(), self.stack.pop()
        self.stack.append(a + b)
    
    def _op_sub(self, inst: Instruction):
        b, a = self.stack.pop(), self.stack.pop()
        self.stack.append(a - b)
    
    def _op_mul(self, inst: Instruction):
        b, a = self.stack.pop(), self.stack.pop()
        self.stack.append(a * b)
    
    def _op_div(self, inst: Instruction):
        b, a = self.stack.pop(), self.stack.pop()
        if b == 0:
            raise YanError("除零错误")
        self.stack.append(a / b)
    
    def _op_mod(self, inst: Instruction):
        b, a = self.stack.pop(), self.stack.pop()
        if b == 0:
            raise YanError("模零错误")
        self.stack.append(a % b)
    
    def _op_pow(self, inst: Instruction):
        b, a = self.stack.pop(), self.stack.pop()
        self.stack.append(a ** b)
    
    def _op_neg(self, inst: Instruction):
        a = self.stack.pop()
        self.stack.append(-a)
    
    def _op_eq(self, inst: Instruction):
        b, a = self.stack.pop(), self.stack.pop()
        self.stack.append(a == b)
    
    def _op_ne(self, inst: Instruction):
        b, a = self.stack.pop(), self.stack.pop()
        self.stack.append(a != b)
    
    def _op_lt(self, inst: Instruction):
        b, a = self.stack.pop(), self.stack.pop()
        self.stack.append(a < b)
    
    def _op_le(self, inst: Instruction):
        b, a = self.stack.pop(), self.stack.pop()
        self.stack.append(a <= b)
    
    def _op_gt(self, inst: Instruction):
        b, a = self.stack.pop(), self.stack.pop()
        self.stack.append(a > b)
    
    def _op_ge(self, inst: Instruction):
        b, a = self.stack.pop(), self.stack.pop()
        self.stack.append(a >= b)
    
    def _op_not(self, inst: Instruction):
        a = self.stack.pop()
        self.stack.append(not a)
    
    def _op_and(self, inst: Instruction):
        b, a = self.stack.pop(), self.stack.pop()
        self.stack.append(a and b)
    
    def _op_or(self, inst: Instruction):
        b, a = self.stack.pop(), self.stack.pop()
        self.stack.append(a or b)
    
    def _op_make_list(self, inst: Instruction):
        count = inst.operand
        items = []
        for _ in range(count):
            items.append(self.stack.pop())
        items.reverse()
        self.stack.append(items)
    
    def _op_get_item(self, inst: Instruction):
        idx = self.stack.pop()
        lst = self.stack.pop()
        self.stack.append(lst[idx])
    
    def _op_set_item(self, inst: Instruction):
        name = inst.operand
        val = self.stack.pop()
        idx = self.stack.pop()
        # 从当前帧或globals查找数组
        lst = None
        for frame in reversed(self.locals_stack):
            if name in frame:
                lst = frame[name]
                break
        if lst is None:
            lst = self.globals.get(name)
        if lst is None:
            raise YanNameError(f"未定义的变量: {name}")
        lst[idx] = val
    
    def _op_list_len(self, inst: Instruction):
        lst = self.stack.pop()
        self.stack.append(len(lst))
    
    def _op_jump(self, inst: Instruction):
        self.ip = inst.operand
    
    def _op_jump_if_false(self, inst: Instruction):
        cond = self.stack.pop()
        if not cond:
            self.ip = inst.operand
    
    def _op_jump_if_true(self, inst: Instruction):
        cond = self.stack.pop()
        if cond:
            self.ip = inst.operand
    
    def _op_call(self, inst: Instruction):
        arity = inst.operand
        args = []
        for _ in range(arity):
            args.append(self.stack.pop())
        args.reverse()
        func = self.stack.pop()
        if callable(func):
            result = func(*args)
            self.stack.append(result)
        else:
            raise YanTypeError(f"不可调用的对象: {type(func)}")
    
    def _op_return(self, inst: Instruction):
        if self.stack:
            self._return_value = self.stack.pop()
        else:
            self._return_value = None
        self.ip = len(self.chunk.instructions)  # 跳出循环
    
    def _op_make_func(self, inst: Instruction):
        params_and_body = inst.operand2
        if isinstance(params_and_body, tuple) and len(params_and_body) == 2:
            params, body_start = params_and_body
        else:
            params, body_start = [], 0
        self.stack.append(OptimizedVMFunction(self, params, body_start, self.chunk))
    
    def _op_builtin(self, inst: Instruction):
        name = inst.operand
        arity = inst.operand2
        args = []
        for _ in range(arity):
            args.append(self.stack.pop())
        args.reverse()
        
        # 调用内置函数
        if name in BUILTINS:
            func = BUILTINS[name]
            self.stack.append(func(*args))
        else:
            raise YanNameError(f"未定义的内置函数: {name}")
    
    def _op_print(self, inst: Instruction):
        val = self.stack.pop()
        print(val)


def run_optimized(chunk: BytecodeChunk) -> Any:
    """优化版运行函数"""
    vm = OptimizedVM()
    return vm.run(chunk)


if __name__ == '__main__':
    # 简单测试
    from yanzhi.runtime.bytecode import BytecodeChunk, OpCode
    
    chunk = BytecodeChunk()
    chunk.emit(OpCode.LOAD_NUM, 5)
    chunk.emit(OpCode.LOAD_NUM, 3)
    chunk.emit(OpCode.ADD)
    chunk.emit(OpCode.PRINT)
    
    result = run_optimized(chunk)
    print(f"结果: {result}")


