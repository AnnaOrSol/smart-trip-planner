import random
import time

from core.custom_optimizer import optimize_trip
from core.dp_optimizer import optimize_trip_dp
from core.ortools_optimizer import optimize_trip_ortools


def run_benchmark(num_attractions, constrained=True, seed=42, include_backtracking=True):
    random.seed(seed)
    n = num_attractions + 1

    matrix = [
        [0 if i == j else random.randint(5, 30) for j in range(n)]
        for i in range(n)
    ]

    if constrained:
        service_times = [0] + [
            random.randint(20, 60) for _ in range(num_attractions)
        ]

        time_windows = [(0, 1440)]

        for _ in range(num_attractions):
            opening = random.randint(540, 780)
            latest_start = opening + random.randint(30, 120)
            time_windows.append((opening, latest_start))

        trip_end = 900
    else:
        service_times = [0] + [15] * num_attractions
        time_windows = [(0, 1440)] * n
        trip_end = 1200

    trip_start = 540

    algorithms = []

    if include_backtracking:
        algorithms.append((
            "Backtracking",
            lambda: optimize_trip(
                matrix, service_times, time_windows,
                trip_start, trip_end
            )
        ))

    algorithms.extend([
        (
            "DP",
            lambda: optimize_trip_dp(
                matrix, service_times, time_windows,
                trip_start, trip_end
            )
        ),
        (
            "OR-Tools",
            lambda: optimize_trip_ortools(
                matrix, service_times, time_windows,
                trip_start, trip_end,
                time_limit_seconds=3
            )
        ),
    ])

    print(
        f"\nScenario: {'Constrained' if constrained else 'Unrestricted'}"
        f" | Attractions: {num_attractions}"
    )

    for name, algorithm in algorithms:
        start = time.perf_counter()
        path, count, cost, explored = algorithm()
        elapsed = time.perf_counter() - start

        print(
            f"{name:15} | Visited={count:2} "
            f"| Cost={cost:6} | Time={elapsed:.4f}s"
        )


if __name__ == "__main__":
    for constrained in [True, False]:
        run_benchmark(
            num_attractions=15,
            constrained=constrained,
            include_backtracking=False
        )