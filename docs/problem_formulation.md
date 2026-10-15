# Smart Trip Planner — Formal Problem Formulation

> Status: Reviewed against the supplied code. Proofs and caveats are documented separately; see `correctness_proof.md`, `held_karp_and_strategy_selection.md`, and `verification_status.md`.

## 1. Problem description

Given a depot and a set of candidate attractions, find a single-day route starting and ending at the depot. Each attraction may be visited at most once. Travel times, visit durations, attraction operating hours and a trip end-time tolerance constrain feasible routes.

The objective is **lexicographic**: (1) maximize the number of visited attractions; (2) among routes with the same number of attractions, minimize weighted travel, waiting and overtime cost.

## 2. Inputs and notation

- `V = {0, 1, ..., n}`: locations; `0` is the depot.
- `t_ij >= 0`: directed travel time from location `i` to `j` (the matrix need not be symmetric).
- `s_i >= 0`: service/visit duration for attraction `i`; `s_0 = 0`.
- `o_i`: opening time of attraction `i`.
- `c_i`: actual closing time of attraction `i`.
- `l_i = c_i - s_i`: latest permissible **start** of the visit.
- `T_s`: trip start time; `T_e`: preferred trip end time.
- `delta >= 0`: maximum permitted overtime; `L = T_e + delta`.
- `lambda >= 0`: waiting-time weight (default `3`).

For an all-day attraction, the application sets `o_i = T_s` and `l_i = L - s_i` rather than using real operating hours.

## 3. Route and time dynamics

A candidate route is `P = (0, v_1, ..., v_k, 0)` where all `v_r` are distinct attraction indices. Define `v_0 = v_{k+1} = 0`, and `F_0 = T_s`.

For each visit `r = 1, ..., k`:

\[
A_r = F_{r-1} + t_{v_{r-1},v_r}, \qquad
B_r = \max(A_r, o_{v_r}),
\]

\[
w_r = B_r - A_r = \max(0, o_{v_r}-A_r), \qquad
F_r = B_r + s_{v_r}.
\]

The return time is

\[
R(P) = F_k + t_{v_k,0}.
\]

For the empty route, `P = (0,0)`, define `R(P) = T_s + t_00` (normally `t_00 = 0`).

## 4. Feasibility constraints

1. Each attraction appears at most once.
2. **Latest visit start:** `B_r <= l_{v_r} = c_{v_r} - s_{v_r}`. This ensures `F_r <= c_{v_r}`.
3. **Trip completion:** `R(P) <= L = T_e + delta`.
4. Travel times and visit durations are nonnegative and all used transitions must be available.

Because the depot and return are fixed, the above conditions also ensure every intermediate visit finishes no later than the permitted trip horizon, assuming nonnegative travel times.

## 5. Objective function

Let

\[
\operatorname{Travel}(P)=\sum_{r=0}^{k}t_{v_r,v_{r+1}},
\qquad
\operatorname{Wait}(P)=\sum_{r=1}^{k}w_r,
\]

\[
\operatorname{Overtime}(P)=\max(0,R(P)-T_e).
\]

Define weighted cost

\[
C(P)=\operatorname{Travel}(P)
+\lambda\operatorname{Wait}(P)
+2\operatorname{Overtime}(P).
\]

The optimization goal is

\[
\operatorname*{lexmax}_{P\text{ feasible}}\bigl(k(P),-C(P)\bigr).
\]

Equivalently, maximize the number of attractions, then minimize cost among all feasible routes visiting that maximum number.

Visit durations affect feasibility but are not directly added to the objective. Their effect is already represented in the visit-finish and return times.

## 6. Example: latest start

If an attraction opens at 09:00, closes at 17:00 and requires 60 minutes, the permitted visit-start interval is `[09:00, 16:00]`. Arrival at 08:45 entails 15 minutes' waiting and a 09:00 start; arrival at 16:05 is infeasible.

## 7. Implementation mapping (reviewed against uploaded ZIP)

- `app.py` converts actual closing time into `latest_start = closing - duration`; all-day attractions use `trip_end + tolerance - duration`.
- `core/strategies/selector.py` chooses Held–Karp only for effectively unrestricted visit-start windows; otherwise it chooses DP.
- `core/dp_optimizer_optimized.py` maintains a frontier of states per `(visited_mask, last_node)` and evaluates lexicographic count and cost on feasible returns.
- `core/route_validator.py` checks `visit_start <= latest_start`, matching the formal specification.

### Input feasibility precondition and arrival check

For every attraction with actual operating hours, `app.py` validates

\[
s_i \le c_i-o_i.
\]

Since `l_i=c_i-s_i`, this implies `o_i <= l_i`. Thus, for validated inputs,

\[
A_i \le l_i \quad\Longrightarrow\quad
B_i=\max(A_i,o_i)\le l_i.
\]

Consequently, the optimized DP's check `if arrival > window_end: continue` is sufficient for this constraint **provided** the optimizer receives only validated windows with `window_start <= window_end`. The application enforces this for fixed-hours attractions; all-day windows should also be checked for consistency when trip duration is shorter than visit duration. Standalone callers of the optimizer must satisfy this precondition themselves or add validation at the optimizer boundary.

No code change is needed to the arrival comparison under that precondition.

### Proof status

A conditional proof of the implemented dominance relation is given in `correctness_proof.md`; it relies on normalized windows, static nonnegative travel and service times, and nonnegative waiting penalties.

## 8. Verification and open items

The user reported 33 passing pytest tests, including a seeded test of 500 exhaustive comparisons. See `verification_status.md` for the distinction between empirical verification and proof, and for remaining input-validation caveats.
