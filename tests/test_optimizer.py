
import random

from core.custom_optimizer import calculate_min_return_times, optimize_trip
from core.dp_optimizer import optimize_trip_dp
from core.ortools_optimizer import optimize_trip_ortools
from core.dp_optimizer_optimized import optimize_trip_dp as optimized_dp

def test_ortools():
    matrix = [
        [0, 10, 20],
        [10, 0, 10],
        [20, 10, 0],
    ]

    service_times = [0, 30, 30]
    time_windows = [
        (0, 1440),
        (540, 900),
        (540, 900),
    ]

    result = optimize_trip_ortools(
        matrix,
        service_times,
        time_windows,
        trip_start=540,
        trip_end=900,
        time_limit_seconds=2,
    )

    print("OR-Tools:", result)

    assert result[1] == 2


def test_known_example():
    time_matrix = [
        [0, 10, 20, 15],
        [10, 0, 8, 12],
        [20, 8, 0, 6],
        [15, 12, 6, 0]
    ]

    service_times = [0, 60, 45, 30]

    time_windows = [
        (0, 1440),
        (600, 720),
        (540, 660),
        (570, 900)
    ]

    path, count, cost, nodes = optimize_trip(
        time_matrix,
        service_times,
        time_windows,
        trip_start=540,
        trip_end=780
    )

    assert path == [0, 2, 3, 1, 0]
    assert count == 3
    assert cost == 48

    print("Known example passed!")


def test_random_cases():
    random.seed(42)

    for test in range(1000):
        n = 5  # Depot + 4 destinations

        time_matrix = [[0] * n for _ in range(n)]

        for i in range(n):
            for j in range(n):
                if i != j:
                    time_matrix[i][j] = random.randint(5, 30)

        service_times = [0] + [
            random.randint(20, 60)
            for _ in range(n - 1)
        ]

        time_windows = [(0, 1440)]

        for _ in range(n - 1):
            opening = random.randint(540, 780)
            latest_start = opening + random.randint(30, 120)
            time_windows.append((opening, latest_start))

        baseline = optimize_trip(
            time_matrix, service_times, time_windows,
            trip_start=540,
            trip_end=900,
            use_pruning=False
        )

        optimized = optimize_trip(
            time_matrix, service_times, time_windows,
            trip_start=540,
            trip_end=900,
            use_pruning=True
        )

        dp_result = optimize_trip_dp(
            time_matrix,
            service_times,
            time_windows,
            trip_start=540,
            trip_end=900
        )

        optimized_dp_result = optimized_dp(
            time_matrix,
            service_times,
            time_windows,
            trip_start=540,
            trip_end=900
        )

        assert optimized_dp_result[1:3] == baseline[1:3]

        assert dp_result[1:3] == baseline[1:3], (
            f"DP mismatch in test {test}: "
            f"Baseline={baseline}, DP={dp_result}"
        )

        assert baseline[1:3] == optimized[1:3], (
            f"Mismatch in test {test + 1}: "
            f"{baseline} vs {optimized}"
        )

    print("1000 random tests passed! (Baseline, Pruned BT, DP)")


def test_no_reachable_destinations():
    time_matrix = [
        [0, 20, 30],
        [20, 0, 15],
        [30, 15, 0]
    ]

    service_times = [0, 60, 60]

    time_windows = [
        (0, 1440),
        (600, 700),
        (650, 750)
    ]

    path, count, cost, nodes = optimize_trip(
        time_matrix,
        service_times,
        time_windows,
        trip_start=540,
        trip_end=580,
        tolerance=0
    )

    assert path == [0, 0]
    assert count == 0
    assert cost == 0

def test_waiting_time():
    time_matrix = [
        [0, 10],
        [10, 0]
    ]

    service_times = [0, 30]

    time_windows = [
        (0, 1440),
        (600, 700)
    ]

    path, count, cost, nodes = optimize_trip(
        time_matrix,
        service_times,
        time_windows,
        trip_start=540,
        trip_end=780
    )

    assert path == [0, 1, 0]
    assert count == 1
    assert cost == 170

