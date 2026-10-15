# Complexity Analysis — Smart Trip Planner

## Scope and notation

This analysis refers to `core/dp_optimizer_optimized.py` in the supplied project snapshot. Let `n` be the number of locations **including** depot 0, and `m = n - 1` the number of attractions. Let `S` denote the number of state objects processed by the outer frontier loops, `I` the number of candidate-state insertions, and `F` the maximum size of a dominance frontier for one `(mask, last_node)` pair.

The implementation is exact subset dynamic programming with potentially **multiple nondominated labels** per `(mask, last_node)`, not the classical one-label-per-subset Held–Karp recurrence.

## State structure

A state stores finish time, accumulated cost, predecessor pointer, and current node. States are grouped by the visited-attraction bitmask and last node. The algorithm processes layers of equal visited-attraction count, creating candidates by extending a state to each unvisited attraction.

There are at most `m * 2^(m-1)` nonempty `(mask, last_node)` keys, plus the initial depot key. This is a bound on **keys**, not on the number of state labels, because each key can retain several labels.

## Time complexity

For each processed state, up to `m` candidate next attractions are considered. Constructing a candidate is O(1) apart from frontier maintenance. For each candidate insertion, `any(dominates(...))` scans up to `F` existing labels, and the list comprehension may scan them again. Each dominance comparison can scan up to `m` still-unvisited attractions to decide whether all are already open. Thus a conservative bound is:

\[
T = O(Sm + IFm), \qquad I \leq Sm,
\]

and therefore

\[
\boxed{T = O(Sm^2F)}.
\]

This is an **output-sensitive / search-size** bound: `S` and `F` depend on the input and on pruning. It does not imply polynomial running time.

Without dominance pruning, each partial route corresponds to an ordered list of distinct attractions. Their number is

\[
P_m = \sum_{k=0}^{m}\frac{m!}{(m-k)!} = O(m!).
\]

The number of generated candidate extensions is also `O(m!)` up to a constant factor. In the worst case, dominance pruning is not guaranteed to reduce the exponential/factorial search to one label per key. A coarse upper bound obtained by substituting `S,F \le O(m!)` into the parameterized formula is `O(m^2(m!)^2)`; this is deliberately loose, not a tight worst-case characterization.

## Space complexity

The active `layer` and `next_layer` dictionaries hold nondominated states. Every stored state also has a `prev` pointer; selected states can keep older predecessor states alive even after their layers have been replaced. Thus counting only the current frontier underestimates total memory. A safe upper bound is `O(m!)` state objects plus `O(m)` reconstruction space and dictionary overhead, with each state object occupying constant-sized fields. The input travel-time matrix occupies `O(n^2)` memory separately.

## Contrast with Held–Karp

Classical Held–Karp for unconstrained shortest Hamiltonian tour uses one value per `(mask, last_node)` and has `O(m^2 2^m)` time and `O(m 2^m)` memory (up to depot/implementation conventions). The constrained label-setting DP here does **not** inherit those bounds, because time windows and weighted waiting require multiple nondominated time/cost labels.

## Practical benchmarking

Report runtime, `states_explored`, number of attractions, and instance type (tight/loose time windows, symmetric/asymmetric travel times). Compare on identical inputs and distinguish observed speedups from worst-case guarantees. Note that `states_explored` counts states processed, not every generated candidate or dominance comparison.

## Assumptions and proof status

The analysis assumes nonnegative travel times, service times, and waiting penalty; fixed travel times; and valid time windows. Correctness of pruning is a separate proof obligation. A passing test suite alone does not establish the general dominance theorem or a tight complexity bound.
