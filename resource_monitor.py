# -*- coding: utf-8 -*-
"""
Resource Monitor: pengukuran RAM (peak, before/after), CPU, dan execution time.
Mendukung konteks (context manager) untuk mengukur blok kode.
"""

import os
import time
import tracemalloc
from typing import Dict, Any, Optional, Callable
from contextlib import contextmanager

try:
    import psutil
except ImportError:
    psutil = None


def get_current_memory_mb() -> float:
    """RAM usage proses saat ini (RSS) dalam MB."""
    if psutil is not None:
        proc = psutil.Process(os.getpid())
        return proc.memory_info().rss / (1024 * 1024)
    # Fallback: tracemalloc
    try:
        current, peak = tracemalloc.get_traced_memory()
        return current / (1024 * 1024)
    except Exception:
        return 0.0


def get_peak_memory_mb() -> float:
    """Peak memory (jika tracemalloc aktif) atau estimasi dari psutil."""
    if psutil is not None:
        proc = psutil.Process(os.getpid())
        return proc.memory_info().rss / (1024 * 1024)  # psutil tidak track peak per-process mudah
    try:
        current, peak = tracemalloc.get_traced_memory()
        return peak / (1024 * 1024)
    except Exception:
        return 0.0


def get_cpu_percent() -> float:
    """CPU usage proses saat ini (%)."""
    if psutil is not None:
        return psutil.Process(os.getpid()).cpu_percent(interval=0.1)
    return 0.0


@contextmanager
def measure_block(use_tracemalloc: bool = True):
    """
    Context manager: ukur memory before/after, peak, dan elapsed time.
    Returns dict dengan keys: memory_before_mb, memory_after_mb, peak_mb, time_sec, cpu_percent (optional).
    """
    if use_tracemalloc:
        tracemalloc.start()
    mem_before = get_current_memory_mb()
    t0 = time.perf_counter()
    cpu_before = get_cpu_percent() if psutil else 0.0

    result: Dict[str, Any] = {
        "memory_before_mb": mem_before,
        "memory_after_mb": 0.0,
        "peak_memory_mb": 0.0,
        "time_sec": 0.0,
        "cpu_percent": 0.0,
    }

    try:
        yield result
    finally:
        result["time_sec"] = time.perf_counter() - t0
        result["memory_after_mb"] = get_current_memory_mb()
        if use_tracemalloc:
            try:
                current, peak = tracemalloc.get_traced_memory()
                result["peak_memory_mb"] = peak / (1024 * 1024)
            except Exception:
                result["peak_memory_mb"] = result["memory_after_mb"]
            tracemalloc.stop()
        else:
            result["peak_memory_mb"] = max(result["memory_before_mb"], result["memory_after_mb"])
        if psutil:
            result["cpu_percent"] = get_cpu_percent()


def run_and_measure(
    fn: Callable[[], Any],
    use_tracemalloc: bool = True,
) -> Dict[str, Any]:
    """
    Jalankan fn() dan ukur resource. Return dict dengan memory_before_mb, memory_after_mb,
    peak_memory_mb, time_sec, cpu_percent.
    """
    with measure_block(use_tracemalloc=use_tracemalloc) as res:
        fn()
    return res


def format_metrics(metrics: Dict[str, Any]) -> Dict[str, Any]:
    """Format metrik untuk log/JSON (nilai numerik bulat/float konsisten)."""
    return {
        "memory_before_mb": round(metrics.get("memory_before_mb", 0), 4),
        "memory_after_mb": round(metrics.get("memory_after_mb", 0), 4),
        "peak_memory_mb": round(metrics.get("peak_memory_mb", 0), 4),
        "time_sec": round(metrics.get("time_sec", 0), 4),
        "cpu_percent": round(metrics.get("cpu_percent", 0), 2),
    }
