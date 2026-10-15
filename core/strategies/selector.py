from core.strategies.base import (
    OptimizationStrategy,
    OptimizerResult,
    TripProblem,
)

from core.strategies.dp_strategy import DPStrategy
from core.strategies.held_karp_strategy import HeldKarpStrategy


class OptimizerSelector:

    def __init__(self):
        self._dp = DPStrategy()
        self._held_karp = HeldKarpStrategy()

    def select(self, problem: TripProblem) -> OptimizationStrategy:
        if self._can_use_held_karp(problem):
            return self._held_karp

        return self._dp

    @staticmethod
    def _can_use_held_karp(problem: TripProblem) -> bool:
        limit = problem.trip_end + problem.tolerance

        for node in range(1, len(problem.time_matrix)):
            opening, latest_start = problem.time_windows[node]
            service_time = problem.service_times[node]

            if opening > problem.trip_start:
                return False

            if latest_start < limit - service_time:
                return False

        return True

    def optimize(self, problem: TripProblem) -> OptimizerResult:
        strategy = self.select(problem)
        return strategy.optimize(problem)
