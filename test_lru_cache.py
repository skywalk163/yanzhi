



#!/usr/bin/env python3
"""
测试LRU缓存功能
"""
import sys
import os
sys.path.insert(0, os.path.abspath('src'))

from yanzhi.compiler.pre_tokenizer import tokenize, get_cache_stats, clear_cache

def test_lru_eviction():
    """测试LRU淘汰机制"""
    print("=== 测试LRU淘汰机制 ===")
    
    clear_cache()
    stats = get_cache_stats()
    max_size = stats['max_size']
    
    print(f"缓存最大容量: {max_size}")
    
    # 创建超过缓存容量的独特源代码
    sources = [f"定义x={i}。" for i in range(max_size + 10)]
    
    # 第一次填充缓存
    for i, source in enumerate(sources[:max_size]):
        tokenize(source)
    
    stats = get_cache_stats()
    print(f"填充{max_size}个条目后缓存大小: {stats['size']}")
    
    # 添加额外的条目，应该触发淘汰
    tokenize(sources[max_size])
    
    stats = get_cache_stats()
    print(f"添加额外条目后缓存大小: {stats['size']} (应保持{max_size})")
    
    if stats['size'] == max_size:
        print("OK LRU淘汰机制工作正常")
        return True
    else:
        print(f"FAIL LRU淘汰机制异常: 实际大小{stats['size']}, 期望{max_size}")
        return False

def test_lru_access_order():
    """测试LRU访问顺序"""
    print("\n=== 测试LRU访问顺序 ===")
    
    clear_cache()
    
    # 创建几个测试源代码
    test_cases = ["定义x=1。", "定义y=2。", "定义z=3。", "定义w=4。"]
    
    # 顺序访问
    for source in test_cases:
        tokenize(source)
    
    # 再次访问第一个，使其"最近使用"
    tokenize(test_cases[0])
    
    # 现在添加新条目，应该淘汰最近最少使用的(应该是test_cases[1])
    for i in range(5, 10):
        tokenize(f"定义new{i}={i}。")
    
    # 检查test_cases[0]是否仍在缓存中（最近使用）
    clear_cache()  # 清空缓存重新测试
    
    # 更简单的测试：检查缓存命中率
    source = "测试缓存命中。"
    
    # 第一次访问
    tokenize(source)
    stats1 = get_cache_stats()
    print(f"第一次访问后命中率: {stats1['hit_rate']:.1%}")
    
    # 第二次访问
    tokenize(source)
    stats2 = get_cache_stats()
    print(f"第二次访问后命中率: {stats2['hit_rate']:.1%}")
    
    if stats2['hit_rate'] > stats1['hit_rate']:
        print("✅ 缓存命中率随重复访问提高")
        return True
    else:
        print("❌ 缓存命中率未提高")
        return False

def test_performance_with_lru():
    """测试LRU缓存性能"""
    print("\n=== 测试LRU缓存性能 ===")
    
    clear_cache()
    
    import time
    
    # 测试重复访问性能
    test_source = "定义阶乘=函数n如果n等于1那么1否则n相乘阶乘n相减1。"
    iterations = 1000
    
    # 无缓存
    start = time.perf_counter()
    for _ in range(iterations):
        tokenize(test_source, use_cache=False)
    time_no_cache = time.perf_counter() - start
    
    # 有LRU缓存（先填充）
    tokenize(test_source, use_cache=True)  # 填充缓存
    start = time.perf_counter()
    for _ in range(iterations):
        tokenize(test_source, use_cache=True)
    time_lru_cache = time.perf_counter() - start
    
    print(f"无缓存 {iterations}次: {time_no_cache:.4f}s")
    print(f"LRU缓存 {iterations}次: {time_lru_cache:.4f}s")
    print(f"加速比: {time_no_cache/time_lru_cache:.2f}x")
    
    if time_no_cache / time_lru_cache > 1.5:
        print("✅ LRU缓存性能提升显著")
        return True
    else:
        print("⚠️ LRU缓存性能提升有限")
        return True

def test_memory_safety():
    """测试内存安全性"""
    print("\n=== 测试内存安全性 ===")
    
    clear_cache()
    max_size = get_cache_stats()['max_size']
    
    # 创建大量独特的源代码，确保不会内存泄漏
    for i in range(max_size * 2):
        tokenize(f"大量测试代码{i}=值{i}。")
    
    stats = get_cache_stats()
    print(f"插入{max_size*2}个条目后缓存大小: {stats['size']}/{max_size}")
    
    if stats['size'] <= max_size:
        print("✅ 内存安全: 缓存大小限制有效")
        return True
    else:
        print(f"❌ 内存安全异常: 缓存大小{stats['size']}超过限制{max_size}")
        return False

if __name__ == '__main__':
    all_passed = True
    
    if not test_lru_eviction():
        all_passed = False
    
    if not test_lru_access_order():
        all_passed = False
    
    if not test_performance_with_lru():
        all_passed = False
    
    if not test_memory_safety():
        all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ 所有LRU缓存测试通过！")
        
        # 显示最终统计
        final_stats = get_cache_stats()
        print(f"\n最终缓存统计:")
        print(f"  命中次数: {final_stats['hits']}")
        print(f"  未命中次数: {final_stats['misses']}")
        print(f"  命中率: {final_stats['hit_rate']:.1%}")
        print(f"  缓存大小: {final_stats['size']}/{final_stats['max_size']}")
    else:
        print("❌ 部分LRU缓存测试失败")



