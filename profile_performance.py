



#!/usr/bin/env python3
"""
言知系统性能分析
"""
import sys
import os
import cProfile
import pstats
import time
sys.path.insert(0, os.path.abspath('src'))

from yanzhi.compiler.pre_tokenizer import tokenize
from yanzhi.compiler.lexer import Lexer
from yanzhi.compiler.parser import Parser
from yanzhi.compiler.codegen import CodeGen
from yanzhi.runtime.vm import VM
from yanzhi.runtime.bytecode import BytecodeChunk

def create_test_code():
    """创建测试代码"""
    return """
定义 计算斐波那契 = 函数 n：
    如果 n 小于等于 1 那么
        返回 n。
    否则
        返回 计算斐波那契 (n 相减 1) 相加 计算斐波那契 (n 相减 2)。

定义 主函数 = 函数：
    循环 i 于 范围 1 到 10：
        结果 = 计算斐波那契 i。
        打印 "斐波那契" i "=" 结果。
    
    列表 数据 = 列表 1 2 3 4 5 6 7 8 9 10。
    列表 平方 = 映射 函数 x：x 相乘 x。 于 数据。
    
    打印 "数据的平方：" 平方。
    
    返回 0。

主函数。
"""

def profile_full_pipeline():
    """分析完整编译执行流程"""
    source = create_test_code()
    
    print("开始性能分析...")
    print("=" * 60)
    
    # 1. 分词性能
    print("\n1. 分词性能分析")
    pr = cProfile.Profile()
    pr.enable()
    for _ in range(100):
        tokens = tokenize(source)
    pr.disable()
    
    stats = pstats.Stats(pr)
    stats.sort_stats('cumulative')
    print("分词性能前10:")
    stats.print_stats(10)
    
    # 2. 词法分析性能
    print("\n2. 词法分析性能分析")
    pr = cProfile.Profile()
    pr.enable()
    for _ in range(100):
        lexer = Lexer(source)
        lexer_tokens = lexer.tokenize()
    pr.disable()
    
    stats = pstats.Stats(pr)
    stats.sort_stats('cumulative')
    print("词法分析性能前10:")
    stats.print_stats(10)
    
    # 3. 解析性能
    print("\n3. 解析性能分析")
    pr = cProfile.Profile()
    pr.enable()
    for _ in range(50):
        parser = Parser(source)
        ast = parser.parse()
    pr.disable()
    
    stats = pstats.Stats(pr)
    stats.sort_stats('cumulative')
    print("解析性能前10:")
    stats.print_stats(10)
    
    # 4. 代码生成和虚拟机执行性能
    print("\n4. 代码生成和执行性能分析")
    pr = cProfile.Profile()
    pr.enable()
    for _ in range(20):
        parser = Parser(source)
        ast = parser.parse()
        generator = CodeGen()
        chunk = generator.generate(ast)
        vm = VM()
        vm.run(chunk)
    pr.disable()
    
    stats = pstats.Stats(pr)
    stats.sort_stats('cumulative')
    print("代码生成和执行性能前10:")
    stats.print_stats(10)

def profile_individual_operations():
    """分析特定操作性能"""
    print("\n\n特定操作性能分析")
    print("=" * 60)
    
    # 测试分词中的集合查找
    from yanzhi.compiler.pre_tokenizer import PreTokenizer
    import yanzhi.compiler.pre_tokenizer as pre_tokenizer_module
    
    test_text = "定义函数如果否则循环遍历"
    
    # 分析scan_chinese方法
    print("\n分词scan_chinese方法分析:")
    pr = cProfile.Profile()
    pr.enable()
    tokenizer = PreTokenizer(test_text * 10)  # 放大文本
    tokenizer.tokenize()
    pr.disable()
    
    stats = pstats.Stats(pr)
    stats.sort_stats('time')
    stats.print_stats(5)
    
    # 分析虚拟机指令执行
    print("\n虚拟机指令执行分析:")
    
    # 创建简单字节码
    chunk = BytecodeChunk()
    for i in range(1000):
        chunk.emit(chunk.OPCODES['LOAD_NUM'], i % 10)
        chunk.emit(chunk.OPCODES['ADD'])
    
    pr = cProfile.Profile()
    pr.enable()
    vm = VM()
    vm.run(chunk)
    pr.disable()
    
    stats = pstats.Stats(pr)
    stats.sort_stats('time')
    print("虚拟机执行性能前10:")
    stats.print_stats(10)

def measure_memory_usage():
    """测量内存使用"""
    print("\n\n内存使用分析")
    print("=" * 60)
    
    import tracemalloc
    from yanzhi.compiler.pre_tokenizer import tokenize
    from yanzhi.compiler.lexer import Lexer
    from yanzhi.compiler.parser import Parser
    
    source = create_test_code()
    
    # 测量分词内存
    tracemalloc.start()
    tokens = tokenize(source * 5)  # 放大
    current, peak = tracemalloc.get_traced_memory()
    print(f"分词内存使用: 当前={current/1024:.1f}KB, 峰值={peak/1024:.1f}KB")
    tracemalloc.stop()
    
    # 测量AST内存
    tracemalloc.start()
    parser = Parser(source * 3)
    ast = parser.parse()
    current, peak = tracemalloc.get_traced_memory()
    print(f"AST内存使用: 当前={current/1024:.1f}KB, 峰值={peak/1024:.1f}KB")
    tracemalloc.stop()

def identify_hotspots():
    """识别热点函数"""
    print("\n\n热点函数识别")
    print("=" * 60)
    
    source = create_test_code()
    
    pr = cProfile.Profile()
    pr.enable()
    
    # 完整流程
    parser = Parser(source)
    ast = parser.parse()
    generator = CodeGenerator()
    chunk = generator.generate(ast)
    vm = VM()
    vm.run(chunk)
    
    pr.disable()
    
    # 输出热点函数
    stats = pstats.Stats(pr)
    print("总调用次数最多的函数:")
    stats.sort_stats('calls')
    stats.print_stats(10)
    
    print("\n总耗时最多的函数:")
    stats.sort_stats('cumulative')
    stats.print_stats(10)
    
    print("\n自身耗时最多的函数:")
    stats.sort_stats('time')
    stats.print_stats(10)

if __name__ == '__main__':
    print("言知系统性能分析报告")
    print("=" * 60)
    
    profile_full_pipeline()
    profile_individual_operations()
    measure_memory_usage()
    identify_hotspots()
    
    print("\n分析完成！")



