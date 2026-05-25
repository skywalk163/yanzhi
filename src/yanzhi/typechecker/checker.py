"""知行语言静态类型检查器

对 AST 进行类型检查，收集类型错误但不阻止运行。
支持：
- 变量定义的类型注解检查
- 函数调用的参数/返回类型检查
- 类型推断（从值推断类型）
"""
from __future__ import annotations

from typing import Any, Optional
from yanzhi.compiler.ast import (
    Node, Program, Define, Lambda, Call, Pipeline,
    Num, Str, Bool, Nil, ListExpr, If, ForLoop, WhileLoop,
    Block, ReturnStmt, TryStmt, ThrowStmt,
    TypeName, TypeFunc, TypeList,
    ImportStmt, ExportStmt, Assign, MacroDef, Word,
)
from yanzhi.errors import YanError


# ==================== 类型环境 ====================

class TypeEnv:
    """类型环境：变量名 -> 类型"""

    def __init__(self, parent: Optional[TypeEnv] = None):
        self.parent = parent
        self.bindings: dict[str, Node] = {}

    def get(self, name: str) -> Optional[Node]:
        """查找变量类型"""
        if name in self.bindings:
            return self.bindings[name]
        if self.parent:
            return self.parent.get(name)
        return None

    def set(self, name: str, type_node: Node) -> None:
        """绑定变量类型"""
        self.bindings[name] = type_node


# ==================== 类型推断 ====================

def infer_type(value: Any) -> Node:
    """从 Python 值推断知行类型"""
    if value is None:
        return TypeName(name='空')
    if isinstance(value, bool):
        return TypeName(name='布尔')
    if isinstance(value, int):
        return TypeName(name='整数')
    if isinstance(value, float):
        return TypeName(name='浮点')
    if isinstance(value, str):
        return TypeName(name='串')
    if isinstance(value, list):
        if value:
            elem_type = infer_type(value[0])
            return TypeList(element_type=elem_type)
        return TypeName(name='表')
    if callable(value) or isinstance(value, tuple):
        return TypeName(name='函')
    return TypeName(name='任意')


def infer_type_from_node(node: Node) -> Node:
    """从 AST 节点推断类型（静态推断）"""
    if isinstance(node, Num):
        if isinstance(node.value, int):
            return TypeName(name='整数')
        return TypeName(name='浮点')
    if isinstance(node, Str):
        return TypeName(name='串')
    if isinstance(node, Bool):
        return TypeName(name='布尔')
    if isinstance(node, Nil):
        return TypeName(name='空')
    if isinstance(node, ListExpr):
        if node.elements:
            elem_type = infer_type_from_node(node.elements[0])
            return TypeList(element_type=elem_type)
        return TypeName(name='表')
    if isinstance(node, Lambda):
        # 函数类型：从参数和返回值推断
        return TypeName(name='函')
    return TypeName(name='任意')


# ==================== 类型兼容性 ====================

def is_subtype(sub: Node, sup: Node) -> bool:
    """判断 sub 是否是 sup 的子类型

    类型层次：
    整数 < 数, 浮点 < 数
    """
    if isinstance(sub, TypeName) and isinstance(sup, TypeName):
        if sup.name == '任意':
            return True
        if sub.name == sup.name:
            return True
        # 整数/浮点 是 数 的子类型
        if sup.name == '数' and sub.name in ('整数', '浮点', '数'):
            return True
        return False

    if isinstance(sub, TypeList) and isinstance(sup, TypeList):
        return is_subtype(sub.element_type, sup.element_type)

    if isinstance(sub, TypeFunc) and isinstance(sup, TypeFunc):
        # 函数类型：参数逆变，返回值协变（简化：只检查返回值）
        if len(sub.param_types) != len(sup.param_types):
            return False
        return is_subtype(sub.return_type, sup.return_type)

    return True  # 未知类型默认兼容


# ==================== 类型检查器 ====================

