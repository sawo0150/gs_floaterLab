# No scale projection (diagnostic) — result (2026-10-09)

1 run (aria1253, seed 0, uniform with replacement), valid (projection calls 0). Final-map held-out PSNR **25.19**:
+0.53 dB over online uniform_iid (24.66); D2 26.65, offline 26.90. Final map: 210,085 Gaussians, p95 max-scale 0.075,
mean opacity 0.583 (online with projection: 211,395 / 0.087 / 0.589).
**Reading.** The per-packet scale clamp costs ~0.5 dB on aria1253, about a quarter of the D2 gain (+1.99). The
remaining ~1.5 dB of the stream-time effect is still unexplained. The offline and D2 arms never clamp trained
Gaussians, so earlier online-vs-offline numbers include this setting difference.

## Amendment 1 results (2026-10-09)
- square-1 `noscale_iid`: 21.75 vs online 21.73 (+0.03): the clamp does not matter there.
- Retail_Street run stopped by the user (too slow); partial output under `noscale/v1/failed_attempts/`.
- aria1253 `seq_noscale` (D2 without clamp; first attempt failed on a name clash in the new switch, fixed and rerun,
  archived under `gap_ladder/v1/failed_attempts/name_clash_*`): **26.52**.
With no clamp on either side, D2 − online on aria1253 = 26.52 − 25.19 = **+1.33 dB** (vs +1.99 with the clamp): the
clamp explains ~0.66 dB of the original stream-time gap there; the stream-time effect itself remains (+1.33 dB).

## Amendment 2 results — clamp-matched ladder (2026-10-09, seed 0; all 5 new runs valid, offline gates PASS)
Final-map held-out PSNR:
| scene | clamp | online | D2 | D1 | offline | stream (D2−on) | order (D1−D2) | allocation (off−D1) | total |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| aria1253 | on | 24.66 | 26.65 | 26.59 | 26.90 | +1.99 | −0.06 | +0.31 | +2.24 |
| aria1253 | off | 25.19 | 26.52 | 26.56 | 26.89 | **+1.33** | +0.04 | +0.33 | +1.70 |
| square-1 | on | 21.73 | 21.99 | 21.94 | 22.72 | +0.27 | −0.05 | +0.78 | +0.99 |
| square-1 | off | 21.75 | 21.85 | 21.74 | 22.51 | **+0.10** | −0.11 | +0.77 | +0.76 |
**Reading.** Without the clamp confound the gap is smaller (aria 1.70, square-1 0.76) and its split is scene-dependent:
aria1253 is dominated by training during the stream (+1.33, 78%), square-1 by count allocation (+0.77, ~100%);
order ≈ 0 in both. The clamp only matters online (offline/D2 barely change), as expected.
