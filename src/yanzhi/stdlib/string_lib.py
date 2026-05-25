# -*- coding: utf-8 -*-
"""字符串基本库

提供字符串操作函数：连接、分割、替换、截取、大小写、查找等。
这些函数不是语言核心关键字，而是通过基本库机制注册。

用法：在知行语言中直接调用
  连接 "你好" "世界"
  分割 "a,b,c" ","
  替换 "ababa" "a" "x"
  小写 "HELLO"
  大写 "hello"
  查找 "abcde" "cd"
"""


def _str_connect(a, b):
    """连接：字符串拼接"""
    return str(a) + str(b)


def _str_split(s, sep):
    """分割：字符串分割"""
    return s.split(sep)


def _str_replace(s, old, new):
    """替换：字符串替换"""
    return s.replace(old, new)


def _str_substring(s, start, end):
    """截取：字符串切片（从1开始，含首不含尾）"""
    return s[start - 1:end - 1] if end > 0 else s[start - 1:]


def _str_lower(s):
    """小写：转小写"""
    return s.lower()


def _str_upper(s):
    """大写：转大写"""
    return s.upper()


def _str_find(s, sub):
    """查找：查找子串位置（从1开始，未找到返回0）"""
    idx = s.find(sub)
    return idx + 1 if idx >= 0 else 0


def _str_contains(s, sub):
    """包含：包含检查"""
    return sub in s


def _str_format(fmt, *args):
    """格式化：字符串格式化"""
    return fmt.format(*args)


LIBS = {
    '连接': (2, _str_connect),
    '分割': (2, _str_split),
    '替换': (3, _str_replace),
    '截取': (3, _str_substring),
    '小写': (1, _str_lower),
    '大写': (1, _str_upper),
    '查找': (2, _str_find),
    '包含': (2, _str_contains),
    '格式化': (-1, _str_format),
}
