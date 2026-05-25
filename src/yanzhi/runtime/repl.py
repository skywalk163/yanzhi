# -*- coding: utf-8 -*-
"""知行语言 REPL（交互式求值环境）

支持：
- 多行输入（块结构）
- 变量持久化
- 错误恢复
- 中文友好提示
- 命令历史（:历史）
- 加载文件（:加载）
- 宏查看（:宏）
- 时间测量（:时间）
"""
from __future__ import annotations

import sys
import time
import os
from yanzhi.compiler.parser import parse, ParseError
from yanzhi.compiler.pre_tokenizer import tokenize
from yanzhi.compiler.expander import MacroExpander
from yanzhi.runtime.evaluator import Evaluator, YanError
from yanzhi.compiler.ast import ast_to_dict


class REPL:
    """知行语言交互式求值环境"""

    def __init__(self):
        self.evaluator = Evaluator()
        self.running = True
        self.history: list[str] = []  # 命令历史
        self.history_limit = 1000

    def run(self):
        """启动 REPL"""
        self._print_welcome()

        while self.running:
            try:
                # 读取输入
                source = self._read_input()
                if source is None:
                    continue
                if not source.strip():
                    continue

                # 处理 REPL 命令
                if self._handle_command(source):
                    continue

                # 记录历史
                self._add_history(source)

                # 解析
                ast = parse(source)

                # 宏收集和展开
                self.evaluator._collect_macros(ast)
                expander = MacroExpander(self.evaluator.macro_env)
                ast = expander.expand(ast)

                # 求值
                result = self.evaluator.eval(ast)

                # 输出结果
                if result is not None:
                    self._print_result(result)

            except ParseError as e:
                print(f"  语法错误: {e}")
            except YanError as e:
                print(f"  运行错误: {e}")
            except KeyboardInterrupt:
                print()
                print("  再见！")
                break
            except Exception as e:
                print(f"  错误: {type(e).__name__}: {e}")

    def _print_welcome(self):
        """打印欢迎信息"""
        print()
        print("  +----------------------------------+")
        print("  |   知行 语言 v0.1.0               |")
        print("  |   中文为骨，数学为翼             |")
        print("  |   输入 :帮助 查看使用说明        |")
        print("  +----------------------------------+")
        print()

    def _read_input(self) -> str | None:
        """读取用户输入（支持多行）"""
        try:
            line = input("知行> ")
        except EOFError:
            self.running = False
            return None

        if not line.strip():
            return None

        # 多行输入：如果行以 ： 结尾，继续读取
        lines = [line]
        while line.rstrip().endswith('：') or line.rstrip().endswith(':'):
            try:
                line = input("  ... ")
                lines.append(line)
            except EOFError:
                break

        return '\n'.join(lines)

    def _add_history(self, source: str) -> None:
        """添加到命令历史"""
        self.history.append(source)
        if len(self.history) > self.history_limit:
            self.history = self.history[-self.history_limit:]

    def _handle_command(self, source: str) -> bool:
        """处理 REPL 特殊命令，返回 True 表示已处理"""
        cmd = source.strip()

        if cmd in (':帮助', ':help', '：帮助'):
            self._print_help()
            return True

        if cmd in (':退出', ':quit', '：退出'):
            print("  再见！")
            self.running = False
            return True

        if cmd in (':环境', ':env', '：环境'):
            self._print_env()
            return True

        if cmd in (':历史', ':history', '：历史'):
            self._print_history()
            return True

        if cmd.startswith(':加载 ') or cmd.startswith(':load '):
            filepath = cmd.split(' ', 1)[1]
            self._load_file(filepath)
            return True

        if cmd in (':宏', ':macro', '：宏'):
            self._print_macros()
            return True

        if cmd.startswith(':时间 ') or cmd.startswith(':time '):
            code = cmd.split(' ', 1)[1]
            self._time_eval(code)
            return True

        if cmd.startswith(':词法 ') or cmd.startswith(':token '):
            code = cmd.split(' ', 1)[1]
            self._print_tokens(code)
            return True

        if cmd.startswith(':语法 ') or cmd.startswith(':ast '):
            code = cmd.split(' ', 1)[1]
            self._print_ast(code)
            return True

        return False

    def _print_help(self):
        """打印帮助信息"""
        print()
        print("  -- 知行语言快速入门 --")
        print()
        print("  基本运算:")
        print("    5加3。          -> 8")
        print("    10减5。         -> 5")
        print("    3乘4。          -> 12")
        print("    10除2。         -> 5")
        print("    2幂10。         -> 1024")
        print()
        print("  管道操作:")
        print("    10加5，乘2。    -> 30")
        print()
        print("  变量定义:")
        print("    定x=10。")
        print("    定张三=100。    (百家姓变量)")
        print()
        print("  函数定义:")
        print("    定加倍=函x乘x 2。")
        print("    定阶乘=函n：若n等1则1否则n乘阶乘n减1。。")
        print()
        print("  条件判断:")
        print("    若5大3则\"大\"否则\"小\"。")
        print()
        print("  列表操作:")
        print("    列1 2 3，皆乘2。    -> [2,4,6]")
        print("    列1 2 3 4 5，只大3。-> [4,5]")
        print()
        print("  REPL命令:")
        print("    :帮助 / :help    显示帮助")
        print("    :退出 / :quit    退出REPL")
        print("    :环境 / :env     查看当前环境")
        print("    :历史 / :history 查看命令历史")
        print("    :加载 / :load    加载源码文件")
        print("    :宏   / :macro   查看已定义宏")
        print("    :时间 / :time    测量执行时间")
        print("    :词法 <代码>     查看词法分析结果")
        print("    :语法 <代码>     查看AST")
        print()

    def _print_env(self):
        """打印当前环境"""
        env = self.evaluator.global_env
        print("  -- 当前环境 --")
        for name, val in sorted(env.bindings.items()):
            if isinstance(val, tuple) and len(val) == 2 and callable(val[1]):
                # 标准库函数，跳过
                continue
            print(f"    {name} = {val}")

    def _print_history(self):
        """打印命令历史"""
        if not self.history:
            print("  (无历史)")
            return
        print("  -- 命令历史 --")
        for i, entry in enumerate(self.history, 1):
            # 截断长行
            display = entry.replace('\n', ' ').strip()
            if len(display) > 60:
                display = display[:57] + '...'
            print(f"    {i:4d}  {display}")

    def _load_file(self, filepath: str) -> None:
        """加载并执行源码文件"""
        if not os.path.exists(filepath):
            print(f"  错误: 文件不存在: {filepath}")
            return

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                source = f.read()

            ast = parse(source)
            self.evaluator._collect_macros(ast)
            expander = MacroExpander(self.evaluator.macro_env)
            ast = expander.expand(ast)
            result = self.evaluator.eval(ast)
            print(f"  已加载: {filepath}")
            if result is not None:
                self._print_result(result)
        except ParseError as e:
            print(f"  语法错误: {e}")
        except YanError as e:
            print(f"  运行错误: {e}")
        except Exception as e:
            print(f"  错误: {type(e).__name__}: {e}")

    def _print_macros(self):
        """打印已定义的宏"""
        macro_env = self.evaluator.macro_env
        if not macro_env:
            print("  (无宏定义)")
            return
        print("  -- 已定义宏 --")
        for name, val in sorted(macro_env.items()):
            print(f"    {name} = {val}")

    def _time_eval(self, code: str) -> None:
        """测量代码执行时间"""
        try:
            ast = parse(code)
            self.evaluator._collect_macros(ast)
            expander = MacroExpander(self.evaluator.macro_env)
            ast = expander.expand(ast)

            start = time.perf_counter()
            result = self.evaluator.eval(ast)
            elapsed = time.perf_counter() - start

            if result is not None:
                self._print_result(result)
            print(f"  耗时: {elapsed*1000:.3f} 毫秒")
        except ParseError as e:
            print(f"  语法错误: {e}")
        except YanError as e:
            print(f"  运行错误: {e}")
        except Exception as e:
            print(f"  错误: {type(e).__name__}: {e}")

    def _print_tokens(self, code: str):
        """打印词法分析结果"""
        tokens = tokenize(code)
        print("  -- 词法分析 --")
        for tok in tokens:
            if tok.type.name not in ('EOF', 'NEWLINE'):
                print(f"    {tok.type.name:12s} {tok.value!r}")

    def _print_ast(self, code: str):
        """打印AST"""
        import json
        ast = parse(code)
        print("  -- AST --")
        print(json.dumps(ast_to_dict(ast), indent=2, ensure_ascii=False))

    def _print_result(self, result):
        """打印求值结果"""
        if isinstance(result, bool):
            print(f"  -> {'真' if result else '假'}")
        elif result is None:
            print(f"  -> 空")
        elif isinstance(result, list):
            print(f"  -> {result}")
        else:
            print(f"  -> {result}")
