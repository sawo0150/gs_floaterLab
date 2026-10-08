# Settle-triggered consolidation — PREREG (2026-10-09, user approved: aria1253 only, 1 run)

Pre-analysis in README.md (table_06 never settles, so it is not run). Arm `settle_iid` (`consolidation_patch.py`):
online uniform with replacement; after every KF birth, KFs older than the newest 6 that see ≥5% of the new points are
marked touched; a touched KF settles after 6 more KFs without a touch and is queued once (with its anchored admitted
dense views). KF/dense draws serve the queue first while consolidation draws ≤ 15% of all draws; otherwise uniform.
aria1253, seed 0. Compare with online uniform_iid 24.66, lowop 25.13, D2 26.65 (final-map held-out views).
