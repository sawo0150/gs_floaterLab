# Exp103 — generation-scoped dense topology evidence

This rerun corrects Exp102's persistence accounting. VIGS restarts
model-local point IDs after map reset, so every identity is now the
pair `(map_generation, point_id)`. Consecutive-set overlap is reset
at each generation boundary. Mapping behavior remains unchanged.

Candidate PSNR: **25.579016 dB**.
Candidate−Exp95 normalized R4: **-0.006001 dB**.
Candidate−fresh vanilla: **+1.614753 dB**.
Double evaluation: **PASS**.
Isolation gate: **PASS**.

Observed map generations: 3; final generation: 3.
Dense opportunities/unique UIDs: 269/267.
Mean positive-gradient rows/share: 129861.7/59.22%.
Mean gradient-mass captured by top 256/1,024/4,096 rows: 14.15%/29.85%/54.27%.
Within-generation consecutive top-1,024 Jaccard: 0.3175.

| Diagnostic top-K | Generation-scoped unique | Repeated ≥2 | Repeated ≥3 | Final-generation live repeated ≥2 |
|---:|---:|---:|---:|---:|
| 256 | 14,190 | 8,849 | 6,592 | 8,440 |
| 1,024 | 39,371 | 26,534 | 21,358 | 25,330 |
| 4,096 | 104,906 | 77,275 | 66,892 | 74,071 |

Probe host/top-k wall time: 2.026 s.

Only this corrected persistence table may be used to design the
bounded mutation ticket. Exp102 remains valid for quality and
gradient concentration, but not for cross-run identity counts.
