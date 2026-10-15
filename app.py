
import streamlit as st
import requests
from datetime import time
from core.strategies.base import TripProblem
from core.strategies.selector import OptimizerSelector
from services.geocoding import get_coordinates, validate_distances
from services.routing import get_route_matrix
from core.transport import build_transport_matrix
from ui.interactive_itinerary import display_interactive_itinerary
from ui.schedule import build_schedule
from core.route_validator import validate_route

st.set_page_config(page_title="Day Trip Planner", layout="wide")
st.markdown("""<style>
/* Light presentation. Keep Streamlit's widget structure and behavior intact. */
:root { --trip-accent:#168b83; --trip-ink:#263b42; --trip-muted:#61757c; --trip-line:#e5ebe9; }
html, body, [data-testid="stApp"], [data-testid="stAppViewContainer"],
[data-testid="stMain"], .stApp { background:#fbfcfa !important; color:var(--trip-ink) !important; }
[data-testid="stHeader"] {background:rgba(251,252,250,.94) !important;}
.block-container {max-width:1190px; padding-top:2rem; padding-bottom:4rem;}
h1,h2,h3,p {letter-spacing:-.015em;}
h1,h2,h3, [data-testid="stMarkdownContainer"] h3 {color:var(--trip-ink) !important;}
/* Only actual bordered containers, not every nested vertical block. */
[data-testid="stVerticalBlockBorderWrapper"] > div {
 border-radius:16px !important; border-color:var(--trip-line) !important;
 background:#fff !important;
}
/* Streamlit may be configured for dark mode. Give controls an explicit light surface
   AND readable foreground instead of recoloring only one of them. */
[data-testid="stButton"] button,
[data-testid="stBaseButton-secondary"],
[data-testid="stBaseButton-tertiary"] {
 background:#fff !important; color:var(--trip-ink) !important;
 border:1px solid #d6e3df !important; border-radius:10px !important;
}
[data-testid="stButton"] button * {color:inherit !important;}
[data-testid="stButton"] button:hover:not(:disabled) {border-color:var(--trip-accent) !important; color:var(--trip-accent) !important;}
[data-testid="stButton"] button[kind="primary"], [data-testid="stBaseButton-primary"] {
 background:var(--trip-accent) !important; color:#fff !important; border-color:var(--trip-accent) !important;
}
[data-testid="stButton"] button:disabled {opacity:.5;}
[data-testid="stTextInput"] [data-baseweb="input"],
[data-testid="stNumberInput"] [data-baseweb="input"],
[data-testid="stTimeInput"] [data-baseweb="input"],
[data-testid="stTimeInput"] [data-baseweb="select"],
[data-testid="stSelectbox"] [data-baseweb="select"] {
 background:#fff !important; color:var(--trip-ink) !important; border-radius:10px !important;
}
[data-testid="stTextInput"] input, [data-testid="stNumberInput"] input,
[data-testid="stTimeInput"] input, [data-testid="stTimeInput"] [data-baseweb="input"] *,
[data-testid="stTextInput"] [data-baseweb="input"] *,
[data-testid="stNumberInput"] [data-baseweb="input"] * {
 background:transparent !important; color:var(--trip-ink) !important;
}
[data-testid="stExpander"] {border:1px solid var(--trip-line) !important; border-radius:12px !important; background:#fff !important;}
[data-testid="stExpander"] summary {background:#fff !important; color:var(--trip-ink) !important;}
[data-testid="stExpander"] summary *, [data-testid="stExpander"] [data-testid="stMarkdownContainer"] * {color:var(--trip-ink) !important;}
[data-testid="stWidgetLabel"] *, [data-testid="stRadio"] label *,
[data-testid="stSlider"] label *, [data-testid="stCheckbox"] label * {color:var(--trip-ink) !important;}
[data-testid="stCaptionContainer"] * {color:var(--trip-muted) !important;}
.st-key-add_stop_top button {font-weight:600;}
.st-key-plan_cta button {min-height:3.1rem; padding:.6rem 1.7rem; font-size:1rem; font-weight:650; border-radius:12px !important;}
.trip-hero {padding:10px 0 20px; margin-bottom:12px; border-bottom:1px solid var(--trip-line);}
.trip-hero .eyebrow {font-size:.88rem;letter-spacing:.09em;font-weight:700;color:var(--trip-accent);text-transform:uppercase;margin-bottom:10px;line-height:1.5;}
.trip-hero h1 {color:var(--trip-ink) !important;font-size:2.15rem !important;line-height:1.3;margin:0 0 9px;font-weight:750;overflow:visible;}
.trip-hero p {color:var(--trip-muted);margin:0;font-size:.96rem;}
.trip-section {display:flex;align-items:center;gap:10px;margin:23px 0 12px;}
.trip-section .symbol {display:inline-flex;align-items:center;justify-content:center;width:31px;height:31px;background:#e8f5f1;border-radius:9px;font-size:17px;color:var(--trip-accent);}
.trip-section .title {font-weight:730;color:var(--trip-ink);font-size:1.27rem;}
.trip-section .sub {font-size:.83rem;color:var(--trip-muted);margin-top:2px;}
.trip-chip {display:inline-block;background:#eaf5f1;color:#24766d;border-radius:999px;padding:6px 12px;font-size:.78rem;font-weight:650;}
.trip-stop-name {font-size:.92rem;font-weight:670;color:var(--trip-ink);line-height:1.4;min-height:39px;overflow-wrap:anywhere;}
.trip-stop-meta {color:var(--trip-muted);font-size:.79rem;margin-top:6px;}
.trip-cta-caption {text-align:center;color:var(--trip-muted);font-size:.9rem;margin-bottom:13px;}
@media (max-width:700px) {
 .block-container {padding:1rem .8rem 3rem;}
 .trip-hero h1 {font-size:1.7rem !important;}
 .trip-section .title {font-size:1.15rem;}
}
</style>""", unsafe_allow_html=True)
st.markdown("""<div class="trip-hero">
  <div class="eyebrow">SMART TRIP PLANNER</div>
  <h1>Plan a lovely day out.</h1>
  <p>Choose your stops. We'll find the best way to explore them.</p>
</div>""", unsafe_allow_html=True)

