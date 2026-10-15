def optimize_trip_held_karp(
    time_matrix,
    service_times,
    time_windows,
    trip_start,
    trip_end,
    tolerance=30,
    wait_weight=3,
):
    n = len(time_matrix)
    limit = trip_end + tolerance

    # This specialized solver is valid only when every attraction
    # can be started immediately throughout the planning horizon.
    if any(
        time_windows[node][0] > trip_start
        or time_windows[node][1] < limit - service_times[node]
        for node in range(1, n)
    ):
        raise ValueError(
            "Held-Karp requires unrestricted attraction windows."
        )

    # dp[(mask, last)] = (travel_time, previous_node)
    dp = {(0, 0): (0, None)}
    states_explored = 0

    best_count = 0
    best_cost = 0
    best_key = (0, 0)

    duration_sums = [0] * (1 << (n - 1))

    for mask in range(1, len(duration_sums)):
        lowest_bit = mask & -mask
        node = lowest_bit.bit_length()

        duration_sums[mask] = (
            duration_sums[mask ^ lowest_bit]
            + service_times[node]
        )
    
    for mask in range(1 << (n - 1)):
        for last in range(n):
            key = (mask, last)

            if key not in dp:
                continue

            states_explored += 1
            travel_sum, _ = dp[key]

            visit_duration = duration_sums[mask]


            current_time = (
                trip_start + travel_sum + visit_duration
            )

            return_time = current_time + time_matrix[last][0]

            if return_time <= limit:
                count = mask.bit_count()
                cost = (
                    travel_sum
                    + time_matrix[last][0]
                    + 2 * max(0, return_time - trip_end)
                )

                if (
                    count > best_count
                    or (count == best_count and cost < best_cost)
                ):
                    best_count = count
                    best_cost = cost
                    best_key = key

            for next_node in range(1, n):
                bit = 1 << (next_node - 1)

                if mask & bit:
                    continue

                new_mask = mask | bit
                new_travel = (
                    travel_sum + time_matrix[last][next_node]
                )

                new_duration = visit_duration + service_times[next_node]

                if trip_start + new_travel + new_duration > limit:
                    continue

                next_key = (new_mask, next_node)

                if (
                    next_key not in dp
                    or new_travel < dp[next_key][0]
                ):
                    dp[next_key] = (new_travel, last)

    path = []
    mask, last = best_key

    while last != 0:
        path.append(last)
        mask ^= 1 << (last - 1)
        last = dp[(mask | (1 << (path[-1] - 1)), path[-1])][1]

    path.reverse()
    path = [0] + path + [0]

    return path, best_count, best_cost, states_explored