



#!/usr/bin/env python3
"""
虚拟机性能测试
"""
import sys
import os
sys.path.insert(0, os.path.abspath('src'))

import time
from yanzhi.runtime.bytecode import BytecodeChunk, OpCode
from yanzhi.runtime.vm import VM as OriginalVM
from yanzhi.runtime.vm_optimized import run_optimized, OptimizedVM

def create_fibonacci_bytecode(n: int) -> BytecodeChunk:
    """创建计算斐波那契数列的字节码"""
    chunk = BytecodeChunk()
    
    # 简单实现：计算fib(n) = fib(n-1) + fib(n-2)
    # 这里我们创建一个循环计算而不是递归
    
    # 初始化: a=0, b=1
    chunk.emit(OpCode.LOAD_NUM, 0)  # a = 0
    chunk.emit(OpCode.STORE_VAR, 'a')
    chunk.emit(OpCode.LOAD_NUM, 1)  # b = 1
    chunk.emit(OpCode.STORE_VAR, 'b')
    chunk.emit(OpCode.LOAD_NUM, 0)  # i = 0
    chunk.emit(OpCode.STORE_VAR, 'i')
    
    # 循环开始位置
    loop_start = len(chunk.instructions)
    
    # 条件: i < n
    chunk.emit(OpCode.LOAD_VAR, 'i')
    chunk.emit(OpCode.LOAD_NUM, n)
    chunk.emit(OpCode.LT)
    
    # 如果条件为假，跳转到循环结束
    loop_end_label = len(chunk.instructions) + 3  # 估算
    chunk.emit(OpCode.JUMP_IF_FALSE, loop_end_label)
    
    # 循环体: a, b = b, a + b
    chunk.emit(OpCode.LOAD_VAR, 'a')
    chunk.emit(OpCode.LOAD_VAR, 'b')
    chunk.emit(OpCode.ADD)
    chunk.emit(OpCode.STORE_VAR, 'temp')
    chunk.emit(OpCode.LOAD_VAR, 'b')
    chunk.emit(OpCode.STORE_VAR, 'a')
    chunk.emit(OpCode.LOAD_VAR, 'temp')
    chunk.emit(OpCode.STORE_VAR, 'b')
    
    # i += 1
    chunk.emit(OpCode.LOAD_VAR, 'i')
    chunk.emit(OpCode.LOAD_NUM, 1)
    chunk.emit(OpCode.ADD)
    chunk.emit(OpCode.STORE_VAR, 'i')
    
    # 跳回循环开始
    chunk.emit(OpCode.JUMP, loop_start)
    
    # 循环结束位置
    loop_end = len(chunk.instructions)
    # 修正跳转地址
    chunk.instructions[loop_start + 2].operand = loop_end
    
    # 返回结果a
    chunk.emit(OpCode.LOAD_VAR, 'a')
    chunk.emit(OpCode.RETURN)
    
    return chunk

def benchmark_vm():
    print("虚拟机性能测试")
    print("=" * 50)
    
    # 创建测试字节码
    test_sizes = [10, 50, 100, 200]
    
    for n in test_sizes:
        print(f"\n计算斐波那契数列第{n}项")
        chunk = create_fibonacci_bytecode(n)
        
        # 原始VM
        vm1 = OriginalVM()
        start = time.perf_counter()
        for _ in range(100):
            result1 = vm1.run(chunk)
        original_time = time.perf_counter() - start
        
        # 优化VM
        start = time.perf_counter()
        for _ in range(100):
            vm2 = OptimizedVM()
            result2 = vm2.run(chunk)
        optimized_time = time.perf_counter() - start
        
        print(f"  原始VM: {original_time:.3f}s")
        print(f"  优化VM: {optimized_time:.3f}s")
        print(f"  加速比: {original_time/optimized_time:.2f}x")
        
        # 验证结果正确性
        if result1 == result2:
            print(f"  结果验证: ✓ (fib({n}) = {result1})")
        else:
            print(f"  结果验证: ✗ (原始: {result1}, 优化: {result2})")
    
    # 简单算术运算测试
    print("\n简单算术运算测试")
    chunk = BytecodeChunk()
    # 计算 1+2+3+...+100
    chunk.emit(OpCode.LOAD_NUM, 0)  # sum = 0
    chunk.emit(OpCode.STORE_VAR, 'sum')
    chunk.emit(OpCode.LOAD_NUM, 1)  # i = 1
    chunk.emit(OpCode.STORE_VAR, 'i')
    
    loop_start = len(chunk.instructions)
    chunk.emit(OpCode.LOAD_VAR, 'i')
    chunk.emit(OpCode.LOAD_NUM, 100)
    chunk.emit(OpCode.LE)
    loop_end_label = len(chunk.instructions) + 3
    chunk.emit(OpCode.JUMP_IF_FALSE, loop_end_label)
    
    chunk.emit(OpCode.LOAD_VAR, 'sum')
    chunk.emit(OpCode.LOAD_VAR, 'i')
    chunk.emit(OpCode.ADD)
    chunk.emit(OpCode.STORE_VAR, 'sum')
    
    chunk.emit(OpCode.LOAD_VAR, 'i')
    chunk.emit(OpCode.LOAD_NUM, 1)
    chunk.emit(OpCode.ADD)
    chunk.emit(OpCode.STORE_VAR, 'i')
    
    chunk.emit(OpCode.JUMP, loop_start)
    
    loop_end = len(chunk.instructions)
    chunk.instructions[loop_start + 2].operand = loop_end
    
    chunk.emit(OpCode.LOAD_VAR, 'sum')
    chunk.emit(OpCode.PRINT)
    chunk.emit(OpCode.RETURN)
    
    iterations = 1000
    
    # 原始VM
    vm1 = OriginalVM()
    start = time.perf_counter()
    for _ in range(iterations):
        vm1.run(chunk)
    original_time = time.perf_counter() - start
    
    # 优化VM
    start = time.perf_counter()
    for _ in range(iterations):
        vm2 = OptimizedVM()
        vm2.run(chunk)
    optimized_time = time.perf_counter() - start
    
    print(f"  迭代次数: {iterations}")
    print(f"  原始VM: {original_time:.3f}s")
    print(f"  优化VM: {optimized_time:.3f}s")
    print(f"  加速比: {original_time/optimized_time:.2f}x")

if __name__ == '__main__':
    benchmark_vm()



