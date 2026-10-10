# Experiment Index

- 2026-10-03 effect decomposition, 19 scenes × 3 seeds (budget 25): K=16 without-replacement group vs with replacement +0.106 dB [+0.04,+0.18] (14/19); ERVS count term vs uniform group −0.061 [−0.14,+0.00] (6/19); total ERVS vs iid +0.045. Worst-region metrics not improved by either. → [card](campaigns/06_gain_attribution/ervs_vs_iid_scenes/README.md)

- 2026-10-03 ERVS K16 vs uniform with replacement, 19 scenes × 3 seeds (budget 25): ΔPSNR +0.045 [−0.01,+0.10] (11/19), min-bin −0.08, worst-Q1 −0.11 [−0.21,−0.00]; dense CV 0.74 vs 0.91; five-bin Δ −0.25/+0.04/+0.22/+0.22/−0.01. → [card](campaigns/06_gain_attribution/ervs_vs_iid_scenes/README.md)

- 2026-10-10 UTMM reference-start rerun (8 scenes) + new datasets (StaticHikes, MipNeRF360, T&T): UTMM I at density 0.75 beats uniform density 1 on 8/8 (+0.21 dB, −33 % Gaussians; straight scenes +0.30…+0.64 dB); new datasets show no I gain (I0.75 −0.08 dB) and no gain from more Gaussians either (PSNR 15–20 dB, count not the bottleneck); garden tracking failed. → [card](campaigns/06_gain_attribution/utmm_scene_screen/README.md)
- 2026-10-10 UTMM 8-scene screen, insertion (I) vs uniform × density (2N): 5 scenes map (3 straight-line scenes never finish IMU init). I at density 0.75 beats uniform at density 1 on all 5: PSNR +0.07 (+0.01…+0.13), LPIPS −0.008, Gaussians −32 %; I lies above the uniform count–PSNR curve at every density. → [card](campaigns/06_gain_attribution/utmm_scene_screen/README.md)
- 2026-10-09/10 insertion (I) × density × budget complete for ETH3D/Aria/TUM/UTMM/RPNG table_01+table_02 (132 runs): UTMM is the only scene with a PSNR gain from I (+0.09…+0.24 dB, larger at ¼ density); table_02 shows no I effect (LPIPS slightly worse); matched-PSNR Gaussian reduction ETH3D −78%, TUM −77%, RPNG −50…−75%, Aria −19…−58%, UTMM −16%, mostly from lower density with an LPIPS cost outside ETH3D. → [card](campaigns/06_gain_attribution/geom_ablation_density/README.md)
- 2026-10-09 insertion (I) vs budget (1N/2N/6N; ETH3D sofa_1, Aria 305, TUM fr1_desk): PSNR Δ stays within ±0.12 dB at every budget; SSIM up 17/17; Gaussians −2…−19% at all budgets. Scarce budget does not turn I into a PSNR gain. → [card](campaigns/06_gain_attribution/geom_ablation_init/README.md)
- 2026-10-09 content-aware insertion (I) on Aria/ETH3D/RPNG (5 scenes, seed 0; UTMM unsupported by the C frontend): R1→R1-I PSNR +0.03, SSIM +0.005, Gaussians −7.6%; R2→R2-I PSNR +0.04, SSIM +0.004, Gaussians −12.2%; SSIM up 10/10, Gaussians down 10/10. Same pattern as TUM (−10%) and exp55: efficiency, not PSNR. → [card](campaigns/06_gain_attribution/geom_ablation_init/README.md)
- 2026-10-09 local TUM10 geometry ablation (colin suite snapshot, R1→R1-I→R2-I→R3→R4, 51/51, seed 0, 6N): KF-pool replay +3.26 dB / −3.1 cm depth MAE (10/10); dense pool + normal/depth losses SSIM +0.031, LPIPS −0.021, depth −0.5 cm, PSNR ≈0; content-aware insertion and SEW3 carving ≈0; FM export −0.03 dB, −15% Gaussians. Snapshot harness bug (uniform init under the density wrapper) fixed locally. → [card](campaigns/06_gain_attribution/geom_ablation_local/README.md)
- 2026-10-09 recipe D (= C + scale cap 0.5 + selective births) vs C, local 5070 Ti, scenes that fit in 16 GB (seed 0, 6N): local C matches colin C within ±0.03 dB; D − C PSNR Aria 0416_301-1253 +0.43, ETH3D sofa_1 +0.29, TUM fr1_desk +0.07 (3/3), SSIM ≈, LPIPS +0.001…+0.006, Gaussians −38…−60%. RPNG table_06 / FAST-LIVO2 Retail_Street skipped (OOM). → [card](campaigns/06_gain_attribution/recipe_d/README.md)
- 2026-10-09 RPNG decomposition (cap 0.5) stopped by the user after 2 scenes (table_06, table_01: online/D2/D1 only). Paper uses the existing 6-scene ladder (decomposition_6scenes_clamp01.csv). → [prereg](campaigns/06_gain_attribution/decomposition_rpng/PREREG.md)
- 2026-10-09 RTG-like transparent births (covered births opacity 0.1 + scale cap 0.1, global cap 0.5; aria1253, rot, square-1): worse than C (−0.50, −0.57, −0.04) and B′ (−0.06, −0.43, −0.06): covered births are 82–91% of points, so most Gaussians fall back under a 0.1 bound. → [card](campaigns/06_gain_attribution/validation/README.md)
- 2026-10-09 validation phase 2 (6 scenes, seed 0): ERVS + cap 0.5 + selective births = 24.38 mean (+0.40 vs adopted 23.98, 5/6; +0.10 vs cap 0.5 alone, gains only on revisit/long scenes: aria +0.44, rot +0.14, Retail +0.09). Online−offline gap 1.36 → 0.96 dB. → [card](campaigns/06_gain_attribution/validation/README.md)
- 2026-10-09 validation phase 1 (6 scenes, seed 0, ERVS): scale cap 0.5 beats the adopted 0.1 clamp on 6/6 scenes, mean +0.30 dB (24.28 vs 23.98); clamp off +0.26 (4/6) but max scale up to 14. Rule → cap 0.5 selected. → [card](campaigns/06_gain_attribution/validation/README.md)
- 2026-10-09 multi-view free-space birth gate (new points in front of an old KF surface start at 0.02; 7–10% of points; ERVS, clamp off; aria1253 + square-1): aria 25.67 (+0.35 vs clamp-off 0.5 births; ≈ selective 25.72), square-1 21.96 (+0.04; selective 21.72). Evidence: per-birth damage vs free-space share corr −0.76. → [card](campaigns/06_gain_attribution/freespace_birth/README.md)
- 2026-10-09 refresh-loss trajectory check (no GPU): base and refresh runs match until ~1,800 renders; the loss is one 25-render training interval at the end where KFs 446–493 drop 7–11 dB. Clamp-off maps contain giant Gaussians (max scale up to 11.7, ~400 with scale>0.3 & opacity>0.3) → "floater lottery" in single clamp-off runs (11–26 catastrophic single-interval KF drops per run). → [card](campaigns/06_gain_attribution/track/README.md)
- 2026-10-09 settle-time single refresh (1 slot/batch, M=6; selective births, clamp off; aria1253 + square-1): aria 25.34 (−0.38; loss in the refreshed early fifths −1.44/−1.08, like the old consolidation), square-1 21.81 (+0.09). Mid-stream refresh does not reproduce the late-replay gain. → [card](campaigns/06_gain_attribution/track/README.md)
- 2026-10-09 why late replay helped (no GPU): births/corrections identical between window and no-window runs; difference is training only (+0.56 → +1.32 aria). ~85 extra late replays of old regions (≈ +1 per old view) bought +0.65 dB; no link between newer-view draws and old-KF losses. Per KF, gap to offline grows with staleness at end (+0.95 → +1.87). → [card](campaigns/06_gain_attribution/track/README.md)
- 2026-10-09 target-based catch-up window (3 slots to views below 0.6 × running per-view budget; aria1253 + square-1): aria 25.36 (−0.36), square-1 22.06 (+0.34, above D2). Slots were almost always full (mid/late dense views below target), counts barely moved; early views stay over-trained (~20 vs ~10) because the pool is tiny when budget starts. → [card](campaigns/06_gain_attribution/track/README.md)
- 2026-10-09 no window role after 70% of the stream (selective births, clamp off, ERVS; aria1253 + square-1): net +0.23 / +0.05; first 70% +0.62 / +0.61 (square-1 above D2/offline there), last 30% −0.62 / −1.27 (last 15% −1.09 / −3.58). Late-stream pool replay helps old regions a lot; newest views pay. Non-causal 70% threshold. → [card](campaigns/06_gain_attribution/track/README.md)
- 2026-10-09 best online + end sweep (selective births, clamp off, ERVS K16 85% + RR sweep 15%; 2 runs): aria1253 26.51 (+1.66 vs adopted online 24.85; = D2 26.52; offline 26.89); square-1 22.07 (+0.09 vs adopted 21.98; old D4 with clamp 22.21; offline 22.51). → [card](campaigns/06_gain_attribution/track/README.md)
- 2026-10-09 per-Gaussian Adam bias correction (RowAdam; aria1253, 2 runs after a hook-wiring fix): 0.5 births 23.65 (−1.54; the uncorrected large first steps of new Gaussians were repairing revisit damage), selective births 25.49 (−0.23). Old-KF peak unchanged (27.2) → Adam bias correction is not the cause of the online−D2 gap. → [card](campaigns/06_gain_attribution/track/README.md)
- 2026-10-09 low ERVS tau (aria1253, selective births, clamp off; 2 runs): tau 0.5 24.89, tau 0.1 22.83 (tau 4 25.72). Low tau shifts budget to late views (last fifth 22.53 → 24.54, above offline 23.98) but early fifths collapse (27.69 → 22.16) despite 19 updates per early KF: early views need continued replay. Net loss. → [card](campaigns/06_gain_attribution/track/README.md)
- 2026-10-09 lagged window (lag 6, on selective births, clamp off; aria1253 + square-1, 3 runs): overall −0.17 / −0.39, last fifth −0.66 / −2.02 (newest KFs lose window training), first 80% neutral (26.48 vs 26.53; 22.18 vs 22.15). Does not recover the online−D2 residual. square-1 selective = online (21.72 vs 21.75). → [card](campaigns/06_gain_attribution/track/README.md)
- 2026-10-09 online−D2 residual candidates (no GPU): ordinary (non-revisit) births cost only −0.48 dB per old KF over the whole stream after the revisit fix → too small. Earliest-born Gaussians online are ~13% larger / more opaque / 8% more numerous than in D2 (weak sign of training on an incomplete map). Residual attributed by elimination to updates acting on a partial map; not directly shown. → [card](campaigns/06_gain_attribution/track/README.md)
- 2026-10-09 online−D2 residual (no GPU): after the revisit fix (selective 0.5/0.02), D2 is still ~+1 dB uniformly over the first 80% of the stream (held-out +0.86…+1.17; last fifth +0.08) — not a budget effect; cause open. Offline−D2 sits in the last 40% (allocation). → [card](campaigns/06_gain_attribution/track/README.md)
- 2026-10-09 selective births 0.5/0.02 + ERVS K16 (aria1253, 1 run): PSNR 25.72 = uniform (25.72); recent-KF gap to offline +1.46 vs +1.55; recent KFs get ~6 updates vs offline 12–13 under either sampler (late arrival, not sampler choice). → [card](campaigns/06_gain_attribution/track/README.md)
- 2026-10-09 event probe, selective births 0.5 (holes) / 0.02 (already-explained, 82%) (aria1253, 1 run): PSNR 25.72 (vs 0.5: 25.19, all-0.12: 25.63); revisit-birth damage −13.5 → −0.5, late old-KF decline −2.30 → −0.45; 77k covered births pruned (GS −22%). Remaining gap to offline: old KFs +1.43, recent KFs +1.55. → [card](campaigns/06_gain_attribution/track/README.md)
- 2026-10-09 event probe with opacity-0.12 births (aria1253, 1 run, 25.63): revisit-birth damage ~8× smaller; late old-KF decline −2.30 → −0.87. Remaining gap to offline: old KFs +1.74 (residual decline + lower peak), recent KFs +1.39 in both arms (late-view under-training, not births). → [card](campaigns/06_gain_attribution/track/README.md)
- 2026-10-09 event probe (aria1253, 1 run): 12 of 90 births carry −11.4 of −13.5 dB birth damage; each lowers the mean over all pool KFs by 0.3–1.95 dB. All are revisits (return to start, frames 1082–1123; backward retrace, 1184–1272). The tracking crash is the birth at 1108 (−1.95), not the pose correction (−0.01); corrections net −1.43. → [card](campaigns/06_gain_attribution/track/README.md)
- 2026-10-09 online vs offline tracking (aria1253, clamp off, 2 runs): online training-view PSNR reaches 26.93 by 1,500 renders (≈ offline final 26.98), then late events crash it (−1.55 dB in one interval spanning the pose/scale correction at frame 1118; −0.80 later, unattributed); online ends 25.22. Offline rises monotonically (peak−final 0.23 vs online 1.54). The online−offline gap on aria is mostly late map disruption, not inefficiency or forgetting. → [card](campaigns/06_gain_attribution/track/README.md)
- 2026-10-09 birth probe per-view net: probed old KFs change only −0.19 dB over ~9 births; KFs never covered +0.01 → no forgetting signal (earlier control −0.067/interval withdrawn). Online old views stay flat but end lower than D2: training efficiency, not loss. → [card](campaigns/06_gain_attribution/birth_probe/README.md)
- 2026-10-09 birth probe correction: by sums, training recovers ~90% of immediate birth damage (−93.7 vs +84.1); non-covered old views lose −0.05 to −0.07 dB per interval during training elsewhere. Earlier "damage outpaces recovery" (from medians) withdrawn. → [card](campaigns/06_gain_attribution/birth_probe/README.md)
- 2026-10-09 selective low-opacity births (aria1253, 1 run): 81% of new points are on already-explained pixels; immediate birth damage −0.21 → −0.04 dB (5× less) but PSNR 25.14 (+0.48, same as uniform lowop). Immediate covering is a minor part of the stream-time gap; the rest builds up later. → [card](campaigns/06_gain_attribution/selop/README.md)
- 2026-10-09 clamp-matched gap ladder (aria1253, square-1; 5 new runs): without the scale clamp, offline − online = +1.70 (aria) / +0.76 (square-1). aria: stream-time +1.33, order +0.04, allocation +0.33; square-1: stream-time +0.10, order −0.11, allocation +0.77. → [card](campaigns/06_gain_attribution/noscale/README.md)
- 2026-10-09 consolidation seed-1 replicate (aria1253): 23.74 vs online s1 24.62 (−0.88; s0 −0.63). Loss replicates, concentrated in consolidated regions incl. training views → real effect; mechanism open (optimizer state candidate). → [card](campaigns/06_gain_attribution/consolidation/README.md)
- 2026-10-09 consolidation stale-pose check (no GPU): window pose updates that do not move Gaussians are tiny (median 0.7 mm, max 4.7 mm); 50/60 consolidations precede the 4 Gaussian-moving corrections → stale-pose cause refuted. Correction: aria1253 archive does have 4 pose_scale_correction events (D3 card said none). → [card](campaigns/06_gain_attribution/consolidation/README.md)
- 2026-10-09 consolidation overfitting check (no GPU): training views of the consolidated region drop as much as held-out (−1.01 vs −1.00) → not overfitting; the replay degrades the region fit itself. Candidates: stale-pose supervision of old regions (aria current-vs-final KF pose change 3.6 cm), optimizer state. → [card](campaigns/06_gain_attribution/consolidation/README.md)
- 2026-10-09 consolidation per-view analysis (no GPU): settle loss is localized to consolidated regions (−1.00 dB vs ±0.38 seed spread; other views −0.08); recent views not starved (KF counts unchanged). Extra replay itself hurts the replayed region; mechanism open. → [card](campaigns/06_gain_attribution/consolidation/README.md)
- 2026-10-09 settle-triggered consolidation run (aria1253, 1 valid run after an audit-record fix): 158 consolidation draws (7%), 49 KFs never settle; PSNR 24.03 vs online 24.66 (seed spread 24.62–24.80) → −0.63 dB. Not pursued. → [card](campaigns/06_gain_attribution/consolidation/README.md)
- 2026-10-09 settle-triggered consolidation pre-analysis (no GPU, 4 scenes): table_06 never settles (179/179 KFs touched to the end); elsewhere 40–80% of touched KFs settle only after the stream. Settle trigger not run; debt-driven replay proposed. → [card](campaigns/06_gain_attribution/consolidation/README.md)
- 2026-10-09 lowop follow-up: aria1253 opacity-0.12 births + no scale clamp 25.64 (+0.98 vs online; effects add up, D2 26.65); square-1 lowop 21.72 (−0.01, no effect). → [card](campaigns/06_gain_attribution/lowop/README.md)
- 2026-10-09 birth probe (aria1253, 1 run, measurement only): right after a birth, old KFs seeing the new points drop −0.21 dB on average (83% negative, n=444); KFs not seeing them 0.000 (n=345). Direct evidence that births damage trained views. → [card](campaigns/06_gain_attribution/birth_probe/README.md)
- 2026-10-09 low-opacity births (aria1253, 1 run): new Gaussians start at opacity 0.12 instead of 0.5 → 25.13 vs online 24.66 (+0.47); D2 26.65. → [card](campaigns/06_gain_attribution/lowop/README.md)
- 2026-10-09 no-scale follow-up: square-1 clamp off +0.03 (no effect); aria1253 D2 without clamp 26.52 vs online without clamp 25.19 → stream-time effect +1.33 dB remains once the clamp is removed on both sides (was +1.99). → [card](campaigns/06_gain_attribution/noscale/README.md)
- 2026-10-09 no-scale-projection diagnostic (aria1253, 1 run): online without the per-packet 0.1 scale clamp +0.53 dB (25.19 vs 24.66); D2 +1.99. The clamp (never applied to trained Gaussians in D2/offline) explains ~1/4 of the stream-time gain on this scene. → [card](campaigns/06_gain_attribution/noscale/README.md)
- 2026-10-09 D3 oracle-pose diagnostic (2 runs): online training with end-of-stream poses gives square-1 −0.01, aria1253 −1.06 dB vs online (D2 +0.27/+1.99); no pose_updates in the archives, Gaussians stay at birth poses. Poses do not explain the D2 gain. → [card](campaigns/06_gain_attribution/pose_oracle/README.md)
- 2026-10-09 settle-aware pools (18 runs) and birth-triggered repair replay (2 runs) on ERVS K16: all below online ERVS (settle −0.14…−0.26, repair −0.67/−1.27). D2 prunes more yet is better, so capacity/pruning is not its advantage; oracle-pose test (D3) remains. → [card](campaigns/06_gain_attribution/settle_pool/README.md), [card](campaigns/06_gain_attribution/birth_repair/README.md)
- 2026-10-08 online→offline gap ladder (6 scenes, seed 0, 18 runs): of offline − online uniform (1.53 dB), training during the stream explains +0.99 (65%), equal count allocation +0.62 (40%), order ≈0; a final 15% RR consolidation after ERVS recovers +0.68 dB (6/6, half of the gap). Pose drift small (<0.5% extent). → [card](campaigns/06_gain_attribution/gap_ladder/README.md)
- 2026-10-06 CaRtGS adaptive optimization as a drop-in sampler (released-code scheduler, UTMM 8 scenes, seed 0): PSNR vs uniform_iid +0.160 (7/8), vs ERVS +0.023 (5/8), vs uniform_k16 −0.094; balances counts most (dense CV 0.64) and, like ERVS, loses the earliest views. Borrow share 13–27%. → [card](campaigns/06_gain_attribution/cartgs_ao/README.md)
- 2026-10-06 offline reference on M2DGR (2) + Oxford new-college-01 (seed 0, 5070 Ti): ERVS − uniform_iid +0.04…+0.09; gap more constant on both M2DGR scenes. Oxford new-college-02 offline gate FAIL (pool cap 700 also cuts the offline pool; oldest dense views untrained); nc04/cc05 not run. → [card](campaigns/06_gain_attribution/offline_reference/README.md)
- 2026-10-06 ERVS τ 8/16 (124 runs): larger τ moves ERVS toward uniform_k16; 19 scenes × 3 seeds PSNR vs uniform_iid τ4 +0.063 / τ8 +0.076 / τ16 +0.077 (k16 +0.091); none beats k16; slope correction in the rule group clear only at τ4 (5/6). τ=4 kept. → [card](campaigns/06_gain_attribution/ervs_tau_scale/README.md)
- 2026-10-06 offline reference + online arms on FAST-LIVO2 (5 scenes, seed 0, RTX 5070 Ti, 20 runs, all gates PASS): offline 1.6–2.9 dB above online; ERVS − uniform_iid −0.03 dB (2/5), gap not more constant (1/5), front-loading lower in 5/5. → [card](campaigns/06_gain_attribution/offline_reference/README.md)
- 2026-10-04 rule A (ERVS K16 + one stale-first dense slot, 8 scenes, seed 0): rejected — mean PSNR −0.10 vs ERVS (2/8), early-15% gap only +0.01, mid gain over uniform drops from +0.16 to +0.04. → [card](campaigns/06_gain_attribution/stale_slot/README.md)
- 2026-10-04 offline reference extended to 19 scenes (15 more runs, all PASS): online is −0.07…−4.17 dB below offline (mean uniform −1.06, ERVS −1.02); ERVS does not make the gap more constant over time (centred MAD 0.560 vs 0.511, lower in 7/19); ERVS lowers training front-loading vs uniform_k16 in 17/19 (−0.020) but only slightly. Output-path incident fixed. → [card](campaigns/06_gain_attribution/offline_reference/README.md)
- 2026-10-03 offline (deferred-training) reference, 4 B scenes × 3 seeds (12 runs, all gates PASS): online is 0.4–2.4 dB below offline everywhere (uniform −1.48, ERVS −1.41); gap is a level offset with a mid-stream trough that ERVS reduces, not the predicted early+/late− tilt; pre-declared |slope| test fails (0.29 vs 0.27), late-bin test passes. Pose/timing confound open. → [card](campaigns/06_gain_attribution/offline_reference/README.md)
- 2026-10-03 training-signal stage 6 (ERVS count weight × (1 + c·loss), c 0.5/1.0, 8 runs, seed0): count tail protected as in ERVS but mean −0.11/+0.00 vs uniform_k16 (ERVS +0.10) and no flatter; study closed, ERVS τ=4 kept (user decision). → [card](campaigns/06_gain_attribution/ervs_train_signal/README.md)
- 2026-10-03 training-signal stage 5 (uniform floor + quality target, 16 runs, seed0): no arm keeps mean ≥ uniform_k16 while flattening; regional forgetting λ0.5 is flattest (sd −0.18) but −0.39 dB; loss floor −0.08/−0.10. A per-draw floor does not protect the low-count tail (dense p10 count 1.0 vs 2.0 under ERVS). → [card](campaigns/06_gain_attribution/ervs_train_signal/README.md)
- 2026-10-03 training-signal replay study complete (stages 1–4, 64 runs): no signal sampler (forgetting/progress/loss/PER/catch-up/age-norm/interference/staleness) beats uniform over 3 seeds; interference's seed-0 4/4 gain was noise (3-seed −0.02); ERVS τ4 +0.07 (3/4). Seed noise up to 0.2 dB mean PSNR, 0.3 dB min-bin. ERVS aria seed-2 early-region collapse recurs. → [card](campaigns/06_gain_attribution/ervs_train_signal/README.md)

- 2026-10-03 training-signal replay study stages 1–2 (4 B scenes, budget 25, seed0): forgetting is real (revisit after >200 steps −0.2…−0.5 dB) and comes from mid-distance training; last training PSNR tracks held-out (ρ 0.45 after difficulty) but replaying forgotten views does not lift held-out. Samplers vs uniform: ERVS τ4 +0.22 (4/4), age_norm +0.05, forget/loss+staleness −0.03/−0.04 (worst-Q1 +0.16/+0.17), progress −0.24, catch-up −0.26. → [card](campaigns/06_gain_attribution/ervs_train_signal/README.md)

- 2026-10-03 ERVS balancing strength on 4 B scenes (budget 25, seed0): τ=4/1/0.25 dense CV 0.76/0.58/0.35 (uniform 0.92) but ΔPSNR vs uniform +0.21/−0.02/−0.74 and Δmin-bin +0.01/−0.44/−1.47 — stronger balancing starves early views and is monotonically worse. → [card](campaigns/06_gain_attribution/ervs_tau_strength/README.md)

- 2026-10-03 ERVS K16 vs uniform with replacement, 3 seeds × 4 B scenes × budget 15/25: mean ΔPSNR +0.085±0.058 (6/8 cells), min-bin −0.06 and worst-Q1 +0.01 (3/8 each); temporal paired Δ by fifth −0.22/+0.07/+0.34/+0.23/0.00 — ERVS loses on the earliest stream and gains mid-stream. → [card](campaigns/06_gain_attribution/ervs_vs_iid_seeds/README.md)

- 2026-10-02 ERVS K16 vs uniform K16 vs uniform with replacement on held-out aria1253/table_06 (budget 15/25, seed0): ERVS count weighting lowers min-bin PSNR (−0.04…−0.44) and worst-Q1 (−0.10…−0.45) vs uniform K16 in 4/4 cells, mean PSNR 3/4 lower; K-group without replacement helps vs with replacement (min-bin 4/4 ≥0, PSNR +0.64/+0.23 in 2 cells). Balancing claim not supported at τ=4 per_view. → [card](campaigns/06_gain_attribution/ervs_vs_uniform_k16/README.md)

- 2026-10-02 ERVS group size K on B (persistent per-pool group queue, rot·square-1, budget 15/25, seed0): selected K=16 (4-cell mean 22.731 vs current per-batch 22.620; K32 22.600, K64 22.625); K16 higher in 3/4 cells (square-1 +0.17/+0.18). Min-bin PSNR / worst-Q1 slightly lower than current (−0.08/−0.07). → [card](campaigns/06_gain_attribution/ervs_group_k/README.md)

- 2026-10-02 ERVS/ERCB vs RR temporal+tail analysis (post-hoc, no training): on B, ERVS raises worst-Q1 in 4/4 scenes at budgets 5/10/15 (+0.71/+0.22/+0.24dB) and lowers per-view std 4/4 at 5/10, mean comparable; no general late-sequence decline. 3dgs-custom ERCB budget-15 gain is early-sequence (+1.97, 18/19) and worse late (−1.01). RR-hard-Q1 is selection-biased. → [card](campaigns/06_gain_attribution/ervs_temporal_analysis/README.md)

- 2026-10-02 live B operating point on RTX 5070 Ti (actual tracking+mapping, TensorRT, 1/1.2/1.5x, ERVS): every admitted KF gets the full 40 renders; the constraint is KF admission (admitted/tracking KFs 1x: aria 70%, rot 54%, rpng 42%, utmm 74%) from tracking lag (rpng +62s, rot +33s at 1x). Renders per tracking KF 1x ≈17–30. PSNR 1x/1.5x: aria 23.29/23.00, rot 22.19/24.48, rpng 23.82/24.03, utmm 20.87/20.84. TRT vs PyTorch tracking at 1x: +0.2…+2.9dB. → [card](campaigns/06_gain_attribution/live_operating_point_5070ti/README.md)

- 2026-10-02 ERVS vs RR on B at 5/10 renders/KF (4 scenes, seed0): budget 5 is the first positive signal (+0.30/+0.09/+0.64/+0.07dB, 4/4) but the mechanism is reversed there (ERVS KF-pool CV higher than RR); budget 10 no signal (+0.00/−0.26/+0.41/−0.08). Budget curves non-monotonic; budget 5 far below live operating point. Candidate only, needs multi-seed. → [card](campaigns/06_gain_attribution/ervs_low_budget/README.md)

- 2026-10-02 depth-off sampler diagnostic (KF depth weight 0, per-pool 2x2, 4 scenes, budget 15/25, seed0): H rejected — joint ERVS−RR b15 +0.05/+0.53/+0.56/−0.28, b25 −0.11/+0.22/−0.95/−0.16dB; removing depth amplifies scene-dependent swings (aria +0.14→+0.56 at 15, −0.41→−0.95 at 25). Exploratory: KF depth term lowers PSNR on RPNG/UTMM, raises on Aria. Diagnostic only. → [card](campaigns/06_gain_attribution/ervs_depth_off/README.md)

- 2026-10-02 ERVS per-pool 2x2 (keyframe pool × dense pool, 4 scenes, budget 15/25, seed0): no consistent pool effect (KF b15 +0.11/+0.19/−0.36/−0.20, dense b15 +0.02/+0.26/+0.50/−0.01dB; b25 mixed), cancellation only in aria15, interactions up to ±0.4dB; 4-scene means of all four arms within 0.25dB. Across all ERVS tests the sampler is second-order on B. → [card](campaigns/06_gain_attribution/ervs_per_pool/README.md)

- 2026-10-01 ERVS window-replacement test (window off = quota 0:6:6, 4 scenes, budget 15/25, seed0): replacement claim not supported — RR degrades without window only on square-1 (R1 2/8), ERVS never resolved-worse (R2 8/8), ERVS gain larger without window 4/8; first-service latency not shorter under ERVS. Exploratory: removing the window raises 4-scene mean ~+0.1dB (aria +0.4~0.9), recent-third favours ERVS 7/8 without window. Single seed. → [card](campaigns/06_gain_attribution/ervs_window_replacement/README.md)

- 2026-10-01 ERVS vs RR on B (4 scenes, budget 15/25, seed0, 16 cells): mechanism moved in 8/8 (KF-pool CV down), but quality inconsistent — ERVS−RR b15 rot +0.13/rpng +0.45/aria +0.14/utmm −0.21, b25 −0.06/+0.27/−0.41/−0.05dB. C2 rule (≥3/4) not met (b15 2/4, b25 1/4); only RPNG table_06 shows a consistent ERVS gain. Not a final claim. → [card](campaigns/06_gain_attribution/b_ablation_v2/README.md)

- 2026-10-01 B ablation chain pilot 24/24 (rot·RPNG table_06, budget 15/40, seed0, B main 6d200f0f): R1 window→R2 +KF pool +2.5~3.7dB, R2→R3 dense RGB +0.19~0.39dB (4/4 signal), R3→R4 pacing −0.00~+0.19dB (1/4, no signal), ERVS−RR +0.13/−0.28/+0.45/+0.22dB inconsistent; κ4 amplification not observed. ERVS lowers only KF-pool service CV (6/6), recent-third PSNR ERVS ahead 5/6 (hint). Single-seed pilot, not a final claim. → [card](campaigns/06_gain_attribution/b_ablation_chain/README.md)

- 2026-10-01 사용자 확정 B(KF metric RGBD + dense RGB)를 VIGS-SLAM-custom main에 merge/commit: 6d200f0f. 40/KF, normal OFF, dense depth OFF, warp backward ON. 공식 run.py 네 장면 재검증 PSNR 25.7747/25.0222/21.8619/24.9850dB, 기존 B seed0와 최대차 0.0144dB; trace/pose/cohort/budget 동일, CPU22 tests 통과. GitHub main push 완료. → [card](campaigns/06_gain_attribution/b_condition_main_adoption/README.md)

- 2026-10-01 fixed40 dense-depth 4scene×3arm×2seed 24/24 완료: held-out PSNR은 dense RGB(B)가 4/4 최고. dense depth(C)는 B 대비 −0.066/−0.092/−0.216/−0.100dB; Aria MPS front mass −2.69/−1.60%p, behind +0.86/+0.88%p, 수동 floater영역 count −11.8%. normal/hard-proxy OFF, depth L1 λ0.25, causal frozen replay/zero-tail. 독립 GT 없는 RPNG·UTMM은 BA 보조지표로 한정. PLY24개와 원자료는 results/campaigns/gain_attribution/dense_depth_four_scene/v1, main 미변경. → [card](campaigns/06_gain_attribution/dense_depth_four_scene/README.md)

- 2026-10-01 dense-depth four-scene fixed40 비교 진행: branch 37fb9152, KF RGBD / +dense RGB / +dense RGBD, seeds0·1. held-out/geometry/PLY는 campaign 경로로 기록하며 main은 미변경. → [card](campaigns/06_gain_attribution/dense_depth_four_scene/README.md)

- 2026-10-01 aria1253rot controls7/7 완료, 기존19+로컬28=47/140. NTFS metadata 대기로 controls_v4 평가 정지; 필수 입력17장면 모두 준비 확인. 검증된28개 manifest/source lock 재사용하는 controls_v5/followup_v6 시작, rpng table_03 학습 진행. → [card](campaigns/06_gain_attribution/handoff_5070ti/local_resume/README.md)

- 2026-10-01 CVPR aria/aria1253rot 40renders/KF native_geometry: status=passed, PSNR=24.991874407158523; /home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/rtx5070ti_controls_v4/render40/aria/aria1253rot/native_geometry → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR aria/aria1253rot 40renders/KF rr_kf_rgb: status=passed, PSNR=24.99573585635326; /home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/rtx5070ti_controls_v4/render40/aria/aria1253rot/rr_kf_rgb → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR aria/aria1253rot 40renders/KF ervs_kf_rgb: status=passed, PSNR=24.69144163913414; /home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/rtx5070ti_controls_v4/render40/aria/aria1253rot/ervs_kf_rgb → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR aria/aria1253rot 40renders/KF rr_dense: status=passed, PSNR=25.235142848530753; /home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/rtx5070ti_controls_v4/render40/aria/aria1253rot/rr_dense → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR aria/aria1253rot 15renders/KF rr_kf_rgb: status=passed, PSNR=23.62655188763728; /home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/rtx5070ti_controls_v4/render15/aria/aria1253rot/rr_kf_rgb → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR aria/aria1253rot 15renders/KF ervs_kf_rgb: status=passed, PSNR=23.61231665689437; /home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/rtx5070ti_controls_v4/render15/aria/aria1253rot/ervs_kf_rgb → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR aria/aria1253rot 15renders/KF rr_dense: status=passed, PSNR=23.721168493051998; /home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/rtx5070ti_controls_v4/render15/aria/aria1253rot/rr_dense → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 pilot-scene controls21/21 검증(기존19 포함40/140). Aria40 RR+dense 평가 signal11 이후 동일지도 재평가2회 일치25.883835dB. 실패로그 보존 중 NTFS rename 대기 미해결·GPU점유0; 새 controls_v4/followup_v5로 결과 재사용 후 aria1253rot 시작. → [card](campaigns/06_gain_attribution/handoff_5070ti/local_resume/README.md)

- 2026-10-01 CVPR aria/aria1253 40renders/KF native_geometry: status=passed, PSNR=25.82559433420196; /home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/rtx5070ti_controls_v3/render40/aria/aria1253/native_geometry → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR aria/aria1253 40renders/KF rr_kf_rgb: status=passed, PSNR=25.33093212215045; /home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/rtx5070ti_controls_v3/render40/aria/aria1253/rr_kf_rgb → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR aria/aria1253 40renders/KF ervs_kf_rgb: status=passed, PSNR=25.046267920777996; /home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/rtx5070ti_controls_v3/render40/aria/aria1253/ervs_kf_rgb → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR aria/aria1253 40renders/KF rr_dense: status=failed, PSNR=None; /home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/rtx5070ti_controls_v3/render40/aria/aria1253/rr_dense → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR aria/aria1253 15renders/KF rr_kf_rgb: status=passed, PSNR=22.838645927778636; /home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/rtx5070ti_controls_v3/render15/aria/aria1253/rr_kf_rgb → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR aria/aria1253 15renders/KF ervs_kf_rgb: status=passed, PSNR=23.1710033926345; /home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/rtx5070ti_controls_v3/render15/aria/aria1253/ervs_kf_rgb → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR aria/aria1253 15renders/KF rr_dense: status=passed, PSNR=23.14226299751806; /home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/rtx5070ti_controls_v3/render15/aria/aria1253/rr_dense → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR utmm/square-1 40renders/KF native_geometry: status=passed, PSNR=22.16141046712428; /home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/rtx5070ti_controls_v3/render40/utmm/square-1/native_geometry → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR utmm/square-1 40renders/KF rr_kf_rgb: status=passed, PSNR=21.74469624625312; /home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/rtx5070ti_controls_v3/render40/utmm/square-1/rr_kf_rgb → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR utmm/square-1 40renders/KF ervs_kf_rgb: status=passed, PSNR=21.814367011741357; /home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/rtx5070ti_controls_v3/render40/utmm/square-1/ervs_kf_rgb → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR utmm/square-1 40renders/KF rr_dense: status=passed, PSNR=22.114579368520666; /home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/rtx5070ti_controls_v3/render40/utmm/square-1/rr_dense → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR utmm/square-1 15renders/KF rr_kf_rgb: status=passed, PSNR=20.736772810971296; /home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/rtx5070ti_controls_v3/render15/utmm/square-1/rr_kf_rgb → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR utmm/square-1 15renders/KF ervs_kf_rgb: status=passed, PSNR=20.716585324134357; /home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/rtx5070ti_controls_v3/render15/utmm/square-1/ervs_kf_rgb → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR utmm/square-1 15renders/KF rr_dense: status=passed, PSNR=21.27508465743359; /home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/rtx5070ti_controls_v3/render15/utmm/square-1/rr_dense → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR rpng/table_06 40renders/KF native_geometry: status=passed, PSNR=25.16449649226558; /home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/rtx5070ti_controls_v3/render40/rpng/table_06/native_geometry → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR rpng/table_06 40renders/KF rr_kf_rgb: status=passed, PSNR=24.947570405564868; /home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/rtx5070ti_controls_v3/render40/rpng/table_06/rr_kf_rgb → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR rpng/table_06 40renders/KF ervs_kf_rgb: status=passed, PSNR=25.10544005729057; /home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/rtx5070ti_controls_v3/render40/rpng/table_06/ervs_kf_rgb → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR rpng/table_06 40renders/KF rr_dense: status=passed, PSNR=24.936770825772673; /home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/rtx5070ti_controls_v3/render40/rpng/table_06/rr_dense → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR rpng/table_06 15renders/KF rr_kf_rgb: status=passed, PSNR=23.802125068183418; /home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/rtx5070ti_controls_v3/render15/rpng/table_06/rr_kf_rgb → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR rpng/table_06 15renders/KF ervs_kf_rgb: status=passed, PSNR=23.793912650443414; /home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/rtx5070ti_controls_v3/render15/rpng/table_06/ervs_kf_rgb → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR rpng/table_06 15renders/KF rr_dense: status=passed, PSNR=23.392751422229114; /home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/rtx5070ti_controls_v3/render15/rpng/table_06/rr_dense → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 UTMM vanilla15 checkpoint evaluator signal11 비정상 종료 기록·부분출력 보존. 동일 설정 재평가7/7·정합7/7 통과, 재학습0. 완료12-run pilot 재개 지원; controls_v3/followup_v4로 이어감. → [card](campaigns/06_gain_attribution/handoff_5070ti/local_resume/README.md)

- 2026-10-01 CVPR utmm/square-1 40renders/KF vanilla: status=passed, PSNR=18.871978459534823; /home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/rtx5070ti_fixed_pilot_v1/render40/utmm/square-1/vanilla → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR utmm/square-1 40renders/KF d3: status=passed, PSNR=22.092828626985902; /home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/rtx5070ti_fixed_pilot_v1/render40/utmm/square-1/d3 → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR utmm/square-1 15renders/KF vanilla: status=passed, PSNR=15.88441706881111; /home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/rtx5070ti_fixed_pilot_v1/render15/utmm/square-1/vanilla → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR utmm/square-1 15renders/KF d3: status=passed, PSNR=20.9630809713293; /home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/rtx5070ti_fixed_pilot_v1/render15/utmm/square-1/d3 → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR rpng/table_06 40renders/KF vanilla: status=passed, PSNR=22.59568762908111; /home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/rtx5070ti_fixed_pilot_v1/render40/rpng/table_06/vanilla → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR rpng/table_06 40renders/KF d3: status=passed, PSNR=25.12768618265788; /home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/rtx5070ti_fixed_pilot_v1/render40/rpng/table_06/d3 → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 RPNG15 양 arm 통과: D3/vanilla held-out23.861218/20.943542 dB. Training renders3405 동일, Adam updates3405/445·D3 proxy1901로 optimizer/총연산 동일 비교는 아님. 누락되던 vanilla completion-list update count 집계 보완; 학습 코드 변경 없음. → [card](campaigns/06_gain_attribution/handoff_5070ti/local_resume/README.md)

- 2026-10-01 CVPR rpng/table_06 15renders/KF vanilla: status=passed, PSNR=20.943542109309018; /home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/rtx5070ti_fixed_pilot_v1/render15/rpng/table_06/vanilla → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR rpng/table_06 15renders/KF d3: status=passed, PSNR=23.861218289212065; /home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/rtx5070ti_fixed_pilot_v1/render15/rpng/table_06/d3 → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 local queue 입력준비 순 실행으로 보완: controls121·전체cohort·recipe 유지, 장면별 full input audit 후 시작, 대기 중 완료지도 checkpoint 평가. RPNG v2 bundled/Aria v3 split geometry 두 archive 형식 검증 지원. 대기 coordinator만 controls_v2/followup_v3로 대체; 기존 결과 보존. → [card](campaigns/06_gain_attribution/handoff_5070ti/local_resume/README.md)

- 2026-10-01 archived controls19/19의 checkpoint 133/133 평가 완료, 정합통과 133/133. Colin 학습 지도만 local5070에서 평가(재학습0); pilot coordinator 자동재개 확인. → [card](campaigns/06_gain_attribution/handoff_5070ti/local_resume/README.md)

- 2026-10-01 CVPR archived19/controls_checkpoint_evaluation_5070ti checkpoint_curverenders/KF saved_maps_no_retraining: status=passed, PSNR=None; /home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/rtx5070ti_archived_curves_v1 → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR aria/aria1253 regionrenders/KF Vanilla_40: status=evaluated, PSNR=20.856434509044384; results/campaigns/gain_attribution/cvpr_assets/rtx5070ti_fixed_pilot_v1/aria_manual_regions.json → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR aria/aria1253 regionrenders/KF D3_40: status=evaluated, PSNR=25.760522092571694; results/campaigns/gain_attribution/cvpr_assets/rtx5070ti_fixed_pilot_v1/aria_manual_regions.json → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR aria/aria1253 regionrenders/KF Vanilla_15: status=evaluated, PSNR=18.954430743938183; results/campaigns/gain_attribution/cvpr_assets/rtx5070ti_fixed_pilot_v1/aria_manual_regions.json → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR aria/aria1253 regionrenders/KF D3_15: status=evaluated, PSNR=23.46318665715574; results/campaigns/gain_attribution/cvpr_assets/rtx5070ti_fixed_pilot_v1/aria_manual_regions.json → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 handoff 집계 보완: 기존controls19도 raw map/snapshot 회수 후 checkpoint 평가에 포함(재학습 없음). 실제6-control로 집계 검증, 불완전 cohort 최종집계 차단 확인. 후속v1은 GPU 실행 전 보존·대체하고 archived19를 포함한 v2 준비. → [card](campaigns/06_gain_attribution/handoff_5070ti/local_resume/README.md)

- 2026-10-01 local pilot checkpoint28/28 평가·pose alignment 통과. Original sampler 소스는 별도 worktree에서 과거152-run train/scheduler SHA와 정확히 복원; init cloud114/114 일치, metadata/schedule171 hash 고정. controls 이후 D3 zero-weight20 및 original sampler114 후속 준비(아직 미실행). → [card](campaigns/06_gain_attribution/handoff_5070ti/local_resume/README.md)

- 2026-10-01 local RTX5070Ti 재개: source119·extension hash 일치, RPNG/UTMM16-scene RGB checksum 일치; Aria 15/40 D3+vanilla pilot4/4 held-out 이중 평가 통과. 나머지 pilot·미완료controls121·checkpoint 평가 준비, 실시간 비교 보류. → [card](campaigns/06_gain_attribution/handoff_5070ti/local_resume/README.md)

- 2026-10-01 CVPR aria/aria1253 40renders/KF vanilla: status=passed, PSNR=20.856434509044384; /home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/rtx5070ti_fixed_pilot_v1/render40/aria/aria1253/vanilla → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR aria/aria1253 40renders/KF d3: status=passed, PSNR=25.760522092571694; /home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/rtx5070ti_fixed_pilot_v1/render40/aria/aria1253/d3 → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR aria/aria1253 15renders/KF vanilla: status=passed, PSNR=18.954430743938183; /home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/rtx5070ti_fixed_pilot_v1/render15/aria/aria1253/vanilla → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR aria/aria1253 15renders/KF d3: status=passed, PSNR=23.46318665715574; /home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/rtx5070ti_fixed_pilot_v1/render15/aria/aria1253/d3 → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 RTX5070Ti 인계: 사용자 요청으로 local GPU queue/worker 중단, fixed80/80 및 controls19/140 보존. 코드·입력 inventory·실행 가이드 정리; 5070 설치/CUDA/실제 실행은 새 컴퓨터에서 검증. 시간 실험 보류. → [card](campaigns/06_gain_attribution/handoff_5070ti/README.md)

- 2026-10-01 CVPR rpng/table_03 40renders/KF ervs_kf_rgb: status=passed, PSNR=24.934068734227505; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/current_controls_v1/render40/rpng/table_03/ervs_kf_rgb → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR rpng/table_03 40renders/KF rr_dense: status=passed, PSNR=23.97124403655614; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/current_controls_v1/render40/rpng/table_03/rr_dense → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR rpng/table_03 15renders/KF rr_kf_rgb: status=passed, PSNR=23.366801742140133; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/current_controls_v1/render15/rpng/table_03/rr_kf_rgb → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR rpng/table_03 15renders/KF ervs_kf_rgb: status=passed, PSNR=23.316275889115055; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/current_controls_v1/render15/rpng/table_03/ervs_kf_rgb → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR 실제 자산 설치/19쪽 PDF 갱신: fixed80+curve80 완료, controls14/140와 live8/80 진행 중 → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR rpng/table_03 15renders/KF rr_dense: status=passed, PSNR=23.31877180445041; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/current_controls_v1/render15/rpng/table_03/rr_dense → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR rpng/table_02 40renders/KF native_geometry: status=passed, PSNR=24.242548713945364; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/current_controls_v1/render40/rpng/table_02/native_geometry → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR rpng/table_02 40renders/KF rr_kf_rgb: status=passed, PSNR=24.2738583022601; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/current_controls_v1/render40/rpng/table_02/rr_kf_rgb → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR rpng/table_02 40renders/KF ervs_kf_rgb: status=passed, PSNR=24.178258804425802; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/current_controls_v1/render40/rpng/table_02/ervs_kf_rgb → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR rpng/table_02 40renders/KF rr_dense: status=passed, PSNR=23.858373576647615; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/current_controls_v1/render40/rpng/table_02/rr_dense → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR rpng/table_02 15renders/KF rr_kf_rgb: status=passed, PSNR=21.479047011022697; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/current_controls_v1/render15/rpng/table_02/rr_kf_rgb → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR rpng/table_02 15renders/KF ervs_kf_rgb: status=passed, PSNR=21.47495967721286; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/current_controls_v1/render15/rpng/table_02/ervs_kf_rgb → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR rpng/table_02 15renders/KF rr_dense: status=passed, PSNR=21.27773225144164; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/current_controls_v1/render15/rpng/table_02/rr_dense → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR rpng/table_01 40renders/KF native_geometry: status=passed, PSNR=25.70282517391372; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/current_controls_v1/render40/rpng/table_01/native_geometry → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR rpng/table_01 40renders/KF rr_kf_rgb: status=passed, PSNR=25.85563205627806; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/current_controls_v1/render40/rpng/table_01/rr_kf_rgb → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR rpng/table_01 40renders/KF ervs_kf_rgb: status=passed, PSNR=25.85854049697815; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/current_controls_v1/render40/rpng/table_01/ervs_kf_rgb → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR rpng/table_01 40renders/KF rr_dense: status=passed, PSNR=25.660401146725356; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/current_controls_v1/render40/rpng/table_01/rr_dense → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR rpng/table_01 15renders/KF rr_kf_rgb: status=passed, PSNR=24.503652960180762; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/current_controls_v1/render15/rpng/table_01/rr_kf_rgb → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR rpng/table_01 15renders/KF ervs_kf_rgb: status=passed, PSNR=24.597321282344986; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/current_controls_v1/render15/rpng/table_01/ervs_kf_rgb → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR rpng/table_01 15renders/KF rr_dense: status=passed, PSNR=24.458256155371192; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/current_controls_v1/render15/rpng/table_01/rr_dense → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR cvpr/curve_aria_aria301_305_40_vanilla full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_aria_aria301_305_40_vanilla.log → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR cvpr/curve_aria_aria301_305_40_d3 full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_aria_aria301_305_40_d3.log → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR cvpr/curve_aria_aria301_305_15_vanilla full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_aria_aria301_305_15_vanilla.log → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR cvpr/curve_aria_aria301_305_15_d3 full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_aria_aria301_305_15_d3.log → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR cvpr/curve_aria_aria301_12F_40_vanilla full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_aria_aria301_12F_40_vanilla.log → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR cvpr/curve_aria_aria301_12F_40_d3 full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_aria_aria301_12F_40_d3.log → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR cvpr/curve_aria_aria301_12F_15_vanilla full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_aria_aria301_12F_15_vanilla.log → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR cvpr/curve_aria_aria301_12F_15_d3 full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_aria_aria301_12F_15_d3.log → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR cvpr/curve_aria_aria1253rot_40_vanilla full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_aria_aria1253rot_40_vanilla.log → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR cvpr/curve_aria_aria1253rot_40_d3 full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_aria_aria1253rot_40_d3.log → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR cvpr/first_supported_region_observations CPU_annotationrenders/KF shared_RGB_reference: status=measured, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/region_observations_v1/summary.json → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR cvpr/curve_aria_aria1253rot_15_vanilla full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_aria_aria1253rot_15_vanilla.log → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR cvpr/curve_aria_aria1253rot_15_d3 full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_aria_aria1253rot_15_d3.log → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR cvpr/curve_aria_aria1253_40_vanilla full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_aria_aria1253_40_vanilla.log → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR cvpr/curve_aria_aria1253_40_d3 full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_aria_aria1253_40_d3.log → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR cvpr/curve_aria_aria1253_15_vanilla full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_aria_aria1253_15_vanilla.log → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR cvpr/curve_aria_aria1253_15_d3 full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_aria_aria1253_15_d3.log → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR cvpr/curve_utmm_square-2_40_vanilla full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_utmm_square-2_40_vanilla.log → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR cvpr/curve_utmm_square-2_40_d3 full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_utmm_square-2_40_d3.log → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR cvpr/curve_utmm_square-2_15_vanilla full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_utmm_square-2_15_vanilla.log → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR cvpr/curve_utmm_square-2_15_d3 full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_utmm_square-2_15_d3.log → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR cvpr/curve_utmm_square-1_40_vanilla full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_utmm_square-1_40_vanilla.log → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR cvpr/curve_utmm_square-1_40_d3 full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_utmm_square-1_40_d3.log → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR cvpr/curve_utmm_square-1_15_vanilla full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_utmm_square-1_15_vanilla.log → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR cvpr/curve_utmm_square-1_15_d3 full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_utmm_square-1_15_d3.log → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR cvpr/curve_utmm_slow-straight-2_40_vanilla full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_utmm_slow-straight-2_40_vanilla.log → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR cvpr/curve_utmm_slow-straight-2_40_d3 full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_utmm_slow-straight-2_40_d3.log → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR cvpr/curve_utmm_slow-straight-2_15_vanilla full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_utmm_slow-straight-2_15_vanilla.log → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR cvpr/curve_utmm_slow-straight-2_15_d3 full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_utmm_slow-straight-2_15_d3.log → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR cvpr/curve_utmm_slow-straight-1_40_vanilla full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_utmm_slow-straight-1_40_vanilla.log → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR cvpr/curve_utmm_slow-straight-1_40_d3 full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_utmm_slow-straight-1_40_d3.log → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR cvpr/curve_utmm_slow-straight-1_15_vanilla full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_utmm_slow-straight-1_15_vanilla.log → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR cvpr/curve_utmm_slow-straight-1_15_d3 full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_utmm_slow-straight-1_15_d3.log → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR cvpr/curve_utmm_fast-straight_40_vanilla full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_utmm_fast-straight_40_vanilla.log → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR cvpr/curve_utmm_fast-straight_40_d3 full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_utmm_fast-straight_40_d3.log → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR cvpr/curve_utmm_fast-straight_15_vanilla full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_utmm_fast-straight_15_vanilla.log → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR cvpr/curve_utmm_fast-straight_15_d3 full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_utmm_fast-straight_15_d3.log → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR cvpr/curve_utmm_ego-drive_40_vanilla full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_utmm_ego-drive_40_vanilla.log → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR cvpr/curve_utmm_ego-drive_40_d3 full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_utmm_ego-drive_40_d3.log → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR cvpr/curve_utmm_ego-drive_15_vanilla full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_utmm_ego-drive_15_vanilla.log → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR cvpr/curve_utmm_ego-drive_15_d3 full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_utmm_ego-drive_15_d3.log → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR cvpr/curve_utmm_ego-centric-2_40_vanilla full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_utmm_ego-centric-2_40_vanilla.log → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR cvpr/curve_utmm_ego-centric-2_40_d3 full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_utmm_ego-centric-2_40_d3.log → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR cvpr/curve_utmm_ego-centric-2_15_vanilla full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_utmm_ego-centric-2_15_vanilla.log → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR cvpr/curve_utmm_ego-centric-2_15_d3 full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_utmm_ego-centric-2_15_d3.log → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR cvpr/curve_utmm_ego-centric-1_40_vanilla full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_utmm_ego-centric-1_40_vanilla.log → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR cvpr/curve_utmm_ego-centric-1_40_d3 full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_utmm_ego-centric-1_40_d3.log → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR cvpr/curve_utmm_ego-centric-1_15_vanilla full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_utmm_ego-centric-1_15_vanilla.log → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR cvpr/curve_utmm_ego-centric-1_15_d3 full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_utmm_ego-centric-1_15_d3.log → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR cvpr/curve_rpng_table_08_40_vanilla full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_rpng_table_08_40_vanilla.log → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR cvpr/curve_rpng_table_08_40_d3 full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_rpng_table_08_40_d3.log → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR cvpr/curve_rpng_table_08_15_vanilla full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_rpng_table_08_15_vanilla.log → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR cvpr/curve_rpng_table_08_15_d3 full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_rpng_table_08_15_d3.log → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR cvpr/curve_rpng_table_07_40_vanilla full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_rpng_table_07_40_vanilla.log → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR cvpr/curve_rpng_table_07_40_d3 full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_rpng_table_07_40_d3.log → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR cvpr/curve_rpng_table_07_15_vanilla full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_rpng_table_07_15_vanilla.log → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR cvpr/curve_rpng_table_07_15_d3 full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_rpng_table_07_15_d3.log → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR cvpr/curve_rpng_table_06_40_vanilla full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_rpng_table_06_40_vanilla.log → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR cvpr/curve_rpng_table_06_40_d3 full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_rpng_table_06_40_d3.log → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR cvpr/curve_rpng_table_06_15_vanilla full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_rpng_table_06_15_vanilla.log → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR cvpr/curve_rpng_table_06_15_d3 full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_rpng_table_06_15_d3.log → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR cvpr/curve_rpng_table_05_40_vanilla full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_rpng_table_05_40_vanilla.log → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR cvpr/curve_rpng_table_05_40_d3 full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_rpng_table_05_40_d3.log → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR cvpr/curve_rpng_table_05_15_vanilla full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_rpng_table_05_15_vanilla.log → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR cvpr/curve_rpng_table_05_15_d3 full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_rpng_table_05_15_d3.log → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR cvpr/curve_rpng_table_04_40_vanilla full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_rpng_table_04_40_vanilla.log → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR cvpr/curve_rpng_table_04_40_d3 full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_rpng_table_04_40_d3.log → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR cvpr/curve_rpng_table_04_15_vanilla full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_rpng_table_04_15_vanilla.log → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR cvpr/curve_rpng_table_04_15_d3 full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_rpng_table_04_15_d3.log → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR cvpr/curve_rpng_table_03_40_vanilla full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_rpng_table_03_40_vanilla.log → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR cvpr/curve_rpng_table_03_40_d3 full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_rpng_table_03_40_d3.log → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR cvpr/curve_rpng_table_03_15_vanilla full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_rpng_table_03_15_vanilla.log → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR cvpr/curve_rpng_table_03_15_d3 full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_rpng_table_03_15_d3.log → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR cvpr/curve_rpng_table_02_40_vanilla full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_rpng_table_02_40_vanilla.log → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR cvpr/curve_rpng_table_02_40_d3 full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_rpng_table_02_40_d3.log → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR cvpr/curve_rpng_table_02_15_vanilla full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_rpng_table_02_15_vanilla.log → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR cvpr/curve_rpng_table_02_15_d3 full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_rpng_table_02_15_d3.log → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR cvpr/curve_rpng_table_01_40_vanilla full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_rpng_table_01_40_vanilla.log → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR cvpr/curve_rpng_table_01_40_d3 full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_rpng_table_01_40_d3.log → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR cvpr/curve_rpng_table_01_15_vanilla full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_rpng_table_01_15_vanilla.log → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR cvpr/curve_rpng_table_01_15_d3 full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_rpng_table_01_15_d3.log → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR cvpr/shared_tracking_pilot measurement_stagerenders/KF pipeline: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/pipeline_v2/shared_tracking_pilot.log → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR aria/aria1253 40renders/KF live_vanilla_1.5x: status=passed, PSNR=20.92910993372211; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/live_shared_tracking_v1/scale1p5/aria/aria1253/vanilla → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR aria/aria1253 40renders/KF live_ours_1.5x: status=passed, PSNR=25.751155314554694; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/live_shared_tracking_v1/scale1p5/aria/aria1253/ours → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR aria/aria1253 40renders/KF live_vanilla_1x: status=passed, PSNR=20.122959835838724; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/live_shared_tracking_v1/scale1/aria/aria1253/vanilla → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR aria/aria1253 40renders/KF live_ours_1x: status=passed, PSNR=23.428837302986903; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/live_shared_tracking_v1/scale1/aria/aria1253/ours → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR rpng/table_01 40renders/KF live_vanilla_1.5x: status=passed, PSNR=22.95078182030484; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/live_shared_tracking_v1/scale1p5/rpng/table_01/vanilla → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR rpng/table_01 40renders/KF live_ours_1.5x: status=passed, PSNR=25.358613965995758; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/live_shared_tracking_v1/scale1p5/rpng/table_01/ours → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR rpng/table_01 40renders/KF live_vanilla_1x: status=passed, PSNR=22.444745099876982; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/live_shared_tracking_v1/scale1/rpng/table_01/vanilla → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR rpng/table_01 40renders/KF live_ours_1x: status=passed, PSNR=23.667279053494276; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/live_shared_tracking_v1/scale1/rpng/table_01/ours → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR cvpr/pilot_checkpoint_vanilla measurement_stagerenders/KF pipeline: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/pipeline_v2/pilot_checkpoint_vanilla.log → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR cvpr/pilot_checkpoint_d3 measurement_stagerenders/KF pipeline: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/pipeline_v2/pilot_checkpoint_d3.log → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR cvpr/fixed_work_12f measurement_stagerenders/KF pipeline: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/pipeline_v2/fixed_work_12f.log → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR aria/aria301_12F 40renders/KF vanilla: status=passed, PSNR=24.271544135700573; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_12f_v1/render40/aria/aria301_12F/vanilla → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR aria/aria301_12F 40renders/KF d3: status=passed, PSNR=27.450468639893966; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_12f_v1/render40/aria/aria301_12F/d3 → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR aria/aria1253_region_checkpoints 40renders/KF d3_vs_vanilla: status=evaluated, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/collection_v1/aria_manual_region_curve40_v2.json → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR aria/aria1253_region_checkpoints 40renders/KF d3_vs_vanilla: status=evaluated, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/collection_v1/aria_manual_region_curve40_v1.json → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR aria/aria301_12F 15renders/KF vanilla: status=passed, PSNR=22.064716050841593; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_12f_v1/render15/aria/aria301_12F/vanilla → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR aria/aria301_12F 15renders/KF d3: status=passed, PSNR=25.69641070365906; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_12f_v1/render15/aria/aria301_12F/d3 → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR cvpr/capture_12f measurement_stagerenders/KF pipeline: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/pipeline_v2/capture_12f.log → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR aria/aria301_305 40renders/KF vanilla: status=passed, PSNR=20.71910099638194; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render40/aria/aria301_305/vanilla → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR aria/aria301_305 40renders/KF d3: status=passed, PSNR=24.840737277368888; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render40/aria/aria301_305/d3 → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR aria/aria301_305 15renders/KF vanilla: status=passed, PSNR=19.008593502646253; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render15/aria/aria301_305/vanilla → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR aria/aria301_305 15renders/KF d3: status=passed, PSNR=23.474117611688673; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render15/aria/aria301_305/d3 → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR aria/aria1253 regionrenders/KF vanilla: status=evaluated, PSNR=20.62817724606463; results/campaigns/gain_attribution/cvpr_assets/collection_v1/aria_manual_region40_v2.json → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR aria/aria1253 regionrenders/KF d3: status=evaluated, PSNR=25.747064095417052; results/campaigns/gain_attribution/cvpr_assets/collection_v1/aria_manual_region40_v2.json → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR aria/aria1253 regionrenders/KF vanilla: status=evaluated, PSNR=19.01287403907485; results/campaigns/gain_attribution/cvpr_assets/collection_v1/aria_manual_region15_v2.json → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR aria/aria1253 regionrenders/KF d3: status=evaluated, PSNR=23.479717014400105; results/campaigns/gain_attribution/cvpr_assets/collection_v1/aria_manual_region15_v2.json → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR aria/aria1253rot 40renders/KF vanilla: status=passed, PSNR=21.83502317960145; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render40/aria/aria1253rot/vanilla → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR aria/aria1253rot 40renders/KF d3: status=passed, PSNR=24.998510898527552; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render40/aria/aria1253rot/d3 → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR aria/aria1253rot 15renders/KF vanilla: status=passed, PSNR=20.373812591052445; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render15/aria/aria1253rot/vanilla → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR aria/aria1253rot 15renders/KF d3: status=passed, PSNR=23.803835471731716; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render15/aria/aria1253rot/d3 → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR aria/aria1253 40renders/KF vanilla: status=passed, PSNR=20.62817724606463; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render40/aria/aria1253/vanilla → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR snapshot CPU audit: 332 immutable states checked, 324 satisfy shared pose-alignment limits, 8 do not; held-out exclusion passed for all332. This is readiness for post-run evaluation, not map-quality validation. Result: results/campaigns/gain_attribution/cvpr_assets/checkpoint_alignment_v1.json. → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR aria/aria1253 40renders/KF d3: status=passed, PSNR=25.747064095417052; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render40/aria/aria1253/d3 → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR aria/aria1253 15renders/KF vanilla: status=passed, PSNR=19.01287403907485; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render15/aria/aria1253/vanilla → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR aria/aria1253 15renders/KF d3: status=passed, PSNR=23.479717014400105; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render15/aria/aria1253/d3 → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR utmm/square-2 40renders/KF vanilla: status=passed, PSNR=18.786255019051687; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render40/utmm/square-2/vanilla → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR utmm/square-2 40renders/KF d3: status=passed, PSNR=22.23544576216717; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render40/utmm/square-2/d3 → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR utmm/square-2 15renders/KF vanilla: status=passed, PSNR=16.45605817911576; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render15/utmm/square-2/vanilla → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR utmm/square-2 15renders/KF d3: status=passed, PSNR=21.19905044399962; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render15/utmm/square-2/d3 → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR utmm/square-1 40renders/KF vanilla: status=passed, PSNR=18.79899032027633; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render40/utmm/square-1/vanilla → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR utmm/square-1 40renders/KF d3: status=passed, PSNR=22.100768560244713; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render40/utmm/square-1/d3 → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR utmm/square-1 15renders/KF vanilla: status=passed, PSNR=15.860937889711357; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render15/utmm/square-1/vanilla → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR utmm/square-1 15renders/KF d3: status=passed, PSNR=20.965688475856073; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render15/utmm/square-1/d3 → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR utmm/slow-straight-2 40renders/KF vanilla: status=passed, PSNR=15.12111733964652; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render40/utmm/slow-straight-2/vanilla → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR utmm/slow-straight-2 40renders/KF d3: status=passed, PSNR=22.77454875126358; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render40/utmm/slow-straight-2/d3 → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR utmm/slow-straight-2 15renders/KF vanilla: status=passed, PSNR=16.816587519054572; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render15/utmm/slow-straight-2/vanilla → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR utmm/slow-straight-2 15renders/KF d3: status=passed, PSNR=20.954066347484748; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render15/utmm/slow-straight-2/d3 → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR utmm/slow-straight-1 40renders/KF vanilla: status=passed, PSNR=13.546598517894745; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render40/utmm/slow-straight-1/vanilla → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR utmm/slow-straight-1 40renders/KF d3: status=passed, PSNR=16.95625534057617; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render40/utmm/slow-straight-1/d3 → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR utmm/slow-straight-1 15renders/KF vanilla: status=passed, PSNR=12.621661043167114; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render15/utmm/slow-straight-1/vanilla → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR utmm/slow-straight-1 15renders/KF d3: status=passed, PSNR=15.127045559883118; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render15/utmm/slow-straight-1/d3 → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR utmm/fast-straight 40renders/KF vanilla: status=passed, PSNR=15.550470758886899; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render40/utmm/fast-straight/vanilla → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR utmm/fast-straight 40renders/KF d3: status=passed, PSNR=18.735907512552597; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render40/utmm/fast-straight/d3 → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR utmm/fast-straight 15renders/KF vanilla: status=passed, PSNR=14.058433939428891; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render15/utmm/fast-straight/vanilla → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR utmm/fast-straight 15renders/KF d3: status=passed, PSNR=17.02004697743584; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render15/utmm/fast-straight/d3 → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR utmm/ego-drive 40renders/KF vanilla: status=passed, PSNR=18.83111600434653; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render40/utmm/ego-drive/vanilla → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR asset update: RPNG8/8 ×15/40 ×D3/vanilla32 runs passed; T1/T2 audited CSV, T3 independent manual region4 records, F11/F12 actual live measurements installed. Source hashes unchanged. UTMM/Aria/full checkpoint assets remain in progress. → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR utmm/ego-drive 40renders/KF d3: status=passed, PSNR=21.516879920009192; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render40/utmm/ego-drive/d3 → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR utmm/ego-drive 15renders/KF vanilla: status=passed, PSNR=17.366720756177802; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render15/utmm/ego-drive/vanilla → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR utmm/ego-drive 15renders/KF d3: status=passed, PSNR=20.772115279771256; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render15/utmm/ego-drive/d3 → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR utmm/ego-centric-2 40renders/KF vanilla: status=passed, PSNR=18.08685510642684; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render40/utmm/ego-centric-2/vanilla → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR utmm/ego-centric-2 40renders/KF d3: status=passed, PSNR=19.55067374423089; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render40/utmm/ego-centric-2/d3 → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR utmm/ego-centric-2 15renders/KF vanilla: status=passed, PSNR=16.139085963311324; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render15/utmm/ego-centric-2/vanilla → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR utmm/ego-centric-2 15renders/KF d3: status=passed, PSNR=19.130685996278494; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render15/utmm/ego-centric-2/d3 → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR utmm/ego-centric-1 40renders/KF vanilla: status=passed, PSNR=16.759209010508155; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render40/utmm/ego-centric-1/vanilla → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR utmm/ego-centric-1 40renders/KF d3: status=passed, PSNR=20.153859510050193; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render40/utmm/ego-centric-1/d3 → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR utmm/ego-centric-1 15renders/KF vanilla: status=passed, PSNR=14.564862241992703; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render15/utmm/ego-centric-1/vanilla → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR utmm/ego-centric-1 15renders/KF d3: status=passed, PSNR=20.653921477206342; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render15/utmm/ego-centric-1/d3 → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR rpng/table_08 40renders/KF vanilla: status=passed, PSNR=21.88165073709297; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render40/rpng/table_08/vanilla → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR rpng/table_08 40renders/KF d3: status=passed, PSNR=24.87198794267203; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render40/rpng/table_08/d3 → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR rpng/table_08 15renders/KF vanilla: status=passed, PSNR=21.47925835868916; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render15/rpng/table_08/vanilla → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR rpng/table_08 15renders/KF d3: status=passed, PSNR=24.521692992660828; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render15/rpng/table_08/d3 → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR aria/aria1253 regionrenders/KF vanilla: status=evaluated, PSNR=19.023149574075948; results/campaigns/gain_attribution/cvpr_assets/collection_v1/aria_manual_region15_v1.json → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR aria/aria1253 regionrenders/KF d3: status=evaluated, PSNR=23.46339702606201; results/campaigns/gain_attribution/cvpr_assets/collection_v1/aria_manual_region15_v1.json → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR aria/aria1253 regionrenders/KF vanilla: status=evaluated, PSNR=20.872029646662355; results/campaigns/gain_attribution/cvpr_assets/collection_v1/aria_manual_region40_v1.json → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR aria/aria1253 regionrenders/KF d3: status=evaluated, PSNR=25.749060383279815; results/campaigns/gain_attribution/cvpr_assets/collection_v1/aria_manual_region40_v1.json → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR rpng/table_07 40renders/KF vanilla: status=passed, PSNR=24.011500866278727; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render40/rpng/table_07/vanilla → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR rpng/table_07 40renders/KF d3: status=passed, PSNR=27.549992338351764; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render40/rpng/table_07/d3 → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR rpng/table_07 15renders/KF vanilla: status=passed, PSNR=22.01145080335454; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render15/rpng/table_07/vanilla → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR rpng/table_07 15renders/KF d3: status=passed, PSNR=25.496817031334736; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render15/rpng/table_07/d3 → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR rpng/table_06 40renders/KF vanilla: status=passed, PSNR=22.56127199396357; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render40/rpng/table_06/vanilla → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR rpng/table_06 40renders/KF d3: status=passed, PSNR=25.12607385790026; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render40/rpng/table_06/d3 → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR rpng/table_06 15renders/KF vanilla: status=passed, PSNR=20.698803021886327; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render15/rpng/table_06/vanilla → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR rpng/table_06 15renders/KF d3: status=passed, PSNR=23.865029927846546; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render15/rpng/table_06/d3 → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR rpng/table_05 40renders/KF vanilla: status=passed, PSNR=20.942781929065575; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render40/rpng/table_05/vanilla → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR rpng/table_05 40renders/KF d3: status=passed, PSNR=23.31833450063894; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render40/rpng/table_05/d3 → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR rpng/table_05 15renders/KF vanilla: status=passed, PSNR=19.83612312180876; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render15/rpng/table_05/vanilla → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR rpng/table_05 15renders/KF d3: status=passed, PSNR=22.14680972091576; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render15/rpng/table_05/d3 → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR rpng/table_04 40renders/KF vanilla: status=passed, PSNR=20.809272621688528; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render40/rpng/table_04/vanilla → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR rpng/table_04 40renders/KF d3: status=passed, PSNR=23.145880527260864; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render40/rpng/table_04/d3 → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR rpng/table_04 15renders/KF vanilla: status=passed, PSNR=20.002419714280116; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render15/rpng/table_04/vanilla → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR rpng/table_04 15renders/KF d3: status=passed, PSNR=21.60679450329439; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render15/rpng/table_04/d3 → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR rpng/table_03 40renders/KF vanilla: status=passed, PSNR=20.682447953162963; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render40/rpng/table_03/vanilla → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR rpng/table_03 40renders/KF d3: status=passed, PSNR=24.990276752967127; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render40/rpng/table_03/d3 → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR rpng/table_03 15renders/KF vanilla: status=passed, PSNR=20.04718496183866; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render15/rpng/table_03/vanilla → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR rpng/table_03 15renders/KF d3: status=passed, PSNR=23.397692402827417; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render15/rpng/table_03/d3 → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR rpng/table_02 40renders/KF vanilla: status=passed, PSNR=20.073584814594216; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render40/rpng/table_02/vanilla → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR rpng/table_02 40renders/KF d3: status=passed, PSNR=24.167826538216577; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render40/rpng/table_02/d3 → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR rpng/table_02 15renders/KF vanilla: status=passed, PSNR=19.18900990486145; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render15/rpng/table_02/vanilla → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR rpng/table_02 15renders/KF d3: status=passed, PSNR=21.446611975970335; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render15/rpng/table_02/d3 → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR rpng/table_01 40renders/KF vanilla: status=passed, PSNR=22.743234839572374; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render40/rpng/table_01/vanilla → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR rpng/table_01 40renders/KF d3: status=passed, PSNR=25.7536418618434; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render40/rpng/table_01/d3 → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR rpng/table_01 15renders/KF vanilla: status=passed, PSNR=21.345150768994333; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render15/rpng/table_01/vanilla → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR rpng/table_01 15renders/KF d3: status=passed, PSNR=24.407874449315774; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render15/rpng/table_01/d3 → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR aria/aria1253 15renders/KF vanilla: status=passed, PSNR=19.023149574075948; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/pilot_v1/render15/aria/aria1253/vanilla → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-10-01 CVPR aria/aria1253 15renders/KF d3: status=passed, PSNR=23.46339702606201; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/pilot_v1/render15/aria/aria1253/d3 → [card](campaigns/06_gain_attribution/cvpr_assets/README.md)

- 2026-09-30 FIFO live 검증 코드·결과 main 반영 완료: bb2d6ce48cbf668d3e910a2fa77c6cbe5d412461, origin/main 및 colin-sync/main push 확인. 기본 unbounded worker는 유지하고 max_pending_packets=2를 opt-in으로 제공; CPU 13 tests, 16 actual-tracker runs, 32 saved-map evaluations 통과. → [card](campaigns/06_gain_attribution/fifo_live/README.md)

- 2026-09-30 actual-tracking FIFO 완료: 4 scenes × 1x/1.5x × ours/vanilla = 16회, saved-map double eval 32회. 8/8 PSNR 이득 유지(mean +2.920/+3.524dB). Mapper optimizer tail=0이나 tracking 지연으로 전조건 realtime 달성은 아님. RPNG/UTMM tracking 설정 차이를 유지한 end-to-end 비교; mapper-only 인과 주장 금지. → [card](campaigns/06_gain_attribution/fifo_live/README.md)

- 2026-09-30 live FIFO 1.0x rot/vanilla: PSNR=21.183946256168554, execution=True, tracking=80.33240165095776s / budget=75.99999987499996s; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/fifo_live/v1/scale1/rot/vanilla → [card](campaigns/06_gain_attribution/fifo_live/README.md)

- 2026-09-30 live FIFO 1.0x rot/ours: PSNR=23.96086298207768, execution=True, tracking=93.42219292395748s / budget=75.99999987499996s; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/fifo_live/v1/scale1/rot/ours → [card](campaigns/06_gain_attribution/fifo_live/README.md)

- 2026-09-30 FIFO live 해석 추가: Aria 두 시퀀스는 Tracking config가 동일하지만 RPNG/UTMM은 기존 custom motion threshold/window/radius=3.6/15/1, vanilla=2.4/25/2를 유지했다. 둘 다 frontend 반복은 실제 4/2이나, KF 수와 tracking 비용까지 다른 전체 시스템 비교다. mapper-only 인과 효과 또는 동일 tracking 비용 비교로 주장하지 않는다. → [card](campaigns/06_gain_attribution/fifo_live/README.md)

- 2026-09-30 live FIFO 1.0x utmm/vanilla: PSNR=18.752133696167558, execution=True, tracking=54.34218886308372s / budget=53.80941700935364s; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/fifo_live/v1/scale1/utmm/vanilla → [card](campaigns/06_gain_attribution/fifo_live/README.md)

- 2026-09-30 live FIFO 1.0x utmm/ours: PSNR=21.17349331761584, execution=True, tracking=54.335821729153395s / budget=53.80941700935364s; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/fifo_live/v1/scale1/utmm/ours → [card](campaigns/06_gain_attribution/fifo_live/README.md)

- 2026-09-30 live FIFO 1.0x rpng/vanilla: PSNR=20.861975919018995, execution=True, tracking=151.89595809811726s / budget=92.24467062950134s; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/fifo_live/v1/scale1/rpng/vanilla → [card](campaigns/06_gain_attribution/fifo_live/README.md)

- 2026-09-30 live FIFO 1.0x rpng/ours: PSNR=24.12675006282222, execution=True, tracking=124.73897861503065s / budget=92.24467062950134s; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/fifo_live/v1/scale1/rpng/ours → [card](campaigns/06_gain_attribution/fifo_live/README.md)

- 2026-09-30 live FIFO 1.5x rot/vanilla: PSNR=21.61899426569704, execution=True, tracking=114.02218396705575s / budget=113.99999981249994s; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/fifo_live/v1/scale1p5/rot/vanilla → [card](campaigns/06_gain_attribution/fifo_live/README.md)

- 2026-09-30 live FIFO 1.5x rot/ours: PSNR=24.75129418920298, execution=True, tracking=116.03360276599415s / budget=113.99999981249994s; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/fifo_live/v1/scale1p5/rot/ours → [card](campaigns/06_gain_attribution/fifo_live/README.md)

- 2026-09-30 live FIFO 1.5x utmm/vanilla: PSNR=18.58018343536942, execution=True, tracking=80.8669381190557s / budget=80.71412551403046s; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/fifo_live/v1/scale1p5/utmm/vanilla → [card](campaigns/06_gain_attribution/fifo_live/README.md)

- 2026-09-30 live FIFO 1.5x utmm/ours: PSNR=21.098959104514417, execution=True, tracking=80.88742585689761s / budget=80.71412551403046s; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/fifo_live/v1/scale1p5/utmm/ours → [card](campaigns/06_gain_attribution/fifo_live/README.md)

- 2026-09-30 live FIFO 1.5x rpng/vanilla: PSNR=21.142978231756537, execution=True, tracking=169.3865443880204s / budget=138.367005944252s; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/fifo_live/v1/scale1p5/rpng/vanilla → [card](campaigns/06_gain_attribution/fifo_live/README.md)

- 2026-09-30 live FIFO 1.5x rpng/ours: PSNR=24.98133297138386, execution=True, tracking=142.05981872300617s / budget=138.367005944252s; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/fifo_live/v1/scale1p5/rpng/ours → [card](campaigns/06_gain_attribution/fifo_live/README.md)

- 2026-09-30 live FIFO 1.5x aria/vanilla: PSNR=21.16782244835191, execution=True, tracking=97.67272765398957s / budget=97.64999836950005s; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/fifo_live/v1/scale1p5/aria/vanilla → [card](campaigns/06_gain_attribution/fifo_live/README.md)

- 2026-09-30 live FIFO 1.5x aria/ours: PSNR=25.77303850013791, execution=True, tracking=97.67256407812238s / budget=97.64999836950005s; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/fifo_live/v1/scale1p5/aria/ours → [card](campaigns/06_gain_attribution/fifo_live/README.md)

- 2026-09-30 live FIFO 1.0x aria/vanilla: PSNR=20.065057652597208, execution=True, tracking=65.5566164997872s / budget=65.09999891300004s; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/fifo_live/v1/scale1/aria/vanilla → [card](campaigns/06_gain_attribution/fifo_live/README.md)

- 2026-09-30 live FIFO 1.0x aria/ours: PSNR=23.283798996728795, execution=True, tracking=69.41958943894133s / budget=65.09999891300004s; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/fifo_live/v1/scale1/aria/ours → [card](campaigns/06_gain_attribution/fifo_live/README.md)

- 2026-09-30 FIFO sensor1x aria/vanilla: PSNR=None, pass=False; results/campaigns/gain_attribution/fifo_sensor1x/gpu_v1/aria/vanilla → [card](campaigns/06_gain_attribution/fifo_sensor1x/README.md)

- 2026-09-30 FIFO sensor1x aria/d3: PSNR=25.778139150779666, pass=True; results/campaigns/gain_attribution/fifo_sensor1x/gpu_v1/aria/d3 → [card](campaigns/06_gain_attribution/fifo_sensor1x/README.md)

- **2026-09-30 geometry main GPU 검증 완료:** main a2f3f62b에서 D3+fixed raster/warp 4회와 official vanilla 4회 새 실행, 각 지도 2회 held-out 평가 통과. Aria/RPNG/UTMM/rot 이득 +4.877/+2.450/+3.222/+3.155 dB(평균 +3.426). 이전 native 저장 결과 대비 평균 −0.087 dB. 입력 prefix 학습량·trajectory·cohort 일치. D3는 40 training renders/KF 외 약 20~21 proxy renders/KF 추가하므로 동일 총 연산 비교 아님. maintenance off/density 유지; 독립 geometry GT는 미평가. 기본 recipe는 변경하지 않음. → [결과](campaigns/06_gain_attribution/geometry_main_validation/SUMMARY.md)

- 2026-09-30 geometry main rot/vanilla: PSNR=21.830012555982247, pass=True; results/campaigns/gain_attribution/geometry_main_validation/gpu_v1/rot/vanilla → [card](campaigns/06_gain_attribution/geometry_main_validation/README.md)

- 2026-09-30 geometry main rot/d3: PSNR=24.98509907956983, pass=True; results/campaigns/gain_attribution/geometry_main_validation/gpu_v1/rot/d3 → [card](campaigns/06_gain_attribution/geometry_main_validation/README.md)

- 2026-09-30 geometry main utmm/vanilla: PSNR=18.87227068123994, pass=True; results/campaigns/gain_attribution/geometry_main_validation/gpu_v1/utmm/vanilla → [card](campaigns/06_gain_attribution/geometry_main_validation/README.md)

- 2026-09-30 geometry main utmm/d3: PSNR=22.09443043779444, pass=True; results/campaigns/gain_attribution/geometry_main_validation/gpu_v1/utmm/d3 → [card](campaigns/06_gain_attribution/geometry_main_validation/README.md)

- 2026-09-30 geometry main rpng/vanilla: PSNR=22.678571195860165, pass=True; results/campaigns/gain_attribution/geometry_main_validation/gpu_v1/rpng/vanilla → [card](campaigns/06_gain_attribution/geometry_main_validation/README.md)

- 2026-09-30 geometry main rpng/d3: PSNR=25.128307569349133, pass=True; results/campaigns/gain_attribution/geometry_main_validation/gpu_v1/rpng/d3 → [card](campaigns/06_gain_attribution/geometry_main_validation/README.md)

- 2026-09-30 geometry main aria/vanilla: PSNR=20.872029646662355, pass=True; results/campaigns/gain_attribution/geometry_main_validation/gpu_v1/aria/vanilla → [card](campaigns/06_gain_attribution/geometry_main_validation/README.md)

- 2026-09-30 geometry main aria/d3: PSNR=25.749060383279815, pass=True; results/campaigns/gain_attribution/geometry_main_validation/gpu_v1/aria/d3 → [card](campaigns/06_gain_attribution/geometry_main_validation/README.md)

- **2026-09-29 병합 main 실제 GPU 4scene 검증 완료:** tested5fa8c76e, fresh ours/vanilla8회PASS. Aria25.776/20.743(+5.033),RPNG25.224/22.473(+2.750),UTMM22.285/18.882(+3.403),rot25.018/21.801(+3.217)dB. 평균+3.601dB. 기존3scene 병합전 대비 최대0.0131dB차이. Rot원본전체1521/heldout305 신규준비,MPS0,동일causal archive·prefix40renders/KF·zero-tail. Fixed-work이며live/geometry검증아님. → [결과](campaigns/06_gain_attribution/main_validation/SUMMARY.md)

- **2026-09-29 main validation aria_rot/vanilla:** PSNR=21.801056358462475, audit=True, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/main_validation/rot_gpu40_v1/vanilla. → [카드](campaigns/06_gain_attribution/main_validation/README.md)

- **2026-09-29 main validation aria_rot/ours:** PSNR=25.018266165061075, audit=True, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/main_validation/rot_gpu40_v1/ours. → [카드](campaigns/06_gain_attribution/main_validation/README.md)

- **2026-09-29 main validation utmm/vanilla:** PSNR=18.88187265984806, audit=True, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/main_validation/gpu40_v1/utmm/vanilla. → [카드](campaigns/06_gain_attribution/main_validation/README.md)

- **2026-09-29 main validation utmm/ours:** PSNR=22.285248650444878, audit=True, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/main_validation/gpu40_v1/utmm/ours. → [카드](campaigns/06_gain_attribution/main_validation/README.md)

- **2026-09-29 main validation rpng/vanilla:** PSNR=22.47345105420362, audit=True, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/main_validation/gpu40_v1/rpng/vanilla. → [카드](campaigns/06_gain_attribution/main_validation/README.md)

- **2026-09-29 main validation rpng/ours:** PSNR=25.223718175802144, audit=True, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/main_validation/gpu40_v1/rpng/ours. → [카드](campaigns/06_gain_attribution/main_validation/README.md)

- **2026-09-29 main validation aria/vanilla:** PSNR=20.743402051561663, audit=True, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/main_validation/gpu40_v1/aria/vanilla. → [카드](campaigns/06_gain_attribution/main_validation/README.md)

- **2026-09-29 main validation aria/ours:** PSNR=25.77617167698518, audit=True, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/main_validation/gpu40_v1/aria/ours. → [카드](campaigns/06_gain_attribution/main_validation/README.md)

- **2026-09-29 selected mapping handoff:** 확정 336/40render/init1.25×/prune0.1@300 recipe, backend patch 및 checksum 고정; preflight 3scene·CPU28 PASS, 새 GPU실험 없음. [실행 안내](campaigns/06_gain_attribution/selected_recipe/HANDOFF.md).

- **2026-09-28 window quota 비교 완료:** 채택 init1.25×·prune0.1/300·최근10KF birth보호·40renders/KF에서 3:3:6 대비 1:5:6은 Aria/RPNG/UTMM +0.025/−0.042/−0.058dB, 0:6:6은 −0.004/−0.293/−0.166dB. 신규6회 audit PASS; render/Adam·birth·pool·prune시점 일치(066 일부 KF/dense ±1회). 3:3:6 유지, 1:5:6은 대안. Full-history retention과 recent allocation은 양립하며, geometry/실시간성 증명은 아님. → [결과](campaigns/06_gain_attribution/window_quota/SUMMARY.md)

- **2026-09-28 window quota 066 / utmm40:** PSNR=22.10634505012889, GS=121305, audit=True, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/window_quota/gpu40_v1/utmm/066. → [카드](campaigns/06_gain_attribution/window_quota/README.md)

- **2026-09-28 window quota 156 / utmm40:** PSNR=22.214482425171653, GS=121702, audit=True, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/window_quota/gpu40_v1/utmm/156. → [카드](campaigns/06_gain_attribution/window_quota/README.md)

- **2026-09-28 window quota 066 / rpng40:** PSNR=24.9324430826548, GS=193157, audit=True, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/window_quota/gpu40_v1/rpng/066. → [카드](campaigns/06_gain_attribution/window_quota/README.md)

- **2026-09-28 window quota 156 / rpng40:** PSNR=25.183229226464622, GS=199189, audit=True, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/window_quota/gpu40_v1/rpng/156. → [카드](campaigns/06_gain_attribution/window_quota/README.md)

- **2026-09-28 window quota 066 / aria40:** PSNR=25.778746939797436, GS=193307, audit=True, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/window_quota/gpu40_v1/aria/066. → [카드](campaigns/06_gain_attribution/window_quota/README.md)

- **2026-09-28 window quota 156 / aria40:** PSNR=25.8073416193023, GS=194674, audit=True, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/window_quota/gpu40_v1/aria/156. → [카드](campaigns/06_gain_attribution/window_quota/README.md)

- **2026-09-28 protected prune opacity01 / utmm40 period=300 birth_denominator=0.8:** PSNR=22.27217948583909, GS=121363, audit=True, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/protected_prune/init_increase300_v1/utmm/increase/opacity01. → [카드](campaigns/06_gain_attribution/protected_prune/README.md)

- **2026-09-28 protected prune opacity01 / utmm40 period=300 birth_denominator=1.0:** PSNR=22.129522300060884, GS=98000, audit=True, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/protected_prune/init_increase300_v1/utmm/base/opacity01. → [카드](campaigns/06_gain_attribution/protected_prune/README.md)

- **2026-09-28 protected prune opacity01 / rpng40 period=300 birth_denominator=0.8:** PSNR=25.225351079305014, GS=202838, audit=True, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/protected_prune/init_increase300_v1/rpng/increase/opacity01. → [카드](campaigns/06_gain_attribution/protected_prune/README.md)

- **2026-09-28 protected prune opacity01 / rpng40 period=300 birth_denominator=1.0:** PSNR=25.08195193866352, GS=164895, audit=True, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/protected_prune/init_increase300_v1/rpng/base/opacity01. → [카드](campaigns/06_gain_attribution/protected_prune/README.md)

- **2026-09-28 protected prune opacity01 / aria40 period=300 birth_denominator=0.8:** PSNR=25.782753099922004, GS=195316, audit=True, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/protected_prune/init_increase300_v1/aria/increase/opacity01. → [카드](campaigns/06_gain_attribution/protected_prune/README.md)

- **2026-09-28 protected prune opacity01 / aria40 period=300 birth_denominator=1.0:** PSNR=25.838654343408482, GS=158393, audit=True, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/protected_prune/init_increase300_v1/aria/base/opacity01. → [카드](campaigns/06_gain_attribution/protected_prune/README.md)

- **2026-09-27 protected prune opacity01 / utmm40:** PSNR=22.12074293324977, GS=96733, audit=True, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/protected_prune/transfer40_v1/utmm/opacity01. → [카드](campaigns/06_gain_attribution/protected_prune/README.md)

- **2026-09-27 protected prune opacity01 / aria40:** PSNR=25.81622082222509, GS=151604, audit=True, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/protected_prune/transfer40_v1/aria/opacity01. → [카드](campaigns/06_gain_attribution/protected_prune/README.md)

- **2026-09-27 protected prune opacity01 / RPNG40:** PSNR=25.070940272013345, GS=159616, audit=True, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/protected_prune/rpng40_low_v2/opacity01. → [카드](campaigns/06_gain_attribution/protected_prune/README.md)

- **2026-09-27 protected prune opacity07 / RPNG40:** PSNR=24.533669085116, GS=68439, audit=True, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/protected_prune/rpng40_v1/opacity07. → [카드](campaigns/06_gain_attribution/protected_prune/README.md)

- **2026-09-27 protected prune opacity07 / RPNG40:** PSNR=None, GS=None, audit=False, error=Traceback (most recent call last):
  File "/home/intern/gs_floaterLab/benchmarks/online_gs/campaigns/gain_attribution/run_protected_prune_comparison.py", line 113, in main
    assert births - removed - resets == x['gaussians']
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError
; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/protected_prune/rpng40_v1/opacity07. → [카드](campaigns/06_gain_attribution/protected_prune/README.md)

- **2026-09-27 protected prune off / RPNG40:** PSNR=25.223685410645633, GS=357071, audit=True, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/protected_prune/rpng40_v1/off. → [카드](campaigns/06_gain_attribution/protected_prune/README.md)

- **2026-09-27 init density budget40 b40_vanilla_count / aria:** execution=True, audit=True, PSNR=25.876509426204304, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/init_density/vanilla_count_gpu15_40_v1/b40_vanilla_count/aria. → [카드](campaigns/06_gain_attribution/init_density/vanilla_budget/README.md)

- **2026-09-27 init density budget15 b15_vanilla_count / utmm:** execution=True, audit=True, PSNR=20.996181264335725, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/init_density/vanilla_count_gpu15_40_v1/b15_vanilla_count/utmm. → [카드](campaigns/06_gain_attribution/init_density/vanilla_budget/README.md)

- **2026-09-27 init density budget15 b15_vanilla_count / rpng:** execution=True, audit=True, PSNR=23.915152496475358, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/init_density/vanilla_count_gpu15_40_v1/b15_vanilla_count/rpng. → [카드](campaigns/06_gain_attribution/init_density/vanilla_budget/README.md)

- **2026-09-27 init density budget15 b15_vanilla_count / aria:** execution=True, audit=True, PSNR=23.243475120486195, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/init_density/vanilla_count_gpu15_40_v1/b15_vanilla_count/aria. → [카드](campaigns/06_gain_attribution/init_density/vanilla_budget/README.md)

- **2026-09-27 init density budget40 b40_d4 / utmm:** execution=True, audit=True, PSNR=20.53334234967644, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/init_density/gpu15_40_v1/b40_d4/utmm. → [카드](campaigns/06_gain_attribution/init_density/README.md)

- **2026-09-27 init density budget40 b40_d4 / rpng:** execution=True, audit=True, PSNR=24.59093381520864, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/init_density/gpu15_40_v1/b40_d4/rpng. → [카드](campaigns/06_gain_attribution/init_density/README.md)

- **2026-09-27 init density budget40 b40_d4 / aria:** execution=True, audit=True, PSNR=25.409114167890475, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/init_density/gpu15_40_v1/b40_d4/aria. → [카드](campaigns/06_gain_attribution/init_density/README.md)

- **2026-09-27 init density budget40 b40_d2 / utmm:** execution=True, audit=True, PSNR=21.528685793464568, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/init_density/gpu15_40_v1/b40_d2/utmm. → [카드](campaigns/06_gain_attribution/init_density/README.md)

- **2026-09-27 init density budget40 b40_d2 / rpng:** execution=True, audit=True, PSNR=25.011698600837775, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/init_density/gpu15_40_v1/b40_d2/rpng. → [카드](campaigns/06_gain_attribution/init_density/README.md)

- **2026-09-27 init density budget40 b40_d2 / aria:** execution=True, audit=True, PSNR=25.699089334211276, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/init_density/gpu15_40_v1/b40_d2/aria. → [카드](campaigns/06_gain_attribution/init_density/README.md)

- **2026-09-27 init density budget40 b40_d1 / utmm:** execution=True, audit=True, PSNR=22.223149417359153, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/init_density/gpu15_40_v1/b40_d1/utmm. → [카드](campaigns/06_gain_attribution/init_density/README.md)

- **2026-09-27 init density budget40 b40_d1 / rpng:** execution=True, audit=True, PSNR=25.220881003302498, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/init_density/gpu15_40_v1/b40_d1/rpng. → [카드](campaigns/06_gain_attribution/init_density/README.md)

- **2026-09-27 init density budget40 b40_d1 / aria:** execution=True, audit=True, PSNR=25.910708995265814, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/init_density/gpu15_40_v1/b40_d1/aria. → [카드](campaigns/06_gain_attribution/init_density/README.md)

- **2026-09-27 init density budget15 b15_d4 / utmm:** execution=True, audit=True, PSNR=19.369094477759468, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/init_density/gpu15_40_v1/b15_d4/utmm. → [카드](campaigns/06_gain_attribution/init_density/README.md)

- **2026-09-27 init density budget15 b15_d4 / rpng:** execution=True, audit=True, PSNR=23.506212351343653, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/init_density/gpu15_40_v1/b15_d4/rpng. → [카드](campaigns/06_gain_attribution/init_density/README.md)

- **2026-09-27 init density budget15 b15_d4 / aria:** execution=True, audit=True, PSNR=23.317019058547857, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/init_density/gpu15_40_v1/b15_d4/aria. → [카드](campaigns/06_gain_attribution/init_density/README.md)

- **2026-09-27 init density budget15 b15_d2 / utmm:** execution=True, audit=True, PSNR=20.284989053820386, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/init_density/gpu15_40_v1/b15_d2/utmm. → [카드](campaigns/06_gain_attribution/init_density/README.md)

- **2026-09-27 init density budget15 b15_d2 / rpng:** execution=True, audit=True, PSNR=23.892736204680023, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/init_density/gpu15_40_v1/b15_d2/rpng. → [카드](campaigns/06_gain_attribution/init_density/README.md)

- **2026-09-27 init density budget15 b15_d2 / aria:** execution=True, audit=True, PSNR=23.232974969703733, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/init_density/gpu15_40_v1/b15_d2/aria. → [카드](campaigns/06_gain_attribution/init_density/README.md)

- **2026-09-27 init density budget15 b15_d1 / utmm:** execution=True, audit=True, PSNR=20.87415121808464, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/init_density/gpu15_40_v1/b15_d1/utmm. → [카드](campaigns/06_gain_attribution/init_density/README.md)

- **2026-09-27 init density budget15 b15_d1 / rpng:** execution=True, audit=True, PSNR=24.023711683943464, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/init_density/gpu15_40_v1/b15_d1/rpng. → [카드](campaigns/06_gain_attribution/init_density/README.md)

- **2026-09-27 init density budget15 b15_d1 / aria:** execution=True, audit=True, PSNR=23.25464710206476, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/init_density/gpu15_40_v1/b15_d1/aria. → [카드](campaigns/06_gain_attribution/init_density/README.md)

- **2026-09-27 15renders/KF RR/ERVS+dense 2×2 완료:** κ16/τ4·3:3:6·영상별Adam유지. Dense에서RR→ERVS Aria22.8292→23.2723(+0.4431),RPNG23.4701→24.0295(+0.5594),UTMM21.1453→20.8756(−0.2696)dB;평균+0.2443(40회+0.0755). Dense−KF RGB-only는ERVS평균+0.2022(3/3개선),RR+0.0640(RPNG−0.4159). GPU12개/평가2회/CPU36/audit PASS;render·Adam·admission·pose·GS동일. Dense↔KF replacement는pool/초기quota로RGB횟수·batch/LR일부상이한시스템비교임을명시. ERVS mapper합계96.52→113.96s(+18.1%). 단일seed3개개발scene/frozen tracker;15회재튜닝/live/geometry검증아님. 기본설정유지. → [결과](campaigns/06_gain_attribution/unified_rr_ervs/SUMMARY15.md)

- **2026-09-27 KF RGB replacement RR/ERVS budget15 rr / utmm:** execution=True, audit=True, PSNR=20.6493724098912, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/unified_rr_ervs/dense_control_gpu15_v1/rr/utmm. → [카드](campaigns/06_gain_attribution/unified_rr_ervs/dense_control/README.md)

- **2026-09-27 KF RGB replacement RR/ERVS budget15 rr / rpng:** execution=True, audit=True, PSNR=23.88601891801164, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/unified_rr_ervs/dense_control_gpu15_v1/rr/rpng. → [카드](campaigns/06_gain_attribution/unified_rr_ervs/dense_control/README.md)

- **2026-09-27 KF RGB replacement RR/ERVS budget15 rr / aria:** execution=True, audit=True, PSNR=22.71711030625205, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/unified_rr_ervs/dense_control_gpu15_v1/rr/aria. → [카드](campaigns/06_gain_attribution/unified_rr_ervs/dense_control/README.md)

- **2026-09-27 KF RGB replacement RR/ERVS budget15 ervs / utmm:** execution=True, audit=True, PSNR=20.63515997227327, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/unified_rr_ervs/dense_control_gpu15_v1/ervs/utmm. → [카드](campaigns/06_gain_attribution/unified_rr_ervs/dense_control/README.md)

- **2026-09-27 KF RGB replacement RR/ERVS budget15 ervs / rpng:** execution=True, audit=True, PSNR=23.876651110949815, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/unified_rr_ervs/dense_control_gpu15_v1/ervs/rpng. → [카드](campaigns/06_gain_attribution/unified_rr_ervs/dense_control/README.md)

- **2026-09-27 KF RGB replacement RR/ERVS budget15 ervs / aria:** execution=True, audit=True, PSNR=23.059171130638997, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/unified_rr_ervs/dense_control_gpu15_v1/ervs/aria. → [카드](campaigns/06_gain_attribution/unified_rr_ervs/dense_control/README.md)

- **2026-09-27 unified RR/ERVS budget15 rr / utmm:** execution=True, audit=True, PSNR=21.145271783993568, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/unified_rr_ervs/gpu15_v1/rr/utmm. → [카드](campaigns/06_gain_attribution/unified_rr_ervs/README.md)

- **2026-09-27 unified RR/ERVS budget15 rr / rpng:** execution=True, audit=True, PSNR=23.470087779964413, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/unified_rr_ervs/gpu15_v1/rr/rpng. → [카드](campaigns/06_gain_attribution/unified_rr_ervs/README.md)

- **2026-09-27 unified RR/ERVS budget15 rr / aria:** execution=True, audit=True, PSNR=22.8291896208552, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/unified_rr_ervs/gpu15_v1/rr/aria. → [카드](campaigns/06_gain_attribution/unified_rr_ervs/README.md)

- **2026-09-27 unified RR/ERVS budget15 ervs / utmm:** execution=True, audit=True, PSNR=20.87563637745233, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/unified_rr_ervs/gpu15_v1/ervs/utmm. → [카드](campaigns/06_gain_attribution/unified_rr_ervs/README.md)

- **2026-09-27 unified RR/ERVS budget15 ervs / rpng:** execution=True, audit=True, PSNR=24.029511869275893, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/unified_rr_ervs/gpu15_v1/ervs/rpng. → [카드](campaigns/06_gain_attribution/unified_rr_ervs/README.md)

- **2026-09-27 unified RR/ERVS budget15 ervs / aria:** execution=True, audit=True, PSNR=23.27230923776408, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/unified_rr_ervs/gpu15_v1/ervs/aria. → [카드](campaigns/06_gain_attribution/unified_rr_ervs/README.md)

- **2026-09-27 unified RR vs ERVS 완료:** κ16/τ4·40renders/KF·3:3:6·영상별Adam에서 RR→ERVS: Aria25.7931→25.8847(+0.0916), RPNG25.0777→25.2298(+0.1521), UTMM22.2401→22.2229(−0.0171)dB; 평균+0.0755dB. GPU6개 개별audit/평가2회PASS, 총·prefix render/Adam/admission/pool/loss/LR/GS동일. Pair exact-role audit는 폐기되는Aria 초기generation의window↔KF5회차이로실패; 차이를보존하고loss schedule·최종generation exact-role 일치 재검증. RR공유KF-control CPU오류수정후36tests·기본dense경로1500batch동등성PASS. 기본ERVS유지. 단일seed3개개발scene/frozen tracker이며 보편적우월성·live·geometry근거아님. → [결과](campaigns/06_gain_attribution/unified_rr_ervs/SUMMARY.md)

- **2026-09-27 unified RR/ERVS rr / utmm:** execution=True, audit=True, PSNR=22.240062716566484, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/unified_rr_ervs/gpu40_v1/rr/utmm. → [카드](campaigns/06_gain_attribution/unified_rr_ervs/README.md)

- **2026-09-27 unified RR/ERVS rr / rpng:** execution=True, audit=True, PSNR=25.077735567522478, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/unified_rr_ervs/gpu40_v1/rr/rpng. → [카드](campaigns/06_gain_attribution/unified_rr_ervs/README.md)

- **2026-09-27 unified RR/ERVS rr / aria:** execution=True, audit=True, PSNR=25.793071950664956, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/unified_rr_ervs/gpu40_v1/rr/aria. → [카드](campaigns/06_gain_attribution/unified_rr_ervs/README.md)

- **2026-09-27 unified RR/ERVS ervs / utmm:** execution=True, audit=True, PSNR=22.222941828362735, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/unified_rr_ervs/gpu40_v1/ervs/utmm. → [카드](campaigns/06_gain_attribution/unified_rr_ervs/README.md)

- **2026-09-27 unified RR/ERVS ervs / rpng:** execution=True, audit=True, PSNR=25.229798847920186, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/unified_rr_ervs/gpu40_v1/ervs/rpng. → [카드](campaigns/06_gain_attribution/unified_rr_ervs/README.md)

- **2026-09-27 unified RR/ERVS ervs / aria:** execution=True, audit=True, PSNR=25.884680151029396, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/unified_rr_ervs/gpu40_v1/ervs/aria. → [카드](campaigns/06_gain_attribution/unified_rr_ervs/README.md)

- **2026-09-26 κ/τ/blur 탐색 완료:** 공통선택 k16_t4_no_blur, 기존immediate/tau1/blurOFF 대비 평균held-out PSNR+0.1734dB·합산mapper시간26.0%감소. aria25.5921→25.8851dB,54.54→35.11s / rpng25.1179→25.2309dB,144.35→115.36s / utmm22.1052→22.2194dB,56.11→38.28s. dense-only κ growth와 실제 pool별tau 보고 연결,40renders/KF·3:3:6·영상별Adam·누적ERVS·scaleON·densify/pruneOFF 유지. 유효21run/CPU30/저장지도평가2회/causal-prefix-cohort-source audit PASS. 초기runtime guard 학습전실패1건 보존·수정, baseline3개 명시재사용. 별도online_mapping_unified_tuned.json 저장, 기존baseline preset유지. 단일seed3개개발scene/frozen tracker/coarse search이며 live·geometry검증 아님. → [결과](campaigns/06_gain_attribution/growth_entropy_blur/SUMMARY.md)

- **2026-09-26 growth/entropy/blur k16_t4_no_blur / utmm:** execution=True, audit=True, PSNR=22.219356218973797, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/growth_entropy_blur/gpu40_v2/k16_t4_no_blur/utmm. → [카드](campaigns/06_gain_attribution/growth_entropy_blur/README.md)

- **2026-09-26 growth/entropy/blur k16_t4_no_blur / rpng:** execution=True, audit=True, PSNR=25.23090243983913, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/growth_entropy_blur/gpu40_v2/k16_t4_no_blur/rpng. → [카드](campaigns/06_gain_attribution/growth_entropy_blur/README.md)

- **2026-09-26 growth/entropy/blur k16_t4_no_blur / aria:** execution=True, audit=True, PSNR=25.885081065520076, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/growth_entropy_blur/gpu40_v2/k16_t4_no_blur/aria. → [카드](campaigns/06_gain_attribution/growth_entropy_blur/README.md)

- **2026-09-26 growth/entropy/blur k16_t4_blur / utmm:** execution=True, audit=True, PSNR=22.234002501876265, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/growth_entropy_blur/gpu40_v2/k16_t4_blur/utmm. → [카드](campaigns/06_gain_attribution/growth_entropy_blur/README.md)

- **2026-09-26 growth/entropy/blur k16_t4_blur / rpng:** execution=True, audit=True, PSNR=25.205477929330087, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/growth_entropy_blur/gpu40_v2/k16_t4_blur/rpng. → [카드](campaigns/06_gain_attribution/growth_entropy_blur/README.md)

- **2026-09-26 growth/entropy/blur k16_t4_blur / aria:** execution=True, audit=True, PSNR=25.899103892668514, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/growth_entropy_blur/gpu40_v2/k16_t4_blur/aria. → [카드](campaigns/06_gain_attribution/growth_entropy_blur/README.md)

- **2026-09-26 growth/entropy/blur k16_t0.25_blur / utmm:** execution=True, audit=True, PSNR=21.865269357775464, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/growth_entropy_blur/gpu40_v2/k16_t0.25_blur/utmm. → [카드](campaigns/06_gain_attribution/growth_entropy_blur/README.md)

- **2026-09-26 growth/entropy/blur k16_t0.25_blur / rpng:** execution=True, audit=True, PSNR=24.73448858175192, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/growth_entropy_blur/gpu40_v2/k16_t0.25_blur/rpng. → [카드](campaigns/06_gain_attribution/growth_entropy_blur/README.md)

- **2026-09-26 growth/entropy/blur k16_t0.25_blur / aria:** execution=True, audit=True, PSNR=23.529499297833624, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/growth_entropy_blur/gpu40_v2/k16_t0.25_blur/aria. → [카드](campaigns/06_gain_attribution/growth_entropy_blur/README.md)

- **2026-09-26 growth/entropy/blur k16_t1_blur / utmm:** execution=True, audit=True, PSNR=22.07020735446318, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/growth_entropy_blur/gpu40_v2/k16_t1_blur/utmm. → [카드](campaigns/06_gain_attribution/growth_entropy_blur/README.md)

- **2026-09-26 growth/entropy/blur k16_t1_blur / rpng:** execution=True, audit=True, PSNR=25.133578357181033, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/growth_entropy_blur/gpu40_v2/k16_t1_blur/rpng. → [카드](campaigns/06_gain_attribution/growth_entropy_blur/README.md)

- **2026-09-26 growth/entropy/blur k16_t1_blur / aria:** execution=True, audit=True, PSNR=25.831853204101098, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/growth_entropy_blur/gpu40_v2/k16_t1_blur/aria. → [카드](campaigns/06_gain_attribution/growth_entropy_blur/README.md)

- **2026-09-26 growth/entropy/blur k8_t1_blur / utmm:** execution=True, audit=True, PSNR=21.978632038022266, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/growth_entropy_blur/gpu40_v2/k8_t1_blur/utmm. → [카드](campaigns/06_gain_attribution/growth_entropy_blur/README.md)

- **2026-09-26 growth/entropy/blur k8_t1_blur / rpng:** execution=True, audit=True, PSNR=24.97500921369673, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/growth_entropy_blur/gpu40_v2/k8_t1_blur/rpng. → [카드](campaigns/06_gain_attribution/growth_entropy_blur/README.md)

- **2026-09-26 growth/entropy/blur k8_t1_blur / aria:** execution=True, audit=True, PSNR=25.700358368968235, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/growth_entropy_blur/gpu40_v2/k8_t1_blur/aria. → [카드](campaigns/06_gain_attribution/growth_entropy_blur/README.md)

- **2026-09-26 growth/entropy/blur k4_t1_blur / utmm:** execution=True, audit=True, PSNR=22.043257966453645, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/growth_entropy_blur/gpu40_v2/k4_t1_blur/utmm. → [카드](campaigns/06_gain_attribution/growth_entropy_blur/README.md)

- **2026-09-26 growth/entropy/blur k4_t1_blur / rpng:** execution=True, audit=True, PSNR=25.108031738556182, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/growth_entropy_blur/gpu40_v2/k4_t1_blur/rpng. → [카드](campaigns/06_gain_attribution/growth_entropy_blur/README.md)

- **2026-09-26 growth/entropy/blur k4_t1_blur / aria:** execution=True, audit=True, PSNR=25.684785697296377, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/growth_entropy_blur/gpu40_v2/k4_t1_blur/aria. → [카드](campaigns/06_gain_attribution/growth_entropy_blur/README.md)

- **2026-09-26 growth/entropy/blur k4_t1_blur / aria:** execution=False, audit=False, PSNR=None, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/growth_entropy_blur/gpu40_v1/k4_t1_blur/aria. → [카드](campaigns/06_gain_attribution/growth_entropy_blur/README.md)

- **2026-09-26 growth/entropy/blur immediate_t1_blur / utmm:** execution=True, audit=True, PSNR=22.09905055128498, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/growth_entropy_blur/gpu40_v1/immediate_t1_blur/utmm. → [카드](campaigns/06_gain_attribution/growth_entropy_blur/README.md)

- **2026-09-26 growth/entropy/blur immediate_t1_blur / rpng:** execution=True, audit=True, PSNR=25.089143038225604, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/growth_entropy_blur/gpu40_v1/immediate_t1_blur/rpng. → [카드](campaigns/06_gain_attribution/growth_entropy_blur/README.md)

- **2026-09-26 growth/entropy/blur immediate_t1_blur / aria:** execution=True, audit=True, PSNR=25.614341794079497, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/growth_entropy_blur/gpu40_v1/immediate_t1_blur/aria. → [카드](campaigns/06_gain_attribution/growth_entropy_blur/README.md)

- **2026-09-26 KF RGB-only 대조군 완료:** dense 자리를 full-KF RGB-only로 대체하고 KF native와 선택 UID/order/batch/LR/count exact match. 동일40 renders/KF·3:3:6·영상별Adam에서 KF native→KF RGB-only→dense RGB-only: Aria24.7299→25.0578→25.5921, RPNG24.8112→25.0035→25.1179, UTMM21.4156→21.7631→22.1052dB. Loss recipe 교체 평균+0.2892dB, dense 경로의 추가이득+0.3303dB. Dense가 여전히3/3높지만 mapper54.54/144.35/56.11초 vs KF RGB-only24.50/88.77/30.15초로 시간비용 큼. RGB항도 masked L1→L1+SSIM으로 달라 depth/normal 제거 단독효과는 아님. CPU27/GPU9/평가2회/모든causal·prefix·cohort·source audit PASS. 기본dense 유지. immediate admission으로κ64비활성, tau1/N 각pool·누적ERVS; κ growth의 근거 아님. 단일seed3개개발scene/frozen tracker이며 live검증 아님. → [결과](campaigns/06_gain_attribution/kf_rgb_control/SUMMARY.md)

- **2026-09-26 KF RGB control kf_rgb / utmm:** execution=True, audit=True, PSNR=21.763058300371522, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/kf_rgb_control/gpu40_v1/kf_rgb/utmm. → [카드](campaigns/06_gain_attribution/kf_rgb_control/README.md)

- **2026-09-26 KF RGB control kf_native / utmm:** execution=True, audit=True, PSNR=21.41564631756441, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/kf_rgb_control/gpu40_v1/kf_native/utmm. → [카드](campaigns/06_gain_attribution/kf_rgb_control/README.md)

- **2026-09-26 KF RGB control dense_rgb / utmm:** execution=True, audit=True, PSNR=22.105193120461923, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/kf_rgb_control/gpu40_v1/dense_rgb/utmm. → [카드](campaigns/06_gain_attribution/kf_rgb_control/README.md)

- **2026-09-26 KF RGB control kf_rgb / rpng:** execution=True, audit=True, PSNR=25.0034789798496, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/kf_rgb_control/gpu40_v1/kf_rgb/rpng. → [카드](campaigns/06_gain_attribution/kf_rgb_control/README.md)

- **2026-09-26 KF RGB control kf_native / rpng:** execution=True, audit=True, PSNR=24.81117957175315, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/kf_rgb_control/gpu40_v1/kf_native/rpng. → [카드](campaigns/06_gain_attribution/kf_rgb_control/README.md)

- **2026-09-26 KF RGB control dense_rgb / rpng:** execution=True, audit=True, PSNR=25.11788134531932, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/kf_rgb_control/gpu40_v1/dense_rgb/rpng. → [카드](campaigns/06_gain_attribution/kf_rgb_control/README.md)

- **2026-09-26 KF RGB control kf_rgb / aria:** execution=True, audit=True, PSNR=25.05776095208321, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/kf_rgb_control/gpu40_v1/kf_rgb/aria. → [카드](campaigns/06_gain_attribution/kf_rgb_control/README.md)

- **2026-09-26 KF RGB control kf_native / aria:** execution=True, audit=True, PSNR=24.729860684343876, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/kf_rgb_control/gpu40_v1/kf_native/aria. → [카드](campaigns/06_gain_attribution/kf_rgb_control/README.md)

- **2026-09-26 KF RGB control dense_rgb / aria:** execution=True, audit=True, PSNR=25.59209155308381, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/kf_rgb_control/gpu40_v1/dense_rgb/aria. → [카드](campaigns/06_gain_attribution/kf_rgb_control/README.md)

- **2026-09-26 dense blur 후보 필터 검증 완료:** 실제 worker의 dense admission 앞에 CPU 상대선명도 gate 추가. 이미 도착한 KF구간 RGB만 사용, held-out/미래 입력0, 탈락 dense의 pose/GPU학습0 검증. 같은40 renders/KF·3:3:6·영상별Adam·누적ERVS·scale projection ON에서 필터OFF Aria/RPNG/UTMM25.5957/25.1127/22.1109→ON25.6071/25.0991/22.1037dB(+0.011/−0.014/−0.007). 7/110/23장 제외, no-dense3:9:0의24.7387/24.7991/21.3995 대비+0.868/+0.300/+0.704dB; 공식vanilla40 대비+4.856/+2.638/+3.279 유지. 초기보수적gate는0/2/0장 제외라 별도보존. 총12GPUrun/24CPUtests/저장지도평가2회 PASS. 품질향상·속도향상 근거는 없어 기본OFF 유지, online_mapping_unified_blur.json opt-in 제공. 단일seed·3개개발scene·frozen causal tracker이며 strict/live검증 아님. → [결과](campaigns/06_gain_attribution/dense_blur_filter/SUMMARY.md)

- **2026-09-26 dense blur on / utmm:** execution=True, audit=True, PSNR=22.10371916971089, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/dense_blur_filter/gpu40_v2/on/utmm. → [카드](campaigns/06_gain_attribution/dense_blur_filter/README.md)

- **2026-09-26 dense blur on / rpng:** execution=True, audit=True, PSNR=25.09907927985664, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/dense_blur_filter/gpu40_v2/on/rpng. → [카드](campaigns/06_gain_attribution/dense_blur_filter/README.md)

- **2026-09-26 dense blur on / aria:** execution=True, audit=True, PSNR=25.607050022096125, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/dense_blur_filter/gpu40_v2/on/aria. → [카드](campaigns/06_gain_attribution/dense_blur_filter/README.md)

- **2026-09-26 dense blur no_dense / utmm:** execution=True, audit=True, PSNR=21.39954235229963, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/dense_blur_filter/gpu40_v1/no_dense/utmm. → [카드](campaigns/06_gain_attribution/dense_blur_filter/README.md)

- **2026-09-26 dense blur on / utmm:** execution=True, audit=True, PSNR=22.12322810844139, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/dense_blur_filter/gpu40_v1/on/utmm. → [카드](campaigns/06_gain_attribution/dense_blur_filter/README.md)

- **2026-09-26 dense blur off / utmm:** execution=True, audit=True, PSNR=22.110949398558816, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/dense_blur_filter/gpu40_v1/off/utmm. → [카드](campaigns/06_gain_attribution/dense_blur_filter/README.md)

- **2026-09-26 dense blur no_dense / rpng:** execution=True, audit=True, PSNR=24.79906783576484, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/dense_blur_filter/gpu40_v1/no_dense/rpng. → [카드](campaigns/06_gain_attribution/dense_blur_filter/README.md)

- **2026-09-26 dense blur on / rpng:** execution=True, audit=True, PSNR=25.13288996241114, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/dense_blur_filter/gpu40_v1/on/rpng. → [카드](campaigns/06_gain_attribution/dense_blur_filter/README.md)

- **2026-09-26 dense blur off / rpng:** execution=True, audit=True, PSNR=25.11266457841203, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/dense_blur_filter/gpu40_v1/off/rpng. → [카드](campaigns/06_gain_attribution/dense_blur_filter/README.md)

- **2026-09-26 dense blur no_dense / aria:** execution=True, audit=True, PSNR=24.738654588015024, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/dense_blur_filter/gpu40_v1/no_dense/aria. → [카드](campaigns/06_gain_attribution/dense_blur_filter/README.md)

- **2026-09-26 dense blur on / aria:** execution=True, audit=True, PSNR=25.573838343147102, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/dense_blur_filter/gpu40_v1/on/aria. → [카드](campaigns/06_gain_attribution/dense_blur_filter/README.md)

- **2026-09-26 dense blur off / aria:** execution=True, audit=True, PSNR=25.595737493675173, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/dense_blur_filter/gpu40_v1/off/aria. → [카드](campaigns/06_gain_attribution/dense_blur_filter/README.md)

- **2026-09-26 unified mapping 최종 검증/기본값 반영:** arrival당 packet1개로 tracker/control 반영과 학습을 통합. native optimizer0·별도 추가학습 packet0, recent-window uniform + full-KF/full-dense 누적 ERVS로 구성. 12장 비율4종×3scene, 영상별 Adam2종×3scene, 기존 scale≤0.1 후처리 복원1종×3scene 총21run 검증. 같은 선택 순서·각 영상 LR에서 묶음별→영상별 Adam으로 품질 회복 확인. 최종3:3:6·영상별 Adam·densify/prune/phase gate OFF·기존 scale 상한 유지,40 renders/KF·seed0에서 Aria/RPNG/UTMM25.5923/25.1177/22.1263 dB. paired OFF25.0216/24.7836/21.7006 대비 +0.5707/+0.3341/+0.4257(평균+0.4435)dB; mapper50.68→52.64 /130.16→138.62 /51.53→55.47초(+4~8%). 모든 arm causal/prefix/cohort/count/one-packet/topology guard 및 저장지도 평가2회 PASS, 최종CPU16tests PASS. 최초 통합 경로가 빠뜨린 native scale projection은 복원해 최종검증했으며 상한 없는26.26dB는 진단 결과로만 유지. integration unified 기본값과 configs/online_mapping_unified.json 반영; paired 재현 경로 및 생산 트리 유지. ratio 탐색용3scene 단일seed이며 실제 동시tracking/live 및 geometry 개선 검증 아님. → [결과](campaigns/06_gain_attribution/unified_batch/SUMMARY.md)

- **2026-09-25 unified batch 336m1p / utmm:** execution=True, audit=True, held-out PSNR=22.126344736711477; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/unified_batch/projected_v1/336m1p/utmm. → [카드](campaigns/06_gain_attribution/unified_batch/README.md)

- **2026-09-25 unified batch 336m1p / rpng:** execution=True, audit=True, held-out PSNR=25.117675599106796; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/unified_batch/projected_v1/336m1p/rpng. → [카드](campaigns/06_gain_attribution/unified_batch/README.md)

- **2026-09-25 unified batch 336m1p / aria:** execution=True, audit=True, held-out PSNR=25.59231961956461; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/unified_batch/projected_v1/336m1p/aria. → [카드](campaigns/06_gain_attribution/unified_batch/README.md)

- **2026-09-25 unified batch 336m1 / utmm:** execution=True, audit=True, held-out PSNR=22.398476506456916; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/unified_batch/optimizer1_v1/336m1/utmm. → [카드](campaigns/06_gain_attribution/unified_batch/README.md)

- **2026-09-25 unified batch 336m1 / rpng:** execution=True, audit=True, held-out PSNR=25.278631107227223; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/unified_batch/optimizer1_v1/336m1/rpng. → [카드](campaigns/06_gain_attribution/unified_batch/README.md)

- **2026-09-25 unified batch 336m1 / aria:** execution=True, audit=True, held-out PSNR=26.264144904740895; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/unified_batch/optimizer1_v1/336m1/aria. → [카드](campaigns/06_gain_attribution/unified_batch/README.md)

- **2026-09-25 unified batch 444m1 / utmm:** execution=True, audit=True, held-out PSNR=22.194252832436266; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/unified_batch/optimizer1_v1/444m1/utmm. → [카드](campaigns/06_gain_attribution/unified_batch/README.md)

- **2026-09-25 unified batch 444m1 / rpng:** execution=True, audit=True, held-out PSNR=25.27027747351844; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/unified_batch/optimizer1_v1/444m1/rpng. → [카드](campaigns/06_gain_attribution/unified_batch/README.md)

- **2026-09-25 unified batch 444m1 / aria:** execution=True, audit=True, held-out PSNR=24.47153246857738; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/unified_batch/optimizer1_v1/444m1/aria. → [카드](campaigns/06_gain_attribution/unified_batch/README.md)

- **2026-09-25 unified batch 336 / utmm:** execution=True, audit=True, held-out PSNR=19.986103846703045; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/unified_batch/gpu40_v1/336/utmm. → [카드](campaigns/06_gain_attribution/unified_batch/README.md)

- **2026-09-25 unified batch 336 / rpng:** execution=True, audit=True, held-out PSNR=23.92392785012185; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/unified_batch/gpu40_v1/336/rpng. → [카드](campaigns/06_gain_attribution/unified_batch/README.md)

- **2026-09-25 unified batch 336 / aria:** execution=True, audit=True, held-out PSNR=23.067362428621482; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/unified_batch/gpu40_v1/336/aria. → [카드](campaigns/06_gain_attribution/unified_batch/README.md)

- **2026-09-25 unified batch 363 / utmm:** execution=True, audit=True, held-out PSNR=19.94246701252313; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/unified_batch/gpu40_v1/363/utmm. → [카드](campaigns/06_gain_attribution/unified_batch/README.md)

- **2026-09-25 unified batch 363 / rpng:** execution=True, audit=True, held-out PSNR=23.79480908368085; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/unified_batch/gpu40_v1/363/rpng. → [카드](campaigns/06_gain_attribution/unified_batch/README.md)

- **2026-09-25 unified batch 363 / aria:** execution=True, audit=True, held-out PSNR=23.133291899702932; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/unified_batch/gpu40_v1/363/aria. → [카드](campaigns/06_gain_attribution/unified_batch/README.md)

- **2026-09-25 unified batch 633 / utmm:** execution=True, audit=True, held-out PSNR=19.758660684397192; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/unified_batch/gpu40_v1/633/utmm. → [카드](campaigns/06_gain_attribution/unified_batch/README.md)

- **2026-09-25 unified batch 633 / rpng:** execution=True, audit=True, held-out PSNR=23.506363653921866; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/unified_batch/gpu40_v1/633/rpng. → [카드](campaigns/06_gain_attribution/unified_batch/README.md)

- **2026-09-25 unified batch 633 / aria:** execution=True, audit=True, held-out PSNR=22.703423805819213; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/unified_batch/gpu40_v1/633/aria. → [카드](campaigns/06_gain_attribution/unified_batch/README.md)

- **2026-09-25 unified batch 444 / utmm:** execution=True, audit=True, held-out PSNR=19.89654070948377; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/unified_batch/gpu40_v1/444/utmm. → [카드](campaigns/06_gain_attribution/unified_batch/README.md)

- **2026-09-25 unified batch 444 / rpng:** execution=True, audit=True, held-out PSNR=23.73948145342303; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/unified_batch/gpu40_v1/444/rpng. → [카드](campaigns/06_gain_attribution/unified_batch/README.md)

- **2026-09-25 unified batch 444 / aria:** execution=True, audit=True, held-out PSNR=22.753850383612946; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/unified_batch/gpu40_v1/444/aria. → [카드](campaigns/06_gain_attribution/unified_batch/README.md)

- **2026-09-25 densify/prune OFF40 최종 완료:** cumulative all_rgb·40 renders/KF·seed0·batch1에서 Aria/RPNG/UTMM held-out PSNR=25.0216/24.7836/21.7006 dB. 직전 cumulative ON 대비 +0.4170/+0.1173/+0.3711 dB(장면 평균 +0.3018), official vanilla 대비 +4.2703/+2.3226/+2.8760 dB. 세 실행 모두 동일 render/Adam/native·extraKF·dense 작업량, causal event/pose/cohort/count 및 저장 지도2회 평가 PASS. densify/prune/stats 금지 호출0회, topology event0회; observation topology gate·phase scheduler OFF, 관측 birth와 초기화/지도 reset 유지. 최종 Gaussian 131388→192623 / 273917→357071 / 76657→141545; mapper초 50.02→50.68 / 123.41→130.16 / 53.71→51.53. fixed-work 단일seed이므로 actual-live·geometry 개선은 미검증. 실험 옵션은 추가했으며 기존 기본 recipe 변경은 없음. → [결과](campaigns/06_gain_attribution/no_densify_prune/SUMMARY.md)

- **2026-09-25 no densify/prune40 / utmm:** execution=True, audit=True, held-out PSNR=21.700596747574984; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/no_densify_prune/gpu40_v2/utmm. → [카드](campaigns/06_gain_attribution/no_densify_prune/README.md)

- **2026-09-25 no densify/prune40 / rpng:** execution=True, audit=True, held-out PSNR=24.783596671164574; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/no_densify_prune/gpu40_v2/rpng. → [카드](campaigns/06_gain_attribution/no_densify_prune/README.md)

- **2026-09-25 no densify/prune40 / aria:** execution=True, audit=True, held-out PSNR=25.021636082015874; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/no_densify_prune/gpu40_v2/aria. → [카드](campaigns/06_gain_attribution/no_densify_prune/README.md)

- **2026-09-25 no densify/prune40 v1 실패 원인/정정:** Aria는 optimizer 0회에서 중단. pruning guard가 tracker 첫 packet의 `GSBackEnd.reset()`을 미허용하여 정상 초기 지도 reset을 차단했다. 품질 실패/결과가 아니라 실행 하네스 실패이며 결과는 보존. `reset` 및 `remove_all_gaussians` 내부만 허용하도록 보완하고 CPU guard에서 직접/nested reset·모델 교체·금지6경로를 확인했다. 학습 중 일반 prune 금지와 operator OFF 설정은 그대로이며 gpu40_v2에서 재실행한다. → [카드](campaigns/06_gain_attribution/no_densify_prune/README.md)

- **2026-09-25 no densify/prune40 / aria:** execution=False, audit=False, held-out PSNR=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/no_densify_prune/gpu40_v1/aria. → [카드](campaigns/06_gain_attribution/no_densify_prune/README.md)

- **2026-09-25 누적 ERVS40 최종 검증 완료:** 동일40 renders/KF·seed0·batch1에서 누적/최근 방식 총6회 실행 및 독립 count/work audit·저장 지도별 평가2회 모두 PASS. 누적 held-out PSNR Aria/RPNG/UTMM=24.6046/24.6663/21.3295 dB, 공식 vanilla40 대비 +3.8532/+2.2053/+2.5049 dB 유지. 현재 소스 recent 재실행 대비 −0.2551/−0.1609/−0.0774 dB(장면 평균 −0.1645). native window 사용까지 포함하는 all_rgb 누적 기본값 유지; 최근 방식의 우위를 누적 ERVS 오류로 해석하지 않음. 기억 기간과 native count 반영이 함께 바뀐 비교이며 causal fixed-work 결과로 actual-live/동시 tracking 성공을 뜻하지 않음. 반복 평가는 학습 seed 반복이 아님. → [결과](campaigns/06_gain_attribution/cumulative_ervs/SUMMARY.md)

- **2026-09-25 cumulative ERVS40 / utmm / recent_photometric:** execution=True, audit=True, held-out PSNR=21.406847058990856; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cumulative_ervs/gpu40_v1/utmm/recent_photometric. → [카드](campaigns/06_gain_attribution/cumulative_ervs/README.md)

- **2026-09-25 cumulative ERVS40 / utmm / all_rgb:** execution=True, audit=True, held-out PSNR=21.32949548886146; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cumulative_ervs/gpu40_v1/utmm/all_rgb. → [카드](campaigns/06_gain_attribution/cumulative_ervs/README.md)

- **2026-09-25 cumulative ERVS40 / rpng / recent_photometric:** execution=True, audit=True, held-out PSNR=24.827265703355945; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cumulative_ervs/gpu40_v1/rpng/recent_photometric. → [카드](campaigns/06_gain_attribution/cumulative_ervs/README.md)

- **2026-09-25 cumulative ERVS40 / rpng / all_rgb:** execution=True, audit=True, held-out PSNR=24.666318010209917; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cumulative_ervs/gpu40_v1/rpng/all_rgb. → [카드](campaigns/06_gain_attribution/cumulative_ervs/README.md)

- **2026-09-25 cumulative ERVS40 / aria / recent_photometric:** execution=True, audit=True, held-out PSNR=24.859723265844448; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cumulative_ervs/gpu40_v1/aria/recent_photometric. → [카드](campaigns/06_gain_attribution/cumulative_ervs/README.md)

- **2026-09-25 cumulative ERVS40 / aria / all_rgb:** execution=True, audit=True, held-out PSNR=24.604614177732977; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cumulative_ervs/gpu40_v1/aria/all_rgb. → [카드](campaigns/06_gain_attribution/cumulative_ervs/README.md)

- **2026-09-25 paired 누적 ERVS 복원:** 사용자 지시로 integration paired 기본 count를 recent_photometric→all_rgb로 변경. KF native+추가 및 dense 실제 완료 사용 횟수를 generation별 누적; 승격 시 보존, 취소 미집계, reset 시 새 generation. CLI로 과거recent 명시 재현 가능. 독립 service ledger audit 및 관련 CPU15test/compile PASS. sampling pool·교대·loss·배치수는 유지. 기존40회 PSNR은 recent 설정 결과이며 새 cumulative 품질 미검증. → [변경/검증](campaigns/06_gain_attribution/cumulative_ervs/README.md)

- **2026-09-25 grouped render timing v2 완료:** 3scene, 같은 초기지도/Adam/영상96개, 1/2/4장 묶음 각6회 warm 측정. ms/render Aria3.407→2.940→2.770, RPNG6.615→6.125→5.950, UTMM2.457→2.077→1.916. 2장7.4–15.4%,4장10.0–22.0% 단축. 준비/전송/선택/guard 제외한 compute 진단이며 live/품질 유지 미검증. 생산 변경 없음. source unchanged 및 replay3run audit PASS. → [결과](campaigns/06_gain_attribution/grouped_render_timing/SUMMARY.md)

- 2026-09-25 v1: causal Aria replay 완료 뒤 offline timing camera 준비가 닫힌 worker의 thread guard에 거부되어 측정 실패. 유효 timing 결과 없음. v2에서 diagnostic의 deferred camera preparation guard만 분리하며 production/EOS guard는 수정하지 않음. → [카드](campaigns/06_gain_attribution/grouped_render_timing/README.md)

- **2026-09-25 — 40 renders/KF 공통 예산 검증 완료:** fixed-work 6회/live 6회 audit 및 저장 지도 평가2회 일치. 정확한40회 비교에서 우리−vanilla PSNR Aria +4.11/RPNG +2.37/UTMM +2.59dB; online40상한에서는 우리 실제17.32/12.39/9.79회(KF/dense 추가350/350,0/0,8/8)로 공통40회 실현 실패. Vanilla는39.87/40.00/39.50회, 처리65.76/150.49/54.25초(입력65.10/92.24/53.81초). RPNG 최종 tracker KF는 논문232/vanilla232/우리211로 과다 최종KF 근거 없음; mapping-off도111.477초. 40은 품질비교 후보이며 실시간 인증값 아님. 생산 mapper/논문/역할배분 변경 없음. → [종합 결과](campaigns/06_gain_attribution/render_budget40_feasibility/SUMMARY.md)

- **2026-09-25 (40 renders/KF / live / utmm / paired):** execution=True, PSNR=11.446189042962628. Result=/home/intern/gs_floaterLab/results/campaigns/gain_attribution/render_budget40_feasibility/v1/live/utmm/paired → [카드](campaigns/06_gain_attribution/render_budget40_feasibility/README.md)

- **2026-09-25 (40 renders/KF / live / utmm / vanilla):** execution=True, PSNR=18.600026333773577. Result=/home/intern/gs_floaterLab/results/campaigns/gain_attribution/render_budget40_feasibility/v1/live/utmm/vanilla → [카드](campaigns/06_gain_attribution/render_budget40_feasibility/README.md)

- **2026-09-25 (40 renders/KF / live / rpng / paired):** execution=True, PSNR=17.819775564176542. Result=/home/intern/gs_floaterLab/results/campaigns/gain_attribution/render_budget40_feasibility/v1/live/rpng/paired → [카드](campaigns/06_gain_attribution/render_budget40_feasibility/README.md)

- **2026-09-25 (40 renders/KF / live / rpng / vanilla):** execution=True, PSNR=21.298174990404835. Result=/home/intern/gs_floaterLab/results/campaigns/gain_attribution/render_budget40_feasibility/v1/live/rpng/vanilla → [카드](campaigns/06_gain_attribution/render_budget40_feasibility/README.md)

- **2026-09-25 (40 renders/KF / live / aria / paired):** execution=True, PSNR=19.30309359717915. Result=/home/intern/gs_floaterLab/results/campaigns/gain_attribution/render_budget40_feasibility/v1/live/aria/paired → [카드](campaigns/06_gain_attribution/render_budget40_feasibility/README.md)

- **2026-09-25 (40 renders/KF / live / aria / vanilla):** execution=True, PSNR=19.935029801521594. Result=/home/intern/gs_floaterLab/results/campaigns/gain_attribution/render_budget40_feasibility/v1/live/aria/vanilla → [카드](campaigns/06_gain_attribution/render_budget40_feasibility/README.md)

- **2026-09-25 (40 renders/KF / fixed / utmm / vanilla):** execution=True, PSNR=18.824628406100803. Result=/home/intern/gs_floaterLab/results/campaigns/gain_attribution/render_budget40_feasibility/v1/fixed/utmm/vanilla → [카드](campaigns/06_gain_attribution/render_budget40_feasibility/README.md)

- **2026-09-25 (40 renders/KF / fixed / utmm / paired):** execution=True, PSNR=21.417964429031183. Result=/home/intern/gs_floaterLab/results/campaigns/gain_attribution/render_budget40_feasibility/v1/fixed/utmm/paired → [카드](campaigns/06_gain_attribution/render_budget40_feasibility/README.md)

- **2026-09-25 (40 renders/KF / fixed / rpng / vanilla):** execution=True, PSNR=22.46096884925086. Result=/home/intern/gs_floaterLab/results/campaigns/gain_attribution/render_budget40_feasibility/v1/fixed/rpng/vanilla → [카드](campaigns/06_gain_attribution/render_budget40_feasibility/README.md)

- **2026-09-25 (40 renders/KF / fixed / rpng / paired):** execution=True, PSNR=24.833668686462953. Result=/home/intern/gs_floaterLab/results/campaigns/gain_attribution/render_budget40_feasibility/v1/fixed/rpng/paired → [카드](campaigns/06_gain_attribution/render_budget40_feasibility/README.md)

- **2026-09-25 (40 renders/KF / fixed / aria / vanilla):** execution=True, PSNR=20.751371936943695. Result=/home/intern/gs_floaterLab/results/campaigns/gain_attribution/render_budget40_feasibility/v1/fixed/aria/vanilla → [카드](campaigns/06_gain_attribution/render_budget40_feasibility/README.md)

- **2026-09-25 (40 renders/KF / fixed / aria / paired):** execution=True, PSNR=24.859212001771418. Result=/home/intern/gs_floaterLab/results/campaigns/gain_attribution/render_budget40_feasibility/v1/fixed/aria/paired → [카드](campaigns/06_gain_attribution/render_budget40_feasibility/README.md)

- **2026-09-25 최종 5090 동시 tracking 비교:** 공식 벤치마크 IMU pose prediction20/20/15 및 frontend4/2 복원, 15 training renders/KF 상한. 바닐라→우리 실제 학습량 Aria15.00→14.79/RPNG15.00→12.43/UTMM14.81→9.73, PSNR차 +0.22/−1.48/−4.44dB. 우리 extra KF/dense267/266,0/0,6/6. 6run 실행 audit·저장map 평가2회 일치 PASS이나 실시간/품질개선 주장은 불성립. RPNG mapping-off도111.477s>92.245s 입력(p95lag21.848s). 기존100000 설정 결과는 진단용 보존; 자세한 최종표는 SUMMARY.md. → [카드](campaigns/06_gain_attribution/live_render_capacity/README.md)

- **2026-09-25 (5090 live / utmm / paired / IMU pose init 15):** renders/KF=9.725806451612904, complete=True, PSNR=11.333392038757419; timing/quality 별도 판정. → [카드](campaigns/06_gain_attribution/live_render_capacity/README.md)

- **2026-09-25 (5090 live / utmm / vanilla / IMU pose init 15):** renders/KF=14.8125, complete=True, PSNR=15.772941839547805; timing/quality 별도 판정. → [카드](campaigns/06_gain_attribution/live_render_capacity/README.md)

- **2026-09-25 (5090 live / rpng / paired / IMU pose init 20):** renders/KF=12.431506849315069, complete=True, PSNR=17.91506887384363; timing/quality 별도 판정. → [카드](campaigns/06_gain_attribution/live_render_capacity/README.md)

- **2026-09-25 (5090 live / rpng / vanilla / IMU pose init 20):** renders/KF=15.0, complete=True, PSNR=19.393897207792815; timing/quality 별도 판정. → [카드](campaigns/06_gain_attribution/live_render_capacity/README.md)

- **2026-09-25 (5090 live / aria / paired / IMU pose init 20):** renders/KF=14.794117647058824, complete=True, PSNR=19.369261101002003; timing/quality 별도 판정. → [카드](campaigns/06_gain_attribution/live_render_capacity/README.md)

- **2026-09-25 (5090 live / aria / vanilla / IMU pose init 20):** renders/KF=15.0, complete=True, PSNR=19.15189616370747; timing/quality 별도 판정. → [카드](campaigns/06_gain_attribution/live_render_capacity/README.md)

- **2026-09-25 설정 정정:** comparison15_v1, current_frontend, v3–v6 및 tracking_controls는 IMU_poseinit_after=100000을 상속했다. IMU preintegration/BA는 실행됐지만 IMU pose prediction은 사실상 비활성이다. 일반 벤치마크 설정으로 해석하지 않는다. 공식 RPNG=20/UTMM=15 및 Aria live=20을 복원한 comparison15_imu_v2를 별도로 실행한다. 기존 측정은 삭제하지 않는다. → [카드](campaigns/06_gain_attribution/live_render_capacity/README.md)

- **2026-09-25 (5090 RPNG tracking-only):** official frontend4/2 설정·mapping0에서도 tracking114.451s/입력92.245s, p95lag24.644s. 같은 tracker+paired15의114.773s와 유사; 이 설정의 1×불가를 렌더 예산만으로 해결할 수 없음. 현재frontend1/0 별도 확인. → [카드](campaigns/06_gain_attribution/live_render_capacity/README.md)

- **2026-09-25 (5090 live / utmm / paired):** renders/KF=9.338709677419354, complete=True, PSNR=10.661520877002198; timing/quality 별도 판정. → [카드](campaigns/06_gain_attribution/live_render_capacity/README.md)

- **2026-09-25 (5090 live / utmm / vanilla):** renders/KF=15.0, complete=True, PSNR=15.932410775879283; timing/quality 별도 판정. → [카드](campaigns/06_gain_attribution/live_render_capacity/README.md)

- **2026-09-25 (5090 live / rpng / paired):** renders/KF=12.356164383561644, complete=True, PSNR=17.74931611928854; timing/quality 별도 판정. → [카드](campaigns/06_gain_attribution/live_render_capacity/README.md)

- **2026-09-25 (5090 live / rpng / vanilla):** renders/KF=14.9765625, complete=True, PSNR=19.750227318153726; timing/quality 별도 판정. → [카드](campaigns/06_gain_attribution/live_render_capacity/README.md)

- **2026-09-25 (5090 live / aria / paired):** renders/KF=14.87, complete=True, PSNR=19.957373200482085; timing/quality 별도 판정. → [카드](campaigns/06_gain_attribution/live_render_capacity/README.md)

- **2026-09-25 (5090 live / aria / vanilla):** renders/KF=15.0, complete=True, PSNR=19.12804331306283; timing/quality 별도 판정. → [카드](campaigns/06_gain_attribution/live_render_capacity/README.md)

- **2026-09-25 (5090 Aria capacity probe):** official frontend4/2+paired, 원속mapper1669render/100KF=16.69. Tracking67.901s/입력65.100s, p95lag3.719s로 안정적realtime capacity아님. 15/KF 공식mapper 비교 진행. → [카드](campaigns/06_gain_attribution/live_render_capacity/README.md)

- **2026-09-25 (5090 live render 계측 시작):** raw RGB/IMU 실제 tracking+paired15 Aria1545render/103admission=15.00, 65.124s, zero-tail. p95입력지연723ms; realtime 품질승인 아님. 준비단계 실패·runner 수정 기록. official4/2 동일조건 비교 진행. → [카드](campaigns/06_gain_attribution/live_render_capacity/README.md)

- **2026-09-25 (15 renders/KF vanilla 비교 완료):** official vanilla3run 동일 prefix별 총렌더·평가cohort/trajectory·이중평가PASS. 새paired−vanilla Aria+1.8184/RPNG+1.0498/UTMM+2.5448dB, 평균+1.8044(seed0). 기존내부구조는 RPNG에서 vanilla보다낮음. fixed-work 진단, 원본source미수정·GPU종료. → [카드](campaigns/06_gain_attribution/render_matched_kf15/README.md)

- **2026-09-25 (15 renders/KF vanilla / utmm):** 15.875981dB, 1350 training renders. → [카드](campaigns/06_gain_attribution/render_matched_kf15/README.md)

- **2026-09-25 (15 renders/KF vanilla / rpng):** 21.228337dB, 3405 training renders. → [카드](campaigns/06_gain_attribution/render_matched_kf15/README.md)

- **2026-09-25 (15 renders/KF vanilla / aria):** 18.906699dB, 1785 training renders. → [카드](campaigns/06_gain_attribution/render_matched_kf15/README.md)

- **2026-09-25 (15 renders/KF 3scene 완료):** 초기화 포함 학습예산15/KF, 기존/paired6run 모두 prefix별 학습·보조포함총렌더 동일·이중평가PASS. paired Δ Aria+0.2596/RPNG+1.7789/UTMM+1.5918dB, 평균+1.2101(seed0). 실행시간은증가. fixed-work 진단이며 실시간/독립ERVS 효과 판정아님; production미수정. → [카드](campaigns/06_gain_attribution/render_matched_kf15/README.md)

- **2026-09-25 (15-render-per-KF / utmm / paired / seed0):** 18.420765dB, mapping 29.606s. → [카드](campaigns/06_gain_attribution/render_matched_kf15/README.md)

- **2026-09-25 (15-render-per-KF / utmm / legacy_growth / seed0):** 16.828925dB, mapping 24.509s. → [카드](campaigns/06_gain_attribution/render_matched_kf15/README.md)

- **2026-09-25 (15-render-per-KF / rpng / paired / seed0):** 22.278183dB, mapping 66.374s. → [카드](campaigns/06_gain_attribution/render_matched_kf15/README.md)

- **2026-09-25 (15-render-per-KF / rpng / legacy_growth / seed0):** 20.499256dB, mapping 49.875s. → [카드](campaigns/06_gain_attribution/render_matched_kf15/README.md)

- **2026-09-25 (15-render-per-KF / aria / paired / seed0):** 20.725142dB, mapping 22.322s. → [카드](campaigns/06_gain_attribution/render_matched_kf15/README.md)

- **2026-09-25 (15-render-per-KF / aria / legacy_growth / seed0):** 20.465558dB, mapping 12.870s. → [카드](campaigns/06_gain_attribution/render_matched_kf15/README.md)

- **2026-09-25 (render budget 변경):** 사용자 지시로 30k 비교 중단, 총15 camera renders/KF 비교로 전환. 고예산 Aria 결과 보존·RPNG 중단·패널미완. → [카드](campaigns/06_gain_attribution/render_matched_kf15/README.md)

- **2026-09-25 (render-matched / aria / paired / seed0):** 27.348867dB, mapping 138.726s. → [카드](campaigns/06_gain_attribution/render_matched/README.md)

- **2026-09-25 (render-matched / aria / legacy_growth / seed0):** 27.708641dB, mapping 97.725s. → [카드](campaigns/06_gain_attribution/render_matched/README.md)

- **2026-09-25 (paired v2 9run 판정):** 3scene×기존/paired/KF-only 실행·동일소스/평가/예산검증PASS. paired 기존대비평균−0.9490dB로 성능유지 실패. KF-only도 Aria/UTMM하락, RPNG유지; dense준비비용만으로 전체하락 설명불가. 구현완료·품질목표미달, production미반영·현재GPU작업없음. → [카드](campaigns/06_gain_attribution/paired_full_pool/README.md)

- **2026-09-25 (paired full-pool / utmm / paired_kf_only / seed0):** 22.126928dB, mapping 80.639s. → [카드](campaigns/06_gain_attribution/paired_full_pool/README.md)

- **2026-09-25 (paired full-pool / rpng / paired_kf_only / seed0):** 24.584378dB, mapping 138.276s. → [카드](campaigns/06_gain_attribution/paired_full_pool/README.md)

- **2026-09-25 (paired full-pool / aria / paired_kf_only / seed0):** 26.496855dB, mapping 97.552s. → [카드](campaigns/06_gain_attribution/paired_full_pool/README.md)

- **2026-09-25 (paired v2 3scene 완료):** 동일소스/예산/평가 검증PASS. paired−기존 Aria-1.3447,RPNG-0.6181,UTMM-0.8843dB, 평균-0.9490; 성능유지 실패. 모든최종지도 dense실사용/최근window/1:1교대검증PASS. KF-only 분리대조 진행. → [카드](campaigns/06_gain_attribution/paired_full_pool/README.md)

- **2026-09-25 (paired full-pool / utmm / legacy_growth / seed0):** 23.269436dB, mapping 80.639s. → [카드](campaigns/06_gain_attribution/paired_full_pool/README.md)

- **2026-09-25 (paired full-pool / utmm / paired / seed0):** 22.385100dB, mapping 80.614s. → [카드](campaigns/06_gain_attribution/paired_full_pool/README.md)

- **2026-09-25 (paired full-pool / rpng / legacy_growth / seed0):** 24.538978dB, mapping 138.277s. → [카드](campaigns/06_gain_attribution/paired_full_pool/README.md)

- **2026-09-25 (paired full-pool / rpng / paired / seed0):** 23.920891dB, mapping 138.276s. → [카드](campaigns/06_gain_attribution/paired_full_pool/README.md)

- **2026-09-25 (paired full-pool / aria / legacy_growth / seed0):** 27.787554dB, mapping 97.553s. → [카드](campaigns/06_gain_attribution/paired_full_pool/README.md)

- **2026-09-25 (paired full-pool / aria / paired / seed0):** 26.442868dB, mapping 97.551s. → [카드](campaigns/06_gain_attribution/paired_full_pool/README.md)

- **2026-09-25 (paired v1 구현검증 정정):** Aria26.5551dB이나 PGBA 후 전체보정KF 재학습 예외 확인; 최근window 전용 구조로는 미승인. v1보존·중단, 실제current_window 강제 및 별도검증 추가·6paired검사PASS. v2 3scene 비교 시작. → [카드](campaigns/06_gain_attribution/paired_full_pool/README.md)

- **2026-09-25 (paired full-pool / aria / paired / seed0):** 26.555117dB, mapping 97.575s. → [카드](campaigns/06_gain_attribution/paired_full_pool/README.md)

- **2026-09-25 (paired full-pool 구현):** 최근window native + KF RGBD/normal·denseRGB 교대 ERVS 구현. full-pool/취소·reset·loss경로 및 기존온라인49검사PASS. zero-depth 역수NaN 수정·대조군동일적용. 3scene seed0 비교 시작; 품질미확정. → [카드](campaigns/06_gain_attribution/paired_full_pool/README.md)

- **2026-09-25 (worker dense 사용량 재분석):** RPNG dense226회는 모두 reset 이전 generation1; 최종generation7은182KF/4817step/dense진입·학습0. whole_pool κ64 조건이 최종지도 dense를 허용하지 않았음. Dense 무효 근거로 해석불가; admission정책 검증 필요. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (actual mapper worker / utmm square-1 growth):** 실패(exit 1); 로그와 상태 보존. seed0; 반복/교차장면/수렴/논문정렬 목표미완. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (actual mapper worker / rpng table_06 kf_only):** 24.487964dB, whole mapping 138.309s; 실행계약/독립이중평가PASS. seed0; 반복/교차장면/수렴/논문정렬 목표미완. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (actual mapper worker / rpng table_06 growth):** 24.460546dB, whole mapping 138.316s; 실행계약/독립이중평가PASS. seed0; 반복/교차장면/수렴/논문정렬 목표미완. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (Aria 실제worker dense 이득):** 동일ERVS dense27.3407/KF27.1628, Δ+0.1779dB; whole-clock/이중평가PASS, seed0미확정. step마다2ms queue대기 발견·생산적학습시대기제거·CPU17검사PASS. v9 공통설정으로3scene 비교 진행. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (actual mapper worker / aria aria1253 kf_only):** 27.162762dB, whole mapping 97.557s; 실행계약/독립이중평가PASS. seed0; 반복/교차장면/수렴/논문정렬 목표미완. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (actual mapper worker / aria aria1253 growth):** 27.340686dB, whole mapping 97.557s; 실행계약/독립이중평가PASS. seed0; 반복/교차장면/수렴/논문정렬 목표미완. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (Aria 전체 mapper worker):** rescale/reset FIFO 연결·CPU32검사PASS. 9137step(native1016/photo8121), held-out27.41716dB 독립이중평가일치. 최초run 전체종료시각 계측부족은 명시미승인; v8에서 worker종료·입력준비 시간을 포함해 dense/KF 비교 중. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (CUDA stream 원인 수정검증):** 별도 DROID·LieTorch46개 launch를 current stream으로 수정·빌드. 실제worker 전용stream/default 대조 모두1024step·dense8개 pose보정 PASS, NaN/lateAdam0·선택횟수일치. 첫packet 실행검증이며 전체온라인 품질미검증; 다음은 rescale/reset worker routing. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (worker packet/CUDA 진단):** heldout 제외시 pose·scale 대응/packet index 수정·CPU28검사PASS. 실제 CUDA 전용stream은 첫dense pose NaN으로 실패(513step); 기본stream 대조는1024step/8dense PASS. legacy DROID·LieTorch current-stream 미사용 확인, 별도바이너리 수정검증 진행·품질목표미완. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (v18 stream quality):** utmm/square-1/production: 20.18s:8.3025dB, 40.56s:12.7913dB, 60.54s:18.1897dB, 80.62s:21.3669dB. Fixed held-out cohort 324; common evaluation coordinates; post-run rendering only. Alignment residuals remain unaccepted; no exact first-attainment claim. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (v18 stream quality):** utmm/square-1/kf_only: 20.18s:8.7536dB, 40.36s:14.1964dB, 60.54s:19.6447dB, 80.61s:22.9322dB. Fixed held-out cohort 324; common evaluation coordinates; post-run rendering only. Alignment residuals remain unaccepted; no exact first-attainment claim. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (실제 VIGS worker API 연결):** 별도본 공통runtime/도착RGB·IMU/pose준비/idle학습 연결·CPU31검사PASS. CUDA·전체control경로·품질반복은 미검증; heldout-only pose control은 현재 명시실패. v18/production 불변·목표미완. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (v18 stream quality):** utmm/square-1/growth_ervs: 20.18s:8.7015dB, 40.36s:14.2734dB, 60.57s:20.0331dB, 80.61s:23.4843dB. Fixed held-out cohort 324; common evaluation coordinates; post-run rendering only. Alignment residuals remain unaccepted; no exact first-attainment claim. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (v18 stream quality):** aria/aria1253/production: 24.44s:10.5841dB, 48.83s:15.1050dB, 73.24s:17.7968dB, 97.55s:25.8522dB. Fixed held-out cohort 262; common evaluation coordinates; post-run rendering only. Alignment residuals remain unaccepted; no exact first-attainment claim. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (v18 stream quality):** aria/aria1253/kf_only: 24.43s:11.6382dB, 48.83s:16.2596dB, 73.24s:17.8599dB, 97.55s:27.5604dB. Fixed held-out cohort 262; common evaluation coordinates; post-run rendering only. Alignment residuals remain unaccepted; no exact first-attainment claim. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (v18 stream quality):** aria/aria1253/growth_ervs: 24.42s:11.6880dB, 48.83s:16.5951dB, 73.24s:17.9812dB, 97.55s:27.7322dB. Fixed held-out cohort 262; common evaluation coordinates; post-run rendering only. Alignment residuals remain unaccepted; no exact first-attainment claim. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (v18 stream quality):** rpng/table_06/production: 34.62s:14.4119dB, 69.52s:22.6222dB, 104.53s:23.9433dB, 138.29s:24.4509dB. Fixed held-out cohort 555; common evaluation coordinates; post-run rendering only. Alignment residuals remain unaccepted; no exact first-attainment claim. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (v18 stream quality):** rpng/table_06/kf_only: 34.89s:14.4297dB, 69.33s:22.7280dB, 104.41s:23.8332dB, 138.27s:25.2330dB. Fixed held-out cohort 555; common evaluation coordinates; post-run rendering only. Alignment residuals remain unaccepted; no exact first-attainment claim. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (v18 stream quality):** rpng/table_06/growth_ervs: 34.92s:14.3760dB, 69.51s:22.6861dB, 104.28s:23.9729dB, 138.28s:25.2114dB. Fixed held-out cohort 555; common evaluation coordinates; post-run rendering only. Alignment residuals remain unaccepted; no exact first-attainment claim. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (v18 중간지도 평가 시작):** 공통KF pose 불일치로 최초export 거부; 정확히 같은 anchor만 사용한 공통좌표 export완료·7검사PASS. Aria75% 정렬잔차0.0713/3.315도 등 남아 곡선은 우선진단용·빠른수렴미확정. 9run 중간렌더평가 진행. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (v18 3scene 비교 완료):** 9/9계약PASS, 후보−KF 평균+0.2341dB/운영대비+1.5860dB. RPNG−0.0216/Aria+0.1719/UTMM+0.5522로 반복검증 필요·미채택. 다음은 중간품질곡선·실제worker연결. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (online whole-pool growth / utmm square-1 production):** held-out 21.366874dB, 80.618/80.714초, 7456 Adam; 전체시간 계약 PASS. 공통100ms여유·중간지도계측 seed0이며 전체목표미완. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (online whole-pool growth / utmm square-1 kf_only):** held-out 22.932163dB, 80.614/80.714초, 19073 Adam; 전체시간 계약 PASS. 공통100ms여유·중간지도계측 seed0이며 전체목표미완. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (별도 worker 통합본 backend 연결):** 새 worktree에서 backend16개 optimizer경로+공통RGB step을 mapper전용 guard로 연결·CPU8검사PASS. 기존 v18/production 불변. 실제 worker·RGB/IMU입력·CUDA연결은 미완. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (online whole-pool growth / utmm square-1 growth_ervs):** held-out 23.484316dB, 80.614/80.714초, 13869 Adam; 전체시간 계약 PASS. 공통100ms여유·중간지도계측 seed0이며 전체목표미완. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (online whole-pool growth / aria aria1253 production):** held-out 25.852154dB, 97.552/97.650초, 11024 Adam; 전체시간 계약 PASS. 공통100ms여유·중간지도계측 seed0이며 전체목표미완. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (online whole-pool growth / aria aria1253 kf_only):** held-out 27.560364dB, 97.552/97.650초, 16823 Adam; 전체시간 계약 PASS. 공통100ms여유·중간지도계측 seed0이며 전체목표미완. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (online whole-pool growth / aria aria1253 growth_ervs):** held-out 27.732228dB, 97.553/97.650초, 13120 Adam; 전체시간 계약 PASS. 공통100ms여유·중간지도계측 seed0이며 전체목표미완. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (live worker 연결 준비):** mapper 인스턴스별 optimizer guard와 EOS/오류 시 queue 취소 worker 구현·CPU10검사PASS. tracker optimizer 불변·late completion 명시실패 확인. 실제 VIGS worker/CUDA연결은 아직 미완, v18 품질실험과 분리. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (online whole-pool growth / rpng table_06 production):** held-out 24.450921dB, 138.288/138.367초, 3434 Adam; 전체시간 계약 PASS. 공통100ms여유·중간지도계측 seed0이며 전체목표미완. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (online whole-pool growth / rpng table_06 kf_only):** held-out 25.233022dB, 138.271/138.367초, 6977 Adam; 전체시간 계약 PASS. 공통100ms여유·중간지도계측 seed0이며 전체목표미완. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (online whole-pool growth / rpng table_06 growth_ervs):** held-out 25.211392dB, 138.277/138.367초, 6766 Adam; 전체시간 계약 PASS. 공통100ms여유·중간지도계측 seed0이며 전체목표미완. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (기하 교차진단 3scene 완료):** depth·normal 유지 dense이득 Aria+0.4321/RPNG+0.0489/UTMM+0.4085dB, 12arm계약PASS. offline진단으로 기하항만의 이득소실 설명기각·online목표미완. v1 NaN은 3번째 native batch의 rendered-depth0에서 재현·운영코드미변경. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (Aria 기하 교차진단 완료):** 동일체크포인트·RGB항·일정·10304render/5312update에서 dense 이득 RGB+0.5028dB, depth·normal유지+0.4321dB(상호작용−0.0707). 기하항만으로 이득소실 설명어려움. afterEOS 진단이며 online성공아님; RPNG/UTMM동일조건 전이예정. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (v1 실패 위치 정정):** 기존 로그에는 native batch번호가 없어 첫 batch 실패 단정은 부정확. v2 첫 batch는 legacy항까지 정상. zero-depth edge case는 재현됐으나 실제 v1 실패지점은 별도계측 필요; 기존기록은 보존. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (기하 교차진단 v1 실패·v2 준비):** 첫 native loss 비정상값으로 중단·결과미산출. zero depth의 역수 후 mask 연산 문제를 CUDA edge case로 재현; 진단전용 유효픽셀 보존 수정검사PASS. 운영mapper 미변경·v1로그보존·전체목표미완. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (실제 Adam 계측 완료):** 3scene 948표본·학습이력/시간/zero-tail검사PASS. dense만의 파괴적 momentum 근거 없음(KF와 유사한 크기·방향). optimizer 미변경; RGB항/일정 고정한 depth·normal 교차진단이 다음 작업. 전체목표미완. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (v17 완료·다음은 optimizer 상호작용):** 3/3 계약PASS,25.0013/27.5497/23.3153dB. KF대비 평균+0.0411이나 RPNG−0.2245/Aria−0.0316로 미채택. native 다중영상 sum/단일RGB가 Adam을 공유하는 코드 확인·악영향 미검증. GPU idle·production 변경없음·전체목표미완. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (online solver only / utmm square-1 growth_ervs):** held-out 23.315265dB, 80.614/80.714초, 13296 Adam; 전체시간 계약 PASS. 공통100ms여유·중간지도계측 seed0이며 전체목표미완. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (online solver only / aria aria1253 growth_ervs):** held-out 27.549683dB, 97.551/97.650초, 11927 Adam; 전체시간 계약 PASS. 공통100ms여유·중간지도계측 seed0이며 전체목표미완. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (online solver only / rpng table_06 growth_ervs):** held-out 25.001349dB, 138.268/138.367초, 5475 Adam; 전체시간 계약 PASS. 공통100ms여유·중간지도계측 seed0이며 전체목표미완. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (pose 계측 비용 확인·v17 준비):** 동일 warm solve60쌍 pose차이0, 선택적 잔차계측 비용 약0.84–0.87ms. 정책/solver 불변으로 진단계측만 끈 v17 3scene seed0 준비. 품질효과 미검증·전체목표미완. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (correspondence 갱신 진단 완료):** 같은 causal anchor의 cached/fresh 비교9사례에서 RGB재투영 차이 절대0.7%이내·방향불일치. 재계산 채택근거 없음. v16에 남은 선택적 pose잔차 계측 비용 분리가 다음 작업; 전체목표미완. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (causal pose 색채널 진단 완료):** 3scene×3사례 비교 완료. 8/9 RGB재투영 오차 변화<0.4%, RPNG한 사례 약3.3%감소; map품질/pose GT 근거 아님·전처리 미변경. 초기 correspondence 재사용의 anchor갱신 영향이 다음 진단. 전체목표미완. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (v16 완료·pose 입력규약 확인):** v16 3/3 PASS:25.0552/27.5597/23.2430dB, KF 대비 평균+0.0383이나 RPNG−0.1707/Aria−0.0215로 미채택. 실제 encoder 입력검사에서 official tracker와 filler 채널규약 차이 확인(정규화 max차4.305); pose/품질 영향은 미검증. 평가·trace 변경 없이 causal pose 준비 진단이 다음 작업. 실행중 GPU 작업 없음. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (online recent counts / utmm square-1 growth_ervs):** held-out 23.243007dB, 80.614/80.714초, 12596 Adam; 전체시간 계약 PASS. 공통100ms여유·중간지도계측 seed0이며 전체목표미완. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (online recent counts / aria aria1253 growth_ervs):** held-out 27.559728dB, 97.555/97.650초, 11892 Adam; 전체시간 계약 PASS. 공통100ms여유·중간지도계측 seed0이며 전체목표미완. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (online recent counts / rpng table_06 growth_ervs):** held-out 25.055159dB, 138.272/138.367초, 5422 Adam; 전체시간 계약 PASS. 공통100ms여유·중간지도계측 seed0이며 전체목표미완. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (v15 ablation 완료·v16 준비):** v15 ablation6/6 PASS: Growth는 즉시추가보다 평균+2.4396dB, ERVS는 RR보다 -0.0721dB로 미채택. recent_photometric 실제 commit/reset 연결·24검사PASS·source36개. 같은3scene/예산 v16 준비; 전체목표미완. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (v15 Growth/sampling / utmm square-1 immediate_rr):** held-out 21.394431dB, 80.614/80.714초, 전체시간 계약 PASS. 동일 v15 소스·seed0 기여분리; 목표미완. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (v15 Growth/sampling / utmm square-1 growth_rr):** held-out 23.285823dB, 80.615/80.714초, 전체시간 계약 PASS. 동일 v15 소스·seed0 기여분리; 목표미완. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (Growth 근거·최근 선택 횟수 후보):** Growth 비교 RPNG+2.9804dB/Aria+2.4470dB vs즉시추가 확인. 과거영상 재선택을 위한 recent-count 순수 helper 준비(현재pool N회 history, 전체영상pool 유지), CPU5검사PASS. 실제mapper 미적용·품질이득 미검증; 잠긴 v15 ablation 완료 뒤 연결 예정. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (v15 Growth/sampling / aria aria1253 immediate_rr):** held-out 25.091564dB, 97.562/97.650초, 전체시간 계약 PASS. 동일 v15 소스·seed0 기여분리; 목표미완. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (v15 Growth/sampling / aria aria1253 growth_rr):** held-out 27.538596dB, 97.554/97.650초, 전체시간 계약 PASS. 동일 v15 소스·seed0 기여분리; 목표미완. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (v15 Growth/sampling / rpng table_06 immediate_rr):** held-out 22.041612dB, 138.271/138.367초, 전체시간 계약 PASS. 동일 v15 소스·seed0 기여분리; 목표미완. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (v15 실제 선택 이력):** 실제 완료된 RGB 선택 기록에서 후보의 후반 초반영상 선택 비중2.5/13.4/12.4%(KF18.0/29.2/32.4%) 확인. RPNG Growth+RR25.0220은 ERVS+0.0336이나 KF−0.2039. ERVS의 초반품질−0.588/후반+0.338 vsRR로 배분 tradeoff 관찰, 원인 확정·채택 아님. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (v15 Growth/sampling / rpng table_06 growth_rr):** held-out 25.021991dB, 138.269/138.367초, 전체시간 계약 PASS. 동일 v15 소스·seed0 기여분리; 목표미완. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (v15 전체 비교 완료):** v15 9실행 완료: 전체시간·zero-tail·held-out 분리 9/9 PASS. 후보 평균 운영대비+1.3023dB/KF대비−0.0377dB로 미채택. 같은 소스로 Growth+RR/즉시추가+RR의 3scene ablation6실행 시작 준비, source29개 보존. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (v15 과거 영역 품질 진단):** v15 후보−KF 평균 차이 RPNG−0.2375/Aria−0.1876/UTMM+0.3121dB. 세 장면 모두 가장 이른 평가영상 1/4 구간은 하락(−0.681/−1.613/−1.148); 후반은 개선. 최종지도 진단이며 원인·수렴곡선 증거는 아님. Growth/RR/ERVS 비교로 확인 예정. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (online image residency / utmm square-1 production):** held-out 21.382108dB, 80.620/80.714초, 7875 Adam; 전체시간 계약 PASS. 공통100ms여유·중간지도계측 seed0이며 전체목표미완. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (online image residency / utmm square-1 kf_only):** held-out 22.935859dB, 80.614/80.714초, 19175 Adam; 전체시간 계약 PASS. 공통100ms여유·중간지도계측 seed0이며 전체목표미완. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (online image residency / utmm square-1 growth_ervs):** held-out 23.247956dB, 80.614/80.714초, 12896 Adam; 전체시간 계약 PASS. 공통100ms여유·중간지도계측 seed0이며 전체목표미완. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (online image residency / aria aria1253 production):** held-out 25.894696dB, 97.555/97.650초, 11139 Adam; 전체시간 계약 PASS. 공통100ms여유·중간지도계측 seed0이며 전체목표미완. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (online image residency / aria aria1253 kf_only):** held-out 27.581262dB, 97.554/97.650초, 16827 Adam; 전체시간 계약 PASS. 공통100ms여유·중간지도계측 seed0이며 전체목표미완. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (online image residency / aria aria1253 growth_ervs):** held-out 27.393702dB, 97.552/97.650초, 11860 Adam; 전체시간 계약 PASS. 공통100ms여유·중간지도계측 seed0이며 전체목표미완. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (v15 RPNG paired diagnostic):** v15 RPNG候補24.9884/KF25.2258dB(−0.2375)。KF再転送0・候補RGB学習+501回でも品質改善なし。過去領域再学習の必要性は未検証仮説、全3scene対照とGrowth/ERVS比較を継続。 → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (online image residency / rpng table_06 production):** held-out 24.446187dB, 138.279/138.367초, 3467 Adam; 전체시간 계약 PASS. 공통100ms여유·중간지도계측 seed0이며 전체목표미완. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (online image residency / rpng table_06 kf_only):** held-out 25.225849dB, 138.276/138.367초, 6985 Adam; 전체시간 계약 PASS. 공통100ms여유·중간지도계측 seed0이며 전체목표미완. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (online image residency / rpng table_06 growth_ervs):** held-out 24.988356dB, 138.275/138.367초, 5436 Adam; 전체시간 계약 PASS. 공통100ms여유·중간지도계측 seed0이며 전체목표미완. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (v14완료·GPU영상재사용):** v14 count-scope 완료: 25.1400/27.5496/23.2829dB, 평균KF+0.0812이나 RPNG−0.1113/Aria−0.0765로 미채택. GPU 상주 영상 중복전송 제거: CPU2검사·실제Camera CUDA검사 PASS(픽셀차이0). 동일수정 대조군 포함 v15 9run 준비. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (online photometric counts / utmm square-1 growth_ervs):** held-out 23.282853dB, 80.614/80.714초, 12544 Adam; 전체시간 계약 PASS. 공통100ms여유·중간지도계측 seed0이며 전체목표미완. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (online photometric counts / aria aria1253 growth_ervs):** held-out 27.549634dB, 97.551/97.650초, 12045 Adam; 전체시간 계약 PASS. 공통100ms여유·중간지도계측 seed0이며 전체목표미완. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (online photometric counts / rpng table_06 growth_ervs):** held-out 25.140033dB, 138.270/138.367초, 4928 Adam; 전체시간 계약 PASS. 공통100ms여유·중간지도계측 seed0이며 전체목표미완. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (v13완료·v14 count-scope준비):** 평균25.2560=KF+0.0130이나RPNG−0.1741/Aria−0.1664로미채택. native RGBD횟수와추가RGB횟수분리ERVS가설: growth credit·기하학습은유지,photo-only counter선택만변경. 14CPU검사PASS/source23개,3scene공통v14예정. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (online sparse pose refresh / utmm square-1 growth_ervs):** held-out 23.231007dB, 80.614/80.714초, 12603 Adam; 전체시간 계약 PASS. 공통100ms여유·중간지도계측 seed0이며 전체목표미완. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (online sparse pose refresh / aria aria1253 growth_ervs):** held-out 27.459756dB, 97.553/97.650초, 11842 Adam; 전체시간 계약 PASS. 공통100ms여유·중간지도계측 seed0이며 전체목표미완. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (v13 RPNG실측):** 동일계약에서pose refresh3.473→0.479초, 필요한KF560개만변환(기존경로31466개). RGB3015→3492회,25.0773dB(+0.0863 vs계측baseline/−0.1741 vsKF),전체시간PASS. 비용절감확인·품질목표미완,Aria/UTMM계속. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (online sparse pose refresh / rpng table_06 growth_ervs):** held-out 25.077266dB, 138.273/138.367초, 5316 Adam; 전체시간 계약 PASS. 공통100ms여유·중간지도계측 seed0이며 전체목표미완. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (v12완료·sparse pose-refresh실장):** 3run시간PASS, 잔차중앙0.804/0.962/0.774px는실제pose오차아님. 모든KF변환하던중복제거: 필요한anchor만변환, CUDA5case pose차이0·100KF합성17.86→0.64ms. 실제backend연결4case도0; v13동일조건3scene검증준비/source21개. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (online pose-fit audit / utmm square-1 growth_ervs):** held-out 23.308588dB, 80.614/80.714초, 12535 Adam; 전체시간 계약 PASS. 공통100ms여유·중간지도계측 seed0이며 전체목표미완. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (online pose-fit audit / aria aria1253 growth_ervs):** held-out 26.775464dB, 97.551/97.650초, 11160 Adam; 전체시간 계약 PASS. 공통100ms여유·중간지도계측 seed0이며 전체목표미완. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (online pose-fit audit / rpng table_06 growth_ervs):** held-out 24.990947dB, 138.270/138.367초, 4847 Adam; 전체시간 계약 PASS. 공통100ms여유·중간지도계측 seed0이며 전체목표미완. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (v11완료·v12 pose-fit준비):** 평균ERVS25.1519/RR25.1716<KF25.2430dB, RPNG·Aria손실로둘다미채택. 6run시간PASS. 현재anchor 대응점잔차wrapper CUDA검사PASS/정책변경없음; 계측비용포함v12 3scene 준비/source19개. 4native자동lock완료. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (online batched sampling / utmm square-1 growth_rr):** held-out 23.400459dB, 80.614/80.714초, 12968 Adam; 전체시간 계약 PASS. 공통100ms여유·중간지도계측 seed0이며 전체목표미완. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (v11 2scene쌍·pose잔차계측준비):** RPNG ERVS25.0092/RR25.0475, Aria27.2445/27.0669dB, 4run시간PASS지만둘다KF미달. UTMM계속. 현재anchor/대응점 fit계측4CPU검사PASS(실제mapper미연결). 실제simple-knn추가확인·4native보존. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (online batched sampling / utmm square-1 growth_ervs):** held-out 23.202066dB, 80.614/80.714초, 12009 Adam; 전체시간 계약 PASS. 공통100ms여유·중간지도계측 seed0이며 전체목표미완. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (online batched sampling / aria aria1253 growth_rr):** held-out 27.066925dB, 97.554/97.650초, 10724 Adam; 전체시간 계약 PASS. 공통100ms여유·중간지도계측 seed0이며 전체목표미완. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (online batched sampling / aria aria1253 growth_ervs):** held-out 27.244456dB, 97.584/97.650초, 11274 Adam; 전체시간 계약 PASS. 공통100ms여유·중간지도계측 seed0이며 전체목표미완. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (online batched sampling / rpng table_06 growth_rr):** held-out 25.047526dB, 138.269/138.367초, 4903 Adam; 전체시간 계약 PASS. 공통100ms여유·중간지도계측 seed0이며 전체목표미완. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (online batched sampling / rpng table_06 growth_ervs):** held-out 25.009189dB, 138.275/138.367초, 5070 Adam; 전체시간 계약 PASS. 공통100ms여유·중간지도계측 seed0이며 전체목표미완. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (BA묶음검사·sampling ablation준비):** 합성4scale에서6×2와1×12 pose차이0, 약2.07→1.55ms/pose; 실제wrapper도current anchor/depth보존PASS. warm호출만묶음처리, 운영checkout clean. v11 ERVS/RR 3scene 공통비용비교/source16개보존, 실제품질이득은미검증. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (v10 9run완료·미채택):** 후보평균25.0365dB, 운영+1.1453/KF−0.2064. RPNG−0.2634·Aria−0.6920·UTMM+0.3360 vsKF. 9run 전체시간PASS; UTMM입력경계guard 실제1회작동. 운영동시tracking통합/최종반복검증은미완. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (online setup clock / utmm square-1 production):** held-out 21.359501dB, 80.615/80.714초, 7737 Adam; 전체시간 계약 PASS. 공통100ms여유·중간지도계측 seed0이며 전체목표미완. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (online setup clock / utmm square-1 kf_only):** held-out 22.851490dB, 80.614/80.714초, 18106 Adam; 전체시간 계약 PASS. 공통100ms여유·중간지도계측 seed0이며 전체목표미완. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (online setup clock / utmm square-1 growth_ervs):** held-out 23.187510dB, 80.614/80.714초, 12810 Adam; 전체시간 계약 PASS. 공통100ms여유·중간지도계측 seed0이며 전체목표미완. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (online setup clock / aria aria1253 production):** held-out 25.866480dB, 97.555/97.650초, 10994 Adam; 전체시간 계약 PASS. 공통100ms여유·중간지도계측 seed0이며 전체목표미완. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (online setup clock / aria aria1253 kf_only):** held-out 27.626149dB, 97.552/97.650초, 15800 Adam; 전체시간 계약 PASS. 공통100ms여유·중간지도계측 seed0이며 전체목표미완. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (online setup clock / aria aria1253 growth_ervs):** held-out 26.934161dB, 97.565/97.650초, 11164 Adam; 전체시간 계약 PASS. 공통100ms여유·중간지도계측 seed0이며 전체목표미완. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (online setup clock / rpng table_06 production):** held-out 24.447656dB, 138.280/138.367초, 3332 Adam; 전체시간 계약 PASS. 공통100ms여유·중간지도계측 seed0이며 전체목표미완. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (online setup clock / rpng table_06 kf_only):** held-out 25.251334dB, 138.272/138.367초, 6904 Adam; 전체시간 계약 PASS. 공통100ms여유·중간지도계측 seed0이며 전체목표미완. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (online setup clock / rpng table_06 growth_ervs):** held-out 24.987951dB, 138.270/138.367초, 4987 Adam; 전체시간 계약 PASS. 공통100ms여유·중간지도계측 seed0이며 전체목표미완. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (online entropy scale / utmm square-1 growth_ervs):** held-out 22.929621dB, 80.756/80.714초, 12654 Adam; 전체시간 계약 FAIL. 공통100ms여유·중간지도계측 seed0이며 전체목표미완. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (online entropy scale / aria aria1253 growth_ervs):** held-out 27.005081dB, 97.551/97.650초, 11122 Adam; 전체시간 계약 PASS. 공통100ms여유·중간지도계측 seed0이며 전체목표미완. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (online entropy scale / rpng table_06 growth_ervs):** held-out 25.009712dB, 138.273/138.367초, 4878 Adam; 전체시간 계약 PASS. 공통100ms여유·중간지도계측 seed0이며 전체목표미완. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (v6 stream quality):** utmm/square-1/kf_only: 20.18s:8.8651dB, 40.36s:14.1811dB, 60.54s:19.6820dB, 80.68s:22.4052dB. Fixed held-out cohort 324; common evaluation coordinates; post-run rendering only. Alignment residuals remain unaccepted; no exact first-attainment claim. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (v6 stream quality):** utmm/square-1/growth_ervs: 20.18s:8.8491dB, 40.39s:14.2707dB, 60.54s:19.9868dB, 80.65s:23.1754dB. Fixed held-out cohort 324; common evaluation coordinates; post-run rendering only. Alignment residuals remain unaccepted; no exact first-attainment claim. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (v6 stream quality):** aria/aria1253/kf_only: 24.43s:11.5658dB, 48.83s:16.2714dB, 73.24s:17.8717dB, 97.55s:27.5219dB. Fixed held-out cohort 262; common evaluation coordinates; post-run rendering only. Alignment residuals remain unaccepted; no exact first-attainment claim. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (v6 stream quality):** aria/aria1253/growth_ervs: 24.53s:11.7732dB, 48.83s:16.5234dB, 73.24s:18.0409dB, 97.56s:26.8482dB. Fixed held-out cohort 262; common evaluation coordinates; post-run rendering only. Alignment residuals remain unaccepted; no exact first-attainment claim. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (v6 stream quality):** rpng/table_06/kf_only: 34.90s:14.3551dB, 69.29s:22.7394dB, 104.35s:23.9699dB, 138.27s:25.2291dB. Fixed held-out cohort 555; common evaluation coordinates; post-run rendering only. Alignment residuals remain unaccepted; no exact first-attainment claim. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (v6 stream quality):** rpng/table_06/growth_ervs: 34.87s:14.3192dB, 69.27s:22.6367dB, 104.37s:23.9627dB, 138.27s:25.0065dB. Fixed held-out cohort 555; common evaluation coordinates; post-run rendering only. Alignment residuals remain unaccepted; no exact first-attainment claim. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (online correspondence reuse / utmm square-1 growth_ervs):** held-out 23.334466dB, 80.620/80.714초, 12683 Adam; 전체시간 계약 PASS. 공통100ms여유·중간지도계측 seed0이며 전체목표미완. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (online correspondence reuse / aria aria1253 growth_ervs):** held-out 27.181781dB, 97.556/97.650초, 11014 Adam; 전체시간 계약 PASS. 공통100ms여유·중간지도계측 seed0이며 전체목표미완. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (online correspondence reuse / rpng table_06 growth_ervs):** held-out 24.842682dB, 138.273/138.367초, 5110 Adam; 전체시간 계약 PASS. 공통100ms여유·중간지도계측 seed0이며 전체목표미완. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (online correspondence reuse / rpng table_06 growth_ervs):** held-out 24.996542dB, 138.273/138.367초, 4410 Adam; 전체시간 계약 PASS. 공통100ms여유·중간지도계측 seed0이며 전체목표미완. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (online deferred / utmm square-1 production):** held-out 21.381898dB, 80.678/80.714초, 7752 Adam; 전체시간 계약 PASS. 공통100ms여유·중간지도계측 seed0이며 전체목표미완. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (online deferred / utmm square-1 kf_only):** held-out 22.405205dB, 80.683/80.714초, 18103 Adam; 전체시간 계약 PASS. 공통100ms여유·중간지도계측 seed0이며 전체목표미완. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (online deferred / utmm square-1 growth_ervs):** held-out 23.175359dB, 80.647/80.714초, 11075 Adam; 전체시간 계약 PASS. 공통100ms여유·중간지도계측 seed0이며 전체목표미완. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (online deferred / aria aria1253 production):** held-out 25.872583dB, 97.554/97.650초, 10953 Adam; 전체시간 계약 PASS. 공통100ms여유·중간지도계측 seed0이며 전체목표미완. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (online deferred Aria대조·반복pose비용):** 새KF27.52186 대비dense26.84819(−0.67368), 복원미달. 동일(uid,anchor쌍) 반복보정은RPNG251회4.807초/Aria493회9.561초; 재사용절약은미측정. Aria75%snapshot정렬잔차7.13cm·3.31°로순수photo수렴해석보류. v6전이뒤대응점재사용단일변경검증예정. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (online deferred / aria aria1253 kf_only):** held-out 27.521864dB, 97.553/97.650초, 16000 Adam; 전체시간 계약 PASS. 공통100ms여유·중간지도계측 seed0이며 전체목표미완. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (online deferred / aria aria1253 growth_ervs):** held-out 26.848187dB, 97.559/97.650초, 9896 Adam; 전체시간 계약 PASS. 공통100ms여유·중간지도계측 seed0이며 전체목표미완. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (online dense RPNG service 진단):** final세대dense70/KF186, 누적학습중앙값9/136; photo1601/2677회dense사용. 현재τ.01의종료시dense확률합0.3596, 대체τ는확률계산만하고실행안함. 최종held-out 4구간중첫구간만+0.028dB, 나머지−0.238/−0.433/−0.246; 수렴곡선과구분. v6공통패널계속. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (online deferred / rpng table_06 production):** held-out 24.456206dB, 138.274/138.367초, 3476 Adam; 전체시간 계약 PASS. 공통100ms여유·중간지도계측 seed0이며 전체목표미완. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (online deferred 새RPNG대조·곡선평가 연결):** 동일계측KF25.22909 대비dense25.00646(−0.22263), 복원미달. 동일held-out cohort·실측시각·좌표잔차를보존하는중간평가기와CPU3test PASS; GPU평가는패널뒤진행. Native11–17뷰합산loss와단일photo의sharedAdam규모차이는후속가설로기록. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (online deferred / rpng table_06 kf_only):** held-out 25.229089dB, 138.275/138.367초, 6711 Adam; 전체시간 계약 PASS. 공통100ms여유·중간지도계측 seed0이며 전체목표미완. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (online deferred RPNG pilot·실제snapshot검증):** 25.00646dB·138.268/138.367초·4501Adam, 전체계약PASS이나이전KF25.227미달. Dense1989후보중65장준비,RGB0.616초. 실제snapshot3개×3시점 PLY재로딩렌더오차0; 좌표계정렬잔차기록·수렴우위미판정. 새3scene공통controls패널시작. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (online deferred / rpng table_06 growth_ervs):** held-out 25.006464dB, 138.268/138.367초, 4501 Adam; 전체시간 계약 PASS. 공통100ms여유·중간지도계측 seed0이며 전체목표미완. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (online dense v6 연결):** v5 UTMM22.36261/22.33186으로lazy단독복원기각. UID metadata→Growth/ERVS선택→RGB/IMU/Camera준비를실제harness에연결, 중간지도observer·RGB비용계측추가. 공통100ms종료여유·1.5x예산으로RPNG v6 pilot시작. 새controls도동일계측필요, 목표미달. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (online pose 준비 / v5_depth_lazy utmm square-1):** held-out 22.331859dB, 80.716/80.714초, 8691 Adam; 전체시간 포함 계약 FAIL. seed0 진단이며 최종 목표 판정은 미완. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (online dense 입력준비 점검):** Growth 전에 모든dense RGB를decode·왜곡보정·Camera생성하는경로확인. 선택된admitted영상만준비하는metadata inventory와CPU4test PASS, 실험미연결. RPNG 미계측잔여시간약48초는decode외대기포함이라원인단정안함. Aria lazy26.79147이나KF미달·10.49ms예산초과실패기록. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (online pose 준비 / v5_depth utmm square-1):** held-out 22.362610dB, 80.722/80.714초, 8353 Adam; 전체시간 포함 계약 FAIL. seed0 진단이며 최종 목표 판정은 미완. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (online pose 준비 / v5_depth_lazy aria aria1253):** held-out 26.791474dB, 97.660/97.650초, 9793 Adam; 전체시간 포함 계약 FAIL. seed0 진단이며 최종 목표 판정은 미완. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (online pose 준비 / v5_depth aria aria1253):** held-out 26.704641dB, 97.631/97.650초, 10142 Adam; 전체시간 포함 계약 PASS. seed0 진단이며 최종 목표 판정은 미완. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (online dense v5 RPNG·수렴측정 준비):** lazy 갱신30,132→73회·packet drop74→60이나 PSNR24.57371→24.48664(−0.08708), 품질개선미달. 독립 중간지도 저장·좌표계정렬·PLY export와 CPU8test PASS; v5에는미연결, 실제수렴곡선은미검증. Aria/UTMM paired실행계속. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (online pose 준비 / v5_depth_lazy rpng table_06):** held-out 24.486636dB, 138.351/138.367초, 3088 Adam; 전체시간 포함 계약 PASS. seed0 진단이며 최종 목표 판정은 미완. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (online pose 준비 / v5_depth rpng table_06):** held-out 24.573715dB, 138.351/138.367초, 3100 Adam; 전체시간 포함 계약 PASS. seed0 진단이며 최종 목표 판정은 미완. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (online dense v4 종료·v5 준비):** UTMM dense22.59241은KF22.48108보다+0.11133이나 전체시간18.90ms 초과, Aria/RPNG는KF보다낮아미달. 실제 보간+IMU 함수의 eager/lazy pose4조건 완전일치·갱신12→4, CPU7test PASS. depth-aware cache를양쪽에반영한v5 paired3scene 실행 준비; 총mapping시간검증추가. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (online dense goal / utmm square-1 growth_ervs):** held-out 22.592412dB, 80.733/80.714초, 8960 Adam/16887 renders, 실행 계약 PASS. 공통 κ64 seed0 전이 실험, 전체 목표 판정은 대조군·3seed·수렴곡선 확인 후. [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (online dense goal / utmm square-1 kf_only):** held-out 22.481081dB, 80.706/80.714초, 17925 Adam/25915 renders, 실행 계약 PASS. 공통 κ64 seed0 전이 실험, 전체 목표 판정은 대조군·3seed·수렴곡선 확인 후. [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (online dense RPNG 원인 점검):** dense24.80775dB는 운영24.40053보다 높지만 KF-only25.22700보다 낮음. 신경망 pose2.78초 외에49개 admitted 대비31,054회 eager dense pose 갱신 확인. 선택 직전 갱신 adapter와 CPU3test PASS, online 미검증. UTMM production 전체시간12.39ms 초과는 Adam deadline PASS와 구분해 기록. → [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (online dense goal / utmm square-1 production):** held-out 21.092689dB, 80.727/80.714초, 7658 Adam/15569 renders, 실행 계약 PASS. 공통 κ64 seed0 전이 실험, 전체 목표 판정은 대조군·3seed·수렴곡선 확인 후. [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (online dense goal / rpng table_06 growth_ervs):** held-out 24.807749dB, 138.351/138.367초, 3172 Adam/25224 renders, 실행 계약 PASS. 공통 κ64 seed0 전이 실험, 전체 목표 판정은 대조군·3seed·수렴곡선 확인 후. [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (online dense goal / rpng table_06 kf_only):** held-out 25.226998dB, 138.351/138.367초, 6695 Adam/32757 renders, 실행 계약 PASS. 공통 κ64 seed0 전이 실험, 전체 목표 판정은 대조군·3seed·수렴곡선 확인 후. [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (online dense goal / rpng table_06 production):** held-out 24.400529dB, 138.361/138.367초, 3373 Adam/25770 renders, 실행 계약 PASS. 공통 κ64 seed0 전이 실험, 전체 목표 판정은 대조군·3seed·수렴곡선 확인 후. [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (online dense goal / κ64 Aria 결과·전이 시작):** κ64 held-out26.882017dB로κ16 coverage26.949130보다추가개선없고KF-only27.620639미달.161dense허용/9532photo, pose688회13.846초,97.65초내·held-out·zero-tail·double-eval PASS. 같은κ64정책의RPNGtable_06/UTMMsquare-1 production·KF-only·growth_ERVS 전이패널 시작. 목표 active,3seed/수렴곡선 미완. [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (online dense goal / timed production 대조):** Aria production25.810882dB,1.5x97.65초·held-out·zero-tail·double-eval PASS. V3 growth+ERVS26.949130은production대비+1.1382이나 새KF-only27.620639대비−0.6715로목표미달. 공통κ64 실험으로 pose준비비용과 반복학습량 균형을 검증하며3scene/3seed/수렴곡선은남아있음. [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (online dense goal / v3 coverage 수정):** Aria26.949130dB, v2대비+0.5297이나 새KF-only대비−0.6715. Dense439허용, 후반UID800이후144장(이전0)으로 coverage 회복. 97.65초내·held-out·zero-tail·double-eval PASS. 품질목표는미달; production대조 실행 후 같은정책의 공통κ64로 pose비용/반복학습 균형 검증 예정. [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (online dense goal / v2 RR 대조·admission 수정):** Aria growth+RR25.831409dB, ERVS26.419423(+0.5880)이나 둘 다 KF-only27.620639 미달. Oldest-first admission이 후반dense343장을 전부 배제한 결함 확인. V3는 현재 도착 후보를 일괄 등록하고 temporal-maximin으로 허용;10CPU검증 PASS, v2소스 보존. 같은시간 Aria v3/production 비교 진행, 목표 active. [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (online dense goal / growth+ERVS pilot 실패):** Aria1.5x97.65s에서26.419423dB, 새KF-only27.620639보다−1.201217. Native827+photo7157=Adam7984; dense497허용/455학습, pose676회14.689초. 공통count·인과성·held-out·zero-tail·double-eval PASS이나 품질실패. Growth+RR/production 대조로 원인분리 진행; 목표 active. [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (online dense goal / 새 KF-only clocked pilot):** Aria held-out27.620639dB, 97.65초 예산 내97.6368초. native830+공통RGB14682=실제Adam15512, render27858. 공통count/실제optimizer 일치, held-out유입0·zero-tail·deadline후업데이트0·독립double-eval PASS. 새 구조 대조군 결과이며 목표 미달; growth+ERVS 같은 조건 pilot 시작. [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (active goal / online dense 구조 구현):** 별도 research/online-view-training worktree에서 causal training pool·완료 RGB step 기반 Growth·논문 ERVS·native/photo 공통count 구현, CPU8검증 PASS. Full-Gaussian 공통RGB optimizer와 finite1.5x 하네스 연결. v1은 legacy profile 검증에서 매핑 전실패, v2는 geometry설정 유지+KF-only dense입력제외로 수정하여 Aria pilot 실행. 성능/3scene/3seed/수렴곡선 목표는 아직 미완료. [카드](campaigns/06_gain_attribution/online_dense_training/README.md)

- **2026-09-25 (visual pose 교차장면 검증 완료):** 신규3장면 fixed-map5k에서 visual−KF는 table_06−0.0578/square-1+0.2838/ego-centric-1+0.2955dB; visual−원본dense는 모두 양수. Online pose 추가효과는 각각+0.05088/+0.02370/+0.01393dB로 작음. 동일 work/선택·causal·held-out·zero-tail·double-eval PASS, 추가 pose연산 포함 총시간동일/strict 검증 아님. UTMM refresh양수 assertion 실패는 별도 root 재실행으로 해결. 다음 방향은 pose준비+공통 photometric pool/service/count 연결, 3-family 사전고정 ablation이며 아직 미구현. Production 유지. [카드](campaigns/06_gain_attribution/visual_pose_transfer/README.md)

- **2026-09-25 (visual pose 타 장면 / square-1 online):** control21.33320→visual21.35691dB(+0.02370). 동일9,345render/757Adam·dense/native 선택·causal·held-out·zero-tail·double-eval PASS. 실제IMU refresh호출0 확인; visual70회1.860초 추가, mapping40.603→42.141초. 고정지도 dense 우위와 달리 online 추가효과 작음. 마지막 ego-centric-1 진행. [카드](campaigns/06_gain_attribution/visual_pose_transfer/README.md)

- **2026-09-25 (visual pose UTMM online / harness 실패):** square-1 대조군 매핑 종료 후 refreshed_views>0 사후검증 실패. 모든 장면에서 PGBA dense refresh가 발생해야 한다는 가정 오류; 품질 결과로 미판정. 실패 산출물 보존. 별도 continuation runner/root에서 refresh 미발생을 허용하고 실행 여부 기록, causal/held-out/work 검증은 유지하여 동일 recipe로 UTMM 재실행. [카드](campaigns/06_gain_attribution/visual_pose_transfer/README.md)

- **2026-09-25 (visual pose 타 장면 / table_06 online):** repair-only24.44525→visual24.49613dB(+0.05088). 동일34,437render/2,714Adam·dense/native 선택순서·held-out·causal·zero-tail·double-eval PASS. Pose420회9.779초 추가, mapping143.223→155.765초(+8.76%). 고정지도+1.214dB 회복과 달리 online 이득은 작으며 총시간동일/strict 검증은 아님. [카드](campaigns/06_gain_attribution/visual_pose_transfer/README.md)

- **2026-09-25 (visual pose 타 장면 / 고정지도 3-scene 완료):** ego-centric-1 KF-only21.8008/원본dense21.8361/visual22.0963dB, KF대비+0.2955. 신규3장면에서 pose보정은 원본dense 대비3/3개선, KF-only대비2/3개선(table_06−0.0578/square-1+0.2838/ego-centric-1+0.2955). 통제·held-out·saved reload PASS. EOS후5k+추가pose계산 진단이며 online pair 진행, production 유지. [카드](campaigns/06_gain_attribution/visual_pose_transfer/README.md)

- **2026-09-25 (visual pose 타 장면 / UTMM square-1 고정지도):** 5k RGB 학습 KF-only23.3274, 원본 dense23.0744, visual dense23.6112dB. 원본 대비+0.5368, KF-only대비+0.2838로 Aria의 dense 이득이 다른 공개 장면에서도 재현. Pose-only·동일 map/Adam/순서·held-out324장·fixed topology·saved reload PASS. 71뷰 pose보정2.024초 추가, EOS 후진단이며 online 판정 별도. [카드](campaigns/06_gain_attribution/visual_pose_transfer/README.md)

- **2026-09-25 (visual pose 타 장면 / RPNG table_06 고정지도):** 5k RGB 학습에서 KF-only25.8155, 원본 dense24.5434, visual dense25.7577dB. Pose 보정+1.2143이나 KF-only보다−0.0578로 우위는 미재현. 같은 snapshot/Adam·mixed순서·held-out555장·fixed topology·saved reload PASS; 244뷰 pose보정5.845초 추가, EOS 후진단. UTMM 두 장면 및 online pair 진행. [카드](campaigns/06_gain_attribution/visual_pose_transfer/README.md)

- **2026-09-25 (hypothesis1 판정 / pose 조건의 중요성 지지):** 같은 Aria 지도에서5000회 mixed 학습은 원본pose27.7515, IMU refresh-only27.9764, visual pose28.5812dB. Visual은 repair-only보다+0.6048, KF-only28.2619보다+0.3193으로 dense 이득을 고정지도에서 복원했다. Gaussian/Adam·KF pose·영상순서·loss 고정. 추가 pose연산/EOS후학습 포함이며 온라인대조는Aria−0.0159/RPNG+0.1162라 strict 복원은미완. 운영코드유지. [카드](campaigns/06_gain_attribution/causal_visual_dense_pose/README.md)

- **2026-09-25 (visual pose 고정지도5k / dense 이득 조건부 복원):** 동일 map·Adam·영상순서에서 dense pose만 visual6회 보정한 mixed가27.7515→28.5812dB(+0.8297), KF-only28.2619보다+0.3193dB 높다. 1000회에서는격차88.93% 회복,5000회에서는역전. Pose 조건이 중요한 원인이라는 근거를 확보했지만 EOS 후추가학습 진단이며 온라인은 Aria−0.0159/RPNG+0.1162로일관복원아님. IMU refresh-only5k control추가사전선언. [카드](campaigns/06_gain_attribution/causal_visual_dense_pose/README.md)

- **2026-09-25 (visual pose 고정지도 인과 진단):** Gaussian·Adam·KF pose·영상순서 고정, dense pose만 DROID visual6회 보정한1000-step mixed는26.3118→26.7288dB(+0.4170). KF-only26.7807와의 격차88.93% 회복하나0.0519dB 남음. 추가 pose 계산을 포함한 EOS 후 진단이며 strict 결과 아님. Pose 불일치가 이 고정지도 손실의 중요한 요인이라는 근거; 동일 corrected snapshot5000-step 확장 사전 선언. [카드](campaigns/06_gain_attribution/causal_visual_dense_pose/README.md)

- **2026-09-25 (causal visual dense pose RPNG transfer):** 같은 영상기반 dense pose 보정은 table_01에서 25.3664→25.4826dB(+0.1162). 38,302 mapping render/3,030 Adam·admission·dense 선택·zero-tail·held-out·double-eval PASS. 추가481회 pose 보정(2886 graph update),10.513초. Aria−0.0159와 달라 보편적 복원은 아니며 추가 총연산비 포함 해석 필요. [카드](campaigns/06_gain_attribution/causal_visual_dense_pose/README.md)

- **2026-09-25 (causal visual dense pose Aria pilot):** 과거 filler의 DROID feature+6회 motion-only 보정을 현재 non-held-out KF 두 장에만 적용했다. 122회/100 dense뷰 보정, anchor pose/depth 불변·same map render/Adam·admission/선택·zero-tail·double-eval PASS. PSNR 25.8400→25.8240dB(−0.0159), 보정 연산3.064초 추가. 영상기반 pose 보정만으로 online 이득은 미복원; RPNG 전이와 고정지도 pose-only 분리 진단 진행. 운영 코드 미변경. [카드](campaigns/06_gain_attribution/causal_visual_dense_pose/README.md)

- **2026-09-25 (dense 과거 조건 source audit / 해석 정정):** Exp66 +3dB는 RGB-only 약23–24k step·Adam reset·종료 후 visual trajectory filler(역사 commit b05e981d에서도 motion-only 6회)·D12 784뷰 조건이다. 현재 진단은 causal 보간+IMU pose·Adam restore·KF91+dense102·최대5k여서 학습량/pose/집합이 일치하지 않는다. 과거124뷰 aggregate PSNR과 현재262뷰 mean PSNR도 다르다. Depth/normal 영향은 아직 열려 있고, 5k 음성 결과로 일반적인 budget 가설까지 기각하지 않는다. 새 GPU 실험/운영 변경 없음. [카드](campaigns/06_gain_attribution/dense_gain_recovery/README.md)

- **2026-09-25 (dense gain recovery 5k 고정지도 진단 / 복원 미달):** 같은 Aria checkpoint·Adam·실제 causal training pose에서 5000회 RGB 학습한 KF-only full은 28.2619dB, KF+dense full은 27.7515dB(−0.5104); SH는26.4171/26.4320. 1000회와 마찬가지로 dense 우위가 없어 단순 반복 횟수 확대도 복원책으로 미채택. 동일 snapshot·scope별 선택순서·held-out·고정 topology·saved/reload 검증 PASS. EOS 뒤5000회 진단이므로 strict27 달성 근거가 아니며 production 미변경. [카드](campaigns/06_gain_attribution/dense_gain_recovery/README.md)

- **2026-09-25 (dense refresh repair RPNG transfer):** 같은 full-scope 조건의 pose 갱신 오류 수정은 table_01에서 25.3779→25.3664dB(−0.0115). 38,302 render/3,030 Adam·admission·dense 선택·held-out·zero-tail·double-eval PASS. Aria +0.0277과 함께 보면 correctness는 개선하지만 dense PSNR 회복 원인으로는 부족하다. 운영 코드 반영 없이 campaign adapter로 보존. [카드](campaigns/06_gain_attribution/dense_gain_recovery/README.md)

- **2026-09-25 (dense refresh repair Aria pilot):** 현재 mapper KF bracket으로 IMU residual을 재계산하고 bracket 밖 pose의 보정 누적을 차단했다. 기존 함수 결함 재현을 포함한 CPU 6개 테스트 PASS. 동일 full-scope control 25.8123→25.8400dB(+0.0277), work·admission·dense 선택·held-out·zero-tail·double-eval PASS. 오류 수정은 작동하나 dense 이득 복원 근거로는 부족하며 production 미반영. [카드](campaigns/06_gain_attribution/dense_gain_recovery/README.md)

- **2026-09-25 (dense scope RPNG transfer / scope-only 복원 기각):** native RGB-D를 보존한 table_01에서 dense SH→full은 25.5747→25.3779dB(−0.1968). Aria +0.0923과 반대여서 공통 개선으로 채택하지 않는다. 동일 render/Adam·admission·선택·zero-tail·held-out·double-eval PASS. IMU pose refresh 오류 수정은 별도로 비교한다. [카드](campaigns/06_gain_attribution/dense_gain_recovery/README.md)

- **2026-09-25 dense pose 고정지도 진단:** GT/eval pose 없이 RGB pose-only 64회×102뷰 후 같은1000회 학습으로 mixed-full 26.3118→26.5717dB. 추가6528 pose render/Adam 비용 포함, KF-only full26.7807 미달. Pose 영향 일부 확인, dense 이득 복원은 미달. [카드](campaigns/06_gain_attribution/dense_gain_recovery/README.md)

- **2026-09-25 dense scope Aria online pair:** native RGB-D 유지, dense SH→full만 변경 시 25.7200→25.8123dB(+0.0923). 같은 render/Adam/admission/선택순서·zero-tail·double-eval PASS. 단일 seed 소폭 이득, strict-live 근거 아님. [카드](campaigns/06_gain_attribution/dense_gain_recovery/README.md)

- **2026-09-25 dense gain recovery 고정지도 진단:** 동일 Aria map/Adam에서 1000회 RGB 학습 시 KF-only SH/full=26.2213/26.7807, KF+dense SH/full=26.2196/26.3118dB. SH 제한 해제만으로 dense 이득은 복원되지 않음. post-EOS 진단이며 strict 결과 아님. [카드](campaigns/06_gain_attribution/dense_gain_recovery/README.md)

> 이 파일은 재현성을 위한 **시간순 원장**이라 길이가 의도적으로 유지된다.
> 일반 탐색은 [research campaign hub](README.md)에서 시작한다. 새 작업은
> `expNNN` 번호보다 `BENCH/TOPO/DENSE/ATTR` campaign 이름을 먼저 사용한다.

- **2026-09-24 exp124 role-aware dense photometric service 3-family PASS (active·quality-safe, gain 미입증):** 마지막 native iteration을 equal-cardinality dense appearance quantum으로 재배치하고 최소 1회 RGB--D geometry iteration, exact render/Adam, zero-tail을 보존했다. 기존 aux-KF appearance slot도 dense repeat로 옮겨 total dense share가 UTMM/RPNG/Aria **11.50/11.03/11.58%**가 됐고 normalized ERCB와 RR trace가 41/115/57행 달랐다. PSNR은 backbone 대비 **−0.219/−0.113/−0.107dB(평균 −0.146)**, normalized−RR 평균 +0.0075dB라 method activation과 품질 보존까지만 채택하고 ERCB quality gain·17-scene·strict-live claim은 보류한다. v1 batch duplicate를 발견해 폐기하고 without-replacement v3에서 128 test와 모든 fairness gate를 통과했다. [실험 카드](exp124_role_aware_dense_service.md)
- **2026-09-24 exp123 dense geometry-mass isolation PASS / candidate rejected:** RPNG fresh control/stats-off/stats-off+geometry-mass는 모두 38,302 render·3,030 Adam exact. PSNR 25.561123/25.434710/25.412915dB. Candidate는 1,610/1,610 dense replacement에서 남은 RGB-D depth/normal만 평균 1.062575배로 보정했지만 **−0.021795dB 추가 악화**(gap recovery −17.24%). Aggregate geometry weight 부족이 아니라 교체된 historical KF의 view-specific RGB-D coverage 손실이 원인. Aggressive KF→dense replacement는 폐기하고 scene 확장·ratio tuning 금지. [실험 카드](exp123_dense_geometry_mass_isolation.md)
- **2026-09-24 exp122 dense-global topology-stat isolation PASS:** RPNG fresh control/stats-on/stats-off 모두 38,302 render·3,030 Adam exact 및 causal/eval gate PASS. PSNR은 25.582787/25.410318/25.424374dB. Dense native topology stats를 빼자 churn은 114,266→112,144(control112,062)로 복원됐지만 품질은 **+0.014056dB**만 회복(손실의 8.15%). 따라서 one-slot RPNG 손실의 주원인은 topology stat이 아니라 historical RGB-D KF를 RGB-only dense로 교체한 것. v1 verifier의 all-commit 기대는 final-v7 frontier-only stat 규칙을 무시한 오류로, immutable ledger 210/210을 쓰는 artifact-only v2에서 정정. [실험 카드](exp122_dense_global_topology_stats_isolation.md)
- **2026-09-24 exp121 topology cost/source-code gate PASS:** frozen unified arm을 CUDA-sync section profile. UTMM/RPNG densify-prune는 총 **69.575/58.666ms**, mapping wall의 **0.171/0.034%**, max spike55.108/40.334ms로 평균 throughput 병목이 아님. 반면 regular churn은 89,296/114,143행이라 품질·해석성 문제는 유지. Downloaded LPM/TileGS/Taming/RTG 실제 코드를 대조해 LPM error-zone+Taming bounded sampling만 strict RGB fixed-work에 채택하고 TileGS CUDA/RTG RGB-D lifecycle/hard prune는 보류. [실험 카드](exp121_topology_cost_profile.md)
- **2026-09-24 exp120 frozen unified dense transfer 2/2 PASS (active·quality-safe, gain 미입증):** Exp119 one-slot/LPM-mass/`gamma=16`을 무튜닝으로 RPNG table_01·Aria1253에 전이. dense share는 1.40→5.61%, 1.48→6.37%이고 1,610/665 replacement 전부 commit; 각 arm은 38,302/13,620 render·3,030/1,055 Adam exact와 모든 causal/eval gate PASS. 품질은 control 대비 **−0.186122/+0.054396dB**. UTMM 포함 3-family 평균은 −0.047930dB, normalized−RR은 +0.000805dB라 ERCB quality gain은 미입증. dense가 native topology stats까지 바꾸는 active path는 확보했지만 현재 rule의 17-scene promotion은 보류. [실험 카드](exp120_unified_dense_transfer.md)
- **2026-09-24 exp119 corrected unified dense global slot PASS:** control-equivalent global cardinality를 먼저 고정해 실제 historical render 1개만 unified LPM-mass dense ERCB로 교체. UTMM square-1 dense renders/share **142/1.52%→625/6.69%**, total 9,345 render·757 Adam exact, 483/483 replacement commit·recent-window/cap/lifecycle/causal/eval gate 전부 PASS. normalized는 control −0.012064dB, matching RR보다 **+0.02562dB**, global trace 70행 차이. 품질 gain은 단일장면 noise 수준이라 RPNG/Aria 무튜닝 전이 후 판단. [실험 카드](exp119_unified_dense_global_corrected.md)
- **2026-09-24 exp118 unified dense historical-slot pilot FAIL (render +49):** recent KF window를 유지하고 flexible historical slot 1개를 LPM-mass dense ERCB로 교체하려 했으나, 초반 historical pool<6일 때 dense가 교체가 아니라 추가되어 9,345→**9,394 renders**. Adam757·lifecycle clock은 동일, dense share1.52→6.65%, normalized/RR global trace70행 차이, 품질 −0.033/−0.052dB였으나 fixed-work 비교로 무효. `G=min(6,available_history); dense=min(1,G,...); tracked=G-dense`로 교정한 새 root만 허용. [실패 카드](exp118_unified_dense_global.md)
- **2026-09-24 exp117 frozen LPM mass-prior transfer 2/2 PASS (active·quality preserved, gain 미입증):** Exp116 수식/`gamma=16`을 무튜닝으로 RPNG table_01·Aria1253에 전이. normalized 결합은 dense trace를 각각 **34/9행** 변경하고 38,302/13,620 render·3,030/1,055 Adam·모든 causal/eval gate PASS, control 대비 **−0.010767/+0.031011dB**. UTMM 포함 3-family 평균 +0.0038dB, mass-only RR 대비 normalized 효과 평균 −0.0040dB라 quality gain은 미입증. 17-scene 반복보다 recent-window floor를 유지한 flexible historical-KF render의 unified dense pool 재배분이 다음 causal gate. [실험 카드](exp117_lpm_mass_transfer.md)
- **2026-09-24 exp116 LPM significant-zone mass prior PASS (active·quality-safe, gain 미입증):** Exp115의 희석된 `1+e_i` 대신 official 16×16 patch 한 개 pseudocount를 둔 `q_i=(active_pixels+256)/(HW+256)`, `p_i∝q_i exp[-16n_i/(T+1)]`를 무튜닝 고정. UTMM square-1에서 normalized 결합이 dense trace 3행을 실제 변경하고 9,345 render·757 Adam·causal/eval gate 전부 PASS, 품질은 control 대비 −0.008967dB. mass-only RR은 10행/+0.003089dB. active contribution 경로는 확보했지만 quality gain은 미입증이며 RPNG/Aria 전이 전 전체 panel 금지. [실험 카드](exp116_lpm_mass_prior.md)
- **2026-09-24 exp115 source-backed LPM dense-view utility FAIL (inactive composition):** downloaded LPM error-zone coverage를 transactional base measure `1+e_i`로 normalized ERCB와 결합했다. UTMM square-1 4arm 모두 9,345 render·757 Adam·fairness gate PASS, 품질도 normalized 대비 −0.019673dB로 안전했지만 **dense trace 변화가 0행**이라 method-active gate 실패. utility-only RR은 9행을 바꿨으나 +0.002957dB로 quality gain 없음. multiplier를 PSNR 튜닝하지 않고, 다음에는 significant-zone mass+one-patch pseudocount라는 source-grounded prior를 trace gate부터 검증한다. [실험 카드](exp115_lpm_view_utility.md)
- **2026-09-24 exp114 official-LPM no-op repeat PASS:** UTMM square-1에서 fresh control 두 개로 exact PLY SHA가 CUDA/topology no-op gate가 될 수 없음을 확인했다(control끼리도 hash 상이, GS 120,137/120,235). author commit `7c060267`의 `get_errormap(diff)` probe는 9,345 render·757 Adam·dense trace를 그대로 유지하고 control 평균 대비 **+0.002144dB**, GS 편차 9/허용121, GPU share 0.187%, wall +0.306%. score도 142 call·95 unique로 비퇴화해, 다음 fixed-work dense-view utility 결합을 허용한다. [실험 카드](exp114_lpm_noop_repeat.md)
- **2026-09-24 exp113 official-LPM error-zone probe FAIL (over-strict gate):** 내려받은 LPM 저자 코드의 image-space operator만 already-paid dense render에 이식해 추가 render/Adam/mutation 0, PSNR +0.007276dB, GPU share 0.211%, 비퇴화 signal을 얻었으나 사전 exact PLY SHA gate가 실패했다. 실패는 유지하며, 두 control 반복으로 gate 자체를 검증하는 exp114로 교정했다. [실험 카드](exp113_lpm_error_zone_probe.md)
- **2026-09-24 exp112 active normalized temperature 3-family PASS (quality gain 미입증):** Exp111 immutable causal pool을 production queue로 재생해 PSNR 없이 UTMM square-1에서 repeat trace 차이≥10%·count-CV 감소≥10%를 처음 만족하는 공통 상수 `gamma=16`을 고정했다. `p_i∝exp[-gamma*n_i/(T+1)]` 그대로이며 `T` scaling·scene tuning 없음. UTMM/RPNG/Aria 12arm 모두 render·Adam·admission·event·held-out·double-eval·zero-tail PASS. 실제 trace는 RR과 9/17/10행 달라지고 count CV는 일관되게 감소했으나, gamma16−R4 평균 **−0.013669dB**, gamma16−log1.5 **−0.009751dB**, gamma16−RR **−0.009250dB**라 PSNR causal gain은 미입증. Active ERCB는 품질 안전하지만 단순 count balance만으로 17-scene 확장하지 않는다. [실험 카드](exp112_normalized_temperature.md)
- **2026-09-24 exp111 first-service+dense-repeat 3-family PASS (ERCB gain 미입증):** 기존 aux-KF 1-view slot을 admitted dense repeat로 바꾸되 primary dense만 admission credit을 만들고 신규 view first-service를 강제했다. UTMM square-1/RPNG table01/Aria1253의 9arm 모두 render·Adam·admission·event·held-out·double-eval·zero-tail PASS. Dense/KF service는 70/70→140/0, 267/267→534/0, 100/100→200/0이고 dense share는 약 0.7%→1.4–1.5%, 추가 work 0. Normalized repeat−R4 평균 **+0.015072dB**로 품질 보존. 하지만 normalized−dense-only-RR 평균 +0.009767dB, 실제 trace 차이는 1/2/0행뿐이라 `gamma=log(1.5)` ERCB causal gain은 미입증. Inline verifier의 selector-snapshot/최종-generation counter 오비교는 artifact-only v2 reporter로 정정했고 원본 실패 보고는 보존. [실험 카드](exp111_dense_repeat_ercb.md)
- **2026-09-24 exp110 normalized ERCB/RR/ticket isolation PASS (causal gain 미입증):** UTMM 3장면×3arm에서 normalized+ticket, 같은 causal growing/no-repeat pool의 zero-energy RR+ticket, normalized ticket-off를 비교. 9arm 모두 render·Adam·archive/config/event·admission/opportunity·held-out·double-eval·zero-tail PASS. normalized−RR 평균 **−0.007705dB**, ticket−off 평균 **+0.002896dB**로 noise 수준. Dense와 aux-KF trace는 전 장면 동일했고 dense selected count 최대가 1이라 현재 one-pass service에서는 ERCB가 선택에 개입할 수 없음을 확인. Native historical-KF만 반복 epoch에서 9/16 rows가 달라졌으나 품질 효과 없음. Exp109 품질 보존 결과는 유지하지만 ERCB/ticket causal quality claim은 금지하고, 다음은 first-service floor를 보존한 existing-work repeat allocation으로 제한. [실험 카드](exp110_rr_ticket_ablation.md)
- **2026-09-24 exp109 frozen first-persistence 17-scene panel PASS:** Exp106–108 common config를 freeze해 RPNG8/UTMM7/Aria2 전부 fresh candidate/official-vanilla pair로 재실행. **17/17 승리, scene 평균 +1.286809dB**, dataset 평균 RPNG +1.6165/UTMM +0.5743/Aria +2.4620, fairness/double-eval/zero-tail/R4-floor 전부 PASS. Exact R4 대비 평균 +0.000426dB로 품질 이득을 그대로 복원했으며 Exp94 stretch(+1.253787, 17/17)도 PASS. 총 6,782 bounded clone이 실제 작동했지만 최종 GS 합계는 R4 대비 +0.043%, 추가 render·Adam 0. Inline summary는 모든 pair 완료 뒤 compact JSON field 누락으로 실패했으나 immutable verifier/runtime artifact-only reporter로 복구·교차검증. B-track current composition으로 채택하되 ticket 자체의 R4 대비 quality causality와 strict-live는 아직 미증명. [실험 카드](exp109_first_persistence_panel.md)
- **2026-09-24 exp108 first-persistence Aria transfer PASS:** Exp106/107 common rule을 Aria `aria1253`에 무튜닝 전이. generation2 첫 persistence에서 repeated148/small70/actual clone70, 기존 native densification stats 보존, 추가 render·Adam 0. PSNR **25.755865dB**, Exp94 normalized R4 **−0.019837**, fresh vanilla **+1.776532**; SSIM +0.045087, LPIPS −0.088476. 13,620 physical render exact match·fairness/double-eval/zero-tail PASS. UTMM/RPNG/Aria family gate가 모두 통과해 common config를 17-scene B-track panel용으로 freeze하되 strict-live/티켓 자체의 R4 대비 품질 이득 주장은 아직 금지. [실험 카드](exp108_first_persistence_aria.md)
- **2026-09-24 exp107 first-persistence RPNG transfer PASS:** Exp106 common rule을 RPNG `table_01`에 무튜닝 전이. 최종 generation 첫 persistence에서 repeated532/small396/actual clone396, native densification stats 보존. PSNR **25.584830dB**, Exp94 normalized R4 **+0.003415**, fresh vanilla **+1.645150**. 38,302 render·3,030 Adam·native topology2·opportunity/fairness/double-eval/zero-tail PASS. Final GS는 R4 대비 192개(+0.046%)만 증가. Work-poor UTMM에서 활성화되면서 RPNG 핵심 이득도 유지해 현 preferred topology composition으로 채택하되 strict-live/전체 panel 주장은 아직 금지. [실험 카드](exp107_first_persistence_rpng.md)
- **2026-09-24 exp106 first-persistence local topology PASS (short UTMM):** native topology가 끝난 뒤 dense evidence가 생겨 mutation 0이던 `slow-straight-2`에서 generation당 첫 persistence 시점에 top-1,024 ticket을 1회 쓰고, mid-cycle `xyz_gradient_accum/denom/max_radii2D`를 보존했다. 반복 후보619/small443/actual clone443, 추가 render·Adam 0. PSNR **17.309940dB**, Exp94 R4 **+0.086496**, Exp105 mutation-0보다 +0.063801, fresh vanilla −0.054132. Fairness/double-eval/zero-tail PASS. 패배 해결 주장은 보류하고 RPNG table01에서 기존 +1.6dB 보존을 다음 gate로 둔다. [실험 카드](exp106_first_persistence_ticket.md)
- **2026-09-24 exp105 dense-ticket transfer pilot (2 scenes, scheduler limitation):** Exp104 common rule을 무튜닝으로 UTMM `slow-straight-2`와 Aria `aria1253`에 전이하고 각 scene에서 fresh render-matched vanilla까지 새로 실행했다. UTMM은 ticket/R4 **+0.0227dB**, fresh vanilla −0.0356이나 native topology가 dense evidence보다 먼저 끝나 actual mutation 0. Aria는 1,453 mutation이 활성이고 R4 −0.0520, fresh vanilla **+1.7636dB**. 두 pair fairness/double-eval/zero-tail PASS, −0.5 stop 미발동. 17-scene 확장은 보류하고 mid-cycle native densification stats를 보존하는 generation당 1회 observation-triggered service를 short UTMM에서 먼저 검증한다. [실험 카드](exp105_dense_ticket_transfer_pilot.md)
- **2026-09-24 exp104 active dense/ERCB topology ticket PASS (single-scene):** normalized ERCB dense backward의 top-1,024 `f_dc` rows를 generation-scoped stable ID로 누적하고, 서로 다른 dense UID 2회 이상 반복된 small Gaussian을 Taming 저자 코드의 weighted `multinomial(replacement=False)`로 기존 native topology event에서만 clone했다. Ticket은 장면 상수가 아니라 해당 event regular add와 매칭. 실제 1,706 mutation, 추가 render/Adam 0; 38,302 render·3,030 Adam·모든 fairness gate PASS. PSNR **25.595663dB**, R4 +0.010645, vanilla **+1.631399**. GS +0.41%, wall +1.52%. Dense/ERCB가 실제 topology를 제어하면서 R4 이득을 보존한 첫 조합이나, R4 대비 gain은 noise 수준이라 무튜닝 전이가 필요하다. [실험 카드](exp104_dense_topology_ticket.md)
- **2026-09-24 exp103 generation-scoped dense evidence PASS / exp102 persistence correction:** VIGS map reset이 point ID를 0부터 재사용하므로 Exp102의 bare-ID lifetime 반복 수는 후속 설계에 사용할 수 없음을 발견했다. `(map_generation, point_id)`로 namespace하고 동일 진단을 재실행해 3 generation을 분리했다. 38,302 render·3,030 Adam·opportunity UID·topology2/2·zero-tail 전부 PASS, PSNR **25.579016dB**(R4 −0.006001, vanilla **+1.614753**). final-generation live repeated top-1,024 ID 25,330개, within-generation Jaccard 0.3175로 corrected signal도 충분하다. Exp102 품질/gradient mass는 유효하나 persistence 표는 폐기한다. [실험 카드](exp103_generation_scoped_dense_evidence.md)
- **2026-09-24 exp102 behavior-neutral ERCB dense topology evidence PASS:** normalized R4의 269 fixed dense opportunity에서 이미 계산된 `f_dc` gradient만 읽어 stable point-ID의 local/persistent evidence를 계측했다. 추가 render/Adam/mutation 0, opportunity UID 순서·38,302 render·3,030 Adam·topology2/2·zero-tail 등 isolation 전부 PASS. PSNR **25.577882dB**, Exp95 R4 대비 −0.007136, fresh vanilla 대비 **+1.613619dB**. top 256/1,024/4,096이 gradient mass 14.14/29.84/54.24%, consecutive top-1,024 Jaccard 0.3180이고 반복 top-1,024 live ID가 25,264개라 dense/ERCB evidence를 bounded topology ticket에 사용할 근거를 확보했다. 아직 topology gain 주장은 아니다. [실험 카드](exp102_dense_topology_evidence_probe.md)
- **2026-09-24 exp101 R4-preserving official residual supplement PASS:** 기존 R4 PPM birth/RNG를 그대로 먼저 실행하고 별도 RNG에서 Gaussian-SLAM 공식 low-alpha/positive-depth-residual+radius operator를 1× causal allocation으로 추가. RPNG table01 **25.609319dB**, Exp95 R4 대비 +0.024301, fresh vanilla 대비 **+1.645055dB**, SSIM/LPIPS도 개선; 38,302 render·3,030 Adam·density trace·opportunity·topology2/2·zero-tail 전부 PASS. 다만 286,549 residual birth가 실제 추가되어 GS +52.0%, wall +11.2%, allocated +26.1%, reserved +84.6%, churn +33.8%라 최종안은 아님. Replacement가 아닌 supplement가 안전하다는 composition rule만 채택하고 다음은 dense/ERCB evidence로 service를 ration한다. [실험 카드](exp101_residual_birth_supplement.md)
- **2026-09-24 exp100 capacity-matched official local-birth replacement FAIL:** full-view causal density trace와 R4 per-view target을 그대로 유지하고 official seed mask/radius만 적용해 모든 fixed-work/causality check가 PASS했다. 그러나 351,624 offer/314,590 accept, final GS 276,837(Exp95 417,656 대비 −33.7%), PSNR **23.581536dB(−2.003482)**로 중단선 실패. Residual-only birth는 VIGS global-map/online-depth에서 blanket PPM birth를 대체할 수 없으며 dense 결합은 미진행. [실패 카드](exp100_capacity_matched_local_birth_failed.md)
- **2026-09-24 exp99 corrected official-code local birth FAIL:** Exp98 cap 결합은 해소되어 final topology cap deletion 0/0·event 2/2·fixed-work/causality 전부 PASS했지만, 1,024 fixed ticket가 235 event에서 185,508개(평균 789/event)만 생존시켜 final GS가 417,656→173,415(−58.5%)로 줄었다. PSNR **23.072144**, Exp95 R4 대비 **−2.512874dB**로 −0.5dB gate 발동. 1,024는 저자 설정이 아니며 공식 config는 30k/100k/unlimited다. Masked depth가 online-density Sobel calibration도 바꾼 confound를 확인해 dense 결합 없이 중단. [실패 카드](exp99_gaussian_slam_local_birth_corrected_failed.md)
- **2026-09-24 exp98 official Gaussian-SLAM local birth STOP:** 저자 공식 코드 commit `eaec10d7`의 low-alpha/positive-depth-residual birth와 bounded ticket/radius reject를 포팅했으나, 기존 Aria-derived density curve가 ticket 이전 target으로 KF cap을 정해 final generation topology event에서 1,007/11,958개를 다시 삭제했다. 단일요인 실험이 아니므로 PLY·PSNR 전에 중단했고 partial log만 보존했다. `d00e2263`에서 기본 R4 수치는 유지한 채 cap을 최종 ticket 뒤로 옮겼으며 corrected run은 새 root에서만 수행한다. [실패 카드](exp98_gaussian_slam_local_birth_stopped.md)
- **2026-09-24 exp97 shadow-count filter-prune isolation PASS:** RPNG `table_01`에서 actual filter deletion 0, controller에는 counterfactual post-prune count를 전달해 topology cadence를 control과 2/2로 고정. 38,302 render·3,030 Adam·zero-tail·이중 평가·isolation checks PASS, PSNR **25.680925**로 Exp95 R4 대비 +0.095907, fresh vanilla 대비 **+1.716662dB**. 대신 GS +11.0%, peak allocated +7.1%, reserved +16.5%, map wall +6.1%. [실험 카드](exp97_shadow_filter_prune_isolation.md)
- **2026-09-24 exp96 naive filter-prune isolation STOP:** RPNG `table_01`에서 regular filter deletion만 끄자 control 2회와 달리 frame657에 topology 3회차가 열림. 실제 post-prune Gaussian count가 R4 phase controller의 prune/recovery certificate라서 deletion 제거가 cadence까지 바꾼다는 결합을 확인했다. Confounded PSNR을 만들지 않고 중단했으며 final PLY/평가 없음. [실패 카드](exp96_filter_prune_isolation_stopped.md)
- **2026-09-24 exp95 behavior-neutral topology churn probe:** RPNG `table_01` normalized R4 25.585018 vs fresh vanilla 23.964263 dB, **+1.620754 dB**, exact 38,302-render budget·zero-tail·double-eval·fairness 10/10 PASS. Final mapper generation의 topology 2회가 19,552 add/48,965 remove, 총 **68,517 row churn**을 만들어 event 수와 달리 전역 mutation이 큼을 확인. telemetry는 generation reset 전 lifetime을 아직 보존하지 않으므로 전체 로그 111,650 churn은 진단값으로만 기록. [실험 카드](exp95_topology_churn_probe.md)
- **2026-09-22 Fig.2 checkpoint 표기:** (a)/(b) 왼쪽·방법명 사진 아래로 이동. 3DGS-LM/Turbo-GS figure 확인 후 두 결과에 1,400 iter. 직접 표기, 그래프에1.4k 안내 추가. 글자 크기·데이터 유지, PDF 렌더 검수·현행본 동기화. [기록](ERCB_ablation/fig3_ab_layout_2026-09-22.md)
- **2026-09-22 HumanTeck Fig.2 배치 수정:** (a) 19 dB 아래 축척 압축·물결 표시, (b) frame1420/1400 iter의 VIGS-SLAM·Ours·GT 전체 화면+확대. 검정/파랑, 기존 글자 크기·28개 원본 측정값 유지. PDF 렌더 검수·current/원고 동기화 완료, 신규 실험 없음. [기록](ERCB_ablation/fig3_ab_layout_2026-09-22.md)
- **2026-09-21 HumanTeck Fig.2 통합:** 현행 B곡선·frame1420을 기존 렌더 비교 자리에 설치.555 held-out/Carve off/최초 도달1400↔2400 캡션 및 본문 참조 수정, current와 원고 asset 동기화·정적 검증. 전체 TeX 컴파일 미확인. [기록](ERCB_ablation/fig3_threshold_literature_2026-09-21.md)
- **2026-09-21 Fig.3 B안 선택·current 관리:** baseline-best 그림 문구 삭제·캡션 이관, 끝 PSNR 숫자 미표기. current/ 고정 SVG/PDF/PNG·캡션·provenance와 자동 갱신 코드·로컬 규칙 추가. [기록](ERCB_ablation/fig3_threshold_literature_2026-09-21.md)
- **2026-09-21 Fig.3 수평 괄호 A/B 출력:** A400/B1000 두 안의 논문용 SVG/PDF/PNG와 캡션 작성·PDF 렌더 검수. frame1420·원시28점 유지, 신규 측정 없음. [기록](ERCB_ablation/fig3_threshold_literature_2026-09-21.md)
- **2026-09-21 Fig.3 수평선 문헌 시각 검토:** 5논문 원문 figure 확인. 3DGS-LM의 짧은 비교 괄호 참고, baseline best23.2813@2400 대비 Ours1400 첫 도달 후 재하락·2000 이후 저장점 유지.400-iter 비교 권고와1000-iter 대안 SVG/PNG 제작, 원본 선택본 보존. [카드](ERCB_ablation/fig3_threshold_literature_2026-09-21.md)
- **2026-09-21 Fig.3 frame1420 사용자 선택:** Fig.2와 동일 정사각형 ROI로800/1400/2600 실제 inset 교체, 높이46.13 mm·하단 범례 유지. 원본28점·6장hash 보존 및 PDF 렌더 검수. 신규 학습·GPU 평가 없음. [기록](ERCB_ablation/fig3_table06_compact_2026-09-21.md)
- **2026-09-21 Fig.3 table06 v2:** 상단 문구 제거·하단 가운데 범례, 원시곡선 28점 유지. 비단조적 품질의 baseline-final 수평선 제거·threshold 민감도 진단. 기존48렌더로8후보의 GT 위치·3시점 crop 비교판 제작, frame 재선택 대기. [기록](ERCB_ablation/fig3_table06_compact_2026-09-21.md)
- **2026-09-21 Fig.3 table06 납작한 도판·frame355:** 동일 폭에서 높이 63.42→46.13 mm(−27%), y축 14–25.5 dB, 원본 555-view 곡선 28점 유지. Fig.2와 다른 8후보×3시점×2arm 48렌더 검증, frame355 gap +2.44/+1.64/+2.01 dB. 기준선 22.69 dB·첫 교점 선형 보간으로 화살표 수정. [카드](ERCB_ablation/fig3_table06_compact_2026-09-21.md)
- **2026-09-21 Fig.3 다른 scene 탐색 3/3 완료:** native pair 6run/92checkpoint 전체 held-out 재평가. table06 중반 +0.7542/최종 +1.7751 dB, table01 +0.9078/+1.6594, square-1 −0.1071/+1.0513. 곡선·포스터 inset 조합으로 table06/frame1420 우선 추천, table01/frame330 대안 SVG/PNG 제작. 사후 illustration 선택이며 순수 optimizer 가속 일반화 아님. [카드](ERCB_ablation/fig3_scene_search_2026-09-21.md)
- **2026-09-21 Fig.3 controlled refinement 10/10 완료:** 공통 입력 event5개, 274 held-out view, 90 map 평가. 추가0→120 iteration에서 Ours 21.4359→21.3775, single-view vanilla 21.4908→20.7582 dB. 입력·평가 pose 고정, step/render=1:1. 최종 +0.6193 dB는 baseline 하락을 반영해 수렴 가속 가설 미입증. Frame1180 SVG/PDF/PNG 제작. [실험 카드](ERCB_ablation/fig3_controlled_refinement_2026-09-21.md)
- **2026-09-21 Fig.3 평가 범위 재집계:** 사용자 frame1180 선택. 해당 단일 view와 주변 41뷰도 1300-step 이전 격차가 작아 전체 평균 희석만으로 설명 불가. 저장된 PSNR의 CPU 진단이며 추가 학습 없음; 공통 입력·pose 상태의 refinement 평가 제안. [카드](ERCB_ablation/fig3_aria301_305_convergence_2026-09-21.md)
- **2026-09-21 HumanTeck Fig.3 Aria301_305 실측 3안 완료:** 55 checkpoint × 고정 held-out 539뷰, 최종 baseline 21.8552 / Ours 25.0936 dB, 총 render 17,620으로 동일. Frame 1180/1220/980의 600/1000/1300-step 실제 inset SVG/PDF/PNG 제작. 후반 큰 차이에 pose-correction 처리 시점 차이가 포함되므로 순수 optimizer 가속 주장은 미검증. [실험 카드·도판](ERCB_ablation/fig3_aria301_305_convergence_2026-09-21.md)
- **2026-09-20 dense-supervision event60 수렴 곡선(38/38 완료):** 기존 19-scene KF-only/KF+dense 비교를 24 checkpoint로 재측정했다. KF+dense가 19/19에서 KF-only endpoint에 더 일찍 한 번 이상 도달했고, optimizer-iteration 절감률 중앙값은 **21.4%**였다. 단 곡선은 비단조이며 event60 최종 승률은 기존과 동일한 15/19이므로 wall-clock 가속이나 endpoint 전승으로 해석하지 않는다. [실험 카드와 곡선](ERCB_ablation/dense-supervision/README.md)
- **2026-09-17 exp94 normalized ERCB 공식 B-track 17/17 완료:** 새 official vanilla와 동일 frozen causal tracker·held-out·zero-tail·physical render로 비교해 **16승1패, scene 평균 +1.253787dB**, 모든 pair fairness 10/10·독립 감사 PASS. 사전 최소 기준 PASS; UTMM `slow-straight-2` −0.126230dB로 기존 R4의 17/17·+1.260888dB 추가 목표는 FAIL. 최악 R4 대비 손실 0.080468dB로 >0.5dB 중단선 미발동. [exp94 카드](exp94_fixed_evaluator_normalized_panel.md) · [17-scene 공식 표](benchmark_custom/metric_benchmark_v2_fixed_eval_20260917/summary.md)
- **2026-09-17 exp94 UTMM 7/7 pair 완료·전체 15/17:** `square-2` normalized 21.416180, fresh vanilla 20.630652, Δ **+0.785529dB**, 8,277/8,277 render·fairness 10/10 PASS. UTMM은 6승1패·평균 +0.517175dB, 전체 14승1패·독립 감사 오류 0. Aria 2 scene pending, 17-scene 최소 판정 미완료. [진행 카드](exp94_fixed_evaluator_normalized_panel.md)
- **2026-09-17 exp94 UTMM `square-1` 공식 pair PASS(14/17):** normalized 21.224773, fresh vanilla 20.181777, Δ **+1.042996dB**. 9,345/9,345 render, 구조 12/12·이중 평가·fairness 10/10 PASS; 기존 R4 대비 −0.014942dB로 중단선 이내. 현재 13승1패, 독립 감사 오류 0, 3 pending. [진행 카드](exp94_fixed_evaluator_normalized_panel.md)
- **2026-09-17 exp94 UTMM `slow-straight-2` 첫 PSNR 패배(13/17):** normalized 17.223444, fresh vanilla 17.349673, Δ **−0.126230dB**. 1,888/1,888 render, 구조 12/12·이중 평가·fairness 10/10 PASS; 기존 R4 대비 −0.024129dB로 중단선 이내. 17/17 승리 stretch target은 실패 확정, 최소 평균+과반+전체 fairness는 4 scene 남아 미판정. 독립 감사 13/13 오류 없음. [진행 카드](exp94_fixed_evaluator_normalized_panel.md)
- **2026-09-17 exp94 UTMM `fast-straight` 공식 pair PASS(12/17):** normalized 16.379936, fresh vanilla 15.948413, Δ **+0.431523dB**. 1,348/1,348 render, 구조 12/12·이중 평가·fairness 10/10 PASS; 기존 R4 대비 +0.000733dB. 독립 감사 12/12 오류 없음, `slow-straight-2` 진행 중. [진행 카드](exp94_fixed_evaluator_normalized_panel.md)
- **2026-09-17 exp94 UTMM `ego-drive` 공식 pair PASS(11/17):** normalized 21.264177, fresh vanilla 20.560581, Δ **+0.703596dB**. 11,226/11,226 render, 구조 12/12·이중 평가·fairness 10/10 PASS; 기존 R4 대비 +0.015283dB. 독립 감사 11/11 오류 없음, 6 pending. [진행 카드](exp94_fixed_evaluator_normalized_panel.md)
- **2026-09-17 exp94 UTMM 두 번째 공식 pair PASS(10/17):** `ego-centric-2` normalized 19.492180, fresh vanilla 19.255612, Δ **+0.236568dB**. 6,655/6,655 render, 구조 12/12·이중 평가·fairness 10/10 PASS; 기존 R4 대비 −0.002240dB. 독립 감사 10/10 오류 없음, 다음 UTMM scene 진행 중. [진행 카드](exp94_fixed_evaluator_normalized_panel.md)
- **2026-09-17 exp94 UTMM 첫 공식 pair PASS(9/17):** `ego-centric-1` normalized 17.758819, fresh vanilla 17.212576, Δ **+0.546243dB**. 5,676/5,676 render, 구조 12/12·이중 평가·fairness 10/10 PASS; 기존 R4 대비 +0.003012dB. 독립 감사 9/9 오류 없음, 다음 `ego-centric-2` 진행 중. [진행 카드](exp94_fixed_evaluator_normalized_panel.md)
- **2026-09-17 exp94 RPNG 8/8 공식 pair 완료:** `table_08` normalized 23.793198, fresh vanilla 22.100431, Δ **+1.692767dB**. 94,283/94,283 render, 구조 12/12·이중 평가·fairness 10/10 PASS; R4 대비 −0.067220dB로 중단선 이내. RPNG 8/8 승리·평균 +1.598585dB, 독립 감사 8/8 오류 없음. UTMM `ego-centric-1` 진행 중이며 전체 17-scene 기준 미판정. [진행 카드](exp94_fixed_evaluator_normalized_panel.md)
- **2026-09-17 exp94 일곱 번째 공식 pair PASS(7/17):** RPNG `table_07` normalized 26.759564, fresh vanilla 25.270524, Δ **+1.489040dB**. 33,422/33,422 render, 구조 12/12·이중 평가·fairness 10/10 PASS; 기존 R4 대비 −0.080468dB로 중단선 이내. 독립 감사 7/7 오류 없음, 다음 `table_08` 진행 중. [진행 카드](exp94_fixed_evaluator_normalized_panel.md)
- **2026-09-17 exp94 여섯 번째 공식 pair PASS(6/17):** RPNG `table_06` normalized 24.473087, fresh vanilla 22.682196, Δ **+1.790892dB**. 34,437/34,437 render, 구조 12/12·이중 평가·fairness 10/10 PASS; 기존 R4 대비 −0.014501dB로 급락 없음. 독립 감사 6/6 오류 없음, 다음 `table_07` 진행 중. [진행 카드](exp94_fixed_evaluator_normalized_panel.md)
- **2026-09-17 exp94 다섯 번째 공식 pair PASS(5/17):** RPNG `table_05` normalized 22.789282, fresh vanilla 21.700924, Δ **+1.088358dB**. 52,480/52,480 render, 구조 12/12·이중 평가·fairness 10/10 PASS; 기존 R4 대비 +0.011273dB. 독립 감사 5/5 오류 없음, 다음 `table_06` 진행 중. [진행 카드](exp94_fixed_evaluator_normalized_panel.md)
- **2026-09-17 exp94 네 번째 공식 pair PASS(4/17):** RPNG `table_04` normalized 22.401817, fresh vanilla 21.276622, Δ **+1.125194dB**. 67,793/67,793 render, 구조 12/12·이중 평가·fairness 10/10 PASS; 기존 R4 대비 +0.036704dB. 독립 감사 4/4 오류 없음, 다음 `table_05` 진행 중. [진행 카드](exp94_fixed_evaluator_normalized_panel.md)
- **2026-09-17 exp94 세 번째 공식 pair PASS(3/17):** RPNG `table_03` normalized 23.555496, fresh vanilla 21.804534, Δ **+1.750962dB**. 85,029/85,029 render, 구조 12/12·이중 평가·pair fairness 10/10 PASS; 기존 R4 대비 +0.050961dB. `table_04` 진행 중, 전체 기준 미판정. [진행 카드](exp94_fixed_evaluator_normalized_panel.md)
- **2026-09-17 exp94 두 번째 공식 pair PASS(2/17):** RPNG `table_02` normalized 23.387709, fresh vanilla 21.188828, Δ **+2.198881dB**. 53,669/53,669 render, 4,229/4,231 Adam, 구조 12/12·이중 평가·pair fairness 10/10 PASS; 기존 R4 대비 +0.092057dB. 다음 `table_03` 실행 중이며 전체 기준 미판정. [진행 카드](exp94_fixed_evaluator_normalized_panel.md)
- **2026-09-17 exp94 평가 계약 수정 후 공식 첫 pair PASS:** RPNG `table_01` normalized **25.581416**, fresh official vanilla **23.928826**, Δ **+1.652589dB**. 38,302/38,302 render, 3,030/3,027 Adam, 구조 12/12·이중 평가·pair fairness PASS; 기존 R4 대비 −0.042900dB로 급락 중단선 미발동. 전체 판정은 아직 1/17. [실험 카드](exp94_fixed_evaluator_normalized_panel.md)
- **2026-09-17 exp93 RPNG 평가 급락 원인 확정:** 혼합 inventory의 Aria 어댑터가 RPNG/UTMM 평가 명령을 덮어써 `--undistort`를 누락했다. 재계측 세 번 모두 argv 누락·전처리 false·20.789347dB. adapter 위임 수정과 RPNG/UTMM/Aria 회귀 테스트 2개 PASS. 기존 20.8dB는 잘못된 GT 계약이며 정식 pair 0/17; exp94에서 새 source lock으로 재실행. [실험 카드](exp93_evaluator_preprocess_root_cause.md)
- **2026-09-17 exp92 evaluator tensor 분기:** 같은 normalized PLY의 저/고 평가 20.785455/25.574595dB에서 render prediction·pose·projection·배경 SHA는 같고 GT SHA만 달랐다. 고평가에서 `--undistort` 확인; 시간/쿨다운 가설 대신 GT 전처리 명령 감사를 시작했다. [실험 카드](exp92_evaluator_tensor_branch.md)
- **2026-09-17 exp91 evaluator 이중 평가 gate 실패 / RPNG STOP:** 15초 cooldown 뒤 같은 normalized PLY의 첫/둘째 평가가 **20.783158/20.783158dB**로 exact low, 약 1분 뒤 셋째는 **25.574971dB**였다. 입력 SHA·work/fairness 불변, R4 대비 −4.841dB 중단선 발동; official vanilla/후속 16 scene 미실행, 정식 pair 0/17. 두 번 일치만으로는 신뢰 가능한 PSNR이 아님. [실험 카드](exp91_double_eval_guard_failure.md)
- **2026-09-17 exp90 saved-PLY evaluator 첫 평가 재현성 오류:** exp88 normalized 같은 PLY `20.7874→25.5843`, exp87 R4 wrapper PLY `20.8109→25.6209`, 신규 wrapper `20.8036→25.6324dB`로 재평가 시 약 +4.8dB. 15초 cooldown 1회는 첫/둘째 25.61936/25.61936 exact지만 저수준 원인 미확정. 전체 loop STOP 유지, 독립 2회 평가 self-consistency 필요. [실험 카드](exp90_evaluator_first_pass_reproducibility.md)
- **2026-09-17 exp89 RPNG selector-family 분리:** 새 direct-file R4 control 25.6262, dense-only 25.6170, aux-only 25.6194, native-only 25.5778, all-normalized 25.5821/25.5867dB. 세 family 단독의 선택 UID trace는 exp88의 low run과 정확히 일치해 4.8dB map 붕괴 가설 기각; 평가 재현성으로 전환. [실험 카드](exp89_normalized_selector_family_isolation.md)
- **2026-09-17 exp88 Metric benchmark v2 normalized-variance ERCB — 첫 RPNG gate에서 STOP:** direct-file 런처의 동일 source/archive/work에서 RPNG `table_01` shortfall **25.6197**, normalized **20.7874dB(−4.8324)**; 기존 vanilla artifact **23.9294**보다도 **−3.1421dB**. 구조 parity 12/12 PASS이나 사전 `R4 대비 >0.5dB 하락` 중단선을 넘겨 vanilla v2와 후속 16 scene은 실행하지 않았다. 전 scene 이득 유지 미확인, normalized 채택 보류. [v2 기록](benchmark_custom/metric_benchmark_v2_normalized_variance_20260917/README.md)
- **2026-09-17 exp87 RPNG R4 실행 경로 재현성 진단:** 같은 current source·archive·seed·3,030 Adam/38,302 render·선택 UID trace에서 exp87 래퍼 **20.8109dB**, 같은 exp87 폴더로 직접 실행 **25.6197dB**. 기존 R4 PLY 재평가 **25.6243**, 당시 source 직접 재실행 **25.6269**로 R4 recipe 자체는 복원됨. 자식 프로세스 실행/로그 경로와 직접 실행 간 품질 분기이며 정확한 메커니즘은 OPEN; exp87 RPNG normalized 상대값과 17-scene 현재-source 재현 claim 보류. [정정 카드](exp87_normalized_variance_ercb_r4.md)
- **2026-09-17 exp87 normalized-variance ERCB R4 pilot(4-scene matched, 채택 보류):** 실제 `Var(count)/mean(count)` 유도의 per-view Gibbs `exp[-log(1.5)n_i/(T+1)]`을 R4의 dense/aux-KF/native-KF selector에 opt-in으로 적용했다. Frozen B-track 동일-source 4-scene seed0에서 normalized−shortfall PSNR은 UTMM fast `+.0188`, UTMM square-1 `−.0155`, RPNG table_01 `−.0144`, Aria1253 `−.0457dB`(평균 **−.0142**, 최대 손실 .0457)로 대폭 하락은 없었다. 단 archived RPNG R4 25.6243이 fresh shortfall 20.8067/20.8047로 재현되지 않았고 unbounded-cache 진단도 20.8058이므로 원인 OPEN; 과거 전체 +1.2609 보존 근거로 쓰지 않는다. [실험 카드](exp87_normalized_variance_ercb_r4.md)
- **2026-09-17 dense-supervision 19-scene fixed-replay panel(38/38 headline run 완료):** stride20·causal arrival·동일 total update·standard densification에서 KF+dense−KF-only held-out PSNR은 event당60 기준 전체 **+0.33dB(15/19)**, Aria **+0.75(4/4)**, UTMM **+0.87(7/7)**, RPNG **−0.34(4/8)**였다. RPNG 음수 장면 일부는 budget 120 또는 interval pool K=2/4/8에서 양수로 전환되어, dense supervision 이득은 frame 수 대비 service와 admission density에 좌우됨을 확인했다. Seed0·고정 VIGS pose/init replay라 strict end-to-end 근거는 아니다. [실험 카드](ERCB_ablation/dense-supervision/README.md)
- **2026-09-17 benchmark-B stride20 full-family(19/20 scene·152/152 run 완료):** 동일 VIGS source의 stride40/20 depth-anchor paired replay에서 stride20은 저예산 RR/ERCB를 각각 scene 평균 **+0.6180/+0.7342dB(19/19 양수)** 개선했다. Stride20 ERCB−RR은 event당 15/30/60 update에서 **+0.6154/+0.1137/+0.2313dB**, 승률 **16/19·7/19·9/19**로 저예산 우위가 가장 일관됐다. `slow-straight-1` source 실패는 unavailable로 보존했고, 약 4× init density 비용 및 fixed final pose/init 때문에 strict VIGS 결론은 아니다. [실험 카드](ERCB_ablation/benchmark-B/summary.md)
- **2026-09-17 exp87 incremental KF-only vs KF+dense supervision(3-scene 1차 완료, 재현 3/3 · 19-scene 확장 실행 중):** 배치에서만 관측되던 "dense supervision이 keyframe-only보다 빨리 수렴한다"(exp66, aria1253 26k에서 31.68 vs 28.38dB)를 **causal/incremental 조건에서 최초로 재현**했다. 기존 ERCB 하네스에서 이 효과가 안 보였던 원인을 실측으로 규명: `--fixed_topology_step_before_report`가 `densify_until_iter=0`을 강제해 **Gaussian 수가 init에 영구 고정**(31,185/100,157/54,373 = init과 정확히 일치)됐고 view당 update가 **0.84–6.6회**뿐이었다(exp66은 ~23회). densify를 표준 3DGS 설정으로 켜고 예산을 30k로 맞춘 exp87에서 held-out PSNR Δ(dense−KF)는 aria1253 **+2.34**, square-1 **+3.38**, table_01 **+0.52dB**로 3/3 양수이고, @3k부터 final까지 모든 milestone에서 3/3 양수다. KF-only가 전체 예산을 다 써서 도달한 품질을 KF+dense는 **1.42×/1.53×/2.95×** 적은 update로 통과한다. 최종 Gaussian 비는 1.06/0.86/1.01×로 dense arm에 체계적 용량 이점이 없어 "Gaussian을 더 많이 만들어서"라는 confound가 닫힌다. 총 update·init·pose·selector·seed·held-out을 고정하고 후보 pool만 바꾼 비교이며, pose/init는 사전 VIGS run의 고정 replay라 strict online 근거는 아니다. [실험 카드](exp87_dense_vs_kf_incremental/README.md)
- **2026-09-16 benchmark-A paired init-density pilot(8/8 완료, GO):** 동일 strict VIGS source run의 BA-refined depth/pose에서 stride40/20 anchor를 동시에 export해 RGB·pose·KF boundary·arrival schedule·Adam update·loss·topology를 고정했다. 저예산(event당15) held-out PSNR은 stride20이 UTMM square-1에서 RR/ERCB **+1.4275/+0.9215dB**, RPNG table_01에서 **+0.2685/+0.5474dB**로 4/4 양수였다. RR/ERCB 장면 평균은 **+0.8480/+0.7345dB**다. 단 training GPU time은 1.17×/1.69–1.71×로 늘어 sparse init이 절대 PSNR 병목이라는 pilot 가설만 통과했으며, 2장면 seed0 fixed replay를 strict end-to-end 결론으로 해석하지 않는다. [실험 카드](ERCB_ablation/benchmark-A/init-density-pilot/RESULT.md)
- **2026-09-15 ERCB benchmark-A recent-10-keyframe-window RR 추가(117/117 run 완료):** 기존 13-scene × 3-budget full RR/ERCB에 최근 10개 VIGS keyframe interval의 RGB frame만 활성화하는 causal RR 39개 arm을 추가했다. Window10−full RR의 scene-unweighted PSNR은 event당 15/30/60 update에서 **−1.3113/−2.1064/−2.7869dB**, 승률은 **1/13→0/13→0/13**이었다. Event 수와 delta의 상관도 **−0.6398/−0.7207/−0.6659**로 긴 장면에서 손실이 커졌다. Hard recent window는 기각하며, 저예산 ERCB 이득은 최신 구간 집중이 아니라 전체 historical pool을 유지한 interval service 조절에서 나온다는 해석을 지지한다. Seed0·fixed pose/init/topology·RGB-only historical replay 한정이다. [실험 카드](ERCB_ablation/benchmark-A/summary.md)
- **2026-09-15 ERCB benchmark-A 저·중·고예산 sweep(78/78 run 완료):** historical exp03 fixed-replay를 13개 유효 scene에서 event당 `15/30/60` update로 무튜닝 비교했다. Scene-unweighted ERCB−RR 평균은 **+0.5909/+0.2283/−0.0478dB**로 예산 증가에 따라 단조 감소했고, 승률도 **12/13→7/13→5/13**이었다. 중예산 평균은 table_05의 +2.5334dB가 지배하며 median은 +0.0037dB라 일반적으로는 동률, 고예산은 평균·median 모두 음수다. 저예산 수렴 가속 가설은 broad transfer에서 지지되지만 full-budget 우위는 기각한다. Seed0·fixed pose/init/topology·RGB-only·historical tail admission이므로 strict VIGS 근거는 아니다. [실험 카드](ERCB_ablation/benchmark-A/summary.md)
- **2026-09-15 ERCB benchmark-A historical low-budget all-scene panel(26/26 run 완료):** exp03의 fixed final VIGS pose/init·RGB-only·fixed-topology·event당15 update·seed0 조건을 무튜닝으로 전체 benchmark inventory에 확장했다. 완전한 exp80 source가 있는 13 scene에서 ERCB−RR은 **12/13 양수, 전체 평균 +0.5909dB**였고, UTMM 7개는 **+0.2638dB(6/7)**, RPNG 6개는 **+0.9725dB(6/6)**였다. Slow-straight-1/table_07/table_08은 원 VIGS 실패로 source가 없어 unavailable로 보존했다. ERCB는 11/13 scene에서 zero-service view를 오히려 늘려 view-level fairness가 아니라 interval 집중 효과이며, seed0/fixed replay/historical tail admission이므로 strict VIGS 근거는 아니다. [실험 카드](ERCB_ablation/benchmark-A/summary.md)
- **2026-09-15 ERCB exp03-H frozen frontend+topology isolation(완료, NO-GO):** GT pose에 더해 exact frontend packet과 packet-driven reference topology를 공유했다. Trace는 UTMM 70 packet/3 event, RPNG 204/1로 exact-match되고 final GS도 각각 162,792/579,323으로 같았다. Fixed ERCB−RR은 **+0.0614/−0.0614dB**, 두 장면 평균 −0.00002dB였다. 과거 fixed replay의 큰 이득은 복구되지 않았으며, 현재 VIGS의 dense max1 admission이 interval을 singleton으로 만드는 구조와 heterogeneous KF/dense loss가 핵심 차이다. [실험 카드](ERCB_ablation/exp03-H_frozen_frontend_topology/RESULT.md)
- **2026-09-15 ERCB exp03-G frozen tracking-pose isolation(완료, 양수 diagnostic):** GT absolute mapping/eval pose로 pose feedback만 제거하고 native topology는 유지했다. RPNG table_07 q3와 UTMM square-1 q15의 3-seed ERCB−RR은 각각 **+0.2546±0.1852/+0.0588±0.0196dB**, 모두 3/3 승이었다. 다만 arm별 frontend/topology/final GS가 달라 strict 근거가 아니며 H의 추가 통제로 이어졌다. [실험 카드](ERCB_ablation/exp03-G_frozen_tracking_pose/RESULT.md)
- **2026-09-15 ERCB exp03-F reliable-keyframe role pilot(완료, 0/2·NO-GO):** dense pose noise를 분리하려고 source-role service를 맞춘 채 tracked keyframe 내부에만 interval ERCB를 적용했다. Exact-step RPNG table_07 q3는 **-1.2385dB**(612/612 step, topology2/2, GS499,521→480,353), UTMM square-1 q15는 **-0.0738dB**(1009/1009 step, topology3/3)였다. KF coverage 균등화도 저예산 PSNR로 전환되지 않았으며, native topology와 causal availability의 폐루프 결합을 확인했다. [실험 카드](ERCB_ablation/exp03-F_keyframe_role/RESULT.md)
- **2026-09-15 ERCB exp03-E strict packet-budget interaction(완료, PSNR 이득 미재현):** causal mapping packet당 physical Adam credit을 해제하고, KF/dense 역할을 parameter-free causal population clock으로 pair-matching한 뒤 dense 내부 RR/ERCB만 비교했다. UTMM square-1 q15 3-seed ERCB−RR은 **-0.0059dB(2/3 승, 평균 동률)**였고 late dense service만 0.82→1.39회로 개선됐다. RPNG table_07 q3 exact-service pair(Adam612/612, KF/dense306/306, topology2/2)는 **-0.7943dB**였다. q5의 +0.7337dB는 Adam819/979 혼입이라 제외했다. Fixed-pose replay의 저예산 우위는 end-to-end PSNR로 전이되지 않았다. [실험 카드](ERCB_ablation/exp03-E_packet_budget_interaction/RESULT.md)
- **2026-09-15 ERCB exp03-A--D strict end-to-end 관측(완료, production 우위 미확립):** work-credit는 selector→service→admission 혼입으로 square-1 ERCB−RR **-0.0868dB**였고([A](ERCB_ablation/exp03-A_strict_e2e/RESULT.md)), fixed-arrival square-1은 3-seed **+0.3418/-0.6498/+0.2994dB**, 평균 **-0.0029dB**로 동률이었다([B](ERCB_ablation/exp03-B_strict_fixed_arrival/RESULT.md)). RPNG table_01 strict1.5는 RR tracking SVD 실패로 pair 불성립([C](ERCB_ablation/exp03-C_strict_rpng_transfer/RESULT.md)), ego-centric-1 compute-matched pair는 **-0.3306dB**로 전이 실패했다([D](ERCB_ablation/exp03-D_strict_utmm_transfer/RESULT.md)). ERCB는 late-cohort service는 개선하지만 native topology/처리량과 학습가치 차이 때문에 strict PSNR 우위가 일관되지 않는다.
- **2026-09-15 ERCB exp03 RTX 5070 Ti budget reproduction(28/28 완료):** exp77의 fixed-pose/init·fixed-topology scheduler-isolation pair를 UTMM square-1/RPNG table_01에서 재현했다. Interval relative-floor ERCB−RR은 15 updates/event 3-seed 평균 **+0.2595/+1.0298dB**(각 3/3 승)였지만, full budget60 3-seed 평균은 **+0.0043/−0.0706dB**(각 1/3 승)로 소멸했다. 저예산 수렴 가속은 재현됐고 full-budget 최종 우위 주장은 기각한다. [실험 카드](ERCB_ablation/exp03/RESULT.md)
- **2026-09-15 exp86-D native opacity pruning 0.5× control(2-scene × 2-selector 완료, 미채택):** birth 1×를 유지하고 online native opacity threshold만 `0.7->0.35`로 낮췄다. Final GS는 기본값의 1.23--1.51×였지만 Adam service가 38.5--40.3% 감소했고 fixed held-out PSNR은 fast RR/ERCB `+0.2247/+0.0156dB`, ego RR/ERCB `-0.4728/-0.1368dB`로 2승2패(평균 -0.0923)였다. 고정 pruning 완화도 기본값으로 채택하지 않는다. [실험 카드](exp86-D_prune_opacity_half.md)
- **2026-09-15 exp86-C causal Gaussian birth 2× control(2-scene × 2-selector 완료, 미채택):** 같은 matched wall-time/r4 unified loop에서 PPM/uniform birth downsample만 `1.0->0.5`로 바꿔 raw birth가 정확히 2×임을 확인했다. Final GS는 1.18--1.65×였지만 Adam service가 35.6--36.6% 감소했고 fixed held-out PSNR은 fast RR/ERCB `-0.0186/-0.1245dB`, ego RR/ERCB `+0.0724/+0.3411dB`로 2승2패(평균 +0.0676)였다. LPIPS는 4/4 개선했으나 PSNR 가설은 성립하지 않아 2× 기본값을 기각한다. [실험 카드](exp86-C_birth2x_capacity_control.md)
- **2026-09-15 exp78 R4 all-local-scene fixed-work B-track(PASS, loop stop):** RPNG 8/8, UTMM 7/7, Aria 2/2의 유효 17개 pair가 모두 PSNR 양수이고 fairness verifier 10/10을 통과했다. Scene-mean은 R4 **22.2592**, vanilla **20.9983**, delta **+1.2609dB**이며 dataset별 delta는 RPNG +1.5991, UTMM +0.5411, Aria +2.4274dB다. UTMM `slow-straight-1`은 IMU metric init/rescale 0으로 양쪽 map이 없어 N/A다. 원래 X4 gate(HOLD)는 사후 변경하지 않았고, 이 PASS는 이후 사용자와 정한 all-scene 평균 +0.5/majority/fairness 기준이다. B mapping-only라 C strict-live/27dB/floater 증거는 아니다. 사용자 지시대로 추가 tuning/run loop를 멈췄다. [all-scene result](benchmark_custom/r4_all_scenes_fixed_work_20260915/README.md)
- **2026-09-15 Stage 6R-X4 frozen archive geometry-cache OOM 수리(infrastructure PASS, X4 OPEN):** RPNG `table_03` R4 candidate가 dense415에서 host OOM으로 SIGKILL됐다. Kernel victim RSS는 25,640,424kB였고, 23GB archive의 26,996개 immutable PGBA geometry version을 reader가 무제한 캐시한 것이 원인이었다. 실패 artifact를 보존하고 legacy reader `c0d79f4`→32-entry LRU+bit-exact test `03426c6`→runner hash pin `5a210f8`로 분리 저장했다. Method/config/gate/RNG/work rule은 불변이며 candidate/vanilla 공통 infrastructure만 수리했다. [exp78-D X4 OOM repair](exp78/d_dataset_general_optimization/stage6rx4_frozen_archive_geometry_cache_oom_repair.md)
- **2026-09-15 Stage 6R R4 native historical-keyframe ERCB(PASS, uniform +0.044161dB / vanilla +1.694893dB):** R3에서 dense269+aux-KF269회에만 있던 ERCB를 BALANCED/REPLAY outside-window native historical slot 8,400회로 확장했다. FRONTIER/local window/dense·aux trace/Adam3,030/render38,302는 exact이며, stable-anchor service spread는 34→1, historical unique는 197→199다. Fixed502에서 R4 **25.624315**, uniform **25.580154**, fresh render-matched vanilla **23.929422dB**이고 final/render-match verifier 각 10/10 PASS다. R4를 Full candidate로 승격하되 단일 개발 장면이므로 untouched cross-sequence 확인 전 dataset-general claim은 보류한다. [exp78-D Stage 6R R4](exp78/d_dataset_general_optimization/stage6r_r4_native_keyframe_ercb_result.md)
- **2026-09-15 Stage 6R R3 separate-source KF C1/C2(PASS, R1 -0.003313dB / vanilla +1.659209dB):** accepted R1의 dense 1-step/packet과 269개 선택 trace를 exact 보존하고, 별도 C1 service1/global-residue C2 queue로 KF appearance 1-step/packet만 추가했다. R3 **25.584451**, R1 **25.587764**, 38,302-render native vanilla **23.925241dB**다. Dense unique 267은 동일, KF는 admitted210 중 unique189(90%), source appearance269/269, final LR clock267/267, zero-tail이며 render-match/R3 verifier 각 10/10 PASS다. KF의 순수 품질 효과는 사실상 0이므로 품질 향상 주장이 아니라 기존 이득을 보존한 method-scope 확장으로 채택한다. [exp78-B Stage 6R R3](5090branch/exp78/b_strict_fair_comparison/README.md)
- **2026-09-15 Stage 6R R1 C1/C2 broad-coverage reinforcement(PASS, Full-vanilla +1.417061dB):** C1 completed-service cost만 `kappa22->1`로 바꿔 global bootstrap1+성공 dense Adam 1회당 admission1로 만들고, C2 K8/rho.75/gamma log1.5/global residue와 native KF geometry/frontier/birth/topology/opportunity는 고정했다. 동일 archive/event/KF/fixed502/38,033-render에서 R1 **25.587764**, 기존 kappa22 Full **25.618109(-.030345)**, native vanilla **24.170703(+1.417061)**이다. 선택 고유 dense view는 13->267(**20.538x**), final S/U=267/269 scarcity, ERCB repeat0이며 render-match/R1 verifier 모두 10/10 PASS다. Dense-only R1은 채택하고 R2는 생략; KF auxiliary appearance는 dense와 분리된 R3에서만 검증한다. [exp78-B Stage 6R R1](5090branch/exp78/b_strict_fair_comparison/README.md)
- **2026-09-15 Stage 6A RPNG table_02 sentinel(10/10 PASS, Full-vanilla +1.761281dB / C1·C2 attribution 미확정):** frozen archive/392 mapping packet/289 KF UID/53,287 physical render/fixed584/mapping-disjoint/zero-tail exact에서 Full **23.289415**, native vanilla **21.528134dB**였다. 그러나 Full의 dense work는 380 render(전체의 **0.713%**)·18 admitted view/1,999 arrivals이고 final workload는 `S=380>U=18` rich였다. 현재 C1/C2는 keyframe 학습이 아니라 dense auxiliary admission/appearance ordering에만 적용되므로, 큰 Full 우위를 C1/C2 기여로 귀속할 수 없다. 다음 cohort 전에 dense coverage 확대와 keyframe-appearance 확장을 별도 arm으로 분리해 scope/ablation을 결정한다. [exp78-B Stage 6A sentinel](5090branch/exp78/b_strict_fair_comparison/README.md)
- **2026-09-15 paper Full Stage 5 seed1/2/3 replication(original gate HOLD, Full-vanilla mean +1.333130dB):** immutable tracker seed0에서 mapper seed1/2/3의 C1+RR/C1+C2/native-vanilla 9 run을 완료했다. 각 seed의 RR/C2는 C1 admission13/arrival1728/pending1715/event283/packet279/opportunity269/Adam2761/render38033/zero-tail exact, verifier 17/17이며 vanilla도 동일 render/event/210 KF UID로 10/10 PASS다. C2-RR은 +.004651/+.002882/-.013922dB, mean -.002130이고 lower-tail mean도 음수라 원래 gate는 HOLD다. 그러나 Full-vanilla는 +1.287321/+1.409458/+1.302612dB, mean **+1.333130dB**로 D1 주 이득은 3/3 안정 유지됐다. 13-view를 267 service로 66 epoch 도는 service-rich 조건임을 기록하고, scarcity-only ERCB 주장은 다음 cross-scene 계약에서 PSNR과 독립적인 workload stratum으로 사전 고정한다. Result commit `bb5707ca`. [exp78-B Stage 5](5090branch/exp78/b_strict_fair_comparison/README.md)
- **2026-09-15 paper Full Stage 4 C1+C2 integration(HOLD, 17/17 PASS but C2-RR -0.003491dB):** Accepted C1(global seed1+completed-service κ22)와 Stage3d global-residue C2를 처음 결합했다. Fixed pair는 C1 admission 13장/1,728 arrival/1,715 pending, 283 event/279 packet/269 opportunity/Adam2,761/render38,033/actual lifecycle·controller/zero-tail이 exact하고 global no-repeat도 valid다. 하지만 fixed502는 C1+RR **25.621600**, C1+C2 **25.618109dB**로 primary gate가 음수다. 13-view set을 양쪽 모두 66회 완전 순회해 C2가 누적 coverage 대신 epoch 내부 순서만 바꾸는 구조적 중복이 확인됐다. C2는 Full에 미통합, Stage2b **+1.082609dB**가 마지막 accepted다. Result commit `38042c2f`. [exp78-B Stage 4](5090branch/exp78/b_strict_fair_comparison/README.md)
- **2026-09-15 paper Full Stage 3d global-residue C2 isolation(13/13 PASS, C2-RR +0.012620dB):** Stage3c ERCB가 final generation 267 service 중 4개를 반복하며 856--1,382 eligible view를 미서비스한 global reshuffling semantic gap을 확인했다. K8/rho.75/gamma=log1.5는 고정하고 base measure만 remaining global residue에 조건화했다. C1-off fixed pair는 283 event/279 packet/269 opportunity/Adam2,761/render38,033/actual lifecycle/controller/zero-tail exact이며, 양 arm 모두 final 267 service=267 unique다. Repaired C2는 RR **25.554556→25.567176dB(+0.012620)**로 사전 양수 gate를 통과했다. §3.2 semantics는 isolation에서 채택하되 Stage2b(+1.082609dB)가 마지막 integrated accepted이고, 다음은 별도 C1+C2 integration gate다. Result commit `b2acecd1`. [exp78-B Stage 3d](5090branch/exp78/b_strict_fair_comparison/README.md)
- **2026-09-15 paper Full Stage 3c C2 orthogonal isolation(HOLD, ERCB-RR -0.004557dB):** C1을 끄고 accepted Stage1 위에서 causally arrived dense pool 전체를 RR/ERCB에 동일 노출했다. 283 event/279 packet/269 dense opportunity/Adam2,761/render38,033/zero-tail과 actual lifecycle membership이 exact이고 verifier 12/12다. Dense 1,728장 중 마지막 opportunity 뒤 도착한 38장은 양쪽에서 동일 pending이다. 모든 opportunity의 candidate interval이 K8 초과(36--541), ERCB block start 36회도 전부 K 초과였지만 fixed502는 RR **25.572639**, ERCB **25.568082dB**로 음수였다. 따라서 C1 small-pool 상호작용은 유일 원인이 아니며 §3.2는 HOLD, Stage2b **+1.082609dB**가 마지막 accepted다. 파라미터 sweep 없이 C2의 late-arrival service 의미를 감사한다. Result commit `fd9913c4`. [exp78-B Stage 3c](5090branch/exp78/b_strict_fair_comparison/README.md)
- **2026-09-15 paper Full Stage 3b selector-independent lifecycle repair(PASS) / ERCB ordering(HOLD, -0.003189dB):** Stage3a 사후 설명을 정정한다. Active RR clock은 `draw/current_pool` 공식이 아니라 native shuffle-refill epoch(66/25)였고, ERCB raw clock은 fractional pool-pass epoch(69/27)라 selector 외 lifecycle까지 달랐다. ERCB 내부에 RR과 동일한 private shadow queue를 두고 successful Adam commit에서만 진전시키자 269/269 기회에서 candidate membership·completed service·shared lifecycle clock이 exact였고 controller trace도 같았다. 12/12 verifier, Adam2,761/render38,033/zero-tail 아래 RR **25.617258**, ERCB **25.614069dB**로 delta **-0.003189dB**여서 §3.2는 여전히 HOLD, Stage2b가 마지막 accepted다. Result commit `f907cfed`; 파라미터 sweep 없이 paper §3.2 수식-구현 대조로 이동한다. [exp78-B Stage 3b](5090branch/exp78/b_strict_fair_comparison/README.md)
- **2026-09-15 paper Full Stage 3a fixed-event ordering isolation(HOLD, ERCB-RR -0.008303dB):** complete causal timeline/269 packet-paid dense opportunity/13 identical C1 admissions/Adam2,761/physical render38,033/zero-tail을 RR과 ERCB에 정확히 맞췄다. Fixed502는 RR **25.624185**, ERCB **25.615882dB**로 ordering gate가 음수라 §3.2를 채택하지 않는다. 기록된 verifier는 10/10이나 post-run audit에서 lifecycle clock이 RR `draw/current pool`, ERCB `epochs_started`로 달라 final clock/origin 66/25 vs69/27임을 발견했다. Result commit `a01e74b1`; 다음은 selector-independent completed-opportunity clock+transition parity를 사전 고정해 재검증한다. [exp78-B Stage 3a](5090branch/exp78/b_strict_fair_comparison/README.md)
- **2026-09-15 paper Full Stage 3 corrected repeat(HOLD 재현, 평균 +0.965844dB):** 동일 completed-service 구현/고정 파라미터 repeat는 custom **25.259935dB**, exact 22,732-render vanilla **24.326188dB**, **+0.933746dB**, verifier 10/10/zero-tail이다. 첫 corrected +0.997941과 합친 평균은 **+0.965844dB**라 gate 실패를 재현했다. 같은 설정인데 pool11→15/dense424→528/packet169→159로 wall-realized C1 work가 달라져, 다음은 파라미터 sweep 없이 membership·admission·service를 고정한 RR↔ERCB ordering-only 진단이다. Result commit `e0c747e7`. [exp78-B Stage 3 corrected repeat](5090branch/exp78/b_strict_fair_comparison/README.md)
- **2026-09-15 paper Full Stage 3 completed-service correction(HOLD, +0.997941dB):** 기존 ERCB queue가 view 선택 순간 service count를 올려 deadline-rejected Adam 1회까지 완료 work로 센 버그를 발견했다. `8c4fefa5`에서 commit/cancel transaction으로, `98e4f30b`에서 rejected physical render 별도 telemetry로 고쳤고 regression 81/81 PASS. 수정 run은 dense=draw=424, pending render1, C1 241/220/21, zero-tail이며 custom **25.282680dB** 대 exact **22,971-render** native vanilla **24.284738dB**, **+0.997941dB**(SSIM +.023069/LPIPS -.012355), verifier 10/10이다. 사전 +1 gate를 0.002059dB 못 넘어 반올림 없이 HOLD, result commit `6521519d`; Stage2b가 마지막 accepted recipe다. [exp78-B Stage 3 correction](5090branch/exp78/b_strict_fair_comparison/README.md)
- **2026-09-15 paper Full Stage 3 ERCB production(HOLD, 반복 평균 +0.9809dB):** Stage2b 위에 §3.2를 contract `2e17c12a`→isolated queue `b7a3f5bf`→opt-in wiring `7426858a`→PGBA 뒤에도 admission interval을 불변으로 유지하는 fix `34b85d70` 순으로 분리 저장했고 관련 scheduler 80/80 test를 통과했다. Frozen K8/rho.75/gamma=log1.5, strict1.5x/zero-tail의 두 반복은 custom **25.2929/25.2971dB**, exact 22,760/22,824-render native vanilla **24.3095/24.3187dB**, delta **+0.9834/+0.9784dB(평균 +0.9809)**이며 verifier 각 10/10이다. RR sibling은 render/dense/pool/packet을 더 받고도 ERCB보다 0.0366dB 낮아 방향은 양수지만 wall work가 달라 ordering-only 증거는 아니다. 사전 +1.0 gate를 평균 0.0191dB 못 넘어 Stage3/최종 Full은 채택하지 않고 result commit `d245363e`로 HOLD 고정했다. [exp78-B Stage 3](5090branch/exp78/b_strict_fair_comparison/README.md)
- **2026-09-15 paper Full Stage 2b C1 production wiring(완료, +1.0826dB 유지):** 외부 replay controller의 global-seed/completed-service κ22/no-prepurchase 장부를 core `map_scheduler.py`로 이식하고, `mapping_model_scheduler`를 켜지 않은 Stage-1 D1 topology-gate 경로에서 token flag가 causal interval discovery만 활성화하도록 분리했다(commit `8b4f00a6`, core 59/59+기존 5/5 test). Core controller를 실제 frozen replay에 사용한 반복은 wall 변동으로 dense413/pool11이었지만 fixed **25.2586dB**, 동일 163 service trace/**22,369 render** vanilla **24.1760dB**, **+1.0826dB**(SSIM +.02348/LPIPS -.01296), verifier 10/10/zero-tail이다. 외부-controller Stage2와 절대 -0.0263dB, gain -0.0046dB라 production 이식을 채택한다. §3.2는 여전히 off이며 cross-scene은 미완료다. [exp78-B Stage 2b](5090branch/exp78/b_strict_fair_comparison/README.md)
- **2026-09-15 paper Full Stage 2 C1 compute-paced growth(개발 gate 완료, +1.0872dB 유지):** accepted Stage 1에 §3.1 admission만 추가했다. Global seed 1장 뒤 completed dense service 22회당 1장을 causal temporal-maximin/interval-waterfill로 등록했고 future prepurchase는 금지했다. 1,728 arrivals 중 13장(bootstrap1+paid12), token 284 minted/264 spent/20 remaining, accounting/prepurchase violation 0이다. Candidate **25.2849dB** 대 동일 trace/**22,210 render** vanilla **24.1978dB**로 **+1.0872dB**, SSIM +.02600/LPIPS -.01708이며 verifier 10/10/zero-tail 통과. Stage 1 절대값보다 -0.1337dB이나 +1 retention gate는 통과했다. 단 C1은 아직 frozen-replay 외부 controller 경로이고 table_01 seed0만 확인했으므로 production wiring·cross-scene 전까지 final Full로 부르지 않는다. [exp78-B Stage 2](5090branch/exp78/b_strict_fair_comparison/README.md)
- **2026-09-15 paper Full Stage 1 observation topology gate(완료, +1.2482dB 유지):** 격리 branch `paper/d1-full-staged`에서 Stage0 `f3945298`, topology-only 구현 `78892a6f`, 결과 고정 `7973d126`으로 분리 저장했다. D1 native frontier/별도 appearance dense Adam/IMU pose/online-rank birth/PGBA는 그대로 두고 cadence auto-freeze만 두 번의 native topology와 상대 pre-prune capacity 회복을 관측하는 unknown-horizon gate로 교체했다. Frame286/501의 prune 뒤 frame607에서 82,520 target 대비 84,311 GS가 되어 전환했으며 scene/horizon/frame/iter/count cutoff는 없다. 1.5x/reserve20ms/zero-tail candidate는 fixed **25.4187dB**, 동일 159 service trace/210 KF UID/**21,751 render** official vanilla는 **24.1705dB**로 **+1.2482dB**, SSIM +.03308/LPIPS -.02324다. Verifier 10/10 PASS이며 §3.1/§3.2는 아직 off다. [exp78-B Stage 1](5090branch/exp78/b_strict_fair_comparison/README.md)
- **2026-09-15 exp78-B native D1 render-match(완료, +1.1127dB 복원):** fixed-Adam이 D1의 별도 dense step을 same-step hybrid로 바꾼다는 문제를 수정했다. Exact D1은 그대로 두고, official vanilla가 D1과 동일 158 mapping event/210 KF UID 및 **총 physical render 21,116회**를 자기 native KF RGB-D/normal 경로로 소비하게 했다. Vanilla에는 D1의 미완료 render 12회까지 유효 학습으로 줘 baseline을 보수적으로 우대했다. Verifier 전 항목/502-view held-out/zero-tail 통과, vanilla **24.3145dB** 대 D1 **25.4272dB**, **+1.1127dB**, SSIM +.02618/LPIPS -.01492다. 원본 D1 이득은 돌아왔지만 historical auto-freeze가 있어 final paper Full은 아니며, 다음은 native frontier+independent dense를 보존한 final-v7 관측 기반 lifecycle 이식이다. [exp78-B native render match](5090branch/exp78/b_strict_fair_comparison/README.md)
- **2026-09-15 exp78-B D1 full-frontier fixed port RPNG(완료, +0.7856dB):** square에서 고정한 arm을 table_01에 무변경 전이했다. B1 Adam3,305/regular41,675 view/279 packet을 모두 보존하고 same-step causal IMU RR dense690개만 추가했으며 verifier/zero-tail 통과. Held-out **24.9065dB(B1 +0.7856)**, SSIM +.03159/LPIPS -.02788, GS429,755로 과거437,714에 근접했다. Old-rule +1.1995보다 0.4139dB 작은 이유는 단순 평가가 아니라 131/145 vs153/124 packet done/drop과 독립 dense Adam/auto-freeze였던 과거를, 279/0 full completion·결합 gradient·final-v7 pose-rematuration으로 바꾼 실행 의미 차이다. [exp78-B D1 full-frontier RPNG](5090branch/exp78/b_strict_fair_comparison/README.md)
- **2026-09-15 exp78-B D1 full-frontier fixed port square(완료, +0.3836dB/목표 미달):** B1의 Adam832/regular9,858 view를 전부 보존하고 마지막 3 iteration에 causal IMU RR appearance dense 180개를 같은 Adam step 안에서만 추가했다. Scene/time/count cutoff나 auto-freeze 없이 final-v7 관측 상태로 topology를 2회 뒤 닫았다. Verifier 전 항목/zero-tail 통과, held-out **20.9976dB(B1 +0.3836)**, SSIM +.00703/LPIPS +.00074, GS113,910이다. 음수 상호작용은 제거했지만 +1에는 부족하다. 과거 D1과 달리 독립 dense Adam이 아니라 결합 gradient이고 topology lifecycle도 달라졌으므로, 동일 arm을 historical 기준 장면 RPNG table_01에 무변경 전이한다. [exp78-B D1 full-frontier port](5090branch/exp78/b_strict_fair_comparison/README.md)
- **2026-09-15 exp78-B exact historical D1 mapper restore(완료, +1dB 재현 성공):** 격리 worktree `9c1e2767`에 과거 runtime provenance의 mapper 5개 파일 SHA를 모두 정확히 복원하고, 동일 frozen `table_01` archive/config와 1.5x·reserve20ms·dense_rr_imu·appearance replay·online-rank2.5/span2·auto-freeze 조건으로 재실행했다. Zero-tail/125.296s를 지켰고 최종 GS **437,714**로 과거 437,702와 12개 차이, fixed held-out **25.4272dB**로 과거 D1 25.3631보다 +0.0641, 당시 vanilla 24.2278보다 **+1.1995dB**였다. 따라서 +1dB 신호와 원본 코드는 살아 있으며 최근 state/count 모사가 다른 work path였던 것이 문제다. 단, 과거 v13 replay-runner는 유실되어 현재 v23 하네스를 썼고 Adam1,735/dense360으로 과거 1,908/535와 달라 이 수치는 historical reproduction이지 최종 fair-B claim은 아니다. 다음은 이 exact mapper 동작을 공통 fixed-iteration ledger에 보존 이식한다. [exp78-B exact D1 restore](5090branch/exp78/b_strict_fair_comparison/README.md)
- **2026-09-15 exp78-B D1 minimal-pruning RPNG(완료, 기각):** square에서 +0.1136dB였던 동일 상대-capacity rule을 RPNG table_01에 무변경 전이했다. Verifier valid/Adam3,305/zero-tail, topology1이며 최종 **437,816 GS**로 과거 D1 437,702와 사실상 정확히 맞았지만 PSNR은 v4 **23.7050→23.2756(-0.4294)**, B1 대비 **-0.8453dB**로 악화했다. Final Gaussian 수·topology 수가 과거 +1.135dB의 원인이 아님을 확정하고 pruning 변형을 중단한다. 다음은 현재 frontier credit을 dense로 치환하는 오류를 없애고 historical `frontier7 + independent dense` 작업 구성을 공정하게 재현한다. [exp78-B D1 minimal-pruning](5090branch/exp78/b_strict_fair_comparison/README.md)
- **2026-09-15 exp78-B D1 minimal-pruning square control(완료, 부분 GO/+1 미달):** 첫 net-prune의 직전 capacity를 상대 target으로 삼고, 서로 다른 두 관측에서 회복되면 topology만 닫는 no-frame/iter/horizon/count 방식으로 square-2를 실행했다. Verifier valid/Adam832/zero-tail에서 topology2→1, GS113,965→116,268, **20.7450→20.8586dB(+0.1136)**, B1 대비 **+0.2447dB**였다. 반복 prune이 이득 소실의 일부임은 확인했지만 +1에는 부족하고 조기 전환으로 dense가 350→399회 늘어 순수 count 효과는 아니다. RPNG table_01 직접 gate 뒤 작으면 pruning 변형을 멈추고 frontier 비잠식 dense 배분으로 이동한다. [exp78-B D1 minimal-pruning](5090branch/exp78/b_strict_fair_comparison/README.md)
- **2026-09-15 exp78-B D1 state-replay reconstruction v4(완료, RPNG capacity-only/품질 기각):** RPNG `table_01` fixed-work에서 verifier 전 항목을 통과하고 topology를 2회 뒤 닫아 최종 GS를 **429,801**로 과거 D1 437,702 수준까지 복원했지만, held-out은 **23.7050dB**로 B1 24.1209보다 **-0.4159dB**였다. 두 번째 prune 8,004개를 없애면 예상 GS가 과거와 거의 같은 437,805가 되므로 최소-prune 대조는 유효하지만, 현재 dense가 1,512/3,305(45.7%)로 과거 535/1,908(28.0%)보다 많고 fixed frontier step을 잠식한다. 따라서 capacity 단독가설은 기각하고 관측 기반 최소-prune와 frontier 비잠식 independent dense를 분리 검증한다. [exp78-B D1 reconstruction](5090branch/exp78/b_strict_fair_comparison/README.md)
- **2026-09-15 exp78-B D1 state-replay reconstruction v3(완료, square GO):** final-v7 controller는 BALANCED를 post-topology overlap으로 정의했지만 backend가 sublinear frontier에서 native topology를 계속 허용하던 state 연결 누락을 찾았다. FRONTIER에서만 topology mutation을 허용하도록 고치되 BALANCED의 birth/frontier Adam/replay는 유지했고 scheduler 71/71 test를 통과했다. 같은 fixed Adam832에서 topology3→2, GS80,335→113,965, square-2 **20.2245→20.7450dB**, B1 대비 **+0.1311dB**로 부호가 복원됐다. Verifier 전 항목 valid/no auto-freeze/drop/overlap/tail이며 다음은 역사적 +1.135의 RPNG table_01 직접 gate다. [exp78-B D1 reconstruction](5090branch/exp78/b_strict_fair_comparison/README.md)
- **2026-09-15 exp78-B D1 state-replay reconstruction v2(완료, 계약 PASS/capacity 기각):** 기존 BALANCED `sqrt(window)` frontier+remaining independent replay로 fixed Adam832를 배분해 verifier 전 항목을 통과했지만, dense가 350/832(42.1%)였고 계속 성장하는 pool 때문에 BALANCED에 머문 채 세 번째 정상 topology가 104,059→70,375 GS를 제거했다. 최종 80,335 GS, square-2 **20.2245dB(B1 -0.3895)**였다. Birth/dense knob를 더 바꾸기 전에 final-v7의 반복 topology+capacity 관측 상태가 topology cadence를 닫도록 의도됐는지 테스트/Git 이력을 감사한다. [exp78-B D1 reconstruction](5090branch/exp78/b_strict_fair_comparison/README.md)
- **2026-09-15 exp78-B D1 state-replay reconstruction v1(완료, 계약 PASS/배분 기각):** exact D1 source objects와 config가 모두 복구 가능함을 확인했다. Fixed-event arm은 online-rank birth+causal IMU RR+final-v7 관측 상태를 사용해 Adam832/832, event ledger exact, topology2, auto-freeze/drop/overlap/tail0을 통과했다. 그러나 두 번째 topology 뒤 work를 전부 replay로 넘겨 dense 510/832(61.3%)가 되었고 square-2 **20.2397dB(B1 -0.3743)**, final GS114,030이었다. 과거 table_01 D1 dense 비중 535/1,908(28.0%)와 달리 지나친 replay 배분이므로, 새 knob 없이 기존 BALANCED 정의의 `sqrt(window)` frontier+remaining replay로 바로잡는다. [exp78-B D1 reconstruction](5090branch/exp78/b_strict_fair_comparison/README.md)
- **2026-09-14 exp78-B stable point-ID service(완료, 기각/forensic 전환):** lineage 대신 stable Gaussian `point_id`마다 visible+nonzero projected appearance gradient를 서로 다른 dense UID의 두 committed Adam step에서 요구했다. Verifier valid/Adam832/regular9,858+dense240/zero-tail이나 square-2는 **20.6189dB(B1 +0.0050)**, SSIM -0.00569/LPIPS +0.01744, final GS 101,464였다. 119,741 points가 직접 mature되어 세 번째 topology 때 보호 point가 3,421개뿐이었다. 두-view 직접 maturity는 D1 capacity를 복원하지 못해 기각하고, 신규 보호 규칙 발명은 멈춘 채 historical D1 source/state의 최초 divergence forensic으로 전환한다. [exp78-B point service](5090branch/exp78/b_strict_fair_comparison/README.md)
- **2026-09-14 exp78-B uniform Gaussian birth 2×(완료, 단독 기각):** 모든 causal KF에 PPM birth multiplier 2.0을 동일 적용하고 dense/protection을 끈 square-2 control은 verifier valid/Adam832/regular9,858/zero-tail이나 **20.3848dB(B1 -0.2292)**, SSIM -0.01838/LPIPS +0.04562였다. 최종 GS도 B1 126,711보다 작은 86,648이라 “더 많이 출생했지만 정상 prune/cap 뒤 더 적게 생존”했다. Birth 수량 단독이 아니라 causal dense service와 생존 조건의 결합이 필요하다. [exp78-B uniform2](5090branch/exp78/b_strict_fair_comparison/README.md)
- **2026-09-14 exp78-B row-visible/lineage-release 진단(완료, granularity 기각):** actual visible row+nonzero projected `f_dc` gradient를 Adam commit 뒤 기록했지만, 한 row의 2-view service로 동일 origin 전체를 release해 protected lineage가 10→1로 급락했다. Verifier valid/Adam832/regular9,858+dense240/zero-tail이나 square-2는 **20.6704dB(B1 +0.0564, 이전 full-cap보다 -0.1140)**, final GS 100,622였다. Service 신호가 아니라 lineage-wide release가 너무 거친 것이므로 stable `point_id`별 두 distinct committed service로 바꾼다. [exp78-B row-service diagnosis](5090branch/exp78/b_strict_fair_comparison/README.md)
- **2026-09-14 exp78-B dense strength/allocation 진단(완료, 두 단순 가설 기각):** newborn-protection square-2에서 projected appearance cap을 0.25→1.0으로 풀어도 **20.7844dB(B1 +0.1705, cap0.25보다 +0.0339)**였고 final GS는 오히려 110,445로 줄었다. 같은 총 Adam832 중 event당 3회를 dense-only로 배정하면 regular RGB-D/normal view가 9,858→7,527로 감소하며 **20.3630dB(B1 -0.2510)**로 악화했다. 둘 다 verifier valid/zero-tail이다. Dense 세기 부족과 KF work 치환을 기각하고, B1 regular work+full-cap projected dense를 유지하면서 실제 newborn row visibility와 committed appearance gradient가 확인될 때만 보호를 해제한다. [exp78-B diagnosis](5090branch/exp78/b_strict_fair_comparison/README.md)
- **2026-09-14 exp78-B observation-conditioned newborn protection(2-scene 완료, 부분 GO):** online-rank birth와 RR dense를 결합하되, 전역 freeze 없이 각 출생 lineage를 causal dense endpoint 2회 관측 전까지만 정상 topology prune/cap에서 보호했다. Fixed-iteration verifier가 두 장면 모두 Adam/regular view exact, no-freeze/drop/overlap/tail을 통과했다. UTMM square-2는 **20.7506dB(B1 +0.1366, 기존 unprotected joint 대비 +0.1435)**, RPNG table_01은 **24.2187dB(B1 +0.0977, 기존 joint 대비 +0.1065)**였다. 결합 효과의 부호는 복구했지만 final GS가 여전히 B1보다 작고 LPIPS가 악화해 과거 +1--2dB 복원에는 부족하다. 다음은 endpoint 선택 횟수가 아니라 newborn row의 실제 visibility/gradient service로 maturity와 dense 우선순위를 묶는다. [exp78-B pilot](5090branch/exp78/b_strict_fair_comparison/README.md)
- **2026-09-14 exp78-B birth×dense interaction audit(완료, 현 조합 기각):** RPNG table_01 fixed-iteration B1 24.1209dB에서 dense RR 단독은 **24.1717(+0.0507)**, online-rank birth 단독은 **24.1064(-0.0145)**, birth+dense는 **24.1122(-0.0088)**였다. 세 arm 모두 Adam3,305/regular41,675 exact, 정상 topology/no-freeze, zero-tail, verifier valid다. Joint interaction은 -0.0450dB이고 최종 GS도 birth/birth+dense가 152,084/151,727로 줄어, appearance-only dense가 newborn을 보존하지 못했다. 과거 D1은 broad dense coverage와 cadence-dependent topology stop 뒤 큰 capacity 보존이 공통 신호였으므로, 다음은 전역 freeze가 아닌 관측 기반 newborn consolidation이다. [exp78-B audit](5090branch/exp78/b_strict_fair_comparison/README.md)
- **2026-09-14 exp78-B corrected D1-style Full(2-scene 완료, 이득 소멸/기각):** 첫 square-2 B3의 +0.4127dB는 official YAML에서 PPM이 꺼져 online-density 호출이 0인 불완전 Full이었다. D1의 PPM+256/64+causal rank2.5/span2를 fail-closed로 복구한 뒤 fixed-iteration verifier를 통과했지만 square-2 **20.6070dB(-0.0069)**, RPNG table_01 **24.0568dB(-0.0641)**로 B1보다 낮고 SSIM/LPIPS도 악화했다. Adam832/3305와 B1 regular view를 보존하면서 aux144/824를 추가했으므로 역사적 +1.598dB(최대 +2.282)는 새 공정 기준에서 유지되지 않는다. Validation/freeze는 중단하고 topology/birth와 C1+IMU+ERCB를 개발 장면에서 분리한다. [exp78-B Full 재평가](5090branch/exp78/b_strict_fair_comparison/README.md)
- **2026-09-14 exp78-B fixed-iteration B2 RR pilot(완료, 미세 양수):** exact-view KF→dense replacement는 UTMM square-2에서 Adam832/view9,858 exact를 지키고도 B1 대비 **-0.1336dB**라 control로 강등했다. B primary를 B1 KF RGB-D/normal gradient와 Adam832회를 보존하고 같은 마지막 step에 appearance-only projected dense batch4를 더하는 fixed-iteration으로 정정했다. B2는 **20.6456dB**, B1 대비 **+0.0316dB**, regular9,858+aux240 view, mapper +3.223초였고 verifier `valid=true`다. B2는 IMU dense-pose shaping 없는 RR backbone이며 아직 recipe freeze 기준에는 부족하다. [exp78-B B2](5090branch/exp78/b_strict_fair_comparison/README.md)
- **2026-09-14 exp78-B fixed-work vanilla parity(완료, 2/2 PASS):** 동일 causal event별 work에서 UTMM square-2 official/custom는 20.6260/20.6140dB(−0.0121), 832 Adam/9,858 view-update로 정확히 일치했다. RPNG table-01도 24.1523/24.1209dB(−0.0313), 3,305 Adam/41,675 view-update로 정확히 일치했다. 양 장면 모두 event/packet/mapped UID 일치, drop·preemption·held-out overlap·tail update 0이며 verifier `valid=true`. B0/B1 경로 parity를 닫고 dev B2/B3 recipe 정의로 이동한다. [exp78-B fixed-work parity](5090branch/exp78/b_strict_fair_comparison/README.md)
- **2026-09-14 exp78-B mapper-only parity 실패 및 B protocol 정정:** UTMM square-2 동일 archive/1.5x에서 official/custom vanilla가 fixed held-out **20.3068/19.9218dB**(custom -0.3850), optimizer **908/529**, view-update **9,993/6,414**, completed packet **63/65**로 사전 parity gate를 실패했다. 첫 원인은 custom backend의 regular frontier가 official 10이 아니라 hard-coded 7 iter였던 것. Frozen tracker가 실제 tracker--mapper 자원 경쟁도 제거하므로 B primary를 동일 event별 optimizer+view credit의 **fixed-work causal isolation**으로 정정하고, mapper-only 1.5x/1.0x는 throughput 진단으로 강등했다. 실시간 주장은 실제 동시 실행 C에서만 판정한다. [exp78-B parity/protocol correction](5090branch/exp78/b_strict_fair_comparison/README.md)
- **2026-09-14 exp78-B frozen causal input lock(완료):** official VIGS commit `22ffe24`와 RTX 5090 TensorRT runtime으로 RPNG 8 + UTMM 8, 총 16개 seed0 tracker archive를 고정했다. Validator v2 기준 16/16 valid, 49,080 frame/3,729 event/36,005 dense unique이며 held-out mapping overlap·future-order violation·geometry hash mismatch·capture/EOS 뒤 Gaussian update는 전부 0이다. 기존 D1은 vanilla/gsslam reserve 50/20ms 비대칭이라 역사적 transfer 근거로만 유지하고, 최종 B0--B3는 공통 reserve·동일 1.5× service deadline으로 다시 실행한다. [exp78-B archive lock](5090branch/exp78/b_strict_fair_comparison/README.md)
- **2026-09-14 exp86-B work-credit selector families(2-scene 완료, RR 유지):** 같은 cycle work-credit r4에서 RR, K128 uniform, original view-count ERCB, interval base/relative-floor/coverage1을 비교했다. Original ERCB는 같은 K128 uniform보다 fast/ego-centric에서 +0.0374/+0.3179dB였지만 RR 대비 +0.2189/-0.2245dB로 전이 부호가 갈렸다. K를 32/8로 낮추면 count CV와 dense service는 개선됐으나 ego-centric PSNR이 RR보다 -1.2831/-0.8615dB라 기각했다. Interval relative-floor/coverage1도 ego-centric에서 RR보다 -0.4152/-0.4898dB였다. [실험 카드](exp86-B_workcredit_selector_families.md)
- **2026-09-14 exp86-A unified work-credit admission fast pilot(완료, r4 전이 후보):** matched-time 주 실험이 work-credit가 아니라 fixed stride5/max1 admission이었음을 확인했다. 기존 credit의 late burst를 unified 경로에서만 `global seed1 → pool maturity → paid1 → registration ack` cycle로 바로잡고 RR/ERCB score는 유지했다. UTMM fast-straight에서 r4 RR/ERCB는 vanilla 대비 +0.2058/+0.2248dB, r2는 +0.0909/+0.0987dB라 r2를 기각했다. r4 ERCB dense p10은 4회이고 마지막 terminal debt 1장만 0회다. Fixed-arrival ERCB +0.3237보다는 아직 낮아 r4는 긴 장면 전이 전 최종 채택하지 않는다. [실험 카드](exp86-A_unified_workcredit_admission.md)
- **2026-09-14 exp85-Y projected-gradient telemetry(완료, stale residual 발견):** X dense와 동일 동작에서 추가 render/host sync 없이 계측했다. `f_dc/f_rest` dense gradient는 KF norm의 0.898/0.879배, conflict 3.72/2.33%, projection 잔존 99.36/99.79%라 PCGrad가 주병목이 아니다. 555개 재관측 progress는 평균 -22.80%였지만 PGBA pose revision 뒤 이전-pose loss cache가 남는 것을 발견해 forgetting으로 해석하지 않는다. Common463은 24.4137dB이며 다음 Z는 pose가 바뀐 view의 residual/last-loss만 무효화한다. [benchmark custom 카드](benchmark_custom/README.md)
- **2026-09-14 exp85-X SH1×dense interaction pair(완료, dense 가설 기각):** 요청 SH1이 IMU 초기화 뒤 `GaussianModel(0)`으로 조용히 리셋되는 버그를 수정하고 PLY `f_rest_0..8`을 확인한 유효 pair를 재실행했다. 동일 non-KF463에서 SH1 KF-only/dense는 **24.5224/24.5270dB**, dense 순효과 **+0.0046dB**(SSIM 동률, LPIPS -0.00083)였다. SH1 자체는 vanilla보다 +0.3525dB지만 dense 상호작용은 없으므로 첫 장면에서 전이를 중단한다. [benchmark custom 카드](benchmark_custom/README.md)
- **2026-09-14 exp85-W budgeted KF→dense appearance replacement(완료, 즉시 기각):** M의 current-window geometry/topology를 보존하고 모든 projected step에서 historical KF global2 중 1회를 dense appearance로 정확히 교체했다. KF-view 35,605+dense 2,160=37,765로 M의 총 historical render service를 맞췄지만 non-KF463 **23.9327dB**, M보다 -0.3137/U보다 -0.4219/vanilla보다 -0.2372이고 SSIM/LPIPS도 악화했다. 현재 dense는 KF를 대체할 view당 한계이득이 없으므로 첫 장면에서 기각하고 전이하지 않는다. [benchmark custom 카드](benchmark_custom/README.md)
- **2026-09-14 exp85-V joint historical marginal selector(완료, 즉시 기각):** U의 계산량과 dense selector를 고정하고 historical KF global2만 residual1+least-served1로 바꿨다. 추가 render 없이 map-call당 loss sync 1회만 사용했지만 non-KF463 **23.8075dB**, U보다 -0.5471/vanilla보다 -0.3624이고 SSIM/LPIPS도 악화했다. KF249장 모두 관측·최소10회 선택됐지만 hard KF 최대90회 집중이라 KF residual을 dense와 같은 학습가치로 보는 가정을 기각하고 타 장면 전이는 하지 않는다. [benchmark custom 카드](benchmark_custom/README.md)
- **2026-09-14 exp85-U representative 4-scene panel 완료(4/4 PSNR 양수, +1 실패):** 마지막 UTMM fast-straight 동일 UID61장은 **17.4575dB**, vanilla보다 +0.0316dB로 사실상 동률이며 projected dense service도 2 step/8 view뿐이었다. Table_01/table_04/ego-drive/fast-straight delta는 +0.1847/+0.4615/+0.3148/+0.0316dB, 평균 **+0.2482dB**다. 사전 sign gate는 통과했지만 대부분 +1 목표에는 부족해 전체16/final 폴더 생성을 보류한다. [benchmark custom 카드](benchmark_custom/README.md)
- **2026-09-14 exp85-U UTMM ego-drive 무재튜닝 전이(완료, panel 3/3 양수·+1 실패):** RPNG에서 고정한 U와 upstream map recipe를 유지하고 UTMM sensor calibration/IMU adapter만 적용했다. Vanilla 동일 UID264장에서 **20.5763dB**, vanilla보다 **+0.3148dB**, SSIM +0.01355/LPIPS -0.01904다. Regular795 step, projected66 step/264 view, loop117.268초, ATE0.06057m, EOF queue0/final update0이다. 현재 세 장면 평균 +0.3203dB이며 같은 U를 fast-straight에 마지막 전이한다. [benchmark custom 카드](benchmark_custom/README.md)
- **2026-09-14 exp85-U table_04 무재튜닝 전이(완료, RPNG 2/2 양수·+1 실패):** table_01에서 고른 marginal-utility selector를 숫자 변경 없이 table_04에 적용했다. Vanilla 동일 UID 1,134장에서 **21.2274dB**, vanilla보다 **+0.4615dB**이며 SSIM +0.01743/LPIPS -0.02917도 동시 개선했다. Table_01/+0.1847과 합쳐 RPNG 2/2 양수지만 평균 +0.3231dB라 +1에는 부족하다. Packet419/409/drop10, projected399 step/1,596 view, loop774.078초, ATE0.06040m, EOF queue0/final update0이다. 다음은 동일 U의 UTMM 무재튜닝 전이이다. [benchmark custom 카드](benchmark_custom/README.md)
- **2026-09-14 exp85-U residual marginal utility(table_01 완료, 전이 진행):** T의 모든 service/slot을 고정하고 residual score만 `robust_loss/sqrt(1+prior_services)`로 바꿘다. Non-KF463 **24.3546dB**, T/P/M/vanilla 대비 +0.0566/+0.0921/+0.1082/+0.1847dB이고 SSIM/LPIPS도 동시 개선했다. Dense305장 최소1회 coverage를 유지하면서 최대 반복은 27→5회로 줄었다. 추가 table_01 튜닝 없이 table_04로 전이한다. [benchmark custom 카드](benchmark_custom/README.md)
- **2026-09-14 exp85-T projected residual50+coverage50(완료, 미세 양수):** P의 dense batch/step/cap을 고정하고 cyclic4만 robust residual2+least-served2로 바꿘다. Regular2975/37765, dense216/864, loop363.713초로 service가 P와 거의 같은 상태에서 non-KF463 **24.2979dB**, P보다 +0.0354/M보다 +0.0516/vanilla보다 +0.1281이었다. Dense305장은 전부 선택됐지만 hard view 최대27회 집중으로, U에서 한계이득 감쇠만 추가한다. [benchmark custom 카드](benchmark_custom/README.md)
- **2026-09-14 exp85-S unbounded no-drop dense all-step(완료, absolute gate 실패):** R의 recipe에서 queue만 unbounded no-drop으로 바꿔 causal packet 243/243, regular3115 step, projected dense2300 step/9200 view를 모두 처리했다. 그럼에도 non-KF463 **24.1253dB**, M보다 -0.1210/vanilla보다 -0.0445이고 vanilla+1 gate를 1.0445dB 미달해 no-drop control pair 없이 고비용 빈도 경로를 종료한다. [benchmark custom 카드](benchmark_custom/README.md)
- **2026-09-14 exp85-R projected dense all-step(완료, 기각):** P의 batch4/cap0.25/geometry0을 고정하고 projected iteration을 packet당 1→10으로 늘렸다. Dense service는 1920 step/7680 view로 약 9배 늘었지만 packet drop18→25, regular step2975→2735로 경쟁이 생겼고 non-KF463 **24.2234dB**, M보다 -0.0230/P보다 -0.0391이었다. [benchmark custom 카드](benchmark_custom/README.md)
- **2026-09-14 exp85-Q projected dense full cap(완료, cap 가설 기각):** P의 batch4/last1/geometry0을 고정하고 PCGrad norm cap만 0.25→1.0으로 높였다. Regular2975 step/37765 KF-view와 projected216 step/864 dense-view에서 non-KF463 **24.2413dB**, P보다 -0.0212/M보다 -0.0050/vanilla보다 +0.0714로 신호 세기는 병목이 아니다. [benchmark custom 카드](benchmark_custom/README.md)
- **2026-09-14 exp85-P projected dense batch4(완료, 미세 양수·+1 실패):** O에서 dense batch만 1→4로 바꿔 regular frontier2965/37635 update를 보존하면서 projected dense215 step/860 view를 투입했다. Non-KF463 **24.2625dB**, M보다 +0.0162/O보다 +0.0292라 부호는 양수지만 noise 수준이다. 다음 Q는 batch4를 고정하고 PCGrad norm cap만 0.25→1.0으로 바꾼다. [benchmark custom 카드](benchmark_custom/README.md)
- **2026-09-14 exp85-O projected dense appearance/opacity(완료, 무손실·gain 없음):** M의 KF RGBD+normal/global2/topology를 보존하고 마지막 regular step에 dense batch1 gradient를 group별 PCGrad+0.25 norm cap으로 더하되 geometry ratio는 0으로 고정했다. Non-KF463 **24.2333dB**, M보다 -0.0130이고 LPIPS는 -0.00081 개선이라 N의 붕괴는 막았지만 PSNR gain은 없다. 다음 P는 같은 cap/step에서 batch1→4만 바꾼다. [benchmark custom 카드](benchmark_custom/README.md)
- **2026-09-14 exp85-N parity-base dense global1(완료, 기각):** M의 10 step/총 global2를 고정하고 historical KF 한 자리를 causal midpoint dense RGB로 교체했다(pool307). 동일 non-KF463 **23.8979dB**, M보다 -0.3484였고 loop/ATE는 같지만 GS가 209,220→217,377로 변했다. Native dense full gradient와 densification 통계가 topology를 흔드는 경로를 기각하고, 다음 O는 regular RGBD/topology를 보존한 projected appearance/opacity gradient 단일축이다. [benchmark custom 카드](benchmark_custom/README.md)
- **2026-09-14 exp85-M complete upstream map parity(품질 GO, realtime NO):** L에 upstream isotropic scale loss를 복구했다. Vanilla 동일 non-KF 463장 **24.2463dB**, vanilla보다 +0.0764이고 L보다 -0.0289뿐이며 KF ATE도 0.04933m로 일치했다. Online loop 358.004초/209,220GS/topology20/final update0이라 품질 parity는 복구했지만 realtime 합격은 아니다. 다음 N은 동일 frontier service에서 historical KF global2 중 1개만 causal dense RGB로 교체한다. [benchmark custom 카드](benchmark_custom/README.md)
- **2026-09-14 exp85-L upstream map parity minus isotropic(품질 GO, telemetry 불완전):** custom 코드를 유지하고 scheduler/idle/dense를 끈 뒤 upstream frontend·init1050·uniform birth·frontier10/global2·RGBD+normal·drop-oldest를 묶음 복구했다. Vanilla 동일 non-KF 463장은 **24.2752dB**, vanilla 24.1699보다 +0.1054이고 KF ATE도 0.04940m로 일치해 4dB gap을 final-v7 map-path 변경 묶음으로 좁혔다. 실행 중 wrapper 수정으로 run.log가 손상돼 packet/runtime 증거에는 쓰지 않으며, M에서 isotropic까지 복구해 고정 wrapper로 재측정 중이다. [benchmark custom 카드](benchmark_custom/README.md)
- **2026-09-14 exp85 metric audit + K upstream frontend(완료, 기각):** D–J가 custom JSON의 fixed+KF union `mean_psnr`를 fixed로 잘못 기록한 것을 발견해 `fixed_eval_mean_psnr`로 정정했다(결론 부호 불변). Vanilla와 동일 463 UID도 재집계했다. H fixed/shared는 20.1342/20.1160, J는 19.1974/19.2192dB다. H에 upstream frontend(window25/radius2/BA4+2/motion2.4)를 복구한 K는 KF221→243·loop181.717초였지만 fixed/shared **19.6051/19.6103dB**, H보다 -0.5291/-0.5057이고 ATE도 0.06548m로 악화해 기각했다. 다음은 scheduler/idle을 끈 upstream map parity control이다. [benchmark custom 카드](benchmark_custom/README.md)
- **2026-09-14 exp85-J RPNG full-frontier service(완료, 기각):** custom 개발 단계의 exact 1.5x hard cutoff를 풀고 H에서 매 packet constant frontier10을 전부 수행했다. 213/213 packet·drop0·tail update0, online loop 203.751초였고 frontier step/view update는 532/8,398→2,078/34,686으로 증가했지만 fixed **19.1974dB**, H보다 -0.9368dB였다. 단순 mapping service 부족 및 fixed current-window 반복 가설을 기각했다. 최초 frame-gate J는 validation 실패한 무효 pilot이고 `_v2`만 유효하다. [benchmark custom 카드](benchmark_custom/README.md)
- **2026-09-14 exp85-I RPNG no-drop dense global3 pair(완료, 기각):** H의 no-drop/KF RGBD+normal에서 dense slot만 0→3으로 바꿔 dense frontier update 1389회를 확인했지만 fixed **20.1043dB**, H보다 -0.0299였다. Dense 무효가 packet drop 때문은 아니다. [benchmark custom 카드](benchmark_custom/README.md)
- **2026-09-14 exp85-H RPNG no-drop mapping queue(완료, 부분 GO):** D에서 queue policy만 causal backpressure로 바꿔 packet 처리 176/213→213/213, drop37→0, idle replay1902→2871을 확보했다. Fixed **20.1342dB**, D보다 +0.1463이다. 구조는 유지 후보다. [benchmark custom 카드](benchmark_custom/README.md)
- **2026-09-14 exp85-G RPNG motion threshold 3.6→2.4(완료, 기각):** F에서 한 값만 바꿔 active candidates 507→662/frontier step 520→644가 됐지만 idle replay2394→874, online loop129→150초로 악화했다. Fixed **19.9195dB**(+0.0741)라 KF 증가도 4dB gap의 원인이 아니다. [benchmark custom 카드](benchmark_custom/README.md)
- **2026-09-14 exp85-F RPNG vanilla uniform 64/32 birth(완료, 기각):** E에서 point-birth policy만 PPM online-rank 256/64→upstream uniform 64/32로 복구했으나 table_01 fixed **19.8453dB**, E보다 -0.0238dB였다. [benchmark custom 카드](benchmark_custom/README.md)
- **2026-09-14 exp85-E RPNG init map 600→1050(완료, 기각):** D에서 initial map optimizer service만 upstream 1050회로 복구했으나 table_01 fixed **19.8691dB**, D보다 -0.1187dB였다. 단순 초기 update 부족은 원인이 아니다. [benchmark custom 카드](benchmark_custom/README.md)
- **2026-09-14 exp85-D RPNG keyframe RGBD+normal 복구(완료, 단독 원인 기각):** table_01에서 KF loss만 `alpha=.95`, normal=.5로 복구했다. Fixed **19.9879dB**로 RGB-only A보다 **-0.2485dB**여서 공통 RPNG gap의 원인이 아니었다. [benchmark custom 카드](benchmark_custom/README.md)
- **2026-09-14 exp85 paced-online dense 대표 panel(중간 완료, B gate 실패):** 1.5× 입력 pacing+EOF frontier queue drain에서 final-v7 KF control/dense-global3를 비교했다. Fixed held-out B는 UTMM ego-drive **22.2251dB(+1.9636 vs vanilla)**, fast-straight **15.8650(-1.5609)**, RPNG table_01 **20.1401(-4.0298)**로 1승2패다. RPNG paired A는 20.2364라 dense는 -0.0963; B는 3/4 gate가 불가능해 table_04/전체16을 중단했다. 짧은 pre-IMU stream에서도 dense가 활성화되도록 provisional endpoint interpolation과 IMU gauge-reset 재등록을 구현했지만 fast 품질 병목은 해소되지 않았다. [benchmark custom 카드](benchmark_custom/README.md)
- **2026-09-14 vanilla benchmark 3종 정리(완료):** `synchronous_unbounded` 18/18, RTX5070Ti `1.5x` paced-streaming UTMM/RPNG 16/16, 논문 before/after-color reference를 분리하고 한 표로 통합했다. 공통 16-scene 평균은 paced-streaming **20.7729**, matched sync **20.8416**, paper-before **21.5400dB**이며 streaming EOF map drain은 평균 1.321초(최대 5.456초)다. [통합표](benchmark_vanila/summary.md)
- **2026-09-13 exp83-R RPNG no-polish vanilla 비교(완료, 크게 미달):** `table_01` 첫 1,000장에서 original vanilla `origin/main@22ffe24c --pure_online`을 실행했다. Vanilla keyframe을 양쪽에서 제외한 shared held-out 185장은 current Q **18.9377** vs vanilla **23.8599dB**, **−4.9222dB**였다. Vanilla에는 final BA/26k color polish가 없지만 synchronous/unbounded online map이라 같은 시간예산 비교는 아니다. 전체 vanilla baseline은 [benchmark_vanila](benchmark_vanila/README.md)로 확장 중이다. [exp83 카드](exp83_kf_dense_supervision/README.md)
- **2026-09-13 exp83-Q final-v7 no-freeze 교차 데이터 회귀(완료, RPNG strict 실패):** 현재 HEAD의 동일 causal-dense final-v7을 UTMM ego-drive full/RPNG table_01 첫 1,000장에 재튜닝 없이 전이했다. Fixed는 **21.2556/18.9723dB**, update tail은 둘 다 0/0. UTMM producer는 deadline +0.012초 경계, RPNG는 **+1.020초로 strict 1.5× 실패**했고 replay도 182회뿐이다. Current-code KF pair가 없어 dense gain으로 귀속하지 않으며 다음 축은 동일 HEAD KF-only pair다. [실험 카드](exp83_kf_dense_supervision/README.md)
- **2026-09-13 exp83-P final-v7 topology-freeze 제거(완료, 평균 27dB 유지):** exp57 freeze800과 exp67 final-v7을 혼동한 계보를 정정하고, frame/count 기반 topology-freeze 및 dense-trigger API·runner wiring을 삭제했다. Aria1253 final-v7 unknown-horizon 2회 fixed는 **26.9449/27.1171dB(평균 27.0310)**, 정상 topology event 2회 뒤 state-based balanced→replay 전환, freeze log 0, online-final map update 0이었다. 개별 2/2 27 통과는 아니지만 장면별 freeze knob 없이 현재 평균 수준은 유지했다. [실험 카드](exp83_kf_dense_supervision/README.md)
- **2026-09-13 exp83-O dense RMSE objective(완료, 기각):** native/idle dense가 같은 L1+DSSIM 분기를 공유함을 확인하고 N의 schedule에서 dense만 MSE-monotone RMSE로 바꿨다. Strict fixed **21.4978dB**로 KF보다 +0.2004지만 N보다 −0.0877; service도 Adam3,542로 N보다 238회 적어 완전 분리는 아니나 loss mismatch가 주병목이라는 증거는 없다. 당시 계획한 topology-trigger P는 후속 계보 감사에서 취소·삭제했다. [실험 카드](exp83_kf_dense_supervision/README.md)
- **2026-09-13 exp83-N native-global3+idle KF75/dense25(완료, 새 최고/+1 미달):** native KF/dense 6,518/1,218회와 pool139를 유지하고 idle을 KF2,244/dense748로 배분했다. Strict tail0/0, fixed **21.5855dB**로 repeat KF보다 **+0.2880**, random-global3보다 +0.0969dB인 native 계열 최고다. Source 비율 sweep은 멈추고, M에서 SSIM/LPIPS만 크게 좋아진 증거를 따라 dense loss와 PSNR=MSE 정렬을 감사한다. [실험 카드](exp83_kf_dense_supervision/README.md)
- **2026-09-13 exp83-M native-global3+idle dense100(완료, PSNR 기각):** native KF/dense 6,420/1,197회를 유지하고 idle replay 3,192회를 모두 dense RGB로 바꿨지만 fixed **21.2360dB**, repeat KF보다 −0.0614/random-global3보다 −0.2525였다. Fixed SSIM 0.71682·LPIPS 0.31502는 KF보다 개선돼 dense 신호 자체는 유효하지만 KF replay 전면 치환은 MSE에 불리하다. 다음 N은 과거 근거가 가장 좋은 idle KF75/dense25만 global3와 결합한다. [실험 카드](exp83_kf_dense_supervision/README.md)
- **2026-09-13 exp83-L hybrid residual/coverage sampler(완료, 기각):** batched EMA 수정 후 idle KF2807·Adam3588·native dense1197·tail0/0을 회복했지만 fixed **21.3731dB**, repeat KF +0.0757이나 K −0.0751/random repeat −0.1154. Late service 증가는 final quality로 이어지지 않아 score/slot sweep을 중단한다. 다음 M은 random global3를 유지하고 idle replay만 compact dense RGB로 교체한다. [실험 카드](exp83_kf_dense_supervision/README.md)
- **2026-09-13 exp83-L hybrid sampler pilot(invalid, sync 위치 버그):** residual1+least-served1+random1은 native dense update 1,197회를 유지했지만 residual EMA의 per-iteration GPU→CPU sync 때문에 idle KF replay 2,701→1, total Adam 3,482→782로 붕괴해 fixed 20.0983dB였다. Selection 판정에서 제외하고 K의 map-call batched progress transfer에 EMA를 병합한 뒤 같은 L을 재실행한다. [실험 카드](exp83_kf_dense_supervision/README.md)
- **2026-09-13 exp83-K native-global3 progress 관측(완료, signal 선택):** random global3를 바꾸지 않고 native map-call progress를 저장했다. Dense update는 기존과 같은 1,197회, fixed **21.4482dB**(repeat KF +0.1508), tail 0/0. Dense 129장/912 pair에서 previous progress→next absolute gain Spearman 0.080, previous loss→next gain **0.315**였다. Fisher는 dense_rr에서 전부 0. 다음 L은 robust residual1+least-served1+random1의 고정 3슬롯 조합이다. [실험 카드](exp83_kf_dense_supervision/README.md)
- **2026-09-13 exp83-J interval-bootstrap+token pure gate-removal(완료, 기각):** 기존 interval bootstrap은 유지하고 paid maturity gate만 completed-work token \(\kappa=22\)로 교체했다. Bootstrap140+paid127=267장, replay3192·Adam3708로 starvation은 해결했지만 fixed **20.9872dB**(A −0.2595, B −0.4994), last/first service 0.271이었다. Final-v7 admission family를 중단하고 +0.20dB가 2/2 재현된 native global3에서 progress를 관측한다. [실험 카드](exp83_kf_dense_supervision/README.md)
- **2026-09-13 exp83-I global-seed token-only(완료, 기각):** 첫 pilot은 exp81이 token flag를 off로 덮어 actual work-credit였고 fixed 21.2030(pool421)이라 I 판정에서 제외했다. Wiring 수정 후 실제 \(\kappa=22\)는 bootstrap1+paid50=pool51, fixed **20.0185dB**(KF A 대비 −1.2283), first/last service 63.92/4.75로 coverage가 굶었다. 숫자 sweep 대신 exp73이 남긴 분리 축인 “interval bootstrap 유지 + paid maturity gate만 token으로 교체”를 exp83-J에서 검증한다. [실험 카드](exp83_kf_dense_supervision/README.md)
- **2026-09-13 exp83-H progress 관측-only 반복(완료, admission 불안정성 노출):** B의 loss/pose/selection을 유지하고 view별 progress를 stream 종료 뒤 JSONL로 남겼지만 fixed **21.0909dB**, B보다 −0.3958dB였다. Pool 310→543, Adam 3,508→2,715로 갈려 maturity work-credit의 timing feedback이 결과를 지배했다. 1,112 paired observation에서 progress↔loss Spearman −0.197, progress↔Fisher −0.095로 세 신호는 구별됐지만 post-PGBA 관측이 희소해 sampler는 보류한다. 다음 exp83-I는 gate-free token \(\kappa=22\)로 admission clock부터 안정화한다. [실험 카드](exp83_kf_dense_supervision/README.md)
- **2026-09-13 exp83-G IMU pose-source 교체(완료, 버그 수정 후 기각):** adaptive dense record가 IMU residual을 누락해 첫 PGBA 뒤 289장 중 0장에 correction이 남는 버그를 발견했다(pilot 19.6242dB). 일반 경로와 같은 residual 보존을 구현하자 316장 중 312장에 재적용되고 fixed **21.1924dB(+1.5682)**로 회복했다. 그러나 KF-only A보다 −0.0544, optical B보다 −0.2942이며 total Adam도 B 3,508→G 2,887로 줄어 pose-source 교체는 기각한다. 두 run 모두 strict tail 0/0. [실험 카드](exp83_kf_dense_supervision/README.md)
- **2026-09-13 exp83-E/F dense frontier timing(완료, 기각):** final-v7 replay-only B(21.4867dB)에 native dense-global3를 추가한 E는 **21.3293dB**, 같은 dense interval을 frontier `map()` 전에 등록한 F는 **21.1035dB**였다. E/F의 native dense update는 동일 420회지만 F는 pool 317→552, total Adam 3,466→3,068로 admission/service가 악화했다. 둘 다 strict deadline/EOS tail 0/0. Native slot 교체와 pre-frontier 등록을 중단하고 다음 exp83-G에서 B의 optical pose source만 저비용 IMU rotation bridge로 바꾼다. [실험 카드](exp83_kf_dense_supervision/README.md)
- **2026-09-13 exp83 final-v7 공통-policy 경계 감사(진행 중):** backpolish 함수를 제거한 current HEAD에서 Aria1253 exp67 policy가 fixed **27.0560dB**로 27dB를 통과했다. UTMM 5070 execution 위 final-v7 dense는 KF-only 21.2468→**21.4867dB(+0.2399)**로 작은 양수이나 +1 미달. 반대로 exp67의 frontend 실행 숫자까지 UTMM에 그대로 이식하면 fixed 17.6878dB, sensor EOS가 1.5× deadline보다 5.94초 늦어 실패했다. 결론은 **공통 scheduler/loss + sensor·measured-cost execution adapter**이며, 모든 실행 숫자의 강제 공통화는 기각한다. [실험 카드](exp83_kf_dense_supervision/README.md)
- **2026-09-13 exp83 2× budget 진단(완료, map-iter 부족 단독가설 NO):** 동일 KF-only/global3 pair에서 scale만 1.5→2.0으로 늘리고 causal sensor-EOS zero-tail을 유지했다. Fixed는 **21.6809/21.8221dB**, dense gap **+0.1412dB**로 1.5× 반복 평균 +0.2013보다 커지지 않았다. Adam은 7,085/7,991회로 크게 늘었고 dense 쪽이 906회 더 많아도 gap이 축소됐다. Common estimated trajectory에서도 dense-map 우위는 +0.0179/+0.2772dB로 양수. **2×는 공식 strict 1.5× 성과가 아닌 budget 진단이다.** [실험 카드](exp83_kf_dense_supervision/README.md)
- **2026-09-13 exp83 native global3 반복성(완료, 작은 효과 GO/+1 NO):** 동일 strict pair를 반복해 dense-global3가 KF-only를 **+0.2115/+0.1911dB**로 2/2 이겼다(평균 +0.2013, range 0.0204). Repeat1은 Adam 차이가 30회뿐인데도 +0.1911이라 작은 dense 효과는 재현됐지만 목표 +1까지 평균 0.7987dB가 남는다. 숫자 sweep은 멈추고 기존 RGB loss에서 view별 learning-progress를 관측한다. [실험 카드](exp83_kf_dense_supervision/README.md)
- **2026-09-13 exp83 native global3 dense-weight2(완료, 기각):** random global3의 view/KF loss/topology를 고정하고 dense RGB 항만 1→2배로 높였지만 fixed **21.5252dB**, KF-only 대비 +0.1938이나 weight1보다 −0.0177. 초기 600 frame은 개선되고 후반은 모두 악화해 상수 weight sweep을 중단하고, 최고 weight1/control pair의 반복성부터 측정한다. [실험 카드](exp83_kf_dense_supervision/README.md)
- **2026-09-13 exp83 native global3 mix1(완료, 기각):** 1 balanced+2 random mixture는 fixed **21.5099dB**, KF-only 대비 +0.1785이나 random global3보다 −0.0330. Late coverage 개선이 early/mid 손실을 상쇄하지 못해 random을 유지하고 다음 단일 축은 dense RGB weight 1→2다. [실험 카드](exp83_kf_dense_supervision/README.md)
- **2026-09-13 exp83 native global3 all-balanced(완료, 기각):** 137 dense 후보를 7–9회로 균등 서비스했으나 fixed **21.3506dB**, random global3보다 −0.1923. Frame1200+는 control 대비 +0.873dB지만 frame0–599를 최대 −0.462dB 훼손했다. 다음은 1 balanced+2 random slot causal mixture다. [실험 카드](exp83_kf_dense_supervision/README.md)
- **2026-09-13 exp83 native global3 open-topology(완료, 기각):** native dense gradient를 후속 topology event 3회에 소비했지만 fixed **21.1846dB**였다. Open KF-only 21.0161보다 +0.1685이나 auto-freeze global3 21.5429보다 −0.3583. Topology 개방은 gain을 키우지 못해 다음 단일 축은 arrived dense 최소 방문 우선 선택이다. [실험 카드](exp83_kf_dense_supervision/README.md)
- **2026-09-13 exp83 unified native-map global3(완료, 부분 GO·수확체감):** 같은 총 6 global 슬롯에서 dense를 1→3으로 늘려 native dense view-update를 406→1,197회로 만들었지만 fixed는 21.4864→**21.5429dB**, +0.0565dB만 상승했다(KF-only 대비 +0.2115). 둘 다 dense 등록 뒤 topology event가 없어 다음 단일 축은 global3+open topology다. [실험 카드](exp83_kf_dense_supervision/README.md)
- **2026-09-13 exp83 unified native-map global1(진행, 부분 GO):** idle dense draw를 0으로 두고 native `map()`의 6 historical-global 슬롯 중 1개만 causal IMU-midpoint dense RGB로 교체했다. Current-window KF RGBD+normal과 총 frontier view 수는 유지됐고 native KF/dense 7,316/406, idle KF/dense 2,787/0회를 실측했다. Fixed **21.4864dB**, KF-only 대비 **+0.1551dB**로 방향은 양수지만 +1 미달. 다음 단일 축은 dense global slot 1→3이다. [실험 카드](exp83_kf_dense_supervision/README.md)
- **2026-09-13 exp83 full-GT pair·early topology 진단(완료, pose/idle-trigger 단독축 기각):** mapping/eval pose를 모두 GT absolute로 바꾼 non-strict pair도 KF-only 18.9002, KF75+dense25 19.0608dB로 dense gain은 **+0.1607dB**뿐이었다. Strict dense-owned topology trigger 64/16도 21.2703/21.2525dB로 KF control보다 −0.0610/−0.0788. trigger16 event도 frontier event 뒤(frame654 vs633)에 발생해 idle replay 자체가 늦음을 확인했다. 다음 단일 축은 causal dense를 native `map()` view scheduler로 합치는 구조다. [실험 카드](exp83_kf_dense_supervision/README.md)
- **2026-09-13 exp83 compact repeated service(완료, 단독 축 기각):** persistent IMU dense pool을 139→28장으로 줄이고 dense update 729회, 약 26회/view로 집중했지만 fixed는 **21.4322dB**였다. KF-only 대비 +0.1008이나 139-view best보다 −0.0720이며 +1 미달. pose/quota/pool sweep을 멈추고 다음 구조 축은 exp84와 달랐던 dense의 pre-freeze topology evidence 참여다. [실험 카드](exp83_kf_dense_supervision/README.md)
- **2026-09-13 exp83 GT-relative dense-pose oracle(완료, +1 경로 NO):** 동일 KF75/B1/native loss/topology/69.9454초에서 dense intra-interval pose만 GT 상대운동으로 바꿨다. UTMM robot→RGB camera axis를 바로잡은 corrected oracle fixed는 **21.3001dB**, KF-only보다 −0.0313dB(138/139 bridge, KF/dense replay 2,277/760). 최초 21.0783dB는 `UTMM_C2R` 누락 invalid pilot으로 보존. pose 단독 병목 가설은 기각하고 다음은 30~40-view compact repeated service 한 축이다. **oracle은 strict 성과 아님.** [실험 카드](exp83_kf_dense_supervision/README.md)
- **2026-09-13 exp83 same-backward dense pose update(완료, 기각):** 기존 dense RGB backward로 camera pose를 502회 joint update하고 PGBA residual 119/119를 유지했지만 fixed는 21.3792dB, KF-only 대비 +0.0479dB 및 pose-align 없는 최선보다 −0.1250dB. 별도 backward는 없으나 total Adam이 3,781→3,415로 9.7% 줄어 pose 방향과 service loss가 섞였다. step-size sweep은 중단하고 다음은 VIGS dense-pose GT 상대운동 oracle 한 축이다. [실험 카드](exp83_kf_dense_supervision/README.md)
- **2026-09-13 exp83 IMU bridge PGBA 지속성 수정(부분 GO):** 첫 PGBA가 기존 dense 119장의 IMU 보정을 interpolation으로 덮어쓰는 버그를 수정해 118개 residual을 재적용했다. 동일 KF75/B1 compact arm fixed가 21.2604→**21.5042dB**, KF-only 대비 **+0.1728dB**로 회복했지만 +1은 미달. 다음은 dense RGB backward를 재사용하는 bounded translation pose update다. [실험 카드](exp83_kf_dense_supervision/README.md)
- **2026-09-13 exp83 compact B2 joint update(완료, 기각):** 동일 139-view/IMU midpoint에서 매 Adam에 KF+dense를 묶자 replay는 1,503/1,503회였지만 fixed 21.0245dB로 KF-only보다 −0.3069dB. 단순 joint 평균은 KF geometry supervision을 보존하지 못하므로 quota/batch sweep을 멈추고, 다음은 dense pose만 GT로 바꾸는 VIGS oracle 진단이다. [실험 카드](exp83_kf_dense_supervision/README.md)
- **2026-09-13 exp83 compact dense service·optical pose 진단(진행 중):** 139-view causal midpoint pool의 dense quota를 10%→25%로 높여 731회(~5.3/view) 서비스했지만 판정용 fixed PSNR은 21.2604dB로 KF-only 21.3314보다 −0.0710dB였다. synchronous optical filler는 queue 비용 0.553→11.304초, replay 2,922→1,312로 붕괴해 fixed 20.9848dB. 다음 단일 축은 동일 pool/IMU pose에서 매 Adam에 KF+dense를 함께 넣는 B2 joint update다. [실험 카드](exp83_kf_dense_supervision/README.md)
- **2026-09-13 exp84 GT-pose frame-density 진단(완료):** UTMM `ego-drive` 1,000 RGB의 동일 GT pose/초기 360,612GS/RGB loss/8k update에서 nested stride16/8/4/2/1 pool을 비교했다. Held-out 125-view PSNR은 21.599/23.475/**23.529**/23.507/23.267dB로 stride4가 최고이며 stride16보다 **+1.930dB**. 정확한 pose에서는 dense 이득이 실재하지만 all-frame은 유한 예산 최적이 아니어서, strict 다음 축은 compact stride8 admission+반복 service다. **offline 진단이며 strict 성과 아님.** [실험 카드](exp84_gt_pose_density/README.md)
- **2026-09-13 exp83 KF+dense 서비스·topology 진단(진행 중):** B1 post-init IMU midpoint는 KF replay를 2,390회로 KF-only 2,375회보다 보존하고 dense 266회를 추가했지만 fixed 21.2640 vs 21.3314dB(−0.0673)로 동률권. Open-topology paired에서도 dense RGB만 −0.0764dB, dense densification 통계 263회까지 연결해도 −0.0916dB라 단순 topology 축은 기각. Sim3 shared-trajectory 교차 렌더에서도 숨은 map gain 없음. 다음은 첫 backward의 residual/progress를 재사용하는 causal dense 선택 감사. [실험 카드](exp83_kf_dense_supervision/README.md)
- **2026-09-13 exp83 KF+dense supervision(진행 중):** strict 1.5× `ego-drive`에서 공정한 B1 KF75+dense25는 KF-only보다 −0.504dB. endpoint-corrected IMU rotation을 넣자 interpolation 대비 +0.288dB로 회복했으나 control 대비 −0.216dB라 +1 목표는 미달. GT-only pose 진단은 회전오차 2.386°→0.066°로 원인을 확인. 다음은 dense appearance+opacity-only gradient 단일 축. [실험 카드](exp83_kf_dense_supervision/README.md)
- **2026-09-13 exp82 Aria vanilla 전이(2/2 GO):** 채택한 동일 custom strict 1.5x recipe를 aria1253/301_305에 무재튜닝 적용. original vanilla `origin/main@22ffe24c` keyframe을 양쪽 fixed set에서 함께 제외한 shared held-out에서 **+1.763/+2.739dB**, 2/2 모두 +1dB 통과. custom은 tail 0/0·MPS0, 다만 KF100이라 dense RR draw는 0회이고 1253 절대 27dB는 미달. [실험 카드](exp82_aria_vanilla_transfer/README.md)

- **2026-09-13 5070 Ti 인계:** 사용자 요청으로3070 실험 중단. RPNG 유효한 비교 없음, parallel 누락 수정/메모리 실패 기록/실행 명령을 전용 Git 브랜치로 전달. [인계](VIGS_ERCB_ablation/HANDOFF_5070TI.md)

- **2026-09-13 RPNG retry4 실패:** cudaMallocAsync도 frame731 correlation 복사 OOM. PSNR 없음; 정확값 CPU staging 메모리 절감 검토로 전환. [카드](VIGS_ERCB_ablation/LOCAL3070.md)

- **2026-09-13 RPNG retry3 OOM:** replay pool 등록 후 frame1538 correlation880MiB 할당 실패. PSNR 없음, cudaMallocAsync allocator 대안 검사. [카드](VIGS_ERCB_ablation/LOCAL3070.md)

- **2026-09-13 RPNG replay 누락 수정:** parallel=false로 worker 미생성 확인, retry2 PSNR은 RR 비교에서 제외. UTMM 공통 mapping 실행 설정을 RPNG overlay에 반영, retry3 예정. [카드](VIGS_ERCB_ablation/LOCAL3070.md)

- **2026-09-13 RPNG RR retry2 완주:** fixed502뷰15.397522dB, Adam2324, deadline/EOS0/0. MAP_RR_DONE 누락으로 replay 활성 여부 점검 필요; 비교 유효성 미확정. [카드](VIGS_ERCB_ablation/LOCAL3070.md)

- **2026-09-13 RPNG retry1 OOM:** frame839 correlation 복사1004MiB 할당 실패, PSNR 없음. retry2 공통 allocator max_split_size_mb:128 검사 예정. [카드](VIGS_ERCB_ablation/LOCAL3070.md)

- **2026-09-13 RPNG RR 초기 실행 실패:** frame276에서 미초기화 Rwg 사용. 공통 gravity-ready guard 추가, CPU tests6 통과; PSNR 없음, retry1 예정. [카드](VIGS_ERCB_ablation/LOCAL3070.md)

- **2026-09-13 RPNG VIGS 비교 재개:** 사용자 요청, native RPNG sensor config+공통 RGB-only mapping/scale6/KF256. table_01 RR seed0 시작, 품질 미검증. [카드](VIGS_ERCB_ablation/LOCAL3070.md)

- **2026-09-13 VIGS3-arm3-seed 수집 종료:** 평균 RR19.415636/기존19.533003/coverage1 19.584229dB. 변형-기존+0.051226(2/3), 변형-RR+0.168593(3/3). 사용자 요청으로 신규 실험 중단, 논문 검증 미완. [카드](VIGS_ERCB_ablation/LOCAL3070.md)

- **2026-09-13 입력 bracket 해석 정정:** VIGS 첫 KF 적분 생략/가용 IMU clamp 확인; 초기12.9ms gap을 실행 거부 대신 별도 경고로 보존. metadata pass, 경계 정확도/decode 미검증. [카드](VIGS_ERCB_ablation/LOCAL3070.md)

- **2026-09-13 slow-straight-2 입력 사전 검사:** 첫 IMU가 첫 RGB보다12.902ms 늦어 엄격 bracket 검사 실패. 입력 처리 대조 필요, 손상 판정 아님; decode 미완. [카드](VIGS_ERCB_ablation/LOCAL3070.md)

- **2026-09-13 RR seed2 완료:** fixed19.398387dB; coverage1-RR3 seeds [+0.060898,+0.228690,+0.216190], 평균+0.168593dB. 단일 장면 개발 결과/일반화 미완. 기존 ERCB seed2 시작. [카드](VIGS_ERCB_ablation/LOCAL3070.md)

- **2026-09-13 VIGS coverage1 seed2 완료:** fixed19.614576dB, Adam25177, pool1235, deadline/EOS0/0. RR seed2 시작, 3-seed paired 비교 미완. [카드](VIGS_ERCB_ablation/LOCAL3070.md)

- **2026-09-13 VIGS RR seed1 완료:** fixed19.390477dB; 기존 ERCB+0.058463/coverage1+0.228690dB. 두 seed 양수이나 일반화 미확정. coverage1 seed2 시작. [카드](VIGS_ERCB_ablation/LOCAL3070.md)

- **2026-09-13 seed1 pool 차이 감사:** relative-floor에만 KF1316 기록, 저장 KF 궤적71/70행. 동일 pool/pose 비교 아님; dense UID 원인 추적은 미완. [카드](VIGS_ERCB_ablation/LOCAL3070.md)

- **2026-09-13 VIGS coverage1 seed1 완료:** fixed19.619168dB, 기존 ERCB+0.170227dB; RR seed1 미판정. 최종 pool1236/1235 불일치 명시, deadline/EOS0/0. RR seed1 시작. [카드](VIGS_ERCB_ablation/LOCAL3070.md)

- **2026-09-13 interval 혼합 CPU 반례:** 크기9/1, full interval block에서200 draw가100/100으로 배분됨(3 mode); frame-uniform 아님. 테스트8개 통과, 학습 코드 불변. [카드](VIGS_ERCB_ablation/LOCAL3070.md)

- **2026-09-13 VIGS relative-floor seed1 완료:** fixed19.448941dB, Adam25692, deadline/EOS0/0. seed1 RR 미실행으로 우열 미판정; coverage1 seed1 진행. [카드](VIGS_ERCB_ablation/LOCAL3070.md)

- **2026-09-13 VIGS coverage1 seed0 완료:** fixed19.518942dB, RR+0.060898/기존 ERCB-0.045353dB, deadline/EOS0/0. 기존 ERCB 대비 개선·반복 우위 미확정; seed1 진행. [카드](VIGS_ERCB_ablation/LOCAL3070.md)

- **2026-09-13 VIGS relative-floor seed0 완료:** fixed324뷰19.5643dB, 동일 조건 RR 대비+0.1063dB; deadline/EOS0/0. 단일 실행으로 우위 미확정, coverage1 비교 진행. [결과 카드](VIGS_ERCB_ablation/LOCAL3070.md)

- **2026-09-13 VIGS relative-floor 통합 실패 수정:** service_state 누락으로 최초 실행 실패, 인터페이스 추가/11 tests 통과 후 동일 조건 재시작. PSNR 없음. [진행 카드](VIGS_ERCB_ablation/LOCAL3070.md)

- **2026-09-13 VIGS RR 공통 설정 seed0:** fixed324뷰19.4580dB, Adam26140, deadline/EOS0/0. relative-floor 동일 조건 시작. [진행 카드](VIGS_ERCB_ablation/LOCAL3070.md)

- **2026-09-13 VIGS 3070 첫 완주:** memory-trim RR diagnostic fixed324뷰19.6030dB, deadline/EOS update0/0, trim7회629ms. ERCB 비교 아직 없음. [진행 카드](VIGS_ERCB_ablation/LOCAL3070.md)

- **2026-09-13 VIGS allocator census:** dense417에서 allocator free3.20GB 확인 후 진단 종료. malloc_trim 전후 계측으로 전환. 품질 결과 없음. [진행 카드](VIGS_ERCB_ablation/LOCAL3070.md)

- **2026-09-13 VIGS buffer128 compact 조합:** frame979 RAM 압박으로 중단, 품질 없음. process_memory.jsonl 보존; storage/allocator 계측 필요. [진행 카드](VIGS_ERCB_ablation/LOCAL3070.md)

- **2026-09-13 VIGS ownedpriors 단독 probe:** frame1289 RAM772MiB로 자체 중단. 이전 OOM 지점 통과했으나 안정적 완주 미확보. [진행 카드](VIGS_ERCB_ablation/LOCAL3070.md)

- **2026-09-13 VIGS GPU lookup probe:** RAM 증가로 자체 중단, PSNR 없음. keyframe depth/normal slice의 전체 batch storage 보유 후보 발견. [진행 카드](VIGS_ERCB_ablation/LOCAL3070.md)

- **2026-09-13 VIGS uint8 CPU 복원 probe:** frame827 RAM 여유509MiB로 자체 중단. 전체 메모리 개선 실패, PSNR 없음. [진행 카드](VIGS_ERCB_ablation/LOCAL3070.md)

- **2026-09-13 VIGS ERCB buffer256 probe:** square-1 RR 6× frame1253 부근 RAM OOM kill 확인. 완주/PSNR 없음, 선할당 축소만으로 부족. [진행 카드](VIGS_ERCB_ablation/LOCAL3070.md)

- **2026-09-13 VIGS ERCB local3070 probe:** square-1 RR 6× 실제 실행은 메모리 압박으로 중단. held-out 품질 결과 없음; 1,200 KF 선할당 경로 확인. [진행 카드](VIGS_ERCB_ablation/LOCAL3070.md)
- **2026-09-13 exp77 (52 runs 완료):** event15 기존 ERCB−RR 3-seed 평균 UTMM +0.241/RPNG +1.027dB, 6/6 양수. coverage1 +0.276/+1.056. 큰 예산 역전·서비스 trade-off 포함. [최종 보고](exp77/FINAL_REPORT.md)

전 실험 목록. 상세는 각 카드 참조. baseline 대비 Δ는 PSNR@30k 기준.

> **HTML 보고서 모음:** [브라우저 인덱스](index.html) · [exp66](exp66/) · [exp67](exp67/) · [exp68](exp68/) · [exp69](exp69/)

## Full 30k, MPS init 1311장 (메인 트랙)

| Exp | 날짜 | 한 줄 설정 | PSNR@30k | vs exp08 | Verdict | 카드 |
|---|---|---|---:|---:|---|---|
| exp01 | 06-16 | full baseline (886k Gaussians) | - | - | 기준선 | [exp01-12](exp01-12_param_sweep.md) |
| exp02 | 06-16 | sparse densification | 33.377 | +0.37 | 최고 PSNR이나 large-scale 위험 | 〃 |
| exp03 | 06-16 | + large-scale 개선 | 33.052 | +0.04 | 보류 | 〃 |
| exp04 | 06-16 | 구조 개선 계열 | 32.831 | -0.18 | 기각 | 〃 |
| exp05 | 06-16 | beta1=0.95 | 조기중단 | - | 기각 | 〃 |
| exp06 | 06-16 | beta1=0.85 | 32.879 | -0.13 | beta1=0.85 채택 | 〃 |
| exp07 | 06-16 | pruning 완화 | 조기중단 | - | 기각 | 〃 |
| **exp08** | 06-16 | dens_until7000 + prune001 + beta1_low | **33.012** | 기준 | **현재 best baseline** | [exp08](exp08_best_baseline.md) |
| exp09 | 06-16 | densify_until=5000 | 조기중단 | - | 너무 이름, 기각 | [exp01-12](exp01-12_param_sweep.md) |
| exp10 | 06-16 | position LR 낮춤 | 32.574 | -0.44 | 기각 | 〃 |
| exp11 | 06-16 | position LR 완화 | 32.682 | -0.33 | 기각 | 〃 |
| exp12 | 06-16 | + sparse depth prior (0.01→0.002) | 32.587 | -0.43 | 기각 (outlier 고정 위험) | 〃 |
| exp13 | 06-30 | + camera-bound pcd filter | 32.855 | -0.16 | **Pop1 해결 확정** | [exp13](exp13_pcd_filter.md) |
| exp19 | 07-05 | + DepthPro ellipsoidal plateau (λ=0.01) | 32.753 | -0.26 | 보류 | [exp19](exp19_mps_depthpro.md) |
| exp20 | 07-05 | + λ schedule 0.10→0.03→0 | 31.693 | -1.32 | 기각 | [exp20](exp20_mps_scheduled.md) |
| exp21 | 07-05 | + opacity_weight, λ=0.10 | 30.770 | -2.24 | 기각 | [exp21](exp21_mps_opacity_weighted.md) |
| exp22 | 07-05 | + exp loss kernel, λ=0.05 | 29.917 | -3.10 | 기각 | [exp22](exp22_mps_exploss.md) |
| exp23 | 07-05 | + adaptive prune (d>1.5m) | 26.655 | -6.36 | 기각 (후반 붕괴) | [exp23](exp23_mps_adaptive_prune.md) |
| exp24 | 07-05 | exp loss + adaptive prune | 미완 (27k Terminated) | - | 보류 (낮은 우선순위) | [exp24](exp24_mps_exp_and_prune.md) |
| **exp25** | 07-05 | + enlarged tau (2-3x) + λ 0.10→0.03 | **32.969** | **-0.04** | **plateau 최선, floater 지표 검증 필요** | [exp25](exp25_mps_tau_enlarged.md) |
| exp26 | 07-05 | + enlarged tau + λ=1.0→0.03 | 32.706 / 32.674 (2회) | -0.31 | 기각 (λ=1.0 과함) | [exp26](exp26_mps_lambda1.md) |
| exp27 | 07-09 | anchor 7,338 pts를 init으로 (미정렬) | 29.540 | -3.47 | **좌표계 버그 발견** — anchor는 Atlas world였음 | [exp27](exp27_anchor_init.md) |
| exp27b | 07-09 | MPS 랜덤 7,338 init (대조군) | 30.583 | -2.43 | 개수 통제 대조군 | 〃 |
| exp27c | 07-09 | 정렬된 anchor 7,338 init | 31.611 | -1.40 | **anchor 배치 합격** (대조군 +1.03dB), \|Z\|>4m 8개 | 〃 |

> **⚠ 좌표계 발견 (07-09)**: exp19~26의 plateau anchor는 MPS world가 아닌 raw Atlas world였다 (표면 대비 median 0.48m, scale x0.95 오차). **Round 7 결론은 정렬 anchor로 재검증 필요.** 상세: [exp27](exp27_anchor_init.md)

## ORB init 656장 (Round 6, plateau 검증 트랙 — baseline 29.023)

| Exp | 날짜 | 한 줄 설정 | PSNR@30k | vs orb_baseline | Verdict | 카드 |
|---|---|---|---:|---:|---|---|
| exp_orb_baseline | 07-05 | plateau 없음 | 29.023 | 기준 | 기준선 | [round6](../rounds/round6_plateau_orb.md) |
| exp15 | 07-05 | spherical plateau, ORB 앵커 | 27.908 | -1.10 | 기각 (과밀집→투명화) | 〃 |
| exp16 | 07-05 | ellipsoidal plateau, ORB 앵커 | 28.924 | -0.10 | ellipsoidal 채택 | 〃 |
| exp17 | 07-05 | ellipsoidal, Metric3D 앵커 | 27.668 | -1.35 | 기각 (앵커 품질) | 〃 |
| exp18 | 07-05 | ellipsoidal, DepthPro 앵커 | 28.934 | -0.09 | DepthPro 앵커 채택 | 〃 |

## 기타 (닫힌 축)

| Exp | 내용 | 결과 | 기록 |
|---|---|---|---|
| exp13_vggt64 (번호 중복 주의) | VGGT64 3DGS 7k | Test PSNR 17.04 | [archive/vggt_evaluation.md](../archive/vggt_evaluation.md) |
| exp14 | OpenMAVIS64/MPS 3DGS 7k | Test PSNR 18.65 | 〃 |

> **번호 중복 주의**: `exp13`은 pcd_filter (메인 트랙)와 vggt64 (VGGT 트랙) 두 개가 존재. result dir 이름으로 구분.

## OpenMAVIS(ORB) 데이터셋 재현 트랙 — exp30~37 (진행 중, baseline 32.671)

MPS 트랙(exp08~29)에서 검증한 방법들을 실제 목표 데이터셋(OpenMAVIS pose + ORB init, `data/03_rgb_3dgs_full`)으로 재현하는 트랙. exp08과 직접 비교 금지 — exp30이 이 트랙의 기준선.

| Exp | 한 줄 설정 | PSNR@30k | 상태 | 카드 |
|---|---|---:|---|---|
| **exp30** | baseline (ORB 원본 7,205 init) | **32.906** | 완료 — 기준선 (run-to-run 노이즈 ±0.24dB 확인됨) | [exp30-37](exp30_37_orb_native_track.md) |
| exp31 | 일반 anchor(obs≥3, 7,108) init | 32.671 | 완료 | 〃 |
| exp32 | + plateau 기본 tau, 일반 anchor | 32.903 | 완료 (baseline과 동급) | 〃 |
| exp33 | + plateau enlarged tau, 일반 anchor | 32.536 | 완료 (MPS와 반대로 열세, floater는 최소) | 〃 |
| exp34 | 고confidence anchor(obs≥10&fr≥0.5, 1,438) init | 31.970 | 완료 (exp31보다 -0.7dB) | 〃 |
| exp35 | + plateau 기본 tau, 고confidence anchor | 32.799 | 완료 (exp32와 비슷한 패턴) | 〃 |
| exp36 | + plateau enlarged tau, 고confidence anchor | 32.591 | 완료 | 〃 |
| **exp37** | dense confidence+monodepth init (148,564), plateau 없음 | **32.621** | **완료 — \|Z\|>4m=0, 이 트랙 최고 floater 억제** | 〃 |
| exp32_lineage_diag | exp32 + lineage & decoupled grad tracking | 32.903 | 완료 — 진단 및 계보 추적 성공 | [exp32_lineage_diag](exp32_lineage_diag.md) |
| carve_loss_design | (분석만) free-space carve 기반 신규 loss 설계, 수동 라벨 리그전 Round 1~10 | 학습 없음 | 완료 — AUC 0.98, 예산 0.75%로 recall 55%, exp38/39 구현 완료 | [round8_carve_loss_design](../rounds/round8_carve_loss_design.md) · [요약](../rounds/round8_carve_loss_summary.md) |

## Carve Loss 학습 검증 트랙 — exp38~40 (07-12, baseline exp30/30r)

| Exp | 한 줄 설정 | PSNR@30k | region_n/가시 | Verdict | 카드 |
|---|---|---:|---:|---|---|
| exp30r | baseline 재현 (노이즈 측정) | 32.579 | 3,749 / 180 | PSNR 노이즈 ±0.33dB 실측 | [exp38-40](exp38_40_carve_track.md) |
| exp38a | soft0.05+prune+gate | 32.266 | 559 / 27 | 억제 최강, -0.3dB 과비용 | 〃 |
| exp38b | prune+gate만 | 32.663 | 1,744 / 187 | soft가 가시 먼지 주역임을 분리 | 〃 |
| exp38c | softlite0.02+prune+gate | 32.557 | 946 / 33 | PSNR 무손실 스위트스팟 | 〃 |
| exp39 | MPS 트랙 carve (full soft) | 32.666 | (MPS) 가시 96→2 | MPS 전이 성공 | 〃 |
| exp40br | 챔피언 재현 | 32.448 | 462 / 25 | 재현 확인 | 〃 |
| **exp39b** | MPS softlite+force | **32.913** | (MPS) 가시 **0** | **MPS 채택** | 〃 |
| exp40a | prune+gate+**force** | 32.667 | 1,309 / 134 | 3D force 부활 실증 (무비용) | 〃 |
| **exp40b** | softlite+prune+gate+force | **32.576** | **498 / 28** | **채택 — 챔피언 레시피** | 〃 |

> exp30~37 전체 완료 (2026-07-09). 큐 진행 중 발견된 자동 체인 중복 실행 버그와 run-to-run 노이즈(±0.24dB)는 카드 참조.

## 계획 및 신규 트랙 카드

| Exp | 내용 | 상태 | 카드 |
|---|---|---|---|
| **VIGS ERCB ablation** | `custom/main@8c094371` 동일 strict recipe 6-scene closure: vanilla 대비 +1dB **4/6**, raw 5/6 승, scene 평균 **+1.178dB**, 1,109-view 가중 **+1.247dB**. `slow-straight-1` −1.999, `square-1` +0.289는 실패 | **대부분 장면 +1dB 전이 GO — 초희소 service·loop drift·장기 gate-off 품질손실은 잔여** | [running log](VIGS_ERCB_ablation/README.md) |
| **ERCB exp02 latency** | 물리 RGB capture 시각부터 첫 applied optimizer update까지를 service latency로 정의하고 research의 7개 후보를 전부 구현. 대표 2-scene 선별·`ego-drive` tuning 후 Debt A/Service Field를 6-scene 고정 transfer. 처리 가능 4-scene p95는 RR 25.988초→18.526/18.540초로 약 29% 감소했지만 held-out PSNR은 RR 19.025→18.548/18.471dB(−.477/−.555), 각각 1/6·2/6 승. pair는 optimizer cadence 절반으로 추가 악화 | **Latency 개선 / final-quality 우월성 NO-GO / RR 지배 후보 없음** | [exp02](ERCB_ablation/exp02/RESULT.md) |
| **ERCB ablation** | UTMM validation bundle 6 scene에서 seed-0 bundle-wide tuning 후 `K=8,rho=.75,gamma=log1.5`를 고정해 seed1/2 검증. RR→ERCB held-out PSNR **21.9148→21.9845dB(+.0698)**, worst-Q1 +.1062dB, RR-hard-Q1 +.3321dB, 11/18 승이며 seed 평균은 모두 양수. 단 fast-straight −.2957dB, count CV .8030→.9389 악화. 이전 RPNG/UTMM artificial-init transfer NO-GO도 같은 카드에 보존 | **UTMM-tuned binary ablation 완료 / 평균 소폭 GO / count-equality 주장은 NO-GO / fixed-pose·init scheduler-isolation 및 same-bundle validation 한계** | [ERCB ablation](ERCB_ablation/README.md) |
| **exp76** | threshold 없는 mean-normalized interval Softmax RR를 305/12F에서 `exp(gamma)=1.0~2.0` 9점 sweep. 공통 `K=8,gamma=log1.25`는 2 scene×2 seed에서 causal RR 대비 overall **4/4 승리**(평균 +.089dB), worst-Q1 +.233dB, RR-hard-Q1 +.660dB이나 exp75 best 대비 overall −.354dB·late −.632dB. count CV .904와 temporal entropy .973은 우수했지만 품질을 설명하지 못함 | **RR에는 소폭 우세 / exp75 최고식과 호각 실패 / 단순 normalized 대체안 기각** | [exp76](exp76/exp76_mean_normalized_softmax_ablation.md) |
| **exp75** | growing-pool causal replay에서 단일 relative-floor interval softmax RR(`K=8, rho=.5, gamma=log3`)를 pure-online zero-tail로 검증. 305/12F/3F×2 seed에서 causal RR 대비 held-out overall **6/6 승리**(평균 +.326dB), worst-Q1 +.654dB, late-third +.522dB. count CV .979→.883, 128-step temporal entropy .972→.962, 20,512 interval block duplicate 0. 추가 1253은 overall 동률(−.009dB)이나 lower-tail/late 개선 | **3-scene goal 달성 / fixed-pose offline evidence / 실제 strict VIGS 이식 전** | [exp75](exp75/exp75_block_weighted_rr_30k_loop.md) |
| **exp74-30k** | exp74의 11.88k가 densify 종료 15k에도 못 미친다는 사용자 지적을 반영해 1253/305 핵심 arm을 30k 재검증. count-balanced는 causal RR 대비 전체 1253 −0.319dB, 305 −1.015dB이나 후반 third는 각각 **+0.078/+0.998dB**. 1253 static all-at-once RR는 35.301dB로 여전히 최고 | **조기 NO-GO 정정: late-bin 회복 확인 / 전체 RR 역전은 아직 실패 / anytime curve 필요** | [exp74 30k 정정](exp74/exp74_offline_causal_full_pool_scheduler_ablation.md) |
| **exp74** | 3dgs-custom에서 모든 dense frame을 admission한 fixed-pose offline/causal replay를 구현. 1253에서 causal RR 32.220dB 대비 count-balanced RR 30.402dB, 305에서 33.378→30.443dB. count CV는 0.80→0.05~0.07로 개선됐지만 temporal entropy와 품질이 악화. static all-at-once RR는 32.660dB로 causal RR보다 +0.440dB | **큰 pool이면 count fairness가 RR을 이긴다는 가설 기각 / raw count equality NO-GO** | [exp74](exp74/exp74_offline_causal_full_pool_scheduler_ablation.md) |
| **exp73** | interval별 무료 bootstrap+maturity-gated admission을 최초 seed 1장 이후 \(\kappa\) dense update당 pending view 1장을 받는 token-only 정책으로 교체. 7 run·526 admission poll에서 \(A_{paid}(u)=\lfloor u/\kappa\rfloor\) 오차 0. 공통 \(\kappa=22\)는 1253 2회 평균 27.711dB(baseline 대비 +0.003)와 305 28.815dB(−0.119)로 품질 기준 통과했지만 selection CV는 0.951/0.942로 악화. 1253 pool −34.8%는 gate 제거가 아니라 interval bootstrap 제거와 pacing의 결합 효과 | **token law 실증 / \(\kappa=22\) 첫 2-scene 후보 / 순수 gate 효과 미분리 / scheduling 미해결 / default 보류** | [exp73](exp73/exp73_gate_free_token_admission_real_ablation.md) |
| **exp72-305** | 선정 후보 \(K=128,\beta=0.02\)를 305호 2,688-frame에서 fresh paired 검증. baseline→후보 PSNR 28.934→28.558dB(−0.376), pool 674→528(−21.7%), streaming replay 14,246→10,859(−23.8%), selection CV 0.470→0.643. entropy 0.9969여도 gate 결합 때문에 admission·최종 균등성이 악화 | **305 일반화 실패 / candidate 지위 철회 / NO-GO 강화** | [exp72 추가 결과](exp72/exp72_entropy_count_scheduler_real_ablation.md) |
| **exp72** | count-Gibbs 분포를 K-view 비복원 block에 적용한 실제 final-v7 A/B. K=128, β=.02는 1253 −0.084dB·rot +0.362dB, wall 차이 &lt;0.04%, entropy ≥99.84%로 품질은 보존했지만 rot middle/first 0.758→0.520 및 기존 maturity gate 유지로 lifetime 균등화·pool-independent admission은 실패 | **opt-in 유지 / production·논문 방법론 보류** | [결과](exp72/exp72_entropy_count_scheduler_real_ablation.md) |
| **exp71** | growing-pool에서 (1) 초기↔\(T/2\) lifetime-count equality, (2) pool-size-independent GPU-token admission, (3) full-pool shuffle entropy/gradient mixing을 공동 정의. \(B=8/16/32\), \(\kappa=16\)~4096, \(\beta=0\)~\(\infty\) sweep 결과 세 조건의 feasible point는 0개. token admission은 정확히 작동했지만 maturity gate는 빠른 부하에서 목표의 18.9%까지 붕괴 | **문제 전제 충돌 확정 / valid beta 없음 / objective 재선택 필요** | [exp71](exp71/exp71_joint_admission_scheduler_problem.md) |
| **exp70** | score-free detached opacity loss 구현. 1.5× baseline에서는 alpha가 manual-region visible을 −9~15% 줄였지만, 교정된 **final-v7 RTX5090 original 1× + legacy carve 완전 off**에서는 control/alpha/NLL이 28.148/27.706/27.792dB, nominal floater 148/161/164, dilated 383/401/407로 두 loss 모두 악화하고 scale&gt;1m giant splat도 1→206/56으로 증가. 단 total replay 차이는 EOS rematuration 착시였고, 이를 제외한 streaming update 5,910/6,089/5,956·시간 69.064/69.098/69.066초로 연산비 증가는 사실상 없음 | **final-v7 final-map NO-GO / fixed online schedule로 action 재검증** | [loss·결과](exp70/exp70_score_free_detached_termination_loss.html) · [1× evidence](exp70/evidence/exp70_v7_1x_legacyoff_seed0_summary.json) · [문제 정의](exp70/exp70_detached_floater_problem_formulation.html) |
| **exp70-S** | growing causal pool의 age-adjusted quota와 gradient mixing을 12k update×48 seed×5 growth pattern에서 비교. ME-QARR는 sub-one discrepancy+고정 pool exact uniform reshuffling, ME-BDS(C=2)는 worst exposure &lt;2회에서 IID급 short-window mixing을 달성 | **scheduler-only 분석 채택; 실제 VIGS A/B 전** | [분석](exp70/exp70_max_entropy_view_scheduler_sim.md) |
| **exp70.5** | vanilla VIGS-SLAM(무수정, `VIGS-SLAM-vanilla-check`)에서 depth loss(alpha)·normal loss(lambda_dnormal) 2x2 ablation, aria1253 pure_online. depth OFF/normal OFF가 4개 중 최고(23.14dB), 둘 다 개별 ON이 각각 손해(−0.70/−1.17dB) — n=1 잠정, 반복 검증 필요 | **측정 완료, 해석 잠정(반복 검증 대기)** | [exp70.5](exp70/exp70.5_vigs_vanilla_depth_normal_loss_ablation.md) |
| **exp69** | mature dust GC, FIFO epoch, pose-balanced active+unbounded archive를 strict 1.5× 세 장면에서 분리 검증; active/archive는 1253/305 photo 통과에도 paired 12F −0.92dB·305 geometry 소폭 악화로 기각 | **완료(범용 후보 기각)** | [결과](exp69/exp69_result.html) |
| exp43 | 교차 장면 완주: rot 점수 AUC 0.98·pseudo-label 정밀도 100% / 305 **depth-anchor carve 재현 성공**(먼지 -83%·PSNR 동급) / 실패 5건 정직 기록 — 결론: carve 성패=앵커 품질 | **완료** | [exp43](exp43_cross_scene_plan.md) |
| exp45 | 채택 큐 4종: 45a 노출 기각(-6dB)·45b dynamic 조건부(깨끗한 init 전제)·44e3 보류(먼지 ×4)·45c progressive resolution 진행 중 | 진행 | [exp44 카드 참조](exp44_fast_geometry_plan.md) |
| exp46 | basin 재프레임: floater=photo loss의 정당한 숏컷 분지 → 압력 대신 '올바른 geometry를 가까운 basin으로'. (a)도달불가=init/(b)환원불가=appearance 이분법 + 다음 실험 7축(원거리 photometric 감쇠 포함) | **완료** | [exp46](exp46_basin_reframe_plan.md) |
| exp47 | 속도 최적화 트랙: 품질 하한 고정하고 속도만 — S1 cuda·S2 carve저빈도·S3 iter·S4 keyframe subset·S5 중간budget. incremental per-chunk 레시피 확정 목적(목표 5분 내) | **완료** | [exp47](exp47_speed_track_plan.md) |
| **exp44** | **고속 geometry 트랙 완료 — 44h 레시피 채택** (스냅 init+densify≤3k+carve, 32.08/7.5분) · 품질 기함 44f(32.67/14분) | **완료** | [exp44](exp44_fast_geometry_plan.md) |
| exp48 | Incremental 3DGS: PPM K=3 + RoMA (Hybrid) 및 온라인 루프 홀인 Selective Opacity Reset 도입 (18.23dB). 종결 — eval 버그(llffhold-8이 test.txt 무시) 규명, 진짜 벽은 저텍스처 영역 + vanilla 3dgs가 online에 안 맞는 틀 | **종결** | [exp48](exp48_incremental_plan.md) |
| exp49 | Photo-SLAM(ORB-SLAM3+GS, CVPR24) 이관: opacity_reset off·상수 LR·times-of-use 슬라이딩 윈도우로 exp48 문제를 설계로 회피한 검증된 online baseline. 빌드 완료(Blackwell+CUDA12.8 호환패치). replay로 Fisheye624 우회 → 배치 baseline → incremental → 방법론 이식 | 계획 | [exp49](exp49_photoslam_plan.md) |
| exp50 | DiskChunGS: Out-of-Core 디스크 스왑 SLAM. B1에서 Fisheye624 라이브 트래킹 root-cause 2건 수정(하드코딩 static_cast, KannalaBrandt-only 게이트) 후 최초 성공(리셋 9~31→0, 매칭 33~76개 지속). 다음: RGB 매핑 카메라 분리 주입 | 진행 | [exp50](exp50_diskchungs_plan.md) |
| exp51 | Incremental mapping 30dB+로: 축A+B(25.29dB)+축C(밀도 무효과)+축F(예산 3.3배→25.59, 소폭). **시각진단 확정: 잔여 갭 = depth-init 바늘형 floater**(GT/render 대조로 확인) — 배치의 carve loss(exp38~44d2 검증됨)를 incremental에 이식하는 축E가 다음 | 진행중 | [exp51](exp51_dense_supervision_plan.md) |
| exp52 | VIGS-SLAM(ECCV2026) 클론·빌드(6가지 환경 이슈 해결)·평가. 소스 분석으로 exp51 가정 검증(isotropic loss+scale clamp 신규, opacity reset은 기본 config 비활성, init dedup은 dead code 확인, normal supervision 신규 발견). 폴리싱 포함 베이스라인: 1253 held-out 26.85dB·keyframe 30.90dB. **`--pure_online` 실측(정정): 순수 온라인 PSNR 22.73dB — 우리 exp51 축A+B(25.29dB)보다 낮음.** 함수 단위 병목 분해(PGBA 신규 발견): gs_mapping rasterize+backward가 최대 원인. **imu_cpp 빌드(IMU 프리적분 −98.5%)+TensorRT 3종(Omnidata −77%·fnet −78%·update_module 효과없음) 전부 적용해 온라인 루프 209.4→180.1초(−14.0%, PSNR 무변화)** — 그런데도 gs_mapping 비중은 30.2%→50.2%로 오히려 커짐(다른 게 줄어든 결과) → gs_mapping을 0으로 줄여도(180.1−90.5=89.6초>65.1초 녹화시간) 순차 구조로는 실시간 불가임을 계산으로 확인, **구조적 전환**: 업스트림 레이스 컨디션(`remove_all_gaussians()` 락 누락, IMU 재초기화 시 `_gs_worker`와 경합) 발견·수정 후 `_gs_parallel: true`(비동기 tracking/mapping 오버랩) 검증 — **온라인 루프 180.1→133.0초(−26.1%), PSNR 무변화, 매핑 비용의 66%가 GPU 유휴시간에 흡수됨**. 여전히 실시간의 2.04배(2.77배에서 개선) — 완전 해결은 아니나 유효한 구조적 레버 확정. **트래킹 전용 fps(20/10/5) 스윕으로 exp50(ORB) vs VIGS 비교**: ORB는 keyframe당 비용 고정(~25ms)이고 keyframe 개수도 fps에 어느 정도 비례(−20.8%)해서 fps 낮추면 실시간 여유가 커짐(20fps부터 이미 0.68배), VIGS는 5fps까지 내려도 여전히 미달(1.11배) — **⚠정정: 원인은 "프레임당 비용 증가"가 아니라 call당 비용은 거의 안 변하고(bundle_adjust만 12.7→15.1ms 소폭↑) keyframe 개수 자체가 fps와 거의 무관(−6.6%, optical-flow 임계값 기반)해서 총 작업량이 안 줄기 때문(frontend 총합은 오히려 48.3→32.9초로 감소, "프레임당 평균"이 분모 착시였음)**. 트래킹 아키텍처도 exp50 경로가 실시간엔 유리함을 확정. **원 논문 대조**: DROID-SLAM 자체도 "2-GPU + 다운샘플/프레임스킵 조건부 실시간"(TartanAir에선 원 저자도 8fps로 실패)이었고, VIGS 저자 공식 벤치마크(RTX 5090)도 tracking만 39.83fps(여유)·tracking+mapping 12.02fps(미달)로 **"매핑이 병목"이라는 우리 결론을 저자 자신의 최상급 GPU 수치가 독립 재확인**. **MPS 기준 evo_ape로 궤적 정확도 비교: 스케일 보정 후(Sim3) ORB 13cm vs VIGS 1.3cm — VIGS의 dense correlation 트래킹이 형태 정확도 10배 우위**(단 절대 스케일은 IMU 1회성 초기화발 편향 3~5%, ORB는 캘리브레이션된 스테레오 기준선이라 더 안정). 소스 추적으로 원인 규명: VIGS는 Gaussian mapping의 depth supervision을 별도 monocular 추정이 아니라 **포즈와 같은 BA에서 공동 최적화된 `disps_up`을 그대로 사용**(`vigs.py:169`) — 우리 exp50/51의 "트래킹과 무관한 독립적 depth prior" 구조와 근본적으로 다름, floater 문제의 뿌리와 동일 메커니즘. **⚠중대정정(07-20): "27초 오버헤드"의 미계측 21.1초를 실제로 계측(pbar/save_trajectory 추가 계측→다 합쳐 0.14초, 가설 기각)하다가 진짜 원인 발견 — `demo.py`의 리더 프로세스 `time.sleep(20)`이 타이밍 마커보다 먼저 실행되는 `reader.join()` 위치 버그로 모든 "온라인 루프 총합"에 인위적 20초가 섞여 있었음(구성요소별 개별 수치는 무관, fps스윕/evo비교도 무관). 코드 수정 후 재검증: 순차 150.56초(2.31배, 기존 2.77배)·gs_parallel 98.94초(**1.52배**, 기존 2.04배) — 오버랩 효율도 66%→88.3%로 상향, 미계측 잔여는 21.1초→0.2초로 사실상 해소**. **GS Mapping 루프 최대 세분화(12단계, `_process_track_data_impl` 전체로 계측 범위 확장)**: rasterize+backward+loss_compute가 81.4%로 여전히 지배적(process_track_data 부가작업은 4.2%뿐, 무시할 수준) — 다만 `map()` 내부에서 기존 5단계 합과 총합 사이에 **12.0초(12.9%)의 새 미계측 포켓 발견**(isotropic loss 계산+viewpoint 샘플링으로 추정, 다음 계측 후보) | 진행중 | [exp52](exp52_vigs_slam_eval.md) |
| exp53 | Frontend Tracking(exp52에서 확정한 진짜 실시간 병목) 자체를 가볍게 만드는 트랙. **전체 완료**: 축A(`iters1`/`iters2`, 4/2→1/0, −20.7%)·축B(`motion_filter.thresh` 2.4→3.6, −15.4%, keyframe 발생률 자체를 줄여 tracking+mapping 양쪽에 동시에 걸리는 최대 레버)·축C(`frontend_window`/`radius` 25/2→15/1, −1.7%) 전부 채택, evo APE(Sim3)는 축A 세 단계 전부 1.59cm로 고정 후 축B+C에서 1.93cm까지 소폭 상승(ORB 13cm 대비 여전히 6.7배 우위). 축D(correlation 해상도)는 조사 결과 사전학습 GRU 가중치에 shape가 고정 결합돼 **재학습 없이는 구현 불가로 판정**(실행 안 함), 축E(커널 튜닝)는 목표 달성으로 불필요. exp54와 통합한 최종 레시피 = **61.34s, 실시간 배수 0.94배(1.0배 미만 최초 달성)** | 완료 | [exp53](exp53_frontend_realtime_plan.md) |
| exp54 | GS Mapping 연산 시간 ablation(exp52의 "rasterize+backward+loss_compute=81.4%" 발견을 구체화). **7축 전부 완료**: 축1(`pcd_downsample` 64→128) 채택(−3.3%) · 축2(`pcd_downsample_init`)·축3(`map() iters`)·축5(`max_viewpoints`) 기각(효과 없음/역효과, 축3에서 tracking이 91% 비중임을 규명해 exp53 우선순위 근거 마련) · 축6+2 결합(densify 공격성 3배 상향+init 밀도 2배 희석) 실험으로 "상쇄" 가설은 확인했으나(최종 gaussian 수 축1보다도 적게 억제 성공) 시간은 그대로라 **이 지점에서 밀도/예산 축 전체가 소진됐음을 확정**, 기각 · **축4(render_downsample) 신규 구현**(`vigs.py::call_gs`에 매핑 전용 다운샘플 추가, eval 해상도 불일치 버그도 수정) — 검증된 유효 레버(−4.2%/−0.8dB)지만 이미 실시간이라 미채택, 코드만 보존 · **축7(PPM) 신규 구현**(`gaussian_model.py`에 Sobel-gradient 기반 content-adaptive 샘플링 이식, `Dataset.ppm_sampling` 플래그) — 동일 예산에서 PSNR 순개선(+0.16dB, exp44 "PPM=품질 왕" VIGS에서도 재현), **채택**. exp53과 통합한 최종 레시피 = **61.34s, 실시간 배수 0.94배** | 완료 | [exp54](exp54_gsmapping_speed_ablation_plan.md) |
| exp55 | 내용-적응 per-frame gaussian 예산(Sobel↔PSNR-이득 상관 실측 r=0.538) + carve loss 이식. **Phase 1+2+3 전부 실행·채택**: Phase1(캘리브레이션 2런)로 배율곡선(0.91~1.57x) 도출 → Phase2(베이스 128→256/init 32→64 + 내용-적응 배율 + per-keyframe 명시적 cap `enforce_kf_caps` 신규)로 **평균 gaussian −35.9%, 최종 −35.3%, PSNR/궤적 손실 없음(오히려 소폭 개선)** — 사용자 목표(평균 gaussian/frame 감소) 달성. Phase3(carve loss 온라인 근사, depth-violation 전용 신규 설계) — 기존 region GT가 1253/VIGS 좌표계에 적용 불가함을 확인 후 **carve_loss.py 자신의 검증된(AUC 0.98) 신호를 오프라인 진단 지표로 새로 구현**(`exp55_score_carve_vigs.py`, 신규 재사용 도구)해 직접 검증 — 가시 floater 수/비율/평균 score 네 지표 전부 일관 개선(−4~8%), PSNR·시간 비용 없음 → `carve_lambda=0.05` 채택. Phase 2Q는 미실행 **부록(07-23): 직렬 실행 분리 결과 tracking 27.9s/mapping 80.1s — exp54 "tracking-bound"는 병렬 한정 결론이었음 발견(GPU 경합으로 병렬 tracking이 1.8배 부풀고, 큐 드롭으로 mapping 호출이 직렬 대비 1/5로 줄어든 합성 결과)**. **부록(07-25): 남는 실시간 예산(5.3s)을 `map()` iters(10→15/20)에 재투자 시도 — 기각(큐 드롭으로 처리 keyframe 수만 줄어 PSNR 개선 없거나 예산 초과), 다음 후보는 `queue_size` 확대** | Phase1+2+3 완료 | [exp55](exp55_adaptive_density_carve_plan.md) |
| exp56 | mapping 고정비(픽셀/커널-launch) 절감 — "gaussian 개수를 줄여도 왜 안 빨라지나"를 기존 `_Sect` 타이밍 계측 재분석으로 규명(신규 실행 없이 Phase 0): 직렬 순수 map() 68.16s 중 rasterize 40%+backward 34%+loss_compute 24%로, loss_compute는 순수 픽셀 고정비(N-무관)이고 rasterize/backward도 이 gaussian 수 규모(85k~130k)에선 고정비가 N-비례 항을 압도함을 exp54 축6+2·exp55 Phase2의 반복 관측과 연결해 확정. **Phase 1(map() iters 10→7→5 스캔)에서 `iters=7` 채택** — 시간 −16.1%(59.80→50.17s)·PSNR mean/kf 둘 다 +0.21dB 개선·map() 성사 횟수 22→26회 증가라는 전 지표 동시 개선(오늘 오전 iters↑ 실험과 대칭 결과: coverage가 반복 깊이보다 지배적임을 재확인). Phase 2(이 새 baseline 위에 `render_downsample=2` 재검증)는 기각(시간 이득 −1.7%뿐, PSNR −0.8dB 손해). exp53+54+55+56 최종 = **50.17s, 실시간 배수 0.77배, PSNR 22.82/23.16(exp55 대비도 개선)**. **Phase 3(coverage/GPU경합 직접 겨냥 3축, 전부 기각)**: `queue_size` 2→4는 역효과(시간·PSNR·coverage 셋 다 악화 — 드롭 정책이 버퍼 크기와 무관하게 "최근 N개만 유지"라 버퍼가 클수록 더 오래된 packet부터 처리하게 됨). CUDA Graph는 조사 후 구조적 부적합 판정(keyframe마다 gaussian 개수·카메라 구성이 달라 매번 재capture 필요, 비용이 iters=7 루프 절감분을 상회할 가능성 높음 — 구현 안 함). mapping 전용 CUDA stream 분리는 **실행 중 CUDA illegal memory access로 크래시**(레포 전체에 명시적 stream 관리가 없어 tracking/mapping이 legacy default stream의 암묵적 교차동기화로 우연히 안전했던 것으로 추정 — custom rasterizer가 진짜 동시실행엔 미검증 상태, 안전하게 원복·GPU 상태 정상 확인). **부록**: "병렬 경합 때문 아니냐"는 재확인 요청에 순수 직렬로 재검증 — render_downsample=2가 직렬(경합 0)에서도 rasterize/backward/loss_compute를 겨우 1~3%만 줄임(병렬 6~8%보다도 작음) — 경합 가설 기각, "데이터量은 거의 공짜, 커널 launch 횟수(iters)만 지배적"이 병렬/직렬과 무관한 구조적 사실임을 확정(iters 10→7 직렬 비교는 −20~24%로 확실히 비례). **Phase 4(신규, 이 세션 최대 발견): `map_call` 세부 로그(iters/n_view/n_gauss)를 처음 집계해 map() 호출 26회 중 단 2~3회(맵 최초 초기화+IMU 재초기화 시 `remove_all_gaussians()`로 맵 전체 삭제 후 재구축, iters=90~131)가 mapping 전체 시간의 49%를 차지함을 발견** — `Training.init_itr_num` 1050→600으로 낮춰 **추가로 시간 −6.2%(50.17→47.08s), PSNR 사실상 무손실(kf +0.05dB), map() 성사 26→30회** 채택(300은 PSNR −0.35~0.44dB 실손실로 기각). exp53+54+55+56 최종 = **47.08s, 실시간 배수 0.72배(exp55 대비 −21.3%), kf PSNR 23.21(+0.26dB)**. **Phase 5(신규): 세션 전체 548개 map() 호출의 map_call 로그를 처음 집계해 회귀분석(`scripts/analysis/exp56_fit_timing_model.py`) — 직렬 R²=0.93~0.998로 rasterize/loss_compute/backward/optimizer_step 관계식 도출, `iters×n_view`(반복×카메라 수)가 압도적이고 gaussian 수·해상도는 부차적임을 계수로 확정(실측 5% 이내 검증). n_view 의존 원인도 코드로 규명: 원본 3DGS render()가 카메라 1대 전용(batch 미지원)이라 매 카메라마다 고정비를 새로 지불 — 다음 후보(rasterizer batch화, 뷰당 고정비 최대 91% 절감 가능하나 CUDA 소스 수정 필요해 고위험)로 식별**. **Phase 6: iters↓·n_view↑ 재배분(같은 view-op 예산) 품질 가설을 실측해 기각 — dead config였던 Training.window_size를 실제 로직에 연결해 테스트, 시간은 회귀식대로 거의 무변화지만 PSNR이 −1.1dB→−3.5dB로 window를 키울수록 단조 악화(프론티어 gradient 희석으로 분석), window_size 기본값 10 원복**. **Phase 7(신규): 프론티어 window는 그대로, 과거-뷰 곁눈질 개수(include_global의 하드코딩 2를 Training.n_global_views로 config화)만 늘려 재검증 — Phase 6과 정반대로 PSNR mean/kf 둘 다 개선(+0.24/+0.22dB), 시간 비용은 무시할 수준(+0.25%) → n_global_views=6 채택. exp55 baseline 대비 최종 누적(Phase 7): **47.20s(−21.1%), PSNR mean +0.36dB·kf +0.48dB, 궤적도 개선**. **Phase 8: 사용자 요청으로 rasterizer batch 구현 조사 — torch.profiler로 확인해보니 진짜 CUDA 커널 비용이라 batch화(forward.cu/backward.cu 수정)는 그래디언트 위험이 커 보류, 대신 프로파일링 중 발견한 안전한 부수 최적화(Camera.world_view_transform/full_proj_transform/camera_center가 pose 불변인데도 매 view마다 torch.linalg.inv() 재계산되던 것을 캐싱, update_RT()에서만 무효화) 적용 — **시간 −3.0%, PSNR +0.52/+0.45dB, map() 성사 +38%, 이 세션 최고 ROI**. exp55 baseline 대비 최종: **45.79s(−23.4%), 실시간 배수 0.70배, PSNR mean +0.88dB·kf +0.93dB**. **Phase 8b(사용자 요청 "물어보지 말고 끝까지"): batch를 실제 구현(기존 단일-카메라 CUDA 커널은 안 건드리고 C++에서 카메라 수만큼 루프, forward bit-exact·backward float32 잡음 수준으로 검증) — 1차 실전 실행에서 PSNR 붕괴(6.65dB) 발견, 원인은 render_batch()의 depth 텐서 shape 불일치(get_loss_normal이 매 호출 조용히 실패, except가 은폐 — 격리 검증이 이 project-specific loss를 안 건드려서 못 잡음). 수정 후 재실행: 크래시 없고 PSNR도 소폭 개선(23.55/24.07)했지만 **시간은 개선 없음**(정규 호출 평균 761.6ms→755.7ms, <1% 차이) — "진짜 병목은 CUDA 커널 실행 자체"라는 Phase 8 예견이 실측으로 확정, `batch_render` 채택 안 함(기본 false 원복, 코드는 향후 커널-레벨 batch화 기반 자산으로 보존)**. **Phase 9(신규, 07-28, exp56 후속분석): "고정비가 지배적" 결론을 통제된 단일-view-op 마이크로벤치마크(카메라 1개 고정, N=1만~9만 서브샘플)로 재검증 — torch.profiler 이중계산 버그(C++ 확장 wrapper가 자식 커널 시간을 self_device_time에 중복 합산, 8.39ms vs 순수 wall-clock 3.43ms) 발견·wall-clock으로 교차검증 후, forward는 N-비례가 56.4%·backward는 84.6%(N=90,770 기준, R²=0.988/0.999)로 실제로는 N이 상당히 유의미함을 확인 — Phase 0/5의 "N-무관 고정비 지배" 결론은 다변량 실측 로그에서 여러 항목이 섞여 희석된 결과였을 가능성. 지도교수가 제안한 visibility 기반 backprop 선별 방향이 이 결과로 재확인됨(backward의 N-slope이 forward의 3.3배) → exp57에 "coarse frustum pre-filter로 유효 N 절감" 항목 공식 추가**. **Phase 10(신규, 07-28): `render_filtered()`/`frustum_prefilter()` 실제 구현(기존 `render()` 무수정, host-side에서 gaussian 부분집합만 뽑아 넘김) — 수치 검증(Phase8b 기준, atomic 노이즈 수준 일치) 통과, length=300 라이브 스모크 통과 후 1253 전체 실측: **온라인 루프 −0.89%(45.79→45.38s, 잡음 수준), PSNR −0.35/−0.29dB, map() 성사 36→30회(−17%) — 기각.** `map_call` 로그로 원인 진단: rasterize avg/call이 오히려 139→290ms로 2배 느려짐 — 필터링 자체(행렬곱+5개 인덱싱 연산, 뷰마다 최대 17회)가 만드는 추가 커널 launch 비용이 줄어든 gaussian 수만큼 아낀 시간보다 컸음. Phase 9를 뒤집는 게 아니라 오히려 재확인: "N-비례가 유의미하다"와 "host-side에서 N을 줄이면 공짜"는 다른 명제 — launch 자체가 비싸다는 Phase 9 결론상 필터링을 CUDA 커널 내부(preprocessCUDA)에 융합해야만 진짜 이득이 나고, 이는 결국 처음부터 고위험으로 미뤄온 forward.cu/backward.cu 직접 수정과 같은 결론으로 수렴. `frustum_prefilter` 기본값 false 유지, 코드는 자산으로 보존**. **Phase 11(신규, 07-28, 사용자 요청 "renderCUDA만 커널 레벨로 batch화"): Phase 8/8b/10이 계속 고위험으로 미뤄온 forward.cu/backward.cu 직접 수정을 범위를 좁혀 시도 — renderCUDA(forward+backward)만 grid.z=camera로 진짜 배치, preprocessCUDA/정렬/computeCov2DCUDA(SE3 포즈 그래디언트 dL_dtau가 있는 곳)는 카메라별 host-loop 그대로 무수정(grep으로 dL_dtau가 renderCUDA엔 없음을 구현 전 확인). 구현 직후 원인불명 segfault(compute-sanitizer 0 errors인데도 크래시) → gdb 백트레이스로 정확히 진단: focal_x_t/focal_y_t를 GPU 텐서로 할당해놓고 host for문에서 CPU가 GPU 포인터를 직접 역참조하던 버그(호스트 벡터에 채운 뒤 한 번만 업로드하는 방식으로 수정, forward/backward 두 곳 다). 재빌드 후 Phase 8b 기준 검증 통과(forward bit-exact, backward 상대오차 atomic 노이즈 수준), length=300 스모크 통과 후 1253 전체 실측: **vigs_track_total 45.79→44.00s(−3.9%), PSNR 23.49/23.88→23.46/23.98(무손실), rasterize avg/call 139.4→66.8ms(−52.1%, 배치화한 부분만 놓고 보면 launch 비용이 정확히 절반) — 채택.** backward는 거의 그대로(348.9→368.5ms) — 배치 안 한 BACKWARD::preprocess가 여전히 backward 시간을 지배하기 때문(다음 후보로 식별, 단 dL_dtau를 직접 건드려야 해서 고위험). Phase 8b/10과 달리 이번엔 시간·PSNR 모두 손해 없는 첫 배치화 계열 순이득. Training.kernel_batch_render(opt-in, 기본 false) 신규 플래그로 배선** | 완료 | [exp56](exp56_mapping_fixedcost_reduction.md) |
| exp57 | 1차 목표 **strict-disjoint held-out 27dB**(MPS 금지, RGB+IMU only, fixed 1.5×, tail 0). late-iters3 3회는 **27.004/26.949/26.572dB**, 최초 27은 1/3회. static 2단계는 기각. causal replay feedback target5100은 5,233 update지만 low=0/high=38로 제어가 작동하지 않아 26.800; target6500 보정이 다음 | **strict-disjoint 27.004dB 단일 최고 / 반복 27 미달** | [exp57](exp57_causal_background_polishing_plan.md) |
| exp57 adaptive6500 | causal replay target6500은 low13/high25로 실제 제어하고 5,310 update를 확보했지만 fixed **26.807dB**. 처리량 feedback만으로 topology/gradient 변동을 못 잡아 축 종료. 1차 목표는 계속 RGB+IMU-only strict 27dB 반복 달성 | **기각 — deadline/tail0 계약 통과, 27 반복 미달** | [exp57](exp57_causal_background_polishing_plan.md) |
| exp57 freeze1060 | static late-iters3에서 freeze만 1050→1060. fixed **26.720dB**, 4,747 update, 77,007GS, 97.203s/tail0. 후반 bin도 23.415/19.850이라 coverage 개선 없음; freeze1040/1060 양쪽 실패로 경계 스캔 종료 | **기각 — freeze1050 유지** | [exp57](exp57_causal_background_polishing_plan.md) |
| exp57 quota5200 | frame 진행률별 background 누적 step 상한을 두는 causal quota 구현. 두 run fixed **26.859/26.676dB**(평균 26.767), update도 4,676/4,305로 갈림. tail0에서는 부족분 catch-up 불가하고 frame700 전 topology가 이미 달라 분산 억제 실패 | **기각 — opt-in/default off** | [exp57](exp57_causal_background_polishing_plan.md) |
| exp57 pose-variance 진단 | quota 두 run은 keyframe 116개 timestamp가 동일하지만 xyz 평균 절대차 0.60/1.17/1.88cm, 최대 3.83cm. background 시작 전 kf17에서 이미 최대 1.03cm divergence → 다음 대상은 tracker/PGBA 수치 변동·regular GS GPU interleaving | **원인 범위 축소** | [exp57](exp57_causal_background_polishing_plan.md) |
| exp57 tracking-only 대조 | GS 제거 두 run은 keyframe 111개 동일, xyz 평균/최대 차이 1.05/3.82mm. mapping 동시 실행은 최대 38.3mm라 GS interleaving이 pose 변동을 크게 증폭. no-mapping `_gs_queue` guard 버그 2곳 수정 | **원인 확정 — GS/IMU-init interleaving** | [exp57](exp57_causal_background_polishing_plan.md) |
| exp57 IMU scale quantum0.005 | online raw metric scale만 causal 반올림. 3회 모두 1.040, fixed **26.728/26.755/26.712dB**(평균 26.731, 범위 0.043). 분산은 약 10배 감소했지만 평균 품질 −0.111dB·27 미달 | **품질 레시피 기각, opt-in A/B stabilizer** | [exp57](exp57_causal_background_polishing_plan.md) |
| exp57 window8 | frontier window 10→8 + IMU quantum0.005. fixed **26.845dB**, 5,023 update, 97.242s/tail0. window10 quant 평균보다 +0.114dB이나 27 미달이고 applied scale도 1.035로 달라 순수 window 효과 확정 불가 | **미채택 — opt-in 진단 스위치** | [exp57](exp57_causal_background_polishing_plan.md) |
| exp57 window8 scale-bin 대조 | quantum0.01로 raw 1.03995를 1.040에 고정했지만 fixed **26.703dB**, 4,961 update. 첫 window8보다 −0.142dB이며 window10 quant 평균보다도 낮음 | **기각 — frontier window 축 종료** | [exp57](exp57_causal_background_polishing_plan.md) |
| **exp57 pre-IMU GS gate** | IMU metric init 뒤 전부 삭제되던 초반 GS를 init 완료까지 보류. 두 run fixed **27.0039/27.0371dB**(평균 27.0205), 97.207/97.241s, tail0. scale도 tracking-only 0.9736대로 복귀 | **채택 — strict pure-online 27dB 2/2 재현** | [exp57](exp57_causal_background_polishing_plan.md) |
| **exp57 freeze850** | pre-IMU gate + append-only PPM birth + post-freeze dense supervision. fixed **27.5822/27.6958dB**(평균 **27.6390**), 97.282/97.200s, tail0, MPS0 | **채택 — strict27 best 갱신(+0.6185dB vs freeze1050 평균)** | [exp57](exp57_causal_background_polishing_plan.md) |
| **exp57 freeze800** | freeze800 fixed **27.8568/27.8361dB**(평균 **27.8464**), floater proxy **15,252/15,573개**; freeze750은 27.6969로 하락. 97.235/97.271s, tail0, MPS0 | **채택 — strict best 및 floater 동시 개선** | [exp57](exp57_causal_background_polishing_plan.md) |
| exp57 strict27 acceptance audit | freeze800 보존 산출물 2개를 JSON/provenance/config/log/PLY로 재검증. PSNR **27.8568/27.8361**, 97.2349/97.2710s, evaluator exclusion·RGB+IMU-only·MPS0·tail0 2/2, floater **15,252/15,573** 재산출 일치 | **1차 목표 acceptance 완료** | [exp57](exp57_causal_background_polishing_plan.md) |
| exp57 late1000 PPM birth2× | frame1000 이후 birth만 2×. 103.6kGS(+23.5%), fixed **27.8335dB**(freeze800 평균 −0.0129), bin1000–1199 +0.499dB지만 final −0.536dB, floater **16,988(+10.2%)** | **기각 — density 단독 축 종료** | [exp57](exp57_causal_background_polishing_plan.md) |
| exp57 late1000 newborn appearance refine | frame1000 이후 newborn 행만 appearance+opacity 1-step. fixed **27.8391dB**(−0.0074), bin1000–1199 +0.518dB/final −0.280dB, floater **15,412** 동급 | **기각 — keyframe-local 정착 무이득** | [exp57](exp57_causal_background_polishing_plan.md) |
| exp57 recent5% newborn-only | recent dense appearance+opacity를 post-freeze 행에만 적용. fixed **27.9030/27.7545dB**(평균 27.8288, control −0.0177), floater **15,126/15,786**(평균 +43.5) | **기각 — 첫 양성 미재현** | [exp57](exp57_causal_background_polishing_plan.md) |
| exp57 recent50% newborn-only | recent 비중 5%→50%, gradient는 post-freeze 행에만 제한. fixed **26.5736dB**(freeze800 평균 −1.2729), 7개 temporal bin 전부 악화, floater **15,734(27.10%)** | **강한 기각 — uniform replay를 대체하는 recent family 종료** | [exp57](exp57_causal_background_polishing_plan.md) |
| exp57 strict27 background carve | depth-anchor floater paired 평가. background carve off→λ0.05에서 fixed **27.012→26.840dB**, visible floater **16,639→17,036**, 비율 28.976→29.689%. 시간/tail0는 통과 | **기각 — regular carve만 유지** | [exp57](exp57_causal_background_polishing_plan.md) |
| exp57 loss-priority | causal loss EMA priority50은 fixed **26.9249dB**(uniform 평균 대비 −0.0956). 모든 view를 한 번씩 보존한 weighted-without-replacement도 **26.9726dB**(−0.0479), 97.2382s/tail0로 uniform을 못 넘음 | **family 기각 — uniform shuffled 유지** | [exp57](exp57_causal_background_polishing_plan.md) |
| exp57 batch sequential-Adam | batch forward 뒤 view별 `autograd.grad`를 구해 Adam 두 step을 보존하는 gate. 90,770GS/1024²/2-view에서 순차 **7.7485ms** vs batch-grad **11.9746ms**로 54.54% 느림; 현재 autograd가 loss마다 batch 전체 backward를 재실행 | **조기 기각 — smoke/full 미실행** | [exp57](exp57_causal_background_polishing_plan.md) |
| exp57 batch repeat-Adam | batch2 평균 gradient를 Adam에 2회 재사용. paired 600 smoke에서 update **2,714→3,100(+14.2%)**이나 fixed **27.4518→27.2989dB(−0.153)**, SSIM/LPIPS도 악화 | **기각 — full 미승격** | [exp57](exp57_causal_background_polishing_plan.md) |
| exp58 | 고위험 backward 속도 축 착수. 첫 저위험 가지인 fixed background view의 pose-gradient 생략은 90,770GS/1024²에서 full **3.0617ms** vs skip **3.1216ms**로 −1.96%(역효과); Gaussian gradient는 atomic-noise 수준으로 정합했지만 full replay 전 기각. 임시 source/binary는 baseline으로 복구·backward 재검증 | **진행 중 — pose-grad-only 가지 기각** | [exp58](exp58_cuda_visibility_backward_plan.md) |
| **exp60 viewpoint-novelty sampler + GPU 락 버그 수정** | novelty sampler(`background_polish_novelty_fraction`) 구현 후 4장면 확장 중 aria1253rot에서 exp59의 미해결 PGBA 크래시가 재현. `CUDA_LAUNCH_BLOCKING=1`+계측으로 근본 원인 2개 확정: (1) `update_pgba`의 `jj_inac` 하한 미검증(수정, 단독으론 불충분) (2) **`background_polish_step`이 PGBA와 `self.video.get_lock()`을 공유 안 해 GPU 커널이 동시 실행됨(수정 → 크래시 해결)**. 수정 후 4장면(aria1253/rot/301_305/301_12F) 전부 크래시 없이 완주. novelty=0.5 자체는 4장면 평균 약 −0.23dB로 uniform 대비 기각(305: −0.17, 1253: −0.46, rot: −0.35, 12F: +0.08) | **sampler는 기각, 그러나 pre-existing GPU 동시성 버그 발견·수정으로 4장면 안정성 확보** | [exp60](exp60_viewpoint_novelty_sampler.md) |
| **exp59 타 데이터 전이** | freeze800 recipe를 재튜닝 없이 aria1253rot·aria301_305·aria301_12F에 적용. as-is 재현은 **26.00/16.95/26.13dB**로 전부 실패, 경계값 rescale은 PGBA CUDA gather kernel에서 **3/3 재현되는 크래시**(background_polish_start_frame 원복 대조군으로 "background 스레드 타이밍" 가설은 기각, freeze/pgba/late-mapping 값 자체로 원인 범위 축소). aria301_305를 freeze/시간제약 없이 재실행(축 D)하니 **22.96dB로 회복**돼, 305 붕괴의 대부분도 freeze 경계 하드코딩(문제1)의 심한 사례였음을 확인 — 잔여 4~5dB 갭만 진짜 scene 난이도로 남음. 1.5× 데드라인도 세 데이터 모두 초과(+1.50/+3.27/+3.28s). VRS→VIGS 변환기(`build_vigs_aria_input.py`) 신규 작성 | **재현 실패 — 원인 3종(경계 하드코딩·PGBA 크래시·데드라인 초과)으로 수렴, 305 이상치는 대부분 문제1로 환원** | [exp59](exp59_strict27_cross_scene_transfer.md) |
| **exp62 라이브 OKVIS2‖3dgs-custom 병렬 파이프라인** | exp61 §7 격차(콜백은 있지만 incremental 브릿지·매퍼 폴링 루프 없음)를 메우는 구현. Codex CLI(`codex exec`)에게 M1(라이브 소스)~M5(12F 확장) 5단계 마일스톤 위임, 매 단계 exp61 오프라인 reference와 자동 비교 검증 통과해야 다음 단계 진행. **74분 만에 M1~M5 전부 통과** — 트래킹↔매핑 동시 실행을 타임스탬프로 확정(M3), 1253/305/12F 세 장면 모두 real-time 예산(1.5×) 안에서 zero-tail 완주(M4/M5, 12F는 배칭 없이도 통과). PSNR 품질 게이트는 아직 없음(다음 과제) | **M1~M5 전부 통과 — real-time 병렬 파이프라인 최초 성공** | [exp62](exp62_live_okvis2_mapping_pipeline_plan.md) |
| **exp63 VIGS-SLAM 매핑 재튜닝(cross-scene·cross-GPU 강건화)** | exp57 freeze800 레시피(1253 27.85dB)의 305/12F 전이 실패(exp59)를 매핑 레시피 자체를 다시 설계해 해결하려는 계획. 본 세션 코드 감사로 신규 확인: (1) vanilla 트래킹이 exp53~56 속도튜닝보다 305/12F ATE 정확 (2) 실시간 map()/background_polish_step()엔 해상도 다운스케일이 전혀 배선 안 됨(color_refinement 오프라인 전용) (3) `adaptive_density_curve`가 aria1253 keyframe으로 fit된 파일 그대로 재사용됨 (4) `background_polish_idle_guard_ms=0`이 exp59/60 미해결 CUDA crash의 원인 후보 (5) `init_itr_num` 등이 RTX 5070Ti 프로파일링 고정값이라 GPU 무관화도 별도 축 필요. 축 A(트래킹 상향 스캔)~축 G(전역 LR 스케줄)로 계획 수립 후 Codex(`codex exec`)에 축별
위임 시작. **축 D(idle_guard) 완료**: 0/5/20ms 전부 exp59 crash(`vectorized_gather_kernel`)를
못 고침(idle_guard는 원인 아님으로 기각), guard=5는 아리아1253 PSNR은 통과(27.63dB)하나
wall time이 예산을 3.4초 초과해 미채택. crash 원인은 미해결로 축 B(경계 비율화)로 이월 |
**축 D+B 완료** — 축 B(경계 비율화)로 305 16.95→**21.09dB**(+4.14), 12F 26.13→**27.04dB**
(+0.91), crash 없음. Codex는 wall time 초과(예산 3.4~3.5초 초과)로 `adopted:false` 보고했으나
직접 검증 결과 이 초과분은 축과 무관 — 채택된 97.65초 예산이 2026-08-03 exp60 GPU-lock
안전수정(2026-07-29 baseline 측정 이후 추가) 비용을 반영 못 한 stale 값임을 확인해 축 B를
채택으로 뒤집고 예산 기준을 ~101/205/168초로 재보정. **축 A(트래킹 파라미터 상향 스캔)**도
완료: `frontend_radius=2`만 채택(12F +0.72dB), `thresh=3.0`은 305 +1.91dB지만 1253 회귀로
기각, `iters1=2`는 예산 초과+305에서도 crash 재현. 305 잔여 격차는 Gaussian 밀도 부족으로
추정(1253 66.4개/프레임 vs 305 29.7개/프레임). **이후 사용자 요청으로 Claude가 직접 crash
근본 원인 규명·수정**: `update_pgba`의 TOCTOU 버그(`t1` 고정 vs `ii`/`ii_inac` 계속 갱신)
확정, `[0,t1)` 필터링으로 수정 — 305가 오늘 처음 crash 없이 완주(22.82dB). **1253 회귀
게이트도 사용자가 명시적으로 폐지**, 앞으로 305 품질/강건성만 기준. **축 A2 완료·채택**:
`motion_filter.thresh=2.6`+`iters1=2` 스택으로 305 **29.8154dB**(+7.00dB) — 병목이
매핑이 아니라 프론트엔드 트래킹 keyframe 밀도였음을 확인. **축 C/C2 완료·기각**:
"map()/PGBA 끝까지 켜두기" 스펙트럼 양극단(전혀 freeze 안 함 / 초기화 직후 즉시
freeze) 테스트 — 둘 다 A2보다 나쁨(각각 305 -4.92dB·12F OOM, 305 -10.46dB·12F는
완주). 12F OOM은 Claude가 직접 근본원인 규명(freeze가 유일한 학습-비용 상한선이라
없으면 `map()`의 매 keyframe 렌더+역전파 호출이 끝까지 계속되며 메모리 하이워터마크가
계속 커짐) — A2의 61% freeze 지점이 이미 세 지점 중 최선이라 freeze-시점 축 종결.
**축 PF 완료·기각**: background_polish가 `dense_only` 필터로 rgb_dense(별도 sparse
raw 프레임)만 보고 birth를 만든 keyframe 자체는 영원히 폴리시 안 받는다는 갭을
발견해 후보 자격을 넓혀봤으나(opt-in 플래그), 선택이 여전히 균등 랜덤이라 오히려
소폭 악화(즉시freeze -0.58dB, 기존스케줄 -0.28dB) — 후보 풀 확대보다 "폴리시가
보는 후보를 작은 trailing window로 제한"이 다음 유망 방향으로 식별됨. **A2가 12F에서
미검증 상태로 -4.84dB 회귀 중이었음을 발견**(23.15dB, 원인: `background_polish` step이
6,586→772로 88% 감소). `VIGS_TIMING_LOG` 계측을 처음 켜고 `background_polish_step`에
신규 타이밍 계측 추가해 4개 런 실측: frontend가 프레임 단계 시간의 64~73%로 압도적
지배(map() 디스패치는 1~4%뿐), polish는 call당 비용(3.9~6.4ms)이 아니라 실행 **횟수**
(772~9,866, 최대 13배)가 dB를 갈랐음을 확정. 결과 시각화: `context/ppt/ppt0812/`. **이어서
`replay_time_scale` 스윕(1.5/2.0/3.0, `--strict_aria_online` 제외)으로 인과관계를 직접
검증**: scale 2.0(+33% 예산)에서 12F가 23.84→**28.10dB(+4.26)**로 A2 이전 baseline을
넘어 거의 완전 회복(polish 806→5,681회)했지만, scale 3.0은 polish가 10,000-step 캡에
도달했음에도 **25.97dB로 역행(-2.13)** — 역-U자형이며 좁은 후보 풀 과적합 가설(미검증)만
있음. `gs_worker_dispatch`/`background_polish_call`에 epoch 타임스탬프를 추가해 polish
횟수의 "계단식" 양상을 gap 단위로 재구성: 총 횟수는 `Σ floor(gap/step비용 4~6ms)`라는
정수 나눗셈의 합이며, gap의 43~57%는 step 1개도 못 낄 만큼 짧아 zero-polish로 버려짐을
확정. 결과 시각화: `context/ppt/ppt0812/`(15슬라이드로 확장) |
[exp63](exp63_vigs_slam_robust_general_mapping_tuning.md) |
| **exp64 map()↔polish 시간-비율 거버너** | exp63의 우선순위 붕괴(A2 12F 회귀)와 freeze의 비가역성(축C2) 두 문제를 동시에 겨냥한 적응형 스케줄러. `background_polish_step`/`map()`에 `VIGS_TIMING_LOG`와 무관한 상시 벽시계 타이머를 추가해 최근 5초 구간의 실측 시간-비율을 추적, polish 몫이 목표(`--polish_share_target_frac`) 밑이면 다음 map() 호출의 `iters`를 부족분에 비례해 줄인다(`--polish_share_min_map_iters`로 바닥 보장, 축C2처럼 0으로는 안 감). 뷰 선택의 staleness 회피는 기존 `--background_polish_shuffle_epoch`가 이미 담당 중이라 재구현 안 함. 비슷한 이름의 기존 미사용 메커니즘(`--late_mapping_adaptive_background_target_steps`)은 인과 방향이 반대(polish 뒤처지면 map iters 증가)라 재사용하지 않고 신규 구현. 1차 실행(12F scale=1.5, target=0.15): PSNR 23.84→**26.13dB**(+2.29), polish 806→2,928회(3.6배), OOM 없음(8.37GB) — 예산을 안 늘리고 재배분만으로 얻은 개선. 아직 27dB 미달, 1253/305 교차검증 전 | **1차 결과 긍정적, 교차검증 전** | [exp64](exp64_map_polish_time_share_governor.md) |
| **exp65 Budget-Constrained GS-SLAM → Backpolish-Free 재프레이밍** | 사용자 작성 논문급 실행 계획을 등록 후, 같은 날 두 ADDENDUM으로 목표를 "iter당 효율 개선"에서 **"backpolish(전역 refinement) 완전 제거"(C0)** 로 재정의. M1을 M1a(naive lift, iter-0 PSNR)→M1.5(prior 감사, confidence↔오차 상관)→M1b(2D fit 후 3D lift, GaussianImage/Augmented Radiance Field 이식, Δ_lift≤3dB 게이트)→M1c(multi-view 누적 열화)로 4단계 분해. 신규 M3′(ray-constrained 1-DoF Gaussian, PAGaS 청사진, DoF 14→6)·M3″(confidence-adaptive DoF 할당). 메인 표는 신규 E6(S0~S5) — `PSNR(S4)-PSNR(S0)`이 C0 판정. RGS-SLAM/PAGaS를 직접 경쟁자로 명시(scoop 리스크 🔴). VIGS-SLAM exp63/64 dirty 변경분을 체크포인트 커밋(`ca851173`)으로 정리 후 `exp65-backpolish-free` 브랜치로 분기, 이후 방향설계=Claude/구현·실행=codex(2) 위임/매 단계 독립 재검증 루프로 운영 시작. **전체 M1/M3/M3′ 트랙 요약(2026-08-19 세션 종료 시점, 상세는 [exp65 status report](exp65_status_report.md))**: E6 S1(freeze confound 정정, backpolish 순수 기여도 -4.77dB) → M1a(0-iter -0.61dB, nofreeze -0.06dB로 격차 1/10 축소 — 자유 최적화가 초기화 차이를 지움) → M1b(Δ_lift=19.39dB로 kill 기준 초과, flat_lift 대조로 92%가 렌더러 불일치임을 규명·계획서 문구상 폐기) → M3′(ray+normal 제약, DoF 14→6: 초기화 민감도 가설은 확인됐으나 3000 iter 시점 ceiling이 free 대비 8.58dB 낮아 acceptance 기준 대실패, R3 없이는 기각) → M3(mesh, A2 — 사용자가 원래 의도한 핵심 실험): SuGaR mesh-binding 공식 포팅(clone+실제 버그 발견·수정), Delaunay mesh(Sobel+normal곡률 밀도가중) 구성 → 파라미터 39% 절감하면서 PSNR 격차는 안정적. **⚠ 정정(속도 실측 후): mesh를 최적화 내내 유지하면 iter당 4.46배 느림(reconstruct() 오버헤드가 파라미터 절감분을 상쇄) → "init에만 mesh 쓰고 bake" 재시도했으나 속도는 정상화돼도 품질이 단순 baseline과 같거나 낮음(M1a부터 반복된 "얇은 orientation-Gaussian이 등방 Gaussian보다 불리" 패턴 3번째 재현). **최종 판정: mesh 기반 접근 순이득 없음, M3-mesh도 기각.** → M2(closed-form 색): rasterizer가 blending weight를 노출 안 해 `A_j`를 `n_touched`로 근사했더니 저기여 가장자리 픽셀까지 세어 대각항을 과대평가, Adam 1 iteration도 못 따라가 기각(`n_touched` 평균 380·중앙값 113로 damping 문제 아님 확인 후 근사 자체가 원인). → M4(carve loss 재평가, "삭제 대신 이동" B3가 B1을 동일 예산에서 이겨야 한다는 가설): `03_rgb_3dgs_full` 7000iter에서 control 28.93 > b1only 28.86 > b3only 28.65dB로 가설 실패, b3only는 wall-clock까지 가장 느려 기각. **M1/M2/M3/M3′/M4 다섯 축 전부 기각, exp65 "예산 수요 감축" 트랙 종결.**
| **exp66 GS-SLAM 2차 최적화 논문 서베이** | exp65 전체 기각 후 사용자가 외부 조사한 GS-SLAM 2차 최적화 논문 4편(3DGS², LM-RS, CaRtGS, FSGS) 중 코드 공개된 2편(LM-RS, CaRtGS)을 codex/codex2로 실측(상세는 [exp66 status report](exp66_status_report.md)). **CaRtGS(Photo-SLAM 기반 완전 별도 C++/CUDA SLAM 시스템)**: 이 머신 GPU(RTX 5070 Ti, sm_120/Blackwell)가 CaRtGS 고정 버전(PyTorch 2.3.1+cu121, sm_90까지만 지원)과 근본 비호환 — `torch.ones(1,device="cuda")`조차 "no kernel image" 실패로 직접 확인, 빌드 2회 실패. 헤드리스 렌더링은 문제 아니었음(`DISPLAY=:1` 정상). "기각"이 아니라 "이 GPU/툴체인 조합에서 검증 불가"로 판정, Replica 미다운로드로 종료(참고용 논문 수치만: room0 29.38±3.70dB). **LM-RS(vanilla 3DGS fork, optimizer만 matrix-free CG로 교체)**: 같은 sm_120 문제를 codex가 CUDA 12.8+`TORCH_CUDA_ARCH_LIST=12.0` 로컬 재컴파일로 우회해 실행 성공. 같은 저장소·같은 scene(`03_rgb_3dgs_full`) 안에서 vanilla Adam과 비교: wall-clock 매칭 기준으로도 +1.9dB 우위(iter1000/84s=27.53dB vs vanilla 7000iter/88s=25.65dB) — **이 세션 전체에서 첫 확실한 순이득**(노이즈 폭 ±0.24~0.33dB 확실히 초과). 그러나 iter 5500~6000 사이 PSNR 27.4→9.8dB 치명적 붕괴 발견. `lr=1/color_update.max()` 0-나눗셈 가드 부재로 원인을 특정해 가드 추가 후 1회 재검증했으나 **가설 기각** — lr을 가드해도 붕괴가 그대로(더 일찍) 재현됨, 진짜 원인은 CG 선형 solve 자체가 optim_iter 2430부터 non-finite 해를 내놓는 더 깊은 문제(scene 취약성 vs 비권장 툴체인 여부 미구분). **"채택도 기각도 아님" — 원리 검증은 성공, CG solver 내부 디버깅 없이는 실사용 불가, 다음 단계는 사용자 결정 대기.** **축 3 Taming-3DGS**(CaRtGS가 "backward parallelism" 출처로 인용한 저장소, vanilla 3DGS 단독 fork라 LM-RS와 동일 방법론으로 같은 scene 비교): PSNR은 vanilla가 계속 우세(iter7000: 29.04 vs 28.45dB, wall-clock 매칭해도 동일) — 순이득 없음. **그러나 Gaussian 개수 727,213(vanilla) vs 102,428(Taming)로 7.1배 절감되면서 손해는 -0.59dB뿐** — score-based budget-constrained densification(`budget=20,mode=multiplier`)이 실제로 통제 가능한 예산으로 동작함을 실증. CaRtGS는 이 budget 메커니즘을 안 쓰고(속도 기법만 차용, Gaussian 개수는 더 약한 opacity regularization으로 별도 관리) 있음을 논문 직접 확인으로 규명. Taming은 오프라인 정적 학습용 설계(목표 개수 하나 고정)라 온라인 incremental mapping엔 롤링 예산 재분배 같은 변형 설계가 필요, 단순 이식 불가. **축 4(LM-RS→VIGS-SLAM backpolish 통합) NO-GO**: backpolish는 map()과 완전히 같은 단일 스레드에서 도는 3.9~6.4ms짜리 극세립 협조적 호출 구조(exp60 CUDA 동시성 크래시 전례로 lock 직렬화됨) — "진짜 병렬 스레드"는 그 크래시 재현 위험, "LM-RS를 잘게 쪼개서 맞추기"는 batch/CG 축소 스윕(6개 조합) 결과 전부 발산하고 vanilla 수준 시간대에선 이득도 미미해 근본적으로 성립 안 함. **이후 사용자가 latency 허용치를 "몇 초까지 허용 가능"으로 명확히 하면서 축 4 전제 자체가 무효화 → 축 5로 전환.** **축 5(LM-RS→VIGS-SLAM 실제 이식, dual-rasterizer) 부분 완료**: 브랜치 `exp66-lmrs-polish-preempt`에서 LM-RS rasterizer를 `diff_gaussian_rasterization_cg`로 이름 바꿔 VIGS-SLAM 자체 env(vigs-slam-5090, sm_120 네이티브)에 충돌 없이 공존 빌드, 실제 aria1253 600프레임 라이브 세션에서 `background_polish_step` 렌더를 이걸로 배선해 크래시 없이 완주(27.66dB, control 27.76dB와 노이즈 범위 안 동일) — rasterizer 호환성·실데이터 연동은 실측 확인. 부수적으로 opt-in burst 스케줄링도 구현·검증했으나 기존 `_gs_worker`가 이미 자연 발생적으로 평균 90회 연속 호출을 하고 있어 불필요했을 가능성 발견. **CG solve 로직 자체(타일링 차원·배치상태·pixel/camera sampler가 CUDA 커널 내부 관례에 강결합) 이식은 미착수** — 잘못하면 크래시가 아니라 조용한 오류 위험, 최소 여러 시간~세션 하나 규모로 판단해 사용자 합의 하에 중단. git 변경사항은 uncommitted 보존(전부 opt-in, 기본 동작 불변, smoke test로 회귀 없음 확인). |

**E6 S1 1차 실측(aria1253): backpolish OFF 시 27.806→17.437dB(−10.369dB)** — keyframe(123)·최종 gaussian 수(95,954→95,426) 거의 동일해 파이프라인은 정상 작동, 진짜 갭. **⚠ 이후 정정: 이 -10.369dB는 freeze confound 포함값.** 사용자가 "옛 vanilla pure_online 22~23dB와 왜 이렇게 차이나냐"고 재확인 요청 → exp52~56 시기엔 `mapping_freeze` 자체가 없었고(map()이 전체 시퀀스 끝까지 정상 작동) freeze+background_polish는 exp57에서 함께 도입되며 "freeze 이후는 backpolish가 보완" 전제로 설계됐음을 서브에이전트 조사로 확인. freeze 3개 플래그만 제거한 **S1-nofreeze 재실행: 23.037dB**(fixed-eval 22.819dB) — 옛 vanilla 수치(22.73dB)와 거의 일치. **backpolish 순수 기여도는 -4.769dB로 정정**(원래 -10.369dB 중 5.6dB는 freeze confound). M1a는 의도적으로 즉시freeze를 썼으므로 이 문제와 무관. codex 구현 1차는 무출력 SIGTERM 실패, codex2로 재시도해 성공했으나 자체 리포트가 "error"로 오탐(직접 diff 재검증으로 실제론 정상 확인); 실행도 출력 디렉터리 선후관계 버그로 1차 실패 후 재시도 성공. **S1b "birth-only" probe는 중단**: `--late_mapping_iters 0`은 `demo.py`가 `ValueError`로 차단, 최솟값 1로도 `map()`의 `first_mapping` 분기(`init_itr_num=0`)에서 `frozen_mask` `UnboundLocalError` 실제 크래시 발견(백그라운드 스레드가 조용히 죽어 20분 멈춘 것처럼 보임) — 버그만 기록하고 probe 자체는 접음. **M1a 구현·측정 완료**: `viewpoint.normal`(omnidata prior)이 이미 매 keyframe 채워져 있는데 raw birth(`create_pcd_from_image_and_depth`)가 무시하고 있음을 확인, opt-in `Dataset.exp65_m1a_normal_orient` 플래그로 normal 기반 quaternion(half-way-vector 공식, `build_rotation()` 컨벤션과 500샘플 대조 후 최대오차 3.4e-7로 검증)+anisotropic surfel scale 구현. exp63 검증된 `mapping_freeze_after_frac=0.0+allow_births`로 크래시 없이 "raw birth만" 측정: **control(identity rotation) 16.446dB vs normalorient(신규) 15.839dB — normal 기반 배치가 오히려 -0.607dB 더 나쁨**(LPIPS는 반대로 우세, 지표 불일치). 둘 다 kill criterion(≥15dB) 통과. 가설: 얇은 surfel이 normal 오차에 훨씬 취약(iter-0라 보정 없음) — M1.5(prior 감사) 없이 M3″로 직행하면 안 된다는 걸 실측으로 뒷받침. 단일 run/단일 flatten_ratio(0.2)라 잠정치, 다음은 M1.5 또는 flatten_ratio sweep | **E6 S1 + M1a 둘 다 1차 측정 완료(48시간 우선순위 소진), 다음 방향 결정 대기** | [exp65](exp65_budget_constrained_gs_slam_plan.md) |
| **exp61 OKVIS2→3dgs-custom 벤치마크 재현** | 팀원(martian35) 벤치마크 `aria-online-3dgs-bench`(OKVIS2/OpenMAVIS stereo+IMU → 3dgs-custom incremental)를 RTX 5070 Ti에서 재현. 팀원 VIGS 재현치가 낮았던 원인은 데이터가 아니라 **GPU(3090, target은 5090)+305/12F 스크립트 오용**임을 확정(자체 재현 27.7735dB로 baseline 일치). OKVIS2 빌드+stage1~6(트래킹 49.3s·chunk 49개·PPM/pool/refilter)이 팀원 3090 수치와 정합적으로 일치. 실제 학습 진입점의 real-time 예산 스케줄러가 팀원 로컬 미푸시 커밋이라 정식 recipe는 보류, 대신 예산 없이 직접 실행해 **순수 학습 wall time 89초(49 events)** 실측. 트래킹 정확도는 OKVIS2(stereo)가 VIGS(mono)보다 305/12F에서 3.6~26배 우세, 매핑 품질은 장면별로 갈림(1253=VIGS 승, 305=OKVIS2 압승, 12F=동률). 코드 감사로 "OKVIS2 자체엔 이미 라이브 콜백 인프라(`okvis_app_realsense.cpp`)가 있지만 incremental 브릿지·매퍼 폴링 루프는 전혀 없음" 확인 | **재현 성공(트래킹~stage6), 정식 학습은 팀원 파일 대기 중** | [exp61](exp61_okvis2_3dgs_custom_benchmark_repro.md) |

- 2026-09-25 | ATTR online dense paired snapshot poses | Aria/RPNG candidate–KF common poses identical at 3 states; common-coordinate quality evaluation pending | [card](campaigns/06_gain_attribution/online_dense_training/README.md)

- 2026-09-25 | ATTR v6 completed / v7 preregistered | mean dense25.0100 vs KF25.0521 / production23.9036; NOT accepted. Current-anchor correspondence reuse next;25 CPU + CUDA checks pass | [card](campaigns/06_gain_attribution/online_dense_training/README.md)

- 2026-09-25 | ATTR shared snapshot coordinates | RPNG/Aria six dense–KF state pairs exported with identical evaluation trajectories;7 CPU checks PASS, GPU curves pending | [card](campaigns/06_gain_attribution/online_dense_training/README.md)

- 2026-09-25 | ATTR v7 manipulation FAIL | RPNG24.9965dB, warm0/308: tensor identity invalidates correspondence cache; panel stopped, already-started Aria allowed to finish | [card](campaigns/06_gain_attribution/online_dense_training/README.md)

- 2026-09-25 | ATTR v7 interruption / v8 UID repair | Aria child ended without result; no quality claim. UID-based correspondence key passes tensor-reallocation/current-depth CUDA checks; actual warm-activation gate added | [card](campaigns/06_gain_attribution/online_dense_training/README.md)

- 2026-09-25 | ATTR v8 RPNG cost/quality | warm336/409, pose3.275s and+609 Adam vs v6, but PSNR24.8427 (−0.1638 vs v6 /−0.3864 vs KF); not accepted, cross-scene transfer running | [card](campaigns/06_gain_attribution/online_dense_training/README.md)

- 2026-09-25 | ATTR v8 three-scene summary | mean25.1196(+0.0676 vsKF), RPNG/Aria still−0.3864/−0.3401; NOT accepted. v6 paired stream evaluation launched | [card](campaigns/06_gain_attribution/online_dense_training/README.md)

- 2026-09-25 | ATTR v9 preparation | current-pool tau=1/N opt-in, objective/invariance tests PASS (27 CPU); GPU experiment not launched, v6 curves in progress | [card](campaigns/06_gain_attribution/online_dense_training/README.md)

- 2026-09-25 | ATTR RPNG paired stream curve | dense−KF at4states:−0.0358/−0.1027/−0.0072/−0.2226dB; no observed earlier-quality gain, actual timestamps preserved | [card](campaigns/06_gain_attribution/online_dense_training/README.md)

- 2026-09-25 | ATTR v6 curves complete / v9 running | three paired curves+PNG/SVG; Aria midstream gain lost at endpoint, UTMM grows; no exact first-attainment proof. IMU startup excluded from clock identified for final cost audit | [card](campaigns/06_gain_attribution/online_dense_training/README.md)

- 2026-09-25 | ATTR startup cost / v9 RPNG | IMU init69.7/35.3/7.6ms excluded from current clock; final boundary correction needed. RPNG v9 25.0097 (+0.1670 vsv8,−0.2194 vsKF), remaining scenes running | [card](campaigns/06_gain_attribution/online_dense_training/README.md)

- 2026-09-25 | ATTR v9 fail / v10 timing repair | UTMM exceeds by41.7ms with final packet0 Adam; added input preparation guards + mapper/IMU setup clock,3 CPU tests PASS. Fresh9-arm matched panel next | [card](campaigns/06_gain_attribution/online_dense_training/README.md)

- 2026-09-25 | ATTR first v10 clock validation | RPNG24.9880dB; setup0.1677s included,138.2702/138.3670s PASS;9-arm panel continues. Warm BA batching diagnostic prepared but not GPU-tested | [card](campaigns/06_gain_attribution/online_dense_training/README.md)

- 2026-09-25 | ATTR v10 RPNG / runtime provenance |24.9880 vsKF25.2513/prod24.4477, budgetPASS;3 actual mapped CUDA libraries preserved, no-Torch probe matches live paths/hashes; real worker integration still pending | [card](campaigns/06_gain_attribution/online_dense_training/README.md)

- 2026-09-27: [init density 15/40 종합](campaigns/06_gain_attribution/init_density/SUMMARY.md) — 18회 PASS; 절반/1/4 공통 축소 품질 미보존, 기본 설정 유지.

- 2026-09-27: [PPM 유지·바닐라 개수 근사 부분 결과](campaigns/06_gain_attribution/init_density/vanilla_budget/README.md) — 4회 완료, 사용자 범위 정정으로 나머지 중단; 추가 튜닝 없음.

- 2026-09-27: [RPNG40 보호 pruning-only](campaigns/06_gain_attribution/protected_prune/SUMMARY.md) — OFF/0.7/0.1 세 조건 완료; 최근10KF 보호, 0.1은GS−55.3%·PSNR−0.153dB·mapper−7.9%, 기본값 미변경.

- 2026-09-27: [opacity0.1 보호 pruning 교차검증](campaigns/06_gain_attribution/protected_prune/TRANSFER40.md) — Aria/UTMM추가2회PASS;PSNR−0.094/−0.102dB,GS−21.3/−31.7%;init증가미실행.

- 2026-09-28: [init+25%/prune0.1/300주기](campaigns/06_gain_attribution/protected_prune/init_increase/SUMMARY.md) — 6회PASS;Aria−0.056/RPNG+0.143/UTMM+0.143dB,기본값미변경.

| 2026-10-01 | CVPR full fixed-work + measured F6/F7 | 20 scenes,80 runs passed; independent region14 states; source106 files unchanged | [card](campaigns/06_gain_attribution/cvpr_assets/README.md) |