def reset_attractions():
    for key in list(st.session_state.keys()):
        if key.startswith((
            "name_",
            "duration_",
            "all_day_",
            "opening_",
            "closing_",
            "_edit_",
            "data_",
        )):
            del st.session_state[key]

    st.session_state.attractions = [
        {
            "id": i + 1,
            "name": name,
            "duration": duration,
        }
        for i, (name, duration) in enumerate(DEFAULT_ATTRACTIONS)
    ]

    st.session_state.next_attraction_id = len(DEFAULT_ATTRACTIONS) + 1
    st.session_state.attraction_page = 0

def to_minutes(value):
    return value.hour * 60 + value.minute

def format_time(minutes):
    hours, mins = divmod(int(minutes), 60)
    return f"{hours:02d}:{mins:02d}"



# A compact, single-screen trip dashboard.
settings_col, location_col = st.columns([1.05, 1], gap="large")
with settings_col:
    with st.container(border=True, key="top_day_card"):
        st.markdown("#### ☀️ Your day")
        start_col, end_col = st.columns(2)
        with start_col:
            trip_start_time = st.time_input("Start", value=time(9, 0))
        with end_col:
            trip_end_time = st.time_input("Finish", value=time(18, 0))
        with st.expander("⚙️ More day settings", expanded=False):
            tolerance = st.number_input(
                "Allowed overtime (minutes)", min_value=0, max_value=180,
                value=30, step=5,
            )

with location_col:
    with st.container(border=True, key="top_location_card"):
        st.markdown("#### 📍 Starting point")
        starting_point = st.text_input(
            "Hotel or starting address", value="Rothschild Boulevard, Tel Aviv",
            placeholder="Where does your day begin?",
        )
        st.caption("Your route starts here.")

trip_start = to_minutes(trip_start_time)
trip_end = to_minutes(trip_end_time)

