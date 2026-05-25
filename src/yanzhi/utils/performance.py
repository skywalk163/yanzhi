"""
知行语言性能优化模块
提供缓存、记忆化、惰性求值等优化功能
"""

from functools import lru_cache, wraps
from typing import Any, Callable, Dict, List
import time


# 1. 记忆化装饰器
def memoize(func: Callable) -> Callable:
    """
    记忆化装饰器，缓存函数结果
    适用于纯函数（无副作用）
    """
    cache: Dict = {}
    
    @wraps(func)
    def wrapper(*args):
        # 将参数转换为可哈希的键
        key = str(args)
        
        if key in cache:
            return cache[key]
        
        result = func(*args)
        cache[key] = result
        return result
    
    wrapper.cache = cache
    wrapper.clear_cache = lambda: cache.clear()
    return wrapper


# 2. 限大小缓存装饰器
def cached(maxsize: int = 128):
    """
    限大小缓存装饰器
    使用LRU策略
    """
    return lru_cache(maxsize=maxsize)


# 3. 惰性求值
class Lazy:
    """惰性求值包装器"""
    
    def __init__(self, func: Callable, *args, **kwargs):
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self._value = None
        self._evaluated = False
    
    def evaluate(self) -> Any:
        """求值"""
        if not self._evaluated:
            self._value = self.func(*self.args, **self.kwargs)
            self._evaluated = True
        return self._value
    
    def __repr__(self):
        if self._evaluated:
            return f"Lazy({self._value})"
        return f"Lazy(<unevaluated>)"


# 4. 惰性列表
class LazyList:
    """惰性列表，按需计算"""
    
    def __init__(self, func: Callable, length: int = None):
        self.func = func
        self.length = length
        self._cache: Dict[int, Any] = {}
    
    def __getitem__(self, index: int) -> Any:
        if index not in self._cache:
            self._cache[index] = self.func(index)
        return self._cache[index]
    
    def __len__(self) -> int:
        if self.length is None:
            raise TypeError("无限惰性列表没有长度")
        return self.length
    
    def __iter__(self):
        if self.length is None:
            index = 0
            while True:
                yield self[index]
                index += 1
        else:
            for i in range(self.length):
                yield self[i]


# 5. 性能计时器
class Timer:
    """性能计时器"""
    
    def __init__(self, name: str = ""):
        self.name = name
        self.start_time = None
        self.end_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, *args):
        self.end_time = time.time()
        if self.name:
            print(f"{self.name}: {self.elapsed:.4f}秒")
    
    @property
    def elapsed(self) -> float:
        """经过时间"""
        if self.start_time is None:
            return 0
        if self.end_time is None:
            return time.time() - self.start_time
        return self.end_time - self.start_time


# 6. 性能分析器
class Profiler:
    """性能分析器"""
    
    def __init__(self):
        self.records: Dict[str, List[float]] = {}
    
    def record(self, name: str, time: float):
        """记录时间"""
        if name not in self.records:
            self.records[name] = []
        self.records[name].append(time)
    
    def profile(self, name: str):
        """性能分析装饰器"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                with Timer() as timer:
                    result = func(*args, **kwargs)
                self.record(name, timer.elapsed)
                return result
            return wrapper
        return decorator
    
    def report(self) -> str:
        """生成报告"""
        lines = ["性能分析报告:", "-" * 50]
        
        for name, times in self.records.items():
            total = sum(times)
            count = len(times)
            avg = total / count if count > 0 else 0
            lines.append(f"{name}:")
            lines.append(f"  调用次数: {count}")
            lines.append(f"  总时间: {total:.4f}秒")
            lines.append(f"  平均时间: {avg:.4f}秒")
        
        return '\n'.join(lines)


# 7. 优化的列表操作
def fast_map(func: Callable, lst: List) -> List:
    """优化的map操作"""
    return [func(x) for x in lst]


def fast_filter(func: Callable, lst: List) -> List:
    """优化的filter操作"""
    return [x for x in lst if func(x)]


def fast_reduce(func: Callable, lst: List, initial: Any = None) -> Any:
    """优化的reduce操作"""
    if initial is None:
        result = lst[0]
        start = 1
    else:
        result = initial
        start = 0
    
    for i in range(start, len(lst)):
        result = func(result, lst[i])
    
    return result


# 8. 批处理优化
def batch_process(func: Callable, items: List, batch_size: int = 100) -> List:
    """批处理优化"""
    results = []
    
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        results.extend(func(batch))
    
    return results


# 9. 并行处理（简化版）
def parallel_map(func: Callable, lst: List, workers: int = 4) -> List:
    """
    并行map（简化实现）
    实际应用中应使用multiprocessing
    """
    # 这里简化实现，实际应使用多进程
    return fast_map(func, lst)


# 10. 缓存预热
def warmup_cache(func: Callable, warmup_args: List):
    """缓存预热"""
    for args in warmup_args:
        if isinstance(args, tuple):
            func(*args)
        else:
            func(args)


# 使用示例
if __name__ == '__main__':
    # 记忆化示例
    @memoize
    def fibonacci(n):
        if n <= 1:
            return n
        return fibonacci(n - 1) + fibonacci(n - 2)
    
    print("斐波那契数列:")
    with Timer("计算fib(30)"):
        print(f"fib(30) = {fibonacci(30)}")
    
    # 性能分析示例
    profiler = Profiler()
    
    @profiler.profile("测试函数")
    def test_func(n):
        return sum(range(n))
    
    for i in range(10):
        test_func(10000)
    
    print("\n" + profiler.report())
