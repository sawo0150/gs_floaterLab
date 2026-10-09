# Offline → online gap decomposition on RPNG (8 scenes) — PREREG (2026-10-09, user approved: RPNG only)

Purpose: paper figure/table. One dataset (RPNG table_01–08; table_06 = pinned key `rpng`), seed 0, budget 25 renders/KF,
all arms with scale cap 0.5 (chosen in validation phase 1; the 0.1 clamp only hurts online and would confound).
Arms:
- online: uniform with replacement, cap 0.5 (`Bp_iid_cap05`, run_validation.py).
- D2: offline_ladder sequence replay of that online run's service sequence after the stream (`seq_cap05`).
- D1: same multiset shuffled (`cnt_cap05`).
- offline: deferred training, epoch round-robin, equal counts (`offline_cap05`, run_offline_cap.py; gates as before).
- online + fix: online + selective births 0.5/0.02 (`C_iid_cap05_sel`).
Decomposition: online→D2 = map-growth interference (training while the map changes); D2→D1 = order;
D1→offline = exposure uniformity (allocation). Fix recovery = (online+fix − online)/(D2 − online).
Metric: final-map held-out PSNR over the final-map span (first trained view of the offline reference), per scene and mean;
per-fifth curves. Order: per scene online → D2 → D1 → offline → fix. Event-probe evidence on 1–2 scenes may follow
(separate approval).

## Amendment 1 (2026-10-09, user)
The "online + fix" arm (`C_iid_cap05_sel`) is dropped: only online, D2, D1, offline (32 runs).

## Stopped (2026-10-09, user)
Stopped after table_06 (online, D2, D1; offline failed on a shadowed-module bug, not rerun) and table_01 (online, D2,
D1; offline interrupted, partial output archived under offline_reference/v1/failed_attempts/stopped_by_user_table_01_*).
The paper decomposition will use the existing 6-scene ladder instead.
