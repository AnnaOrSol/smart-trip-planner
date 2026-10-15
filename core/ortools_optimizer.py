from ortools.constraint_solver import routing_enums_pb2, pywrapcp


def optimize_trip_ortools(
    time_matrix,
    service_times,
    time_windows,
    trip_start,
    trip_end,
    tolerance=30,
    wait_weight=3,
    time_limit_seconds=10,
):
    n = len(time_matrix)

    manager = pywrapcp.RoutingIndexManager(n, 1, 0)
    routing = pywrapcp.RoutingModel(manager)

    def travel_callback(from_index, to_index):
        i = manager.IndexToNode(from_index)
        j = manager.IndexToNode(to_index)
        return int(time_matrix[i][j])

    travel_callback_index = routing.RegisterTransitCallback(
        travel_callback
    )

    routing.SetArcCostEvaluatorOfAllVehicles(
        travel_callback_index
    )

    def time_callback(from_index, to_index):
        i = manager.IndexToNode(from_index)
        j = manager.IndexToNode(to_index)

        return int(
            time_matrix[i][j] + service_times[i]
        )

    time_callback_index = routing.RegisterTransitCallback(
        time_callback
    )

    latest_end = trip_end + tolerance

    routing.AddDimension(
        time_callback_index,
        latest_end - trip_start,
        latest_end,
        False,
        "Time"
    )

    time_dimension = routing.GetDimensionOrDie("Time")

    start_index = routing.Start(0)
    end_index = routing.End(0)

    time_dimension.CumulVar(start_index).SetValue(
        trip_start
    )

    time_dimension.CumulVar(end_index).SetRange(
        trip_start,
        latest_end
    )

    # Penalize returning after the preferred trip end.
    time_dimension.SetCumulVarSoftUpperBound(
        end_index,
        trip_end,
        2
    )

    # Penalize waiting before attractions open.
    time_dimension.SetSlackCostCoefficientForAllVehicles(
        wait_weight
    )

    # Skipping an attraction must be more expensive
    # than any difference in travel/wait/overtime costs.
    max_travel = max(max(row) for row in time_matrix)

    skip_penalty = (
        (n + 1) * max_travel
        + wait_weight * (latest_end - trip_start)
        + 2 * tolerance
        + 1
    )

    for node in range(1, n):
        index = manager.NodeToIndex(node)

        opening, latest_start = time_windows[node]

        time_dimension.CumulVar(index).SetRange(
            max(trip_start, int(opening)),
            min(latest_end, int(latest_start))
        )

        routing.AddDisjunction(
            [index],
            int(skip_penalty)
        )

    search_params = pywrapcp.DefaultRoutingSearchParameters()

    search_params.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy
        .PATH_CHEAPEST_ARC
    )

    search_params.local_search_metaheuristic = (
        routing_enums_pb2.LocalSearchMetaheuristic
        .AUTOMATIC
    )

    search_params.time_limit.FromSeconds(
        time_limit_seconds
    )

    solution = routing.SolveWithParameters(search_params)

    if solution is None:
        return [], 0, float("inf"), 0

    path = []
    index = start_index

    while not routing.IsEnd(index):
        path.append(manager.IndexToNode(index))
        index = solution.Value(routing.NextVar(index))

    path.append(0)

    # Recalculate the objective exactly as DP does.
    current_time = trip_start
    travel_cost = 0
    waiting_cost = 0

    for i in range(1, len(path)):
        previous_node = path[i - 1]
        current_node = path[i]

        current_time += service_times[previous_node]

        travel = time_matrix[previous_node][current_node]
        current_time += travel
        travel_cost += travel

        if current_node != 0:
            opening = time_windows[current_node][0]
            waiting = max(0, opening - current_time)

            current_time += waiting
            waiting_cost += wait_weight * waiting

    overtime = max(0, current_time - trip_end)

    cost = travel_cost + waiting_cost + 2 * overtime

    visited_count = len(path) - 2

    return path, visited_count, cost, None