"""Compare optimized DP with independent exhaustive enumeration on small inputs."""
import random
from core.dp_optimizer_optimized import optimize_trip_dp


def exhaustive(matrix, durations, windows, start, end, tolerance, wait_weight):
    n = len(matrix)
    limit = end + tolerance
    best = (0, float('inf'))

    def visit(last, used, clock, cost, count):
        nonlocal best
        back = clock + matrix[last][0]
        if back <= limit:
            candidate = (count, cost + matrix[last][0] + 2 * max(0, back - end))
            if candidate[0] > best[0] or (candidate[0] == best[0] and candidate[1] < best[1]):
                best = candidate
        for nxt in range(1, n):
            if used & (1 << (nxt - 1)):
                continue
            arrival = clock + matrix[last][nxt]
            opening, latest = windows[nxt]
            beginning = max(arrival, opening)
            finish = beginning + durations[nxt]
            if beginning > latest or finish > limit:
                continue
            visit(nxt, used | (1 << (nxt - 1)), finish,
                  cost + matrix[last][nxt] + wait_weight * (beginning - arrival), count + 1)

    visit(0, 0, start, 0, 0)
    return best


def test_dp_matches_exhaustive_on_500_random_valid_instances():
    rng = random.Random(20261015)
    for case in range(500):
        n = rng.randint(2, 7)
        matrix = [[0 if i == j else rng.randint(1, 35) for j in range(n)] for i in range(n)]
        durations = [0] + [rng.randint(5, 35) for _ in range(n - 1)]
        windows = [(0, 300)]
        for i in range(1, n):
            opening = rng.randint(0, 90)
            closing = rng.randint(opening + durations[i], 180)
            windows.append((opening, closing - durations[i]))
        end = rng.randint(60, 160)
        tolerance = rng.choice([0, 15, 30])
        weight = rng.choice([0, 1, 3, 5])
        expected = exhaustive(matrix, durations, windows, 0, end, tolerance, weight)
        actual = optimize_trip_dp(matrix, durations, windows, 0, end, tolerance, weight)
        assert actual[1:3] == expected, f'Case {case}: expected {expected}, got {actual[1:3]}; matrix={matrix}; windows={windows}; durations={durations}; end={end}; tolerance={tolerance}; weight={weight}'
