# -*- coding: utf-8 -*-
"""正则库

提供正则表达式匹配和替换能力：
- 匹配/搜索/查找全部
- 替换
- 分割
"""
from __future__ import annotations

import re as _re
from typing import Any, Callable


def _regex_match(pattern: str, text: str) -> Any:
    """正则匹配（从头开始）"""
    m = _re.match(pattern, text)
    if m is None:
        return None
    if m.groups():
        return list(m.groups())
    return m.group(0)


def _regex_search(pattern: str, text: str) -> Any:
    """正则搜索（任意位置）"""
    m = _re.search(pattern, text)
    if m is None:
        return None
    if m.groups():
        return list(m.groups())
    return m.group(0)


def _regex_findall(pattern: str, text: str) -> list:
    """查找所有匹配"""
    return _re.findall(pattern, text)


def _regex_replace(pattern: str, replacement: str, text: str) -> str:
    """正则替换"""
    return _re.sub(pattern, replacement, text)


def _regex_split(pattern: str, text: str) -> list:
    """正则分割"""
    return _re.split(pattern, text)


def _regex_test(pattern: str, text: str) -> bool:
    """测试是否匹配"""
    return bool(_re.search(pattern, text))


# 标准库注册字典
LIBS: dict[str, tuple[int, Callable]] = {
    '正则匹配':   (2, _regex_match),     # 正则匹配
    '正则搜索':   (2, _regex_search),    # 正则搜索
    '正则全找':   (2, _regex_findall),   # 查找全部
    '正则替换':   (3, _regex_replace),   # 正则替换
    '正则分割':   (2, _regex_split),     # 正则分割
    '正则测试':   (2, _regex_test),      # 测试是否匹配
}
