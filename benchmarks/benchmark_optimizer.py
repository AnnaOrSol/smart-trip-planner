
import random
import time

from core.custom_optimizer import optimize_trip
from core.dp_optimizer import optimize_trip_dp

def run_benchmark(constrained=True, num_tests=10):
    random.seed(42)

    scenario = "Constrained" if constrained else "Unrestricted"
    print(f"\nScenario: {scenario}")

    bt_total_nodes = 0
    bt_total_time = 0

    dp_total_states = 0
    dp_total_time = 0

    for test in range(num_tests):
        n = 16  # Depot + 15 destinations

        time_matrix = [[0] * n for _ in range(n)]

        for i in range(n):
            for j in range(i + 1, n):
                travel = random.randint(5, 30)
                time_matrix[i][j] = travel
                time_matrix[j][i] = travel

        if constrained:
            service_times = [0] + [
                random.randint(20, 60)
                for _ in range(n - 1)
            ]

            time_windows = [(0, 1440)]

            for _ in range(n - 1):
                opening = random.randint(540, 780)
                latest_start = opening + random.randint(30, 120)
                time_windows.append((opening, latest_start))

            trip_end = 900

        else:
            service_times = [0] + [15] * (n - 1)
            time_windows = [(0, 1440)] * n
            trip_end = 1200

        # Backtracking benchmark
        start = time.perf_counter()

        bt_path, bt_count, bt_cost, bt_nodes = optimize_trip(
            time_matrix,
            service_times,
            time_windows,
            trip_start=540,
            trip_end=trip_end,
            use_pruning=True
        )

        bt_elapsed = time.perf_counter() - start

        # Dynamic Programming benchmark
        start = time.perf_counter()

        dp_path, dp_count, dp_cost, dp_states = optimize_trip_dp(
            time_matrix,
            service_times,
            time_windows,
            trip_start=540,
            trip_end=trip_end
        )

        dp_elapsed = time.perf_counter() - start

        # Verify that both algorithms agree
        assert (bt_count, bt_cost) == (dp_count, dp_cost), (
            f"Mismatch in test {test + 1}: "
            f"BT=({bt_count}, {bt_cost}), "
            f"DP=({dp_count}, {dp_cost})"
        )

        bt_total_nodes += bt_nodes
        bt_total_time += bt_elapsed

        dp_total_states += dp_states
        dp_total_time += dp_elapsed

        print(
            f"Test {test + 1}: "
            f"Visited={bt_count}, Cost={bt_cost} | "
            f"BT: {bt_nodes} nodes, {bt_elapsed:.4f}s | "
            f"DP: {dp_states} states, {dp_elapsed:.4f}s"
        )

    print(f"\n--- {scenario} averages ---")
    print(
        f"Backtracking: "
        f"{bt_total_nodes / num_tests:.1f} nodes, "
        f"{bt_total_time / num_tests:.4f}s"
    )
    print(
        f"DP:           "
        f"{dp_total_states / num_tests:.1f} states, "
        f"{dp_total_time / num_tests:.4f}s"
    )

    if dp_total_time > 0:
        print(f"Speed ratio (BT / DP): {bt_total_time / dp_total_time:.2f}x")


if __name__ == "__main__":
    run_benchmark(constrained=True, num_tests=10)
    run_benchmark(constrained=False, num_tests=10)
