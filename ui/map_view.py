
import folium
import requests
import streamlit as st
import streamlit.components.v1 as components
from folium import plugins

from services.routing import get_route_geometry


def display_route_map(places, coords, route, transport_matrix):
    st.subheader("📍 Route Map")

    m = folium.Map(
        location=coords[0],
        zoom_start=14,
        tiles="OpenStreetMap",
        zoom_control=True,
        control_scale=True
    )

    # Add fullscreen and zoom controls.
    plugins.Fullscreen(position="topright").add_to(m)
    folium.plugins.MiniMap(toggle_display=True).add_to(m)

    # Add numbered markers for each destination.
    for step, (node, _) in enumerate(route[:-1]):
        marker_html = f"""
        <div style="
            background:#2563EB;
            color:white;
            border:3px solid white;
            border-radius:50%;
            width:34px;
            height:34px;
            display:flex;
            align-items:center;
            justify-content:center;
            font-weight:bold;
            font-size:14px;
            box-shadow:0 3px 10px #0003;
        ">{step + 1}</div>
        """

        folium.Marker(
            location=coords[node],
            popup=places[node],
            tooltip=f"{step + 1}. {places[node]}",
            icon=folium.DivIcon(
                html=marker_html,
                icon_size=(34, 34),
                icon_anchor=(17, 17)
            )
        ).add_to(m)

    # Draw actual walking and driving routes, including the return.
    route_bounds = []

    for step in range(len(route) - 1):
        from_node = route[step][0]
        to_node = route[step + 1][0]
        mode = transport_matrix[from_node][to_node]

        try:
            geometry = get_route_geometry(
                coords[from_node],
                coords[to_node],
                mode
            )
        except (requests.RequestException, ValueError, KeyError, TypeError) as e:
            st.warning(
                f"Unable to display route from {places[from_node]} "
                f"to {places[to_node]}: {e}"
            )
            continue

        color = "#10B981" if mode == "walking" else "#6366F1"
        label = "Walking" if mode == "walking" else "Taxi"

        folium.PolyLine(
            geometry,
            color=color,
            weight=5,
            opacity=0.9,
            tooltip=f"{label}: {places[from_node]} → {places[to_node]}"
        ).add_to(m)

        route_bounds.extend(geometry)

    # Fit the map to the complete route.
    if route_bounds:
        m.fit_bounds(route_bounds)
    else:
        m.fit_bounds(coords)

    components.html(m._repr_html_(), height=550)
