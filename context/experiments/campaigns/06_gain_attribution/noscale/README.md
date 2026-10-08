# No scale projection (diagnostic) — result (2026-10-09)

1 run (aria1253, seed 0, uniform with replacement), valid (projection calls 0). Final-map held-out PSNR **25.19**:
+0.53 dB over online uniform_iid (24.66); D2 26.65, offline 26.90. Final map: 210,085 Gaussians, p95 max-scale 0.075,
mean opacity 0.583 (online with projection: 211,395 / 0.087 / 0.589).
**Reading.** The per-packet scale clamp costs ~0.5 dB on aria1253, about a quarter of the D2 gain (+1.99). The
remaining ~1.5 dB of the stream-time effect is still unexplained. The offline and D2 arms never clamp trained
Gaussians, so earlier online-vs-offline numbers include this setting difference.
