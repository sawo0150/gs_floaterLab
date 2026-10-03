# ERVS balancing strength τ on B (2026-10-03)

Status: **EVIDENCE — complete, 8 new runs** (seed 0, four B scenes, budget 25), all gates passed.
[PREREG](PREREG.md) (`d81fe5e`). Raw `results/campaigns/gain_attribution/ervs_tau_strength/v1/`; page
https://claude.ai/artifact/4tcFwhyDosU5oDZ5vrgYZC (builder `build_ervs_tau_page.py`). The scene-extension run was
paused after table_04 uniform_iid_s1 (in-flight table_05 ervs_k16_s1 archived as `paused_for_tau_*`) and resumed.

## Results (mean of 4 scenes; Δ vs uniform with replacement)

| Arm | exp(−1/τ) | dense CV | KF CV | PSNR | ΔPSNR | Δmin-bin | Δworst-Q1 | dense services ÷ uniform: first 20% / 40–80% / last 20% |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| uniform_iid | 1 | 0.92 | 0.61 | 23.68 | — | — | — | 1 / 1 / 1 |
| ERVS τ=4 | 0.78 | 0.76 | 0.61 | 23.88 | **+0.21** | +0.01 | +0.00 | 0.89 / 1.09 / 1.06 |
| ERVS τ=1 | 0.37 | 0.58 | 0.50 | 23.65 | −0.02 | −0.44 | −0.22 | 0.69 / 1.18 / 0.98 |
| ERVS τ=0.25 | 0.018 | 0.35 | 0.38 | 22.94 | −0.74 | −1.47 | −1.20 | 0.55 / 2.02 / 2.45 |

Per-scene ΔPSNR: τ=4 +0.19/+0.19/+0.22/+0.24; τ=1 −0.04/−0.02/−0.09/+0.08; τ=0.25 −1.76/−0.44/−0.59/−0.15
(aria1253, table_06, rot, square-1). Five-bin paired Δ: τ=1 −0.87/−0.28/+0.55/+0.39/+0.11;
τ=0.25 −2.07/−1.64/−1.03/+0.26/+0.79.

## Reading

- Smaller τ does balance: dense CV 0.92 → 0.76 → 0.58 → 0.35 and services move from early-arriving to later views.
- Quality falls monotonically with stronger balancing: starving early views costs far more on the early stream than
  the late stream gains (τ=0.25 −2.1 dB on the first fifth). τ=4 is the best of the three, matching the 3dgs-custom
  per-view τ sweep (stronger balancing monotonically worse).
- Single seed; τ=4 seed-0 cells sit above its 3-seed mean (+0.09 on these scenes).

## Follow-up analysis (CPU only, same 16 runs) — `analyze_ervs_replay_rate.py`, `replay_analysis.json`

- **Replay rate** (final-generation services ÷ steps since first service; uniform scene mean = 1): dense views that
  arrived in the first 20% get 1.33 under uniform, 1.17 at τ=4, 0.98 at τ=1, 0.71 at τ=0.25. Stronger balancing lowers
  how often old views are revisited.
- **View identity explains most per-view PSNR variance**: 80% on average (aria1253 55%, table_06 94%, rot 80%,
  square-1 93%); sampler choice explains the rest.
- **Local training still matters**: on the same held-out view, doubling the services of training views within ±1.5% of
  the stream changes PSNR by +0.93 / +1.49 / +1.67 dB (τ=4 / 1 / 0.25; r = 0.23 / 0.45 / 0.53).
- At τ=0.25 views whose local training was unchanged or up to ×1.27 still lose 1.1–1.4 dB: part of the cost is non-local
  (map-wide degradation from starving old views), not only less local training.
- Reading: count balancing is the wrong target; equal per-view totals cut the revisit rate of old views (forgetting),
  while the PSNR profile itself is set mostly by the scene.
