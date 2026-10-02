# Preregistration — live ERVS vs RR on aria1253 and square-1 (2026-10-02, before the RR runs)

Scenes aria1253 and UTMM square-1 only: their tracking nearly keeps up at 1× on this machine (overrun 7 s / 1 s),
so the sampler is not masked by tracking lag. Same live setup as the operating-point sweep (v2_trt): actual tracking
+ B mapping, TensorRT, queue 2, renders/KF credit 40, sensor deadline, zero tail. Driver option `--selector rr` only;
no code change.

Runs (results folder `v2_trt`):
- RR at 1×, 1.2×, 1.5× for both scenes (6 runs). ERVS at the same cells is reused from the sweep.
- Repeat at 1× for both arms and both scenes (`--tag _r2`, 4 runs) to estimate live run-to-run spread.

Reading (fixed now):
- Noise per scene = max |run1 − run2| at 1× over the two arms.
- ERVS−RR at a cell is resolved if its magnitude exceeds that noise; at 1× the mean of the two repeats is used.
- "ERVS helps live" is supported only if ERVS−RR is resolved-positive in both scenes at ≥2 of the 3 speeds.
- Also reported: admitted keyframes, renders, tracking overrun, recent-third PSNR. No parameter changes afterwards.
