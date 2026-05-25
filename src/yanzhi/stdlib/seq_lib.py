# -*- coding: utf-8 -*-
"""序列基本库

参考 Common Lisp (sort, reverse, remove-duplicates, position, count,
subseq, intersection, union, set-difference) 和
Python (sorted, reversed, zip, set operations) 设计。

提供列表/序列的高级操作函数。

用法：
  排序【3，1，2】        → [1, 2, 3]
  反转【1，2，3】        → [3, 2, 1]
  去重【1，2，2，3】     → [1, 2, 3]
  位置【1，2，3】2       → 2  (1-based)
  计数【1，2，2，3】2    → 2
  子列【1，2，3，4，5】2 4  → [2, 3, 4]  (1-based, 含首含尾)
  拉链【1，2】【a，b】   → [[1,a], [2,b]]
  交集【1，2，3】【2，3，4】 → [2, 3]
  并集【1，2】【2，3】   → [1, 2, 3]
  差集【1，2，3】【2，3，4】 → [1]
"""


def _sort(lst):
    """排序：升序排列"""
    return sorted(lst)


def _reverse(lst):
    """反转：逆序排列"""
    return list(reversed(lst))


def _deduplicate(lst):
    """去重：移除重复元素（保持首次出现顺序）"""
    seen = set()
    result = []
    for x in lst:
        key = (type(x).__name__, x) if not isinstance(x, list) else (type(x).__name__, tuple(x))
        if key not in seen:
            seen.add(key)
            result.append(x)
    return result


def _position(lst, x):
    """位置：查找元素首次出现的位置（1-based，未找到返回0）"""
    try:
        return lst.index(x) + 1
    except ValueError:
        return 0


def _count(lst, x):
    """计数：统计元素出现次数"""
    return lst.count(x)


def _sublist(lst, start, end):
    """子列：取子列表（1-based，含首含尾）"""
    return lst[start - 1:end]


def _zip(a, b):
    """拉链：将两个列表配对"""
    return [list(pair) for pair in zip(a, b)]


def _intersection(a, b):
    """交集：两个列表的公共元素"""
    return [x for x in a if x in b]


def _union(a, b):
    """并集：两个列表的合并（去重）"""
    seen = set()
    result = []
    for x in a + b:
        if x not in seen:
            seen.add(x)
            result.append(x)
    return result


def _difference(a, b):
    """差集：在a中但不在b中的元素"""
    return [x for x in a if x not in b]


LIBS = {
    '排序': (1, _sort),
    '反转': (1, _reverse),
    '去重': (1, _deduplicate),
    '位置': (2, _position),
    '计数': (2, _count),
    '子列': (3, _sublist),
    '拉链': (2, _zip),
    '交集': (2, _intersection),
    '并集': (2, _union),
    '差集': (2, _difference),
}
