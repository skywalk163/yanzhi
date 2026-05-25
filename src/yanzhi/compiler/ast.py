"""
知行语言AST节点定义
"""

from typing import List, Any, Optional, Union
from dataclasses import dataclass


@dataclass
class ASTNode:
    """AST节点基类"""
    pass


# 别名，用于兼容性
Node = ASTNode


# 字面量节点
@dataclass
class Num(ASTNode):
    """数字字面量"""
    value: float


@dataclass
class Str(ASTNode):
    """字符串字面量"""
    value: str


@dataclass
class Bool(ASTNode):
    """布尔值"""
    value: bool


@dataclass
class Nil(ASTNode):
    """空值"""
    pass


# 标识符和调用
@dataclass
class Ident(ASTNode):
    """标识符"""
    name: str


@dataclass
class Call(ASTNode):
    """函数调用"""
    verb: Union[str, 'Ident']      # 动词名称或Ident节点
    args: List[ASTNode]  # 参数列表


@dataclass
class Pipeline(ASTNode):
    """管道操作"""
    left: ASTNode   # 左侧表达式
    right: ASTNode  # 右侧表达式


# 定义
@dataclass
class Define(ASTNode):
    """变量定义"""
    name: str
    value: ASTNode


@dataclass
class Assign(ASTNode):
    """变量赋值"""
    name: str
    value: ASTNode
    index: ASTNode = None  # 可选索引：name[index] = value


@dataclass
class Lambda(ASTNode):
    """匿名函数"""
    params: List[str]  # 参数列表
    body: ASTNode      # 函数体


# 控制流
@dataclass
class If(ASTNode):
    """条件表达式"""
    condition: ASTNode
    then_branch: ASTNode
    else_branch: ASTNode


@dataclass
class ForEach(ASTNode):
    """遍历循环"""
    var: str          # 循环变量
    iterable: ASTNode  # 可迭代对象
    body: ASTNode      # 循环体


@dataclass
class While(ASTNode):
    """当循环"""
    condition: ASTNode  # 循环条件
    body: ASTNode       # 循环体


# 块结构
@dataclass
class Block(ASTNode):
    """代码块"""
    statements: List[ASTNode]


# 特殊
@dataclass
class MathExpr(ASTNode):
    """数学表达式"""
    expr: str


@dataclass
class PythonCode(ASTNode):
    """Python代码块"""
    code: str


@dataclass
class Quote(ASTNode):
    """引用"""
    expr: ASTNode


# 类型注解系统
@dataclass
class TypeName(ASTNode):
    """类型名称"""
    name: str  # 类型名称，如 '数', '文', '列'


@dataclass
class TypeFunc(ASTNode):
    """函数类型"""
    param_types: List[ASTNode]  # 参数类型列表
    return_type: ASTNode        # 返回类型


@dataclass
class TypeList(ASTNode):
    """列表类型"""
    element_type: ASTNode  # 元素类型


# 其他节点（用于兼容性）
@dataclass
class Word(ASTNode):
    """单词/标识符"""
    name: str


@dataclass
class ListExpr(ASTNode):
    """列表表达式"""
    elements: List[ASTNode]


@dataclass
class ForLoop(ASTNode):
    """For循环"""
    var: str
    iterable: ASTNode
    body: ASTNode


@dataclass
class WhileLoop(ASTNode):
    """While循环"""
    condition: ASTNode
    body: ASTNode


@dataclass
class ReturnStmt(ASTNode):
    """返回语句"""
    value: ASTNode


class ReturnValue(Exception):
    """用于处理返回语句的异常"""
    def __init__(self, value):
        self.value = value


@dataclass
class TryStmt(ASTNode):
    """Try语句"""
    try_block: ASTNode
    error_var: str
    catch_block: ASTNode
    finally_block: Optional[ASTNode] = None  # 新增finally块支持


@dataclass
class ThrowStmt(ASTNode):
    """Throw语句"""
    value: ASTNode


@dataclass
class Eval(ASTNode):
    """求值表达式"""
    expr: ASTNode


@dataclass
class MacroDef(ASTNode):
    """宏定义"""
    name: str
    params: List[str]
    body: ASTNode


@dataclass
class ExportStmt(ASTNode):
    """导出语句"""
    names: List[str]


# 模块系统
@dataclass
class Import(ASTNode):
    """导入语句"""
    module: str           # 模块路径
    alias: Optional[str] = None  # 别名
    items: Optional[List[str]] = None  # 导入的项目


@dataclass
class Export(ASTNode):
    """导出语句"""
    items: List[str]      # 导出的名称
    default: Optional[str] = None  # 默认导出


@dataclass
class Module(ASTNode):
    """模块定义"""
    name: str             # 模块名称
    body: List[ASTNode]   # 模块体


