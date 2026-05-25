# -*- coding: utf-8 -*-
"""输入库

提供用户输入功能。

用法：
  输入           → 读取一行用户输入
  输入 提示       → 显示提示并读取输入
"""


def _input(prompt: str = '') -> str:
    """读取用户输入"""
    return input(prompt)


LIBS = {
    '输入': (0, _input),
}
