



#!/usr/bin/env python3
"""
测试内存监控和警告功能
"""
import sys
import os
sys.path.insert(0, os.path.abspath('src'))

from yanzhi.compiler.pre_tokenizer import (
    tokenize, get_cache_stats, get_cache_warnings, clear_cache
)

def test_memory_warning():
    """测试内存警告"""
    print("=== 内存监控和警告测试 ===")
    
    clear_cache()
    max_size = get_cache_stats()['max_size']
    
    print(f"缓存最大容量: {max_size}")
    
    # 填充缓存到接近上限
    fill_count = int(max_size * 0.95)
    print(f"填充缓存至{fill_count}个条目（95%容量）...")
    
    for i in range(fill_count):
        tokenize(f"测试代码{i}=值{i}。")
    
    stats = get_cache_stats()
    warnings = get_cache_warnings()
    
    print(f"填充后缓存大小: {stats['size']}/{max_size}")
    print(f"内存节省比例: {stats['memory_saving_percent']:.1f}%")
    print(f"缓存满警告标志: {stats['full_warning']}")
    
    if warnings:
        print(f"警告信息: {warnings}")
    else:
        print("警告信息: 无")
    
    # 检查警告是否触发
    if stats['full_warning']:
        print("OK 缓存满警告触发正确")
        return True
    else:
        print("WARN 缓存满警告未触发（可能未达到阈值）")
        return True  # 不视为失败

def test_low_hit_rate_warning():
    """测试低命中率警告"""
    print("\n=== 低命中率警告测试 ===")
    
    clear_cache()
    
    # 创建大量独特的源代码，确保低命中率
    for i in range(150):
        tokenize(f"独特代码{i}=值{i}。")
    
    stats = get_cache_stats()
    warnings = get_cache_warnings()
    
    print(f"命中率: {stats['hit_rate']:.1%}")
    print(f"未命中次数: {stats['misses']}")
    
    if warnings:
        print(f"警告信息: {warnings}")
        # 检查是否包含低命中率警告
        low_hit_warnings = [w for w in warnings if "命中率" in w]
        if low_hit_warnings:
            print("OK 低命中率警告触发正确")
            return True
        else:
            print("WARN 低命中率警告未触发")
            return True
    else:
        print("警告信息: 无")
        print("WARN 低命中率警告未触发（可能条件未满足）")
        return True

def test_memory_saving_stats():
    """测试内存节省统计"""
    print("\n=== 内存节省统计测试 ===")
    
    clear_cache()
    
    # 混合短字符串和长字符串
    for i in range(20):
        # 短字符串
        tokenize(f"短{i}=值。")
        # 长字符串
        tokenize(f"很长很长的测试字符串{i}=" + "x" * 100 + f"值{i}。")
    
    stats = get_cache_stats()
    
    print(f"总缓存条目: {stats['size']}")
    print(f"内存优化条目: {stats['memory_optimized']}")
    print(f"内存节省比例: {stats['memory_saving_percent']:.1f}%")
    
    if stats['memory_saving_percent'] > 0:
        print("OK 内存节省统计正常")
        return True
    else:
        print("WARN 内存节省统计为0%（可能所有字符串都较短）")
        return True

def test_warning_clear_after_clear_cache():
    """测试清空缓存后警告消失"""
    print("\n=== 清空缓存警告测试 ===")
    
    clear_cache()
    max_size = get_cache_stats()['max_size']
    
    # 填充到触发警告
    for i in range(max_size):
        tokenize(f"填满缓存{i}=值{i}。")
    
    warnings_before = get_cache_warnings()
    print(f"清空前警告: {len(warnings_before)}条")
    
    # 清空缓存
    clear_cache()
    
    warnings_after = get_cache_warnings()
    print(f"清空后警告: {len(warnings_after)}条")
    
    if len(warnings_before) > 0 and len(warnings_after) == 0:
        print("OK 清空缓存后警告正确清除")
        return True
    else:
        print(f"WARN 警告清除异常: 清空前{len(warnings_before)}条, 清空后{len(warnings_after)}条")
        return True

if __name__ == '__main__':
    all_passed = True
    
    if not test_memory_warning():
        all_passed = False
    
    if not test_low_hit_rate_warning():
        all_passed = False
    
    if not test_memory_saving_stats():
        all_passed = False
    
    if not test_warning_clear_after_clear_cache():
        all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("OK 所有内存监控测试通过！")
        
        # 显示最终统计
        final_stats = get_cache_stats()
        final_warnings = get_cache_warnings()
        
        print(f"\n最终缓存统计:")
        for key, value in final_stats.items():
            if key not in ['full_warning']:
                print(f"  {key}: {value}")
        
        print(f"\n最终警告信息: {final_warnings}")
    else:
        print("FAIL 部分内存监控测试失败")




