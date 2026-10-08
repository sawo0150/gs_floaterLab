# D3 — online training with end-of-stream poses — result (2026-10-09)

PREREG: [PREREG.md](PREREG.md). 2 runs, valid (every training view swapped: square-1 1,124 KF + 1,126 dense; no misses).
Final-map held-out PSNR: square-1 21.72 (online uniform 21.73, D2 21.99); aria1253 **23.60** (online 24.66, D2 26.65).
Mean pose change applied: square-1 0.008° / 0.027 units; aria1253 0.16° (p90 0.51°) / 0.036 units.

**Reading.** Training online with end-of-stream poses does not move toward D2; on aria1253 it is 1.06 dB *worse*.
The archives carry no `pose_updates`/`scale_updates` in the final generation for any of the 6 ladder scenes, so the
mapper never moves Gaussians after births here: Gaussians are placed with the pose a KF had at birth while D3
supervises with later poses, which misaligns them. D2 also supervises with final poses yet gains +2 dB, so poses alone
do not explain the stream-time effect; the mechanism of the D2 gain remains open (candidates left: optimizer state
built up while parameters are still being added, interplay of the render-position LR schedule with growth).
