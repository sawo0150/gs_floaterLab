# Settle-aware pool management on ERVS K16 — PREREG (2026-10-09, user approved incl. a pose-based variant)

**Why (gap_ladder).** Training during the stream explains 65% of offline − online; per held-out view, the gain from
deferring the same updates is largest where nearby training was replay of regions the camera had left (washed out by
later training), and smallest for frontier updates. Fresh regions are trained by the window role anyway.

**Rule** (`settle_pool_patch.py`): the KF-role and dense-role replay pools contain only *settled* views; dense
admission (one per κ steps, largest temporal hole first) considers only settled offered views; ERVS K16 group draws
over the settled members; window picks, quotas, credit, κ, τ = 4, births unchanged. Settled:
- `set_kf5` / `set_kf15`: ≥ 5 / 15 keyframes arrived after the view (dense: after its right anchor KF);
- `set_pose`: the newest KF camera is farther than 8 × the median consecutive-KF distance from the view (dense: mean
  of its anchor KF centres), or its viewing direction differs by > 45° — current causal pose estimates, scale-free.

**Scenes/seed.** aria1253, aria1253rot, square-1, table_06, ego-drive, Retail_Street; seed 0; 3 arms = 18 runs.
**Success (pre-declared, 6-scene mean):** mean PSNR above online ERVS K16 seed 0; reported next to D4 (final 15% RR
sweep) and offline. Secondary: offline-gap curve, front-loading, settled share of pools.
