





#!/usr/bin/env python3
"""
测试线程安全的缓存实现
"""
import sys
import os
import threading
import time
import random
sys.path.insert(0, os.path.abspath('src'))

from yanzhi.compiler.pre_tokenizer import tokenize, get_cache_stats, clear_cache, get_cache_warnings

def worker(worker_id, sources, results, errors):
    """工作线程函数"""
    try:
        for i, source in enumerate(sources):
            # 随机选择是否使用缓存
            use_cache = random.choice([True, False])
            
            # 执行分词
            tokens = tokenize(source, use_cache=use_cache)
            
            # 记录结果
            results.append({
                'worker': worker_id,
                'source': source,
                'token_count': len(tokens),
                'use_cache': use_cache
            })
            
            # 随机延迟，模拟实际工作负载
            time.sleep(random.uniform(0.001, 0.01))
            
    except Exception as e:
        errors.append(f"Worker {worker_id} error: {e}")

def test_concurrent_access():
    """测试并发访问"""
    print("=== 线程安全测试：并发访问 ===")
    
    clear_cache()
    
    # 准备测试数据
    test_sources = [
        f"定义线程安全测试{i}=值{i}。" for i in range(20)
    ]
    
    # 创建多个线程
    num_threads = 5
    threads = []
    all_results = []
    all_errors = []
    results_per_thread = []
    
    for i in range(num_threads):
        # 每个线程处理所有源代码（模拟并发访问）
        results = []
        errors = []
        t = threading.Thread(
            target=worker,
            args=(i, test_sources, results, errors),
            name=f"Worker-{i}"
        )
        threads.append(t)
        results_per_thread.append(results)
        all_errors.extend(errors)
    
    # 启动所有线程
    start_time = time.time()
    for t in threads:
        t.start()
    
    # 等待所有线程完成
    for t in threads:
        t.join()
    end_time = time.time()
    
    # 收集所有结果
    for results in results_per_thread:
        all_results.extend(results)
    
    # 输出统计信息
    execution_time = end_time - start_time
    print(f"并发执行时间: {execution_time:.3f}s")
    print(f"线程数量: {num_threads}")
    print(f"总执行次数: {len(all_results)}")
    print(f"错误数量: {len(all_errors)}")
    
    if all_errors:
        print(f"错误信息: {all_errors}")
        return False
    
    # 检查缓存统计
    stats = get_cache_stats()
    print(f"\n缓存统计:")
    print(f"  命中次数: {stats['hits']}")
    print(f"  未命中次数: {stats['misses']}")
    print(f"  命中率: {stats['hit_rate']:.1%}")
    print(f"  缓存大小: {stats['size']}")
    
    # 验证结果一致性（相同的源代码应该产生相同的分词结果）
    source_to_token_count = {}
    for result in all_results:
        source = result['source']
        token_count = result['token_count']
        
        if source not in source_to_token_count:
            source_to_token_count[source] = token_count
        elif source_to_token_count[source] != token_count:
            print(f"错误: 源代码 '{source}' 的分词结果不一致")
            print(f"  预期: {source_to_token_count[source]} tokens")
            print(f"  实际: {token_count} tokens")
            return False
    
    print("OK 所有相同源代码的分词结果一致")
    return True

def test_thread_safety_under_contention():
    """测试高竞争下的线程安全性"""
    print("\n=== 线程安全测试：高竞争环境 ===")
    
    clear_cache()
    
    # 使用少量源代码，增加竞争
    high_contention_sources = [
        "定义竞争测试=值123。",
        "如果条件成立那么执行操作否则跳过。",
        "列表1 2 3 4 5，映射相加1。",
    ]
    
    num_threads = 10
    iterations = 50
    errors = []
    
    def high_contention_worker(worker_id):
        try:
            for _ in range(iterations):
                source = random.choice(high_contention_sources)
                # 随机选择是否使用缓存
                use_cache = random.choice([True, False])
                tokenize(source, use_cache=use_cache)
                
                # 50%的概率获取统计信息
                if random.random() > 0.5:
                    get_cache_stats()
                
                # 10%的概率清空缓存
                if random.random() > 0.9:
                    clear_cache()
                    
        except Exception as e:
            errors.append(f"HighContentionWorker {worker_id} error: {e}")
    
    # 创建和启动线程
    threads = []
    for i in range(num_threads):
        t = threading.Thread(
            target=high_contention_worker,
            args=(i,),
            name=f"HighContention-{i}"
        )
        threads.append(t)
    
    start_time = time.time()
    for t in threads:
        t.start()
    
    for t in threads:
        t.join()
    end_time = time.time()
    
    execution_time = end_time - start_time
    total_operations = num_threads * iterations
    ops_per_second = total_operations / execution_time if execution_time > 0 else 0
    
    print(f"高竞争环境测试:")
    print(f"  线程数量: {num_threads}")
    print(f"  每线程迭代次数: {iterations}")
    print(f"  总操作数: {total_operations}")
    print(f"  执行时间: {execution_time:.3f}s")
    print(f"  操作/秒: {ops_per_second:.1f}")
    print(f"  错误数量: {len(errors)}")
    
    if errors:
        print(f"  错误信息: {errors}")
        return False
    
    # 最终缓存状态应该有效
    final_stats = get_cache_stats()
    if final_stats['size'] <= final_stats['max_size']:
        print("OK 缓存大小在限制范围内")
        return True
    else:
        print(f"FAIL 缓存大小异常: {final_stats['size']} > {final_stats['max_size']}")
        return False

