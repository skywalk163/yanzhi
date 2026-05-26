
#!/usr/bin/env python3
"""
测试动态分区调整功能
"""

import sys
sys.path.insert(0, 'src')

from yanzhi.compiler.pre_tokenizer import (
    tokenize, get_cache_stats, get_cache_warnings, clear_cache,
    _token_cache  # 直接访问缓存实例
)

def test_basic_functionality():
    """测试基本功能"""
    print("=== 测试动态分区调整基本功能 ===")
    
    # 清空缓存
    clear_cache()
    
    # 添加一些测试数据
    test_sources = [
        f"测试代码{i} 乘以 {i+1} 等于结果。" for i in range(200)
    ]
    
    # 首次分词（填充缓存）
    for i, source in enumerate(test_sources[:50]):
        tokenize(source, use_cache=True)
    
    # 获取初始统计
    stats = get_cache_stats()
    print(f"初始分区数量: {stats['dynamic_partitioning']['current_partitions']}")
    print(f"缓存大小: {stats['size']}/{stats['max_size']}")
    print(f"分区分布: {stats['partition_sizes']}")
    
    # 添加更多数据，可能触发重新平衡
    for i, source in enumerate(test_sources[50:150]):
        tokenize(source, use_cache=True)
    
    # 获取更新后的统计
    stats = get_cache_stats()
    print(f"\n添加数据后分区数量: {stats['dynamic_partitioning']['current_partitions']}")
    print(f"缓存大小: {stats['size']}/{stats['max_size']}")
    print(f"分区分布: {stats['partition_sizes']}")
    
    # 强制触发重新平衡
    print("\n=== 强制触发重新平衡 ===")
    success = _token_cache.auto_rebalance()
    print(f"重新平衡结果: {'成功' if success else '无需调整'}")
    
    # 最终统计
    stats = get_cache_stats()
    print(f"\n最终分区数量: {stats['dynamic_partitioning']['current_partitions']}")
    print(f"重新平衡次数: {stats['dynamic_partitioning']['rebalance_count']}")
    print(f"分区历史记录: {stats['partition_history_count']} 次")
    
    return True

def test_partition_imbalance():
    """测试分区不均衡检测"""
    print("\n=== 测试分区不均衡检测 ===")
    
    clear_cache()
    
    # 创建不均衡负载：所有访问同一个分区
    partition_keys = {0: [], 1: [], 2: [], 3: []}
    
    # 使用特定的键确保它们映射到同一个分区
    # 注意：这依赖于哈希函数，我们只需要创建大量相同分区的键
    test_base = "不均衡测试"
    for i in range(100):
        key = f"{test_base}_{i}"
        tokens = tokenize(key, use_cache=True)
    
    # 获取统计
    stats = get_cache_stats()
    print(f"分区分布: {stats['partition_sizes']}")
    
    # 检查不均衡警告
    warnings = get_cache_warnings()
    print(f"警告信息: {warnings}")
    
    # 强制重新平衡
    success = _token_cache.auto_rebalance()
    print(f"重新平衡结果: {'成功' if success else '无需调整'}")
    
    # 再次检查分区分布
    stats = get_cache_stats()
    print(f"重新平衡后分区分布: {stats['partition_sizes']}")
    
    return True

def test_performance_monitoring():
    """测试性能监控和调整"""
    print("\n=== 测试性能监控和调整 ===")
    
    clear_cache()
    
    # 添加大量数据
    test_sources = [
        f"性能测试代码_{i}_乘以_{j}_结果。" 
        for i in range(100) 
        for j in range(3)
    ]
    
    # 批量添加（触发多次自动调整检查）
    for i, source in enumerate(test_sources):
        tokenize(source, use_cache=True)
        
        # 定期打印进度
        if i % 100 == 0 and i > 0:
            stats = get_cache_stats()
            print(f"  添加 {i} 项后: {stats['dynamic_partitioning']['current_partitions']} 分区, "
                  f"大小 {stats['size']}, 重新平衡 {stats['dynamic_partitioning']['rebalance_count']} 次")
    
    # 最终统计
    stats = get_cache_stats()
    print(f"\n最终结果:")
    print(f"  分区数量: {stats['dynamic_partitioning']['current_partitions']}")
    print(f"  缓存大小: {stats['size']}/{stats['max_size']}")
    print(f"  重新平衡次数: {stats['dynamic_partitioning']['rebalance_count']}")
    print(f"  命中率: {stats['hit_rate']:.1%}")
    print(f"  读写比例: {stats['read_write_ratio']:.1f}")
    print(f"  锁等待时间: {stats['total_lock_wait_time']:.3f}s")
    
    return True

def test_configuration_limits():
    """测试配置限制"""
    print("\n=== 测试配置限制 ===")
    
    clear_cache()
    
    # 测试最小分区限制
    print("测试最小分区限制...")
    _token_cache.min_partitions = 2
    _token_cache.max_partitions = 4
    _token_cache.rebalance_threshold = 0.1  # 低阈值，容易触发
    
    # 添加大量数据
    for i in range(500):
        tokenize(f"配置测试代码_{i}", use_cache=True)
    
    stats = get_cache_stats()
    print(f"分区数量: {stats['dynamic_partitioning']['current_partitions']} "
          f"(最小={_token_cache.min_partitions}, 最大={_token_cache.max_partitions})")
    
    # 验证在限制范围内
    assert _token_cache.min_partitions <= stats['dynamic_partitioning']['current_partitions'] <= _token_cache.max_partitions
    print("配置限制测试通过!")
    
    return True

def main():
    """主测试函数"""
    print("开始测试动态分区调整功能...")
    
    try:
        # 运行所有测试
        test_basic_functionality()
        test_partition_imbalance()
        test_performance_monitoring()
        test_configuration_limits()
        
        print("\n" + "="*60)
        print("✅ 所有动态分区调整测试通过!")
        print("="*60)
        
        # 打印最终统计摘要
        stats = get_cache_stats()
        print("\n最终缓存统计摘要:")
        print(f"  分区数量: {stats['dynamic_partitioning']['current_partitions']}")
        print(f"  缓存大小: {stats['size']}/{stats['max_size']}")
        print(f"  命中率: {stats['hit_rate']:.1%}")
        print(f"  重新平衡次数: {stats['dynamic_partitioning']['rebalance_count']}")
        print(f"  距离上次重新平衡: {stats['dynamic_partitioning']['time_since_last_rebalance']:.1f}秒")
        
        return True
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
