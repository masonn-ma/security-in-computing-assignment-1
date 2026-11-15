import time, psutil
def measure(fn):
    p = psutil.Process()
    baseline = p.memory_info().rss
    start = time.perf_counter_ns()
    result = fn()
    elapsed = time.perf_counter_ns() - start
    peak = p.memory_info().rss
    return result, elapsed, baseline, peak
