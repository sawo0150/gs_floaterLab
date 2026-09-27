# exp95 — behavior-neutral topology churn probe

- Date: 2026-09-24
- Status: RPNG `table_01` pair complete; diagnostic objective achieved
- Candidate source: VIGS-SLAM commit `56881ee1bea106baa095c8a28ecb4d33c58dae88`
- Runner: `benchmarks/online_gs/run_exp95_topology_churn_probe.py`
- Results: `results/experiments/exp95_topology_churn_probe/`
- Summary: [table and topology accounting](benchmark_custom/exp95_topology_churn_probe_20260924/summary.md)

## Question

Does the accepted normalized-variance R4 recipe actually perform little
topology work because only two topology events survive in the runtime summary,
or do those events hide large global clone/split/prune transactions?

## Change under test

No mapping behavior was intentionally changed.  Exact counters were added to
the existing clone, split, filter-prune, and cap-prune tensor mutations.  The
backend writes both per-event `MAP_TOPOLOGY_MUTATION` records and an aggregate
under `mapping_replay_summary.topology_mutations`.  Unit and regression tests
passed before the run: topology telemetry 2/2, normalized ERCB 25/25, R4
keyframe selection 10/10, plus Python compilation and a behavior diff check.

## Result

| Arm | PSNR | SSIM | LPIPS | Physical renders | Adam | Gaussians | Map wall | Peak CUDA allocated |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| normalized R4 + telemetry | 25.585018 | 0.847780 | 0.153816 | 38,302 | 3,030 | 417,656 | 165.90 s | 5.09 GB |
| fresh official vanilla | 23.964263 | 0.794350 | 0.198004 | 38,302 | 3,027 | 183,283 | 190.95 s | 2.38 GB |
| difference | **+1.620754 dB** | +0.053430 | -0.044188 | 0 | +3 | +234,373 | -25.04 s | +2.71 GB |

Both saved maps produced identical metrics in two independent evaluations.
The pair used the same frozen tracker archive, 502-view held-out evaluator,
210 tracking keyframes, zero-tail contract, and exact 38,302-render physical
budget.  All ten fairness checks passed.  The candidate is 0.039298 dB below
the historical R4 value 25.624315, safely inside the predeclared 0.5 dB stop
threshold.

## Topology accounting

The final mapper generation contains two events: 19,552 rows added, 48,965
removed, and **68,517 total row mutations**.  Of the removals, 46,025 are the
ordinary densify/prune filter and 2,940 are split parents.  The largest event
alone adds 13,337 and removes 33,465 rows (46,802 churn) from 77,545 inputs.
Accounting error is zero.

The raw mapping log has four transactions because mapper reset/reconstruction
paths each create another generation.  Summed only as a diagnostic, they
contain 31,755 additions and 79,895 removals (111,650 churn).  The current
runtime aggregate is reset with the mapper and therefore describes only the
final generation.  A generation ID/lifetime summary is required before any
cross-generation headline is made.

## Interpretation and next experiment

R4's quality gain is still present, but its topology is neither local nor
lightweight.  A pair of coarse global events can mutate most of the current
tensor while the final Gaussian count hides the add/remove turnover.  The next
controlled test will keep growth unchanged and isolate/defer the ordinary
filter-prune branch on `table_01`; it will not add local births at the same
time.  Only after that causal split should a bounded current-view birth
operator, derived from public author code, be ported as a separate experiment.

This is a B-track mapping-only diagnosis, not evidence of tracker+mapper
strict-live performance.
