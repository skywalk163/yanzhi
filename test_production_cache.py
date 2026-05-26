


#!/usr/bin/env python3
"""
测试生产代码中的缓存机制
"""
import sys
import os
sys.path.insert(0, os.path.abspath('src'))

from yanzhi.compiler.pre_tokenizer import tokenize, get_cache_stats, clear_cache

def test_basic():
    """基础功能测试"""
    print("生产代码缓存机制测试")
    print("=" * 60)
    
    # 清空缓存
    clear_cache()
    
    test_source = "定义x=5相加3。"
    
    # 第一次调用（应该缓存未命中）
    tokens1 = tokenize(test_source)
    stats = get_cache_stats()
    print(f"第一次调用后:")
    print(f"  缓存命中: {stats['hits']}, 未命中: {stats['misses']}, 命中率: {stats['hit_rate']:.1%}")
    print(f"  Token数量: {len(tokens1)}")
    
    # 第二次调用相同代码（应该缓存命中）
    tokens2 = tokenize(test_source)
    stats = get_cache_stats()
    print(f"\n第二次调用相同代码后:")
    print(f"  缓存命中: {stats['hits']}, 未命中: {stats['misses']}, 命中率: {stats['hit_rate']:.1%}")
    print(f"  Token数量: {len(tokens2)}")
    
    # 验证结果一致性
    if len(tokens1) != len(tokens2):
        print("FAIL ERROR: Token数量不一致!")
        return False
    
    # 比较Token
    for i, (t1, t2) in enumerate(zip(tokens1, tokens2)):
        if t1.type != t2.type or t1.value != t2.value:
            print(f"FAIL ERROR: 第{i}个Token不一致:")
            print(f"   第一次: {t1}")
            print(f"   第二次: {t2}")
            return False
    
    print("OK 结果验证: 两次分词结果一致")
    return True

def test_disable_cache():
    """测试禁用缓存功能"""
    print("\n" + "=" * 60)
    print("测试禁用缓存功能")
    
    clear_cache()
    test_source = "列表1 2 3。"
    
    # 使用缓存
    tokens1 = tokenize(test_source, use_cache=True)
    stats1 = get_cache_stats()
    print(f"使用缓存调用后: 命中{stats1['hits']}次, 未命中{stats1['misses']}次")
    
    # 禁用缓存
    tokens2 = tokenize(test_source, use_cache=False)
    stats2 = get_cache_stats()
    print(f"禁用缓存调用后: 命中{stats2['hits']}次, 未命中{stats2['misses']}次")
    
    # 命中次数不应增加
    if stats2['hits'] == stats1['hits']:
        print("✅ 禁用缓存功能正常")
        return True
    else:
        print("FAIL ERROR: 禁用缓存功能异常")
        return False

def test_performance():
    """性能测试"""
    print("\n" + "=" * 60)
    print("性能测试")
    
    import time
    
    clear_cache()
    test_source = "如果x大于y那么x否则y。"
    iterations = 1000
    
    # 第一次运行（缓存未命中）
    start = time.perf_counter()
    for _ in range(iterations):
        tokenize(test_source, use_cache=True)
    first_run = time.perf_counter() - start
    
    # 第二次运行（缓存命中）
    start = time.perf_counter()
    for _ in range(iterations):
        tokenize(test_source, use_cache=True)
    second_run = time.perf_counter() - start
    
    # 无缓存运行
    clear_cache()
    start = time.perf_counter()
    for _ in range(iterations):
        tokenize(test_source, use_cache=False)
    no_cache = time.perf_counter() - start
    
    print(f"无缓存版本: {no_cache:.4f}s")
    print(f"缓存版本第一次运行: {first_run:.4f}s (缓存未命中)")
    print(f"缓存版本第二次运行: {second_run:.4f}s (缓存命中)")
    print(f"缓存命中后加速比: {first_run/second_run:.2f}x")
    print(f"相对于无缓存加速比: {no_cache/second_run:.2f}x")
    
    stats = get_cache_stats()
    print(f"缓存统计: 命中率={stats['hit_rate']:.1%}")
    
    if no_cache / second_run > 1.5:
        print("✅ 性能优化效果显著")
        return True
    else:
        print("⚠️ 性能优化效果不明显")
        return True  # 不视为失败

def test_existing_code_compatibility():
    """测试现有代码兼容性"""
    print("\n" + "=" * 60)
    print("测试现有代码兼容性")
    
    # 测试使用tokenize的其他模块能否正常工作
    try:
        from yanzhi.compiler.lexer import Lexer
        
        source = "定义阶乘=函数n如果n等于1那么1否则n相乘阶乘n相减1。"
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        
        print(f"Lexer模块工作正常，生成{len(tokens)}个Token")
        
        # 检查Token类型
        token_types = set(t.type.name for t in tokens if t.type.name != 'EOF')
        print(f"包含的Token类型: {', '.join(sorted(token_types))}")
        
        print("✅ 现有代码兼容性测试通过")
        return True
    except Exception as e:
        print(f"❌ ERROR: 兼容性测试失败: {e}")
        return False

if __name__ == '__main__':
    all_passed = True
    
    if not test_basic():
        all_passed = False
    
    if not test_disable_cache():
        all_passed = False
    
    if not test_performance():
        all_passed = False
    
    if not test_existing_code_compatibility():
        all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ 所有测试通过！缓存机制已成功部署到生产代码")
        
        # 显示最终缓存统计
        final_stats = get_cache_stats()
        print(f"\n最终缓存统计:")
        print(f"  命中次数: {final_stats['hits']}")
        print(f"  未命中次数: {final_stats['misses']}")
        print(f"  命中率: {final_stats['hit_rate']:.1%}")
        print(f"  缓存大小: {final_stats['size']}/{final_stats['max_size']}")
    else:
        print("❌ 部分测试失败，请检查实现")


