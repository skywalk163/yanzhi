

#!/usr/bin/env python3
"""
测试修复版缓存分词器
"""
import sys
import os
sys.path.insert(0, os.path.abspath('src'))

from yanzhi.compiler.pre_tokenizer import tokenize as original_tokenize
from yanzhi.compiler.pre_tokenizer_cached_fixed import tokenize_cached, CachedPreTokenizer

def test_basic():
    """基础测试"""
    test_cases = [
        "定义x=5相加3。",
        "列表1 2 3，映射相乘2。",
        "如果x大于y那么x否则y。",
        "张三=18。",
        "定义阶乘=函数n如果n等于1那么1否则n相乘阶乘n相减1。",
    ]
    
    print("修复版缓存分词器测试")
    print("=" * 60)
    
    all_passed = True
    
    for i, source in enumerate(test_cases):
        print(f"\n测试用例 {i+1}: {source}")
        
        # 清空缓存
        CachedPreTokenizer.clear_cache()
        
        # 原始版本
        orig_tokens = original_tokenize(source)
        
        # 缓存版本（第一次，应该缓存未命中）
        cached_tokens1 = tokenize_cached(source)
        
        # 缓存版本（第二次，应该缓存命中）
        cached_tokens2 = tokenize_cached(source)
        
        # 比较结果
        if len(orig_tokens) != len(cached_tokens1):
            print(f"  ❌ Token数量不一致: 原始={len(orig_tokens)}, 缓存={len(cached_tokens1)}")
            all_passed = False
            continue
        
        # 比较每个Token
        match = True
        for j, (t1, t2) in enumerate(zip(orig_tokens, cached_tokens1)):
            if t1.type != t2.type or t1.value != t2.value:
                print(f"  ❌ 第{j}个Token不一致:")
                print(f"     原始: {t1}")
                print(f"     缓存: {t2}")
                match = False
                break
        
        if match:
            print(f"  OK 分词结果一致")
        
        # 检查缓存命中
        stats = CachedPreTokenizer.get_cache_stats()
        if stats['hits'] == 1 and stats['misses'] == 1:
            print(f"  OK 缓存工作正常: 命中1次, 未命中1次")
        else:
            print(f"  WARN 缓存统计异常: 命中{stats['hits']}次, 未命中{stats['misses']}次")
    
    return all_passed

def test_performance():
    """性能测试"""
    import time
    
    source = "定义x=5相加3。"
    iterations = 1000
    
    print("\n\n性能测试")
    print("=" * 60)
    
    # 清空缓存
    CachedPreTokenizer.clear_cache()
    
    # 第一次运行（缓存未命中）
    start = time.perf_counter()
    for _ in range(iterations):
        tokenize_cached(source)
    first_run = time.perf_counter() - start
    
    # 第二次运行（缓存命中）
    start = time.perf_counter()
    for _ in range(iterations):
        tokenize_cached(source)
    second_run = time.perf_counter() - start
    
    # 无缓存版本
    start = time.perf_counter()
    for _ in range(iterations):
        original_tokenize(source)
    no_cache = time.perf_counter() - start
    
    print(f"无缓存版本: {no_cache:.4f}s")
    print(f"缓存版本第一次运行: {first_run:.4f}s (缓存未命中)")
    print(f"缓存版本第二次运行: {second_run:.4f}s (缓存命中)")
    print(f"缓存命中后加速比: {first_run/second_run:.2f}x")
    print(f"相对于无缓存加速比: {no_cache/second_run:.2f}x")
    
    stats = CachedPreTokenizer.get_cache_stats()
    print(f"缓存统计: 命中率={stats['hit_rate']:.1%}")

if __name__ == '__main__':
    if test_basic():
        print("\n" + "=" * 60)
        print("OK 所有基础测试通过!")
        test_performance()
    else:
        print("\n" + "=" * 60)
        print("FAIL 基础测试失败，请检查实现")

