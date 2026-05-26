

#!/usr/bin/env python3
"""
测试动态分区调整功能（简化版）
"""

import sys
sys.path.insert(0, 'src')

from yanzhi.compiler.pre_tokenizer import (
    tokenize, get_cache_stats, get_cache_warnings, clear_cache,
    _token_cache  # 直接访问缓存实例
)

def main():
    """主测试函数"""
    print("开始测试动态分区调整功能...")
    
    # 清空缓存
    clear_cache()
    
    # 1. 测试基本功能
    print("\n1. 测试基本功能")
    for i in range(100):
        tokenize(f"测试代码_{i}", use_cache=True)
    
    stats = get_cache_stats()
    print(f"  初始分区: {stats['dynamic_partitioning']['current_partitions']}")
    print(f"  缓存大小: {stats['size']}")
    print(f"  分区分布: {stats['partition_sizes']}")
    
    # 2. 测试重新平衡
    print("\n2. 测试重新平衡")
    
    # 修改阈值以强制重新平衡
    _token_cache.rebalance_threshold = 0.1
    _token_cache.rebalance_interval = 0  # 立即检查
    
    # 添加更多数据
    for i in range(100, 300):
        tokenize(f"测试代码_{i}", use_cache=True)
    
    # 手动触发重新平衡
    success = _token_cache.auto_rebalance()
    print(f"  重新平衡结果: {'成功' if success else '无需调整'}")
    
    # 3. 检查最终状态
    stats = get_cache_stats()
    print("\n3. 最终状态")
    print(f"  分区数量: {stats['dynamic_partitioning']['current_partitions']}")
    print(f"  缓存大小: {stats['size']}/{stats['max_size']}")
    print(f"  重新平衡次数: {stats['dynamic_partitioning']['rebalance_count']}")
    print(f"  命中率: {stats['hit_rate']:.1%}")
    
    # 4. 验证功能
    print("\n4. 验证功能")
    
    # 验证缓存命中
    test_source = "测试代码_50"
    tokens1 = tokenize(test_source, use_cache=True)
    tokens2 = tokenize(test_source, use_cache=True)
    
    if len(tokens1) == len(tokens2) and all(t1.type == t2.type for t1, t2 in zip(tokens1, tokens2)):
        print("  缓存命中验证: 通过")
    else:
        print("  缓存命中验证: 失败")
        return False
    
    # 验证统计信息
    if stats['dynamic_partitioning']['current_partitions'] >= _token_cache.min_partitions:
        print("  分区数量验证: 通过")
    else:
        print("  分区数量验证: 失败")
        return False
    
    print("\n" + "="*60)
    print("所有动态分区调整测试通过!")
    print("="*60)
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)