# 结构体系统
@dataclass
class StructDef(ASTNode):
    """结构体定义"""
    name: str                    # 结构体名称
    fields: List[tuple]          # 字段列表 [(name, type), ...]
    methods: List[ASTNode] = None  # 方法列表


@dataclass
class StructInstance(ASTNode):
    """结构体实例"""
    struct_name: str             # 结构体名称
    fields: dict                 # 字段值 {name: value, ...}


@dataclass
class FieldAccess(ASTNode):
    """字段访问"""
    obj: ASTNode                 # 对象
    field: str                   # 字段名


@dataclass
class FieldSet(ASTNode):
    """字段设置"""
    obj: ASTNode                 # 对象
    field: str                   # 字段名
    value: ASTNode               # 新值


# 异常处理
@dataclass
class Try(ASTNode):
    """try语句"""
    try_block: ASTNode           # try块
    error_var: str               # 错误变量名
    catch_block: ASTNode         # catch块
    finally_block: Optional[ASTNode] = None  # finally块（可选）


@dataclass
class Throw(ASTNode):
    """抛出异常"""
    error: ASTNode               # 错误值


# 程序
@dataclass
class Program(ASTNode):
    """程序"""
    statements: List[ASTNode]


def ast_to_string(node: ASTNode, indent: int = 0) -> str:
    """将AST转换为字符串表示"""
    prefix = "  " * indent
    
    if isinstance(node, Num):
        return f"{prefix}Num({node.value})"
    
    elif isinstance(node, Str):
        return f"{prefix}Str({node.value!r})"
    
    elif isinstance(node, Bool):
        return f"{prefix}Bool({node.value})"
    
    elif isinstance(node, Nil):
        return f"{prefix}Nil()"
    
    elif isinstance(node, Ident):
        return f"{prefix}Ident({node.name})"
    
    elif isinstance(node, Call):
        args_str = ", ".join(ast_to_string(arg, 0) for arg in node.args)
        return f"{prefix}Call({node.verb}, [{args_str}])"
    
    elif isinstance(node, Pipeline):
        left_str = ast_to_string(node.left, 0)
        right_str = ast_to_string(node.right, 0)
        return f"{prefix}Pipeline(\n{ast_to_string(node.left, indent+1)},\n{ast_to_string(node.right, indent+1)}\n{prefix})"
    
    elif isinstance(node, Define):
        return f"{prefix}Define({node.name},\n{ast_to_string(node.value, indent+1)}\n{prefix})"
    
    elif isinstance(node, Assign):
        return f"{prefix}Assign({node.name},\n{ast_to_string(node.value, indent+1)}\n{prefix})"
    
    elif isinstance(node, Lambda):
        params_str = ", ".join(node.params)
        return f"{prefix}Lambda([{params_str}],\n{ast_to_string(node.body, indent+1)}\n{prefix})"
    
    elif isinstance(node, If):
        return f"{prefix}If(\n{ast_to_string(node.condition, indent+1)},\n{ast_to_string(node.then_branch, indent+1)},\n{ast_to_string(node.else_branch, indent+1)}\n{prefix})"
    
    elif isinstance(node, ForEach):
        return f"{prefix}ForEach({node.var},\n{ast_to_string(node.iterable, indent+1)},\n{ast_to_string(node.body, indent+1)}\n{prefix})"
    
    elif isinstance(node, While):
        return f"{prefix}While(\n{ast_to_string(node.condition, indent+1)},\n{ast_to_string(node.body, indent+1)}\n{prefix})"
    
    elif isinstance(node, Block):
        stmts_str = ",\n".join(ast_to_string(stmt, indent+1) for stmt in node.statements)
        return f"{prefix}Block([\n{stmts_str}\n{prefix}])"
    
    elif isinstance(node, MathExpr):
        return f"{prefix}MathExpr({node.expr!r})"
    
    elif isinstance(node, PythonCode):
        return f"{prefix}PythonCode({node.code!r})"
    
    elif isinstance(node, Quote):
        return f"{prefix}Quote(\n{ast_to_string(node.expr, indent+1)}\n{prefix})"
    
    elif isinstance(node, Program):
        stmts_str = ",\n".join(ast_to_string(stmt, indent+1) for stmt in node.statements)
        return f"{prefix}Program([\n{stmts_str}\n{prefix}])"
    
    else:
        return f"{prefix}Unknown({type(node).__name__})"


# 测试代码
if __name__ == '__main__':
    # 构建一个简单的AST
    ast = Program([
        Define('x', Num(5)),
        Define('y', Call('加', [Ident('x'), Num(3)])),
        Call('印', [Ident('y')])
    ])
    
    print(ast_to_string(ast))
