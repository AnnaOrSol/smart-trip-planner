# Smart Trip Planner 🗺️

A Python/Streamlit application that plans a one-day sightseeing itinerary using travel times, visit durations, attraction opening hours and an optional overtime allowance. It uses open mapping and routing services instead of Google Maps.

## What it optimizes

The optimizer prioritizes **the maximum number of visited attractions**, then **the minimum weighted cost** among routes with that visit count. The cost is total travel time + `wait_weight × waiting time` + `2 × overtime minutes`. Each route begins and ends at the chosen starting point. A visit must start by the attraction's *latest permissible start time* (`closing − duration`).

## Setup (macOS / Python 3.13)

```bash
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Use a Python version supported by OR-Tools; this project was tested by its author on Python 3.13.16. Geocoding and routing require internet access and the public Nominatim/Valhalla services; availability and rate limits are external to this repository.

## Tests

```bash
python -m pytest tests/ -v
```

The author reported **33 passing pytest tests** in the supplied snapshot. The test suite includes 500 seeded comparisons of the constrained DP with exhaustive enumeration of small valid instances. These are empirical checks, **not a substitute for mathematical proof**.

## Implementation overview

- `app.py` — Streamlit interface and input checks
- `services/` — geocoding and route-matrix retrieval
- `core/transport.py` — transport-time matrix construction
- `core/strategies/selector.py` — chooses between specialized Held–Karp and constrained DP
- `core/held_karp_optimizer.py` — subset DP for unrestricted attraction windows
- `core/dp_optimizer_optimized.py` — label-setting subset DP with dominance pruning for constrained windows
- `core/custom_optimizer.py`, `core/dp_optimizer.py`, `core/ortools_optimizer.py` — additional implementations for comparison and experiments
- `core/route_validator.py` — route consistency checks
- `tests/` — automated regression and optimizer comparisons
- `benchmarks/` — performance experiments

## Mathematical and technical documentation

- [Formal problem formulation](docs/problem_formulation.md)
- [Optimized DP correctness argument](docs/correctness_proof.md)
- [Held–Karp and strategy selection](docs/held_karp_and_strategy_selection.md)
- [Complexity analysis](docs/complexity_analysis.md)
- [Historical optimization development and benchmarks](docs/optimization.md)
- [Verification and remaining caveats](docs/verification_status.md)

## Known constraints

The optimized DP assumes finite nonnegative static travel times, nonnegative visit durations and weights, and normalized nonempty start windows. `app.py` checks fixed-hours attractions; **all-day attractions with durations longer than the entire allowed trip horizon are not explicitly rejected** before calling the optimizer. Direct library callers should validate inputs. The formal correctness arguments apply only under their stated assumptions.

The public routing API is not a guaranteed service-level dependency; failures or usage limits can prevent route generation.