with st.expander("🚶 Transportation preferences", expanded=False):
    transport_preference = st.radio(
        "How should transportation be selected?",
        options=["Prefer walking", "Fastest route"],
        format_func=lambda option: {
            "Prefer walking": "🚶 Prefer walking within my distance limit",
            "Fastest route": "⚡ Choose the fastest transportation",
        }[option],
        horizontal=True,
    )
    max_walk_km = st.slider(
        "Maximum walking distance between destinations (km)",
        min_value=0.5, max_value=5.0, value=1.5, step=0.1,
        disabled=transport_preference == "Fastest route",
    )

MAX_ATTRACTIONS_PER_DAY = 15
DEFAULT_ATTRACTIONS = [
    ("Carmel Market, Tel Aviv, Israel", 60),
    ("Dizengoff Center, Tel Aviv, Israel", 45),
    ("Habima Square, Tel Aviv, Israel", 30),
    ("Sarona Market, Tel Aviv, Israel", 60),
    ("Tel Aviv Museum of Art, Tel Aviv, Israel", 90),
    ("Rabin Square, Tel Aviv, Israel", 20),
    ("Gordon Beach, Tel Aviv, Israel", 45),
    ("Old Jaffa Port, Tel Aviv, Israel", 60),
    ("Jaffa Clock Tower, Tel Aviv, Israel", 20),
    ("Neve Tzedek, Tel Aviv, Israel", 45),
    ("Charles Clore Park, Tel Aviv, Israel", 30),
    ("Independence Hall, Tel Aviv, Israel", 30),
    ("Yarkon Park, Tel Aviv, Israel", 60),
    ("Bloch 47, Tel Aviv, Israel", 45),
    ("Tel Aviv Port, Tel Aviv, Israel", 60),
]
if "attractions" not in st.session_state:
    st.session_state.attractions = [
        {
            "id": i + 1,
            "name": name,
            "duration": duration,
        }
        for i, (name, duration) in enumerate(DEFAULT_ATTRACTIONS)
    ]

    st.session_state.next_attraction_id = len(DEFAULT_ATTRACTIONS) + 1


def add_attraction():
    if len(st.session_state.attractions) >= MAX_ATTRACTIONS_PER_DAY:
        return
    new_id = st.session_state.next_attraction_id
    st.session_state.attractions.append({"id": new_id})
    st.session_state.next_attraction_id += 1
    initialize_attraction(st.session_state.attractions[-1])
    st.session_state.attraction_page = (len(st.session_state.attractions) - 1) // 4
    st.session_state.open_editor_for = new_id


def clear_all_attractions():
    for item in st.session_state.attractions:
        aid = item["id"]
        for field in ("name", "duration", "all_day", "opening", "closing"):
            st.session_state.pop(f"data_{field}_{aid}", None)
            st.session_state.pop(f"_edit_{field}_{aid}", None)
    st.session_state.attractions = []
    st.session_state.attraction_page = 0
    st.session_state.pop("open_editor_for", None)


def remove_attraction(attraction_id):
    st.session_state.attractions = [
        item for item in st.session_state.attractions if item["id"] != attraction_id
    ]
    for field in ("name", "duration", "all_day", "opening", "closing"):
        st.session_state.pop(f"data_{field}_{attraction_id}", None)
        st.session_state.pop(f"_edit_{field}_{attraction_id}", None)


st.markdown("""<div class="trip-section"><span class="symbol">✦</span><div><div class="title">Places to explore</div><div class="sub">Curate your perfect day, one stop at a time</div></div></div>""", unsafe_allow_html=True)
stops_heading, stops_action = st.columns([4, 1.2], vertical_alignment="center")
with stops_heading:
    st.markdown(f"<span class=\"trip-chip\">{len(st.session_state.attractions)} / {MAX_ATTRACTIONS_PER_DAY} stops selected</span>", unsafe_allow_html=True)
with stops_action:
    with st.container(key="add_stop_top"):
        if st.button("＋ Add attraction", key="add_stop_always", disabled=len(st.session_state.attractions) >= MAX_ATTRACTIONS_PER_DAY, use_container_width=True):
            add_attraction()
            st.rerun()

