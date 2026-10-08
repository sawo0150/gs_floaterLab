# Online vs offline tracking — result (2026-10-09, aria1253 seed 0, scale clamp off, 2 valid runs)

Final-map PSNR unchanged by the measurement: online 25.17 (noscale_iid 25.19), offline 26.89 (gates PASS; 26.89).
**Births.** Online: covered old KFs −92.7 summed at births, +85.7 recovered between births (same as before).
Offline: the probe recorded no events (the trainer pool is not synced during the stream, so no "old KFs" exist);
births happen before any training, so there is no trained result to damage.
**Forgetting (final generation, every pool KF every 50 renders).**
| | smoothed peak − final (mean / median / p90) | KFs with drop > 0.5 dB | pool-mean PSNR at the end |
|---|---|---:|---:|
| online | 1.54 / 1.51 / 2.76 | 79% | 25.22 |
| offline | 0.23 / 0.11 / 0.68 | 18% | 26.98 |
Online pool-mean PSNR (training views) climbs to **26.93 at 1,500 renders** (≈ offline's final 26.98) and stays ~26.3–26.9
until ~1,950, then same-KF PSNR drops **−1.55 dB** within one 50-render interval (newest KF frame 1091→1123, which spans
the pose_scale_correction at frame 1118), partly recovers (+1.09), and drops again −0.80 (frames 1201→1217). The
corrections at 1076 (+0.01) and 1187 (−0.08) did little. Offline trains after all corrections and rises monotonically.
**Reading.** Online is not inefficient: it reaches offline-level quality on the KFs it has, then **late-stream events
crash the trained map** (−1.55 and −0.80 dB), and the remaining budget recovers only part of it. The −1.55 coincides
with a Gaussian-moving pose/scale correction; the −0.80 is not yet attributed (snapshot resolution 50 renders).
Earlier readings ("training efficiency", "no forgetting") are superseded.
