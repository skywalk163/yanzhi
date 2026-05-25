"""
知行语言性能优化
提供缓存和优化功能
"""

from typing import Dict, Any, Optional
from functools import lru_cache
import hashlib


class CompileCache:
    """编译缓存"""
    
    def __init__(self, max_size: int = 100):
        self.max_size = max_size
        self.cache: Dict[str, Any] = {}
        self.hits = 0
        self.misses = 0
    
    def get_key(self, source: str) -> str:
        """生成缓存键"""
        return hashlib.md5(source.encode('utf-8')).hexdigest()
    
    def get(self, source: str) -> Optional[Any]:
        """获取缓存"""
        key = self.get_key(source)
        if key in self.cache:
            self.hits += 1
            return self.cache[key]
        self.misses += 1
        return None
    
    def set(self, source: str, result: Any):
        """设置缓存"""
        if len(self.cache) >= self.max_size:
            # 移除最旧的缓存
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]
        
        key = self.get_key(source)
        self.cache[key] = result
    
    def clear(self):
        """清空缓存"""
        self.cache.clear()
        self.hits = 0
        self.misses = 0
    
    def stats(self) -> Dict[str, int]:
        """获取缓存统计"""
        total = self.hits + self.misses
        hit_rate = self.hits / total if total > 0 else 0
        return {
            'size': len(self.cache),
            'max_size': self.max_size,
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': hit_rate
        }


# 全局编译缓存
_compile_cache = CompileCache()


def get_compile_cache() -> CompileCache:
    """获取全局编译缓存"""
    return _compile_cache


class Optimizer:
    """代码优化器"""
    
    def __init__(self):
        self.optimizations = []
    
    def optimize(self, code: str) -> str:
        """优化代码"""
        # 1. 移除多余空行
        code = self.remove_empty_lines(code)
        
        # 2. 移除多余空格
        code = self.remove_extra_spaces(code)
        
        # 3. 合并连续赋值
        code = self.merge_assignments(code)
        
        return code
    
    def remove_empty_lines(self, code: str) -> str:
        """移除多余空行"""
        lines = code.split('\n')
        result = []
        prev_empty = False
        
        for line in lines:
            is_empty = line.strip() == ''
            
            # 只保留单个空行
            if is_empty:
                if not prev_empty:
                    result.append(line)
                prev_empty = True
            else:
                result.append(line)
                prev_empty = False
        
        return '\n'.join(result)
    
    def remove_extra_spaces(self, code: str) -> str:
        """移除多余空格"""
        lines = code.split('\n')
        result = []
        
        for line in lines:
            # 移除行尾空格
            line = line.rstrip()
            result.append(line)
        
        return '\n'.join(result)
    
    def merge_assignments(self, code: str) -> str:
        """合并连续赋值（简单优化）"""
        # 这里可以实现更复杂的优化
        return code


# 全局优化器
_optimizer = Optimizer()


def get_optimizer() -> Optimizer:
    """获取全局优化器"""
    return _optimizer


# 性能分析工具
class Profiler:
    """性能分析器"""
    
    def __init__(self):
        self.timings: Dict[str, list] = {}
        self.enabled = False
    
    def start(self, name: str):
        """开始计时"""
        if not self.enabled:
            return
        
        import time
        if name not in self.timings:
            self.timings[name] = []
        self.timings[name].append(('start', time.time()))
    
    def end(self, name: str):
        """结束计时"""
        if not self.enabled:
            return
        
        import time
        if name in self.timings and self.timings[name]:
            start_time = self.timings[name][-1][1]
            elapsed = time.time() - start_time
            self.timings[name][-1] = (elapsed, start_time)
    
    def report(self) -> str:
        """生成报告"""
        if not self.timings:
            return "无性能数据"
        
        lines = ["性能分析报告:", "=" * 60]
        
        for name, timings in self.timings.items():
            times = [t[0] for t in timings if isinstance(t[0], float)]
            if times:
                total = sum(times)
                avg = total / len(times)
                lines.append(f"{name}:")
                lines.append(f"  总时间: {total:.4f}秒")
                lines.append(f"  平均时间: {avg:.4f}秒")
                lines.append(f"  调用次数: {len(times)}")
        
        lines.append("=" * 60)
        return '\n'.join(lines)
    
    def clear(self):
        """清空数据"""
        self.timings.clear()


# 全局性能分析器
_profiler = Profiler()


def get_profiler() -> Profiler:
    """获取全局性能分析器"""
    return _profiler
