"""
知行语言求值器
执行AST
"""

from typing import Any, Dict, List, Callable
from .builtin import get_builtin, is_builtin
from ..compiler.ast import *


class Curry:
    """柯里化闭包"""
    
    def __init__(self, func: Callable, args: List):
        self.func = func
        self.args = args
    
    def __call__(self, *more_args):
        all_args = self.args + list(more_args)
        try:
            return self.func(*all_args)
        except TypeError:
            # 参数仍然不足，返回新的闭包
            return Curry(self.func, all_args)
    
    def __repr__(self):
        return f"Curry({self.func.__name__}, {self.args})"


class Evaluator:
    """求值器"""
    
    def __init__(self):
        self.env: Dict[str, Any] = {}
        self.current_topic: str = ""  # 主题链：当前主题
        self.load_builtins()
    
    def load_builtins(self):
        """加载内置函数"""
        from .builtin import MANGLED_BUILTINS
        self.env.update(MANGLED_BUILTINS)
    
    def eval(self, node: ASTNode, env: Dict[str, Any] = None) -> Any:
        """求值"""
        if env is None:
            env = self.env

        if isinstance(node, Program):
            return self.eval_program(node, env)
        elif isinstance(node, Num):
            return self.eval_num(node, env)
        elif isinstance(node, Str):
            return self.eval_str(node, env)
        elif isinstance(node, Bool):
            return self.eval_bool(node, env)
        elif isinstance(node, Nil):
            return self.eval_nil(node, env)
        elif isinstance(node, Ident):
            return self.eval_ident(node, env)
        elif isinstance(node, Call):
            return self.eval_call(node, env)
        elif isinstance(node, Pipeline):
            return self.eval_pipeline(node, env)
        elif isinstance(node, Define):
            return self.eval_define(node, env)
        elif isinstance(node, Assign):
            return self.eval_assign(node, env)
        elif isinstance(node, Lambda):
            return self.eval_lambda(node, env)
        elif isinstance(node, If):
            return self.eval_if(node, env)
        elif isinstance(node, ForEach):
            return self.eval_foreach(node, env)
        elif isinstance(node, ForLoop):
            return self.eval_forloop(node, env)
        elif isinstance(node, While):
            return self.eval_while(node, env)
        elif isinstance(node, Block):
            return self.eval_block(node, env)
        elif isinstance(node, MathExpr):
            return self.eval_math_expr(node, env)
        elif isinstance(node, PythonCode):
            return self.eval_python_code(node, env)
        elif isinstance(node, Quote):
            return self.eval_quote(node, env)
        elif isinstance(node, Quasiquote):
            return self.eval_quasiquote(node, env)
        elif isinstance(node, Unquote):
            # Unquote 只能出现在 Quasiquote 内部，单独出现时求值其内容
            return self.eval(node.expr, env)
        elif isinstance(node, UnquoteSplicing):
            raise RuntimeError("展开嵌入 只能出现在 模板(...) 内部")
        elif isinstance(node, Try):
            return self.eval_try(node, env)
        elif isinstance(node, Throw):
            return self.eval_throw(node, env)
        elif isinstance(node, Import):
            return self.eval_import(node, env)
        elif isinstance(node, StructDef):
            return self.eval_struct_def(node, env)
        elif isinstance(node, StructInstance):
            return self.eval_struct_instance(node, env)
        elif isinstance(node, FieldAccess):
            return self.eval_field_access(node, env)
        elif isinstance(node, FieldSet):
            return self.eval_field_set(node, env)
        elif isinstance(node, ReturnStmt):
            return self.eval_return(node, env)
        elif isinstance(node, MacroDef):
            return self.eval_macro_def(node, env)
        else:
            raise RuntimeError(f"未知的AST节点类型: {type(node).__name__}")
    
    def eval_program(self, node: Program, env: Dict) -> Any:
        """求值程序"""
        result = None
        for stmt in node.statements:
            result = self.eval(stmt, env)
        return result
    
    def eval_num(self, node: Num, env: Dict) -> Any:
        """求值数字"""
        return node.value
    
    def eval_str(self, node: Str, env: Dict) -> Any:
        """求值字符串"""
        return node.value
    
    def eval_bool(self, node: Bool, env: Dict) -> Any:
        """求值布尔值"""
        return node.value
    
    def eval_nil(self, node: Nil, env: Dict) -> Any:
        """求值空值"""
        return None
    
    def eval_ident(self, node: Ident, env: Dict) -> Any:
        """求值标识符"""
        name = self.mangle_name(node.name)
        if name in env:
            return env[name]
        
        # V1 主题链：当标识符无法解析时，尝试分解
        # 如果当前主题已设置，且标识符以主题开头，则拆分为 "主题 + 动作"
        if self.current_topic and node.name.startswith(self.current_topic):
            topic_name = self.mangle_name(self.current_topic)
            if topic_name in env:
                topic_obj = env[topic_name]
                action = node.name[len(self.current_topic):]
                if action:
                    # 尝试将动作作为主题对象的方法/属性调用
                    from .structs import StructInstance
                    if isinstance(topic_obj, StructInstance):
                        try:
                            return topic_obj.get_field(action)
                        except KeyError:
                            pass
                    action_method = getattr(topic_obj, action, None)
                    if action_method is None:
                        action_method = getattr(topic_obj, self.mangle_name(action), None)
                    if action_method is not None:
                        if callable(action_method):
                            return action_method()
                        return action_method
                    raise RuntimeError(
                        f"未定义的变量: {node.name}（主题 {self.current_topic} 无属性 {action}）")
        
        raise RuntimeError(f"未定义的变量: {node.name}")
    
    def eval_call(self, node: Call, env: Dict) -> Any:
        """求值函数调用"""
        # 处理verb是Ident节点的情况
        if isinstance(node.verb, Ident):
            verb = node.verb.name
        else:
            verb = node.verb  # 不mangle，保留原始名称
        
        # 特殊处理：抛出异常
        if verb == '抛':
            args = [self.eval(arg, env) for arg in node.args]
            if args:
                raise Exception(args[0])
            raise Exception("抛出异常")

        # 特殊处理：求值引用（同像性）—— '行' 为旧接口，'执行' 为新接口
        if verb in ('行', '执行'):
            args = [self.eval(arg, env) for arg in node.args]
            if not args:
                return None
            ast_node = args[0]
            if isinstance(ast_node, ASTNode):
                # 对 AST 节点求值（代码即数据的核心）
                return self.eval(ast_node, env)
            # 如果传入的是字符串，先解析再求值（方便 REPL 使用）
            if isinstance(ast_node, str):
                from ..compiler.parser import parse
                return self.eval(parse(ast_node), env)
            return ast_node
        
        # 查找函数
        mangled_verb = self.mangle_name(verb)
        if mangled_verb in env:
            func = env[mangled_verb]
        else:
            raise RuntimeError(f"未定义的动词: {verb}")

        # 主题链：跟踪第一个Ident参数作为当前主题
        if node.args and isinstance(node.args[0], Ident):
            first_arg_name = node.args[0].name
            if first_arg_name and not first_arg_name[0].isascii():
                self.current_topic = first_arg_name

        # 特殊处理'使用'动词
        if verb == '使用':
            # '用'动词：第一个参数是函数，其余参数是参数
            if len(node.args) > 0:
                # 先求值第一个参数（函数）
                first_arg = node.args[0]
                first_func = self.eval(first_arg, env)

                # 检查是否是宏
                is_macro = False
                if callable(first_func):
                    try:
                        is_macro = first_func.__name__ == 'macro_closure'
                    except:
                        pass

                if is_macro:
                    # 宏调用：其余参数不求值
                    args = [first_func] + node.args[1:]
                else:
                    # 普通函数调用：求值所有参数
                    args = [first_func] + [self.eval(arg, env) for arg in node.args[1:]]
            else:
                # 没有参数
                args = []
        else:
            # 检查是否是宏（通过检查函数的__name__属性）
            is_macro = False
            if callable(func):
                try:
                    is_macro = func.__name__ == 'macro_closure'
                except:
                    pass

            if is_macro:
                # 宏调用：参数不求值，直接传递AST节点
                args = node.args
            else:
                # 普通函数调用：求值参数
                args = [self.eval(arg, env) for arg in node.args]

        # 调用函数（支持柯里化）
        return self.call_func(func, args)
    
    def eval_pipeline(self, node: Pipeline, env: Dict) -> Any:
        """求值管道操作"""
        # 求值左侧
        left_result = self.eval(node.left, env)
        
        # 将左侧结果注入到右侧
        if isinstance(node.right, Call):
            # 求值右侧的动词
            verb = self.mangle_name(node.right.verb)
            if verb in env:
                func = env[verb]
            else:
                raise RuntimeError(f"未定义的动词: {node.right.verb}")
            
            # 求值参数
            args = [self.eval(arg, env) for arg in node.right.args]
            
            # 特殊处理高阶函数
            # 高阶函数期望 (函数, 列表)，但管道操作提供 (列表, 函数)
            # 所以需要交换参数顺序
            if verb in ('映射', '过滤', '归约', '合并'):
                # 高阶函数：函数在前，列表在后
                all_args = args + [left_result]
            else:
                # 普通函数：列表在前，函数在后
                all_args = [left_result] + args
            
            # 调用函数
            return self.call_func(func, all_args)
        else:
            # 如果右侧不是调用，直接求值
            return self.eval(node.right, env)
    
    def eval_define(self, node: Define, env: Dict) -> Any:
        """求值变量定义"""
        name = self.mangle_name(node.name)
        value = self.eval(node.value, env)
        env[name] = value

        # 主题链：跟踪新定义的变量名作为当前主题
        if node.name and not node.name[0].isascii():
            self.current_topic = node.name

        # 如果定义的是宏，将宏名添加到动词列表
        if callable(value) and hasattr(value, '_param_count'):
            # 将宏名添加到parser的动词列表
            from ..compiler.parser import Parser
            if node.name not in Parser.VERB_ARITY:
                # 使用宏的参数数量
                Parser.VERB_ARITY[node.name] = value._param_count
        return value
    
    def eval_assign(self, node: Assign, env: Dict) -> Any:
        """求值变量赋值"""
        name = self.mangle_name(node.name)
        value = self.eval(node.value, env)
        env[name] = value

        # 主题链：跟踪赋值变量名作为当前主题
        if node.name and not node.name[0].isascii():
            self.current_topic = node.name

        return value
    
    def eval_lambda(self, node: Lambda, env: Dict) -> Any:
        """求值匿名函数"""
        params = [self.mangle_name(p) for p in node.params]
        body = node.body

        # 创建闭包
        def closure(*args):
            # 创建新的环境
            new_env = env.copy()

            # 绑定参数
            for param, arg in zip(params, args):
                new_env[param] = arg

            # 求值函数体，捕获返回异常
            try:
                return self.eval(body, new_env)
            except ReturnValue as ret:
                return ret.value

        return closure
    
    def eval_if(self, node: If, env: Dict) -> Any:
        """求值条件表达式"""
        condition = self.eval(node.condition, env)
        
        if condition:
            return self.eval(node.then_branch, env)
        else:
            return self.eval(node.else_branch, env)
    
    def eval_foreach(self, node: ForEach, env: Dict) -> Any:
        """求值遍历循环"""
        var = self.mangle_name(node.var)
        iterable = self.eval(node.iterable, env)

        result = None
        for item in iterable:
            # 创建新的环境
            new_env = env.copy()
            new_env[var] = item

            # 求值循环体，捕获返回语句
            try:
                result = self.eval(node.body, new_env)
            except ReturnValue as rv:
                return rv.value

        return result

    def eval_forloop(self, node: ForLoop, env: Dict) -> Any:
        """求值For循环（遍历i从1到10）"""
        var = self.mangle_name(node.var)
        iterable = self.eval(node.iterable, env)

        result = None
        for item in iterable:
            # 更新循环变量
            env[var] = item

            # 求值循环体，捕获返回语句
            try:
                result = self.eval(node.body, env)
            except ReturnValue as rv:
                return rv.value

        return result

    def eval_while(self, node: While, env: Dict) -> Any:
        """求值当循环"""
        result = None

        while self.eval(node.condition, env):
            # 求值循环体，捕获返回语句
            try:
                result = self.eval(node.body, env)
            except ReturnValue as rv:
                return rv.value

        return result
    
    def eval_block(self, node: Block, env: Dict) -> Any:
        """求值代码块"""
        result = None
        for stmt in node.statements:
            result = self.eval(stmt, env)
        return result
    
    def eval_math_expr(self, node: MathExpr, env: Dict) -> Any:
        """求值数学表达式"""
        # 在当前环境中求值数学表达式
        return eval(node.expr, {"__builtins__": {}}, env)

    def eval_python_code(self, node: PythonCode, env: Dict) -> Any:
        """求值Python代码块，支持变量回写和模块导入"""
        import textwrap

        # 保存执行前的变量列表
        before_vars = set(env.keys())

        # 创建Python执行环境，预导入常用模块
        py_env = {
            '__builtins__': __builtins__,
            'math': __import__('math'),
            'json': __import__('json'),
            're': __import__('re'),
            'os': __import__('os'),
            'sys': __import__('sys'),
            'random': __import__('random'),
            'datetime': __import__('datetime'),
        }
        # 复制当前环境变量
        py_env.update(env)

        # 处理多行代码的缩进
        code = textwrap.dedent(node.code).strip()

        # 执行Python代码
        try:
            exec(code, py_env)
        except Exception as e:
            raise Exception(f"Python代码执行错误: {e}")

        # 同步新变量到知行环境
        after_vars = set(py_env.keys())
        new_vars = after_vars - before_vars - {'__builtins__', 'math', 'json', 're', 'os', 'sys', 'random', 'datetime'}
        for var in new_vars:
            if not var.startswith('_'):  # 跳过私有变量
                env[var] = py_env[var]

        # 返回结果（如果有_result变量）
        return py_env.get('_result', None)
    
    def eval_quote(self, node: Quote, env: Dict) -> Any:
        """求值引用——返回 AST 节点本身（代码即数据）"""
        return node.expr

    def eval_quasiquote(self, node: Quasiquote, env: Dict) -> Any:
        """求值反引用模板——递归处理 Unquote / UnquoteSplicing 插值"""
        return self._expand_quasiquote(node.expr, env)

    def _expand_quasiquote(self, node: ASTNode, env: Dict) -> Any:
        """递归展开反引用模板中的插值节点"""
        if isinstance(node, Unquote):
            # 嵌入：对内部表达式求值，返回其结果（可以是任意值或 AST 节点）
            return self.eval(node.expr, env)

        if isinstance(node, UnquoteSplicing):
            # 展开嵌入：在列表上下文中使用，这里单独调用时报错
            raise RuntimeError("展开嵌入 必须在列表节点内部使用")

        if isinstance(node, Call):
            # 对 Call 的每个参数递归展开，并处理 UnquoteSplicing 展开
            new_args = []
            for arg in node.args:
                if isinstance(arg, UnquoteSplicing):
                    spliced = self.eval(arg.expr, env)
                    if not isinstance(spliced, list):
                        raise RuntimeError(f"展开嵌入 期望列表，得到 {type(spliced).__name__}")
                    # 将展开的值包装为 AST 节点
                    for item in spliced:
                        new_args.append(self._value_to_ast(item))
                else:
                    new_args.append(self._expand_quasiquote(arg, env))
            new_verb = self._expand_quasiquote(node.verb, env) if isinstance(node.verb, ASTNode) else node.verb
            return Call(new_verb, new_args)

        if isinstance(node, Block):
            return Block([self._expand_quasiquote(s, env) for s in node.statements])

        if isinstance(node, If):
            return If(
                self._expand_quasiquote(node.condition, env),
                self._expand_quasiquote(node.then_branch, env),
                self._expand_quasiquote(node.else_branch, env),
            )

        if isinstance(node, Define):
            return Define(node.name, self._expand_quasiquote(node.value, env))

        if isinstance(node, Lambda):
            return Lambda(node.params, self._expand_quasiquote(node.body, env))

        if isinstance(node, ListExpr):
            new_elems = []
            for elem in node.elements:
                if isinstance(elem, UnquoteSplicing):
                    spliced = self.eval(elem.expr, env)
                    if not isinstance(spliced, list):
                        raise RuntimeError(f"展开嵌入 期望列表")
                    for item in spliced:
                        new_elems.append(self._value_to_ast(item))
                else:
                    new_elems.append(self._expand_quasiquote(elem, env))
            return ListExpr(new_elems)

        # 字面量和标识符：原样返回（不插值）
        return node

    def _value_to_ast(self, value: Any) -> ASTNode:
        """将运行时值转换为 AST 节点（用于反引用插值）"""
        if isinstance(value, ASTNode):
            return value
        if isinstance(value, bool):
            return Bool(value)
        if value is None:
            return Nil()
        if isinstance(value, (int, float)):
            return Num(value)
        if isinstance(value, str):
            return Str(value)
        if isinstance(value, list):
            return ListExpr([self._value_to_ast(v) for v in value])
        # 无法转换为 AST，包装为字符串
        return Str(str(value))


    def eval_try(self, node: Try, env: Dict) -> Any:
        """求值try-catch-finally"""
        result = None
        exception = None

        try:
            result = self.eval(node.try_block, env)
        except ReturnValue:
            # 返回语句异常直接传播，但先执行finally
            if node.finally_block:
                self.eval(node.finally_block, env)
            raise
        except Exception as e:
            exception = e
            # 创建新的环境，绑定错误变量
            new_env = env.copy()
            # 如果异常有args，使用第一个参数，否则使用异常本身
            error_value = e.args[0] if e.args else str(e)
            new_env[node.error_var] = error_value
            try:
                result = self.eval(node.catch_block, new_env)
            except Exception as e2:
                exception = e2

        # finally块总是执行
        if node.finally_block:
            try:
                self.eval(node.finally_block, env)
            except Exception as e:
                # finally块中的异常覆盖之前的异常
                exception = e

        # 如果有未处理的异常，重新抛出
        if exception:
            raise exception

        return result
    
    def eval_throw(self, node: Throw, env: Dict) -> Any:
        """求值throw"""
        error = self.eval(node.error, env)
        raise Exception(error)

    def eval_return(self, node: ReturnStmt, env: Dict) -> Any:
        """求值返回语句"""
        # 检查是否为空值
        if node.value is None:
            raise ReturnValue(None)

        value = self.eval(node.value, env)

        # 检查是否为"空"关键字或Nil节点
        if isinstance(node.value, Nil):
            raise ReturnValue(None)

        # 检查是否为字符串"空"
        if isinstance(value, str) and value == '空':
            raise ReturnValue(None)

        raise ReturnValue(value)

    def eval_macro_def(self, node: MacroDef, env: Dict) -> Any:
        """求值宏定义——返回宏闭包（接收未求值的 AST 参数，展开后求值）"""
        params = node.params
        body = node.body
        macro_name = node.name  # 可能为空（匿名宏）

        # 捕获定义时的环境（词法作用域）
        captured_env = env

        def macro_closure(*args):
            """宏闭包：接收 AST 节点，替换后在捕获环境中求值"""
            # 参数数量校验
            if len(args) != len(params):
                raise RuntimeError(
                    f"宏 {macro_name or '匿名'} 期望 {len(params)} 个参数，"
                    f"得到 {len(args)} 个"
                )
            # 构建参数名 → AST 节点映射
            param_map = dict(zip(params, args))
            # 替换宏体中的参数占位符
            expanded_body = self.substitute_ast(body, param_map)
            # 对展开后的 AST 在调用时的环境求值
            try:
                return self.eval(expanded_body, env)
            except ReturnValue as ret:
                return ret.value

        # 标记为宏，供 eval_call 识别
        macro_closure.__name__ = 'macro_closure'
        macro_closure._param_count = len(params)
        macro_closure._macro_name = macro_name

        # 若有宏名，自动注册到当前环境（支持递归宏）
        if macro_name:
            mangled = self.mangle_name(macro_name)
            env[mangled] = macro_closure

        return macro_closure

    def substitute_ast(self, node: ASTNode, param_map: Dict[str, ASTNode]) -> ASTNode:
        """在AST中替换参数名为对应的AST节点"""
        if isinstance(node, Ident):
            # 如果标识符是参数名，替换为对应的AST
            if node.name in param_map:
                return param_map[node.name]
            return node
        elif isinstance(node, Num):
            return node
        elif isinstance(node, Str):
            return node
        elif isinstance(node, Bool):
            return node
        elif isinstance(node, Nil):
            return node
        elif isinstance(node, Call):
            # 递归替换调用中的参数
            new_args = [self.substitute_ast(arg, param_map) for arg in node.args]
            # 处理verb是Ident的情况
            new_verb = self.substitute_ast(node.verb, param_map) if isinstance(node.verb, Ident) else node.verb
            return Call(new_verb, new_args)
        elif isinstance(node, Pipeline):
            # 递归替换管道中的参数
            new_left = self.substitute_ast(node.left, param_map)
            new_right = self.substitute_ast(node.right, param_map)
            return Pipeline(new_left, new_right)
        elif isinstance(node, If):
            # 递归替换条件表达式中的参数
            new_condition = self.substitute_ast(node.condition, param_map)
            new_then = self.substitute_ast(node.then_branch, param_map)
            new_else = self.substitute_ast(node.else_branch, param_map)
            return If(new_condition, new_then, new_else)
        elif isinstance(node, Define):
            # 递归替换定义中的参数
            new_value = self.substitute_ast(node.value, param_map)
            return Define(node.name, new_value)
        elif isinstance(node, Assign):
            # 递归替换赋值中的参数
            new_value = self.substitute_ast(node.value, param_map)
            return Assign(node.name, new_value)
        elif isinstance(node, Block):
            # 递归替换块中的参数
            new_stmts = [self.substitute_ast(stmt, param_map) for stmt in node.statements]
            return Block(new_stmts)
        elif isinstance(node, Lambda):
            # Lambda不替换其参数
            new_body = self.substitute_ast(node.body, param_map)
            return Lambda(node.params, new_body)
        elif isinstance(node, Program):
            # 递归替换程序中的参数
            new_stmts = [self.substitute_ast(stmt, param_map) for stmt in node.statements]
            return Program(new_stmts)
        elif isinstance(node, Quote):
            # 引用内部不替换（保留引用语义）
            return node
        elif isinstance(node, Quasiquote):
            return Quasiquote(self.substitute_ast(node.expr, param_map))
        elif isinstance(node, Unquote):
            return Unquote(self.substitute_ast(node.expr, param_map))
        elif isinstance(node, UnquoteSplicing):
            return UnquoteSplicing(self.substitute_ast(node.expr, param_map))
        elif isinstance(node, ListExpr):
            return ListExpr([self.substitute_ast(e, param_map) for e in node.elements])
        elif isinstance(node, While):
            return While(self.substitute_ast(node.condition, param_map),
                         self.substitute_ast(node.body, param_map))
        elif isinstance(node, (ForEach, ForLoop)):
            return type(node)(node.var,
                              self.substitute_ast(node.iterable, param_map),
                              self.substitute_ast(node.body, param_map))
        else:
            # 其他节点类型不替换
            return node

    def eval_import(self, node: Import, env: Dict) -> Any:
        """求值import"""
        from .module_loader import import_module, import_items
        
        if node.items:
            # 选择性导入
            exports = import_items(node.module, node.items)
        else:
            # 导入整个模块
            exports = import_module(node.module, node.alias)
        
        # 将导入的内容添加到环境
        for name, value in exports.items():
            env[name] = value
        
        return None
    
    def eval_struct_def(self, node: StructDef, env: Dict) -> Any:
        """求值结构体定义"""
        from .structs import define_struct
        
        # 转换字段列表为字典
        fields = {name: type_name for name, type_name in node.fields}
        
        # 定义结构体
        definition = define_struct(node.name, fields, node.methods or {})
        
        # 将结构体构造函数添加到环境
        env[node.name] = lambda **kwargs: definition.create_instance(**kwargs)
        
        return definition
    
    def eval_struct_instance(self, node: StructInstance, env: Dict) -> Any:
        """求值结构体实例"""
        from .structs import create_struct
        
        # 求值字段值
        field_values = {}
        for name, value_expr in node.fields.items():
            field_values[name] = self.eval(value_expr, env)
        
        return create_struct(node.struct_name, **field_values)
    
    def eval_field_access(self, node: FieldAccess, env: Dict) -> Any:
        """求值字段访问"""
        from .structs import StructInstance
        
        obj = self.eval(node.obj, env)
        
        if isinstance(obj, StructInstance):
            return obj.get_field(node.field)
        elif isinstance(obj, dict):
            return obj.get(node.field)
        else:
            return getattr(obj, node.field)
    
    def eval_field_set(self, node: FieldSet, env: Dict) -> Any:
        """求值字段设置"""
        from .structs import StructInstance
        
        obj = self.eval(node.obj, env)
        value = self.eval(node.value, env)
        
        if isinstance(obj, StructInstance):
            return obj.set_field(node.field, value)
        elif isinstance(obj, dict):
            new_obj = obj.copy()
            new_obj[node.field] = value
            return new_obj
        else:
            setattr(obj, node.field, value)
            return obj
    
    def call_func(self, func: Callable, args: List) -> Any:
        """调用函数（支持柯里化）"""
        import inspect
        
        if isinstance(func, Curry):
            # 如果是柯里化闭包，直接调用
            return func(*args)
        
        # 尝试直接调用
        try:
            result = func(*args)
            # 如果结果是可调用的，说明函数返回了一个函数（柯里化）
            # 不需要再包装为Curry
            return result
        except TypeError as e:
            # 参数不足，返回柯里化闭包
            if "missing" in str(e) or "required" in str(e) or "positional" in str(e):
                return Curry(func, args)
            raise
    
    def mangle_name(self, name) -> str:
        """名称修饰"""
        # 处理Ident节点
        if isinstance(name, Ident):
            name = name.name
        
        if name.isascii():
            return name
        return f"_zh_{name}"


def evaluate(ast: ASTNode) -> Any:
    """求值函数"""
    # 如果输入是字符串，先解析
    if isinstance(ast, str):
        from yanzhi.compiler.parser import parse
        ast = parse(ast)
    
    evaluator = Evaluator()
    return evaluator.eval(ast)


# 测试代码
if __name__ == '__main__':
    import sys
    sys.path.insert(0, 'G:\\zhixing\\src')
    
    from yanzhi.compiler.parser import parse
    
    test_cases = [
        "定义x=5。",
        "定义y=5相加3。",
        "列表1 2 3，映射相乘2。",
        "如果5大于3那么1否则0。",
        "定义平方=函数x相乘x x。",
    ]
    
    for source in test_cases:
        print(f"\n源码: {source}")
        try:
            ast = parse(source)
            result = evaluate(ast)
            print(f"结果: {result}")
        except Exception as e:
            print(f"错误: {e}")
            import traceback
            traceback.print_exc()
