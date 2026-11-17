import threading
import time

import psutil


def measure(fn):
    p = psutil.Process()
    baseline = p.memory_info().rss
    peak = baseline
    stop = threading.Event()

    def sample_rss():
        nonlocal peak
        while not stop.is_set():
            peak = max(peak, p.memory_info().rss)
            stop.wait(0.001)

    sampler = threading.Thread(target=sample_rss, daemon=True)
    sampler.start()
    start = time.perf_counter_ns()
    try:
        result = fn()
    finally:
        elapsed = time.perf_counter_ns() - start
        stop.set()
        sampler.join()
        peak = max(peak, p.memory_info().rss)
    return result, elapsed, baseline, peak
