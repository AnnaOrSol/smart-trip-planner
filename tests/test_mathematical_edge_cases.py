"""Regression tests for assumptions used in the mathematical documentation."""
import pytest
from core.dp_optimizer_optimized import optimize_trip_dp
from core.held_karp_optimizer import optimize_trip_held_karp


def test_arrival_before_opening_waits_and_still_fits_latest_start():
    matrix = [[0, 10], [10, 0]]
    result = optimize_trip_dp(matrix, [0, 30], [(0, 200), (60, 70)], 0, 120, tolerance=0)
    assert result[:3] == ([0, 1, 0], 1, 10 + 3 * 50 + 10)


def test_arrival_exactly_at_latest_start_is_allowed():
    result = optimize_trip_dp([[0, 40], [10, 0]], [0, 20], [(0, 200), (0, 40)], 0, 100, tolerance=0)
    assert result[:3] == ([0, 1, 0], 1, 50)


def test_no_attraction_feasible_returns_empty_trip():
    result = optimize_trip_dp([[0, 50], [50, 0]], [0, 10], [(0, 100), (0, 20)], 0, 60, tolerance=0)
    assert result[:3] == ([0, 0], 0, 0)


def test_return_overtime_penalty():
    result = optimize_trip_dp([[0, 15], [15, 0]], [0, 10], [(0, 100), (0, 100)], 0, 35, tolerance=10)
    assert result[:3] == ([0, 1, 0], 1, 40)


def test_held_karp_rejects_constrained_window():
    with pytest.raises(ValueError, match='unrestricted'):
        optimize_trip_held_karp([[0, 5], [5, 0]], [0, 10], [(0, 100), (20, 100)], 0, 50, tolerance=0)


def test_held_karp_matches_dp_when_unrestricted():
    matrix = [[0, 8, 15], [9, 0, 7], [12, 6, 0]]
    durations = [0, 10, 10]
    windows = [(0, 100)] * 3
    dp = optimize_trip_dp(matrix, durations, windows, 0, 50, tolerance=0)
    hk = optimize_trip_held_karp(matrix, durations, windows, 0, 50, tolerance=0)
    assert dp[1:3] == hk[1:3]
