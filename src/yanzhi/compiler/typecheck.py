"""
知行语言类型检查器
提供静态类型检查功能
"""

from typing import Dict, Set, Optional, List, Any
from .ast import *
from .errors import TypeError as YanTypeError


class TypeChecker:
    """类型检查器"""
    
    def __init__(self):
        self.types: Dict[str, str] = {}  # 变量名 -> 类型
        self.functions: Dict[str, List[str]] = {}  # 函数名 -> 参数类型列表
        self.errors: List[str] = []
    
    def check(self, node: ASTNode) -> List[str]:
        """检查AST节点的类型"""
        self.errors = []
        self.visit(node)
        return self.errors
    
    def visit(self, node: ASTNode) -> str:
        """访问AST节点，返回类型"""
        if isinstance(node, Num):
            return '数'
        elif isinstance(node, Str):
            return '文'
        elif isinstance(node, Bool):
            return '布尔'
        elif isinstance(node, Nil):
            return '空'
        elif isinstance(node, Ident):
            return self.visit_ident(node)
        elif isinstance(node, Call):
            return self.visit_call(node)
        elif isinstance(node, Pipeline):
            return self.visit_pipeline(node)
        elif isinstance(node, Define):
            return self.visit_define(node)
        elif isinstance(node, Assign):
            return self.visit_assign(node)
        elif isinstance(node, Lambda):
            return self.visit_lambda(node)
        elif isinstance(node, If):
            return self.visit_if(node)
        elif isinstance(node, ForEach):
            return self.visit_foreach(node)
        elif isinstance(node, While):
            return self.visit_while(node)
        elif isinstance(node, Block):
            return self.visit_block(node)
        elif isinstance(node, Program):
            return self.visit_program(node)
        else:
            return '未知'
    
    def visit_ident(self, node: Ident) -> str:
        """访问标识符"""
        name = node.name
        if name in self.types:
            return self.types[name]
        else:
            self.errors.append(f"未定义的变量: {name}")
            return '未知'
    
    def visit_call(self, node: Call) -> str:
        """访问函数调用"""
        verb = node.verb
        args = node.args
        
        # 检查参数类型
        arg_types = [self.visit(arg) for arg in args]
        
        # 根据动词推断返回类型
        if verb in ['加', '减', '乘', '除', '模', '幂', '负', '绝对']:
            # 算术运算返回数
            if not all(t in ['数', '未知'] for t in arg_types):
                self.errors.append(f"算术运算'{verb}'需要数值参数")
            return '数'
        
        elif verb in ['大', '小', '等', '不等', '大等于', '小等于']:
            # 比较运算返回布尔
            return '布尔'
        
        elif verb in ['且', '或', '非']:
            # 逻辑运算返回布尔
            return '布尔'
        
        elif verb == '列':
            # 列表构造
            return '列'
        
        elif verb in ['首', '余']:
            # 列表操作
            if arg_types[0] != '列':
                self.errors.append(f"'{verb}'需要列表参数")
            return '未知'
        
        elif verb == '长':
            # 长度返回数
            return '数'
        
        elif verb == '印':
            # 打印返回空
            return '空'
        
        else:
            # 未知动词
            return '未知'
    
    def visit_pipeline(self, node: Pipeline) -> str:
        """访问管道操作"""
        left_type = self.visit(node.left)
        right_type = self.visit(node.right)
        return right_type
    
    def visit_define(self, node: Define) -> str:
        """访问定义语句"""
        name = node.name
        value_type = self.visit(node.value)
        self.types[name] = value_type
        return '空'
    
    def visit_assign(self, node: Assign) -> str:
        """访问赋值语句"""
        name = node.name
        value_type = self.visit(node.value)
        
        if name in self.types:
            if self.types[name] != value_type and value_type != '未知':
                self.errors.append(f"类型不匹配: 变量'{name}'期望{self.types[name]}，实际{value_type}")
        else:
            self.errors.append(f"未定义的变量: {name}")
        
        return '空'
    
    def visit_lambda(self, node: Lambda) -> str:
        """访问Lambda表达式"""
        # 添加参数到类型环境
        old_types = self.types.copy()
        for param in node.params:
            self.types[param] = '未知'
        
        # 检查函数体
        body_type = self.visit(node.body)
        
        # 恢复类型环境
        self.types = old_types
        
        return '函'
    
    def visit_if(self, node: If) -> str:
        """访问If表达式"""
        cond_type = self.visit(node.condition)
        then_type = self.visit(node.then_branch)
        else_type = self.visit(node.else_branch)
        
        if cond_type != '布尔' and cond_type != '未知':
            self.errors.append(f"条件表达式需要布尔类型，实际{cond_type}")
        
        return then_type if then_type == else_type else '未知'
    
    def visit_foreach(self, node: ForEach) -> str:
        """访问ForEach循环"""
        iter_type = self.visit(node.iterable)
        
        if iter_type != '列' and iter_type != '未知':
            self.errors.append(f"遍历需要列表类型，实际{iter_type}")
        
        # 添加循环变量
        old_types = self.types.copy()
        self.types[node.var] = '未知'
        
        # 检查循环体
        self.visit(node.body)
        
        # 恢复类型环境
        self.types = old_types
        
        return '空'
    
    def visit_while(self, node: While) -> str:
        """访问While循环"""
        cond_type = self.visit(node.condition)
        
        if cond_type != '布尔' and cond_type != '未知':
            self.errors.append(f"循环条件需要布尔类型，实际{cond_type}")
        
        self.visit(node.body)
        return '空'
    
    def visit_block(self, node: Block) -> str:
        """访问代码块"""
        for stmt in node.statements:
            self.visit(stmt)
        return '空'
    
    def visit_program(self, node: Program) -> str:
        """访问程序"""
        for stmt in node.statements:
            self.visit(stmt)
        return '空'


def type_check(ast: ASTNode) -> List[str]:
    """类型检查入口函数"""
    checker = TypeChecker()
    return checker.check(ast)
