"""
端到端集成测试 — lex → parse → compile → execute 全链路
验证所有示例文件能正确解析和执行
"""
import sys
import os
import io
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

import pytest
from yanzhi.compiler.lexer import lex
from yanzhi.compiler.parser import parse
from yanzhi.runtime.compiler_bc import compile_to_bytecode
from yanzhi.runtime.vm import VM

# 项目根目录
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
EXAMPLES_DIR = os.path.join(PROJECT_ROOT, 'examples')


def run_code(code):
    """执行言知代码并返回 (stdout, result, error)"""
    try:
        tokens = lex(code)
        ast = parse(tokens)
        chunk = compile_to_bytecode(ast)
        vm = VM()
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        try:
            result = vm.run(chunk)
            output = sys.stdout.getvalue()
            return (output, result, None)
        finally:
            sys.stdout = old_stdout
    except Exception as e:
        return ("", None, str(e))


class TestFullPipeline:

    def test_hello_world(self):
        """最简单的打印"""
        out, res, err = run_code('打印 "hello"。')
        assert err is None, f"出错: {err}"
        assert "hello" in out

    def test_arithmetic(self):
        """数学运算"""
        out, res, err = run_code('打印 1 + 2 * 3。')
        assert err is None, f"出错: {err}"
        assert "7" in out

    def test_variable_define_and_print(self):
        """定义变量并打印"""
        code = '定义 x = 42。 打印 x。'
        out, res, err = run_code(code)
        assert err is None, f"出错: {err}"
        assert "42" in out

    def test_if_else(self):
        """条件判断"""
        code = '定义 x = 10。 如果 x > 5 那么 打印 "大" 否则 打印 "小"。'
        out, res, err = run_code(code)
        assert err is None, f"出错: {err}"
        assert "大" in out

    def test_lambda(self):
        """Lambda 函数"""
        code = '定义 平方 = 函数 n：n * n。。 定义 r = 平方 5。 打印 r。'
        out, res, err = run_code(code)
        assert err is None, f"出错: {err}"
        assert "25" in out

    def test_recursive_factorial(self):
        """递归阶乘"""
        code = """
定义 阶乘 = 函数 n：
  如果 n <= 1 那么 1 否则 n * 阶乘(n - 1)。
。
定义 r = 阶乘 5。
打印 r。
"""
        out, res, err = run_code(code)
        assert err is None, f"出错: {err}"
        assert "120" in out

    def test_list_create(self):
        """创建列表"""
        out, res, err = run_code('打印 列表 1 2 3。')
        assert err is None, f"出错: {err}"
        assert "1, 2, 3" in out or "[1, 2, 3]" in out

    def test_list_operations(self):
        """列表操作"""
        code = """
定义 data = 列表 10 20 30 40 50。
打印 首个 data。
打印 长度 data。
"""
        out, res, err = run_code(code)
        assert err is None, f"出错: {err}"
        assert "10" in out
        assert "5" in out

    def test_while_loop(self):
        """循环当 语句"""
        code = """
定义 i = 0。
循环当 i < 3：
  打印 i。
  赋值 i = i + 1。
结束
"""
        out, res, err = run_code(code)
        assert err is None, f"出错: {err}"
        assert "0" in out and "1" in out and "2" in out

    def test_math_escape(self):
        """$(...) 数学表达式逃逸"""
        out, res, err = run_code('定义 r = $(abs(-5) + 10)。 打印 r。')
        assert err is None, f"出错: {err}"
        assert "15" in out

    def test_bubblesort(self):
        """冒泡排序完整示例"""
        with open(os.path.join(EXAMPLES_DIR, 'bubblesort.yan')) as f:
            code = f.read()
        out, res, err = run_code(code)
        assert err is None, f"出错: {err}"
        assert "排序前" in out
        assert "排序后" in out
        # 最终结果应为排序好的数组
        assert res == [1, 2, 3, 4, 5, 6, 7, 8, 9]

    def test_hanoi(self):
        """汉诺塔递归示例"""
        with open(os.path.join(EXAMPLES_DIR, 'hanoi.yan')) as f:
            code = f.read()
        out, res, err = run_code(code)
        assert err is None, f"出错: {err}"
        assert "完成" in str(res) or "完成" in out

    # === 标准库测试 ===

    def test_stdlib_sum(self):
        """求和标准库函数"""
        out, res, err = run_code('定义 s = 求和 列表 1 2 3 4 5。 打印 s。')
        assert err is None, f"出错: {err}"
        assert "15" in out

    def test_stdlib_sqrt(self):
        """开方标准库函数"""
        out, res, err = run_code('定义 r = 开方 100。 打印 r。')
        assert err is None, f"出错: {err}"
        assert "10" in out

    def test_stdlib_random(self):
        """随机标准库函数"""
        out, res, err = run_code('定义 r = 随机。 打印 r。')
        assert err is None, f"出错: {err}"
        r = float(out.strip())
        assert 0 <= r <= 1

    def test_stdlib_file_exists(self):
        """存在标准库函数"""
        out, res, err = run_code('定义 r = 存在 "run-tests.bat"。 打印 r。')
        assert err is None, f"出错: {err}"
        # 应输出 Python 的 True 值
        assert out.strip() in ('真', 'True')

    def test_stdlib_interval(self):
        """间隔标准库函数"""
        out, res, err = run_code('定义 r = 间隔 1 5。 打印 r。')
        assert err is None, f"出错: {err}"
        assert "[1, 2, 3, 4, 5]" in out

    def test_stdlib_dict(self):
        """字典标准库函数"""
        out, res, err = run_code('定义 d = 字典 "a" 1 "b" 2。 打印 d。')
        assert err is None, f"出错: {err}"
        assert "'a': 1" in out or '"a": 1' in out
