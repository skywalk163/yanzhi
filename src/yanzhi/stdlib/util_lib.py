# -*- coding: utf-8 -*-
"""工具基本库

参考 Common Lisp (loop, dotimes, maplist) 和
Python (range, enumerate, min, max, sum, repeat, flatten) 设计。

提供数值和列表的实用工具函数。

用法：
  范围步 1 10 2    → [1, 3, 5, 7, 9]
  重复 3 "哈"      → "哈哈哈"
  最小【3，1，2】   → 1
  最大【3，1，2】   → 3
  求和【1，2，3】   → 6
  乘积【1，2，3】   → 6
  展平【1，【2，3】，4】 → [1, 2, 3, 4]
  枚举【a，b，c】   → [[1,a], [2,b], [3,c]]
  间隔 1 5         → [1, 2, 3, 4, 5]
"""


def _range_step(start, end, step):
    """范围步：生成从start到end步长为step的列表"""
    if step > 0:
        return list(range(start, end + 1, step))
    elif step < 0:
        return list(range(start, end - 1, step))
    return [start]


def _interval(start, end):
    """间隔：生成从start到end的连续列表（含两端）"""
    if start <= end:
        return list(range(start, end + 1))
    return list(range(start, end - 1, -1))


def _repeat(n, x):
    """重复：重复n次"""
    if isinstance(x, str):
        return x * n
    if isinstance(x, list):
        return x * n
    return [x] * n


def _minimum(lst):
    """最小：取最小值"""
    return min(lst)


def _maximum(lst):
    """最大：取最大值"""
    return max(lst)


def _sum(lst):
    """求和：列表求和"""
    return sum(lst)


def _product(lst):
    """乘积：列表求积"""
    result = 1
    for x in lst:
        result *= x
    return result


def _flatten(lst):
    """展平：将嵌套列表展平为一维"""
    result = []
    for x in lst:
        if isinstance(x, list):
            result.extend(_flatten(x))
        else:
            result.append(x)
    return result


def _enumerate(lst):
    """枚举：将列表元素配对索引（1-based）"""
    return [[i + 1, x] for i, x in enumerate(lst)]


def _chunk(lst, n):
    """分块：将列表按n个一组分块"""
    return [lst[i:i + n] for i in range(0, len(lst), n)]


def _interleave(*lists):
    """交织：将多个列表交替合并"""
    result = []
    max_len = max(len(lst) for lst in lists) if lists else 0
    for i in range(max_len):
        for lst in lists:
            if i < len(lst):
                result.append(lst[i])
    return result


LIBS = {
    '范围步': (3, _range_step),
    '间隔': (2, _interval),
    '重复': (2, _repeat),
    '最小': (1, _minimum),
    '最大': (1, _maximum),
    '求和': (1, _sum),
    '乘积': (1, _product),
    '展平': (1, _flatten),
    '枚举': (1, _enumerate),
    '分块': (2, _chunk),
    '交织': (-1, _interleave),
}
