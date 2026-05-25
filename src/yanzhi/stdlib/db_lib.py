# -*- coding: utf-8 -*-
"""数据库库

基于 sqlite3，提供 SQLite 数据库操作能力：
- 连接/关闭数据库
- 执行 SQL
- 查询结果
"""
from __future__ import annotations

import sqlite3
from typing import Any, Callable
import atexit


# 数据库连接缓存
_connections: dict[str, sqlite3.Connection] = {}


def _cleanup_connections():
    """清理所有数据库连接（程序退出时调用）"""
    for path, conn in list(_connections.items()):
        try:
            conn.close()
        except:
            pass
    _connections.clear()


# 注册退出清理函数
atexit.register(_cleanup_connections)


def _db_open(path: str) -> str:
    """打开 SQLite 数据库"""
    # 如果已存在连接，直接返回
    if path in _connections:
        return path
    
    # 创建新连接
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    _connections[path] = conn
    return path


def _db_close(path: str) -> None:
    """关闭数据库连接"""
    if path in _connections:
        _connections[path].close()
        del _connections[path]


def _db_exec(path: str, sql: str) -> list:
    """执行 SQL 语句（无返回值）"""
    if path not in _connections:
        _db_open(path)
    conn = _connections[path]
    try:
        cursor = conn.execute(sql)
        conn.commit()
        return []
    except sqlite3.Error as e:
        raise RuntimeError(f"SQL 执行错误: {e}")


def _db_query(path: str, sql: str) -> list:
    """执行 SQL 查询，返回结果列表"""
    if path not in _connections:
        _db_open(path)
    conn = _connections[path]
    try:
        cursor = conn.execute(sql)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    except sqlite3.Error as e:
        raise RuntimeError(f"SQL 查询错误: {e}")


def _db_exec_params(path: str, sql: str, params: list) -> list:
    """执行带参数的 SQL"""
    if path not in _connections:
        _db_open(path)
    conn = _connections[path]
    try:
        cursor = conn.execute(sql, params)
        conn.commit()
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    except sqlite3.Error as e:
        raise RuntimeError(f"SQL 执行错误: {e}")


def _db_tables(path: str) -> list:
    """获取所有表名"""
    if path not in _connections:
        _db_open(path)
    conn = _connections[path]
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    return [row[0] for row in cursor.fetchall()]


# 标准库注册字典
LIBS: dict[str, tuple[int, Callable]] = {
    '开库':     (1, _db_open),         # 打开数据库
    '关库':     (1, _db_close),        # 关闭数据库
    '执行SQL':  (2, _db_exec),         # 执行 SQL
    '查询SQL':  (2, _db_query),        # 查询 SQL
    '执行参数': (3, _db_exec_params),  # 带参数执行
    '表列表':   (1, _db_tables),       # 获取表名列表
}
