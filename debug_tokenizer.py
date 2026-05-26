


#!/usr/bin/env python3
"""
调试分词器差异
"""
import sys
import os
sys.path.insert(0, os.path.abspath('src'))

from yanzhi.compiler.pre_tokenizer import tokenize as original_tokenize
from yanzhi.compiler.pre_tokenizer_optimized import tokenize_optimized as optimized_tokenize

test_cases = [
    "定义x=5相加3。",
    "张三=18。",
    "定阶乘=函n：若n等1则1否则n乘阶乘$(n-1)。",
]

for source in test_cases:
    print(f"\n源码: {source}")
    
    original = original_tokenize(source)
    optimized = optimized_tokenize(source)
    
    print("原始版Tokens:")
    for i, token in enumerate(original):
        if token.type.name != 'EOF':
            print(f"  {i:2d}: {token.type.name:10} = {repr(token.value)}")
    
    print("优化版Tokens:")
    for i, token in enumerate(optimized):
        if token.type.name != 'EOF':
            print(f"  {i:2d}: {token.type.name:10} = {repr(token.value)}")
    
    # 比较差异
    min_len = min(len(original), len(optimized))
    differences = []
    
    for i in range(min_len):
        o1 = original[i]
        o2 = optimized[i]
        if o1.type != o2.type or o1.value != o2.value:
            differences.append((i, o1, o2))
    
    if differences:
        print("差异:")
        for i, o1, o2 in differences:
            print(f"  位置 {i}: 原始={o1}, 优化={o2}")
    
    if len(original) != len(optimized):
        print(f"Token数量不一致: 原始={len(original)}, 优化={len(optimized)}")
        if len(original) > len(optimized):
            print("  原始版多出的Tokens:")
            for i in range(min_len, len(original)):
                print(f"    {i}: {original[i]}")
        else:
            print("  优化版多出的Tokens:")
            for i in range(min_len, len(optimized)):
                print(f"    {i}: {optimized[i]}")


