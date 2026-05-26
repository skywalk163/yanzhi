


#!/usr/bin/env python3
"""
简化版缓存测试
"""
import sys
import os
sys.path.insert(0, os.path.abspath('src'))

from yanzhi.compiler.pre_tokenizer import tokenize, get_cache_stats, clear_cache
import time

def main():
    # 清空缓存
    clear_cache()
    
    print("=== 缓存机制测试 ===")
    
    test_source = "定义x=5相加3。"
    
    # 第一次调用（缓存未命中）
    start = time.perf_counter()
    tokens1 = tokenize(test_source)
    time1 = time.perf_counter() - start
    
    stats = get_cache_stats()
    print(f"第一次调用: 耗时{time1*1000:.2f}ms, 命中{stats['hits']}次, 未命中{stats['misses']}次")
    
    # 第二次调用（缓存命中）
    start = time.perf_counter()
    tokens2 = tokenize(test_source)
    time2 = time.perf_counter() - start
    
    stats = get_cache_stats()
    print(f"第二次调用: 耗时{time2*1000:.2f}ms, 命中{stats['hits']}次, 未命中{stats['misses']}次")
    
    # 验证一致性
    if len(tokens1) == len(tokens2):
        match = True
        for t1, t2 in zip(tokens1, tokens2):
            if t1.type != t2.type or t1.value != t2.value:
                match = False
                break
        if match:
            print("结果验证: 两次分词结果一致")
        else:
            print("结果验证: 分词结果不一致")
            return False
    else:
        print(f"结果验证: Token数量不一致 ({len(tokens1)} vs {len(tokens2)})")
        return False
    
    # 测试禁用缓存
    clear_cache()
    tokens3 = tokenize(test_source, use_cache=False)
    stats = get_cache_stats()
    if stats['hits'] == 0 and stats['misses'] == 0:
        print("禁用缓存测试: 通过 (缓存未使用)")
    else:
        print(f"禁用缓存测试: 异常 (命中{stats['hits']}次)")
    
    # 性能对比
    clear_cache()
    iterations = 1000
    
    # 无缓存
    start = time.perf_counter()
    for _ in range(iterations):
        tokenize(test_source, use_cache=False)
    time_no_cache = time.perf_counter() - start
    
    # 有缓存（先填充缓存）
    tokenize(test_source, use_cache=True)  # 填充缓存
    start = time.perf_counter()
    for _ in range(iterations):
        tokenize(test_source, use_cache=True)
    time_with_cache = time.perf_counter() - start
    
    print(f"\n=== 性能测试 ===")
    print(f"无缓存 {iterations}次: {time_no_cache:.4f}s")
    print(f"有缓存 {iterations}次: {time_with_cache:.4f}s")
    print(f"加速比: {time_no_cache/time_with_cache:.2f}x")
    
    if time_no_cache / time_with_cache > 1.5:
        print("结论: 缓存机制性能提升显著")
    else:
        print("结论: 缓存机制性能提升有限")
    
    return True

if __name__ == '__main__':
    if main():
        print("\n所有测试通过！")
        sys.exit(0)
    else:
        print("\n测试失败！")
        sys.exit(1)


