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

## Amendment 1 (2026-10-06, before any accepted result)
First square-1 run failed the fallback gate (13.5% of draws: with batches of 3 KF / 6 dense picks the last views with
uses left were often already in the batch). The user approved checking the released code (github.com/DapengFeng/cartgs,
commit 547c905, `GaussianMapper::useOneRandomSlidingWindowKeyframe`). The sampler now mirrors it: walk a shuffled
order of the pool (reshuffled when the pool changes), take the next view with uses left; refill (+1 all, +1 top
max(1, k/4) by last loss) only when no view has uses left; new views get 2 uses (`new_keyframe_times_of_use` in the TUM
configs). Batch adaptation: if every view with uses left is already in the batch, the next unused view in walk order
is borrowed without consuming a use (`borrow`, counted with fallback in the 5% gate). Not modelled: loop-closure bonus
uses (+2, no loop flag in our stream); local-BA bonus is 0 in the TUM configs. Failed run archived under
`cartgs_ao/v1/failed_attempts/fallback_gate_*` (PSNR 21.48, not used).
