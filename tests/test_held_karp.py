import random

from core.dp_optimizer import optimize_trip_dp
from core.held_karp_optimizer import optimize_trip_held_karp


def test_held_karp():
    for seed in range(1000):
        rng = random.Random(seed)

        n = rng.randint(2, 10)  # Includes depot
        trip_start = 540
        trip_end = rng.randint(650, 1000)
        tolerance = 30

        time_matrix = [
            [
                0 if i == j else rng.randint(5, 50)
                for j in range(n)
            ]
            for i in range(n)
        ]

        service_times = [0] + [
            rng.randint(10, 60)
            for _ in range(n - 1)
        ]

        # Unrestricted windows: latest allowed visit start
        time_windows = [(0, 1440)] * n

        args = (
            time_matrix,
            service_times,
            time_windows,
            trip_start,
            trip_end,
        )

        expected = optimize_trip_dp(
            *args,
            tolerance=tolerance,
        )

        actual = optimize_trip_held_karp(
            *args,
            tolerance=tolerance,
        )

        assert actual[1] == expected[1], (
            f"Seed {seed}: different attraction counts\n"
            f"DP: {expected}\n"
            f"HK: {actual}"
        )

        assert abs(actual[2] - expected[2]) < 1e-9, (
            f"Seed {seed}: different costs\n"
            f"DP: {expected}\n"
            f"HK: {actual}"
        )

        path = actual[0]

        assert path[0] == 0 and path[-1] == 0
        assert len(path) == actual[1] + 2
        assert len(set(path[1:-1])) == actual[1]

    print("PASS: 1000 Held-Karp correctness tests")


if __name__ == "__main__":
    test_held_karp()