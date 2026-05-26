



#!/usr/bin/env python3
"""
全部分词器性能比较测试
"""
import sys
import os
import time
sys.path.insert(0, os.path.abspath('src'))

from yanzhi.compiler.pre_tokenizer import tokenize as original_tokenize
from yanzhi.compiler.pre_tokenizer_optimized import tokenize_optimized as trie_tokenize
from yanzhi.compiler.pre_tokenizer_cached import tokenize_cached as cached_tokenize
from yanzhi.compiler.pre_tokenizer_cached import CachedPreTokenizer

def generate_test_cases():
    """生成测试用例"""
    # 常见模式
    common_patterns = [
        "定义x=5相加3。",
        "列表1 2 3，映射相乘2。",
        "如果x大于y那么x否则y。",
        "张三=18。",
        "定义阶乘=函数n如果n等于1那么1否则n相乘阶乘n相减1。",
    ]
    
    # 长文本
    chinese_chars = "定函如返打印加载运算处理计算数据算法结构变量类型函数模块导入导出测试验证确认"
    verbs = "相加相减相乘相除大于小于等于不等于映射过滤归约列表首个剩余长度"
    
    long_text = ""
    for i in range(100):
        if i % 10 == 0:
            long_text += "。"
        long_text += chinese_chars[i % len(chinese_chars)]
    
    # 重复模式（测试缓存效果）
    repeated = "定义变量=值。" * 20
    
    return common_patterns + [long_text, repeated]

def benchmark_tokenizers():
    """基准测试"""
    test_cases = generate_test_cases()
    iterations = 100
    
    print("分词器性能比较测试")
    print("=" * 60)
    
    results = []
    
    for i, source in enumerate(test_cases):
        print(f"\n测试用例 {i+1}/{len(test_cases)}: {source[:50]}...")
        
        # 预热
        _ = original_tokenize(source)
        _ = trie_tokenize(source)
        _ = cached_tokenize(source)
        
        # 原始版本
        start = time.perf_counter()
        for _ in range(iterations):
            original_tokenize(source)
        original_time = time.perf_counter() - start
        
        # Trie优化版本
        start = time.perf_counter()
        for _ in range(iterations):
            trie_tokenize(source)
        trie_time = time.perf_counter() - start
        
        # 缓存优化版本
        start = time.perf_counter()
        for _ in range(iterations):
            cached_tokenize(source)
        cached_time = time.perf_counter() - start
        
        # 计算加速比
        trie_speedup = original_time / trie_time if trie_time > 0 else 0
        cached_speedup = original_time / cached_time if cached_time > 0 else 0
        
        print(f"  原始版本: {original_time:.4f}s")
        print(f"  Trie优化: {trie_time:.4f}s ({trie_speedup:.2f}x)")
        print(f"  缓存优化: {cached_time:.4f}s ({cached_speedup:.2f}x)")
        
        # 验证结果一致性
        orig_tokens = original_tokenize(source)
        trie_tokens = trie_tokenize(source)
        cached_tokens = cached_tokenize(source)
        
        # 比较长度
        if len(orig_tokens) != len(trie_tokens) or len(orig_tokens) != len(cached_tokens):
            print(f"  警告: Token数量不一致!")
            print(f"    原始: {len(orig_tokens)}, Trie: {len(trie_tokens)}, 缓存: {len(cached_tokens)}")
        
        results.append({
            'case': i,
            'length': len(source),
            'original': original_time,
            'trie': trie_time,
            'cached': cached_time,
            'trie_speedup': trie_speedup,
            'cached_speedup': cached_speedup
        })
    
    # 汇总统计
    print("\n" + "=" * 60)
    print("汇总统计:")
    
    avg_original = sum(r['original'] for r in results) / len(results)
    avg_trie = sum(r['trie'] for r in results) / len(results)
    avg_cached = sum(r['cached'] for r in results) / len(results)
    
    print(f"平均时间 - 原始: {avg_original:.4f}s, Trie: {avg_trie:.4f}s, 缓存: {avg_cached:.4f}s")
    print(f"平均加速比 - Trie: {avg_original/avg_trie:.2f}x, 缓存: {avg_original/avg_cached:.2f}x")
    
    # 缓存统计
    cache_stats = CachedPreTokenizer.get_cache_stats()
    print(f"\n缓存统计:")
    print(f"  命中次数: {cache_stats['hits']}")
    print(f"  未命中次数: {cache_stats['misses']}")
    print(f"  命中率: {cache_stats['hit_rate']:.1%}")
    print(f"  缓存大小: {cache_stats['size']}/{cache_stats['max_size']}")
    
    # 最佳情况分析
    best_trie = max(results, key=lambda x: x['trie_speedup'])
    worst_trie = min(results, key=lambda x: x['trie_speedup'])
    
    print(f"\nTrie优化最佳情况: 用例{best_trie['case']}, 加速比{best_trie['trie_speedup']:.2f}x")
    print(f"Trie优化最差情况: 用例{worst_trie['case']}, 加速比{worst_trie['trie_speedup']:.2f}x")
    
    best_cached = max(results, key=lambda x: x['cached_speedup'])
    worst_cached = min(results, key=lambda x: x['cached_speedup'])
    
    print(f"缓存优化最佳情况: 用例{best_cached['case']}, 加速比{best_cached['cached_speedup']:.2f}x")
    print(f"缓存优化最差情况: 用例{worst_cached['case']}, 加速比{worst_cached['cached_speedup']:.2f}x")
    
    return results

def test_cache_effectiveness():
    """测试缓存效果"""
    print("\n" + "=" * 60)
    print("缓存效果测试")
    print("=" * 60)
    
    # 清空缓存
    CachedPreTokenizer.clear_cache()
    
    test_source = "定义变量=值相加2。"
    iterations = 1000
    
    # 第一次运行（缓存未命中）
    start = time.perf_counter()
    for _ in range(iterations):
        cached_tokenize(test_source)
    first_run = time.perf_counter() - start
    
    # 第二次运行（缓存命中）
    start = time.perf_counter()
    for _ in range(iterations):
        cached_tokenize(test_source)
    second_run = time.perf_counter() - start
    
    # 无缓存版本对比
    start = time.perf_counter()
    for _ in range(iterations):
        original_tokenize(test_source)
    no_cache = time.perf_counter() - start
    
    print(f"无缓存版本: {no_cache:.4f}s")
    print(f"缓存版本第一次运行: {first_run:.4f}s (缓存未命中)")
    print(f"缓存版本第二次运行: {second_run:.4f}s (缓存命中)")
    print(f"缓存命中后加速比: {first_run/second_run:.2f}x")
    print(f"相对于无缓存加速比: {no_cache/second_run:.2f}x")
    
    cache_stats = CachedPreTokenizer.get_cache_stats()
    print(f"\n最终缓存统计: 命中率={cache_stats['hit_rate']:.1%}")

if __name__ == '__main__':
    benchmark_tokenizers()
    test_cache_effectiveness()



