# -*- coding: utf-8 -*-
"""
增强的运行时功能

扩展知行语言运行时，添加更多内置函数和优化。
"""

import math
import random
from typing import Any, List, Callable


# ==================== 增强的数学函数 ====================

def enhanced_math_functions():
    """增强的数学函数"""
    return {
        # 基础数学
        '绝对': (1, lambda x: abs(x)),
        '最大': (2, lambda x, y: max(x, y)),
        '最小': (2, lambda x, y: min(x, y)),
        '乘方': (2, lambda x, y: x ** y),
        '开方': (1, lambda x: math.sqrt(x)),
        '四舍五入': (1, lambda x: round(x)),
        '向下取整': (1, lambda x: math.floor(x)),
        '向上取整': (1, lambda x: math.ceil(x)),
        
        # 三角函数
        '正弦': (1, lambda x: math.sin(x)),
        '余弦': (1, lambda x: math.cos(x)),
        '正切': (1, lambda x: math.tan(x)),
        '反正弦': (1, lambda x: math.asin(x)),
        '反余弦': (1, lambda x: math.acos(x)),
        '反正切': (1, lambda x: math.atan(x)),
        
        # 对数函数
        '对数': (1, lambda x: math.log(x)),
        '自然对数': (1, lambda x: math.log(x)),
        '常用对数': (1, lambda x: math.log10(x)),
        '二进制对数': (1, lambda x: math.log2(x)),
        '指数': (1, lambda x: math.exp(x)),
        
        # 双曲函数
        '双曲正弦': (1, lambda x: math.sinh(x)),
        '双曲余弦': (1, lambda x: math.cosh(x)),
        '双曲正切': (1, lambda x: math.tanh(x)),
        
        # 数学常量
        '圆周率': (0, lambda: math.pi),
        '自然常数': (0, lambda: math.e),
        '无穷': (0, lambda: math.inf),
    }


# ==================== 增强的列表函数 ====================

def enhanced_list_functions():
    """增强的列表函数"""
    
    def _range(start, end=None, step=1):
        """范围生成"""
        if end is None:
            return list(range(start))
        return list(range(start, end, step))
    
    def _take(lst, n):
        """取前n个元素"""
        return lst[:n]
    
    def _drop(lst, n):
        """丢弃前n个元素"""
        return lst[n:]
    
    def _reverse(lst):
        """反转列表"""
        return lst[::-1]
    
    def _sort(lst, key=None):
        """排序列表"""
        return sorted(lst, key=key)
    
    def _zip(*lists):
        """压缩多个列表"""
        return list(zip(*lists))
    
    def _flatten(lst):
        """展平嵌套列表"""
        result = []
        for item in lst:
            if isinstance(item, list):
                result.extend(_flatten(item))
            else:
                result.append(item)
        return result
    
    def _unique(lst):
        """去重"""
        seen = set()
        result = []
        for item in lst:
            if item not in seen:
                seen.add(item)
                result.append(item)
        return result
    
    def _group_by(lst, key_func):
        """分组"""
        groups = {}
        for item in lst:
            key = key_func(item)
            if key not in groups:
                groups[key] = []
            groups[key].append(item)
        return groups
    
    return {
        '范围': (1, _range),  # 支持range(n)和range(start, end)
        '取': (2, _take),
        '丢弃': (2, _drop),
        '反转': (1, _reverse),
        '排序': (1, _sort),
        '压缩': (2, _zip),
        '展平': (1, _flatten),
        '去重': (1, _unique),
        '分组': (2, _group_by),
    }


# ==================== 增强的字符串函数 ====================