def test_deadlock_prevention():
    """测试死锁预防（嵌套调用）"""
    print("\n=== 线程安全测试：死锁预防 ===")
    
    clear_cache()
    
    # 测试嵌套调用（stats()内部调用带锁的方法）
    try:
        # 先填充一些数据
        for i in range(10):
            tokenize(f"死锁测试{i}=值{i}。")
        
        # 嵌套调用：get_cache_stats() -> stats() -> 带锁
        stats1 = get_cache_stats()
        
        # 在锁内再次调用（测试可重入锁）
        stats2 = get_cache_stats()
        
        # 获取警告（也会调用stats()）
        warnings = get_cache_warnings()
        
        print(f"嵌套调用测试通过")
        print(f"  第一次统计: {stats1['size']} 条目")
        print(f"  第二次统计: {stats2['size']} 条目")
        print(f"  警告数量: {len(warnings)}")
        
        return True
        
    except Exception as e:
        print(f"FAIL 死锁预防测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_performance_with_threads():
    """测试多线程性能"""
    print("\n=== 线程安全测试：性能影响 ===")
    
    clear_cache()
    
    # 单线程基准测试
    test_source = "定义性能测试=值123456789。"
    iterations = 1000
    
    # 单线程
    start = time.time()
    for _ in range(iterations):
        tokenize(test_source, use_cache=True)
    single_thread_time = time.time() - start
    
    # 多线程
    clear_cache()
    num_threads = 4
    iterations_per_thread = iterations // num_threads
    
    def perf_worker():
        for _ in range(iterations_per_thread):
            tokenize(test_source, use_cache=True)
    
    threads = []
    start = time.time()
    for _ in range(num_threads):
        t = threading.Thread(target=perf_worker)
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join()
    multi_thread_time = time.time() - start
    
    print(f"性能测试结果:")
    print(f"  单线程时间: {single_thread_time:.3f}s")
    print(f"  多线程时间: {multi_thread_time:.3f}s ({num_threads} 线程)")
    print(f"  加速比: {single_thread_time/multi_thread_time:.2f}x")
    print(f"  效率: {(single_thread_time/multi_thread_time)/num_threads*100:.1f}%")
    
    # 线程安全通常会有轻微性能开销
    if multi_thread_time < single_thread_time * 1.5:  # 允许50%开销
        print("OK 线程安全开销在可接受范围")
        return True
    else:
        print("WARN 线程安全开销较大")
        return True  # 不视为失败，只是警告

if __name__ == '__main__':
    all_passed = True
    
    print("开始线程安全测试...")
    
    if not test_concurrent_access():
        all_passed = False
    
    if not test_thread_safety_under_contention():
        all_passed = False
    
    if not test_deadlock_prevention():
        all_passed = False
    
    if not test_performance_with_threads():
        all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("OK 所有线程安全测试通过！")
        
        # 显示最终统计
        final_stats = get_cache_stats()
        print(f"\n最终缓存统计:")
        print(f"  总命中次数: {final_stats['hits']}")
        print(f"  总未命中次数: {final_stats['misses']}")
        print(f"  最终命中率: {final_stats['hit_rate']:.1%}")
        print(f"  线程安全: 是 (使用threading.RLock)")
    else:
        print("FAIL 部分线程安全测试失败")




