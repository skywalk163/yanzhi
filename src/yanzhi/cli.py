"""
知行语言命令行接口
"""

import sys
import os
import argparse
from typing import Optional

# 添加src到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from yanzhi.compiler.lexer import lex
from yanzhi.compiler.parser import parse
from yanzhi.runtime.compiler_bc import compile_to_bytecode
from yanzhi.runtime.vm import VM
from yanzhi.compiler.errors import YanError
from yanzhi.compiler.expander import MacroExpander
from yanzhi.runtime.macro_env import MacroEnvironment
from yanzhi.yan.dsl_factory import register_builtins

# 内置宏注册标志 & 全局宏环境单例
_BUILTIN_MACROS_REGISTERED = False
_GLOBAL_MACRO_ENV = None


def _collect_macros(ast, macro_env: MacroEnvironment):
    """从 AST 中提取宏定义并注册到宏环境"""
    from yanzhi.compiler.ast import Program, Define, MacroDef, Block
    def _walk(node):
        if isinstance(node, Program):
            for stmt in node.statements:
                _walk(stmt)
        elif isinstance(node, Block):
            for stmt in node.statements:
                _walk(stmt)
        elif isinstance(node, Define):
            if isinstance(node.value, MacroDef):
                macro_def = node.value
                macro_def.name = node.name  # 确保宏名与绑定名一致
                macro_env.set(node.name, macro_def)
    _walk(ast)


def _get_global_macro_env() -> MacroEnvironment:
    """获取全局宏环境（单例，内置宏只注册一次）"""
    global _BUILTIN_MACROS_REGISTERED, _GLOBAL_MACRO_ENV
    if _GLOBAL_MACRO_ENV is not None:
        return _GLOBAL_MACRO_ENV
    _GLOBAL_MACRO_ENV = MacroEnvironment()
    if not _BUILTIN_MACROS_REGISTERED:
        # 创建临时展开器用于注册内置成语
        temp_expander = MacroExpander(_GLOBAL_MACRO_ENV)
        try:
            register_builtins(temp_expander)
            _BUILTIN_MACROS_REGISTERED = True
        except Exception as e:
            import sys
            print(f"[警告] 内置成语注册失败: {e}", file=sys.stderr)
    return _GLOBAL_MACRO_ENV


class REPL:
    """交互式解释器"""
    
    def __init__(self):
        self.history = []
        self.vm = VM()  # 共享 VM 实例，变量跨行持久化
    
    def run(self):
        """运行REPL"""
        print("言知语言 REPL v0.1 (字节码 VM)")
        print("输入'退出'或'quit'退出，'帮助'或'help'查看帮助\n")
        
        while True:
            try:
                # 读取输入
                line = input("言知> ")
                
                # 处理命令
                if line.strip() in ('退出', 'quit', 'exit'):
                    print("再见！")
                    break
                
                if line.strip() in ('帮助', 'help'):
                    self.show_help()
                    continue
                
                if line.strip() in ('历史', 'history'):
                    self.show_history()
                    continue
                
                # 执行代码
                if line.strip():
                    result = self.execute(line)
                    if result is not None:
                        print(f"=> {result}")
                    
                    # 添加到历史
                    self.history.append(line)
            
            except KeyboardInterrupt:
                print("\n再见！")
                break
            except EOFError:
                print("\n再见！")
                break
            except Exception as e:
                print(f"错误: {e}")
    
    def execute(self, source: str):
        """执行代码（使用字节码 VM + 宏展开）"""
        try:
            # 词法分析
            tokens = lex(source)
            
            # 语法分析
            ast = parse(tokens)
            
            # 宏收集与展开
            macro_env = _get_global_macro_env()
            _collect_macros(ast, macro_env)
            expander = MacroExpander(macro_env)
            ast = expander.expand(ast)
            
            # 编译为字节码并执行
            chunk = compile_to_bytecode(ast)
            result = self.vm.run(chunk)
            
            return result
        
        except YanError as e:
            print(f"语法错误: {e}")
            return None
        except Exception as e:
            print(f"错误: {e}")
            return None
    
    def show_help(self):
        """显示帮助"""
        print("""
言知语言帮助

基本语法：
  定义 x = 5。          定义变量
  打印 5 + 3。          数学符号表达式
  列表 1 2 3，映射相乘2。    管道操作
  如果 x > 5 那么 x 否则 0。  条件表达式
  定义 f = 函数 n：n * n。。  函数定义

言律句式（自然语言）：
  循环当 真，就打印 "OK"。        条件触发
  回家的时候：打印 "进门"。    作用域块

动词：
  相加 相减 相乘 相除              算术运算
  大于 小于 等于                 比较运算（也可用 > < ==）
  列表 首个 剩余 长度              列表操作
  映射 过滤 归约 合并              高阶函数
  打印                       打印
""")
    
    def show_history(self):
        """显示历史"""
        if not self.history:
            print("历史为空")
            return
        
        for i, line in enumerate(self.history, 1):
            print(f"{i}: {line}")


def run_file(filename: str):
    """运行文件（使用字节码 VM + 宏展开）"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            source = f.read()
        
        # 词法分析
        tokens = lex(source)
        
        # 语法分析
        ast = parse(tokens)
        
        # 宏收集与展开
        macro_env = _get_global_macro_env()
        _collect_macros(ast, macro_env)
        expander = MacroExpander(macro_env)
        ast = expander.expand(ast)
        
        # 编译为字节码并执行
        chunk = compile_to_bytecode(ast)
        vm = VM()
        result = vm.run(chunk)
        
        return result
    
    except FileNotFoundError:
        print(f"错误: 文件不存在: {filename}")
        return None
    except YanError as e:
        print(f"语法错误: {e}")
        return None
    except Exception as e:
        print(f"错误: {e}")
        return None


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='知行语言编译器')
    parser.add_argument('file', nargs='?', help='要运行的文件')
    parser.add_argument('-c', '--code', help='直接执行代码')
    parser.add_argument('-i', '--interactive', action='store_true', help='启动交互式REPL')
    parser.add_argument('-v', '--version', action='version', version='言知语言 v0.1 (字节码 VM)')
    
    args = parser.parse_args()
    
    # 启动REPL
    if args.interactive or (not args.file and not args.code):
        repl = REPL()
        repl.run()
        return
    
    # 执行代码
    if args.code:
        repl = REPL()
        result = repl.execute(args.code)
        if result is not None:
            print(result)
        return
    
    # 运行文件
    if args.file:
        result = run_file(args.file)
        if result is not None:
            print(result)
        return


if __name__ == '__main__':
    main()
