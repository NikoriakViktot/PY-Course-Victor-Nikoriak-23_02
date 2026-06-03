"""
metrics.py — Timing, operation counting, and memory protection.

Public API
----------
  time_measure(func, *args)       → TimedResult
  get_memory_usage_gb()           → float
  check_memory(limit_gb, ctx)     → None  (raises MemoryGuardError)
  memory_guard(limit_gb, ctx)     → decorator
  OperationCounter                → manual op counting
  MemoryGuardError                → rich MemoryError subclass
  BenchmarkPoint / benchmark_series
"""
from __future__ import annotations

import functools
import time
from dataclasses import dataclass
from typing import Any, Callable, TypeVar

import psutil

T = TypeVar("T")

# One process handle, shared across the module
_PROCESS = psutil.Process()

# Approximate pandas row size for 4 columns (str + float64 + int32 + int32)
BYTES_PER_ROW: int = 96


# ===========================================================================
# TimedResult
# ===========================================================================

@dataclass
class TimedResult:
    """Return value of time_measure(): result + wall-clock time + op count."""
    value: Any
    elapsed_ms: float
    op_count: int = 0

    @property
    def elapsed_us(self) -> float:
        return self.elapsed_ms * 1_000

    def __str__(self) -> str:
        return (
            f"result={self.value!r}  "
            f"time={self.elapsed_ms:.4f} ms  "
            f"ops={self.op_count:,}"
        )


# ===========================================================================
# time_measure
# ===========================================================================

def time_measure(func: Callable[..., T], *args: Any, **kwargs: Any) -> TimedResult:
    """
    Execute *func* and return a TimedResult.

    If the function returns (value, op_count: int), the pair is unpacked
    automatically so that .value is the actual result and .op_count is the
    operation counter.
    """
    start = time.perf_counter()
    raw   = func(*args, **kwargs)
    elapsed_ms = (time.perf_counter() - start) * 1_000

    op_count = 0
    if isinstance(raw, tuple) and len(raw) == 2 and isinstance(raw[1], int):
        value, op_count = raw
    else:
        value = raw

    return TimedResult(value=value, elapsed_ms=elapsed_ms, op_count=op_count)


# ===========================================================================
# Memory utilities
# ===========================================================================

def get_memory_usage_gb() -> float:
    """Return current RSS (resident set size) of this process in gigabytes."""
    return _PROCESS.memory_info().rss / (1_024 ** 3)


def estimate_dataframe_gb(n_rows: int, bytes_per_row: int = BYTES_PER_ROW) -> float:
    """Estimate RAM for a pandas DataFrame with *n_rows* rows."""
    return n_rows * bytes_per_row / (1_024 ** 3)


class MemoryGuardError(MemoryError):
    """
    Raised when a memory limit is breached.

    Attributes
    ----------
    current_gb : float  — measured RSS at the moment of the error
    limit_gb   : float  — the configured limit
    context    : str    — which function/operation triggered the check
    delta_gb   : float  — RAM increase since the operation started (may be 0)
    """

    def __init__(
        self,
        current_gb: float,
        limit_gb: float,
        context: str = "",
        delta_gb: float = 0.0,
    ) -> None:
        self.current_gb = current_gb
        self.limit_gb   = limit_gb
        self.context    = context
        self.delta_gb   = delta_gb
        where = f" in «{context}»" if context else ""
        super().__init__(
            f"RAM limit exceeded{where}: "
            f"{current_gb:.2f} GB > {limit_gb:.1f} GB limit  "
            f"(+{delta_gb:+.2f} GB during this operation)"
        )


def check_memory(limit_gb: float, context: str = "") -> None:
    """
    Immediately raise MemoryGuardError if current process RSS > limit_gb.

    Call this at any checkpoint inside a heavy operation.
    """
    current = get_memory_usage_gb()
    if current > limit_gb:
        raise MemoryGuardError(current_gb=current, limit_gb=limit_gb,
                               context=context, delta_gb=0.0)


def memory_guard(limit_gb: float, context: str = "") -> Callable:
    """
    Decorator factory that wraps a function with before/after RAM checks.

    Usage
    -----
    @memory_guard(limit_gb=8.0, context="sample_from_view")
    def sample_from_view(con, n): ...

    Or at call-time (limit not known until runtime):
        guarded = memory_guard(limit_gb)(some_func)
        result  = guarded(*args)
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            before_gb = get_memory_usage_gb()
            result    = func(*args, **kwargs)
            after_gb  = get_memory_usage_gb()
            if after_gb > limit_gb:
                raise MemoryGuardError(
                    current_gb=after_gb,
                    limit_gb=limit_gb,
                    context=context or func.__name__,
                    delta_gb=after_gb - before_gb,
                )
            return result
        return wrapper
    return decorator


# ===========================================================================
# OperationCounter
# ===========================================================================

class OperationCounter:
    """Mutable counter for tracking algorithm steps without polluting return types."""

    def __init__(self) -> None:
        self.count: int = 0

    def inc(self, n: int = 1) -> None:
        self.count += n

    def reset(self) -> None:
        self.count = 0

    def __repr__(self) -> str:
        return f"OperationCounter(count={self.count:,})"


# ===========================================================================
# Benchmark series (scaling chart helper)
# ===========================================================================

@dataclass
class BenchmarkPoint:
    n: int
    elapsed_ms: float
    op_count: int = 0


def benchmark_series(
    func: Callable,
    sizes: list[int],
    build_args_fn: Callable[[int], tuple],
    repeats: int = 3,
) -> list[BenchmarkPoint]:
    """
    Run *func* at each size in *sizes* and return the best-of-*repeats* time.
    *build_args_fn* receives n and must return the args tuple for func.
    """
    points: list[BenchmarkPoint] = []
    for n in sizes:
        args  = build_args_fn(n)
        times = [time_measure(func, *args).elapsed_ms for _ in range(repeats)]
        points.append(BenchmarkPoint(n=n, elapsed_ms=min(times)))
    return points
