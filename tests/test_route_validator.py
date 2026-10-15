import unittest

from core.route_validator import validate_route
from core.strategies.base import TripProblem
from core.strategies.selector import OptimizerSelector


class TestRouteValidator(unittest.TestCase):

    def setUp(self):
        self.problem = TripProblem(
            time_matrix=[
                [0, 10, 20],
                [10, 0, 15],
                [20, 15, 0],
            ],
            service_times=[0, 30, 30],
            time_windows=[
                (0, 1440),
                (0, 1440),
                (0, 1440),
            ],
            trip_start=540,
            trip_end=1080,
            tolerance=30,
            wait_weight=3,
        )

    def test_optimizer_produces_valid_route(self):
        result = OptimizerSelector().optimize(self.problem)

        validation = validate_route(
            *result[:3],
            time_matrix=self.problem.time_matrix,
            service_times=self.problem.service_times,
            time_windows=self.problem.time_windows,
            trip_start=self.problem.trip_start,
            trip_end=self.problem.trip_end,
            tolerance=self.problem.tolerance,
            wait_weight=self.problem.wait_weight,
        )

        self.assertTrue(validation.valid, validation.errors)

    def test_duplicate_attraction_is_rejected(self):
        validation = validate_route(
            path=[0, 1, 1, 0],
            visited_count=2,
            reported_cost=20,
            time_matrix=self.problem.time_matrix,
            service_times=self.problem.service_times,
            time_windows=self.problem.time_windows,
            trip_start=self.problem.trip_start,
            trip_end=self.problem.trip_end,
        )

        self.assertFalse(validation.valid)
        self.assertTrue(
            any("more than once" in error for error in validation.errors)
        )

    def test_incorrect_cost_is_rejected(self):
        validation = validate_route(
            path=[0, 1, 0],
            visited_count=1,
            reported_cost=999,
            time_matrix=self.problem.time_matrix,
            service_times=self.problem.service_times,
            time_windows=self.problem.time_windows,
            trip_start=self.problem.trip_start,
            trip_end=self.problem.trip_end,
        )

        self.assertFalse(validation.valid)
        self.assertTrue(
            any("Cost mismatch" in error for error in validation.errors)
        )

    def test_late_visit_is_rejected(self):
        problem = TripProblem(
            time_matrix=self.problem.time_matrix,
            service_times=self.problem.service_times,
            time_windows=[
                (0, 1440),
                (0, 545),
                (0, 1440),
            ],
            trip_start=540,
            trip_end=1080,
        )

        validation = validate_route(
            path=[0, 1, 0],
            visited_count=1,
            reported_cost=20,
            time_matrix=problem.time_matrix,
            service_times=problem.service_times,
            time_windows=problem.time_windows,
            trip_start=problem.trip_start,
            trip_end=problem.trip_end,
        )

        self.assertFalse(validation.valid)
        self.assertTrue(
            any("latest allowed time" in error for error in validation.errors)
        )


if __name__ == "__main__":
    unittest.main()