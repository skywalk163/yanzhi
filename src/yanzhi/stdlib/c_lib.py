# -*- coding: utf-8 -*-
"""C 库桥接库

基于 ctypes，提供知行语言与 C 共享库的互操作能力：
- 加载 C 共享库
- 调用 C 函数
- 基本类型转换
"""
from __future__ import annotations

import ctypes
from typing import Any, Callable


# 已加载的 C 库缓存
_loaded_libs: dict[str, ctypes.CDLL] = {}


def _c_load(lib_name: str) -> str:
    """加载 C 共享库"""
    try:
        lib = ctypes.CDLL(lib_name)
        _loaded_libs[lib_name] = lib
        return lib_name
    except OSError as e:
        raise RuntimeError(f"无法加载 C 库: {lib_name} ({e})")


def _c_call(lib_name: str, func_name: str, *args) -> Any:
    """调用 C 库中的函数"""
    if lib_name not in _loaded_libs:
        _c_load(lib_name)

    lib = _loaded_libs[lib_name]
    try:
        func = getattr(lib, func_name)
    except AttributeError:
        raise AttributeError(f"C 库 {lib_name} 没有函数 {func_name}")

    # 转换参数类型
    c_args = []
    for arg in args:
        if isinstance(arg, int):
            c_args.append(ctypes.c_int(arg))
        elif isinstance(arg, float):
            c_args.append(ctypes.c_double(arg))
        elif isinstance(arg, str):
            c_args.append(ctypes.c_char_p(arg.encode('utf-8')))
        else:
            c_args.append(arg)

    result = func(*c_args)

    # 转换返回值
    if isinstance(result, int):
        return result
    elif isinstance(result, float):
        return result
    return result


def _c_call_double(lib_name: str, func_name: str, arg: float) -> float:
    """调用 C 库中返回 double 的函数"""
    if lib_name not in _loaded_libs:
        _c_load(lib_name)

    lib = _loaded_libs[lib_name]
    try:
        func = getattr(lib, func_name)
    except AttributeError:
        raise AttributeError(f"C 库 {lib_name} 没有函数 {func_name}")

    func.restype = ctypes.c_double
    func.argtypes = [ctypes.c_double]
    return func(arg)


def _c_get(lib_name: str, symbol_name: str) -> Any:
    """获取 C 库中的符号值"""
    if lib_name not in _loaded_libs:
        _c_load(lib_name)

    lib = _loaded_libs[lib_name]
    try:
        return getattr(lib, symbol_name)
    except AttributeError:
        raise AttributeError(f"C 库 {lib_name} 没有符号 {symbol_name}")


# 标准库注册字典
LIBS: dict[str, tuple[int, Callable]] = {
    '加载C库':    (1, _c_load),          # 加载 C 共享库
    '调C函数':    (3, _c_call),          # 调用 C 函数 (库名, 函数名, 参数)
    '调C双精':    (3, _c_call_double),   # 调用返回 double 的 C 函数
    '取C符号':    (2, _c_get),           # 获取 C 符号值
}
