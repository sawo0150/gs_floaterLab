# No scale projection (diagnostic) — PREREG (2026-10-09, user approved; aria1253 only)

**Why.** The B recipe clamps Gaussian scales to 0.1 at every tracker packet (`--unified-scale-projection`, 76 calls in
square-1). Online, clamps interleave with training; in D2/offline all clamps happen before any training, so trained
Gaussians are never clamped (final-map p95 max-scale: online 0.084–0.10 at the cap, D2 0.087–0.17, offline
0.078–0.15). The 2026-09-26 unified-mapping record already noted an uncapped diagnostic at 26.26 dB on Aria.

**Arm `noscale_iid`** (`noscale_patch.py`): online uniform with replacement (as the online/D2 reference), scale
projection disabled (calls must be 0). aria1253, seed 0, 1 run. Read-out vs online uniform_iid (24.66), D2 (26.65),
offline (26.90) on final-map held-out views.

## Amendment 1 (2026-10-09, user approved)
(1) `noscale_iid` on square-1 and Retail_Street (1 run each). (2) `seq_noscale`: the D2 sequence replay with scale
projection disabled (`B_NO_SCALE_PROJ=1` in offline_ladder_patch; default behaviour unchanged) on aria1253, so online
and D2 are compared with no clamp on either side: remaining D2 − online = stream-time effect without the clamp.
