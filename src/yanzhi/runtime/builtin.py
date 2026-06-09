"""
知行语言内置函数库
"""

import functools
from typing import Any, List, Callable


# 算术运算
def _add(x, y):
    """加法"""
    return x + y

def _sub(x, y):
    """减法"""
    return x - y

def _mul(x, y):
    """乘法"""
    return x * y

def _div(x, y):
    """除法"""
    return x / y

def _mod(x, y):
    """取模"""
    return x % y

def _pow(x, y):
    """幂运算"""
    return x ** y

def _neg(x):
    """取负"""
    return -x

def _abs(x):
    """绝对值"""
    return abs(x)


# 比较运算
def _gt(x, y=None):
    """大于"""
    if y is None:
        # 柯里化：返回函数，期望y，返回y > x
        # 注意：这里x是阈值，返回的函数期望要比较的值
        return lambda val: val > x
    return x > y

def _lt(x, y=None):
    """小于"""
    if y is None:
        return lambda y: y < x
    return x < y

def _eq(x, y=None):
    """等于"""
    if y is None:
        return lambda y: y == x
    return x == y

def _ne(x, y=None):
    """不等于"""
    if y is None:
        return lambda y: y != x
    return x != y

def _ge(x, y=None):
    """大于等于"""
    if y is None:
        return lambda y: y >= x
    return x >= y

def _le(x, y=None):
    """小于等于"""
    if y is None:
        return lambda y: y <= x
    return x <= y


# 逻辑运算
def _and(x, y):
    """逻辑与"""
    return x and y

def _or(x, y):
    """逻辑或"""
    return x or y

def _not(x):
    """逻辑非"""
    return not x


# 列表操作
def _list(*args):
    """创建列表"""
    return list(args)

def _head(lst):
    """取首元素"""
    return lst[0] if lst else None

def _tail(lst):
    """取余元素"""
    return lst[1:] if len(lst) > 1 else []

def _nth(lst, i):
    """索引访问"""
    return lst[i] if i < len(lst) else None

def _len(lst):
    """列表长度"""
    return len(lst)

def _append(lst, x):
    """追加元素"""
    return lst + [x]

def _concat(lst1, lst2):
    """连接列表"""
    return lst1 + lst2

def _contains(lst, x):
    """包含检查"""
    return x in lst

def _remove(lst, x):
    """删除元素"""
    return [item for item in lst if item != x]

def _is_empty(lst):
    """空检查"""
    return len(lst) == 0

def _range(start, end=None):
    """生成范围"""
    if end is None:
        return list(range(int(start)))
    return list(range(int(start), int(end)))


# 高阶函数
def _map(func, lst):
    """映射"""
    return list(map(func, lst))

def _filter(func, lst):
    """过滤"""
    return list(filter(func, lst))

def _reduce(func_or_curry, init_or_lst, lst=None):
    """归约"""
    from .evaluator import Curry
    
    # 处理不同的参数形式
    if lst is None:
        # 两个参数：可能是 (curry, lst) 或 (func, lst)
        if isinstance(func_or_curry, Curry):
            # Curry对象：提取函数和初始值
            curry = func_or_curry
            lst = init_or_lst
            # Curry对象包含函数和部分参数
            # 例如：Curry(_add, [0]) 表示 _add(0, ?)
            # 我们需要将其转换为 reduce 使用的函数
            func = curry.func
            partial_args = curry.args
            if len(partial_args) == 1:
                # 加(0) -> lambda x, y: x + y，初始值为0
                init = partial_args[0]
                return functools.reduce(func, lst, init)
            else:
                raise TypeError(f"不支持的Curry参数数量: {len(partial_args)}")
        else:
            # 普通函数：没有初始值
            return functools.reduce(func_or_curry, init_or_lst)
    else:
        # 三个参数：(func, init, lst)
        return functools.reduce(func_or_curry, lst, init_or_lst)

def _zip(lst1, lst2):
    """合并"""
    return list(zip(lst1, lst2))


# I/O
def _print(x):
    """打印"""
    print(x)
    return x


# 函数调用
def _apply(func_or_ast, *args):
    """应用函数"""
    # 如果第一个参数是AST节点，需要先求值
    # 但这里我们无法访问evaluator，所以假设func_or_ast已经是函数
    func = func_or_ast

    # 检查是否可调用
    if not callable(func):
        raise TypeError(f"'{type(func).__name__}'对象不可调用")

    # 检查是否是宏
    is_macro = False
    try:
        is_macro = func.__name__ == 'macro_closure'
    except:
        pass

    if is_macro:
        # 宏调用：args应该是AST节点，直接传递
        return func(*args)
    else:
        # 普通函数调用：args已经是求值后的值
        return func(*args)


