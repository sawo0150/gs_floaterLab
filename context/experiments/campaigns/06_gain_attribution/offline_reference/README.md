# Offline (deferred-training) reference vs online samplers — stage 1 (2026-10-03)

PREREG: [PREREG.md](PREREG.md) (+ Amendment 1). Runner `benchmarks/online_gs/campaigns/gain_attribution/run_offline_reference.py`,
patch `offline_patch.py`. Results `results/campaigns/gain_attribution/offline_reference/v1/`. 12 offline runs
(4 scenes × seeds 0–2), all gates PASS: final-generation renders equal online, KF and dense sets identical to online,
per-view counts KF 12–13 / dense 8–9, Gaussians within −6%…+1% of online.

d(v) = PSNR_online(v) − PSNR_offline(v), seed-paired, held-out views; slope = Spearman of the 10% moving average of d
over the first 90% of the stream. Mean over 12 scene-seeds:

| online arm | mean d | slope (signed) | mean |slope| | bins 0–20 … 80–100% |
|---|---:|---:|---:|---|
| uniform_iid | −1.48 | −0.15 | 0.27 | −1.22 / −1.46 / −1.77 / −1.80 / −1.16 |
| uniform_k16 | −1.41 | −0.30 | — | −1.02 / −1.32 / −1.63 / −1.80 / −1.29 |
| ERVS K16 | −1.41 | +0.00 | 0.29 | −1.44 / −1.47 / −1.43 / −1.62 / −1.09 |

Per scene mean d (uniform_iid): aria1253 −2.27, table_06 −0.56, aria1253rot −2.19, square-1 −0.91.

**Pre-declared tests.** (1) mean |slope_ERVS| < |slope_uniform_iid|: **fails** (0.29 vs 0.27). (2) late-bin (60–100%)
d of ERVS above uniform_iid: passes (−1.35 vs −1.48). The predicted shape "d > 0 early, < 0 late" is **not** observed:
online is below offline everywhere; the gap is mainly a level offset (0.4–2.4 dB), with a mid-stream trough
(40–80%) under uniform that ERVS reduces at the cost of the first 20%. Only square-1 shows the predicted monotone
tilt (uniform −0.64 → ERVS −0.36 at seed 0; −0.50 → −0.20 over seeds).

**Open confound.** Offline trains with final poses and after all births; online trains with poses current at the
time. The level gap (largest on the Aria scenes, ~2.2 dB) cannot yet be attributed to count allocation. A
decomposition arm (deferred training with online's per-view counts) is needed before the gap is read as sampling bias.
