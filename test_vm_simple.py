



#!/usr/bin/env python3
"""
简单虚拟机性能测试
"""
import sys
import os
sys.path.insert(0, os.path.abspath('src'))

import time
from yanzhi.runtime.bytecode import BytecodeChunk, OpCode
from yanzhi.runtime.vm import VM as OriginalVM
from yanzhi.runtime.vm_optimized import OptimizedVM

def create_simple_bytecode() -> BytecodeChunk:
    """创建简单的算术运算字节码"""
    chunk = BytecodeChunk()
    
    # 计算 (1+2)*(3-4)/5 等复杂表达式
    # 多次运算以增加测试负载
    
    # 初始化一些变量
    chunk.emit(OpCode.LOAD_NUM, 1)
    chunk.emit(OpCode.STORE_VAR, 'x')
    chunk.emit(OpCode.LOAD_NUM, 2)
    chunk.emit(OpCode.STORE_VAR, 'y')
    chunk.emit(OpCode.LOAD_NUM, 3)
    chunk.emit(OpCode.STORE_VAR, 'z')
    
    # 执行多次运算
    for i in range(100):  # 100次运算
        chunk.emit(OpCode.LOAD_VAR, 'x')
        chunk.emit(OpCode.LOAD_VAR, 'y')
        chunk.emit(OpCode.ADD)      # x+y
        chunk.emit(OpCode.LOAD_VAR, 'z')
        chunk.emit(OpCode.MUL)      # (x+y)*z
        chunk.emit(OpCode.LOAD_NUM, 2)
        chunk.emit(OpCode.DIV)      # (x+y)*z/2
        chunk.emit(OpCode.STORE_VAR, 'x')  # 存回x
        
        # 更新y和z
        chunk.emit(OpCode.LOAD_VAR, 'y')
        chunk.emit(OpCode.LOAD_NUM, 1)
        chunk.emit(OpCode.ADD)
        chunk.emit(OpCode.STORE_VAR, 'y')
        
        chunk.emit(OpCode.LOAD_VAR, 'z')
        chunk.emit(OpCode.LOAD_NUM, 1)
        chunk.emit(OpCode.SUB)
        chunk.emit(OpCode.STORE_VAR, 'z')
    
    # 返回最终结果
    chunk.emit(OpCode.LOAD_VAR, 'x')
    chunk.emit(OpCode.RETURN)
    
    return chunk

def benchmark():
    print("虚拟机简单性能测试")
    print("=" * 50)
    
    chunk = create_simple_bytecode()
    iterations = 1000
    
    # 原始VM
    print("\n原始VM测试...")
    start = time.perf_counter()
    for _ in range(iterations):
        vm = OriginalVM()
        result1 = vm.run(chunk)
    original_time = time.perf_counter() - start
    
    # 优化VM
    print("优化VM测试...")
    start = time.perf_counter()
    for _ in range(iterations):
        vm = OptimizedVM()
        result2 = vm.run(chunk)
    optimized_time = time.perf_counter() - start
    
    print(f"\n结果:")
    print(f"  迭代次数: {iterations}")
    print(f"  原始VM时间: {original_time:.3f}s")
    print(f"  优化VM时间: {optimized_time:.3f}s")
    print(f"  加速比: {original_time/optimized_time:.2f}x")
    print(f"  原始VM结果: {result1}")
    print(f"  优化VM结果: {result2}")
    
    if result1 == result2:
        print("  结果验证: OK 一致")
    else:
        print("  结果验证: 不一致")

if __name__ == '__main__':
    benchmark()



