"""Interactive itinerary and synchronized Folium map (presentation only)."""

import html
import json

import folium
from folium import plugins
import requests
import streamlit as st
import streamlit.components.v1 as components

from services.routing import get_route_geometry


def _clock(minutes):
    hours, mins = divmod(int(minutes), 60)
    return f"{hours:02d}:{mins:02d}"


def _leg(previous, current, transport_matrix, time_matrix,
         walking_distances, driving_distances):
    mode = transport_matrix[previous][current]
    distance = (walking_distances if mode == "walking" else driving_distances)[previous][current]
    distance_label = f"{distance:.2f} km" if distance is not None else "Distance unavailable"
    color = "walk" if mode == "walking" else "drive"
    label = "Walking" if mode == "walking" else "Driving / taxi"
    return f'''<div class="leg {color}"><span class="leg-arrow">↓</span>
      <span>{'🚶' if color == 'walk' else '🚕'} {label}</span>
      <span class="leg-metrics">{distance_label} · {time_matrix[previous][current]} min</span></div>'''


def display_interactive_itinerary(places, coords, route, visits, path,
                                  transport_matrix, time_matrix,
                                  walking_distances, driving_distances,
                                  attractions_data, trip_start, trip_end):
    """Render the complete timeline + map in one HTML document for instant hover sync."""
    m = folium.Map(location=coords[0], zoom_start=13, tiles="OpenStreetMap",
                   zoom_control=True, control_scale=True)
    plugins.Fullscreen(position="topright").add_to(m)

    # DivIcon markers expose a stable stop ID to the shared HTML document.
    marker_nodes = list(path[:-1]) if len(path) > 1 else [0]
    for step, node in enumerate(marker_nodes):
        marker_markup = (f'<div class="route-pin" data-stop="{step}">'
                         f'{"⌂" if step == 0 else step}</div>')
        folium.Marker(
            coords[node], tooltip=f"{step}. {places[node]}",
            popup=folium.Popup(html.escape(places[node]), max_width=260),
            icon=folium.DivIcon(html=marker_markup, icon_size=(38, 38),
                                icon_anchor=(19, 19)),
        ).add_to(m)

    bounds = []
    for previous, current in zip(path, path[1:]):
        mode = transport_matrix[previous][current]
        try:
            geometry = get_route_geometry(coords[previous], coords[current], mode)
        except (requests.RequestException, ValueError, KeyError, TypeError) as exc:
            st.warning(f"Could not display a route segment: {exc}")
            continue
        folium.PolyLine(geometry, color="#16a34a" if mode == "walking" else "#2563eb",
                        weight=5, opacity=0.85).add_to(m)
        bounds.extend(geometry)
    if bounds:
        m.fit_bounds(bounds)
    elif coords:
        m.fit_bounds([coords[node] for node in marker_nodes])

    cards = [f'''<article class="stop-card" data-stop="0" tabindex="0" role="button"
        aria-label="Highlight starting point on map">
        <div class="card-top"><span class="stop-number">⌂</span><span class="eyebrow">STARTING POINT</span></div>
        <h3>{html.escape(places[0])}</h3><div class="times"><span>Departure <b>{_clock(trip_start)}</b></span></div>
        <div class="extra">Starting address: {html.escape(places[0])}</div></article>''']

    for index, visit in enumerate(visits, start=1):
        node = visit["node"]
        info = attractions_data[node - 1]
        if info["all_day"]:
            hours = "Open all day (within trip limits)"
        else:
            hours = f'{info["opening"].strftime("%H:%M")}–{info["closing"].strftime("%H:%M")}'
        cards.append(_leg(path[index - 1], node, transport_matrix, time_matrix,
                          walking_distances, driving_distances))
        waiting = (f'<span class="waiting">Waiting for opening: {visit["wait"]} min</span>'
                   if visit["wait"] else "")
        cards.append(f'''<article class="stop-card" data-stop="{index}" tabindex="0" role="button"
            aria-label="Highlight {html.escape(places[node], quote=True)} on map">
            <div class="card-top"><span class="stop-number">{index}</span><span class="eyebrow">STOP {index}</span></div>
            <h3>{html.escape(places[node])}</h3>
            <div class="times"><span>Arrival <b>{_clock(visit['arrival'])}</b></span>
            <span>Visit <b>{_clock(visit['start'])}–{_clock(visit['end'])}</b></span></div>
            {waiting}<div class="extra">Opening hours: <b>{html.escape(hours)}</b><br>
            Planned duration: <b>{info['duration']} min</b></div></article>''')

    if path and len(path) >= 2:
        cards.append(_leg(path[-2], 0, transport_matrix, time_matrix,
                          walking_distances, driving_distances))
        finish = route[-1][1]
        overtime = f'<div class="waiting">Overtime used: {finish - trip_end} min</div>' if finish > trip_end else ''
        cards.append(f'''<article class="stop-card return-card" data-stop="0" tabindex="0" role="button"
          aria-label="Highlight return location on map"><div class="card-top"><span class="stop-number">⌂</span>
          <span class="eyebrow">RETURN TO START</span></div><h3>{html.escape(places[0])}</h3>
          <div class="times"><span>Arrival <b>{_clock(finish)}</b></span></div>{overtime}</article>''')

    sidebar = f'''<aside id="trip-timeline" aria-label="Trip itinerary">
      <div class="timeline-heading"><h2>Your optimized itinerary</h2>
      <p>{len(visits)} attractions · Hover or tap a stop to highlight it on the map</p></div>
      <div class="timeline-cards">{''.join(cards)}</div></aside>'''

    styles = '''<style>
      html,body{height:100%;margin:0;font-family:system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
      .folium-map{position:absolute!important;left:39%!important;top:0!important;width:61%!important;height:100%!important}
      #trip-timeline{position:absolute;left:0;top:0;width:39%;height:100%;box-sizing:border-box;
        background:#f7f9fc;overflow-y:auto;border-right:1px solid #e2e8f0;z-index:1000;color:#18283d}
      .timeline-heading{position:sticky;top:0;z-index:2;background:#fff;padding:20px 18px 14px;border-bottom:1px solid #e7edf4}
      .timeline-heading h2{margin:0;font-size:19px;letter-spacing:-.5px}
      .timeline-heading p{font-size:12px;color:#64748b;margin:7px 0 0;line-height:1.5}
      .timeline-cards{padding:18px 16px 30px}
      .stop-card{background:#fff;border:1px solid #e1e8f0;border-radius:16px;padding:15px;
        box-shadow:0 2px 8px #0f172a09;transition:transform .18s,border-color .18s,box-shadow .18s;
        cursor:pointer;outline-offset:3px}
      .stop-card:hover,.stop-card:focus,.stop-card.active{transform:scale(1.025);border-color:#f59e0b;
        box-shadow:0 8px 22px #0f172a1a;position:relative;z-index:1}
      .card-top{display:flex;align-items:center;gap:9px}
      .stop-number{display:inline-flex;align-items:center;justify-content:center;width:29px;height:29px;
        background:#eaf2ff;color:#2563eb;border-radius:50%;font-weight:800;font-size:13px}
      .eyebrow{font-size:10px;font-weight:750;letter-spacing:1px;color:#64748b}
      .stop-card h3{font-size:14px;line-height:1.4;margin:10px 0;overflow-wrap:anywhere}
      .times{display:flex;flex-wrap:wrap;gap:9px 14px;font-size:12px;color:#64748b}
      .times b{display:block;color:#17263c;font-size:13px;margin-top:3px}
      .waiting{display:block;margin-top:10px;font-size:11px;color:#9a6700}
      .extra{max-height:0;opacity:0;overflow:hidden;font-size:12px;color:#475569;line-height:1.8;
        transition:max-height .2s,opacity .2s,margin .2s}
      .stop-card:hover .extra,.stop-card:focus .extra,.stop-card.active .extra{max-height:120px;opacity:1;margin-top:12px;padding-top:9px;border-top:1px solid #edf2f7}
      .leg{margin:8px 0 8px 24px;padding:9px 0 9px 14px;border-left:3px solid;display:flex;align-items:center;
        flex-wrap:wrap;gap:5px 9px;font-size:11px;font-weight:700}
      .leg.walk{color:#15803d;border-color:#22c55e}.leg.drive{color:#1d4ed8;border-color:#3b82f6}
      .leg-arrow{font-size:18px}.leg-metrics{margin-left:auto;font-weight:600}
      .route-pin{height:34px;width:34px;display:flex;align-items:center;justify-content:center;border-radius:50%;
        border:3px solid white;background:#2563eb;color:white;font-weight:800;font-size:14px;
        box-shadow:0 3px 10px #0004;transition:transform .16s,background .16s,box-shadow .16s}
      .route-pin.highlight{transform:scale(1.48);background:#f59e0b;box-shadow:0 0 0 6px #f59e0b44,0 4px 15px #0005;z-index:999}
      @media(max-width:640px){.folium-map{left:0!important;top:48%!important;width:100%!important;height:52%!important}
        #trip-timeline{width:100%;height:48%;border-right:0;border-bottom:1px solid #e2e8f0}}
    </style>'''
    script = '''<script>
      (function(){
        const cards=[...document.querySelectorAll('.stop-card')];
        const pins=[...document.querySelectorAll('.route-pin')];
        let selected=null;
        function highlight(id){
          cards.forEach(c=>c.classList.toggle('active',c===selected && c.dataset.stop===id));
          pins.forEach(p=>p.classList.toggle('highlight',p.dataset.stop===id));
        }
        function clear(){selected=null;cards.forEach(c=>c.classList.remove('active'));
          pins.forEach(p=>p.classList.remove('highlight'));}
        cards.forEach(c=>{
          c.addEventListener('mouseenter',()=>highlight(c.dataset.stop));
          c.addEventListener('mouseleave',()=>{if(selected){highlight(selected.dataset.stop)}else{clear()}});
          c.addEventListener('focus',()=>highlight(c.dataset.stop));
          c.addEventListener('blur',()=>{if(!selected)clear()});
          c.addEventListener('click',()=>{if(selected===c){clear()}else{selected=c;highlight(c.dataset.stop)}});
          c.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();c.click()}});
        });
        pins.forEach(p=>{
          p.addEventListener('mouseenter',()=>highlight(p.dataset.stop));
          p.addEventListener('mouseleave',()=>{if(selected)highlight(selected.dataset.stop);else clear()});
        });
      })();
    </script>'''
    document = m.get_root().render()
    document = document.replace('</head>', styles + '</head>')
    # Folium creates its markers in scripts AFTER </body>. Insert our handlers
    # after Folium's initialization, otherwise .route-pin elements do not exist yet.
    document = document.replace('</body>', sidebar + '</body>')
    document = document.replace('</html>', script + '</html>')
    components.html(document, height=690, scrolling=False)