def enhanced_string_functions():
    """增强的字符串函数"""
    
    def _split(s, sep=' '):
        """分割字符串"""
        return s.split(sep)
    
    def _join(lst, sep=''):
        """连接字符串列表"""
        return sep.join(str(x) for x in lst)
    
    def _trim(s):
        """去除首尾空白"""
        return s.strip()
    
    def _upper(s):
        """转大写"""
        return s.upper()
    
    def _lower(s):
        """转小写"""
        return s.lower()
    
    def _replace(s, old, new):
        """替换字符串"""
        return s.replace(old, new)
    
    def _contains(s, sub):
        """包含检查"""
        return sub in s
    
    def _starts_with(s, prefix):
        """前缀检查"""
        return s.startswith(prefix)
    
    def _ends_with(s, suffix):
        """后缀检查"""
        return s.endswith(suffix)
    
    return {
        '分割': (2, _split),
        '连接': (2, _join),
        '去空白': (1, _trim),
        '大写': (1, _upper),
        '小写': (1, _lower),
        '替换': (3, _replace),
        '包含': (2, _contains),
        '前缀': (2, _starts_with),
        '后缀': (2, _ends_with),
    }


# ==================== 增强的随机函数 ====================

def enhanced_random_functions():
    """增强的随机函数"""
    
    def _randint(a, b):
        """随机整数"""
        return random.randint(a, b)
    
    def _random():
        """随机小数"""
        return random.random()
    
    def _choice(lst):
        """随机选择"""
        return random.choice(lst)
    
    def _shuffle(lst):
        """随机打乱"""
        result = lst.copy()
        random.shuffle(result)
        return result
    
    def _sample(lst, n):
        """随机采样"""
        return random.sample(lst, n)
    
    def _gauss(mu, sigma):
        """高斯分布"""
        return random.gauss(mu, sigma)
    
    return {
        '随机整数': (2, _randint),
        '随机小数': (0, _random),
        '随机选择': (1, _choice),
        '随机打乱': (1, _shuffle),
        '随机采样': (2, _sample),
        '高斯随机': (2, _gauss),
    }


# ==================== 增强的类型函数 ====================

def enhanced_type_functions():
    """增强的类型函数"""
    
    def _is_number(x):
        """是否为数字"""
        return isinstance(x, (int, float))
    
    def _is_string(x):
        """是否为字符串"""
        return isinstance(x, str)
    
    def _is_list(x):
        """是否为列表"""
        return isinstance(x, list)
    
    def _is_function(x):
        """是否为函数"""
        return callable(x)
    
    def _to_int(x):
        """转整数"""
        return int(x)
    
    def _to_float(x):
        """转浮点数"""
        return float(x)
    
    def _to_string(x):
        """转字符串"""
        return str(x)
    
    def _to_list(x):
        """转列表"""
        return list(x)
    
    return {
        '是数字': (1, _is_number),
        '是字符串': (1, _is_string),
        '是列表': (1, _is_list),
        '是函数': (1, _is_function),
        '转整数': (1, _to_int),
        '转浮点': (1, _to_float),
        '转字符串': (1, _to_string),
        '转列表': (1, _to_list),
    }


# ==================== 合并所有增强函数 ====================

def get_all_enhanced_functions():
    """获取所有增强的内置函数"""
    all_funcs = {}
    all_funcs.update(enhanced_math_functions())
    all_funcs.update(enhanced_list_functions())
    all_funcs.update(enhanced_string_functions())
    all_funcs.update(enhanced_random_functions())
    all_funcs.update(enhanced_type_functions())
    return all_funcs


# ==================== 性能优化 ====================

class Memoize:
    """记忆化装饰器，用于优化递归函数"""
    
    def __init__(self, func):
        self.func = func
        self.cache = {}
    
    def __call__(self, *args):
        if args in self.cache:
            return self.cache[args]
        result = self.func(*args)
        self.cache[args] = result
        return result


def optimize_recursive(func):
    """优化递归函数"""
    return Memoize(func)


# ==================== 导出 ====================

if __name__ == '__main__':
    # 测试增强函数
    print("增强的运行时功能测试")
    print("=" * 70)
    
    # 测试数学函数
    funcs = get_all_enhanced_functions()
    print(f"总函数数: {len(funcs)}")
    
    # 测试一些函数
    print(f"圆周率: {funcs['圆周率'][1]()}")
    print(f"正弦(π/2): {funcs['正弦'][1](math.pi/2)}")
    print(f"范围(5): {funcs['范围'][1](5)}")
    print(f"反转([1,2,3]): {funcs['反转'][1]([1,2,3])}")
    
    print("\n[OK] 增强运行时功能测试完成")
