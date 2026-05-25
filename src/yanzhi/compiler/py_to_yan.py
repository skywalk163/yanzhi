# -*- coding: utf-8 -*-
"""
Python 到知行语言转换器

基于 AST 的代码转换工具，将 Python 代码转换为知行语言代码。
"""

import ast as python_ast
import re
from typing import List, Optional


class PythonToZhixingConverter:
    """Python 到知行语言转换器"""
    
    def __init__(self):
        self.indent_level = 0
        self.indent_str = "  "  # 两个空格缩进
        
        # 运算符映射
        self.binop_map = {
            python_ast.Add: '加',
            python_ast.Sub: '减',
            python_ast.Mult: '乘',
            python_ast.Div: '除',
            python_ast.FloorDiv: '除',
            python_ast.Mod: '模',
            python_ast.Pow: '幂',
        }
        
        self.compareop_map = {
            python_ast.Gt: '大',
            python_ast.Lt: '小',
            python_ast.Eq: '等',
            python_ast.NotEq: '不等',
            python_ast.GtE: '大等于',
            python_ast.LtE: '小等于',
        }
        
        self.boolop_map = {
            python_ast.And: '且',
            python_ast.Or: '或',
        }
    
    def convert(self, python_code: str) -> str:
        """转换 Python 代码为知行语言代码"""
        try:
            python_ast_tree = python_ast.parse(python_code)
            return self.visit(python_ast_tree)
        except SyntaxError as e:
            return f"# Python 语法错误: {e}"
    
    def visit(self, node: python_ast.AST) -> str:
        """访问 AST 节点"""
        method_name = f'visit_{node.__class__.__name__}'
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)
    
    def generic_visit(self, node: python_ast.AST) -> str:
        """默认访问方法"""
        return f"# 不支持的节点: {node.__class__.__name__}"
    
    def indent(self) -> str:
        """获取当前缩进"""
        return self.indent_str * self.indent_level
    
    # ==================== 模块和语句 ====================
    
    def visit_Module(self, node: python_ast.Module) -> str:
        """处理模块"""
        statements = []
        for stmt in node.body:
            result = self.visit(stmt)
            if result and not result.startswith('#'):
                statements.append(result)
        return '\n'.join(statements)
    
    def visit_Expr(self, node: python_ast.Expr) -> str:
        """处理表达式语句"""
        return f"{self.indent()}{self.visit(node.value)}，印。"
    
    # ==================== 变量和赋值 ====================
    
    def visit_Assign(self, node: python_ast.Assign) -> str:
        """处理赋值语句"""
        target = node.targets[0]
        value = self.visit(node.value)
        
        if isinstance(target, python_ast.Name):
            return f"{self.indent()}定{target.id}={value}。"
        elif isinstance(target, python_ast.Tuple):
            # 多重赋值
            names = [elt.id for elt in target.elts if isinstance(elt, python_ast.Name)]
            if isinstance(node.value, python_ast.Tuple):
                values = [self.visit(v) for v in node.value.elts]
                return '\n'.join(f"{self.indent()}定{name}={val}。" 
                               for name, val in zip(names, values))
        return f"{self.indent()}# 不支持的赋值"
    
    def visit_AugAssign(self, node: python_ast.AugAssign) -> str:
        """处理增强赋值 (+=, -= 等)"""
        target = node.target.id
        value = self.visit(node.value)
        op = self.binop_map.get(type(node.op), '?')
        return f"{self.indent()}设{target}={target}{op}{value}。"
    
    def visit_Name(self, node: python_ast.Name) -> str:
        """处理变量名"""
        return node.id
    
    # ==================== 字面值 ====================
    
    def visit_Constant(self, node: python_ast.Constant) -> str:
        """处理常量"""
        if isinstance(node.value, str):
            return f'"{node.value}"'
        elif isinstance(node.value, bool):
            return '真' if node.value else '假'
        elif node.value is None:
            return '空'
        else:
            return str(node.value)
    
    def visit_Num(self, node: python_ast.Num) -> str:
        """处理数字（Python 3.7 兼容）"""
        return str(node.n)
    
    def visit_Str(self, node: python_ast.Str) -> str:
        """处理字符串（Python 3.7 兼容）"""
        return f'"{node.s}"'
    
    def visit_List(self, node: python_ast.List) -> str:
        """处理列表"""
        elements = [self.visit(elt) for elt in node.elts]
        return f"列{' '.join(elements)}"
    
    def visit_Tuple(self, node: python_ast.Tuple) -> str:
        """处理元组"""
        elements = [self.visit(elt) for elt in node.elts]
        return f"列{' '.join(elements)}"
    
    def visit_Dict(self, node: python_ast.Dict) -> str:
        """处理字典"""
        # 简化处理：转换为注释
        return "# 字典需要特殊处理"
    
    # ==================== 运算符 ====================
    
    def visit_BinOp(self, node: python_ast.BinOp) -> str:
        """处理二元运算"""
        left = self.visit(node.left)
        right = self.visit(node.right)
        op = self.binop_map.get(type(node.op), '?')
        return f"{left}{op}{right}"
    
    def visit_UnaryOp(self, node: python_ast.UnaryOp) -> str:
        """处理一元运算"""
        operand = self.visit(node.operand)
        if isinstance(node.op, python_ast.USub):
            return f"负{operand}"
        elif isinstance(node.op, python_ast.Not):
            return f"非{operand}"
        return operand
    
    def visit_Compare(self, node: python_ast.Compare) -> str:
        """处理比较运算"""
        left = self.visit(node.left)
        comparisons = []
        
        for op, comparator in zip(node.ops, node.comparators):
            right = self.visit(comparator)
            op_str = self.compareop_map.get(type(op), '?')
            comparisons.append(f"{left}{op_str}{right}")
            left = right
        
        return '且'.join(comparisons) if len(comparisons) > 1 else comparisons[0]
    
    def visit_BoolOp(self, node: python_ast.BoolOp) -> str:
        """处理布尔运算"""
        values = [self.visit(v) for v in node.values]
        op = self.boolop_map.get(type(node.op), '?')
        return op.join(values)
    
    # ==================== 控制流 ====================
    
    def visit_If(self, node: python_ast.If) -> str:
        """处理条件语句"""
        test = self.visit(node.test)
        
        # 处理 then 分支
        self.indent_level += 1
        body = '\n'.join(self.visit(stmt) for stmt in node.body)
        self.indent_level -= 1
        
        if node.orelse:
            # 处理 else 分支
            self.indent_level += 1
            orelse = '\n'.join(self.visit(stmt) for stmt in node.orelse)
            self.indent_level -= 1
            
            return f"{self.indent()}若{test}则：\n{body}\n{self.indent()}否则：\n{orelse}\n{self.indent()}。"
        else:
            return f"{self.indent()}若{test}则：\n{body}\n{self.indent()}。"
    
    def visit_For(self, node: python_ast.For) -> str:
        """处理 for 循环"""
        target = node.target.id if isinstance(node.target, python_ast.Name) else '?'
        iter_ = self.visit(node.iter)
        
        self.indent_level += 1
        body = '\n'.join(self.visit(stmt) for stmt in node.body)
        self.indent_level -= 1
        
        return f"{self.indent()}遍历{target}从1到{iter_}：\n{body}\n{self.indent()}。"
    
    def visit_While(self, node: python_ast.While) -> str:
        """处理 while 循环"""
        test = self.visit(node.test)
        
        self.indent_level += 1
        body = '\n'.join(self.visit(stmt) for stmt in node.body)
        self.indent_level -= 1
        
        return f"{self.indent()}当{test}：\n{body}\n{self.indent()}。"
    
    # ==================== 函数 ====================
    
    def visit_FunctionDef(self, node: python_ast.FunctionDef) -> str:
        """处理函数定义"""
        name = node.name
        args = ' '.join(arg.arg for arg in node.args.args)
        
        self.indent_level += 1
        body_statements = [self.visit(stmt) for stmt in node.body]
        body = '\n'.join(body_statements)
        self.indent_level -= 1
        
        if args:
            return f"{self.indent()}定{name}=函{args}：\n{body}\n{self.indent()}。"
        else:
            return f"{self.indent()}定{name}=函：\n{body}\n{self.indent()}。"
    
    def visit_Return(self, node: python_ast.Return) -> str:
        """处理 return 语句"""
        if node.value:
            value = self.visit(node.value)
            return f"{self.indent()}{value}。"
        return f"{self.indent()}空。"
    
    def visit_Call(self, node: python_ast.Call) -> str:
        """处理函数调用"""
        # 特殊处理一些内置函数
        if isinstance(node.func, python_ast.Name):
            func_name = node.func.id
            
            # range() -> 范围
            if func_name == 'range':
                if len(node.args) == 1:
                    return f"范围{self.visit(node.args[0])}"
                elif len(node.args) == 2:
                    return f"范围{self.visit(node.args[0])}到{self.visit(node.args[1])}"
            
            # len() -> 长
            elif func_name == 'len':
                return f"{self.visit(node.args[0])}，长"
            
            # print() -> 印
            elif func_name == 'print':
                if node.args:
                    return f"{self.visit(node.args[0])}，印"
                return "印"
            
            # abs() -> 绝对
            elif func_name == 'abs':
                return f"绝对{self.visit(node.args[0])}"
            
            # sum() -> 归加
            elif func_name == 'sum':
                return f"{self.visit(node.args[0])}，归加0"
        
        # 普通函数调用
        func = self.visit(node.func)
        args = ' '.join(self.visit(arg) for arg in node.args)
        return f"{func}{args}"
    
    # ==================== 列表推导式 ====================
    
    def visit_ListComp(self, node: python_ast.ListComp) -> str:
        """处理列表推导式"""
        # [x*2 for x in range(10) if x > 3]
        # → 范围10，只大3，皆乘2。
        
        generator = node.generators[0]
        iter_ = self.visit(generator.iter)
        
        # 处理过滤条件
        filter_parts = []
        if generator.ifs:
            for cond in generator.ifs:
                cond_str = self.visit(cond)
                # 简化条件：假设是 x > 3 这样的形式
                filter_parts.append(f"只{cond_str}")
        
        # 处理映射
        elt = self.visit(node.elt)
        
        result = iter_
        if filter_parts:
            result += '，' + '，'.join(filter_parts)
        result += f"，皆{elt}"
        
        return result
    
    # ==================== 其他 ====================
    
    def visit_Pass(self, node: python_ast.Pass) -> str:
        """处理 pass 语句"""
        return f"{self.indent()}# pass"
    
    def visit_Break(self, node: python_ast.Break) -> str:
        """处理 break 语句"""
        return f"{self.indent()}结束。"
    
    def visit_Continue(self, node: python_ast.Continue) -> str:
        """处理 continue 语句"""
        return f"{self.indent()}# continue"


def convert_file(input_file: str, output_file: Optional[str] = None) -> str:
    """转换 Python 文件为知行语言文件"""
    with open(input_file, 'r', encoding='utf-8') as f:
        python_code = f.read()
    
    converter = PythonToZhixingConverter()
    zhixing_code = converter.convert(python_code)
    
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(zhixing_code)
    
    return zhixing_code


def convert_code(python_code: str) -> str:
    """转换 Python 代码字符串"""
    converter = PythonToZhixingConverter()
    return converter.convert(python_code)


# 示例用法
if __name__ == '__main__':
    # 测试代码
    test_python = """
def factorial(n):
    if n <= 1:
        return 1
    else:
        return n * factorial(n - 1)

result = factorial(5)
"""
    
    print("=" * 70)
    print("Python 代码：")
    print("=" * 70)
    print(test_python)
    print()
    
    print("=" * 70)
    print("知行语言代码：")
    print("=" * 70)
    zhixing_code = convert_code(test_python)
    print(zhixing_code)
