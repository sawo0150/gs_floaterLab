# B ablation v2 — regime-aligned ERVS and role-quota experiments (plan, 2026-10-01)

Status: **PLAN — not yet preregistered or run.** After approval, the decision rules below are frozen
into `PREREG.md` (+ sha256) and committed before the first run.

Predecessor: [b_ablation_chain pilot](../b_ablation_chain/README.md) (24 runs, single seed).
Background: [ERCB_ablation](../../../ERCB_ablation/README.md) (3dgs-custom offline replay).

## 1. What the pilot and prior work established

| Evidence | Result | Consequence for v2 |
|---|---|---|
| Pilot R2→R3/R4 | dense RGB +0.19 … +0.55 dB, 4/4 | already strong; confirm with seeds, not redesign |
| Pilot R3 vs R4 | pacing vs immediate admission: no difference | B's fixed 3:3:6 quota caps the dense share at 6/12, so immediate admission cannot dilute keyframe service |
| 3dgs-custom dense-supervision | single uniform pool, all frames: K=all −0.72 dB vs K=4 +0.19 (RPNG table_03) | dilution is real when keyframes lose their share |
| 3dgs-custom benchmark-B | ERCB−RR +0.62 (budget 15), +0.11/+0.23 (30/60) | sampler gains appear under scarce per-view budget |
| 3dgs-custom KF-only RR control | +0.49 of the +0.62 came from emphasising keyframes | in B, the quota already does this; ERVS's marginal effect is smaller |
| Pilot ERVS−RR | budget 15: +0.13/+0.45; budget 40: −0.28/+0.22; recent-third 5/6 positive | test at the real operating budget, with mechanism-aligned metrics |
| Pilot mechanism | ERVS lowers keyframe-pool service CV 6/6, not dense CV | report the keyframe-pool balance as the mechanism |

## 2. Operating point (why the low-budget regime is the honest one)

Realised training renders per admitted KF in the live FIFO runs (RTX 5090, ours, `docs/LIVE_FIFO_COMPARISON.md`;
completed renders / KF admissions of the fixed-40 replay):

| Scene | 1× | 1.5× |
|---|---:|---:|
| aria1253 | ≈27.7 | ≈30.6 |
| table_06 | ≈20.6 | ≈29.3 |
| square-1 | ≈22.7 | ≈22.7 |
| aria1253rot | ≈29.8 | ≈35.8 |

Real time delivers about **20–30 renders/KF on a 5090** (less on a 5070 Ti; those live runs also paid D3 proxy
renders, so B may realise a few more). Budget 40 is above the live operating point. v2 therefore spans
**10, 15, 25, 40**, and reports 25 as the live-representative budget. (Before freezing the PREREG, re-derive these
numbers from the live artifact JSON instead of the document table.)

## 3. Claims to test

- **C1a dense RGB beyond keyframes improves held-out quality** (pilot signal; confirm).
- **C1b role separation prevents dilution**: when the keyframe share of service falls toward its uniform-pool value
  (|K|/(|K|+|D|) ≈ 8–10%), quality drops; B's fixed keyframe share prevents this. This replaces the pacing claim,
  which the pilot did not support.
- **C2 ERVS under scarce budgets**: ERVS improves convergence and recent-region quality when per-view service is
  scarce; with ample budget both samplers reach similar endpoints.

## 4. Design

Dev scenes (fixed now): aria1253, aria1253rot, RPNG table_06, UTMM square-1 (the four B-pinned scenes).
Seeds 0, 1, 2. All runs: official B worker + recipe + environment, override arguments only (pilot runner pattern),
fixed-work frozen-tracker replay, zero tail, 1 image = 1 Adam step.

### Part A — ERVS vs RR across budget (C2)

| Factor | Levels |
|---|---|
| Budget (renders/KF) | 10, 15, 25, 40 |
| Sampler | ERVS (B), RR (`--selector rr`) |
| Scenes × seeds | 4 × 3 |

96 runs. **Snapshots on** (checkpoint curves).

### Part B — keyframe share / role separation (C1a, C1b)

All with immediate admission (`--membership immediate`) so that the dense pool is maximal and only the quota decides
the keyframe share; window kept at 3 except the last row.

