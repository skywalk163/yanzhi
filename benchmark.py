"""
言知性能基准测试
测试字节码 VM 各功能模块的性能基线
"""
import sys
import os
import time
import statistics

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from yanzhi.cli import REPL


BENCHMARKS = [
    ("列表创建", "列表 1 2 3 4 5 6 7 8 9 10。"),
    ("算术运算", "相加 1 2 3 4 5 6 7 8 9 10。"),
    ("条件判断", "如果 5 大于 3 那么 1 否则 0。"),
    ("管道链(映射+过滤+归约)", (
        "列表 1 2 3 4 5 6 7 8 9 10，"
        "映射 相乘 2，"
        "过滤 大于 10，"
        "归约 相加 0。"
    )),
    ("管道链(映射+打印)", "列表 0 1 2 3 4 5 6 7 8 9，映射 相乘 2。"),
    ("大列表映射", "列表 0 1 2 3 4 5 6 7 8 9，映射 相乘 2，映射 相加 1，映射 字。"),
    ("函数调用", "定义 平方=函数 n 相乘 n n。平方 5。"),
    ("字符串操作", (
        '定义 result="a"。'
        '赋值 result=相加 result "b"。'
        '赋值 result=相加 result "c"。'
        'result。'
    )),
]


def benchmark(name: str, source: str, iterations: int = 5, warmup: int = 2):
    """运行基准测试"""
    r = REPL()

    # 预热
    for _ in range(warmup):
        try:
            r.execute(source)
        except Exception:
            pass

    # 正式测试
    times = []
    last_result = None
    for i in range(iterations):
        start = time.perf_counter()
        try:
            result = r.execute(source)
            elapsed = time.perf_counter() - start
            times.append(elapsed)
            last_result = result
        except Exception as e:
            print(f"  [{name}] 执行失败: {e}")
            return

    if not times:
        return

    avg = statistics.mean(times)
    med = statistics.median(times)
    _min = min(times)
    _max = max(times)
    std = statistics.stdev(times) if len(times) > 1 else 0

    # 格式化输出
    label = f"[{name}]"
    print(f"  {label:<30s} 平均={avg*1000:6.2f}ms  中位={med*1000:6.2f}ms   "
          f"最快={_min*1000:6.2f}ms  最慢={_max*1000:6.2f}ms  "
          f"结果={last_result}")


if __name__ == '__main__':
    print("=" * 70)
    print("  言知 字节码 VM 性能基准测试")
    print(f"  Python {sys.version.split()[0]}")
    print(f"  预热={2}次  迭代={5}次")
    print("=" * 70)

    for name, source in BENCHMARKS:
        benchmark(name, source)

    print(f"\n{'='*70}")
    print("  基准测试完成")
    print(f"{'='*70}")
