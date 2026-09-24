# exp103 — generation-scoped ERCB dense topology evidence

- Date: 2026-09-24
- Status: RPNG `table_01` quality/isolation/correctness gate **PASS**
- Corrects: Exp102 persistence accounting only
- VIGS source: `913b9da2` (bounded operator present but disabled)
- Runner: `benchmarks/online_gs/run_exp103_generation_scoped_dense_evidence.py`
- Results: `results/experiments/exp103_generation_scoped_dense_evidence/`
- Summary: [corrected evidence](benchmark_custom/exp103_generation_scoped_dense_evidence_20260924/summary.md)

## Correction

VIGS creates a fresh `GaussianModel` after map reset, so stable point IDs are
stable only within one active map generation. Exp102 accumulated bare IDs and
could conflate different Gaussians that reused the same integer. Exp103 binds
every model instance to the harness generation and uses
`(map_generation, point_id)` for counters, live-set membership, and consecutive
set overlap. The overlap state is cleared at every generation boundary.

## Result

| Run | PSNR | Renders | Adam | Final GS | Map generations |
|---|---:|---:|---:|---:|---:|
| Exp103 corrected probe | **25.579016** | 38,302 | 3,030 | 417,637 | 3 |
| Exp95 normalized R4 | 25.585018 | 38,302 | 3,030 | 417,656 | — |
| Fresh vanilla | 23.964263 | 38,302 | 3,027 | 183,283 | — |

Exp103 is **−0.006001 dB** from R4 and **+1.614753 dB** over fresh vanilla.
The archive/config/events, dense admission, dense and keyframe opportunity UID
sequence, physical renders, Adam work, topology count 2/2, held-out
disjointness, zero-tail, and saved-map double evaluation all pass.

Across 269 dense opportunities, the top 256 / 1,024 / 4,096 rows capture
14.15% / 29.85% / 54.27% of gradient mass. Within-generation consecutive
top-1,024 Jaccard is 0.3175. At top-1,024, 39,371 generation-scoped IDs were
nominated; 26,534 occurred at least twice, 21,358 at least three times, and
25,330 repeatedly nominated IDs from the final generation remain live.

## Decision

The corrected evidence still supports a bounded local topology experiment.
Only final/current-generation nominations may be consumed. The first active
test will preserve R4 birth/prune and existing topology cadence, require at
least two dense nominations, and use the downloaded Taming 3DGS author's
without-replacement weighted ticket operator. It must add no render or Adam
step and retains the −0.5 dB quality stop. No hard pruning is introduced.
