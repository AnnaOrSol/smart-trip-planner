import random
import time
import statistics

from core.dp_optimizer import optimize_trip_dp
from core.ortools_optimizer import optimize_trip_ortools


def generate_problem(num_attractions, constrained, seed):
    rng = random.Random(seed)
    n = num_attractions + 1

    matrix = [
        [
            0 if i == j else rng.randint(5, 30)
            for j in range(n)
        ]
        for i in range(n)
    ]

    if constrained:
        service_times = [0] + [
            rng.randint(20, 60)
            for _ in range(num_attractions)
        ]

        time_windows = [(0, 1440)]

        for _ in range(num_attractions):
            opening = rng.randint(540, 780)
            latest_start = opening + rng.randint(30, 120)
            time_windows.append((opening, latest_start))

        trip_end = 900

    else:
        service_times = [0] + [15] * num_attractions
        time_windows = [(0, 1440)] * n
        trip_end = 1200

    return {
        "time_matrix": matrix,
        "service_times": service_times,
        "time_windows": time_windows,
        "trip_start": 540,
        "trip_end": trip_end,
        "tolerance": 30,
    }


def validate_result(path, count, cost, problem):
    if not path or path[0] != 0 or path[-1] != 0:
        return False, "Invalid start/end"

    visited = path[1:-1]

    if len(visited) != len(set(visited)):
        return False, "Duplicate attractions"

    if any(node < 1 or node >= len(problem["time_matrix"])
           for node in visited):
        return False, "Invalid attraction index"

    if len(visited) != count:
        return False, "Incorrect visit count"

    current_time = problem["trip_start"]
    calculated_cost = 0

    matrix = problem["time_matrix"]
    service_times = problem["service_times"]
    windows = problem["time_windows"]

    for previous, current in zip(path, path[1:]):
        travel = matrix[previous][current]
        current_time += travel
        calculated_cost += travel

        if current != 0:
            opening, latest_start = windows[current]
            waiting = max(0, opening - current_time)
            visit_start = current_time + waiting

            if visit_start > latest_start:
                return False, "Time window violated"

            calculated_cost += 3 * waiting
            current_time = visit_start + service_times[current]

    if current_time > problem["trip_end"] + problem["tolerance"]:
        return False, "Trip end exceeded"

    calculated_cost += 2 * max(
        0, current_time - problem["trip_end"]
    )

    if abs(calculated_cost - cost) > 1e-6:
        return False, (
            f"Cost mismatch: returned={cost}, "
            f"calculated={calculated_cost}"
        )

    return True, "OK"


def measure(algorithm, problem):
    start = time.perf_counter()
    path, count, cost, _ = algorithm(**problem)
    elapsed = time.perf_counter() - start

    valid, reason = validate_result(path, count, cost, problem)

    return {
        "path": path,
        "count": count,
        "cost": cost,
        "time": elapsed,
        "valid": valid,
        "reason": reason,
    }


def run_comparison(num_attractions, constrained, seeds):
    dp_times = []
    ortools_times = []

    same_count = 0
    same_optimum = 0
    missed_attractions = 0
    invalid_results = 0

    for seed in seeds:
        problem = generate_problem(
            num_attractions, constrained, seed
        )

        dp = measure(optimize_trip_dp, problem)

        ortools = measure(
            lambda **kwargs: optimize_trip_ortools(
                **kwargs,
                time_limit_seconds=1
            ),
            problem
        )

        dp_times.append(dp["time"])
        ortools_times.append(ortools["time"])

        if not dp["valid"] or not ortools["valid"]:
            invalid_results += 1
            print(
                f"INVALID seed={seed}: "
                f"DP={dp['reason']}, "
                f"OR-Tools={ortools['reason']}"
            )
            continue

        if dp["count"] == ortools["count"]:
            same_count += 1

            if abs(dp["cost"] - ortools["cost"]) < 1e-6:
                same_optimum += 1

        missed_attractions += max(
            0, dp["count"] - ortools["count"]
        )

    print(
        f"\nAttractions={num_attractions} | "
        f"{'Constrained' if constrained else 'Unrestricted'}"
    )

    print(f"Runs: {len(seeds)}")

    print(
        f"DP       | mean={statistics.mean(dp_times):.4f}s "
        f"| median={statistics.median(dp_times):.4f}s "
        f"| max={max(dp_times):.4f}s"
    )

    print(
        f"OR-Tools | mean={statistics.mean(ortools_times):.4f}s "
        f"| median={statistics.median(ortools_times):.4f}s "
        f"| max={max(ortools_times):.4f}s"
    )

    print(f"Same attraction count: {same_count}/{len(seeds)}")
    print(f"Same optimal result:   {same_optimum}/{len(seeds)}")
    print(f"Total missed attractions: {missed_attractions}")
    print(f"Invalid results: {invalid_results}")


if __name__ == "__main__":
    seeds = range(10)

    for n in [8, 10, 12, 15]:
        run_comparison(n, constrained=True, seeds=seeds)
        run_comparison(n, constrained=False, seeds=seeds)