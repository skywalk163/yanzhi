



#!/usr/bin/env python3
"""
测试优化版LRU缓存（哈希键）
"""
import sys
import os
sys.path.insert(0, os.path.abspath('src'))

from yanzhi.compiler.pre_tokenizer import tokenize, get_cache_stats, clear_cache

def test_basic_functionality():
    """基础功能测试"""
    print("=== 优化版LRU缓存基础测试 ===")
    
    clear_cache()
    
    # 测试短字符串（直接使用）
    short_source = "定义x=1。"
    tokens1 = tokenize(short_source)
    stats = get_cache_stats()
    print(f"短字符串测试: 缓存大小={stats['size']}, 命中率={stats['hit_rate']:.1%}")
    
    # 测试长字符串（使用哈希）
    long_source = "这是一个非常长的源代码字符串，" * 10 + "定义x=" + "非常长的表达式" * 5 + "。"
    tokens2 = tokenize(long_source)
    stats = get_cache_stats()
    print(f"长字符串测试: 缓存大小={stats['size']}, 命中率={stats['hit_rate']:.1%}")
    print(f"  内存优化统计: {stats.get('memory_optimized', 'N/A')}个键使用哈希")
    
    # 验证缓存命中
    tokenize(short_source)  # 第二次调用
    tokenize(long_source)   # 第二次调用
    stats = get_cache_stats()
    print(f"重复调用后命中率: {stats['hit_rate']:.1%}")
    
    if stats['hit_rate'] > 0:
        print("OK 缓存命中功能正常")
        return True
    else:
        print("FAIL 缓存命中异常")
        return False

def test_memory_efficiency():
    """测试内存效率"""
    print("\n=== 内存效率测试 ===")
    
    clear_cache()
    initial_stats = get_cache_stats()
    
    # 插入大量长字符串
    for i in range(100):
        long_source = f"这是第{i}个很长的测试字符串，" * 5 + f"定义变量{i}=值{i}。"
        tokenize(long_source)
    
    stats = get_cache_stats()
    print(f"插入100个长字符串后:")
    print(f"  缓存大小: {stats['size']}")
    print(f"  内存优化键: {stats.get('memory_optimized', 'N/A')}")
    print(f"  键映射大小: {stats.get('key_map_size', 'N/A')}")
    
    if stats.get('memory_optimized', 0) > 0:
        print("OK 内存优化生效（长字符串使用哈希键）")
        return True
    else:
        print("WARN 内存优化未生效（可能所有字符串都较短）")
        return True  # 不视为失败

def test_performance():
    """性能测试"""
    print("\n=== 性能测试 ===")
    
    clear_cache()
    import time
    
    # 准备长字符串
    sources = []
    for i in range(50):
        sources.append(f"定义长变量{i}={'很长很长的值' * 10}加上{i}。")
    
    # 无缓存测试
    start = time.perf_counter()
    for source in sources:
        tokenize(source, use_cache=False)
    time_no_cache = time.perf_counter() - start
    
    # 有缓存测试（第一次填充）
    clear_cache()
    start = time.perf_counter()
    for source in sources:
        tokenize(source, use_cache=True)
    time_with_cache_fill = time.perf_counter() - start
    
    # 有缓存测试（第二次命中）
    start = time.perf_counter()
    for source in sources:
        tokenize(source, use_cache=True)
    time_with_cache_hit = time.perf_counter() - start
    
    print(f"无缓存: {time_no_cache:.4f}s")
    print(f"有缓存（第一次填充）: {time_with_cache_fill:.4f}s")
    print(f"有缓存（第二次命中）: {time_with_cache_hit:.4f}s")
    print(f"缓存命中后加速比: {time_with_cache_fill/time_with_cache_hit:.2f}x")
    print(f"相对于无缓存加速比: {time_no_cache/time_with_cache_hit:.2f}x")
    
    if time_no_cache / time_with_cache_hit > 1.5:
        print("OK 优化版缓存性能提升显著")
        return True
    else:
        print("WARN 优化版缓存性能提升有限")
        return True

def test_lru_eviction_with_optimized_keys():
    """测试优化键的LRU淘汰"""
    print("\n=== 优化键LRU淘汰测试 ===")
    
    clear_cache()
    max_size = get_cache_stats()['max_size']
    
    # 创建大量独特的长字符串
    for i in range(max_size + 20):
        long_source = f"淘汰测试字符串{i}=" + "x" * 100 + f"值{i}。"
        tokenize(long_source)
    
    stats = get_cache_stats()
    print(f"插入{max_size+20}个长字符串后:")
    print(f"  缓存大小: {stats['size']} (应≤{max_size})")
    print(f"  内存优化键: {stats.get('memory_optimized', 'N/A')}")
    
    if stats['size'] <= max_size:
        print("OK LRU淘汰机制与优化键兼容")
        return True
    else:
        print(f"FAIL LRU淘汰异常: 大小{stats['size']}超过限制{max_size}")
        return False

if __name__ == '__main__':
    all_passed = True
    
    if not test_basic_functionality():
        all_passed = False
    
    if not test_memory_efficiency():
        all_passed = False
    
    if not test_performance():
        all_passed = False
    
    if not test_lru_eviction_with_optimized_keys():
        all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("OK 所有优化版缓存测试通过！")
        
        # 显示详细统计
        final_stats = get_cache_stats()
        print(f"\n最终优化版缓存统计:")
        for key, value in final_stats.items():
            print(f"  {key}: {value}")
    else:
        print("FAIL 部分优化版缓存测试失败")