def test_overtime():
    time_matrix = [
        [0, 20],
        [20, 0]
    ]

    service_times = [0, 60]

    time_windows = [
        (0, 1440),
        (540, 900)
    ]

    path, count, cost, nodes = optimize_trip(
        time_matrix,
        service_times,
        time_windows,
        trip_start=540,
        trip_end=630,
        tolerance=30
    )

    assert path == [0, 1, 0]
    assert count == 1
    assert cost == 60


def test_exceeds_tolerance():
    time_matrix = [
        [0, 20],
        [20, 0]
    ]

    service_times = [0, 60]

    time_windows = [
        (0, 1440),
        (540, 900)
    ]

    path, count, cost, nodes = optimize_trip(
        time_matrix,
        service_times,
        time_windows,
        trip_start=540,
        trip_end=630,
        tolerance=5
    )

    assert path == [0, 0]
    assert count == 0
    assert cost == 0

def test_asymmetric_travel_times():
    time_matrix = [
        [0, 10, 30],
        [25, 0, 5],
        [15, 20, 0]
    ]

    service_times = [0, 10, 10]

    time_windows = [
        (0, 1440),
        (540, 900),
        (540, 900)
    ]

    path, count, cost, nodes = optimize_trip(
        time_matrix,
        service_times,
        time_windows,
        trip_start=540,
        trip_end=700
    )

    assert path == [0, 1, 2, 0]
    assert count == 2
    assert cost == 30


def test_indirect_return():
    time_matrix = [
        [0, 5, 50],
        [100, 0, 5],
        [5, 100, 0]
    ]

    service_times = [0, 10, 10]

    time_windows = [
        (0, 1440),
        (540, 900),
        (540, 900)
    ]

    results = []

    for use_pruning in [False, True]:
        results.append(optimize_trip(
            time_matrix,
            service_times,
            time_windows,
            trip_start=540,
            trip_end=600,
            tolerance=0,
            use_pruning=use_pruning
        ))

    for result in results:
        assert result[1:3] == (2, 15), (
            f"Indirect return failed: {result}"
        )

    dp_result = optimize_trip_dp(
        time_matrix,
        service_times,
        time_windows,
        trip_start=540,
        trip_end=600,
        tolerance=0
    )

    assert dp_result[1:3] == (2, 15), (
        f"DP indirect return failed: {dp_result}"
    )

    print("Without pruning:", results[0])
    print("With pruning:", results[1])

def test_shortest_return():
    time_matrix = [
        [0, 10, 30],
        [25, 0, 5],
        [5, 20, 0]
    ]

    result = calculate_min_return_times(time_matrix)

    assert result == [0, 10, 5]
    print("Shortest return test passed!")

def test_dp_vs_backtracking():
    time_matrix = [
        [0, 10, 30],
        [25, 0, 5],
        [15, 20, 0]
    ]

    service_times = [0, 10, 10]

    time_windows = [
        (0, 1440),
        (540, 900),
        (540, 900)
    ]

    backtracking_result = optimize_trip(
        time_matrix,
        service_times,
        time_windows,
        trip_start=540,
        trip_end=700
    )

    dp_result = optimize_trip_dp(
        time_matrix,
        service_times,
        time_windows,
        trip_start=540,
        trip_end=700
    )

    print("Backtracking:", backtracking_result)
    print("DP:", dp_result)

    assert backtracking_result[1:3] == dp_result[1:3]
    print("DP comparison passed!")


if __name__ == "__main__":
    test_known_example()
    test_random_cases()
    test_no_reachable_destinations()
    test_asymmetric_travel_times()
    test_exceeds_tolerance()
    test_overtime()
    test_waiting_time()
    test_indirect_return()
    test_shortest_return()
    test_dp_vs_backtracking()
    print("All correctness tests passed!")
