# -*- coding: utf-8 -*-
"""Python 模块桥接库

提供知行语言与 Python 模块的互操作能力：
- 导入 Python 模块
- 调用 Python 函数
- 自动类型转换：Python 值 <-> 知行值
"""
from __future__ import annotations

from typing import Any, Callable


# 已导入的 Python 模块缓存
_imported_modules: dict[str, Any] = {}


def _python_import(module_name: str) -> str:
    """导入 Python 模块，返回模块标识"""
    import importlib
    try:
        mod = importlib.import_module(module_name)
        _imported_modules[module_name] = mod
        return module_name
    except ImportError as e:
        raise ImportError(f"无法导入 Python 模块: {module_name} ({e})")


def _python_call(module_name: str, func_name: str, *args) -> Any:
    """调用 Python 模块中的函数"""
    if module_name not in _imported_modules:
        _python_import(module_name)

    mod = _imported_modules[module_name]
    if not hasattr(mod, func_name):
        raise AttributeError(f"Python 模块 {module_name} 没有属性 {func_name}")

    func = getattr(mod, func_name)
    if not callable(func):
        return func  # 返回属性值

    # 类型转换：知行值 -> Python 值
    py_args = [_to_python(a) for a in args]
    result = func(*py_args)

    # 类型转换：Python 值 -> 知行值
    return _to_yan(result)


def _python_get(module_name: str, attr_name: str) -> Any:
    """获取 Python 模块的属性"""
    if module_name not in _imported_modules:
        _python_import(module_name)

    mod = _imported_modules[module_name]
    if not hasattr(mod, attr_name):
        raise AttributeError(f"Python 模块 {module_name} 没有属性 {attr_name}")

    return _to_yan(getattr(mod, attr_name))


def _python_eval(code: str) -> Any:
    """执行 Python 表达式"""
    try:
        result = eval(code)
        return _to_yan(result)
    except Exception as e:
        raise RuntimeError(f"Python 表达式求值错误: {e}")


def _python_exec(code: str) -> None:
    """执行 Python 语句"""
    try:
        exec(code)
    except Exception as e:
        raise RuntimeError(f"Python 语句执行错误: {e}")


def _to_python(value: Any) -> Any:
    """知行值 -> Python 值"""
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float, str, list, dict)):
        return value
    # 其他类型直接传递
    return value


def _to_yan(value: Any) -> Any:
    """Python 值 -> 知行值"""
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float, str)):
        return value
    if isinstance(value, (list, tuple)):
        return [_to_yan(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _to_yan(v) for k, v in value.items()}
    if isinstance(value, set):
        return [_to_yan(v) for v in value]
    # 其他类型转为字符串
    return value


# 标准库注册字典
LIBS: dict[str, tuple[int, Callable]] = {
    '导入模块':  (1, _python_import),   # 导入 Python 模块
    '调模块':    (3, _python_call),     # 调用模块函数 (模块名, 函数名, 参数)
    '取模块':    (2, _python_get),      # 获取模块属性 (模块名, 属性名)
    '求值Py':    (1, _python_eval),     # 执行 Python 表达式
    '执行Py':    (1, _python_exec),     # 执行 Python 语句
}
