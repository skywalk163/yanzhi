

#!/usr/bin/env python3
"""
测试优化版分词器
"""
import sys
import os
sys.path.insert(0, os.path.abspath('src'))

from yanzhi.compiler.pre_tokenizer import tokenize as original_tokenize
from yanzhi.compiler.pre_tokenizer_optimized import tokenize_optimized as optimized_tokenize
import time

test_cases = [
    "定义x=5相加3。",
    "列表1 2 3，映射相乘2。",
    "如果x大于y那么x否则y。",
    "张三=18。",
    "定义阶乘=函数n如果n等于1那么1否则n相乘阶乘n相减1。",
    "循环变量于1到10：打印变量。",
    "定a=定b=定c=5。",
    "当条件成立就执行操作。",
    "导入数学模块并使用正弦函数。",
]

def benchmark():
    print("优化版分词器性能测试")
    print("=" * 50)
    
    total_original = 0
    total_optimized = 0
    iterations = 100
    
    for source in test_cases:
        print(f"\n测试: {source}")
        
        # 预热
        original_tokenize(source)
        optimized_tokenize(source)
        
        # 原始版性能
        start = time.perf_counter()
        for _ in range(iterations):
            original_tokenize(source)
        original_time = time.perf_counter() - start
        
        # 优化版性能
        start = time.perf_counter()
        for _ in range(iterations):
            optimized_tokenize(source)
        optimized_time = time.perf_counter() - start
        
        print(f"  原始版: {original_time:.4f}s")
        print(f"  优化版: {optimized_time:.4f}s")
        print(f"  加速比: {original_time/optimized_time:.2f}x")
        
        total_original += original_time
        total_optimized += optimized_time
    
    print("\n" + "=" * 50)
    print(f"总计:")
    print(f"  原始版: {total_original:.4f}s")
    print(f"  优化版: {total_optimized:.4f}s")
    print(f"  总体加速比: {total_original/total_optimized:.2f}x")
    
    # 验证两个版本的结果是否一致
    print("\n验证结果一致性:")
    for source in test_cases:
        original = original_tokenize(source)
        optimized = optimized_tokenize(source)
        
        # 比较Token序列
        if len(original) != len(optimized):
            print(f"  '{source}': 长度不一致 - 原始: {len(original)}, 优化: {len(optimized)}")
            continue
        
        all_match = True
        for i, (o1, o2) in enumerate(zip(original, optimized)):
            if o1.type != o2.type or o1.value != o2.value:
                print(f"  '{source}': 第{i}个Token不一致")
                print(f"    原始: {o1}")
                print(f"    优化: {o2}")
                all_match = False
        
        if all_match:
            print(f"  '{source}': OK 一致")

if __name__ == '__main__':
    benchmark()

