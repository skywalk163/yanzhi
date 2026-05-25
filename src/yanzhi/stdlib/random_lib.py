# -*- coding: utf-8 -*-
"""随机数库

提供随机数生成和随机选择功能。

用法：
  随机             → 0-1 之间的随机小数
  随机整数 a b    → a 到 b 之间的随机整数（含两端）
  随机选择 列表   → 从列表中随机选择一个元素
  随机打乱 列表   → 随机打乱列表顺序
"""
import random


def _random() -> float:
    """生成 0-1 之间的随机小数"""
    return random.random()


def _randint(a: int, b: int) -> int:
    """生成 a 到 b 之间的随机整数（含两端）"""
    return random.randint(a, b)


def _choice(lst: list) -> any:
    """从列表中随机选择一个元素"""
    return random.choice(lst)


def _shuffle(lst: list) -> list:
    """随机打乱列表顺序"""
    result = lst.copy()
    random.shuffle(result)
    return result


def _sample(lst: list, k: int) -> list:
    """从列表中随机选择 k 个元素（不重复）"""
    return random.sample(lst, k)


LIBS = {
    '随机': (0, _random),
    '随机整数': (2, _randint),
    '随机选择': (1, _choice),
    '随机打乱': (1, _shuffle),
    '随机采样': (2, _sample),
}
