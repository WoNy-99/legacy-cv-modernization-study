"""New CPU timing example, not historical CV code or a GPU benchmark.

No network, input assets, environment dump, or output files are used.
The callable API is a template: real workloads need their own completion hook.
"""

import argparse
import json
import math
import statistics
import time


def measure(step, synchronize, *, warmup=3, repeats=20, clock=time.perf_counter):
    """Time completed calls, excluding warmup; propagate workload errors.

    synchronize must wait for pending work, or be a no-op for synchronous CPU
    work. The caller defines and documents what one step includes.
    """
    if type(warmup) is not int or type(repeats) is not int:
        raise ValueError("warmup and repeats must be integers")
    if warmup < 0 or repeats < 1:
        raise ValueError("warmup must be nonnegative and repeats positive")
    for _ in range(warmup):
        step()
        synchronize()
    values = []
    for _ in range(repeats):
        synchronize()
        start = clock()
        step()
        synchronize()
        elapsed = (clock() - start) * 1000
        if not math.isfinite(elapsed) or elapsed < 0:
            raise ValueError("invalid elapsed time")
        values.append(elapsed)
    ordered = sorted(values)
    return {
        "warmup_steps": warmup,
        "measured_steps": repeats,
        "unit": "milliseconds_per_completed_call",
        "mean": statistics.mean(values),
        "median": statistics.median(values),
        "p95_nearest_rank": ordered[math.ceil(0.95 * repeats) - 1],
        "minimum": ordered[0],
        "maximum": ordered[-1],
    }


def demo_step():
    """Synchronous toy CPU arithmetic; no CV or training semantics."""
    return sum((i * i) % 97 for i in range(10000))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--demo", action="store_true", help="time toy CPU work")
    parser.add_argument("--warmup", type=int, default=3)
    parser.add_argument("--repeats", type=int, default=20)
    args = parser.parse_args(argv)
    if not args.demo:
        parser.error("No CV workload is implemented. Use --demo for CPU toy work only.")
    if not 0 <= args.warmup <= 1000 or not 1 <= args.repeats <= 10000:
        parser.error("warmup must be 0..1000 and repeats 1..10000")
    result = measure(demo_step, lambda: None, warmup=args.warmup, repeats=args.repeats)
    print(json.dumps({
        "workload": "cpu_arithmetic_demo_only",
        "historical_measurement": False,
        "cv_performance_claim": False,
        "gpu_measured": False,
        "timing": result,
    }, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
