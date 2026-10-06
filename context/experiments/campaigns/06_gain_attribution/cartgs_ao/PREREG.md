# CaRtGS adaptive optimization as a drop-in sampler — PREREG (2026-10-06, user approved; UTMM seed 0 first)

**Why.** CaRtGS (Feng et al., RA-L 2025) names the same problem ("long-tail optimization": uneven re-optimization as
the keyframe pool grows, declining PSNR for new keyframes, their Fig. 2) and solves it with Adaptive Optimization
(Eq. 5-8). Reviewers will ask how ERVS differs; the standard answer is a drop-in comparison of the scheduler inside the
same system and budget (as PER, MIR and Curious Replay compare samplers inside one agent).

**Arm `cartgs_ao`** (`cartgs_ao_patch.py`): per pool (KF and dense separately), new views get r0 = 2 (CaRtGS setting for
real-world TUM-RGBD / VECtor); draw uniformly among views with r > 0 and decrement; when all r = 0 refill: top
max(1, ⌊k/4⌋) by last training loss get 2, others 1 (d = 4, CaRtGS default). Loss = last per-view training loss of the
B objective. Window picks, quotas 3:3:6, credit, κ, births unchanged; ERVS weights unused; no K-group queue (CaRtGS has
none). Splat-wise backprop and opacity regularization (CaRtGS's other modules) are not part of this comparison.

**Stage 1.** UTMM 8 scenes (square-1 + 7 extra), budget 25, seed 0, 8 runs, compared with existing seed-0 uniform_iid,
uniform_k16, ERVS τ=4 and offline. Gates: valid run; refills > 0 in both pools; fallback share < 5% of draws.
Read-outs: mean PSNR vs uniform_iid / ERVS, offline gap curve, front-loading, count CV. Extension to all scenes and
seeds only after looking at stage 1 with the user.
