# Exp98 — official-code local birth first attempt (stopped)

- Scene: RPNG `table_01`
- Status: **STOPPED before completion; no PSNR claim**
- Partial output: `results/experiments/exp98_gaussian_slam_local_birth/`
- Code provenance: Gaussian-SLAM author repository, commit
  `eaec10d73ce7511563882b8856896e06d1f804e3` (MIT)

The port successfully ran Gaussian-SLAM's low-alpha/positive-depth-residual
candidate mask, 1,024-point ticket, and current-frustum 1 cm duplicate test.
The partial log contains 156 `MAP_LOCAL_BIRTH` records across mapper resets.
It was deliberately stopped before a PLY or held-out evaluation because the
existing per-keyframe density cap confounded the operator.

In the surviving mapper generation the first two topology transactions were:

| Frame | Input | Added | Split parent removed | Filter removed | **Cap removed** | Output |
|---:|---:|---:|---:|---:|---:|---:|
| 286 | 18,763 | 5,710 | 1,160 | 5,161 | **1,007** | 17,145 |
| 482 | 37,050 | 11,365 | 2,201 | 6,986 | **11,958** | 27,270 |

`create_pcd_from_image_and_depth()` recorded `kf_budget` from the
content-adaptive target before the explicit local-birth ticket replaced that
target. Consequently, the Aria-derived content curve still controlled how
many official-code births survived. This violates the intended single-factor
test and is particularly unsuitable for an anti-overfitting claim.

VIGS commit `d00e2263` makes the final admitted target the lineage-cap basis.
With no ticket, the historical R4 arithmetic is unchanged. A corrected run
must start under a new experiment ID and output root.
