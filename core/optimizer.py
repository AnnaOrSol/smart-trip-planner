from ortools.constraint_solver import routing_enums_pb2, pywrapcp


def solve_trip(locations, time_matrix, service_times, time_windows):
    n = len(locations)
    if (len(service_times) != n or len(time_windows) != n or
            len(time_matrix) != n or any(len(row) != n for row in time_matrix)):
        raise ValueError("Input dimensions do not match.")

    manager = pywrapcp.RoutingIndexManager(n, 1, 0)
    routing = pywrapcp.RoutingModel(manager)

    def time_callback(from_idx, to_idx):
        i = manager.IndexToNode(from_idx)
        j = manager.IndexToNode(to_idx)
        return time_matrix[i][j] + service_times[i]

    transit_idx = routing.RegisterTransitCallback(time_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_idx)

    # Allow up to 60 minutes of waiting and a 600-minute trip horizon.
    routing.AddDimension(transit_idx, 60, 600, False, "Time")
    time_dim = routing.GetDimensionOrDie("Time")
    time_dim.CumulVar(routing.Start(0)).SetValue(0)

    # Apply arrival time windows to destinations.
    for i in range(1, n):
        idx = manager.NodeToIndex(i)
        time_dim.CumulVar(idx).SetRange(*time_windows[i])

    # The first location is both the start and end of the trip.
    depot_start, depot_end = time_windows[0]
    if not (depot_start <= 0 <= depot_end):
        return []
    time_dim.CumulVar(routing.End(0)).SetRange(0, depot_end)

    search_params = pywrapcp.DefaultRoutingSearchParameters()
    search_params.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    search_params.local_search_metaheuristic = routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    search_params.time_limit.FromSeconds(10)

    solution = routing.SolveWithParameters(search_params)
    if not solution:
        return []

    route = []
    index = routing.Start(0)
    while not routing.IsEnd(index):
        node = manager.IndexToNode(index)
        arrival = solution.Min(time_dim.CumulVar(index))
        route.append((node, arrival))
        index = solution.Value(routing.NextVar(index))

    route.append((manager.IndexToNode(index), solution.Min(time_dim.CumulVar(index))))
    return route