# -*- coding: utf-8 -*-
"""知行 AST -> 字节码编译器

将 AST 编译为字节码指令序列
"""
from __future__ import annotations

from yanzhi.compiler.ast import (
    Node, Program, Num, Str, Bool, Nil, Word, Ident,
    Call, Pipeline, If, Block, Define, Lambda,
    ForLoop, WhileLoop, While, ReturnStmt, TryStmt, ThrowStmt,
    ListExpr, MathExpr, PythonCode, Quote, Eval,
    MacroDef, ExportStmt, Assign,
)
from yanzhi.runtime.bytecode import OpCode, BytecodeChunk, Instruction
from yanzhi.runtime.builtin import is_builtin


# 动词到操作码的映射
VERB_TO_OPCODE = {
    '加': OpCode.ADD,
    '减': OpCode.SUB,
    '乘': OpCode.MUL,
    '除': OpCode.DIV,
    '模': OpCode.MOD,
    '幂': OpCode.POW,
    '等': OpCode.EQ,
    '不等': OpCode.NE,
    '小': OpCode.LT,
    '小等': OpCode.LE,
    '大': OpCode.GT,
    '大等': OpCode.GE,
    '且': OpCode.AND,
    '或': OpCode.OR,
    '非': OpCode.NOT,
    '负': OpCode.NEG,
}

# 需要翻转操作数顺序的比较动词（a大b → b<a）
REVERSE_COMPARISON = {'大': OpCode.LT, '大等': OpCode.LE}


