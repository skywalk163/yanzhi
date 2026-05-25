# -*- coding: utf-8 -*-
"""谓词基本库

参考 Common Lisp (typep, null, zerop, numberp, stringp, listp,
every, some, notevery, notany) 和
Python (isinstance, type, all, any, callable) 设计。

提供类型判断和逻辑谓词函数。

用法：
  是数 3          → 真
  是串 "hello"    → 真
  是列 【1，2】   → 真
  是空 【】       → 真
  是零 0          → 真
  全真【真，真，假】 → 假
  任真【真，假，假】 → 真
"""


def _is_number(x):
    """是数：判断是否为数字"""
    return isinstance(x, (int, float, complex)) and not isinstance(x, bool)


def _is_string(x):
    """是串：判断是否为字符串"""
    return isinstance(x, str)


def _is_list(x):
    """是列：判断是否为列表"""
    return isinstance(x, list)


def _is_bool(x):
    """是布尔：判断是否为布尔值"""
    return isinstance(x, bool)


def _is_empty(x):
    """是空：判断是否为空（空列表/空字符串/零）"""
    if isinstance(x, list):
        return len(x) == 0
    if isinstance(x, str):
        return len(x) == 0
    return x == 0


def _is_zero(x):
    """是零：判断是否为零"""
    return x == 0


def _is_positive(x):
    """是正：判断是否为正数"""
    return x > 0


def _is_negative(x):
    """是负：判断是否为负数"""
    return x < 0


def _all_true(lst):
    """全真：列表中所有元素为真"""
    return all(lst)


def _any_true(lst):
    """任真：列表中存在元素为真"""
    return any(lst)


def _none_true(lst):
    """全假：列表中所有元素为假"""
    return not any(lst)


LIBS = {
    '是数': (1, _is_number),
    '是串': (1, _is_string),
    '是列': (1, _is_list),
    '是布尔': (1, _is_bool),
    '是空': (1, _is_empty),
    '是零': (1, _is_zero),
    '是正': (1, _is_positive),
    '是负': (1, _is_negative),
    '全真': (1, _all_true),
    '任真': (1, _any_true),
    '全假': (1, _none_true),
}
