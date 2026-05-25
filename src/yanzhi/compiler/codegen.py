"""
知行语言代码生成器
将AST转换为Python代码
"""

from typing import List, Dict, Set
from .ast import *


class CodeGen:
    """代码生成器"""
    
    def __init__(self):
        self.indent = 0
        self.imports: Set[str] = set()
        self.helpers: List[str] = []
    
    def generate(self, ast: ASTNode) -> str:
        """生成Python代码"""
        # 生成主代码
        code = self.gen(ast)
        
        # 组合导入和辅助函数
        result = []
        
        if self.imports:
            result.append('\n'.join(sorted(self.imports)))
            result.append('')
        
        if self.helpers:
            result.extend(self.helpers)
            result.append('')
        
        result.append(code)
        
        return '\n'.join(result)
    
    def gen(self, node: ASTNode) -> str:
        """生成代码"""
        if isinstance(node, Program):
            return self.gen_program(node)
        elif isinstance(node, Num):
            return self.gen_num(node)
        elif isinstance(node, Str):
            return self.gen_str(node)
        elif isinstance(node, Bool):
            return self.gen_bool(node)
        elif isinstance(node, Nil):
            return self.gen_nil(node)
        elif isinstance(node, Ident):
            return self.gen_ident(node)
        elif isinstance(node, Call):
            return self.gen_call(node)
        elif isinstance(node, Pipeline):
            return self.gen_pipeline(node)
        elif isinstance(node, Define):
            return self.gen_define(node)
        elif isinstance(node, Assign):
            return self.gen_assign(node)
        elif isinstance(node, Lambda):
            return self.gen_lambda(node)
        elif isinstance(node, If):
            return self.gen_if(node)
        elif isinstance(node, ForEach):
            return self.gen_foreach(node)
        elif isinstance(node, ForLoop):
            return self.gen_forloop(node)
        elif isinstance(node, While):
            return self.gen_while(node)
        elif isinstance(node, Block):
            return self.gen_block(node)
        elif isinstance(node, MathExpr):
            return self.gen_math_expr(node)
        elif isinstance(node, PythonCode):
            return self.gen_python_code(node)
        elif isinstance(node, Quote):
            return self.gen_quote(node)
        else:
            raise RuntimeError(f"未知的AST节点类型: {type(node).__name__}")
    
    def gen_program(self, node: Program) -> str:
        """生成程序"""
        codes = []
        for stmt in node.statements:
            code = self.gen(stmt)
            if code:
                codes.append(code)
        return '\n'.join(codes)
    
    def gen_num(self, node: Num) -> str:
        """生成数字"""
        return repr(node.value)
    
    def gen_str(self, node: Str) -> str:
        """生成字符串"""
        return repr(node.value)
    
    def gen_bool(self, node: Bool) -> str:
        """生成布尔值"""
        return 'True' if node.value else 'False'
    
    def gen_nil(self, node: Nil) -> str:
        """生成空值"""
        return 'None'
    
    def gen_ident(self, node: Ident) -> str:
        """生成标识符"""
        return self.mangle_name(node.name)
    
    def gen_call(self, node: Call) -> str:
        """生成函数调用"""
        verb = self.mangle_name(node.verb)
        args = ', '.join(self.gen(arg) for arg in node.args)
        return f"{verb}({args})"
    
    def gen_pipeline(self, node: Pipeline) -> str:
        """生成管道操作"""
        # 左侧的结果作为右侧的第一个参数
        left = self.gen(node.left)
        
        if isinstance(node.right, Call):
            # 将左侧结果插入到参数列表的最前面
            right = node.right
            verb = self.mangle_name(right.verb)
            args = [left] + [self.gen(arg) for arg in right.args]
            args_str = ', '.join(args)
            return f"{verb}({args_str})"
        else:
            # 如果右侧不是调用，直接生成
            right = self.gen(node.right)
            return f"{right}({left})"
    
    def gen_define(self, node: Define) -> str:
        """生成变量定义"""
        name = self.mangle_name(node.name)
        value = self.gen(node.value)
        return f"{name} = {value}"
    
    def gen_assign(self, node: Assign) -> str:
        """生成变量赋值"""
        name = self.mangle_name(node.name)
        value = self.gen(node.value)
        return f"{name} = {value}"
    
    def gen_lambda(self, node: Lambda) -> str:
        """生成匿名函数"""
        params = ', '.join(self.mangle_name(p) for p in node.params)
        body = self.gen(node.body)
        
        if isinstance(node.body, Block):
            # 块体需要特殊处理
            return f"lambda {params}: ({body})"
        else:
            return f"lambda {params}: {body}"
    
    def gen_if(self, node: If) -> str:
        """生成条件表达式"""
        condition = self.gen(node.condition)
        then_branch = self.gen(node.then_branch)
        else_branch = self.gen(node.else_branch)
        return f"({then_branch} if {condition} else {else_branch})"
    
    def gen_foreach(self, node: ForEach) -> str:
        """生成遍历循环"""
        var = self.mangle_name(node.var)
        iterable = self.gen(node.iterable)
        body = self.gen(node.body)

        if isinstance(node.body, Block):
            # 块体
            return f"for {var} in {iterable}:\n{self.indent_code(body)}"
        else:
            # 单行体
            return f"for {var} in {iterable}:\n{self.indent_code(body)}"

    def gen_forloop(self, node: ForLoop) -> str:
        """生成ForLoop循环"""
        var = self.mangle_name(node.var)
        iterable = self.gen(node.iterable)
        body = self.gen(node.body)

        if isinstance(node.body, Block):
            # 块体
            return f"for {var} in {iterable}:\n{self.indent_code(body)}"
        else:
            # 单行体
            return f"for {var} in {iterable}:\n{self.indent_code(body)}"

    def gen_while(self, node: While) -> str:
        """生成当循环"""
        condition = self.gen(node.condition)
        body = self.gen(node.body)
        
        if isinstance(node.body, Block):
            return f"while {condition}:\n{self.indent_code(body)}"
        else:
            return f"while {condition}:\n{self.indent_code(body)}"
    
    def gen_block(self, node: Block) -> str:
        """生成代码块"""
        codes = []
        for stmt in node.statements:
            code = self.gen(stmt)
            if code:
                codes.append(code)
        return '\n'.join(codes)
    
    def gen_math_expr(self, node: MathExpr) -> str:
        """生成数学表达式"""
        # 直接嵌入数学表达式
        return f"({node.expr})"
    
    def gen_python_code(self, node: PythonCode) -> str:
        """生成Python代码块"""
        return f"({node.code})"
    
    def gen_quote(self, node: Quote) -> str:
        """生成引用"""
        # 引用返回AST的字典表示
        self.imports.add('import json')
        expr = self.gen(node.expr)
        return f"'{expr}'"  # 简化处理，返回字符串表示
    
    def mangle_name(self, name) -> str:
        """名称修饰（处理中文和特殊字符）"""
        # 处理Ident对象
        from .ast import Ident
        if isinstance(name, Ident):
            name = name.name
        
        # 如果是纯ASCII，直接返回
        if name.isascii():
            return name
        
        # 否则，添加前缀
        return f"_zh_{name}"
    
    def indent_code(self, code: str) -> str:
        """缩进代码"""
        lines = code.split('\n')
        return '\n'.join('    ' + line for line in lines)


def codegen(ast: ASTNode) -> str:
    """代码生成函数"""
    gen = CodeGen()
    return gen.generate(ast)


# 测试代码
if __name__ == '__main__':
    from .parser import parse
    
    test_cases = [
        "定x=5。",
        "定y=5加3。",
        "列1 2 3，皆乘2。",
        "若x大y则x否则y。",
        "定平方=函x乘x x。",
    ]
    
    for source in test_cases:
        print(f"\n源码: {source}")
        try:
            ast = parse(source)
            python_code = codegen(ast)
            print(f"Python:\n{python_code}")
        except Exception as e:
            print(f"错误: {e}")
