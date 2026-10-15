import streamlit as st
import requests
from geopy.distance import geodesic


@st.cache_data(ttl=86400)
def get_coordinates(place_name):
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": place_name, "format": "json", "limit": 1}
    headers = {"User-Agent": "SmartTripPlanner/1.0"}

    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        results = response.json()
        if results:
            return float(results[0]["lat"]), float(results[0]["lon"])
    except (requests.RequestException, ValueError, KeyError):
        pass
    return None


def validate_distances(places, coords, max_distance_km=15):
    # Check the straight-line distance between every pair of destinations.
    for i in range(len(coords)):
        for j in range(i + 1, len(coords)):
            distance = geodesic(coords[i], coords[j]).km
            if distance > max_distance_km:
                return False, (
                    f"{places[i]} and {places[j]} are {distance:.1f} km apart. "
                    f"Maximum allowed: {max_distance_km} km."
                )
    return True, None