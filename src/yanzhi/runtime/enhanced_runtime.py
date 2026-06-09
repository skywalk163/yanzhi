# -*- coding: utf-8 -*-
"""
[DEPRECATED] 增强运行时（旧实现）

此文件不再使用。所有标准库功能已迁移至 stdlib/ 目录。
stdlib 通过 stdlib/loader.py 的 load_all_libs() 统一加载。

此文件将在未来版本中彻底删除。
"""

# 向后兼容导入
from yanzhi.stdlib.math_lib import *
from yanzhi.stdlib.seq_lib import *
from yanzhi.stdlib.string_lib import *
from yanzhi.stdlib.random_lib import *