# 字符串操作
def _str(x):
    """转字符串"""
    return str(x)

def _len_str(s):
    """字符串长度"""
    return len(s)

def _upper(s):
    """大写"""
    return s.upper()

def _lower(s):
    """小写"""
    return s.lower()

def _strip(s):
    """去除空白"""
    return s.strip()

def _split(s, sep=' '):
    """分割字符串"""
    return s.split(sep)

def _join(lst, sep=' '):
    """连接字符串"""
    # 如果第一个参数是字符串，则进行字符串拼接
    if isinstance(lst, str):
        return str(lst) + str(sep)
    # 否则进行列表连接
    return sep.join(str(x) for x in lst)

def _replace(s, old, new):
    """替换字符串"""
    return s.replace(old, new)

def _contains_str(s, sub):
    """包含子串"""
    return sub in s

def _starts_with(s, prefix):
    """以...开始"""
    return s.startswith(prefix)

def _ends_with(s, suffix):
    """以...结束"""
    return s.endswith(suffix)


# 数学函数
def _sqrt(x):
    """平方根"""
    import math
    return math.sqrt(x)

def _log(x, base=10):
    """对数"""
    import math
    if base == 10:
        return math.log10(x)
    return math.log(x, base)

def _exp(x):
    """指数"""
    import math
    return math.exp(x)

def _sin(x):
    """正弦"""
    import math
    return math.sin(x)

def _cos(x):
    """余弦"""
    import math
    return math.cos(x)

def _tan(x):
    """正切"""
    import math
    return math.tan(x)

def _floor(x):
    """向下取整"""
    import math
    return math.floor(x)

def _ceil(x):
    """向上取整"""
    import math
    return math.ceil(x)

def _round(x, n=0):
    """四舍五入"""
    return round(x, n)

def _min(lst):
    """最小值"""
    return min(lst)

def _max(lst):
    """最大值"""
    return max(lst)

def _sum(lst):
    """求和"""
    return sum(lst)


# 类型检查
def _is_num(x):
    """是否为数字"""
    return isinstance(x, (int, float))

def _is_str(x):
    """是否为字符串"""
    return isinstance(x, str)

def _is_list(x):
    """是否为列表"""
    return isinstance(x, list)

def _is_func(x):
    """是否为函数"""
    return callable(x)

def _type(x):
    """获取类型"""
    if isinstance(x, (int, float)):
        return '数'
    elif isinstance(x, str):
        return '文'
    elif isinstance(x, list):
        return '列'
    elif callable(x):
        return '函数'
    else:
        return '未知'


