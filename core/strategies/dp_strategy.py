from core.dp_optimizer_optimized import optimize_trip_dp

from core.strategies.base import (
    OptimizationStrategy,
    OptimizerResult,
    TripProblem,
)


class DPStrategy(OptimizationStrategy):

    def optimize(self, problem: TripProblem) -> OptimizerResult:
        return optimize_trip_dp(
            time_matrix=problem.time_matrix,
            service_times=problem.service_times,
            time_windows=problem.time_windows,
            trip_start=problem.trip_start,
            trip_end=problem.trip_end,
            tolerance=problem.tolerance,
            wait_weight=problem.wait_weight,
        )