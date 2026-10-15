"""Valhalla matrix batching, independent of Streamlit for unit testing."""

import math


def fetch_route_matrix(coords, costing, post, url, batch_size=8):
    """Return distance (km) and travel time (rounded-up minutes) matrices."""
    if batch_size < 1:
        raise ValueError("batch_size must be positive")
    n = len(coords)
    if not n:
        return [], []

    locations = [{"lat": lat, "lon": lon} for lat, lon in coords]
    distances = [[None] * n for _ in range(n)]
    times = [[None] * n for _ in range(n)]

    for source_start in range(0, n, batch_size):
        for target_start in range(0, n, batch_size):
            sources = locations[source_start:source_start + batch_size]
            targets = locations[target_start:target_start + batch_size]
            response = post(
                url,
                json={
                    "sources": sources,
                    "targets": targets,
                    "costing": costing,
                    "units": "kilometers",
                },
                headers={"X-Client-Id": "smart-trip-planner-dev"},
                timeout=30,
            )
            response.raise_for_status()
            result = response.json()["sources_to_targets"]
            if len(result) != len(sources) or any(
                len(row) != len(targets) for row in result
            ):
                raise ValueError("Invalid Valhalla matrix dimensions.")
            for i, row in enumerate(result):
                for j, cell in enumerate(row):
                    global_i = source_start + i
                    global_j = target_start + j
                    if (cell is None or cell.get("distance") is None
                            or cell.get("time") is None):
                        raise ValueError(
                            f"No route found between locations {global_i} and {global_j}."
                        )
                    distances[global_i][global_j] = float(cell["distance"])
                    times[global_i][global_j] = math.ceil(float(cell["time"]) / 60)

    return distances, times