# 内置函数字典
BUILTINS = {
    # 函数调用
    '使用': _apply,
    
    # 算术运算
    '相加': _add,
    '相减': _sub,
    '相乘': _mul,
    '相除': _div,
    '取余': _mod,
    '乘方': _pow,
    '取负': _neg,
    '绝对': _abs,
    
    # 比较运算
    '大于': _gt,
    '小于': _lt,
    '等于': _eq,
    '不等': _ne,
    '大于等于': _ge,
    '小于等于': _le,
    
    # 逻辑运算
    '并且': _and,
    '或者': _or,
    '非也': _not,
    
    # 列表操作
    '列表': _list,
    '首个': _head,
    '剩余': _tail,
    '索引': _nth,
    '取': _nth,  # 数组索引
    '长度': _len,
    '添加': _append,
    '连接': _concat,
    '包含': _contains,
    '删除': _remove,
    '空值': _is_empty,
    '范围': _range,
    
    # 高阶函数
    '映射': _map,
    '过滤': _filter,
    '归约': _reduce,
    '合并': _zip,
    
    # I/O
    '打印': _print,

    # 谓词函数
    '是数': lambda x: isinstance(x, (int, float)),
    '是文': lambda x: isinstance(x, str),
    '是列': lambda x: isinstance(x, list),
    '是空': lambda x: x is None or (isinstance(x, (list, str)) and len(x) == 0),
    '是零': lambda x: x == 0,
    '是正': lambda x: x > 0,
    '是负': lambda x: x < 0,
    '是布尔': lambda x: isinstance(x, bool),
    '全真': lambda lst: all(lst) if isinstance(lst, list) else all(x for x in lst),
    '任真': lambda lst: any(lst) if isinstance(lst, list) else any(x for x in lst),
    '全假': lambda lst: not any(lst) if isinstance(lst, list) else not any(x for x in lst),

    # 序列操作
    '排序': lambda lst: sorted(lst),
    '反转': lambda lst: list(reversed(lst)),
    '去重': lambda lst: list(dict.fromkeys(lst)),
    '位置': lambda lst, x: lst.index(x) + 1 if x in lst else 0,  # 1-based索引
    '子列': lambda lst, start, end: lst[start-1:end],  # 1-based索引，含首含尾
    '拉链': lambda lst1, lst2: [list(pair) for pair in zip(lst1, lst2)],  # 返回列表的列表
    '交集': lambda lst1, lst2: list(set(lst1) & set(lst2)),
    '并集': lambda lst1, lst2: list(set(lst1) | set(lst2)),
    '差集': lambda lst1, lst2: list(set(lst1) - set(lst2)),

    # 数学函数
    '四舍五入': lambda x, n=0: round(x, n),
    '最小': lambda lst: min(lst) if isinstance(lst, list) else min(*lst),
    '最大': lambda lst: max(lst) if isinstance(lst, list) else max(*lst),
    '求和': lambda lst: sum(lst) if isinstance(lst, list) else sum(*lst),
    '求积': lambda lst: functools.reduce(lambda x, y: x * y, lst, 1),
    '展平': lambda lst: [item for sublist in lst for item in sublist] if all(isinstance(x, list) for x in lst) else lst,
    '枚举': lambda lst: list(enumerate(lst)),
    '分块': lambda lst, n: [lst[i:i+n] for i in range(0, len(lst), n)],
    '交错': lambda lst1, lst2: [val for pair in zip(lst1, lst2) for val in pair],

    # 字符串操作
    '子串': lambda s, start, end=None: s[start:end] if end else s[start:],
    '长度': lambda x: len(x),
    '截取': lambda s, start, end: s[start-1:end-1] if end else s[start-1:],  # 从1开始的索引
    
    # 字符串操作
    '转文': _str,
    '文长': _len_str,
    '大写': _upper,
    '小写': _lower,
    '去空': _strip,
    '分割': _split,
    '替换': _replace,
    '含文': _contains_str,
    '始为': _starts_with,

    # 同像性
    '行': lambda ast: ast,  # 占位符，实际在evaluator中处理
    '终为': _ends_with,
    
    # 数学函数
    '根': _sqrt,
    '对数': _log,
    '指数': _exp,
    '正弦': _sin,
    '余弦': _cos,
    '正切': _tan,
    '下整': _floor,
    '上整': _ceil,
    '四舍五入': _round,
    '最小': _min,
    '最大': _max,
    '求和': _sum,
    
    # 类型检查
    '为数': _is_num,
    '为文': _is_str,
    '为列': _is_list,
    '为函': _is_func,
    '类型': _type,
    
    # 字典操作
    '字典': lambda *args: dict(zip(args[::2], args[1::2])) if len(args) % 2 == 0 else {},
    '取值': lambda d, k, default=None: d.get(k, default) if isinstance(d, dict) else default,
    '设值': lambda d, k, v: {**d, k: v} if isinstance(d, dict) else {},
    '键列': lambda d: list(d.keys()) if isinstance(d, dict) else [],
    '值列': lambda d: list(d.values()) if isinstance(d, dict) else [],
    '项列': lambda d: list(d.items()) if isinstance(d, dict) else [],
    '有键': lambda d, k: k in d if isinstance(d, dict) else False,
    
    # 集合操作
    '集合': lambda *args: set(args),
    '子集': lambda a, b: a <= b if isinstance(a, set) and isinstance(b, set) else False,
    
    # 元组操作
    '元组': lambda *args: args,
    '解包': lambda t: list(t) if isinstance(t, tuple) else [],
    
    # 排序和查找
    '排序': lambda lst, key=None: sorted(lst, key=key) if isinstance(lst, list) else [],
    '反序': lambda lst: list(reversed(lst)) if isinstance(lst, list) else [],
    '查找': lambda obj, x: obj.find(x) + 1 if isinstance(obj, str) and obj.find(x) >= 0 else (obj.index(x) if isinstance(obj, list) and x in obj else (0 if isinstance(obj, str) else -1)),
    '计数': lambda lst, x: lst.count(x) if isinstance(lst, list) else 0,
    
    # 数值操作
    '取整': lambda x: int(x),
    '取余': lambda a, b: a % b,
    '整除': lambda a, b: a // b,
    '符号': lambda x: 1 if x > 0 else (-1 if x < 0 else 0),
    '介于': lambda x, a, b: a <= x <= b,
    
    # 字符串高级操作
    '格式化': lambda fmt, *args: fmt.format(*args),
    '重复': lambda s, n: s * n,
    '居中': lambda s, w, fill=' ': s.center(w, fill),
    '左对齐': lambda s, w, fill=' ': s.ljust(w, fill),
    '右对齐': lambda s, w, fill=' ': s.rjust(w, fill),
    '补零': lambda s, w: s.zfill(w),
    
    # 列表高级操作
    '切片': lambda lst, start, end=None: lst[start:end] if isinstance(lst, (list, str)) else [],
    '取前': lambda lst, n: lst[:n] if isinstance(lst, (list, str)) else [],
    '取后': lambda lst, n: lst[-n:] if isinstance(lst, (list, str)) else [],
    '跳过': lambda lst, n: lst[n:] if isinstance(lst, (list, str)) else [],
    '步长': lambda lst, step: lst[::step] if isinstance(lst, (list, str)) else [],
    '扁平': lambda lst: [item for sublist in lst for item in sublist] if isinstance(lst, list) else [],
    '去重': lambda lst: list(dict.fromkeys(lst)) if isinstance(lst, list) else [],
    '分组': lambda lst, n: [lst[i:i+n] for i in range(0, len(lst), n)] if isinstance(lst, list) else [],
}

