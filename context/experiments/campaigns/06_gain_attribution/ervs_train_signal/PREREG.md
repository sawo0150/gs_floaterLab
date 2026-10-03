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

## Amendment 1 — stage 3 (2026-10-03, after analysing stages 1–2; user granted autonomy for this study)

Arms (four scenes, budget 25): `sig_interference` (MIR-inspired: rank of log(1+mid) − log(1+near) training steps since
the last visit, near ±1.5%, mid 1.5–9% of the stream, mixed with staleness ρ=0.3, T=0.3), `sig_loss_per` (PER,
p ∝ (last loss + 1e-3)^0.7, no staleness), both seed 0; plus `uniform_iid_log_s1` and `ervs_tau4_log_s1` (seed 1) to
measure seed noise. 16 runs. Motivation: stage-1 interference analysis; user request for plain loss-based sampling;
single-seed differences unresolved.

## Amendment 2 — stage 4 (2026-10-03, after analysing stage 3)

`sig_interference` seeds 1–2, `uniform_iid_log` seed 2, `ervs_tau4_log` seed 2, and `sig_stale_only` (the interference
sampler with ρ = 1, i.e. staleness distribution only) seed 0. Four scenes, budget 25, 20 runs. Purpose: 3-seed
comparison of uniform / ERVS τ=4 / interference on mean, min-bin and worst-Q1, and attribution of the interference gain.

## Amendment 3 — stage 5 (2026-10-03, after the mean-vs-flatness analysis of all stage 1–4 samplers; user approved)

Question: can a sampler keep the mean held-out PSNR while making the temporal PSNR curve flatter? Analysis of
stages 1–4 showed every sampler so far redistributes training zero-sum (some views starve below the uniform rate),
and only loss-based samplers lowered temporal unevenness. Stage 5 adds a **uniform floor**: within each pool,
p = (1−λ)·uniform + λ·target share, inside the same persistent K=16 Gumbel group queue; unseen views keep priority.
Targets: `floor_region` (regional forgetting: best − last training PSNR, ≥0, averaged over views within ±1.5% of the
stream) and `floor_loss` (last training loss). λ ∈ {0.25, 0.5}. Four scenes, budget 25, seed 0, 16 runs.
Pre-declared success: mean PSNR ≥ uniform_k16 (seed 0) **and** temporal sd over deciles 1–9 below uniform_k16, both
as the 4-scene mean. Single seed: a pass is only a candidate for seeds 1–2, not a result.

## Amendment 4 — stage 6 (2026-10-03, after stage 5; user approved, "if this fails too, keep ERVS")

Stage 5 showed a per-draw uniform floor does not protect the low-count tail; only the ERVS count term does. Stage 6
keeps the ERVS τ=4 count weight inside the K=16 Gumbel group queue and multiplies it by a mild quality factor:
log w = −(n − n_min)/scale + log(1 + c·loss/mean seen loss), c ∈ {0.5, 1.0}; unseen views get the neutral factor
(no unseen priority, as in ERVS). Four scenes, budget 25, seed 0, 8 runs. Success as in Amendment 3, now against
ERVS τ=4 seed 0 as well: mean PSNR ≥ uniform_k16 and ≥ ERVS − 0.05, and temporal sd below ERVS. If no arm passes,
ERVS τ=4 stays the method (user decision).
