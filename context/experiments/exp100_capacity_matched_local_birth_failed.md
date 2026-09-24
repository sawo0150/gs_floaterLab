# exp100 — capacity-matched official-code replacement still fails quality

- Date: 2026-09-24
- Status: **FAIL / stopped before dense coupling**
- VIGS source: `1721e3cc`
- Official implementation source: Gaussian-SLAM
  `eaec10d73ce7511563882b8856896e06d1f804e3` (MIT)
- Runner: `benchmarks/online_gs/run_exp100_capacity_matched_local_birth.py`
- Results: `results/experiments/exp100_capacity_matched_local_birth/`
- Summary: [metrics and gate](benchmark_custom/exp100_capacity_matched_local_birth_20260924/summary.md)

Exp100 fixed both Exp99 confounds. It preserved the exact full-view causal
online-density trace and used R4's own per-view target inside the official
Gaussian-SLAM seed mask. All archive, event, render, Adam, dense/KF
opportunity, topology-event, disjointness, and zero-tail checks passed.

Quality still failed: **23.581536 dB**, or **−2.003482 dB** versus Exp95 R4
and −0.382728 dB versus fresh vanilla. This recovers +0.509392 dB over Exp99
but remains far beyond the −0.5 dB stop threshold. The operator offered
351,624 candidates and accepted 314,590 after radius rejection, leaving
276,837 final Gaussians versus Exp95's 417,656 (−33.7%).

Therefore low-alpha/positive-depth-residual birth is not a drop-in
replacement for VIGS's blanket PPM keyframe birth. In this global-map,
online-depth regime the current render often declares pixels covered even
though additional appearance capacity remains useful. Gaussian-SLAM's author
implementation operates with much larger initial/new-submap allocations and
different RGB-D/submap assumptions, so copying only its replacement rule
changes the capacity regime.

The next safe isolation, if pursued, is to preserve the proven R4 birth path
bit-for-bit and add the official residual/radius operator as a bounded
supplement on a separate RNG stream. That tests local residual topology
without deleting the capacity responsible for the existing quality gain.
