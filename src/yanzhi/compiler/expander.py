# -*- coding: utf-8 -*-
"""知行语言宏展开器

实现宏的编译时展开，包括：
- 宏调用检测
- 参数替换
- 递归展开
"""
from __future__ import annotations

from typing import Any

from yanzhi.compiler.ast import *
from yanzhi.runtime.macro_env import MacroEnvironment


class MacroExpander:
    """宏展开器

    在编译时展开宏调用，替换为宏体。
    """

    def __init__(self, macro_env: MacroEnvironment):
        self.macro_env = macro_env

    def expand(self, node: Node) -> Node:
        """展开 AST 中的所有宏调用"""
        if isinstance(node, Program):
            return self._expand_program(node)
        elif isinstance(node, MacroDef):
            # 宏定义不需要展开
            return node
        elif isinstance(node, Word):
            # 无参数宏调用：标识符引用宏名时，展开为宏体
            if self.macro_env.has(node.name):
                macro = self.macro_env.get(node.name)
                if len(macro.params) == 0:
                    return self._expand_macro_call(macro, [])
            return node
        elif isinstance(node, Define):
            return Define(name=node.name, value=self.expand(node.value), prefix=node.prefix, type_annot=node.type_annot)
        elif isinstance(node, Assign):
            return Assign(name=node.name, value=self.expand(node.value))
        elif isinstance(node, Lambda):
            return Lambda(params=node.params, body=self.expand(node.body), type_annot=node.type_annot)
        elif isinstance(node, Block):
            return Block(statements=[self.expand(stmt) for stmt in node.statements])
        elif isinstance(node, If):
            return If(
                cond=self.expand(node.cond),
                then_branch=self.expand(node.then_branch),
                else_branch=self.expand(node.else_branch) if node.else_branch else None,
            )
        elif isinstance(node, ForLoop):
            return ForLoop(
                var=node.var,
                start=self.expand(node.start),
                end=self.expand(node.end),
                body=self.expand(node.body),
            )
        elif isinstance(node, WhileLoop):
            return WhileLoop(
                cond=self.expand(node.cond),
                body=self.expand(node.body),
            )
        elif isinstance(node, ReturnStmt):
            return ReturnStmt(value=self.expand(node.value))
        elif isinstance(node, TryStmt):
            return TryStmt(
                try_block=self.expand(node.try_block),
                catch_var=node.catch_var,
                catch_block=self.expand(node.catch_block),
                finally_block=self.expand(node.finally_block) if node.finally_block else None,
            )
        elif isinstance(node, ThrowStmt):
            return ThrowStmt(value=self.expand(node.value))
        elif isinstance(node, Call):
            return self._expand_call(node)
        elif isinstance(node, Pipeline):
            return Pipeline(steps=[self.expand(step) for step in node.steps])
        elif isinstance(node, Quote):
            # 引用不展开
            return node
        elif isinstance(node, Eval):
            # 求值引用不展开
            return node
        elif isinstance(node, ListExpr):
            return ListExpr(elements=[self.expand(e) for e in node.elements])
        else:
            # 字面值节点不需要展开
            return node

    def _expand_program(self, node: Program) -> Program:
        """展开程序中的所有语句"""
        statements = []
        for stmt in node.statements:
            statements.append(self.expand(stmt))
        return Program(statements=statements)

    def _expand_call(self, node: Call) -> Node:
        """展开函数调用（可能是宏调用）"""
        # 检查是否是宏调用
        if isinstance(node.verb, Word) and self.macro_env.has(node.verb.name):
            # 宏调用
            macro = self.macro_env.get(node.verb.name)
            return self._expand_macro_call(macro, node.args)
        else:
            # 普通函数调用，展开参数
            return Call(verb=self.expand(node.verb), args=[self.expand(arg) for arg in node.args])

    def _expand_macro_call(self, macro: MacroDef, args: list[Node]) -> Node:
        """展开宏调用

        将宏调用替换为宏体，参数替换为实际参数。
        如果解析器吞噬了过多参数，只取宏定义所需数量的参数。
        """
        # 参数数量调整：解析器可能吞噬了过多参数
        if len(args) > len(macro.params):
            # 只取前 N 个参数，多余的留给后续表达式
            args = args[:len(macro.params)]
        elif len(args) < len(macro.params):
            raise RuntimeError(f"宏 {macro.name} 期望 {len(macro.params)} 个参数，得到 {len(args)} 个")

        # 创建参数映射
        param_map = {param: arg for param, arg in zip(macro.params, args)}

        # 替换宏体中的参数
        expanded_body = self._replace_params(macro.body, param_map)

        # 递归展开
        return self.expand(expanded_body)

    def _replace_params(self, node: Node, param_map: dict[str, Node]) -> Node:
        """替换 AST 中的参数引用

        参数引用是 Word 节点，名称匹配参数名。
        """
        if isinstance(node, Word) and node.name in param_map:
            # 参数引用，替换为实际参数
            return param_map[node.name]
        elif isinstance(node, Program):
            return Program(statements=[self._replace_params(stmt, param_map) for stmt in node.statements])
        elif isinstance(node, Define):
            return Define(
                name=node.name,
                value=self._replace_params(node.value, param_map),
                prefix=node.prefix,
                type_annot=node.type_annot,
            )
        elif isinstance(node, MacroDef):
            # 宏定义中的参数不替换
            return node
        elif isinstance(node, Assign):
            return Assign(name=node.name, value=self._replace_params(node.value, param_map))
        elif isinstance(node, Lambda):
            return Lambda(params=node.params, body=self._replace_params(node.body, param_map))
        elif isinstance(node, Block):
            return Block(statements=[self._replace_params(stmt, param_map) for stmt in node.statements])
        elif isinstance(node, If):
            return If(
                cond=self._replace_params(node.cond, param_map),
                then_branch=self._replace_params(node.then_branch, param_map),
                else_branch=self._replace_params(node.else_branch, param_map) if node.else_branch else None,
            )
        elif isinstance(node, ForLoop):
            return ForLoop(
                var=node.var,
                start=self._replace_params(node.start, param_map),
                end=self._replace_params(node.end, param_map),
                body=self._replace_params(node.body, param_map),
            )
        elif isinstance(node, WhileLoop):
            return WhileLoop(
                cond=self._replace_params(node.cond, param_map),
                body=self._replace_params(node.body, param_map),
            )
        elif isinstance(node, ReturnStmt):
            return ReturnStmt(value=self._replace_params(node.value, param_map))
        elif isinstance(node, TryStmt):
            return TryStmt(
                try_block=self._replace_params(node.try_block, param_map),
                catch_var=node.catch_var,
                catch_block=self._replace_params(node.catch_block, param_map),
                finally_block=self._replace_params(node.finally_block, param_map) if node.finally_block else None,
            )
        elif isinstance(node, ThrowStmt):
            return ThrowStmt(value=self._replace_params(node.value, param_map))
        elif isinstance(node, Call):
            return Call(
                verb=self._replace_params(node.verb, param_map),
                args=[self._replace_params(arg, param_map) for arg in node.args],
            )
        elif isinstance(node, Pipeline):
            return Pipeline(steps=[self._replace_params(step, param_map) for step in node.steps])
        elif isinstance(node, Quote):
            # 引用中的参数也需要替换
            return Quote(expr=self._replace_params(node.expr, param_map))
        elif isinstance(node, Eval):
            return Eval(quote=Quote(expr=self._replace_params(node.quote.expr, param_map)))
        elif isinstance(node, ListExpr):
            return ListExpr(elements=[self._replace_params(e, param_map) for e in node.elements])
        else:
            # 字面值节点不需要替换
            return node
