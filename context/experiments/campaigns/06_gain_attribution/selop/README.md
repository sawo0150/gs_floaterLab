# Selective low-opacity births — result (2026-10-09, aria1253 seed 0, 1 valid run)

116 births, 282,107 points; **80.6% of the points fall on already-explained pixels** (start at 0.12), so the arm is
close to uniform lowop (all at 0.12). Final-map held-out PSNR **25.14** (online 24.66, uniform lowop 25.13, D2 26.65).
Birth probe (immediate Δ on old KFs that see the new points, same 84 events / 444 probes as the baseline):
| | mean Δ | median | p10 | share Δ<0 |
|---|---:|---:|---:|---:|
| baseline (opacity 0.5) | −0.211 | −0.028 | −0.714 | 83% |
| selop | **−0.041** | −0.003 | −0.077 | 70% |
Control views 0.000 in both.
**Reading.** Immediate birth damage drops ~5× (−0.21 → −0.04), yet PSNR gains only +0.48 (same as uniform lowop) of the
+1.99 stream-time gap (+1.33 without the clamp). So the *immediate* covering at birth is a minor part; most of the
stream-time effect arises later — e.g. new Gaussians trained by recent views becoming opaque over old views (a
training-time interference involving new Gaussians), which the probe does not measure.