# VM 字节码 VM 使用的短名别名（兼容 bytecode compiler）
BUILTINS.update({
    '尾': lambda lst: lst[-1] if lst else None,                   # last element
    '排': lambda lst: sorted(lst),                                # sort
    '反': lambda lst: list(reversed(lst)),                        # reverse
    '类': lambda x: '整数' if isinstance(x, int) else ('小数' if isinstance(x, float)
         else '文' if isinstance(x, str) else '列' if isinstance(x, list)
         else '函' if callable(x) else '未知'),                   # type
    '整': lambda x: int(x),                                       # to int
    '字': lambda x: str(x),                                       # to str
    '合': lambda lst, sep='': sep.join(str(x) for x in lst),     # join
})


# 文件I/O函数
def _read_file(filename):
    """读取文件"""
    with open(filename, 'r', encoding='utf-8') as f:
        return f.read()


def _write_file(filename, content):
    """写入文件"""
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(str(content))
    return content


def _append_file(filename, content):
    """追加文件"""
    with open(filename, 'a', encoding='utf-8') as f:
        f.write(str(content))
    return content


def _file_exists(filename):
    """文件是否存在"""
    import os
    return os.path.exists(filename)


def _delete_file(filename):
    """删除文件"""
    import os
    os.remove(filename)


def _list_dir(path='.'):
    """列出目录"""
    import os
    return os.listdir(path)


def _make_dir(path):
    """创建目录"""
    import os
    os.makedirs(path, exist_ok=True)


def _is_dir(path):
    """是否为目录"""
    import os
    return os.path.isdir(path)


def _is_file(path):
    """是否为文件"""
    import os
    return os.path.isfile(path)


def _join_path(*args):
    """连接路径"""
    import os
    return os.path.join(*args)


def _split_path(path):
    """分割路径"""
    import os
    return os.path.split(path)


def _getcwd():
    """获取当前目录"""
    import os
    return os.getcwd()


def _chdir(path):
    """改变目录"""
    import os
    os.chdir(path)


# 添加文件I/O到BUILTINS
BUILTINS.update({
    '读文件': _read_file,
    '写文件': _write_file,
    '追加文件': _append_file,
    '文件存在': _file_exists,
    '删文件': _delete_file,
    '列目录': _list_dir,
    '建目录': _make_dir,
    '为目录': _is_dir,
    '为文件': _is_file,
    '连路径': _join_path,
    '分路径': _split_path,
    '当前目录': _getcwd,
    '改目录': _chdir,
})

# 添加用户输入功能
def _input(prompt: str = '') -> str:
    """读取用户输入一行"""
    return input(prompt)

def _read_char(prompt: str = '') -> str:
    """读取单个字符"""
    if prompt:
        print(prompt, end='', flush=True)
    import sys
    char = sys.stdin.read(1)
    return char

