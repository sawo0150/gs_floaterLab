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

## Amendment 3 (2026-10-09, user request; aria1253, 1 run)
Same event probe with births at opacity 0.02 (`event_op002_noscale_iid`). Note: below the protected-prune threshold
0.1, so births not raised above 0.1 by training before leaving the 10-birth protection are pruned; prune counts reported.
