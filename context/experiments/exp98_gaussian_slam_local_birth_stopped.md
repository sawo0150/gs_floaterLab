# exp98 — Gaussian-SLAM local birth first port stopped on legacy-cap coupling

- Date: 2026-09-24
- Status: **stopped during RPNG `table_01`; no quality result**
- VIGS source at run start: `2cf16da4c31f2663b8e84f213b4d3c82503df8c7`
- Official implementation source: Gaussian-SLAM
  `eaec10d73ce7511563882b8856896e06d1f804e3` (MIT)
- Runner: `benchmarks/online_gs/run_exp98_gaussian_slam_local_birth.py`
- Partial output: `results/experiments/exp98_gaussian_slam_local_birth/`
- Detailed record: [summary](benchmark_custom/exp98_gaussian_slam_local_birth_20260924/summary.md)

Exp98 ported Gaussian-SLAM's executed current-view birth rule: low rendered
alpha OR a large positive depth residual, a bounded without-replacement pixel
ticket, and current-frustum radius duplicate rejection. It used only VIGS's
causal online pose/depth. This is implementation-derived; the paper was used
for the methodological review, not as executable pseudocode.

The operator executed, but the experiment did not isolate it. The existing
Aria-derived `adaptive_density_curve` fixed each keyframe's lineage cap from
the pre-ticket content target. The new operator then admitted up to 1,024
rows, after which `enforce_kf_caps()` deleted rows against that smaller legacy
cap. In the final mapper generation, regular topology event 1 removed 1,007
rows by the cap and event 2 removed 11,958. Therefore the intended bounded
birth was being silently redefined by a pre-existing scene-derived control.

The run was interrupted before completion and has no final PLY, held-out
metric, or success claim. VIGS commit `d00e2263` moves cap registration after
the final ticket resolution while leaving the `max_points=None` R4 path
numerically unchanged. The corrected test must use a fresh root and source
lock; this partial output must never be resumed or mixed into a comparison.
