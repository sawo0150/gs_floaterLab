# Preregistration — training signals (PSNR / loss / counts) for replay, two stages (2026-10-03, before any run)

User request (/loop): analyse every proposed signal (training PSNR, loss, counts, maturity, staleness) in stage 1, then
test samplers built on them in stage 2. Four B scenes (aria1253, table_06, aria1253rot, square-1), budget 25, seed 0.

Instrumentation (`train_signal.py`): sha-checked copy of `OnlinePhotometricTrainer.step` with one injected hook after
the loss; per render it records training PSNR and RGB L1 of the render against the view's own target and the scalar
loss, without gradients or extra renders (`train_signal.json`).

## Stage 1 — logging only (8 runs)

uniform_iid (`sampling_mode_patch.py`, with replacement, τ=1e12) and ervs_tau4 (`group_k_patch.py`, K=16, τ=4), each
launched through the logger. Check: held-out PSNR equals the earlier seed-0 runs (logging must not change training).
Analyses (CPU): per-view training-PSNR trajectories; forgetting = drop between consecutive visits vs steps elapsed and
vs view age; whether last training PSNR / forgetting / counts / staleness / age-normalized maturity explain held-out
PSNR (local ±1.5% window); difficulty confound (view's best training PSNR vs held-out).

## Stage 2 — signal samplers (20 runs)

K=16 per-pool group queue, weights from the per-view state of the current generation; unseen views first.

| Mode | Weight | Fixed parameters |
|---|---|---|
| forget_stale | (1−ρ)·rank(best − last training PSNR)^(1/T) + ρ·staleness | ρ=0.3, T=0.3 |
| progress_stale | same with learning progress (last − previous training PSNR)⁺ | ρ=0.3, T=0.3 |
| loss_stale | same with last training loss | ρ=0.3, T=0.3 |
| catchup | c·β^n + 1 (Curious-Replay count term with a uniform floor) | β=0.7, c=30 |
| age_norm | exp(−(m−1)/τ), m = n / (steps since first service × pool rate) | τ=1 |

References: uniform_iid and ervs_tau4 seed 0 (existing). Metrics: held-out PSNR, min-bin PSNR, worst-Q1, five-bin
paired Δ vs uniform_iid, service counts and replay rate by arrival time, forgetting under each sampler. Single seed,
exploratory; all cells reported. The scene-extension run is paused during both stages and resumed afterwards.
