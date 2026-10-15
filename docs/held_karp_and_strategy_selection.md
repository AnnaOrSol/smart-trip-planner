# Held–Karp Optimization and Strategy Selection

## Scope
This document describes `core/held_karp_optimizer.py` and `core/strategies/selector.py` as supplied in the project archive. The proof applies to finite, nonnegative, time-independent travel times, nonnegative service durations, a common start/end depot (node 0), and validated latest-start windows. The objective is lexicographic: maximize visits first, then minimize total travel plus twice the overtime past the planned end. Waiting has zero cost in this specialized case because it never occurs.

## Notation
Let `n` include the depot, let `T_s` be the trip start, `T_e` the nominal trip end, `δ` the permitted overtime, and `L=T_e+δ`. Attraction `i` has service duration `s_i`, opening `o_i`, and latest permissible start `b_i` (actual closing time minus duration). Travel time from `i` to `j` is `t_ij` and need not be symmetric.

## Strategy-selection condition
The selector chooses Held–Karp if, for every attraction `i>0`,

\[
o_i \le T_s,\qquad b_i \ge L-s_i.
\]

Otherwise it chooses the constrained DP strategy. The Held–Karp solver independently checks the same conditions and raises `ValueError` if they fail.

**Why these conditions suffice.** Consider any visit starting at time `B_i` on a route whose return to the depot is no later than `L`. Because travel times are nonnegative, the end of the visit cannot exceed the return time: `B_i+s_i <= L`, hence `B_i <= L-s_i <= b_i`. Also `B_i >= T_s >= o_i`. Thus every visit on any route feasible with respect to the trip horizon automatically satisfies its attraction window, and waiting for opening is unnecessary. This is a sufficient, not necessary, condition for the windows to be irrelevant.

## DP state and recurrence
For a subset `M` of attractions and last location `j` (with `(∅,0)` as the initial state), define

\[
D[M,j]=\text{minimum travel time from depot 0 through exactly M, ending at j}.
\]

The base case is `D[∅,0]=0`. For `j∈M`, the recurrence is

\[
D[M,j]=\min_{i\in M\setminus\{j\}\;\text{or}\;i=0\text{ when }M=\{j\}}\left(D[M\setminus\{j\},i]+t_{ij}\right).
\]

The implementation uses forward transitions and stores a predecessor for reconstruction. Let `S(M)=Σ_{i∈M}s_i`. For any state, the earliest return time is

\[
R(M,j)=T_s+D[M,j]+S(M)+t_{j0}.
\]

A state is a candidate when `R(M,j) <= L`. Its number of visits is `|M|` and its objective cost is

\[
C(M,j)=D[M,j]+t_{j0}+2\max(0,R(M,j)-T_e).
\]

The algorithm chooses the feasible candidate with maximum `|M|`, breaking ties by minimum `C`.

## Correctness argument
**Lemma 1 (state optimality).** For each reachable `(M,j)`, `D[M,j]` is the minimum travel time among paths visiting exactly `M` and ending at `j`. Proof is by induction on `|M|`: the base case is immediate; every nonempty path has a penultimate node, and the recurrence considers that predecessor. Replacing a prefix by a shorter prefix cannot worsen the total travel time.

**Lemma 2 (state sufficiency).** For fixed `(M,j)`, all paths have the same service-duration sum `S(M)`. Therefore the minimum-travel prefix has the earliest finish and return time. Its return penalty is no greater than that of any longer-travel prefix. Consequently, retaining only the minimum-travel prefix cannot discard a feasible or lower-cost completion for the same `(M,j)`.

**Theorem (lexicographic optimality).** Every feasible route corresponds to a state `(M,j)`. By Lemmas 1–2, the algorithm has a candidate of the same visit count and no greater cost whenever that route is feasible. Taking the maximum visit count and then minimum cost yields the lexicographically optimal feasible route. The strategy-selection conditions ensure that the ignored attraction windows cannot invalidate this conclusion.

## Complexity
There are at most `O(n 2^(n-1))` subset/last-node states, each attempting up to `n-1` extensions. Time is `O(n² 2^n)`; DP and predecessor storage require `O(n 2^n)` space, with `O(2^n)` additional space for precomputed service-duration sums.

## Tests and limitations
`tests/test_held_karp.py` compares counts and costs against the general DP over 1,000 seeded random cases. `tests/test_strategy_selector.py` checks dispatch for unrestricted, late-opening, and early-latest-start windows. The user reported 33 passing tests overall, including the existing seeded Held–Karp comparisons. Tests support but do not replace the proof. The argument assumes nonnegative travel/service times and valid matrix/window inputs. It does not establish correctness of the constrained DP or any separate OR-Tools implementation.
