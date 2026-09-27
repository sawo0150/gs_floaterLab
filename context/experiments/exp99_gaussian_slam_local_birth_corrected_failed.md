# exp99 — corrected official-code local birth fails the quality gate

- Date: 2026-09-24
- Status: **FAIL / stopped before dense coupling**
- VIGS source: `d00e2263`
- Official implementation source: Gaussian-SLAM
  `eaec10d73ce7511563882b8856896e06d1f804e3` (MIT)
- Runner: `benchmarks/online_gs/run_exp99_gaussian_slam_local_birth_corrected.py`
- Results: `results/experiments/exp99_gaussian_slam_local_birth_corrected/`
- Summary: [metrics and gate](benchmark_custom/exp99_gaussian_slam_local_birth_corrected_20260924/summary.md)

Exp99 removed Exp98's legacy-cap coupling: the two final-generation topology
events had cap deletion `0/0` instead of `1,007/11,958`, event count remained
2/2, and all fixed-work/causality checks passed. Nevertheless held-out PSNR
was **23.072144 dB**, which is **−2.512874 dB** versus Exp95 normalized R4 and
**−0.892119 dB** versus fresh vanilla. The predeclared −0.5 dB stop threshold
therefore fired. No dense-topology experiment follows this result.

The immediate capacity evidence is decisive: the fixed 1,024 ticket admitted
185,508 births over 235 events (789/event after radius rejection), and the
final map contained only 173,415 Gaussians versus Exp95's 417,656 (−58.5%) at
the exact same 38,302 renders and 3,030 Adam steps. The 1,024 value was our
adapter choice, not an official Gaussian-SLAM setting; the downloaded author
configs use 30,000, 100,000, or unlimited new-frame samples depending on the
dataset/submap regime.

A second confound is also visible: zeroing depth outside the official seed
mask made VIGS's causal online-density calibrator measure Sobel content only
inside the eligible region, so its per-view rank trace diverged from R4. The
next valid isolation must retain the full-view causal R4 allocation and use
the official Gaussian-SLAM mask/radius test only to choose candidates within
that allocation. It must use a fresh source lock/output and the same −0.5 dB
quality stop.
