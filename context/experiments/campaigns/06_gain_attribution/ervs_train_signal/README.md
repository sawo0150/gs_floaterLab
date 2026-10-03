# Training signals for replay (PSNR / loss / counts) — stages 1–2 (2026-10-03)

Status: **EVIDENCE — stages 1–2 complete** (8 + 20 runs, four B scenes, budget 25, seed 0). [PREREG](PREREG.md)
(`6d6fb6a`). Page: https://claude.ai/artifact/BFFg2zBqgAw8jW5vDk8a2U. Raw `results/campaigns/gain_attribution/ervs_train_signal/v1/`.
Code: `train_signal.py` (logger + samplers), `run_ervs_train_signal.py`, `analyze_train_signal.py`, `build_signal_page.py`.
Note: `train_signal.py` gained two modes (loss_per, interference) while stage 2 was running; the five stage-2 modes'
code paths were unchanged (new branches only).

## Stage 1 (logging only; uniform_iid, ERVS τ=4)

- Logging did not change training: identical service sequences and trajectories; held-out differs by ≤0.03 dB through
  GPU atomic nondeterminism (Gaussian count 211395 vs 211283) — this is the single-run noise floor.
- Forgetting is real: training-PSNR change at revisit (pooled, uniform) KF +0.66/+0.48/−0.01/−0.46/−0.28 dB and dense
  +0.52/+0.14/+0.01/−0.19/−0.45 dB for gaps 0–50/50–100/100–200/200–400/400–800 steps.
- Signals vs held-out (local ±1.5% mean, Spearman, 4-scene mean, uniform / ERVS): last training PSNR 0.77/0.79
  (0.45/0.49 after removing best training PSNR; ≡ −forgetting), staleness −0.25/−0.37, count −0.32/−0.45,
  progress +0.26/+0.23, maturity +0.09/+0.08 (difficulty-removed). First-visit dense PSNR (a novel-view probe) only
  0.45/0.43 (0.19/0.20 difficulty-removed); last training PSNR keeps 0.69/0.75 even after removing first-visit PSNR.
- Interference: between two visits, log-count of training on near views (±1.5%) raises the next-visit PSNR
  (+0.10…+0.40), mid-distance views (1.5–9%) lower it (−0.22…−0.44), far views barely (−0.02…−0.19) — 4/4 scenes.

## Stage 2 (signal samplers, K=16 group queue; Δ vs uniform_iid)

| Sampler | ΔPSNR aria/table_06/rot/sq-1 | mean | Δmin-bin | Δworst-Q1 | five-bin Δ | dense CV | early-10% dense ×uniform |
|---|---|---:|---:|---:|---|---:|---:|
| ERVS τ=4 | +0.21/+0.20/+0.25/+0.23 | +0.22 | +0.02 | +0.03 | +0.05/+0.47/+0.37/+0.12/+0.09 | 0.76 | 0.94 |
| age_norm | +0.21/−0.11/+0.01/+0.09 | +0.05 | −0.08 | −0.06 | −0.42/+0.33/+0.34/−0.11/+0.10 | 0.78 | 0.90 |
| forget_stale | −0.04/−0.13/−0.03/+0.07 | −0.03 | +0.01 | +0.16 | +0.27/+0.05/−0.12/−0.23/−0.13 | 1.02 | 1.13 |
| loss_stale | +0.07/−0.09/−0.16/+0.02 | −0.04 | +0.03 | +0.17 | −0.29/+0.16/+0.02/−0.18/+0.09 | 0.84 | 0.98 |
| progress_stale | −0.73/−0.09/−0.07/−0.05 | −0.24 | −0.13 | −0.37 | −0.32/−0.12/−0.57/−0.34/+0.17 | 0.79 | 0.97 |
| catchup | −0.92/−0.13/−0.08/+0.07 | −0.26 | −0.61 | −0.49 | −1.26/−0.98/−0.18/+0.50/+0.59 | 0.49 | 0.65 |

- forget_stale did reduce training-view forgetting (end forgetting dense 1.53→0.91 aria, 1.47→1.16 table_06) without
  held-out gain: training-view PSNR is a marker of local quality, not a lever.
- Early-view replay ratio vs first-bin Δ across 24 arm×scene cells: r = 0.70 (vs total ΔPSNR r = 0.10).
- catch-up (c·β^n + 1, c=30) behaves like strong count balancing (τ=0.25): early views ×0.55 on aria1253, −2 dB early.
- Single seed: ERVS τ=4 is +0.22 here vs +0.09 over 3 seeds on the same scenes; inter-sampler gaps ≤0.2 dB are not
  resolved. Stage 3 adds seed 1 for uniform and ERVS.

## Stage 3 (2026-10-03; interference, PER, seed-1 baselines)

| Arm (seed 0 unless noted) | ΔPSNR aria/table_06/rot/sq-1 vs uniform s0 | mean | Δmin-bin | Δworst-Q1 |
|---|---|---:|---:|---:|
| sig_interference | +0.11/+0.18/+0.09/+0.03 | +0.10 | +0.13 | +0.12 |
| sig_loss_per | −0.24/−0.24/+0.03/+0.05 | −0.10 | +0.15 | +0.01 |

Seed noise (seed 1 − seed 0, mean |Δ| over 4 scenes): uniform 0.04 (mean PSNR) / 0.30 (min-bin) / 0.22 (worst-Q1);
ERVS τ=4 0.12 / 0.16 / 0.22. Min-bin and worst-Q1 single-seed differences below ~0.2 dB are not resolved.
Against the uniform seed 0/1 mean: ERVS τ=4 (2 seeds) +0.16 / +0.07 / 0.00 (4/2/3 scenes positive);
sig_interference (seed 0) +0.10 / +0.23 / +0.16 (4/4/3). Interference exposure is the only signal sampler that beats
uniform in all four scenes, and it lifts the worst time bin; needs more seeds and a staleness-only control.

## Stage 4 (3 seeds; staleness control) and conclusion (2026-10-03)

Δ vs uniform_iid, means of 3 seeds per scene (aria1253 / table_06 / rot / square-1 → mean):
- ERVS τ=4: PSNR −0.10/+0.15/+0.15/+0.09 → **+0.07** (3/4); min-bin +0.03; worst-Q1 −0.06.
- sig_interference: PSNR −0.23/+0.08/−0.01/+0.08 → **−0.02**; min-bin +0.02; worst-Q1 −0.08. The seed-0 4/4 gain
  (+0.10, min-bin +0.23) was seed noise.
- sig_stale_only (seed 0): −0.39/+0.01/+0.03/+0.20 → −0.04.
Uniform seed spread per scene up to 0.2 dB on mean PSNR (aria1253 24.60/24.57/24.76).
ERVS τ=4 aria1253 seed 2 collapses again (24.03; same tracker trajectory, resets, Gaussian count): only the first 40%
of the stream drops (bins 25.20/23.31 vs 25.98–26.56/25.42–26.09 at seeds 0–1), the failure mode of reduced early
replay.

**Conclusion.** Training forgetting is real and driven by mid-distance training, and last training PSNR tracks
held-out quality, but no replay signal tested (forgetting, progress, loss, PER, catch-up, age-normalized maturity,
interference exposure, staleness) beats uniform sampling with replacement over seeds; ERVS τ=4 keeps a small mean gain
(+0.07 over 3 seeds here, +0.09 in ervs_vs_iid_seeds) without lifting the worst regions. Single-seed differences
below ~0.2 dB (mean) and ~0.3 dB (min-bin, worst-Q1) are not resolvable on these scenes.
