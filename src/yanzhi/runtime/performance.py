# -*- coding: utf-8 -*-
"""
性能优化模块

提供编译和运行时的性能优化功能。
"""

import time
import functools
from typing import Any, Callable, Dict, List
import sys


# ==================== 编译性能优化 ====================

class CompileCache:
    """编译缓存，避免重复编译"""
    
    def __init__(self, max_size=1000):
        self.cache: Dict[str, Any] = {}
        self.max_size = max_size
        self.hits = 0
        self.misses = 0
    
    def get(self, source: str) -> Any:
        """获取缓存的编译结果"""
        if source in self.cache:
            self.hits += 1
            return self.cache[source]
        self.misses += 1
        return None
    
    def set(self, source: str, result: Any):
        """设置缓存"""
        if len(self.cache) >= self.max_size:
            # 简单的LRU：删除最早的项
            oldest = next(iter(self.cache))
            del self.cache[oldest]
        self.cache[source] = result
    
    def clear(self):
        """清空缓存"""
        self.cache.clear()
        self.hits = 0
        self.misses = 0
    
    def stats(self) -> Dict[str, int]:
        """获取缓存统计"""
        return {
            'size': len(self.cache),
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': self.hits / (self.hits + self.misses) if (self.hits + self.misses) > 0 else 0
        }


# 全局编译缓存
compile_cache = CompileCache()


# ==================== 运行时性能优化 ====================

class InlineCache:
    """内联缓存，优化属性访问和方法调用"""
    
    def __init__(self):
        self.caches: Dict[str, Any] = {}
    
    def get(self, key: str) -> Any:
        """获取缓存值"""
        return self.caches.get(key)
    
    def set(self, key: str, value: Any):
        """设置缓存值"""
        self.caches[key] = value


# ==================== 性能分析 ====================

class Profiler:
    """性能分析器"""
    
    def __init__(self):
        self.timings: Dict[str, List[float]] = {}
        self.counts: Dict[str, int] = {}
    
    def time(self, name: str):
        """计时上下文管理器"""
        return self._Timer(self, name)
    
    class _Timer:
        def __init__(self, profiler, name):
            self.profiler = profiler
            self.name = name
            self.start = 0
        
        def __enter__(self):
            self.start = time.perf_counter()
            return self
        
        def __exit__(self, *args):
            elapsed = time.perf_counter() - self.start
            if self.name not in self.profiler.timings:
                self.profiler.timings[self.name] = []
                self.profiler.counts[self.name] = 0
            self.profiler.timings[self.name].append(elapsed)
            self.profiler.counts[self.name] += 1
    
    def report(self) -> str:
        """生成性能报告"""
        lines = ["性能分析报告", "=" * 70]
        
        for name in sorted(self.timings.keys()):
            times = self.timings[name]
            count = self.counts[name]
            total = sum(times)
            avg = total / count
            min_time = min(times)
            max_time = max(times)
            
            lines.append(f"\n{name}:")
            lines.append(f"  调用次数: {count}")
            lines.append(f"  总时间: {total:.6f}s")
            lines.append(f"  平均时间: {avg:.6f}s")
            lines.append(f"  最小时间: {min_time:.6f}s")
            lines.append(f"  最大时间: {max_time:.6f}s")
        
        return "\n".join(lines)


# 全局性能分析器
profiler = Profiler()


# ==================== 优化装饰器 ====================

def memoize(func: Callable) -> Callable:
    """记忆化装饰器"""
    cache = {}
    
    @functools.wraps(func)
    def wrapper(*args):
        # 将参数转换为可哈希的键
        key = str(args)
        if key in cache:
            return cache[key]
        result = func(*args)
        cache[key] = result
        return result
    
    return wrapper


def profile(name: str) -> Callable:
    """性能分析装饰器"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with profiler.time(name):
                return func(*args, **kwargs)
        return wrapper
    return decorator


def optimize_tail_call(func: Callable) -> Callable:
    """尾调用优化装饰器"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        while True:
            result = func(*args, **kwargs)
            if not isinstance(result, tuple) or result[0] != '__tail_call__':
                return result
            args, kwargs = result[1], result[2]
    return wrapper


# ==================== 内存优化 ====================

class ObjectPool:
    """对象池，减少对象创建开销"""
    
    def __init__(self, factory: Callable, max_size: int = 100):
        self.factory = factory
        self.max_size = max_size
        self.pool: List[Any] = []
    
    def acquire(self) -> Any:
        """获取对象"""
        if self.pool:
            return self.pool.pop()
        return self.factory()
    
    def release(self, obj: Any):
        """释放对象"""
        if len(self.pool) < self.max_size:
            self.pool.append(obj)


class StringIntern:
    """字符串驻留，减少字符串内存占用"""
    
    def __init__(self):
        self.strings: Dict[str, str] = {}
    
    def intern(self, s: str) -> str:
        """驻留字符串"""
        if s in self.strings:
            return self.strings[s]
        self.strings[s] = s
        return s


# 全局字符串驻留
string_intern = StringIntern()


# ==================== JIT编译提示 ====================

def jit_hint(func: Callable) -> Callable:
    """JIT编译提示装饰器（预留接口）"""
    # 当前版本只是标记，未来可以实现真正的JIT
    func._jit_hint = True
    return func


# ==================== 性能测试 ====================

def benchmark(func: Callable, *args, iterations: int = 1000) -> Dict[str, float]:
    """性能基准测试"""
    # 预热
    for _ in range(10):
        func(*args)
    
    # 正式测试
    start = time.perf_counter()
    for _ in range(iterations):
        func(*args)
    elapsed = time.perf_counter() - start
    
    return {
        'iterations': iterations,
        'total_time': elapsed,
        'avg_time': elapsed / iterations,
        'ops_per_sec': iterations / elapsed
    }


# ==================== 导出 ====================

if __name__ == '__main__':
    print("性能优化模块测试")
    print("=" * 70)
    
    # 测试记忆化
    @memoize
    def fib(n):
        if n <= 1:
            return n
        return fib(n-1) + fib(n-2)
    
    print("测试记忆化斐波那契:")
    start = time.perf_counter()
    result = fib(30)
    elapsed = time.perf_counter() - start
    print(f"  fib(30) = {result}, 耗时: {elapsed:.6f}s")
    
    # 测试性能分析
    @profile("测试函数")
    def test_func(n):
        return sum(range(n))
    
    test_func(1000)
    print("\n" + profiler.report())
    
    # 测试基准测试
    print("\n基准测试:")
    stats = benchmark(lambda: sum(range(1000)), iterations=10000)
    print(f"  操作/秒: {stats['ops_per_sec']:.0f}")
    
    print("\n[OK] 性能优化模块测试完成")
