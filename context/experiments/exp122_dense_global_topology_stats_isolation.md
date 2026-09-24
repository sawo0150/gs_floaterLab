# Exp122 — unified dense topology-stat isolation

Date: 2026-09-24

## Question

Exp120's RPNG `table_01` unified arm lost 0.186 dB while moving dense RGB
service from 1.40% to 5.61%. This experiment isolates two explanations:

1. the dense RGB replacement changes native radii/viewspace-gradient
   densification statistics; or
2. replacing one historical RGB-D keyframe render with an RGB-only dense
   render removes useful geometry supervision from the shared Adam step.

No scheduler, birth, densify, or prune rule is introduced. This is a
single-factor diagnosis before another downloaded-author-code primitive is
allowed into the mapper.

## Frozen arms

All three arms are fresh runs over the same RPNG archive, held-out manifest,
event stream, and admitted dense views:

- `mass_normalized_control`: no native global-slot replacement;
- `unified_stats_on`: Exp120's one-slot LPM-mass + normalized-variance ERCB
  replacement, including native topology statistics;
- `unified_stats_off`: the same dense render, RGB loss, multi-view Adam step,
  selector proposal/commit, and recent keyframe window, but only the dense
  replacement's radius/viewspace-gradient observation is omitted from native
  densification statistics.

The stats-off switch does not mask any Gaussian parameter gradient. The
remaining keyframes retain full RGB/depth/normal gradients. The selected dense
view is RGB-only because it has no depth target.

## Results

| Arm | PSNR | Delta vs control | SSIM | LPIPS | Renders | Adam | Final GS | Dense global commits | Topology stats skipped | Regular add/remove/churn |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| control | 25.582787 | 0 | 0.847447 | 0.153699 | 38,302 | 3,030 | 417,947 | 0 | 0 | 31,857 / 80,205 / 112,062 |
| unified stats-on | 25.410318 | -0.172469 | 0.840008 | 0.163926 | 38,302 | 3,030 | 418,972 | 1,610 | 0 | 33,476 / 80,790 / 114,266 |
| unified stats-off | 25.424374 | -0.158413 | 0.840737 | 0.163894 | 38,302 | 3,030 | 417,690 | 1,610 | 210 | 31,773 / 80,371 / 112,144 |

The fresh control differs from Exp120's control by only +0.00319 dB, and the
fresh stats-on loss (-0.17247 dB) reproduces Exp120's direction and magnitude
(-0.18612 dB).

Stats-off brings topology churn back to within 82 rows of control, but recovers
only **+0.014056 dB** over stats-on—8.15% of the stats-on PSNR gap. The
remaining loss is -0.158413 dB.

## Verification correction

The source-locked v1 verifier correctly completed all mapping and double
evaluation work, but marked the experiment invalid because it expected
`topology_stats_skipped == dense_global_commits` (1,610). That expectation was
wrong: final-v7 accepts native topology statistics only while its
observation-driven controller is in `frontier`. The immutable selection ledger
contains exactly 210 committed frontier-phase dense replacements and 1,400
balanced/replay replacements. Stats-off skipped exactly those 210 eligible
observations.

The artifact-only v2 verifier corrects only this predicate, reruns no mapping
or evaluation, and passes every fixed-work, causal, held-out, double-eval,
zero-tail, ledger, and quality-floor check. The original failed v1 files are
retained.

## Verdict

**PASS as a single-factor diagnostic.** Dense-origin native topology statistics
substantially change mutation churn, but explain only a small fraction of the
RPNG quality loss. The evidence is consistent with the missing historical
RGB-D keyframe supervision being the primary cause of this one-slot design's
loss.

Consequences:

1. do not solve this result with a new local prune or TileGS CUDA port;
2. do not expand the one-slot replacement to 17 scenes;
3. keep the quality-preserving recent/native RGB-D geometry carrier;
4. make dense/ERCB more active by reallocating non-geometry work or by
   explicitly preserving the aggregate geometry-loss mass, then test that as
   a separate fixed-work factor;
5. any new local evidence or mutation operator must still come from a pinned,
   downloaded author implementation. Paper prose is comparison context only.

## Provenance

- lab implementation commit: `6227d6c`
- VIGS implementation commit: `01195124`
- mapping/evaluation artifacts:
  `results/experiments/exp122_dense_global_topology_stats_isolation/`
- compact table:
  `context/experiments/benchmark_custom/exp122_dense_global_topology_stats_isolation_20260924/summary.md`
- corrected verifier:
  `benchmarks/online_gs/verify_exp122_dense_global_topology_stats.py`

