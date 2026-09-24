# exp107 — first-persistence ticket preserves the RPNG R4 gain

- Date: 2026-09-24
- Status: RPNG `table_01` quality/structure/fresh-pair gate **PASS**
- VIGS source: `f6a90853`
- Lab source: `1e8acbd` plus source-locked runner
- Runner: `benchmarks/online_gs/run_exp107_first_persistence_rpng.py`
- Results: `results/experiments/exp107_first_persistence_rpng/`
- Summary: [metrics](benchmark_custom/exp107_first_persistence_rpng_20260924/summary.md)

## Result

The Exp106 rule transfers unchanged from UTMM to RPNG. In the final map
generation, the first persistent dense step found 532 repeated point IDs; 396
passed the standard small-scale clone qualifier and were sampled without
replacement. Native densification state was preserved.

| Run | PSNR | Renders | Adam | Native topology events | Final GS |
|---|---:|---:|---:|---:|---:|
| Exp107 first-persistence | **25.584830** | 38,302 | 3,030 | 2 | 417,753 |
| Exp94 normalized R4 | 25.581416 | 38,302 | 3,030 | 2 | 417,561 |
| Exp107 fresh vanilla | 23.939681 | 38,302 | 3,027 | — | 182,726 |

Candidate−Exp94 R4 is **+0.003415 dB** and candidate−fresh vanilla is
**+1.645150 dB**. Candidate and vanilla saved-map double evaluation, physical
render matching, opportunity/event/archive/config parity, held-out
disjointness, zero-tail, and pair verification all pass. Final GS rises by only
192 (+0.046%) from Exp94 R4 despite 396 local clones because the later unchanged
native topology absorbs part of the added capacity.

## Decision

This is the current preferred topology composition for further transfer:

1. Preserve normalized R4 birth, keyframe/dense service, prune, and
   observation-driven native topology.
2. Use the paid normalized-ERCB dense gradient to accumulate generation-scoped
   per-point evidence.
3. At the first two-distinct-view persistence event in each map generation,
   spend at most one top-1,024 weighted without-replacement small-clone ticket.
4. Preserve all native densification statistics across the mid-cycle append.

The rule makes dense/ERCB topology active in the short UTMM scene and preserves
the full RPNG +1.6 dB vanilla advantage with negligible final capacity change.
It is still validated on only two active scenes plus the Exp105 Aria native-
event variant. Freeze all hyperparameters and next transfer this exact
first-persistence rule to Aria `aria1253`, then run the 17-scene panel only if
that gate also passes. Strict-live latency remains unproven.