class TypeChecker:
    """静态类型检查器

    遍历 AST，检查类型注解与实际值是否匹配。
    收集类型错误但不阻止运行。
    """

    def __init__(self):
        self.errors: list[dict] = []
        self.env = TypeEnv()
        self._init_builtin_types()

    def _init_builtin_types(self):
        """初始化内置动词的类型签名"""
        # 算术动词
        arith_type = TypeFunc(
            param_types=[TypeName(name='数'), TypeName(name='数')],
            return_type=TypeName(name='数'),
        )
        for verb in ('加', '减', '乘', '除', '模', '幂'):
            self.env.set(verb, arith_type)

        # 比较动词
        cmp_type = TypeFunc(
            param_types=[TypeName(name='任意'), TypeName(name='任意')],
            return_type=TypeName(name='布尔'),
        )
        for verb in ('大', '小', '等', '不等', '大等', '小等'):
            self.env.set(verb, cmp_type)

        # 逻辑动词
        logic_type = TypeFunc(
            param_types=[TypeName(name='布尔'), TypeName(name='布尔')],
            return_type=TypeName(name='布尔'),
        )
        for verb in ('且', '或'):
            self.env.set(verb, logic_type)

        # 一元动词
        self.env.set('非', TypeFunc(
            param_types=[TypeName(name='布尔')],
            return_type=TypeName(name='布尔'),
        ))
        self.env.set('负', TypeFunc(
            param_types=[TypeName(name='数')],
            return_type=TypeName(name='数'),
        ))

        # 列表动词
        self.env.set('首', TypeFunc(
            param_types=[TypeName(name='表')],
            return_type=TypeName(name='任意'),
        ))
        self.env.set('尾', TypeFunc(
            param_types=[TypeName(name='表')],
            return_type=TypeName(name='表'),
        ))
        self.env.set('长', TypeFunc(
            param_types=[TypeName(name='任意')],
            return_type=TypeName(name='整数'),
        ))
        self.env.set('添', TypeFunc(
            param_types=[TypeName(name='表'), TypeName(name='任意')],
            return_type=TypeName(name='表'),
        ))
        self.env.set('连', TypeFunc(
            param_types=[TypeName(name='表'), TypeName(name='表')],
            return_type=TypeName(name='表'),
        ))

        # 字符串动词
        self.env.set('拼', TypeFunc(
            param_types=[TypeName(name='串'), TypeName(name='串')],
            return_type=TypeName(name='串'),
        ))

        # IO
        self.env.set('印', TypeFunc(
            param_types=[TypeName(name='任意')],
            return_type=TypeName(name='空'),
        ))

    def check(self, node: Node) -> list[dict]:
        """检查 AST 的类型，返回错误列表"""
        self.errors = []
        self._check(node)
        return self.errors

    def _add_error(self, msg: str, node: Node = None) -> None:
        """添加类型错误"""
        self.errors.append({
            'message': msg,
            'type': 'type_error',
        })

    def _check(self, node: Node) -> Optional[Node]:
        """检查节点类型，返回推断的类型"""
        if isinstance(node, Program):
            for stmt in node.statements:
                self._check(stmt)
            return None

        if isinstance(node, Block):
            child_env = TypeEnv(parent=self.env)
            old_env = self.env
            self.env = child_env
            for stmt in node.statements:
                self._check(stmt)
            self.env = old_env
            return None

        if isinstance(node, Define):
            return self._check_define(node)

        if isinstance(node, Assign):
            value_type = self._check(node.value)
            expected = self.env.get(node.name)
            if expected and value_type:
                if not is_subtype(value_type, expected):
                    self._add_error(
                        f"赋值类型不匹配：变量 '{node.name}' 期望 {self._type_str(expected)}，实际 {self._type_str(value_type)}"
                    )
            return value_type

        if isinstance(node, Lambda):
            return self._check_lambda(node)

        if isinstance(node, Call):
            return self._check_call(node)

        if isinstance(node, Pipeline):
            result_type = None
            for step in node.steps:
                result_type = self._check(step)
            return result_type

        if isinstance(node, If):
            self._check(node.cond)
            then_type = self._check(node.then_branch)
            if node.else_branch:
                self._check(node.else_branch)
            return then_type

        if isinstance(node, ForLoop):
            self._check(node.iterable)
            child_env = TypeEnv(parent=self.env)
            old_env = self.env
            self.env = child_env
            if node.var_name:
                self.env.set(node.var_name, TypeName(name='任意'))
            self._check(node.body)
            self.env = old_env
            return None

        if isinstance(node, WhileLoop):
            self._check(node.cond)
            self._check(node.body)
            return None

        if isinstance(node, ReturnStmt):
            if node.value:
                return self._check(node.value)
            return TypeName(name='空')

        if isinstance(node, TryStmt):
            self._check(node.try_block)
            if node.catch_block:
                self._check(node.catch_block)
            if node.finally_block:
                self._check(node.finally_block)
            return None

        if isinstance(node, ThrowStmt):
            if node.value:
                self._check(node.value)
            return None

        if isinstance(node, ListExpr):
            elem_type = TypeName(name='任意')
            if node.elements:
                elem_type = self._check(node.elements[0])
                for elem in node.elements[1:]:
                    self._check(elem)
            return TypeList(element_type=elem_type)

        if isinstance(node, ImportStmt) or isinstance(node, ExportStmt):
            return None

        if isinstance(node, MacroDef):
            return None

        # 字面值
        return infer_type_from_node(node)

    def _check_define(self, node: Define) -> Node:
        """检查变量定义的类型"""
        value_type = self._check(node.value)

        if node.type_annot:
            # 有类型注解，检查值是否匹配
            if value_type and not is_subtype(value_type, node.type_annot):
                self._add_error(
                    f"类型不匹配：变量 '{node.name}' 注解为 {self._type_str(node.type_annot)}，"
                    f"但值推断为 {self._type_str(value_type)}"
                )
            self.env.set(node.name, node.type_annot)
            return node.type_annot
        else:
            # 无类型注解，推断类型
            if value_type:
                self.env.set(node.name, value_type)
            return value_type

    def _check_lambda(self, node: Lambda) -> Node:
        """检查函数定义的类型"""
        child_env = TypeEnv(parent=self.env)
        old_env = self.env
        self.env = child_env

        # 绑定参数类型
        for i, param in enumerate(node.params):
            if node.type_annot and isinstance(node.type_annot, TypeFunc):
                if i < len(node.type_annot.param_types):
                    self.env.set(param, node.type_annot.param_types[i])
                else:
                    self.env.set(param, TypeName(name='任意'))
            else:
                self.env.set(param, TypeName(name='任意'))

        # 检查函数体
        body_type = self._check(node.body)

        self.env = old_env

        # 构造函数类型
        if node.type_annot:
            return node.type_annot

        param_types = [TypeName(name='任意') for _ in node.params]
        return_type = body_type or TypeName(name='任意')
        return TypeFunc(param_types=param_types, return_type=return_type)

    def _check_call(self, node: Call) -> Node:
        """检查函数调用的类型"""
        # 检查动词的类型签名
        verb_name = None
        if isinstance(node.verb, Word):
            verb_name = node.verb.name
        elif isinstance(node.verb, str):
            verb_name = node.verb

        if verb_name:
            func_type = self.env.get(verb_name)
            if func_type and isinstance(func_type, TypeFunc):
                # 检查参数数量
                if len(node.args) != len(func_type.param_types):
                    self._add_error(
                        f"参数数量不匹配：动词 '{verb_name}' 期望 {len(func_type.param_types)} 个参数，"
                        f"实际 {len(node.args)} 个"
                    )
                else:
                    # 检查参数类型
                    for i, arg in enumerate(node.args):
                        arg_type = self._check(arg)
                        if arg_type and not is_subtype(arg_type, func_type.param_types[i]):
                            self._add_error(
                                f"参数类型不匹配：动词 '{verb_name}' 第{i+1}个参数期望 "
                                f"{self._type_str(func_type.param_types[i])}，"
                                f"实际 {self._type_str(arg_type)}"
                            )
                return func_type.return_type

        # 检查参数
        for arg in node.args:
            self._check(arg)

        return TypeName(name='任意')

    @staticmethod
    def _type_str(type_node: Node) -> str:
        """将类型节点转为可读字符串"""
        if isinstance(type_node, TypeName):
            return type_node.name
        if isinstance(type_node, TypeFunc):
            params = ', '.join(TypeChecker._type_str(t) for t in type_node.param_types)
            ret = TypeChecker._type_str(type_node.return_type)
            return f"({params}) -> {ret}"
        if isinstance(type_node, TypeList):
            elem = TypeChecker._type_str(type_node.element_type)
            return f"表<{elem}>"
        return '?'


# ==================== 便捷函数 ====================

def check_types(source: str) -> list[dict]:
    """对源码进行类型检查，返回错误列表"""
    from yanzhi.compiler.pre_tokenizer import PreTokenizer
    from yanzhi.compiler.parser import Parser

    tokens = PreTokenizer(source).tokenize()
    ast = Parser(tokens).parse()

    checker = TypeChecker()
    return checker.check(ast)
