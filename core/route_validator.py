from dataclasses import dataclass
from math import isclose


@dataclass
class ValidationResult:
    valid: bool
    errors: list[str]


def validate_route(
    path,
    visited_count,
    reported_cost,
    time_matrix,
    service_times,
    time_windows,
    trip_start,
    trip_end,
    tolerance=30,
    wait_weight=3,
):
    errors = []
    n = len(time_matrix)

    if not path or len(path) < 2:
        return ValidationResult(False, ["Route is empty or incomplete."])

    if path[0] != 0 or path[-1] != 0:
        errors.append("Route must start and end at depot 0.")

    attractions = path[1:-1]

    if any(not isinstance(node, int) or not 1 <= node < n
           for node in attractions):
        errors.append("Route contains an invalid attraction index.")
        return ValidationResult(False, errors)

    if len(attractions) != len(set(attractions)):
        errors.append("Route visits an attraction more than once.")

    if len(attractions) != visited_count:
        errors.append(
            f"Visited count mismatch: expected {len(attractions)}, "
            f"reported {visited_count}."
        )

    current_time = trip_start
    calculated_cost = 0

    for previous_node, node in zip(path, path[1:]):
        travel_time = time_matrix[previous_node][node]

        if travel_time is None or travel_time < 0:
            errors.append(
                f"Invalid travel time from {previous_node} to {node}."
            )
            return ValidationResult(False, errors)

        current_time += travel_time
        calculated_cost += travel_time

        if node == 0:
            continue

        opening, latest_start = time_windows[node]

        visit_start = max(current_time, opening)
        waiting = visit_start - current_time

        if visit_start > latest_start:
            errors.append(
                f"Attraction {node} starts after its latest allowed time."
            )

        calculated_cost += wait_weight * waiting
        current_time = visit_start + service_times[node]

    if current_time > trip_end + tolerance:
        errors.append(
            f"Route ends at {current_time}, "
            f"after allowed limit {trip_end + tolerance}."
        )

    overtime = max(0, current_time - trip_end)
    calculated_cost += 2 * overtime

    if not isclose(calculated_cost, reported_cost, abs_tol=1e-9):
        errors.append(
            f"Cost mismatch: calculated={calculated_cost}, "
            f"reported={reported_cost}."
        )

    return ValidationResult(
        valid=len(errors) == 0,
        errors=errors,
    )