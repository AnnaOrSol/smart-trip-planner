

def add_state(frontier, new_state, wait_weight, time_windows, visited, n):
    new_time = new_state["time"]
    new_cost = new_state["cost"]

    def dominates(a, b):
        if a["time"] > b["time"]:
            return False

        # No future waiting is possible if every remaining
        # attraction is already open at the earlier state's time.
        no_future_waiting = all(
            node in visited or time_windows[node][0] <= a["time"]
            for node in range(1, n)
        )

        if no_future_waiting:
            return a["cost"] <= b["cost"]

        return (
            a["cost"]
            + wait_weight * (b["time"] - a["time"])
            <= b["cost"]
        )

    for state in frontier:
        if dominates(state, new_state):
            return False

    frontier[:] = [
        state for state in frontier
        if not dominates(new_state, state)
    ]

    frontier.append(new_state)
    return True


def optimize_trip_dp(
    time_matrix,
    service_times,
    time_windows,
    trip_start,
    trip_end,
    tolerance=30,
    wait_weight=3
):
    n = len(time_matrix)

    return_times = [time_matrix[node][0] for node in range(n)]

    start_state = {
        "time": trip_start,
        "cost": 0,
        "prev": None,
        "node": 0
    }

    dp = {
        frozenset({0}): {
            0: [start_state]
        }
    }

    best_state = None
    best_count = -1
    best_cost = float("inf")
    states_explored = 0

    # Process states layer by layer
    for count in range(n):
        current_layer = [
            visited
            for visited in dp
            if len(visited) == count + 1
        ]

        for visited in current_layer:
            for current_node, frontier in dp[visited].items():

                for state in list(frontier):
                    # Skip states removed by dominance
                    if not any(s is state for s in frontier):
                        continue

                    states_explored += 1
                    visited_count = len(visited) - 1

                    # Evaluate returning to the hotel
                    return_travel = return_times[current_node]
                    return_time = state["time"] + return_travel

                    if return_time <= trip_end + tolerance:
                        overtime = max(0, return_time - trip_end)

                        total_cost = (
                            state["cost"]
                            + return_travel
                            + 2 * overtime
                        )

                        visited_count = len(visited) - 1

                        if (
                            visited_count > best_count
                            or (
                                visited_count == best_count
                                and total_cost < best_cost
                            )
                        ):
                            best_count = visited_count
                            best_cost = total_cost
                            best_state = state


                    # Try visiting each unvisited attraction
                    for next_node in range(1, n):
                        if next_node in visited:
                            continue

                        travel_time = time_matrix[current_node][next_node]
                        arrival_time = state["time"] + travel_time

                        window_start, window_end = time_windows[next_node]

                        if arrival_time > window_end:
                            continue

                        wait_time = max(0, window_start - arrival_time)
                        new_time = arrival_time + wait_time + service_times[next_node]

                        # Check whether returning to the hotel is still possible
                        if new_time > trip_end + tolerance:
                            continue

                        new_cost = (
                            state["cost"]
                            + travel_time
                            + wait_weight * wait_time
                        )

                        new_visited = visited | {next_node}

                        new_state = {
                            "time": new_time,
                            "cost": new_cost,
                            "prev": state,
                            "node": next_node
                        }

                        next_frontier = (
                            dp.setdefault(new_visited, {})
                              .setdefault(next_node, [])
                        )

                        add_state(next_frontier, new_state, wait_weight, time_windows, new_visited, n)

    # Reconstruct the optimal route
    if best_state is None:
        return [], 0, float("inf"), states_explored

    path = []
    current = best_state

    while current is not None:
        path.append(current["node"])
        current = current["prev"]

    path.reverse()
    path.append(0)

    return path, best_count, best_cost, states_explored