import random
import time
import statistics

from core.dp_optimizer import optimize_trip_dp as original_dp
from core.dp_optimizer_optimized import optimize_trip_dp as optimized_dp
from core.held_karp_optimizer import optimize_trip_held_karp

def generate_problem(n, constrained, seed):
    rng = random.Random(seed)
    size = n + 1

    matrix = [
        [0 if i == j else rng.randint(5, 30)
         for j in range(size)]
        for i in range(size)
    ]

    if constrained:
        service_times = [0] + [
            rng.randint(20, 60) for _ in range(n)
        ]
        windows = [(0, 1440)]

        for _ in range(n):
            opening = rng.randint(540, 780)
            windows.append(
                (opening, opening + rng.randint(30, 120))
            )
        trip_end = 900
    else:
        service_times = [0] + [15] * n
        windows = [(0, 1440)] * size
        trip_end = 1200

    return dict(
        time_matrix=matrix,
        service_times=service_times,
        time_windows=windows,
        trip_start=540,
        trip_end=trip_end,
        tolerance=30,
    )


def measure(fn, problem):
    start = time.perf_counter()
    result = fn(**problem)
    return result, time.perf_counter() - start


def benchmark(n, constrained, seeds=range(10)):
    original_times = []
    optimized_times = []
    mismatches = 0
    held_karp_times = []

    for seed in seeds:
        problem = generate_problem(n, constrained, seed)

        original, t1 = measure(original_dp, problem)
        optimized, t2 = measure(optimized_dp, problem)
        if not constrained:
            held_karp, t3 = measure(optimize_trip_held_karp, problem)

            assert held_karp[1:3] == original[1:3], (
                f"Held-Karp mismatch for seed={seed}: "
                f"original={original[:3]}, "
                f"held_karp={held_karp[:3]}"
            )

            held_karp_times.append(t3)

        original_times.append(t1)
        optimized_times.append(t2)

        if original[1:3] != optimized[1:3]:
            mismatches += 1
            print(
                f"MISMATCH seed={seed}: "
                f"original={original[:3]}, "
                f"optimized={optimized[:3]}"
            )

    a = statistics.median(original_times)
    b = statistics.median(optimized_times)

    print(
        f"\nAttractions={n} | "
        f"{'Constrained' if constrained else 'Unrestricted'}"
    )
    print(f"Original DP  | median={a:.4f}s")
    print(f"Optimized DP | median={b:.4f}s")
    print(f"Speedup      | {a / b:.2f}x" if b > 0 else "Speedup: N/A")
    print(f"Mismatches   | {mismatches}")
    if not constrained:
        median_hk = statistics.median(held_karp_times)

        print(f"Held-Karp   | median={median_hk:.4f}s")
        print(
            f"HK speedup vs optimized DP: "
            f"{statistics.median(optimized_times) / median_hk:.2f}x"
        )

if __name__ == "__main__":
    for n in [8, 10, 12, 15]:
        benchmark(n, constrained=True)
        benchmark(n, constrained=False)