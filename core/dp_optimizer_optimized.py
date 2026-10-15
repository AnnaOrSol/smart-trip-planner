"""Exact subset dynamic programming for a single-day trip itinerary."""


def optimize_trip_dp(
    time_matrix,
    service_times,
    time_windows,
    trip_start,
    trip_end,
    tolerance=30,
    wait_weight=3,
):
    """Return (path, visited_count, cost, states_explored)."""
    n = len(time_matrix)
    limit = trip_end + tolerance
    all_attractions_mask = (1 << (n - 1)) - 1
    openings = [window[0] for window in time_windows]
    return_times = [time_matrix[node][0] for node in range(n)]

    start_state = {"time": trip_start, "cost": 0, "prev": None, "node": 0}
    # Each layer contains only subsets with the same number of attractions.
    layer = {0: {0: [start_state]}}
    best_state = None
    best_count = -1
    best_cost = float("inf")
    states_explored = 0

    for count in range(n):
        if not layer:
            break
        next_layer = {}

        for mask, nodes in layer.items():
            remaining = all_attractions_mask ^ mask
            for current_node, frontier in nodes.items():
                # Snapshot needed because the dominance frontier can change.
                for state in list(frontier):
                    if not any(candidate is state for candidate in frontier):
                        continue

                    states_explored += 1
                    return_time = state["time"] + return_times[current_node]
                    if return_time <= limit:
                        total_cost = (
                            state["cost"]
                            + return_times[current_node]
                            + 2 * max(0, return_time - trip_end)
                        )
                        if count > best_count or (count == best_count and total_cost < best_cost):
                            best_count = count
                            best_cost = total_cost
                            best_state = state

                    remaining_bits = remaining
                    while remaining_bits:
                        bit = remaining_bits & -remaining_bits
                        remaining_bits -= bit
                        next_node = bit.bit_length()  # bit 0 -> node 1

                        travel = time_matrix[current_node][next_node]
                        arrival = state["time"] + travel
                        window_start, window_end = time_windows[next_node]
                        if arrival > window_end:
                            continue

                        waiting = max(0, window_start - arrival)
                        finish = arrival + waiting + service_times[next_node]
                        if finish > limit:
                            continue

                        new_mask = mask | bit
                        new_state = {
                            "time": finish,
                            "cost": state["cost"] + travel + wait_weight * waiting,
                            "prev": state,
                            "node": next_node,
                        }
                        frontier_next = next_layer.setdefault(new_mask, {}).setdefault(next_node, [])
                        # Only the current state's time matters for this rule;
                        # cache the remaining-opening check once per insertion.
                        still_unvisited = all_attractions_mask ^ new_mask
                        # Important: the original rule checks a['time'] for
                        # each dominance direction, not always new_state time.
                        # Preserve that behavior by using a state-aware check.
                        def dominates(a, b):
                            if a["time"] > b["time"]:
                                return False
                            scan_bits = still_unvisited
                            all_open = True
                            while scan_bits:
                                other_bit = scan_bits & -scan_bits
                                scan_bits -= other_bit
                                if openings[other_bit.bit_length()] > a["time"]:
                                    all_open = False
                                    break
                            if all_open:
                                return a["cost"] <= b["cost"]
                            return a["cost"] + wait_weight * (b["time"] - a["time"]) <= b["cost"]

                        if not any(dominates(old, new_state) for old in frontier_next):
                            frontier_next[:] = [old for old in frontier_next if not dominates(new_state, old)]
                            frontier_next.append(new_state)

        layer = next_layer

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
