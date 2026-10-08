# Online vs offline tracking (measurement) — PREREG (2026-10-09, user approved; aria1253, 2 runs)

Questions: (1) does offline have birth damage (online: −93.7 summed at births, +84.1 recovered between births)?
(2) is there forgetting online / offline? Training unchanged; scale clamp OFF in both (it only hurts online).
`track_patch.py`: birth probe (as birth_probe) + every 50 completed RGB services, every pool KF rendered (no grad),
PSNR vs its own RGB. Runs: online `track_noscale_iid` (uniform with replacement, run_track.py) and offline
`offline_track_noscale` (offline_patch base, run_offline_reference.py --track --noscale-scenes aria; offline gates as
usual). Read-out: at-birth vs between-birth sums; per-KF PSNR curves; forgetting = peak − final per KF (online vs
offline, final generation); final-map PSNR should match noscale_iid 25.19 / offline_noscale 26.89.
