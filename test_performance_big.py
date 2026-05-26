

#!/usr/bin/env python3
"""
大文本性能测试
"""
import sys
import os
sys.path.insert(0, os.path.abspath('src'))

from yanzhi.compiler.pre_tokenizer import tokenize as original_tokenize
from yanzhi.compiler.pre_tokenizer_optimized import tokenize_optimized as optimized_tokenize
import time
import random

# 生成大文本测试用例
chinese_chars = "定函如返打印加载运算处理计算数据算法结构变量类型函数模块导入导出测试验证确认"
verbs = "相加相减相乘相除大于小于等于不等于映射过滤归约列表首个剩余长度"
keywords = "定义函数如果否则循环遍历导入结构方法返回抛出尝试捕获结束"

def generate_large_text(size=1000):
    """生成大段中文文本"""
    text = []
    all_chars = chinese_chars + verbs + keywords
    
    # 添加一些标点
    punctuation = ['。', '，', '：', '=']
    
    for i in range(size):
        if random.random() < 0.1:  # 10%概率添加标点
            text.append(random.choice(punctuation))
        else:
            # 随机选择1-3个字符的词
            word_len = random.randint(1, 3)
            word = ''.join(random.choice(all_chars) for _ in range(word_len))
            text.append(word)
    
    return ''.join(text)

def benchmark_large():
    print("大文本分词性能测试")
    print("=" * 50)
    
    # 生成测试数据
    test_sizes = [100, 500, 1000, 2000]
    
    for size in test_sizes:
        print(f"\n文本大小: {size} 字符")
        source = generate_large_text(size)
        
        # 预热
        _ = original_tokenize(source)
        _ = optimized_tokenize(source)
        
        # 原始版性能
        start = time.perf_counter()
        for _ in range(10):
            original_tokenize(source)
        original_time = time.perf_counter() - start
        
        # 优化版性能
        start = time.perf_counter()
        for _ in range(10):
            optimized_tokenize(source)
        optimized_time = time.perf_counter() - start
        
        print(f"  原始版: {original_time:.3f}s")
        print(f"  优化版: {optimized_time:.3f}s")
        print(f"  加速比: {original_time/optimized_time:.2f}x")
        
        # 验证结果正确性
        original_tokens = original_tokenize(source)
        optimized_tokens = optimized_tokenize(source)
        
        if len(original_tokens) != len(optimized_tokens):
            print(f"  警告: Token数量不一致 - 原始: {len(original_tokens)}, 优化: {len(optimized_tokens)}")
        else:
            match_count = 0
            for i, (o1, o2) in enumerate(zip(original_tokens, optimized_tokens)):
                if o1.type == o2.type and o1.value == o2.value:
                    match_count += 1
            
            accuracy = match_count / len(original_tokens)
            print(f"  准确率: {accuracy:.1%}")

def benchmark_real_code():
    print("\n实际代码片段性能测试")
    print("=" * 50)
    
    # 实际代码片段
    real_code = """
定义 计算阶乘 = 函数 n：
    如果 n 等于 0 那么
        返回 1。
    否则
        返回 n 相乘 计算阶乘 (n 相减 1)。

定义 主函数 = 函数：
    打印 "计算斐波那契数列前10项："。
    循环 i 于 范围 1 到 10：
        打印 "斐波那契" i "=" 计算阶乘 i。
    
    列表 数据 = 列表 1 2 3 4 5 6 7 8 9 10。
    列表 平方 = 映射 函数 x：x 相乘 x。 于 数据。
    
    打印 "数据的平方：" 平方。
    
    返回 0。

主函数。
"""
    
    # 预热
    _ = original_tokenize(real_code)
    _ = optimized_tokenize(real_code)
    
    iterations = 100
    
    # 原始版性能
    start = time.perf_counter()
    for _ in range(iterations):
        original_tokenize(real_code)
    original_time = time.perf_counter() - start
    
    # 优化版性能
    start = time.perf_counter()
    for _ in range(iterations):
        optimized_tokenize(real_code)
    optimized_time = time.perf_counter() - start
    
    print(f"代码长度: {len(real_code)} 字符")
    print(f"迭代次数: {iterations}")
    print(f"原始版总时间: {original_time:.3f}s")
    print(f"优化版总时间: {optimized_time:.3f}s")
    print(f"加速比: {original_time/optimized_time:.2f}x")
    
    # 计算平均每字符时间
    chars_per_original = original_time / (len(real_code) * iterations) * 1e6  # 微秒/字符
    chars_per_optimized = optimized_time / (len(real_code) * iterations) * 1e6  # 微秒/字符
    print(f"原始版平均: {chars_per_original:.2f}μs/字符")
    print(f"优化版平均: {chars_per_optimized:.2f}μs/字符")

if __name__ == '__main__':
    benchmark_large()
    benchmark_real_code()

