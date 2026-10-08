# Birth-triggered repair replay on ERVS K16 — PREREG (2026-10-09, user approved; 2 runs first)

**Why.** gap_ladder: replaying the same updates after all Gaussians exist gains ~1 dB (65% of the offline gap).
Births into already-seen space are common in every scene (25–95%) and do not correlate with the gap (ρ = −0.09, 27
scenes), and suppressing them costs ~2 dB (exp98–100). Working hypothesis: late-born Gaussians in old regions are
needed capacity that stays under-trained online.

**Arm `repair6`** (`birth_repair_patch.py`): after each KF birth event, project a 2,000-point subsample of the new
Gaussians into pool KFs older than the newest 6 (current poses); the 6 KFs seeing the largest share (≥ 20%) go to the
front of the KF-role queue and up to 6 admitted dense views anchored to them to the front of the dense-role queue;
then ERVS K16 group draws. Births, credit, quotas 3:3:6, window, κ, τ = 4 unchanged.

**Scenes/seed.** aria1253 (gap 2.2 dB) and square-1 (0.75 dB), seed 0, 2 runs. Compared with online ERVS K16, D2
(seq) and offline. Read-out: mean PSNR (final-map views) vs ERVS; offline-gap curve. Extension only after review.
