# -*- coding: utf-8 -*-
"""哈希表库（字典库）

提供字典/映射操作功能。

用法：
  字典 键1 值1 键2 值2 ...  → 创建字典
  键 字典 键名                 → 获取值
  设键 字典 键名 值           → 设置值
  键集 字典                   → 获取所有键
  值集 字典                   → 获取所有值
  含键 字典 键名              → 检查键是否存在
  删键 字典 键名              → 删除键
  键数 字典                   → 获取键值对数量
"""


def _dict(*args) -> dict:
    """创建字典：键1 值1 键2 值2 ..."""
    if len(args) % 2 != 0:
        raise ValueError("字典参数必须是键值对")
    return dict(zip(args[::2], args[1::2]))


def _get(d: dict, key: any) -> any:
    """获取值"""
    return d.get(key)


def _set(d: dict, key: any, value: any) -> dict:
    """设置值（返回修改后的字典）"""
    d[key] = value
    return d


def _keys(d: dict) -> list:
    """获取所有键"""
    return list(d.keys())


def _values(d: dict) -> list:
    """获取所有值"""
    return list(d.values())


def _has_key(d: dict, key: any) -> bool:
    """检查键是否存在"""
    return key in d


def _del_key(d: dict, key: any) -> dict:
    """删除键"""
    if key in d:
        del d[key]
    return d


def _len(d: dict) -> int:
    """获取键值对数量"""
    return len(d)


LIBS = {
    '字典': (-1, _dict),
    '键': (2, _get),
    '设键': (3, _set),
    '键集': (1, _keys),
    '值集': (1, _values),
    '含键': (2, _has_key),
    '删键': (2, _del_key),
    '键数': (1, _len),
}
