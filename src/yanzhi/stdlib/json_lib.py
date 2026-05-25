# -*- coding: utf-8 -*-
"""JSON 库

提供 JSON 编解码能力：
- JSON 字符串 -> 知行值
- 知行值 -> JSON 字符串
"""
from __future__ import annotations

import json as _json
from typing import Any, Callable


def _json_parse(s: str) -> Any:
    """JSON 字符串 -> 知行值"""
    try:
        return _json.loads(s)
    except _json.JSONDecodeError as e:
        raise RuntimeError(f"JSON 解码错误: {e}")


def _json_stringify(value: Any) -> str:
    """知行值 -> JSON 字符串"""
    try:
        return _json.dumps(value, ensure_ascii=False, indent=2)
    except (TypeError, ValueError) as e:
        raise RuntimeError(f"JSON 编码错误: {e}")


def _json_compact(value: Any) -> str:
    """知行值 -> 紧凑 JSON 字符串"""
    try:
        return _json.dumps(value, ensure_ascii=False)
    except (TypeError, ValueError) as e:
        raise RuntimeError(f"JSON 编码错误: {e}")


def _json_load(path: str) -> Any:
    """从文件加载 JSON"""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return _json.load(f)
    except (FileNotFoundError, _json.JSONDecodeError) as e:
        raise RuntimeError(f"JSON 文件加载错误: {e}")


def _json_save(path: str, value: Any) -> None:
    """保存 JSON 到文件"""
    try:
        with open(path, 'w', encoding='utf-8') as f:
            _json.dump(value, f, ensure_ascii=False, indent=2)
    except (TypeError, ValueError) as e:
        raise RuntimeError(f"JSON 文件保存错误: {e}")


# 标准库注册字典
LIBS: dict[str, tuple[int, Callable]] = {
    '解JSON':    (1, _json_parse),      # JSON 解码
    '编JSON':    (1, _json_stringify),  # JSON 编码（格式化）
    '紧JSON':    (1, _json_compact),    # JSON 编码（紧凑）
    '读JSON':    (1, _json_load),       # 从文件读 JSON
    '写JSON':    (2, _json_save),       # 写 JSON 到文件
}
