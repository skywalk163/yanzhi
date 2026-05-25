# -*- coding: utf-8 -*-
"""基本库加载器

负责发现和加载 stdlib/ 下的基本库模块，
将函数注册到求值器的全局环境中。

设计原则：
- 语言内核只保留核心关键字（语法结构 + 基础算术/比较/逻辑/列表/高阶/IO）
- 数学、字符串、组合比较等通过基本库扩展
- 基本库默认自动加载，也可按需加载
"""
from __future__ import annotations

from typing import Any, Callable


# 默认加载的基本库模块
DEFAULT_LIBS = [
    'yan.stdlib.math_lib',
    'yan.stdlib.string_lib',
    'yan.stdlib.compare_lib',
    'yan.stdlib.seq_lib',
    'yan.stdlib.pred_lib',
    'yan.stdlib.util_lib',
    'yan.stdlib.file_lib',
    'yan.stdlib.random_lib',
    'yan.stdlib.dict_lib',
    'yan.stdlib.input_lib',
    'yan.stdlib.python_lib',
    'yan.stdlib.c_lib',
    'yan.stdlib.net_lib',
    'yan.stdlib.db_lib',
    'yan.stdlib.json_lib',
    'yan.stdlib.regex_lib',
]


def load_lib(module_path: str) -> dict[str, tuple[int, Callable]]:
    """加载单个基本库模块，返回 {动词名: (元数, 函数)} 字典"""
    import importlib
    mod = importlib.import_module(module_path)
    if not hasattr(mod, 'LIBS'):
        raise ImportError(f"基本库模块 {module_path} 缺少 LIBS 字典")
    return mod.LIBS


def load_all_libs(libs: list[str] | None = None) -> dict[str, tuple[int, Callable]]:
    """加载所有基本库，合并为统一字典

    Args:
        libs: 要加载的模块路径列表，None 表示加载默认库
    Returns:
        合并后的 {动词名: (元数, 函数)} 字典
    """
    if libs is None:
        libs = DEFAULT_LIBS
    result: dict[str, tuple[int, Callable]] = {}
    for module_path in libs:
        lib = load_lib(module_path)
        result.update(lib)
    return result


def get_all_lib_names(libs: list[str] | None = None) -> set[str]:
    """获取所有基本库提供的动词名集合"""
    return set(load_all_libs(libs).keys())
