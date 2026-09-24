# exp102 — behavior-neutral ERCB dense topology evidence probe

- Date: 2026-09-24
- Status: RPNG `table_01` quality/isolation gate **PASS**; diagnostic only
- VIGS source: `2306b6f9`
- Runner: `benchmarks/online_gs/run_exp102_dense_topology_evidence_probe.py`
- Results: `results/experiments/exp102_dense_topology_evidence_probe/`
- Summary: [dense evidence](benchmark_custom/exp102_dense_topology_evidence_probe_20260924/summary.md)
- Implementation references: TileGS `7f109a403ed522ba5ec7610f3d4778c363b68b11`
  persistent evidence concept; Taming 3DGS
  `fd0f7d9edfe135eb4eefd3be82ee56dada7f2a16` explicit mutation-ticket
  structure. No CUDA or method code was copied in this diagnostic.

## Question and isolation

Exp102 asks whether the RGB gradient already produced by each paid,
normalized-variance ERCB dense replay contains a sufficiently local and
persistent per-Gaussian signal to control a future bounded topology service.
The probe reads the existing `f_dc` gradient before the already scheduled Adam
step and maps the highest-gradient rows to stable point IDs. It performs no
additional render, Adam step, birth, split, clone, or prune.

The run preserves the Exp95 normalized R4 archive, configuration, event order,
dense admission, dense and keyframe opportunity skeletons, 38,302 physical
renders, 3,030 Adam steps, two topology events, held-out disjointness, and
zero-tail. Both saved-map evaluations agree exactly.

## Result

| Run | PSNR | Renders | Adam | Final GS | Mapping wall |
|---|---:|---:|---:|---:|---:|
| Exp102 evidence probe | **25.577882** | 38,302 | 3,030 | 417,637 | 165.18 s |
| Exp95 normalized R4 | 25.585018 | 38,302 | 3,030 | 417,656 | 165.90 s |
| Fresh vanilla | 23.964263 | 38,302 | 3,027 | 183,283 | — |

Exp102 is **−0.007136 dB** from R4 and **+1.613619 dB** over fresh vanilla,
so the predeclared −0.5 dB stop line is not approached. The probe itself spent
1.674 s in diagnostic GPU top-k/host synchronization; the end-to-end mapping
wall comparison is not used to claim speedup because that timing is noisy and
the diagnostic synchronization is not production code.

All **269 fixed dense opportunities** were observed in ledger order, covering
267 unique dense UIDs. The replay queue's `dense_updates=267` excludes two
frontier/bootstrap opportunities and is therefore not the correct probe
denominator. The original post-run gate compared against that field and
reported a false failure; the audit predicate was corrected to compare the
fixed-opportunity ledger and exact selected-UID sequence. No map or metric was
rerun or changed by this reporting correction.

## Dense signal

- On average, 129,918 Gaussian rows, or 59.25% of the current map, had a finite
  positive `f_dc` gradient from the selected dense view.
- The top 256 / 1,024 / 4,096 rows captured 14.14% / 29.84% / 54.24% of total
  gradient mass. The signal is therefore concentrated but not sparse enough
  for a visibility mask alone to be a bounded topology policy.
- Consecutive top-1,024 point-ID sets had mean Jaccard 0.3180, showing useful
  temporal persistence rather than independent per-view noise.
- For top-1,024 nomination, 37,947 lifetime point IDs were seen; 26,572 were
  nominated at least twice, 21,378 at least three times, and 25,264 repeatedly
  nominated IDs remained alive in the final map.

## Decision

This experiment validates dense/ERCB gradient evidence as a real input to a
future topology controller, not a quality-improving topology method by itself.
The next experiment may port the downloaded author-code pattern of an explicit
without-replacement mutation ticket, restricted to repeatedly nominated stable
point IDs. It must preserve R4 birth, exact render/Adam work, and the same
−0.5 dB quality stop. Dense RGB supplies no trusted depth, so it must not be
used to back-project new points. Hard pruning remains out of scope until the
quality-preserving local growth path is established.
