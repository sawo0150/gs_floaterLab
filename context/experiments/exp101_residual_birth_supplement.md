# exp101 — R4-preserving official residual-birth supplement passes quality

- Date: 2026-09-24
- Status: RPNG `table_01` quality/structure gate **PASS**; single-scene only
- VIGS source: `96de04b3`
- Official implementation source: Gaussian-SLAM
  `eaec10d73ce7511563882b8856896e06d1f804e3` (MIT)
- Runner: `benchmarks/online_gs/run_exp101_residual_birth_supplement.py`
- Results: `results/experiments/exp101_residual_birth_supplement/`
- Summary: [metrics and cost](benchmark_custom/exp101_residual_birth_supplement_20260924/summary.md)

## Result

Exp101 preserves R4 blanket PPM birth and its RNG stream, then uses a separate
RNG stream to add only low-alpha/positive-depth-residual candidates through
the current-frustum radius rejection ported from the downloaded author code.
The supplemental allocation is the same causal per-view R4 target, not a
scene-tuned fixed ticket.

| Run | PSNR | SSIM | LPIPS | Renders | Adam | GS |
|---|---:|---:|---:|---:|---:|---:|
| Exp101 supplement | **25.609319** | **0.848595** | **0.149098** | 38,302 | 3,030 | 634,950 |
| Exp95 normalized R4 | 25.585018 | 0.847780 | 0.153816 | 38,302 | 3,030 | 417,656 |
| Fresh vanilla | 23.964263 | 0.794350 | 0.198004 | 38,302 | 3,027 | 183,283 |

Candidate−R4 is **+0.024301 dB** and candidate−vanilla is **+1.645055 dB**.
Both saved-map evaluations agree exactly. Full-view causal density trace,
archive/events, physical renders, Adam work, dense/KF opportunity skeletons,
topology count 2/2, held-out disjointness, and zero-tail all pass.

Across 235 events, the preserved baseline admitted 498,627 births. The
official residual service offered 324,428 more, accepted 286,549, and rejected
37,879 as current-frustum duplicates. This proves the port is materially
active rather than a narrative-only module.

## Cost and decision

The quality is preserved, but the 1× supplemental allocation is not the final
method. Versus Exp95 it raises final GS by 52.0% (417,656→634,950), mapping wall
time by 11.2% (165.90→184.53 s), peak allocated memory by 26.1%
(5.092→6.419 GB), and peak reserved memory by 84.6% (8.670→16.008 GB), for only
+0.024 dB PSNR. Final-generation regular topology churn also rises 68,517→
91,652 rows (+33.8%).

Therefore Exp101 establishes the safe composition rule—supplement, not
replacement—but not an efficient contribution. The next step is to let causal
dense/ERCB evidence ration or nominate this local service while preserving the
R4 baseline and the same quality gate. Strict-live feasibility remains
untested.
