from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TypeAlias


OptimizerResult: TypeAlias = tuple[list[int], int, float, int]


@dataclass
class TripProblem:
    time_matrix: list[list[int]]
    service_times: list[int]
    time_windows: list[tuple[int, int]]
    trip_start: int
    trip_end: int
    tolerance: int = 30
    wait_weight: int = 3


class OptimizationStrategy(ABC):

    @abstractmethod
    def optimize(self, problem: TripProblem) -> OptimizerResult:
        pass