# Smart Trip Planner — Correctness Proof for Optimized Subset DP

> Scope: `core/dp_optimizer_optimized.py` in the supplied project snapshot (15 October 2026). This proof concerns this optimizer, not the separate Held–Karp or OR-Tools implementations. It assumes valid normalized input as specified below.

## 1. Problem and assumptions

Locations are `0,1,...,m`, where `0` is the depot. Each attraction can be visited at most once. Travel times `t[i][j]` and service times `s[i]` are finite and nonnegative; travel times are static and may be asymmetric. Each attraction has a normalized *start window* $[o_{i}, l_{i}]$, where $l_{i} = closing_i - s_{i}$ and $o_{i} \le  l_{i}$. The trip starts at $T_{s}$; return to the depot must occur by $L = T_{e} + \delta$. The waiting weight $\lambda$ and overtime coefficient `2` are nonnegative. All candidate routes are evaluated under the same input and deterministic travel times.

**Input boundary:** The application's validation checks $s_{i} \le  closing_i - opening_i$ for time-constrained attractions. The optimizer itself does not check $o_{i} \le  l_{i}$, so its correctness guarantee requires the normalized precondition from the caller. An independently callable library API should validate this itself.

For a route $P=(0,v_{1},\ldots ,v_{k},0)$, each visit starts at $B_{r} = \max(F_{r-1}+t[v_{r-1}][v_{r}], o_{v_{r}})$ and finishes at $F_{r}=B_{r}+s_{v_{r}}$. It is feasible when $B_{r} \le  l_{v_{r}}$ for every visit and $R=F_{k}+t[v_{k}][0] \le  L$.

Its cost is $C(P) = \sum(travel) + \lambda*\sum(waiting) + 2*\max(0,R-T_{e})$. The objective is lexicographic: maximize `k`, then minimize $C(P)$.

## 2. State invariant

For a subset mask `M` and final node `i`, a stored state `S=(M,i,t,c,prev)` represents an actual prefix starting at the depot, visiting exactly `M` once, ending at `i`, finishing at time `t`, and incurring prefix cost $c = travel_so_far + \lambda*waiting_so_far$. `prev` reconstructs this prefix. The initial state `(empty,0,T_s,0,None)` satisfies the invariant.

**Transition:** To an unvisited attraction `j`, set `A=t+t[i][j]`, $W=\max(0,o_{j}-A)$, $F=A+W+s_{j}$, and `c'=c+t[i][j]+lambda*W`. The implementation rejects $A>l_{j}$ and $F>L$. Since the normalized input ensures $o_{j}\le l_{j}$, $A\le l_{j}$ implies $\max(A,o_{j})\le l_{j}$; thus the new visit finishes by its actual closing time. The new state has subset $M union {j}$, last node `j`, time `F`, and cost `c'`, preserving the invariant.

## 3. Dominance lemma

Consider states `A` and `B` with the **same subset and last node**, and let $t_{A}\le t_{B}$. They have identical possible unvisited attractions and future travel/service parameters.

### 3.1 Conservative waiting bound

Fix any ordered continuation feasible from `B`. If it is executed from `A`, every arrival and completion time is no later than its counterpart from `B`: this follows inductively because $x -> \max(x,o_{j})+s_{j}$ is nondecreasing. Hence the continuation is also feasible from `A`.

Let $d=t_{B}-t_{A}\ge 0$. Along the same continuation, the **additional total waiting** when starting from `A` rather than `B` is at most `d`. To see this, for a transition with identical travel and service times, let `d_before` be the difference between the two current times and let $w_{A},w_{B}$ be their waiting times. The new time difference is $d_{after}=d_{before}-(w_{A}-w_{B})\ge 0$. Summing over visits telescopes: $\sum(w_{A}-w_{B})=d-d_{final}\le d$. The travel contributions are identical; the return from `A` is no later, so its overtime penalty is no larger.

Therefore, if $c_{A} + \lambda*(t_{B}-t_{A}) \le  c_{B}$, any feasible completed route extending `B` has a counterpart extending `A` with no greater total cost and the same number of attractions.

### 3.2 All remaining attractions already open

If every unvisited attraction has $o_{j}\le t_{A}$, then no continuation from `A` or `B` requires waiting for opening, since travel and service times are nonnegative. Thus $c_{A}\le c_{B}$ and $t_{A}\le t_{B}$ suffice to dominate `B`.

These are precisely the two cases implemented by the local `dominates(a,b)` function, with $still_unvisited$ computed from the *new subset*.

## 4. Preservation of an optimum under pruning

When the algorithm discards a candidate state because an existing frontier state dominates it, the dominance lemma gives a replacement prefix for every feasible continuation of the discarded state, with the same visited count and no greater completed cost. Likewise, when the new state dominates existing frontier entries, replacing them is safe. Because each dominance replacement is at the same subset and last node, this argument applies recursively to later pruning decisions. Thus pruning cannot eliminate the existence of a lexicographically optimal completed route.

## 5. Exhaustive generation and terminal selection

Without pruning, every feasible attraction sequence is generated inductively by appending its next unvisited attraction. With pruning, Section 4 ensures that an equally good or better completion remains representable. Every surviving state is evaluated as a possible completed route by adding its return travel time; only returns by `L` are considered. The algorithm compares $(visited_count, total_cost)$ lexicographically, prioritizing larger counts and then smaller costs. Consequently, whenever a feasible return exists, the returned route is feasible and lexicographically optimal under the assumptions in Section 1.

If no feasible return exists, the implementation returns `([],0,infinity,states_explored)`, which is an explicit failure/no-solution result, not a feasible tour.

## 6. Limits of the claim and verification checklist

- This proof assumes the caller supplies normalized, nonempty feasible start windows; it does not establish correctness for arbitrary malformed direct calls to the optimizer.
- This proof does not establish the correctness of `HeldKarpStrategy`, its selection criterion, or other optimizers. Those need separate treatment.
- Passing 26 existing tests is valuable evidence but is not itself the proof.
- Recommended additional regression tests: arrivals before opening; zero-duration visits; equality at the latest start; asymmetric matrices; tied states; paths returning exactly at $T_{e}+\delta$; and randomized comparison with exhaustive enumeration on small normalized instances.

## 7. Implementation correspondence

- Initial state and layer-by-subset enumeration: `start_state`, `layer`, `for count in range(n)`.
- Transition and time feasibility: `arrival`, `waiting`, `finish`, `if arrival > window_end`, `if finish > limit`.
- Dominance: nested `dominates(a,b)` and `frontier_next` insertion/removal.
- Terminal objective: `return_time`, $total_cost$, $best_count$, $best_cost$.
- Path reconstruction: the `prev` chain followed by appending depot `0`.
