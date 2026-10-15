# Verification status and review notes

## What was verified

- The uploaded archive contains 33 pytest test functions (per the user's successful run; this packaging environment did not rerun the suite).
- `tests/test_dp_exhaustive_comparison.py` contains 500 deterministic randomized small-instance comparisons against exhaustive search.
- `tests/test_held_karp.py` and `tests/test_strategy_selector.py` cover the specialized optimizer and dispatch.
- The mathematical documents were reviewed against the included implementations.

## Important assumptions and limitations

1. The optimized DP's `arrival > latest_start` check is correct for normalized windows with `opening <= latest_start`, because `max(arrival, opening) <= latest_start` then follows. The fixed-hours UI validates this precondition.
2. The UI's all-day case sets `opening=trip_start` and `latest_start=trip_end+tolerance-duration`, but does not explicitly reject a duration exceeding the entire allowed horizon. The optimizer may return an empty route; standalone callers should normalize and validate windows.
3. The `dominates` argument relies on static nonnegative travel/service times and nonnegative waiting penalty. When all remaining attractions are already open, an earlier no-more-expensive state is safe. Otherwise the cost margin `wait_weight*(t_B-t_A)` conservatively bounds extra waiting for an identical continuation.
4. The Held–Karp selection test is a **sufficient**, not necessary, condition for ignoring opening windows.
5. The separate custom/backtracking and OR-Tools implementations are not covered by the optimized DP's proof; the system's primary selector chooses between constrained DP and Held–Karp.
6. The current tests support the implementation, but do not constitute a proof for arbitrary invalid input, external routing failures, or the alternative optimizers.

## Suggested final verification

On a supported Python environment, run `python -m pip install -r requirements.txt`, `python -m pytest tests/ -v`, and `python -m streamlit run app.py`. Test both an unrestricted itinerary (Held–Karp) and a constrained-window itinerary (DP).