# Keep the actual attraction data in persistent state, independently of which
# carousel page is currently visible. Streamlit discards hidden widget keys.
def initialize_attraction(item):
    aid = item["id"]
    defaults = {
        "name": item.get("name", ""),
        "duration": item.get("duration", 60),
        "all_day": True,
        "opening": time(9, 0),
        "closing": time(17, 0),
    }
    for field, default in defaults.items():
        st.session_state.setdefault(f"data_{field}_{aid}", default)


def prepare_attraction_editor(aid):
    """Create temporary widget values from persistent attraction data."""
    for field in ("name", "duration", "all_day", "opening", "closing"):
        st.session_state[f"_edit_{field}_{aid}"] = st.session_state[f"data_{field}_{aid}"]


@st.dialog("Edit attraction", width="small")
def attraction_editor(aid):
    name_key = f"_edit_name_{aid}"
    duration_key = f"_edit_duration_{aid}"
    all_day_key = f"_edit_all_day_{aid}"
    st.text_input("Attraction name or address", key=name_key)
    st.number_input("Visit duration (minutes)", min_value=5, max_value=480, step=5, key=duration_key)
    st.checkbox("Open all day", key=all_day_key)
    if not st.session_state[all_day_key]:
        st.time_input("Opening time", key=f"_edit_opening_{aid}")
        st.time_input("Closing time", key=f"_edit_closing_{aid}")
    if st.button("Done", type="primary", use_container_width=True, key=f"done_{aid}"):
        for field in ("name", "duration", "all_day", "opening", "closing"):
            st.session_state[f"data_{field}_{aid}"] = st.session_state[f"_edit_{field}_{aid}"]
        st.rerun()


@st.dialog("Remove attraction?")
def confirm_remove(aid):
    name = st.session_state.get(f"data_name_{aid}", "this attraction")
    st.write(f"Remove **{name or 'this attraction'}** from your itinerary?")
    yes, no = st.columns(2)
    with yes:
        if st.button("Remove", type="primary", use_container_width=True, key=f"confirm_remove_{aid}"):
            remove_attraction(aid)
            st.rerun()
    with no:
        if st.button("Cancel", use_container_width=True, key=f"cancel_remove_{aid}"):
            st.rerun()


for item in st.session_state.attractions:
    initialize_attraction(item)

# Four equal-width tiles per page, including the add tile at the end.
CARDS_PER_PAGE = 4
show_add = len(st.session_state.attractions) < MAX_ATTRACTIONS_PER_DAY
items = [("attraction", item) for item in st.session_state.attractions]
if show_add:
    items.append(("add", None))
