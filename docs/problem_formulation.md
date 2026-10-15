# Smart Trip Planner — Formal Problem Formulation

> Status: Draft 1 — mathematical specification. Implementation consistency and correctness proofs are pending.

## 1. Problem description

Given a depot and a set of candidate attractions, find a single-day route starting and ending at the depot. Each attraction may be visited at most once. Travel times, visit durations, attraction operating hours and a trip end-time tolerance constrain feasible routes.

The objective is **lexicographic**: (1) maximize the number of visited attractions; (2) among routes with the same number of attractions, minimize weighted travel, waiting and overtime cost.

## 2. Inputs and notation

- $V = {0, 1, \ldots , n}$: locations; `0` is the depot.
- $t_{ij} \ge  0$: directed travel time from location `i` to `j` (the matrix need not be symmetric).
- $s_{i} \ge  0$: service/visit duration for attraction `i`; $s_{0} = 0$.
- $o_{i}$: opening time of attraction `i`.
- $c_{i}$: actual closing time of attraction `i`.
- $l_{i} = c_{i} - s_{i}$: latest permissible **start** of the visit.
- $T_{s}$: trip start time; $T_{e}$: preferred trip end time.
- $\delta \ge  0$: maximum permitted overtime; $L = T_{e} + \delta$.
- $\lambda \ge  0$: waiting-time weight (default `3`).

For an all-day attraction, the application sets $o_{i} = T_{s}$ and $l_{i} = L - s_{i}$ rather than using real operating hours.

## 3. Route and time dynamics

A candidate route is $P = (0, v_{1}, \ldots , v_{k}, 0)$ where all $v_{r}$ are distinct attraction indices. Define $v_{0} = v_{k+1} = 0$, and $F_{0} = T_{s}$.

For each visit $r = 1, \ldots , k$:

$$
A_r = F_{r-1} + t_{v_{r-1},v_r}, \qquad
B_r = \max(A_r, o_{v_r}),
$$

$$
w_r = B_r - A_r = \max(0, o_{v_r}-A_r), \qquad
F_r = B_r + s_{v_r}.
$$

The return time is

$$
R(P) = F_k + t_{v_k,0}.
$$

For the empty route, $P = (0,0)$, define $R(P) = T_{s} + t_{00}$ (normally $t_{00} = 0$).

## 4. Feasibility constraints

1. Each attraction appears at most once.
2. **Latest visit start:** $B_{r} \le  l_{v_{r}} = c_{v_{r}} - s_{v_{r}}$. This ensures $F_{r} \le  c_{v_{r}}$.
3. **Trip completion:** $R(P) \le  L = T_{e} + \delta$.
4. Travel times and visit durations are nonnegative and all used transitions must be available.

Because the depot and return are fixed, the above conditions also ensure every intermediate visit finishes no later than the permitted trip horizon, assuming nonnegative travel times.

## 5. Objective function

Let

$$
\mathrm{Travel}(P)=\sum_{r=0}^{k}t_{v_r,v_{r+1}},
\qquad
\mathrm{Wait}(P)=\sum_{r=1}^{k}w_r,
$$

$$
\mathrm{Overtime}(P)=\max(0,R(P)-T_e).
$$

Define weighted cost

$$
C(P)=\mathrm{Travel}(P)
+\lambda\mathrm{Wait}(P)
+2\mathrm{Overtime}(P).
$$

The optimization goal is

$$
\max_{P\text{ feasible}}\bigl(k(P),-C(P)\bigr)\quad\text{(lexicographic order)}.
$$

Equivalently, maximize the number of attractions, then minimize cost among all feasible routes visiting that maximum number.

Visit durations affect feasibility but are not directly added to the objective. Their effect is already represented in the visit-finish and return times.

## 6. Example: latest start

If an attraction opens at 09:00, closes at 17:00 and requires 60 minutes, the permitted visit-start interval is `[09:00, 16:00]`. Arrival at 08:45 entails 15 minutes' waiting and a 09:00 start; arrival at 16:05 is infeasible.

## 7. Implementation mapping (reviewed against uploaded ZIP)

- `app.py` converts actual closing time into $latest_start = closing - duration$; all-day attractions use `trip_end + tolerance - duration`.
- `core/strategies/selector.py` chooses Held–Karp only for effectively unrestricted visit-start windows; otherwise it chooses DP.
- `core/dp_optimizer_optimized.py` maintains a frontier of states per $(visited_mask, last_node)$ and evaluates lexicographic count and cost on feasible returns.
- `core/route_validator.py` checks $visit_start \le  latest_start$, matching the formal specification.

### Input feasibility precondition and arrival check

For every attraction with actual operating hours, `app.py` validates

$$
s_i \le c_i-o_i.
$$

Since $l_{i}=c_{i}-s_{i}$, this implies $o_{i} \le  l_{i}$. Thus, for validated inputs,

$$
A_i \le l_i \quad\Longrightarrow\quad
B_i=\max(A_i,o_i)\le l_i.
$$

Consequently, the optimized DP's check `if arrival > window_end: continue` is sufficient for this constraint **provided** the optimizer receives only validated windows with $window_start \le  window_end$. The application enforces this for fixed-hours attractions; all-day windows should also be checked for consistency when trip duration is shorter than visit duration. Standalone callers of the optimizer must satisfy this precondition themselves or add validation at the optimizer boundary.

No code change is needed to the arrival comparison under that precondition.

### Proof status

No formal optimality claim is made yet for dominance pruning in the optimized DP. The pruning relation must be proved sound under waiting-time penalties and time windows, or revised, before documenting a full correctness proof.

## 8. Next documentation steps

1. Record and test input preconditions at the optimizer boundary, including all-day windows.
2. Define the DP recurrence and state invariant.
3. Prove feasibility and optimality, including a justified dominance relation.
4. Analyze time and memory complexity.
5. Record empirical tests and benchmark conditions separately from formal proofs.
