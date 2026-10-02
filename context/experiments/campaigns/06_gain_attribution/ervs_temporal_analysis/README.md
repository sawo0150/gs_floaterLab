# ERVS/ERCB vs RR: temporal and tail metrics on two systems (2026-10-02)

Status: **ANALYSIS — post-hoc, no new training.** Metrics chosen after the B results were seen; descriptive.

Script: `benchmarks/online_gs/campaigns/gain_attribution/analyze_ervs_temporal.py`.
Raw/figures: `results/campaigns/gain_attribution/ervs_temporal_analysis/v1/` (`aggregate.csv`, `per_scene_deltas.json`,
`B_temporal_curves.png`, `ercb_temporal_curves.png`, `delta_vs_time.png`).

## Inputs

| System | Sampler pair | Runs | Per-view PSNR source |
|---|---|---|---|
| B (VIGS-SLAM-custom `6d200f0f`, fixed-work frozen-tracker replay, seed 0) | cumulative ERVS vs RR | 4 scenes × budgets 5/10/15/25 renders/KF; budget 40 on rot, rpng (pilot) | fixed held-out manifest, frame-indexed |
| 3dgs-custom benchmark-B (offline replay, final VIGS pose/init, RGB-only, fixed topology, stride20, seed 0) | original interval ERCB vs RR | 19 scenes × 15/30/60 updates/event | `evaluation_curve.jsonl` final test split, timestamp order |

## Metric definitions

- `mean`: mean per-view held-out PSNR.
- `worst_q1`: mean of the arm's own lowest ⌈n/4⌉ views (ERCB_ablation definition).
- `rr_hard_q1`: mean PSNR on RR's lowest ⌈n/4⌉ views, same view set for both arms (ERCB_ablation definition).
  **Selection-biased toward the challenger** (views are chosen where RR happened to be low; regression to the mean
  favours any other arm), so it must not be the only tail metric.
- `early` / `late`: mean PSNR of the first / last 25% of held-out views in time order; `drop` = late − early.
- `std`: standard deviation of per-view PSNR within a scene (dispersion).
- Curves: centred moving average over 15% of the views, x = normalized time.

## Aggregate ERVS/ERCB − RR (scene means; wins = scenes where the challenger is better)

| System | Budget | Scenes | Mean | worst-Q1 | RR-hard-Q1 | Early | Late | Drop | Std (lower=better) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| B | 5 | 4 | +0.27 (4/4) | **+0.71 (4/4)** | +1.21 (4/4) | −0.06 (1/4) | +0.05 (2/4) | +0.11 | **−0.26 (4/4)** |
| B | 10 | 4 | +0.02 (2/4) | **+0.22 (4/4)** | +0.62 (4/4) | −0.05 (3/4) | −0.02 (1/4) | +0.04 | **−0.19 (4/4)** |
| B | 15 | 4 | +0.12 (3/4) | **+0.24 (4/4)** | +0.65 (4/4) | −0.03 (2/4) | +0.14 (4/4) | +0.17 | −0.03 (1/4) |
| B | 25 | 4 | −0.07 (1/4) | +0.04 (2/4) | +0.30 (3/4) | −0.17 (1/4) | +0.05 (3/4) | +0.22 | −0.04 (2/4) |
| B | 40 | 2 | −0.03 (1/2) | −0.16 (0/2) | +0.03 (2/2) | −0.29 (1/2) | +0.26 (1/2) | +0.55 | +0.05 (0/2) |
| 3dgs-custom | 15 | 19 | +0.62 (16/19) | +0.35 (12/19) | +1.03 (13/19) | **+1.97 (18/19)** | **−1.01 (3/19)** | −2.98 | +0.26 (5/19) |
| 3dgs-custom | 30 | 19 | +0.11 (7/19) | −0.01 (11/19) | +0.37 (16/19) | +0.37 (10/19) | −0.22 (9/19) | −0.58 | +0.08 (10/19) |
| 3dgs-custom | 60 | 19 | +0.23 (9/19) | +0.16 (13/19) | +0.60 (15/19) | +0.33 (8/19) | +0.06 (10/19) | −0.27 | +0.02 (10/19) |

## Reading

- **B, tail quality:** ERVS raises the worst-quarter views in 4/4 scenes at budgets 5, 10 and 15 (+0.71, +0.22,
  +0.24 dB) and lowers per-view dispersion in 4/4 at budgets 5 and 10, while the mean is scene-dependent. At 25/40 the
  tail effect disappears. Example: aria1253 at budget 5 — RR collapses to ≈16 dB over 30–50% of the sequence, ERVS
  stays near 20 dB.
- **B, time profile:** held-out PSNR along the sequence is scene-shaped (aria1253 falls toward the end; table_06 rises);
  there is no general late-sequence decline that ERVS flattens. ERVS−RR vs time has no consistent trend across
  budgets.
- **3dgs-custom, time profile:** PSNR does fall along many sequences, but ERCB's budget-15 gain is concentrated in the
  **early** part (+1.97, 18/19) and it is **worse late** (−1.01, 3/19 wins). The ERCB-family gain there is better
  coverage of older views, not protection of recent ones.
- RR-hard-Q1 is positive almost everywhere in both systems, partly by selection bias (see definition).

## Candidate wording (B system, needs multi-seed confirmation before use)

"Under scarce per-keyframe budgets (≤15 renders/KF), ERVS improves the worst-quarter held-out views in all four
scenes (+0.2–0.7 dB) and reduces per-view PSNR dispersion, while mean PSNR remains comparable to RR."