page_count = max(1, (len(items) + CARDS_PER_PAGE - 1) // CARDS_PER_PAGE)
st.session_state.setdefault("attraction_page", 0)
st.session_state.attraction_page = min(st.session_state.attraction_page, page_count - 1)

# Compact navigation and consistent-height attraction cards.
st.markdown("""<style>
/* Limit this styling to the attraction card area where supported by Streamlit. */
div[data-testid="stHorizontalBlock"] button[kind="secondary"] {border-radius: 10px;}
</style>""", unsafe_allow_html=True)
nav_prev, nav_title, nav_next = st.columns([0.7, 5, 0.7], vertical_alignment="center")
with nav_prev:
    if st.button("‹", key="carousel_prev", disabled=st.session_state.attraction_page == 0, help="Previous attractions", use_container_width=True):
        st.session_state.attraction_page -= 1
        st.rerun()
with nav_title:
    st.markdown(f"<div style='text-align:center;color:#64748b;font-size:13px'> {st.session_state.attraction_page + 1} / {page_count} </div>", unsafe_allow_html=True)
with nav_next:
    if st.button("›", key="carousel_next", disabled=st.session_state.attraction_page >= page_count - 1, help="Next attractions", use_container_width=True):
        st.session_state.attraction_page += 1
        st.rerun()

visible = items[st.session_state.attraction_page * CARDS_PER_PAGE:(st.session_state.attraction_page + 1) * CARDS_PER_PAGE]
# Center the final partial carousel page rather than leaving one card stuck to the left.
visible_count = len(visible)
if visible_count < CARDS_PER_PAGE:
    side = (CARDS_PER_PAGE - visible_count) / 2
    centered_columns = st.columns([side] + [1] * visible_count + [side], gap="small")
    columns = centered_columns[1:-1]
else:
    columns = st.columns(CARDS_PER_PAGE, gap="small")
for col, (kind, item) in zip(columns, visible):
    with col:
        with st.container(border=True, height=178):
            if kind == "add":
                st.markdown("<div style='text-align:center;font-size:25px;color:#64748b;margin:8px 0 0'>＋</div>", unsafe_allow_html=True)
                if st.button("Add attraction", key="carousel_add", use_container_width=True):
                    add_attraction()
                    st.rerun()
                continue

            aid = item["id"]
            number = next(i + 1 for i, x in enumerate(st.session_state.attractions) if x["id"] == aid)
            name = st.session_state[f"data_name_{aid}"]
            duration = st.session_state[f"data_duration_{aid}"]
            all_day = st.session_state[f"data_all_day_{aid}"]
            head, edit, trash = st.columns([5, 1, 1], gap="small", vertical_alignment="center")
            with head:
                st.caption(f"#{number:02d}")
            with edit:
                if st.button("", icon=":material/edit:", key=f"edit_{aid}", help="Edit attraction", use_container_width=True):
                    prepare_attraction_editor(aid)
                    attraction_editor(aid)
            with trash:
                if st.button("", icon=":material/delete_outline:", key=f"remove_{aid}", help="Remove attraction", use_container_width=True):
                    confirm_remove(aid)
            st.markdown(f"<div class=\"trip-stop-name\">{__import__('html').escape(name or 'New attraction')}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class=\"trip-stop-meta\">◷ {duration} min &nbsp;·&nbsp; {'Open all day' if all_day else 'Custom hours'}</div>", unsafe_allow_html=True)

# Automatically open the edit dialog for a newly created attraction.
if st.session_state.get("open_editor_for") is not None:
    new_aid = st.session_state.pop("open_editor_for")
    prepare_attraction_editor(new_aid)
    attraction_editor(new_aid)

@st.dialog("Delete all attractions?")
def confirm_clear_all():
    st.warning("This will remove all attractions from your itinerary.")
    yes, no = st.columns(2)
    with yes:
        if st.button("Delete all", type="primary", key="confirm_clear_all"):
            clear_all_attractions()
            st.rerun()
    with no:
        if st.button("Cancel", key="cancel_clear_all"):
            st.rerun()


actions_col, _ = st.columns([1.4, 4])
with actions_col:
    st.button("🔄 Restore Default Attractions", on_click=reset_attractions, use_container_width=True)
    if st.button("Delete All Attractions", icon=":material/delete_sweep:",
                 disabled=not st.session_state.attractions, use_container_width=True):
        confirm_clear_all()

# Read ALL attractions, including those on other carousel pages.
attractions_data = []
for item in st.session_state.attractions:
    aid = item["id"]
    all_day = st.session_state[f"data_all_day_{aid}"]
    attractions_data.append({
        "name": st.session_state[f"data_name_{aid}"].strip(),
        "duration": st.session_state[f"data_duration_{aid}"],
        "all_day": all_day,
        "opening": None if all_day else st.session_state[f"data_opening_{aid}"],
        "closing": None if all_day else st.session_state[f"data_closing_{aid}"],
    })

places = [starting_point.strip()]
service_times = [0]
time_windows = [(0, 1440)]

for attraction in attractions_data:
    places.append(attraction["name"])
    service_times.append(attraction["duration"])

    if attraction["all_day"]:
        opening = trip_start
        latest_start = trip_end + tolerance - attraction["duration"]
    else:
        opening = to_minutes(attraction["opening"])
        latest_start = (
            to_minutes(attraction["closing"])
            - attraction["duration"]
        )

    time_windows.append((opening, latest_start))

st.markdown("---")
st.markdown("<h3 style='text-align:center; margin-bottom:0.2rem'>Ready for your day out?</h3>", unsafe_allow_html=True)
st.markdown("<p class='trip-cta-caption'>One click away from your personalized itinerary.</p>", unsafe_allow_html=True)
cta_left, cta_center, cta_right = st.columns([2, 1.5, 2])
with cta_center:
    with st.container(key="plan_cta"):
        plan_clicked = st.button("✨ Build my itinerary  →", type="primary", use_container_width=True)
if plan_clicked:

    if trip_end <= trip_start:
        st.error("Trip end must be later than trip start.")
        st.stop()

    if not starting_point.strip():
        st.error("Please enter a starting point.")
        st.stop()

    if not attractions_data:
        st.error("Please add at least one attraction.")
        st.stop()

    if len(attractions_data) > MAX_ATTRACTIONS_PER_DAY:
        st.error("You can select up to 15 attractions per day.")
        st.stop()

    if any(not attraction["name"] for attraction in attractions_data):
        st.error("Please enter a name for every attraction.")
        st.stop()

    for attraction in attractions_data:
        if attraction["all_day"]:
            continue

        opening = to_minutes(attraction["opening"])
        closing = to_minutes(attraction["closing"])

        if closing <= opening:
            st.error(
                f"Invalid opening hours for {attraction['name']}."
            )
            st.stop()

        if attraction["duration"] > closing - opening:
            st.error(
                f"Visit duration exceeds opening hours for "
                f"{attraction['name']}."
            )
            st.stop()

    with st.spinner("Calculating the optimal route..."):
        coords = []
        failed_places = []

        for place in places:
            coordinate = get_coordinates(place)

            if coordinate is None:
                failed_places.append(place)
                continue

            coords.append(coordinate)

        if failed_places:
            st.error(
                "Unable to find coordinates for: "
                + ", ".join(failed_places)
            )
            st.stop()

        valid, error = validate_distances(places, coords)

        if not valid:
            st.error(f"⚠️ {error}")
            st.stop()


        try:
            walking_distances, walking_times = get_route_matrix(
                coords, "pedestrian"
            )
            driving_distances, driving_times = get_route_matrix(
                coords, "auto"
            )

            matrix, transport_matrix = build_transport_matrix(
                walking_distances,
                walking_times,
                driving_distances,
                driving_times,
                max_walk_km,
                preference=transport_preference
            )

        except (requests.RequestException, ValueError, KeyError, TypeError) as e:
            st.error(f"Unable to calculate transport routes: {e}")
            st.stop()

        problem = TripProblem(
            time_matrix=matrix,
            service_times=service_times,
            time_windows=time_windows,
            trip_start=trip_start,
            trip_end=trip_end,
            tolerance=tolerance,
            wait_weight=3,
        )

        selector = OptimizerSelector()

        strategy = selector.select(problem)
        st.caption(
            f"Optimization algorithm: {type(strategy).__name__}"
        )

        path, visited_count, cost, states_explored = (
            strategy.optimize(problem)
        )

        if path:
            validation = validate_route(
                path=path,
                visited_count=visited_count,
                reported_cost=cost,
                time_matrix=matrix,
                service_times=service_times,
                time_windows=time_windows,
                trip_start=trip_start,
                trip_end=trip_end,
                tolerance=tolerance,
                wait_weight=3,
            )

            if not validation.valid:
                st.error("Optimizer returned an invalid route:")
                for error in validation.errors:
                    st.error(error)
                st.stop()

        if not path:
            st.error("No feasible route found.")
            st.stop()

        route, visits = build_schedule(
            path,
            matrix,
            service_times,
            time_windows,
            trip_start
        )

        with st.expander("🔍 Debug Information"):
            st.write("Path:", path)
            st.write("Visited Attractions:", visited_count)
            st.write("Cost:", cost)
            st.write("States Explored:", states_explored)
            st.write("Time Matrix:", matrix)
            st.write("Transport Matrix:", transport_matrix)

        st.subheader("🗺️ Your Interactive Trip Plan")
        st.success(
            f"Planned {visited_count} out of {len(attractions_data)} attractions."
        )
        if visited_count == 0:
            st.warning("No attractions fit the selected schedule and travel limits.")

        display_interactive_itinerary(
            places=places,
            coords=coords,
            route=route,
            visits=visits,
            path=path,
            transport_matrix=transport_matrix,
            time_matrix=matrix,
            walking_distances=walking_distances,
            driving_distances=driving_distances,
            attractions_data=attractions_data,
            trip_start=trip_start,
            trip_end=trip_end,
        )
