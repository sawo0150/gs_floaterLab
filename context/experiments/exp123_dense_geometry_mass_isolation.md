# Exp123 — dense replacement geometry-mass isolation

Date: 2026-09-24

## Question

Exp122 showed that dense-origin native topology statistics explain only 8.15%
of the RPNG quality gap. This experiment asks whether the remaining loss is
merely lower aggregate depth/normal weight after one historical RGB-D
keyframe is replaced, or whether the missing keyframe's view-specific geometry
coverage is essential.

This is an internal diagnostic control, not a paper-method port or a proposed
contribution. No local topology or pruning rule is added. Paper-derived
production primitives remain restricted to pinned downloaded author code.

## Intervention

Both unified arms keep dense-origin native densification statistics disabled,
so Exp122's topology factor is held fixed. The candidate alone preserves the
aggregate geometry-loss mass. If the selected Adam step contains (D)
remaining RGB-D views and one RGB-only dense replacement, only the depth and
normal terms of those RGB-D views are multiplied by

\[
\frac{D+1}{D}.
\]

RGB losses, view identities, normalized-variance ERCB, LPM mass prior, recent
window, renders, Adam steps, and all Gaussian parameter gradients remain
unchanged. The predeclared diagnosis was:

- recovery fraction at least 50%: aggregate geometry mass is substantial;
- recovery fraction at most 20%: view-specific geometry coverage dominates;
- otherwise: mixed cause.

## Fresh results

| Arm | PSNR | Delta vs control | SSIM | LPIPS | Render | Adam | Final GS | Dense commits | Geometry steps / mean scale | Regular churn |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| control | 25.561123 | 0 | 0.847250 | 0.153962 | 38,302 | 3,030 | 417,930 | 0 | 0 / 1.000000 | 111,850 |
| unified, stats off | 25.434710 | -0.126413 | 0.840641 | 0.163971 | 38,302 | 3,030 | 417,848 | 1,610 | 0 / 1.000000 | 112,137 |
| unified, stats off + geometry mass | 25.412915 | -0.148208 | 0.839953 | 0.164555 | 38,302 | 3,030 | 417,785 | 1,610 | 1,610 / 1.062575 | 112,353 |

The candidate changes exactly the 1,610 committed dense-replacement steps.
Its recorded mean and maximum scale match values independently reconstructed
from the immutable recent-window/historical-slot ledger. Every archive,
config, event, admission, render, Adam, held-out, repeated evaluation, and
zero-tail check passes.

Geometry-mass preservation recovers **-0.021795 dB**, or **-17.24%** of the
stats-off gap: it slightly worsens all three image metrics rather than
recovering them. This is not a catastrophic failure and remains above the
-0.5 dB development stop line, but it decisively enters the predeclared
`view_specific_geometry_coverage_dominates` category.

## Verdict

**PASS as a causal diagnosis; reject the method candidate.** The RPNG loss is
not repaired by restoring aggregate depth/normal magnitude. A particular
historical RGB-D keyframe provides spatial geometry constraints that another
RGB-only view plus globally reweighted geometry cannot replace.

Consequences:

1. retire the aggressive one-of-six historical KF to dense replacement;
2. do not tune its ratio, temperature, or scene-dependent phase and do not run
   a 17-scene panel;
3. preserve every native/recent RGB-D geometry carrier in the quality base;
4. use dense/ERCB through the already quality-safe auxiliary work and
   source-backed bounded topology ticket (Exp109/111/117), not by consuming a
   geometry-bearing render;
5. Track B should now isolate the remaining R4 gain between capacity/birth and
   native RGB-D service structure. Dense/ERCB and local topology are no longer
   credible explanations for the bulk +1.2 dB gain.

## Provenance

- lab implementation commit: `cc8e2cb`
- VIGS implementation commit: `b544c28b`
- artifacts:
  `results/experiments/exp123_dense_geometry_mass_isolation/`
- compact summary:
  `context/experiments/benchmark_custom/exp123_dense_geometry_mass_isolation_20260924/summary.md`

