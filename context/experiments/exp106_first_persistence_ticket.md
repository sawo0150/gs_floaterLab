# exp106 — first-persistence local topology on the short UTMM failure case

- Date: 2026-09-24
- Status: quality/structure/activation gate **PASS**; single-scene isolation
- VIGS source: `f6a90853`
- Runner: `benchmarks/online_gs/run_exp106_first_persistence_ticket.py`
- Scene: UTMM `slow-straight-2`
- Results: `results/experiments/exp106_first_persistence_ticket/`
- Summary: [metrics](benchmark_custom/exp106_first_persistence_ticket_20260924/summary.md)

## Method

The Exp104 top-1,024 and two-distinct-dense-UID evidence rule is unchanged,
but it no longer waits for another native topology event. Once per active map
generation, the first paid dense step with persistent evidence spends one
top-1,024 weighted without-replacement ticket immediately after its Adam step.
The bounded VIGS operator snapshots and restores the existing
`xyz_gradient_accum`, `denom`, and `max_radii2D` rows and appends zeros for new
clones, so later native densification receives its original accumulated state.

## Result

| Run | PSNR | Δ Exp94 R4 | Δ fresh vanilla | Dense mutation | Renders | Adam | Final GS |
|---|---:|---:|---:|---:|---:|---:|---:|
| Exp106 first-persistence | **17.309940** | **+0.086496** | −0.054132 | **443** | 1,888 | 177 | 24,810 |
| Exp105 native-event ticket | 17.246139 | +0.022695 | −0.035588 | 0 | 1,888 | 177 | 24,368 |
| Exp94 normalized R4 | 17.223444 | — | −0.126230 vs its fresh vanilla | 0 | 1,888 | 177 | 24,366 |

All 619 repeated candidates arose after the last native topology event. The
new trigger selected all 443 standard small-scale eligible parents, preserved
native stats, and added no render or Adam step. Candidate and fresh vanilla
saved maps pass double evaluation and render-matched fairness. Mapping wall was
11.19 s versus Exp94 R4 11.47 s; this small difference is timing noise, not a
speed claim.

## Decision

The scheduling failure is fixed: dense/ERCB topology is now active in the
work-poor scene and the candidate is +0.0638 dB above the Exp105 mutation-zero
run and +0.0865 dB above Exp94 R4. It still trails this run's fresh vanilla by
0.0541 dB, and the deltas are too small for a single-run causal quality claim.
Keep the result as an activation/quality-preservation isolation. Before any
panel expansion, run the identical common rule on RPNG `table_01` and require
the historical +1.6 dB vanilla advantage and −0.5 dB R4 stop to remain intact.
