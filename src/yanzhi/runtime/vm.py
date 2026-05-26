# -*- coding: utf-8 -*-
"""知行字节码虚拟机

基于栈的虚拟机，执行字节码指令
"""
from __future__ import annotations

import math
from typing import Any
from yanzhi.runtime.bytecode import OpCode, BytecodeChunk, Instruction
from yanzhi.runtime.builtin import BUILTINS
from yanzhi.runtime.evaluator import Curry
from yanzhi.errors import YanError, NameError as YanNameError, TypeError as YanTypeError


class VMFunction:
    """VM 内部函数对象"""
    def __init__(self, vm: 'VM', params: list[str], body_start: int, chunk: 'BytecodeChunk'):
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

        # 切换到函数自身的 chunk
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
            vm._execute(inst)

        # 获取返回值
        result = vm._return_value

        # 弹出栈帧
        vm.locals_stack.pop()

        # 恢复执行位置
        vm.ip = return_ip
        vm.chunk = return_chunk

        return result


class VM:
    """知行字节码虚拟机"""

    def __init__(self):
        self.stack: list[Any] = []
        self.globals: dict[str, Any] = {}
        self.locals_stack: list[dict[str, Any]] = [{}]  # 栈帧（最底层为全局级）
        self.ip: int = 0  # 指令指针
        self.chunk: BytecodeChunk | None = None
        self._return_value: Any = None
        self._setup_builtins()

    def _setup_builtins(self):
        """设置内置函数"""
        self.builtins = {
            '打印': self._builtin_print,
            '首个': self._builtin_first,
            '尾': self._builtin_last,
            '长度': self._builtin_len,
            '索引': self._builtin_getitem,
            '取': self._builtin_getitem,  # 数组索引
            '映射': self._builtin_map,
            '过滤': self._builtin_filter,
            '排': self._builtin_sort,
            '反': self._builtin_reverse,
            '合': self._builtin_join,
            '包含': self._builtin_contains,
            '类': self._builtin_type,
            '字': self._builtin_str,
            '整': self._builtin_int,
            '绝对': self._builtin_abs,
        }

    def run(self, chunk: BytecodeChunk) -> Any:
        """执行字节码块"""
        self.chunk = chunk
        self.ip = 0
        self.stack = []

        while self.ip < len(chunk.instructions):
            inst = chunk.instructions[self.ip]
            self.ip += 1
            self._execute(inst)

        # 返回栈顶（如果有）
        if self.stack:
            return self.stack[-1]
        return None

    def _execute(self, inst: Instruction) -> None:
        """执行单条指令"""
        op = inst.opcode

        # 常量加载
        if op == OpCode.LOAD_NUM:
            self.stack.append(inst.operand)
        elif op == OpCode.LOAD_STR:
            self.stack.append(inst.operand)
        elif op == OpCode.LOAD_BOOL:
            self.stack.append(inst.operand)
        elif op == OpCode.LOAD_NIL:
            self.stack.append(None)

        # 变量操作
        elif op == OpCode.LOAD_VAR:
            name = inst.operand
            # 从当前栈帧逐层查找
            for frame in reversed(self.locals_stack):
                if name in frame:
                    self.stack.append(frame[name])
                    break
            else:
                if name in self.globals:
                    self.stack.append(self.globals[name])
                else:
                    raise YanNameError(f"未定义的变量: {name}")
        elif op == OpCode.STORE_VAR:
            name = inst.operand
            val = self.stack.pop()
            # 存储在当前栈帧
            if self.locals_stack:
                self.locals_stack[-1][name] = val
            else:
                self.globals[name] = val

        # 算术运算
        elif op == OpCode.ADD:
            b, a = self.stack.pop(), self.stack.pop()
            self.stack.append(a + b)
        elif op == OpCode.SUB:
            b, a = self.stack.pop(), self.stack.pop()
            self.stack.append(a - b)
        elif op == OpCode.MUL:
            b, a = self.stack.pop(), self.stack.pop()
            self.stack.append(a * b)
        elif op == OpCode.DIV:
            b, a = self.stack.pop(), self.stack.pop()
            if b == 0:
                raise YanError("除零错误")
            self.stack.append(a / b)
        elif op == OpCode.MOD:
            b, a = self.stack.pop(), self.stack.pop()
            self.stack.append(a % b)
        elif op == OpCode.POW:
            b, a = self.stack.pop(), self.stack.pop()
            self.stack.append(a ** b)
        elif op == OpCode.NEG:
            a = self.stack.pop()
            self.stack.append(-a)

        # 比较运算
        elif op == OpCode.EQ:
            b, a = self.stack.pop(), self.stack.pop()
            self.stack.append(a == b)
        elif op == OpCode.NE:
            b, a = self.stack.pop(), self.stack.pop()
            self.stack.append(a != b)
        elif op == OpCode.LT:
            b, a = self.stack.pop(), self.stack.pop()
            self.stack.append(a < b)
        elif op == OpCode.LE:
            b, a = self.stack.pop(), self.stack.pop()
            self.stack.append(a <= b)
        elif op == OpCode.GT:
            b, a = self.stack.pop(), self.stack.pop()
            self.stack.append(a > b)
        elif op == OpCode.GE:
            b, a = self.stack.pop(), self.stack.pop()
            self.stack.append(a >= b)

        # 逻辑运算
        elif op == OpCode.NOT:
            a = self.stack.pop()
            self.stack.append(not a)
        elif op == OpCode.AND:
            b, a = self.stack.pop(), self.stack.pop()
            self.stack.append(a and b)
        elif op == OpCode.OR:
            b, a = self.stack.pop(), self.stack.pop()
            self.stack.append(a or b)

        # 列表操作
        elif op == OpCode.MAKE_LIST:
            count = inst.operand
            items = []
            for _ in range(count):
                items.append(self.stack.pop())
            items.reverse()
            self.stack.append(items)
        elif op == OpCode.GET_ITEM:
            idx = self.stack.pop()
            lst = self.stack.pop()
            self.stack.append(lst[idx])
        elif op == OpCode.SET_ITEM:
            name = inst.operand
            val = self.stack.pop()
            idx = self.stack.pop()
            # 从当前帧或 globals 查找数组
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
        elif op == OpCode.LIST_LEN:
            lst = self.stack.pop()
            self.stack.append(len(lst))

        # 控制流
        elif op == OpCode.JUMP:
            self.ip = inst.operand
        elif op == OpCode.JUMP_IF_FALSE:
            cond = self.stack.pop()
            if not cond:
                self.ip = inst.operand
        elif op == OpCode.JUMP_IF_TRUE:
            cond = self.stack.pop()
            if cond:
                self.ip = inst.operand
        elif op == OpCode.CALL:
            arity = inst.operand
            args = []
            for _ in range(arity):
                args.append(self.stack.pop())
            args.reverse()
            func = self.stack.pop()
            if callable(func):
                result = func(*args)
                self.stack.append(result)
            elif isinstance(func, tuple) and len(func) == 2:
                # (arity, callable) 格式
                _, fn = func
                result = fn(*args)
                self.stack.append(result)
            else:
                raise YanTypeError(f"不可调用的对象: {type(func)}")
        elif op == OpCode.RETURN:
            if self.stack:
                self._return_value = self.stack.pop()
            else:
                self._return_value = None
            self.ip = len(self.chunk.instructions)  # 跳出循环

        # 函数定义
        elif op == OpCode.MAKE_FUNC:
            params_and_body = inst.operand2
            if isinstance(params_and_body, tuple) and len(params_and_body) == 2:
                params, body_start = params_and_body
            else:
                params, body_start = [], 0
            self.stack.append(VMFunction(self, params, body_start, self.chunk))

        # 内置动词
        elif op == OpCode.BUILTIN:
            name = inst.operand
            arity = inst.operand2
            args = []
            for _ in range(arity):
                args.append(self.stack.pop())
            args.reverse()
            self._handle_builtin(name, args)

        # 打印
        elif op == OpCode.PRINT:
            val = self.stack.pop()
            print(val)

        # 异常处理
        elif op == OpCode.THROW:
            val = self.stack.pop()
            raise YanError(str(val))
        elif op == OpCode.TRY_ENTER:
            # 简化：记录 catch/finally 地址
            pass
        elif op == OpCode.TRY_EXIT:
            pass

        # 空操作
        elif op == OpCode.NOP:
            pass

        else:
            raise YanError(f"未知操作码: {op}")

    # ==================== 内置动词 ====================

    def _builtin_print(self, *args) -> None:
        """印：打印"""
        for arg in args:
            if isinstance(arg, bool):
                print('真' if arg else '假')
            elif arg is None:
                print('空')
            else:
                print(arg)
        return args[-1] if args else None

    def _builtin_first(self, lst) -> Any:
        """首：取首元素"""
        return lst[0]

    def _builtin_last(self, lst) -> Any:
        """尾：取末元素"""
        return lst[-1]

    def _builtin_len(self, obj) -> int:
        """长：取长度"""
        return len(obj)

    def _builtin_getitem(self, lst, idx) -> Any:
        """入：取元素"""
        return lst[idx]

    def _builtin_map(self, func, lst) -> list:
        """皆：映射"""
        if isinstance(func, tuple) and len(func) == 2 and callable(func[1]):
            _, fn = func
            return [fn(x) for x in lst]
        if callable(func):
            return [func(x) for x in lst]
        raise YanTypeError(f"皆: 不可映射的对象: {type(func)}")

    def _builtin_filter(self, func, lst) -> list:
        """只：过滤"""
        if isinstance(func, tuple) and len(func) == 2 and callable(func[1]):
            _, fn = func
            return [x for x in lst if fn(x)]
        if callable(func):
            return [x for x in lst if func(x)]
        raise YanTypeError(f"只: 不可过滤的对象: {type(func)}")

    def _builtin_sort(self, lst) -> list:
        """排：排序"""
        return sorted(lst)

    def _builtin_reverse(self, lst) -> list:
        """反：反转"""
        return list(reversed(lst))

    def _builtin_join(self, lst, sep='') -> str:
        """合：合并"""
        return sep.join(str(x) for x in lst)

    def _builtin_contains(self, lst, item) -> bool:
        """含：包含"""
        return item in lst

    def _builtin_type(self, obj) -> str:
        """类：类型"""
        if isinstance(obj, bool):
            return '布尔'
        elif isinstance(obj, int):
            return '整数'
        elif isinstance(obj, float):
            return '浮点'
        elif isinstance(obj, str):
            return '字符串'
        elif isinstance(obj, list):
            return '列表'
        return '未知'

    def _builtin_str(self, obj) -> str:
        """字：转字符串"""
        return str(obj)

    def _builtin_int(self, obj) -> int:
        """整：转整数"""
        return int(obj)

    def _builtin_abs(self, obj) -> int | float:
        """绝对：绝对值"""
        return abs(obj)

    def _handle_builtin(self, name: str, args: list) -> None:
        """处理内置动词调用：依次查找 VM 内置→evaluator BUILTINS→globals"""
        # 0. 副词（映射/过滤/归约/合并）在管道中参数顺序为 (func, lst)
        #    但栈上顺序为 (lst, func)，需要交换
        if name in ('映射', '过滤', '归约', '合并') and len(args) == 2:
            args = [args[1], args[0]]  # 交换为 (func, lst)

        # 1. 检查 VM 内置函数（印/首/尾/长等有特殊实现的方法）
        if name in self.builtins:
            result = self.builtins[name](*args)
            if result is not None:
                self.stack.append(result)
            return

        # 2. 检查 evaluator 的 BUILTINS 字典
        if name in BUILTINS:
            func = BUILTINS[name]
            try:
                result = func(*args)
                if result is not None:
                    self.stack.append(result)
            except TypeError:
                # 参数不足：尝试部分应用（柯里化），使用 Curry 对象
                # 以便与 evaluator 的柯里化兼容
                self.stack.append(Curry(func, list(args)))
            return

        # 3. 检查全局变量（用户定义函数）
        if name in self.globals:
            func = self.globals[name]
            if callable(func):
                result = func(*args)
                if result is not None:
                    self.stack.append(result)
                return
            raise YanTypeError(f"不可调用的对象: {type(func)}")

        # 4. 特殊处理
        if name == 'math_expr':
            expr = self.chunk.constants.pop(0) if self.chunk.constants else ''
            try:
                result = eval(expr)
                self.stack.append(result)
            except Exception as e:
                raise YanError(f"数学表达式错误: {e}")
            return
        elif name == 'python_code':
            code = self.chunk.constants.pop(0) if self.chunk.constants else ''
            try:
                result = eval(code)
                self.stack.append(result)
            except Exception:
                exec(code)
            return

        raise YanNameError(f"未知内置动词: {name}")


def evaluate_bytecode(source: str) -> Any:
    """从源码编译并执行字节码（便捷函数）"""
    from yanzhi.compiler.parser import parse
    from yanzhi.runtime.compiler_bc import compile_to_bytecode

    ast = parse(source)
    chunk = compile_to_bytecode(ast)
    vm = VM()
    return vm.run(chunk)
