"""Turn an optimizer path into an arrival and visit schedule."""


def build_schedule(path, time_matrix, service_times, time_windows, trip_start):
    """Return map-compatible (node, visit_start) tuples and detailed visit data."""
    if not path:
        return [], []

    route = [(0, trip_start)]
    visits = []
    departure = trip_start

    for previous_node, node in zip(path, path[1:]):
        arrival = departure + time_matrix[previous_node][node]

        if node == 0:
            route.append((0, arrival))
            break

        visit_start = max(arrival, time_windows[node][0])
        visit_end = visit_start + service_times[node]
        visits.append({
            "node": node,
            "arrival": arrival,
            "start": visit_start,
            "end": visit_end,
            "wait": visit_start - arrival,
        })
        route.append((node, visit_start))
        departure = visit_end

    return route, visits
