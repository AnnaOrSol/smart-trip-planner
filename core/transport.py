
def build_transport_matrix(
    walking_distances,
    walking_times,
    driving_distances,
    driving_times,
    max_walk_km,
    taxi_wait=5,
    preference="Prefer walking"
):
    n = len(walking_distances)

    time_matrix = [[0] * n for _ in range(n)]
    transport_matrix = [[None] * n for _ in range(n)]

    for i in range(n):
        for j in range(n):
            if i == j:
                continue

            walk_dist = walking_distances[i][j]
            walk_time = walking_times[i][j]
            drive_dist = driving_distances[i][j]
            drive_time = driving_times[i][j]

            can_walk = (
                walk_dist is not None
                and walk_time is not None
            )

            can_drive = (
                drive_dist is not None
                and drive_time is not None
            )

            taxi_time = (
                drive_time + taxi_wait
                if can_drive else float("inf")
            )

            if preference == "Prefer walking":
                use_walking = (
                    can_walk
                    and walk_dist <= max_walk_km
                )
            elif preference == "Fastest route":
                use_walking = (
                    can_walk
                    and walk_time <= taxi_time
                )
            else:
                raise ValueError(
                    f"Unknown transport preference: {preference}"
                )

            if use_walking:
                time_matrix[i][j] = walk_time
                transport_matrix[i][j] = "walking"

            elif can_drive:
                time_matrix[i][j] = taxi_time
                transport_matrix[i][j] = "taxi"

            elif can_walk:
                # Walking is the only available route.
                time_matrix[i][j] = walk_time
                transport_matrix[i][j] = "walking"

            else:
                raise ValueError(
                    f"No walking or driving route between {i} and {j}."
                )

    return time_matrix, transport_matrix
