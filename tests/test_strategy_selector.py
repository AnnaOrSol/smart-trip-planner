import unittest

from core.strategies.base import TripProblem
from core.strategies.selector import OptimizerSelector
from core.strategies.dp_strategy import DPStrategy
from core.strategies.held_karp_strategy import HeldKarpStrategy


class TestOptimizerSelector(unittest.TestCase):

    def setUp(self):
        self.selector = OptimizerSelector()

        self.matrix = [
            [0, 10, 20],
            [10, 0, 15],
            [20, 15, 0],
        ]

        self.services = [0, 30, 30]

    def make_problem(self, windows):
        return TripProblem(
            time_matrix=self.matrix,
            service_times=self.services,
            time_windows=windows,
            trip_start=540,
            trip_end=1080,
            tolerance=30,
        )

    def test_unrestricted_selects_held_karp(self):
        problem = self.make_problem([
            (0, 1440),
            (0, 1440),
            (0, 1440),
        ])

        strategy = self.selector.select(problem)

        self.assertIsInstance(strategy, HeldKarpStrategy)

    def test_late_opening_selects_dp(self):
        problem = self.make_problem([
            (0, 1440),
            (660, 1440),
            (0, 1440),
        ])

        strategy = self.selector.select(problem)

        self.assertIsInstance(strategy, DPStrategy)

    def test_early_latest_start_selects_dp(self):
        problem = self.make_problem([
            (0, 1440),
            (0, 900),
            (0, 1440),
        ])

        strategy = self.selector.select(problem)

        self.assertIsInstance(strategy, DPStrategy)

    def test_unrestricted_result_matches_held_karp(self):
        problem = self.make_problem([
            (0, 1440),
            (0, 1440),
            (0, 1440),
        ])

        actual = self.selector.optimize(problem)
        expected = HeldKarpStrategy().optimize(problem)

        self.assertEqual(actual, expected)

    def test_constrained_result_matches_dp(self):
        problem = self.make_problem([
            (0, 1440),
            (660, 900),
            (0, 1440),
        ])

        actual = self.selector.optimize(problem)
        expected = DPStrategy().optimize(problem)

        self.assertEqual(actual, expected)


if __name__ == "__main__":
    unittest.main()