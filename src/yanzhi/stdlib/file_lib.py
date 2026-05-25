# -*- coding: utf-8 -*-
"""文件操作库

提供文件读写功能。

用法：
  读 "文件路径"       → 读取文件内容
  写 "文件路径" 内容  → 写入内容到文件
  追 "文件路径" 内容  → 追加内容到文件
"""
import os


def _read_file(filepath: str) -> str:
    """读取文件内容"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()


def _write_file(filepath: str, content: str) -> None:
    """写入文件内容"""
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(str(content))


def _append_file(filepath: str, content: str) -> None:
    """追加内容到文件"""
    with open(filepath, 'a', encoding='utf-8') as f:
        f.write(str(content))


def _exists(filepath: str) -> bool:
    """检查文件是否存在"""
    return os.path.exists(filepath)


def _is_dir(path: str) -> bool:
    """检查是否为目录"""
    return os.path.isdir(path)


def _is_file(path: str) -> bool:
    """检查是否为文件"""
    return os.path.isfile(path)


def _delete_file(path: str) -> None:
    """删除文件"""
    os.remove(path)


def _list_dir(path: str) -> list[str]:
    """列出目录内容"""
    return os.listdir(path)


LIBS = {
    '读': (1, _read_file),
    '写': (2, _write_file),
    '追': (2, _append_file),
    '存在': (1, _exists),
    '是目录': (1, _is_dir),
    '是文件': (1, _is_file),
    '删文件': (1, _delete_file),
    '列目录': (1, _list_dir),
}
