# Custom Trip Optimization Algorithm

## Overview

This project includes a custom trip optimization algorithm implemented in Python, without relying on an external optimization solver.

The algorithm aims to:

1. **Maximize the number of destinations visited.**
2. **Minimize the weighted route cost** among solutions visiting the same number of destinations.

The route starts and ends at a designated depot and respects destination opening hours, visit durations, and the trip's time limit.

## Objective Function

The weighted route cost is defined as:

`cost = travel_time + wait_weight × waiting_time + 2 × overtime`

Where:
- `travel_time` is the total travel duration, including the return to the depot.
- `waiting_time` is the total time spent waiting for destinations to open.
- `overtime` is the amount of time exceeding the preferred trip end time.
- `wait_weight` defaults to 3.
- A configurable tolerance allows a limited extension beyond the preferred trip end time.

The optimization is lexicographic: maximizing the number of destinations takes priority over minimizing cost.

## Algorithm Development

### 1. Backtracking

Implemented a recursive search that explores feasible destination sequences while tracking:

- Current destination and time
- Visited destinations
- Accumulated travel and waiting times
- Destination time windows
- Feasibility of returning to the starting point

### 2. Branch and Bound

Added pruning rules to eliminate branches that cannot improve the best solution:

- **Destination-count bound:** Prune when the maximum number of potentially reachable destinations is below the current best.
- **Cost bound:** Prune when a branch cannot visit more destinations and its accumulated cost is already no better than the best solution.

### 3. Candidate Ordering

Candidates are explored in ascending order of their earliest possible visit completion time.

This heuristic changes the search order without intentionally removing feasible solutions.

### 4. Memoization and Dominance Pruning

States are grouped by their current destination and visited destination set.

For each state, non-dominated combinations of current time and accumulated cost are retained.

A state is pruned when a previously explored state with the same current destination and visited set can match its arrival time at no greater weighted cost, accounting for any additional waiting required.


### 5. Travel Cost Lower Bounds

Two additional pruning bounds were introduced:

- **Minimum next-travel bound:** Uses the shortest travel time from the current destination to a reachable unvisited destination.
- **Global minimum-travel bound:** Precomputes the minimum travel time between distinct nodes and multiplies it by the minimum number of remaining travel legs, including the return to the depot.

These bounds are applied only when matching the current best destination count requires visiting additional destinations, and the branch cannot exceed that count.

The global minimum is calculated once per optimization run, allowing the bound to be evaluated in constant time during recursive search.

## Validation

The optimized algorithm was compared against exhaustive backtracking.

- 100 randomized small test cases passed.
- Both implementations returned the same destination count and weighted cost in every tested case.
- Additional manual tests covered different trip durations and destination counts.

These tests provide empirical validation, not a formal proof of correctness.

## Performance Results

All benchmarks used synthetic travel-time matrices and were executed locally.

| Scenario | Average States Explored | Average Execution Time |
|---|---:|---:|
| 12 destinations, constrained windows — before new lower bounds | 774.6 | 1.8 ms |
| 12 destinations, constrained windows — after both lower bounds | 745.8 | 1.9 ms |
| 12 destinations, unrestricted windows — before new lower bounds | 3,005,227 | 8.58 s |
| 12 destinations, unrestricted windows — after next-travel bound | 2,265,896 | 7.98 s |
| 12 destinations, unrestricted windows — after global minimum-travel bound | 609,156 | 1.62 s |

**Key result:** Adding the global minimum-travel bound reduced explored states by approximately 73.1% and execution time by 79.7% compared with the previous version in the unrestricted scenario.

All 100 randomized correctness tests continued to pass after the changes.

Benchmarks were performed locally on synthetic data, using 12 destinations and 10 runs per scenario.

The 9-destination comparison reduced the number of explored states by approximately **83.1%**.

The unrestricted time-window benchmark revealed a significant increase in search complexity when most destination sequences remain feasible.

Benchmark results are workload-dependent and do not establish general runtime guarantees.

## Planned Improvements

- Investigate tighter remaining-travel lower bounds
- Investigation of MST-based bounds for subset-selection problems
- Further performance and correctness testing
- Detailed itinerary output and skipped-destination reporting
- Comparison with OR-Tools
- Integration with the Streamlit user interface

## Technologies

Python, recursive backtracking, Branch and Bound, memoization, and dominance pruning.