def _read_key(prompt: str = '') -> str:
    """读取单个按键（非阻塞，适合游戏等场景）"""
    if prompt:
        print(prompt, end='', flush=True)
    try:
        # 尝试使用msvcrt（Windows）
        import msvcrt
        char = msvcrt.getch().decode('utf-8', errors='ignore')
        return char
    except ImportError:
        # Unix/Linux/Mac 使用termios
        import sys
        import tty
        import termios
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            char = sys.stdin.read(1)
            return char
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

def _read_line(prompt: str = '') -> str:
    """读取一行（同输入）"""
    return input(prompt)

def _read_int(prompt: str = '') -> int:
    """读取整数"""
    while True:
        try:
            return int(input(prompt))
        except ValueError:
            print("请输入有效的整数")

def _read_float(prompt: str = '') -> float:
    """读取浮点数"""
    while True:
        try:
            return float(input(prompt))
        except ValueError:
            print("请输入有效的数字")

def _read_yes_no(prompt: str = '') -> bool:
    """读取是/否确认"""
    response = input(prompt).strip().lower()
    return response in ['是', 'y', 'yes', '好', '对', '真', '1']

BUILTINS.update({
    '输入': _input,
    '读入': _input,
    '读行': _read_line,
    '读字符': _read_char,
    '读键': _read_key,
    '读整数': _read_int,
    '读小数': _read_float,
    '读确认': _read_yes_no,
    '确认': _read_yes_no,
})


# ── 代码即数据（同像性）内置函数 ──────────────────────────────────────────────

def _ast_to_source(node) -> str:
    """将 AST 节点转换为言知源码字符串（源码化）"""
    from ..compiler.ast import ast_to_source, ASTNode
    if not isinstance(node, ASTNode):
        return str(node)
    return ast_to_source(node)


def _ast_to_string(node) -> str:
    """将 AST 节点转换为调试字符串（树形结构）"""
    from ..compiler.ast import ast_to_string, ASTNode
    if not isinstance(node, ASTNode):
        return str(node)
    return ast_to_string(node)


def _ast_type(node) -> str:
    """返回 AST 节点的类型名称"""
    from ..compiler.ast import ASTNode
    if not isinstance(node, ASTNode):
        return type(node).__name__
    return type(node).__name__


def _ast_children(node) -> list:
    """返回 AST 节点的子节点列表"""
    from ..compiler.ast import (ASTNode, Call, Block, If, Define, Lambda,
                                 Pipeline, While, ForEach, ForLoop, ListExpr,
                                 Program, Quote, Quasiquote)
    if isinstance(node, Call):
        return list(node.args)
    if isinstance(node, Block):
        return list(node.statements)
    if isinstance(node, If):
        return [node.condition, node.then_branch, node.else_branch]
    if isinstance(node, (Define, Quote, Quasiquote)):
        return [node.value if isinstance(node, Define) else node.expr]
    if isinstance(node, Lambda):
        return [node.body]
    if isinstance(node, Pipeline):
        return [node.left, node.right]
    if isinstance(node, (While,)):
        return [node.condition, node.body]
    if isinstance(node, (ForEach, ForLoop)):
        return [node.iterable, node.body]
    if isinstance(node, ListExpr):
        return list(node.elements)
    if isinstance(node, Program):
        return list(node.statements)
    return []


def _is_ast(node) -> bool:
    """判断一个值是否是 AST 节点"""
    from ..compiler.ast import ASTNode
    return isinstance(node, ASTNode)


BUILTINS.update({
    '源码': _ast_to_source,       # AST → 源码字符串
    '语法树': _ast_to_string,     # AST → 调试树字符串
    '节点类型': _ast_type,         # 获取节点类型名
    '子节点': _ast_children,       # 获取子节点列表
    '是语法树': _is_ast,           # 判断是否为 AST 节点
})


# 名称修饰后的内置函数
MANGLED_BUILTINS = {}

for name, func in BUILTINS.items():
    # 添加原始名称
    MANGLED_BUILTINS[name] = func
    
    # 添加修饰后的名称
    if not name.isascii():
        MANGLED_BUILTINS[f"_zh_{name}"] = func


def get_builtin(name: str) -> Callable:
    """获取内置函数"""
    return MANGLED_BUILTINS.get(name)


def is_builtin(name: str) -> bool:
    """检查是否为内置函数"""
    return name in MANGLED_BUILTINS
