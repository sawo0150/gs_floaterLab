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

## Stage 2 — 15 extra scenes, offline seed 0 (2026-10-04, Amendment 2)

15 runs, all gates PASS. Page: `results/.../offline_reference/v1/offline_compare.html` (artifact ALuTKiHsUjKesE9wVJ4dh1).
19 scenes, online seed mean vs offline (pinned: seed-paired; extra: offline seed 0).

| | uniform_iid | uniform_k16 | ERVS K16 |
|---|---:|---:|---:|
| mean gap online − offline (dB) | −1.06 | −0.95 | −1.02 |
| centred-gap MAD, first 90% (dB, lower = more constant) | 0.511 | 0.495 | 0.560 |
| cumulative-training front-loading (0 = offline) | 0.275 | 0.291 | 0.271 |
| bins 0–20 … 80–100% | −1.08/−1.23/−1.00/−1.04/−0.95 | −0.88/−1.01/−0.83/−0.99/−1.05 | −1.33/−1.19/−0.78/−0.81/−0.97 |

Paired over scenes (bootstrap 95%): MAD ERVS − iid +0.049 [−0.019, +0.124], lower in 7/19; ERVS − K16 +0.065
[−0.016, +0.169], 8/19. Front-loading ERVS − iid −0.004 [−0.016, +0.009], 15/19; ERVS − K16 −0.020 [−0.025, −0.013],
17/19 (the count term reduces front-loading consistently but by a small amount; every online arm stays far from 0).
Range of mean gap: −0.07 (table_04) … −4.17 dB (aria301_305).

**Reading.** The data do not support "ERVS keeps the gap to offline constant over time": on 19 scenes the gap is no
more constant under ERVS than under uniform (7/19), and the 19-scene mean curve shows ERVS trading the first 20%
(−1.33 vs −1.08) for the middle (40–80%). What holds is the allocation statement: ERVS lowers count dispersion
(CV 0.91 → 0.76 dense on the 4 scenes) and, against the same-group uniform arm, front-loading in 17/19 scenes.

**Incident.** Stage 2 outputs were first written under `ervs_vs_iid_scenes/v1/offline/` because importing
`run_ervs_vs_iid_scenes` re-pointed `base.OUT`; that run also overwrote `ervs_vs_iid_scenes/v1/summary.{csv,json}`
(untracked, derived). Fixed in the runner; outputs moved to `offline_reference/v1/offline/` with paths rewritten in
30 JSON files; both summaries regenerated from all row.json files (scenes: 135 rows; offline: 27 rows).
