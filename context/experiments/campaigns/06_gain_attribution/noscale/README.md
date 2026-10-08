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
