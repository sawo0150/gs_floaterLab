# Multi-view free-space birth gate — PREREG (2026-10-09, user approved; aria1253 + square-1, 2 runs)

**Evidence (no GPU, event probe of online 0.5 births, clamp off, aria1253):** over 4,004 (birth, old KF) pairs, birth
damage tracks the share of new points lying in front of the old KF's surface (known free space; final-map centre
z-buffer, margin 10%): per birth corr(summed damage, summed free-space share) = −0.76 vs −0.21 for plain visibility;
pairs with ≥1% free-space points lose −0.57…−0.70 dB vs −0.16. Existing birth rules (RTG-SLAM, SplaTAM, Gaussian-SLAM)
judge only the current view.
**Rule (`B_FREESPACE_OPACITY=0.02`, event_probe_patch):** at each KF birth (not the first of a generation), every new
point is projected into the pool KFs older than the newest 6 that see ≥2% of the points; those KFs are rendered
(no grad) and a point is a conflict if, in any of them, rendered alpha ≥ 0.6 and point depth < 0.9 × rendered depth.
Conflict points start at opacity 0.02, all others at 0.5 (count and positions unchanged). ERVS K16, clamp off.
Arm `event_freespace002_noscale_ervs`. Compare: ERVS clamp off with 0.5 births (validation B: 25.32 / 21.92) and
selective births (aria 25.72); birth damage on old KFs from the event probe.
