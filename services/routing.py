
import streamlit as st
import requests
from services.routing_matrix import fetch_route_matrix
import polyline


VALHALLA_URL = "https://valhalla1.openstreetmap.de/sources_to_targets"
BATCH_SIZE = 8


@st.cache_data(ttl=3600)
def get_route_matrix(coords, costing):
    return fetch_route_matrix(coords, costing, requests.post, VALHALLA_URL, BATCH_SIZE)


@st.cache_data(ttl=3600)
def get_route_geometry(start, end, mode):
    payload = {
        "locations": [
            {"lat": start[0], "lon": start[1]},
            {"lat": end[0], "lon": end[1]}
        ],
        "costing": "pedestrian" if mode == "walking" else "auto",
        "units": "kilometers"
    }

    response = requests.post(
        "https://valhalla1.openstreetmap.de/route",
        json=payload,
        headers={"X-Client-Id": "smart-trip-planner-dev"},
        timeout=30
    )
    response.raise_for_status()

    legs = response.json()["trip"]["legs"]
    return [
        point
        for leg in legs
        for point in polyline.decode(leg["shape"], precision=6)
    ]