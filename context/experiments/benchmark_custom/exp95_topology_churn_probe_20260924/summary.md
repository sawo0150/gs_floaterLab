# Exp95 topology churn probe — behavior-neutral R4 vs official vanilla

Predeclared valid inventory: 17 scenes; UTMM slow-straight-1 tracker-ineligible N/A.
Both arms: same frozen tracker, zero-tail, render-matched B-track, 15 s
post-map cooldown and two independent saved-map evaluations. Any >0.01 dB
per-view PSNR disagreement stops the panel; no score is selected by rank.

| Dataset | Scene | Normalized PSNR | Vanilla PSNR | ΔPSNR | Renders N/V | Adam N/V | GS N/V | Eval/Fairness |
|---|---|---:|---:|---:|---:|---:|---:|---|
| rpng | table_01 | 25.5850 | 23.9643 | +1.6208 | 38302/38302 | 3030/3027 | 417656/183283 | PASS |
| rpng | table_02 | — | — | — | — | — | — | PENDING |
| rpng | table_03 | — | — | — | — | — | — | PENDING |
| rpng | table_04 | — | — | — | — | — | — | PENDING |
| rpng | table_05 | — | — | — | — | — | — | PENDING |
| rpng | table_06 | — | — | — | — | — | — | PENDING |
| rpng | table_07 | — | — | — | — | — | — | PENDING |
| rpng | table_08 | — | — | — | — | — | — | PENDING |
| utmm | ego-centric-1 | — | — | — | — | — | — | PENDING |
| utmm | ego-centric-2 | — | — | — | — | — | — | PENDING |
| utmm | ego-drive | — | — | — | — | — | — | PENDING |
| utmm | fast-straight | — | — | — | — | — | — | PENDING |
| utmm | slow-straight-2 | — | — | — | — | — | — | PENDING |
| utmm | square-1 | — | — | — | — | — | — | PENDING |
| utmm | square-2 | — | — | — | — | — | — | PENDING |
| aria | aria1253 | — | — | — | — | — | — | PENDING |
| aria | aria301_305 | — | — | — | — | — | — | PENDING |

Completed formal pairs: **1/17**.
No all-scene acceptance claim until all 17 pairs complete.

## table_01 topology probe

The telemetry patch is behavior-neutral: it changes only mutation methods'
return values and logging.  The candidate retained the Exp94 work contract
(38,302 physical renders, 3,030 Adam steps, 267 dense and 267 paired keyframe
updates, zero post-EOS updates).  Its saved map evaluated twice at exactly
25.5850178274 dB.  This is +1.620754 dB over the fresh vanilla arm and only
-0.039298 dB below the historical R4 gate value, so the predeclared 0.5 dB
stop condition did not fire.  All ten pair-fairness checks passed.

The final surviving mapper generation reported two regular topology events:

| Quantity | Total | Largest single event |
|---|---:|---:|
| Clone children | 13,672 | 9,379 |
| Split children | 5,880 | 3,958 |
| Added rows | 19,552 | 13,337 |
| Split parents removed | 2,940 | 1,979 |
| Filter-pruned rows | 46,025 | 31,486 |
| Total removed rows | 48,965 | 33,465 |
| Mutation churn (added + removed) | **68,517** | **46,802** |
| Net mutation delta | -29,413 | -20,128 |
| Accounting error | 0 | 0 |

Thus the small number of topology calls does **not** imply a small topology
operation: the second event alone rewrote 46,802 rows from an input of 77,545.
The complete mapping log contains four transactions across mapper resets/map
generations (111,650 aggregate row mutations).  The runtime JSON currently
retains only the final generation, so that cross-generation sum is diagnostic
and must not be presented as one map's net delta.  The next instrumentation
revision must add an explicit map-generation ID and lifetime accumulator.

The candidate ended with 417,656 Gaussians versus vanilla's 183,283, used
5.09 GB versus 2.38 GB peak allocated VRAM, and took 165.90 s versus 190.95 s
mapping wall time in this isolated run.  The wall times are not a strict-live
claim: this is the mapping-only fixed-render B-track and the one-run timing is
not controlled enough to attribute speed to the larger map.

## Decision

Do not run the full 17-scene panel for this telemetry-only experiment.  It
already reproduces Exp94 quality within noise and exposes the next causal
question.  Before adding a local birth operator, isolate deletion from growth
on this development scene while preserving the exact scheduler, render work,
dense/KF selection, topology opportunities, and zero-tail contract.  This
avoids changing scheduler, birth, and prune semantics in one experiment.
