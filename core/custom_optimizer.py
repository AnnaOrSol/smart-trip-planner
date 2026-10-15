import heapq


def calculate_min_return_times(time_matrix):
    n = len(time_matrix)

    min_return_time = [float("inf")] * n
    min_return_time[0] = 0

    pq = [(0, 0)]

    while pq:
        current_dist, node = heapq.heappop(pq)

        if current_dist > min_return_time[node]:
            continue

        for prev_node in range(n):
            travel_time = time_matrix[prev_node][node]
            new_dist = current_dist + travel_time

            if new_dist < min_return_time[prev_node]:
                min_return_time[prev_node] = new_dist
                heapq.heappush(pq, (new_dist, prev_node))

    return min_return_time


def optimize_trip(
    time_matrix,
    service_times,
    time_windows,
    trip_start,
    trip_end,
    tolerance=30,
    wait_weight=3,
    use_pruning=True
):
    best_path = []
    best_count = 0
    best_cost = float("inf")
    memo = {}
    nodes_explored = 0

    min_travel = 0

    if use_pruning and len(time_matrix) > 1:
        min_travel = min(
            time_matrix[i][j]
            for i in range(len(time_matrix))
            for j in range(len(time_matrix))
            if i != j
        )
    return_times = [time_matrix[node][0] for node in range(len(time_matrix))]
    def backtrack(current_node, current_time, visited, path, travel, wait):

        nonlocal best_path, best_count, best_cost, nodes_explored
        nodes_explored += 1
        return_travel = return_times[current_node]
        return_time = current_time + return_travel

        if return_time <= trip_end + tolerance:
            overtime = max(0, return_time - trip_end)
            cost = travel + return_travel + wait_weight * wait + 2 * overtime
            count = len(visited) - 1

            if count > best_count or (count == best_count and cost < best_cost):
                best_path = path + [0]
                best_count = count
                best_cost = cost

        reachable = 0

        for node in range(1, len(time_matrix)):
            if node not in visited:
                arrival = current_time + time_matrix[current_node][node]

                if arrival <= time_windows[node][1]:
                    reachable += 1

        max_possible_count = len(visited) - 1 + reachable
        if use_pruning and max_possible_count < best_count:
            return

        current_cost = travel + wait_weight * wait
        remaining = best_count - (len(visited) - 1)

        lower_bound = (remaining + 1) * min_travel
        if (
            use_pruning
            and remaining > 0
            and max_possible_count == best_count
            and current_cost + lower_bound >= best_cost
        ):
            return
        
        if use_pruning and len(visited) - 1 < best_count:
            reachable_nodes = [
                node
                for node in range(1, len(time_matrix))
                if node not in visited
                and current_time + time_matrix[current_node][node] <= time_windows[node][1]
            ]

            if reachable_nodes:
                min_next_travel = min(
                    time_matrix[current_node][node]
                    for node in reachable_nodes
                )

                if (
                    max_possible_count == best_count
                    and current_cost + min_next_travel >= best_cost
                ):
                    return


        if use_pruning and max_possible_count == best_count and current_cost >= best_cost:
            return
        if use_pruning:
        # Memoization - dominance pruning
            key = (current_node, frozenset(visited))

            if key not in memo:
                memo[key] = []

            for saved_time, saved_cost in memo[key]:
                if (
                    saved_time <= current_time
                    and saved_cost + wait_weight * (current_time - saved_time) <= current_cost
                ):
                    return

            memo[key] = [
                (saved_time, saved_cost)
                for saved_time, saved_cost in memo[key]
                if not ( current_time <= saved_time and
                         current_cost + wait_weight * (saved_time - current_time) <= saved_cost
                )
            ]

            memo[key].append((current_time, current_cost))

        candidates = [node for node in range(1, len(time_matrix))
                    if node not in visited]

        candidates.sort(
            key=lambda node: (
                max(
                    current_time + time_matrix[current_node][node],
                    time_windows[node][0]
                ) + service_times[node]
            )
        )

        for next_node in candidates:   
            if next_node not in visited:
                travel_time = time_matrix[current_node][next_node]
                arrival_time = current_time + travel_time
                service_time = service_times[next_node]
                window_start, window_end = time_windows[next_node]

                if arrival_time <= window_end:
                    wait_time = max(0, window_start - arrival_time)
                    new_time = arrival_time + wait_time + service_time

                    if new_time  <= trip_end + tolerance:
                        backtrack(
                            next_node,
                            new_time,
                            visited | {next_node},
                            path + [next_node],
                            travel + travel_time,
                            wait + wait_time
                        )


    backtrack(0, trip_start, {0}, [0], 0, 0)

    return best_path, best_count, best_cost, nodes_explored
