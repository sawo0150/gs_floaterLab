# Online vs offline tracking (measurement) — PREREG (2026-10-09, user approved; aria1253, 2 runs)

Questions: (1) does offline have birth damage (online: −93.7 summed at births, +84.1 recovered between births)?
(2) is there forgetting online / offline? Training unchanged; scale clamp OFF in both (it only hurts online).
`track_patch.py`: birth probe (as birth_probe) + every 50 completed RGB services, every pool KF rendered (no grad),
PSNR vs its own RGB. Runs: online `track_noscale_iid` (uniform with replacement, run_track.py) and offline
`offline_track_noscale` (offline_patch base, run_offline_reference.py --track --noscale-scenes aria; offline gates as
usual). Read-out: at-birth vs between-birth sums; per-KF PSNR curves; forgetting = peak − final per KF (online vs
offline, final generation); final-map PSNR should match noscale_iid 25.19 / offline_noscale 26.89.

## Amendment 1 (2026-10-09, user approved; aria1253, 1 run)
`event_probe_patch.py` (`run_event_probe.py`, arm `event_noscale_iid`, online uniform with replacement, clamp off):
every pool KF rendered right before/after each map-changing event — tracker packet (process_track_data), Gaussian
move by pose/scale correction, birth, pruning (when it removes), mapper control. Training unchanged. Goal: attribute
the −1.55 / −0.80 dB drops seen in tracking to specific events; training contribution = change between events.

## Amendment 2 (2026-10-09, user approved; aria1253, 1 run)
Event probe on low-opacity births (opacity 0.12, lowop_patch; clamp off): arm `event_lowop_noscale_iid`. Question:
does low initial opacity remove the revisit-birth damage (baseline: 12 births −11.4 dB, frames 1082–1123, 1184–1272)?

## Amendment 3 — WITHDRAWN (user rejected; misread request). A run had started and was interrupted; partial output
under `event_probe/v1/failed_attempts/rejected_by_user_*`. Original text:
Same event probe with births at opacity 0.02 (`event_op002_noscale_iid`). Note: below the protected-prune threshold
0.1, so births not raised above 0.1 by training before leaving the 10-birth protection are pruned; prune counts reported.

## Amendment 4 (2026-10-09, user request: "0.5, 0.02" = selective; aria1253, 1 run)
Event probe on selective births: points on already-explained pixels start at 0.02, others at 0.5 (selop_patch with
B_COVERED_OPACITY=0.02, clamp off; arm `event_selop002_noscale_iid`). 0.02 is below the protected-prune threshold 0.1:
covered births not raised above 0.1 by training before leaving the 10-birth protection are pruned (counts reported).

## Amendment 5 (2026-10-09, user approved; aria1253, 1 run)
Selective births 0.5/0.02 with the adopted ERVS K16 sampler (group_k_patch, B_GROUP_K=16, default tau) instead of
uniform with replacement; clamp off; event probe. Arm `event_selop002_noscale_ervs`. Question: does ERVS reduce the
recent-KF gap (+1.55 vs offline with uniform)? Compare with `event_selop002_noscale_iid` (25.72).

## Amendment 6 (2026-10-09, user approved; 3 runs)
Lagged window: the window role trains the KFs 6 positions behind the current window (`B_WINDOW_LAG=6`; nothing old
enough → window quota goes to the other roles); KF/dense pools unchanged. Basis: a KF's view has only ~30% of its
eventual post-arrival Gaussians within 3 KFs, ~43–53% within 6. Base: selective births 0.5/0.02, clamp off, uniform
with replacement, event probe. Runs: `event_selop002_noscale_iid_lag6` on aria1253 and square-1, and the unlagged
base `event_selop002_noscale_iid` on square-1. Compare with D2 (aria 26.52, square-1 21.85) and the unlagged base.
Note: the last 6 KFs get no window training.

## Amendment 7 (2026-10-09, user approved; aria1253, 2 runs)
Lower ERVS temperature: selective births 0.5/0.02, clamp off, ERVS K16 with tau 0.5 and 0.1 (arms
`event_selop002_noscale_ervs_t05/_t01`; tau 4 → 25.72). With per_view scale = tau × mean count, tau 4 is nearly flat;
low tau approaches lowest-count-first, which could move budget to late views (offline: ~12.5 KF / 8 dense each;
online last fifth 5.2 / 0.9). Read-out: PSNR, per-fifth held-out PSNR (last fifth 22.57; offline 23.98), counts by fifth.

## Amendment 8 (2026-10-09, user approved; aria1253, 2 runs)
Optimizer: GaussianModel appends Gaussians with zero Adam moments but keeps the tensor's shared step, so late rows get
no bias correction (effective step 3.2× at 1 update, 6.5× at 10, 3.2× at 100, 2× at 300). `rowadam_patch.py`: Adam
with per-row step counts (pruning/replace hooks; unit tests: identical to torch Adam without appends, appended rows
identical to a fresh Adam). Arms (clamp off, uniform with replacement, event probe): `event_noscale_iid_rowadam`
(births 0.5; vs 25.19) and `event_selop002_noscale_iid_rowadam` (selective 0.5/0.02; vs 25.72). D2 26.52.

## Amendment 9 (2026-10-09, user approved; aria1253 + square-1, 2 runs)
Best online setting + end-of-stream sweep: `hyb85_selop_noscale` (offline_ladder_patch hybrid: ERVS K16 online for 85% of
the earned credit, the rest as an epoch round-robin sweep over KF/dense pools after the last arrival; selective births
0.5/0.02 via selop_patch; clamp off). Compare: online selective (aria ERVS 25.72; square-1 uniform 21.72), D2
(26.52 / 21.85), offline (26.89 / 22.51), per-fifth held-out PSNR.

## Amendment 10 (2026-10-09, user request; aria1253 + square-1, 2 runs)
No window role after 70% of the stream (non-causal threshold: frame uid at 70% of the final-generation span of the
uniform_iid reference); its quota is refilled by the KF/dense roles. Base: selective births 0.5/0.02, clamp off,
ERVS K16 (`event_selop002_noscale_ervs_nowin70`). Compare with the same setting with window (aria 25.72; square-1
uniform 21.72). Expectation stated before running: last 30% worse (cf. lag 6), first 70% ≈ unchanged.