| Arm | Quotas (window : KF pool : dense) | Keyframe share | Meaning |
|---|---|---:|---|
| Q-kf | 3:3:6 + `--auxiliary-mode kf_native` | 12/12 | no dense RGB (R2) |
| Q6 | 3:3:6 | 6/12 | B's share (= pilot R3) |
| Q3 | 3:0:9 | 3/12 | reduced |
| Q1 | 1:0:11 | 1/12 ≈ 8% | ≈ uniform single pool |

Budgets 15 and 25; 4 scenes × 3 seeds → 96 runs (Q6 at 15/25 is shared with nothing in Part A because Part A uses
growth admission; keep it separate). Prediction: Q6 > Q1 and Q3 in most cells; Q6 > Q-kf (C1a).
If Q1 ≈ Q6, the dilution argument does not hold in B and C1b is dropped.

### Optional Part C — confirmation

After A/B, freeze one budget (expected 25) and run B vs the strongest control on all 20 scenes, seed 0, using the
CVPR runner inputs (`rtx5070ti_references_v5/inputs`). Not part of the dev-scene decision.

## 5. Metrics (order of reading)

1. **Mechanism** (from run records): per-view completed service counts vs admission time; keyframe-pool and dense CV;
   never-served views; realised keyframe share. A quality claim is read only if its mechanism moved.
2. **Recent-region quality**: recent-third held-out PSNR (definition as in the pilot); Fig. 4 new-region
   convergence for the same runs.
3. **Convergence**: checkpoint PSNR vs completed updates → area under the curve and updates to reach a fixed
   fraction of the B endpoint.
4. **Endpoint**: whole-cohort PSNR/SSIM/LPIPS (always reported, never hidden).

## 6. Decision rules (to freeze in the PREREG)

- Noise: per scene/budget/metric, the seed spread of the same arm (max over compared arms).
- Resolved: same sign in all three paired seeds and |mean Δ| > 2 × noise.
- **C2 holds** if ERVS−RR on recent-third PSNR or AUC is resolved-positive in ≥3/4 scenes at budget ≤25, and the
  keyframe-pool CV is lower under ERVS. Budget-40 results are reported whatever their sign.
- **C1b holds** if Q6−Q1 is resolved-positive in ≥3/4 scenes at either budget.
- No κ/τ/quota tuning after seeing results; all scenes and budgets reported.

## 7. Paper outputs

| Output | Source |
|---|---|
| Figure: ERVS−RR vs budget, with the live operating band shaded | Part A |
| Figure: service count vs admission time, RR vs ERVS | Part A records |
| Table: chain R1→R4 (pilot rows + seeds) | pilot + Part B (Q-kf, Q6) |
| Table/figure: keyframe share vs PSNR | Part B |
| Supplement: 3dgs-custom single-pool results (dilution, ERCB) as controlled mechanism evidence | existing ERCB_ablation |

## 8. Implementation tasks before running

1. Runner v2 from `run_b_ablation_chain.py`: parameterised arms/budgets/seeds, snapshot capture (port from
   `run_cvpr_measurements.install_snapshots`), checkpoint evaluation stage.
2. Link aria1253 and square-1 inputs as for rot/rpng; run the B preflight for all four scenes.
3. Re-derive the live operating point from the artifact JSON.
4. Verify the Part B quota arms with one smoke run each (realised keyframe share from the service log).
5. Disk: ~23 GB free; snapshots add ~150 MB/run → keep snapshots only for Part A or prune after curve evaluation.

## 9. Cost (RTX 5070 Ti, sequential)

Part A 96 + Part B 96 = 192 runs, ≈ 3–4 min each plus checkpoint evaluation → roughly 12–15 h. Splitting scenes
with colin (5090, idle) halves it; wall times are then not compared across GPUs.

## 10. Records

- Card: `context/experiments/campaigns/06_gain_attribution/b_ablation_v2/` (`PLAN.md`, `PREREG.md`, `README.md`)
- Runner: `benchmarks/online_gs/campaigns/gain_attribution/run_b_ablation_v2.py`
- Raw: `results/campaigns/gain_attribution/b_ablation_v2/v1/<part>/<scene>/render<budget>/<arm>_s<seed>/`
- On completion: card + INDEX + STATUS.