class Compiler:
    """AST 到字节码编译器"""

    def __init__(self):
        self.chunk = BytecodeChunk(name='main')

    def compile(self, node: Node) -> BytecodeChunk:
        """编译 AST 节点为字节码"""
        self._compile(node)
        return self.chunk

    def _compile(self, node: Node) -> None:
        """递归编译 AST 节点"""
        if isinstance(node, Program):
            self._compile_program(node)
        elif isinstance(node, Num):
            self.chunk.emit(OpCode.LOAD_NUM, node.value)
        elif isinstance(node, Str):
            self.chunk.emit(OpCode.LOAD_STR, node.value)
        elif isinstance(node, Bool):
            self.chunk.emit(OpCode.LOAD_BOOL, node.value)
        elif isinstance(node, Nil):
            self.chunk.emit(OpCode.LOAD_NIL)
        elif isinstance(node, Word):
            self.chunk.emit(OpCode.LOAD_VAR, node.name)
        elif isinstance(node, Ident):
            self.chunk.emit(OpCode.LOAD_VAR, node.name)
        elif isinstance(node, Call):
            self._compile_call(node)
        elif isinstance(node, Pipeline):
            self._compile_pipeline(node)
        elif isinstance(node, If):
            self._compile_if(node)
        elif isinstance(node, Block):
            self._compile_block(node)
        elif isinstance(node, Define):
            self._compile_define(node)
        elif isinstance(node, Lambda):
            self._compile_lambda(node)
        elif isinstance(node, ForLoop):
            self._compile_for_loop(node)
        elif isinstance(node, WhileLoop):
            self._compile_while(node)
        elif isinstance(node, While):
            # While 使用 condition 而非 cond
            self._compile_while_yanzhi(node)
        elif isinstance(node, ReturnStmt):
            self._compile_return(node)
        elif isinstance(node, ListExpr):
            self._compile_list(node)
        elif isinstance(node, MathExpr):
            self._compile_math(node)
        elif isinstance(node, TryStmt):
            self._compile_try(node)
        elif isinstance(node, ThrowStmt):
            self._compile_throw(node)
        elif isinstance(node, MacroDef):
            pass  # 宏在编译前已展开
        elif isinstance(node, ExportStmt):
            pass  # 导出在模块加载时处理
        elif isinstance(node, PythonCode):
            # Python 代码块：作为内置操作处理
            self.chunk.emit(OpCode.BUILTIN, 'python_code', 0)
            self.chunk.constants.append(node.code)
        elif isinstance(node, Quote):
            pass  # 引用需要特殊处理
        elif isinstance(node, Eval):
            pass  # 求值引用需要特殊处理
        elif isinstance(node, Assign):
            self._compile_assign(node)
        else:
            raise RuntimeError(f"不支持的 AST 节点: {type(node).__name__}")

    def _compile_program(self, node: Program) -> None:
        """编译程序"""
        for stmt in node.statements:
            self._compile(stmt)

    def _compile_call(self, node: Call) -> None:
        """编译函数调用"""
        verb = node.verb
        args = node.args

        # 检查是否是算术/比较动词
        if isinstance(verb, Word) and verb.name in VERB_TO_OPCODE:
            opcode = VERB_TO_OPCODE[verb.name]

            if verb.name in REVERSE_COMPARISON:
                # 翻转比较：a大b → b < a
                actual_opcode = REVERSE_COMPARISON[verb.name]
                if len(args) == 2:
                    self._compile(args[1])
                    self._compile(args[0])
                elif len(args) == 1:
                    self._compile(args[0])
                self.chunk.emit(actual_opcode)
            elif verb.name == '负':
                # 一元负
                self._compile(args[0])
                self.chunk.emit(OpCode.NEG)
            elif verb.name == '非':
                # 逻辑非
                self._compile(args[0])
                self.chunk.emit(OpCode.NOT)
            else:
                # 二元运算
                if len(args) >= 2:
                    self._compile(args[0])
                    self._compile(args[1])
                    self.chunk.emit(opcode)
                elif len(args) == 1:
                    # 单参数：可能是管道上下文
                    self._compile(args[0])
                    self.chunk.emit(opcode)
            return

        # 检查是否是动词操作符（加、减、乘等）
        from ..compiler.ast import Ident
        if isinstance(verb, Word):
            verb_name = verb.name
        elif isinstance(verb, Ident):
            verb_name = verb.name
        else:
            verb_name = verb
        if verb_name in VERB_TO_OPCODE:
            opcode = VERB_TO_OPCODE[verb_name]
            # 处理翻转比较
            if verb_name in REVERSE_COMPARISON:
                if len(args) >= 2:
                    self._compile(args[1])
                    self._compile(args[0])
                    self.chunk.emit(REVERSE_COMPARISON[verb_name])
                return
            # 处理一元运算
            if verb_name == '负':
                self._compile(args[0])
                self.chunk.emit(OpCode.NEG)
                return
            if verb_name == '非':
                self._compile(args[0])
                self.chunk.emit(OpCode.NOT)
                return
            # 二元运算
            if len(args) >= 2:
                self._compile(args[0])
                self._compile(args[1])
                self.chunk.emit(opcode)
            elif len(args) == 1:
                self._compile(args[0])
                self.chunk.emit(opcode)
            return

        # 检查是否是内置动词
        verb_name = verb.name if hasattr(verb, 'name') else verb
        if is_builtin(verb_name):
            for arg in args:
                self._compile(arg)
            self.chunk.emit(OpCode.BUILTIN, verb_name, len(args))
            return

        # 一般函数调用
        if isinstance(verb, str):
            # verb是字符串，直接加载变量
            self.chunk.emit(OpCode.LOAD_VAR, verb)
        else:
            # verb是AST节点
            self._compile(verb)
        for arg in args:
            self._compile(arg)
        self.chunk.emit(OpCode.CALL, len(args))

    def _emit_builtin(self, name, argc):
        """发射内置函数调用指令"""
        self.chunk.emit(OpCode.BUILTIN, name, argc)

    def _compile_pipe_arg(self, node):
        """编译管道参数：算术动词作为函数引用，不进行算术优化"""
        if isinstance(node, Call):
            verb = node.verb
            verb_name = verb.name if hasattr(verb, 'name') else None
            # 检查是否是算术动词（在 VERB_TO_OPCODE 中）
            if verb_name and verb_name in VERB_TO_OPCODE:
                # 编译为 BUILTIN 调用（保留柯里化语义）
                for arg in node.args:
                    self._compile(arg)
                self._emit_builtin(verb_name, len(node.args))
                return
        # 其他类型正常编译
        self._compile(node)

    def _compile_pipeline(self, node: Pipeline) -> None:
        """编译管道操作"""
        # 管道操作：left | right
        # 先编译left，结果留在栈顶
        self._compile(node.left)

        # 编译right，right应该是一个Call节点，会使用栈顶的值作为第一个参数
        # 如果right是Call节点，需要特殊处理
        if isinstance(node.right, Call):
            # right是一个函数调用，如"乘2"
            # 我们需要将left的结果作为第一个参数传递给right
            # 编译函数名
            verb = node.right.verb
            if isinstance(verb, Ident):
                # 内置动词或用户定义函数
                func_name = verb.name
                # 检查是否是内置动词
                if is_builtin(func_name):
                    # 编译参数（left的结果已经在栈顶）
                    # 管道参数特殊处理：算术动词作为函数引用，不进行算术优化
                    for arg in node.right.args:
                        self._compile_pipe_arg(arg)
                    self._emit_builtin(func_name, len(node.right.args) + 1)
                else:
                    # 用户定义函数
                    self.chunk.emit(OpCode.LOAD_VAR, func_name)
                    # 参数已经在栈上（left的结果 + right的参数）
                    for arg in node.right.args:
                        self._compile_pipe_arg(arg)
                    self.chunk.emit(OpCode.CALL, len(node.right.args) + 1)
            elif isinstance(verb, str):
                # verb是字符串（内置动词）
                func_name = verb
                for arg in node.right.args:
                    self._compile_pipe_arg(arg)
                self._emit_builtin(func_name, len(node.right.args) + 1)
            else:
                # 其他情况，直接编译
                self._compile(node.right)
        else:
            # right不是Call节点，直接编译
            self._compile(node.right)

    def _compile_if(self, node: If) -> None:
        """编译条件表达式"""
        # 编译条件
        self._compile(node.condition)

        # 条件为假时跳转
        jump_false = self.chunk.emit(OpCode.JUMP_IF_FALSE, 0)  # 占位

        # 编译真分支
        self._compile(node.then_branch)

        if node.else_branch is not None and not isinstance(node.else_branch, Nil):
            # 真分支结束后跳过假分支
            jump_end = self.chunk.emit(OpCode.JUMP, 0)  # 占位

            # 修补假跳转目标
            self.chunk.instructions[jump_false].operand = len(self.chunk.instructions)

            # 编译假分支
            self._compile(node.else_branch)

            # 修补结束跳转目标
            self.chunk.instructions[jump_end].operand = len(self.chunk.instructions)
        else:
            # 无假分支，直接修补
            self.chunk.instructions[jump_false].operand = len(self.chunk.instructions)

    def _compile_block(self, node: Block) -> None:
        """编译代码块"""
        for stmt in node.statements:
            self._compile(stmt)

    def _compile_define(self, node: Define) -> None:
        """编译变量定义"""
        self._compile(node.value)
        self.chunk.emit(OpCode.STORE_VAR, node.name)

    def _compile_assign(self, node: Assign) -> None:
        """编译变量赋值"""
        if node.index is not None:
            # 索引赋值：name[index] = value
            # SET_ITEM 通过 operand 读取 name，从当前帧/globals 查变量
            self._compile(node.index)   # 编译索引
            self._compile(node.value)   # 编译值
            self.chunk.emit(OpCode.SET_ITEM, node.name)  # operand 为变量名
        else:
            # 简单赋值：name = value
            self._compile(node.value)
            self.chunk.emit(OpCode.STORE_VAR, node.name)

    def _compile_lambda(self, node: Lambda) -> None:
        """编译函数定义"""
        # 简化：将函数体编译为独立块，记录起始位置
        # 实际实现需要闭包支持，这里用简化方案
        code_start = len(self.chunk.instructions)
        # 跳过函数体（先编译函数体，再修补）
        jump_over = self.chunk.emit(OpCode.JUMP, 0)  # 占位

        body_start = len(self.chunk.instructions)
        self._compile(node.body)
        self.chunk.emit(OpCode.RETURN)

        # 修补跳转
        self.chunk.instructions[jump_over].operand = len(self.chunk.instructions)

        # 创建函数对象（参数名列表 + 函数体起始位置）
        self.chunk.emit(OpCode.MAKE_FUNC, len(node.params), (node.params, body_start))

    def _compile_for_loop(self, node: ForLoop) -> None:
        """编译 for 循环"""
        # 编译起始和结束值
        self._compile(node.start)
        self._compile(node.end)
        self.chunk.emit(OpCode.BUILTIN, 'range', 2)

        loop_start = len(self.chunk.instructions)

        # 获取下一个元素
        self.chunk.emit(OpCode.BUILTIN, 'next', 1)
        self.chunk.emit(OpCode.STORE_VAR, node.var)

        # 检查是否结束
        self.chunk.emit(OpCode.LOAD_VAR, '__iter_done__')
        jump_end = self.chunk.emit(OpCode.JUMP_IF_TRUE, 0)  # 占位

        # 编译循环体
        self._compile(node.body)
        self.chunk.emit(OpCode.JUMP, loop_start)

        # 修补结束跳转
        self.chunk.instructions[jump_end].operand = len(self.chunk.instructions)

    def _compile_while(self, node: WhileLoop) -> None:
        """编译 while 循环"""
        loop_start = len(self.chunk.instructions)

        # 编译条件
        self._compile(node.cond)
        jump_end = self.chunk.emit(OpCode.JUMP_IF_FALSE, 0)  # 占位

        # 编译循环体
        self._compile(node.body)
        self.chunk.emit(OpCode.JUMP, loop_start)

        # 修补结束跳转
        self.chunk.instructions[jump_end].operand = len(self.chunk.instructions)

    def _compile_while_yanzhi(self, node: While) -> None:
        """编译当循环（yanzhi 版 While）"""
        loop_start = len(self.chunk.instructions)
        self._compile(node.condition)
        jump_end = self.chunk.emit(OpCode.JUMP_IF_FALSE, 0)
        self._compile(node.body)
        self.chunk.emit(OpCode.JUMP, loop_start)
        self.chunk.instructions[jump_end].operand = len(self.chunk.instructions)

    def _compile_return(self, node: ReturnStmt) -> None:
        """编译返回语句"""
        if node.value is not None:
            self._compile(node.value)
        else:
            self.chunk.emit(OpCode.LOAD_NIL)
        self.chunk.emit(OpCode.RETURN)

    def _compile_list(self, node: ListExpr) -> None:
        """编译列表字面量"""
        for elem in node.elements:
            self._compile(elem)
        self.chunk.emit(OpCode.MAKE_LIST, len(node.elements))

    def _compile_math(self, node: MathExpr) -> None:
        """编译数学表达式"""
        # 数学表达式需要特殊处理
        # 简化：作为内置操作
        self.chunk.emit(OpCode.BUILTIN, 'math_expr', 0)
        self.chunk.constants.append(node.expr)

    def _compile_try(self, node: TryStmt) -> None:
        """编译 try-catch"""
        # 简化实现：标记 try/catch/finally 地址
        try_start = len(self.chunk.instructions)
        catch_addr = 0  # 占位
        finally_addr = 0  # 占位

        self.chunk.emit(OpCode.TRY_ENTER, 0, 0)  # 占位

        # 编译 try 块
        self._compile(node.try_block)
        self.chunk.emit(OpCode.TRY_EXIT)

        # catch 地址
        catch_addr = len(self.chunk.instructions)
        if node.catch_block.statements:
            # 编译 catch 块
            self._compile(node.catch_block)

        # finally 地址
        finally_addr = len(self.chunk.instructions)
        if node.finally_block:
            self._compile(node.finally_block)

        # 修补 TRY_ENTER
        self.chunk.instructions[try_start].operand = catch_addr
        self.chunk.instructions[try_start].operand2 = finally_addr

    def _compile_throw(self, node: ThrowStmt) -> None:
        """编译 throw"""
        if node.value is not None:
            self._compile(node.value)
        else:
            self.chunk.emit(OpCode.LOAD_NIL)
        self.chunk.emit(OpCode.THROW)


def compile_to_bytecode(ast: Node) -> BytecodeChunk:
    """编译 AST 为字节码（便捷函数）"""
    compiler = Compiler()
    return compiler.compile(ast)
