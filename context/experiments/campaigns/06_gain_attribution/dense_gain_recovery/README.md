# Dense supervision gain recovery — 2026-09-25

Status: Aria 1000/5000-step fixed-map and pose diagnostics complete; Aria/RPNG online scope and refresh-repair pairs complete. Dense benefit not recovered; no production promotion.

Question: did appearance-only gradient routing remove the dense RGB gains seen
in historical Gaussian-full polishing? Preserve current native RGB-D mapping.
No Carve, scene-dependent phase cutoff, or production recipe promotion.

1. Capture the current R4 mapper at EOS, including optimizer moments and actual
   mapper training camera poses. Never use evaluation-only trajectory for training.
2. From the identical immutable snapshot, compare KF-only vs KF+admitted dense,
   each with SH-only vs full Gaussian updates. RGB-only loss for all four arms,
   fixed topology/camera poses, same 1,000 single-view Adam/render updates and
   seed-0 random reshuffling. Report 0/250/1000 held-out PSNR. Scope pairs use
   identical image order. This is explicitly an offline, post-EOS diagnostic;
   it is not strict streaming evidence or an exact replay of the old polish run.
3. If useful, compare online auxiliary dense replay appearance vs full scope,
   keeping native RGB-D iterations intact. Both use identical existing primary
   and repeat slots, admission, source LR schedules and selector. No extra work.
4. Evaluate saved online maps independently twice with the existing fixed
   manifest evaluator. Verify equal work/admission/selection and zero-tail.

Start with Aria1253, then transfer the same configuration to RPNG table_01 and
UTMM square-1 if the diagnostic or online result justifies further work. A
negative result must remain negative; no scene-specific tuning. Single-seed
results are pilot evidence, not reproducibility or geometry-quality claims.

Runner: `benchmarks/online_gs/campaigns/gain_attribution/recover_dense_supervision.py`
Artifacts: `results/campaigns/gain_attribution/dense_gain_recovery/`

Budget follow-up (declared before running): repeat the four fixed-map branches
at 5000 map updates using the same original checkpoint, original unaligned
training cameras, LR schedule, seed and RGB loss. This matches the historical
5k-polish budget scale and tests whether dense needs more repeated service;
it is not a new online phase rule. Record the 1000-step negative result regardless
of the 5000-step outcome. Use a separate `dense_gain_recovery_5k/` result root.

## Fixed-map diagnostic — Aria1253

Same captured map/Adam state and actual mapper camera poses; 91 keyframes and
102 admitted dense cameras; 262 fixed held-out views. Initial PSNR 25.757572 dB.

| Pool | Scope | PSNR after 1000 | Gain from same map |
|---|---|---:|---:|
| KF only | SH | 26.221306 | +0.463734 |
| KF + dense | SH | 26.219571 | +0.461999 |
| KF only | full Gaussian | 26.780733 | +1.023161 |
| KF + dense | full Gaussian | 26.311760 | +0.554188 |

Full scope alone does **not** recover the dense advantage: mixed-full remains
below KF-full. This falsifies the simple claim that SH-only routing is the sole
reason dense supervision stopped helping in this setting. All four arms have
identical initial PSNR, unchanged Gaussian count, disjoint held-out sets, and
zero saved/reloaded per-view PSNR differences. SH arms have bit-identical
xyz/scale/rotation/opacity. The fixed-map experiments intentionally have 1000
post-EOS updates; no streaming-quality claim is made.

The original diagnostic runner is archived as `runner_source.py` beside the
checkpoint and its source lock. The current runner also supports a separate
result root and an optional pose-alignment diagnostic.

## Pose consistency follow-up

Comparing training camera poses to the evaluation-only filled trajectory (a
reference, **not GT**) gives mean rotation discrepancies of 0.0233 degrees for
keyframes and 0.7259 degrees for dense frames (dense maximum 6.1871 degrees).
Mean translation discrepancies are 0.000886 and 0.017205 in trajectory units.
This is evidence of a representation/pose mismatch, not proof which trajectory
is correct. The evaluation trajectory is never fed into training.

Predeclared follow-up: from the exact same checkpoint, align each admitted dense
training camera for 64 bounded pose-only RGB steps against the frozen map, then
repeat the identical mixed-full sequence for 1000 map steps. Use the existing
pose learning rate (1e-4), no GT pose/depth, fixed topology. Report all additional
pose renders/Adam steps; this is **not** work-matched against the original four
arms and is only a diagnostic of pose sensitivity. Evaluation camera poses stay
unchanged. Artifacts use `dense_pose_alignment_diagnostic/`.

## Online scope pair

`run_dense_scope_online.py` retains the native RGB-D mapper and changes only
the permitted Gaussian gradients in the existing two single-view dense slots.
The historical harness requires an appearance CLI, so the campaign adapter
sets the effective scope explicitly before installing the optimizer guard;
`scope_override.json` and effective-scope counters must agree. No production
source is edited. The unchanged base requested scope remains visible in raw
runtime metadata; it must not be mistaken for the measured effective scope.

Aria online pair: appearance **25.720004**, full **25.812259 dB**, delta **+0.092254 dB**. Same 13,620 renders / 1,055 Adam, same admission and dense selection order, same historical KF selection, zero-tail and held-out disjointness pass. Both saved maps pass independent double evaluation. This single-seed small gain is not yet a replicated recovery.

Pose-only follow-up completed: 64 steps ×102 dense cameras = **6528 additional pose renders/Adam steps**, followed by the same 1000 map steps and identical image order. PSNR **26.571708 dB**, versus unaligned mixed-full 26.311760 (+0.259949). This partly recovers dense degradation but remains below KF-full 26.7807, and is not work-matched. Pose sensitivity is supported; pose error as the sole cause is not established. Saved-map reload discrepancy is 0.

## Concrete refresh defects and predeclared repair

Code audit found two defects in `install_dense_imu_pose_refresh`:
1. The backend re-brackets dense cameras using currently retained mapper KFs,
   but the wrapper reuses curvature residuals built for the admission bracket.
   In the Aria snapshot, 64/102 dense cameras have different endpoint pairs.
2. The backend skips dense cameras outside its KF range, but the wrapper still
   multiplies their existing pose by the residual on every refresh. This can
   compound rotation. UID2 lies before mapper's first KF4 in this snapshot.

A separate campaign adapter recomputes/caches IMU curvature for the actual
current bracket and skips cameras the backend cannot re-interpolate. It preserves
immutable admission brackets and selector history. Four CPU tests pass for
idempotence, bracket changes, future-IMU exclusion, and no extrapolation.

Test repaired vs unrepaired **full-scope** online pair first, same scene/input,
render/Adam/admission/selection, no extra training updates. No production source
is modified; no evaluation trajectory is used. Report quality separately from
correctness. Runner `run_dense_refresh_repair.py`; artifacts `dense_refresh_repair/`.

## RPNG scope transfer — completed

RPNG table_01: appearance **25.574663**, full **25.377903 dB**, delta **−0.196760 dB**. Same 38302 renders / 3030 Adam, identical admission/dense selection/native historical selection, zero-tail, held-out exclusion, and independent double evaluation all pass. Thus the Aria +0.092 dB does not transfer; unrestricted dense gradients are not adopted as a recovery. The refresh correctness repair is evaluated separately against the same-scope control.

## Refresh repair — Aria completed

The repaired full-scope run reaches **25.839955 dB**, vs unchanged full-scope control **25.812259 dB** (+0.027696). Same render/Adam/admission/dense selection and zero-tail/held-out gates pass; saved-map double evaluation passes. Four refresh calls, 350 corrected camera visits, 99 cached residual builds, 4 unbracketed skips. This is a correctness repair with a small single-run quality difference, not recovered dense benefit. The production/legacy harness source remains unchanged.

Tests now total **6**, including two regression tests executing the actual legacy function extracted by AST: unbracketed rotation compounds, and a stale-bracket residual differs from the current-bracket residual. RPNG transfer uses the same repair without scene-specific tuning.

## Interpretation boundary

The historical [Exp66](../../../exp66/exp66_viewset_density_result.html) RGB-only gain used an Adam reset, a fixed trajectory, and a different initial map/view inventory. The present diagnostic restores the current Adam state and actual causal mapper training cameras. It tests candidate causes under controlled present conditions; it is not an exact recreation of Exp66. The 5000-step follow-up tests budget sensitivity only. Neither scope experiment tests whole-history vs a window; do not interpret its result as evidence against full-history pools.

## Refresh repair — RPNG completed

RPNG table_01 repaired full-scope **25.366390 dB**, control **25.377903 dB**, delta **−0.011513 dB**. Work (38,302 renders / 3,030 Adam), admission, dense selection, zero-tail/held-out, and independent double evaluation pass. The adapter recorded 36 calls, 5,810 corrected camera visits, 267 residual builds, 36 unbracketed skips. Together with Aria +0.027696 dB, this does not show consistent PSNR recovery. Correctness and quality attribution remain separate; no production promotion.

## Budget diagnostic — 5000 steps completed

Same original Aria checkpoint, restored Adam, unaligned actual training cameras, RGB-only loss, fixed topology, and sampling seed as the 1000-step diagnostic. No repair or pose alignment is combined into this experiment.

| Pool | SH-only PSNR | Full Gaussian PSNR |
|---|---:|---:|
| KF only | 26.417100 | 28.261885 |
| KF + admitted dense | 26.432000 | 27.751467 |

The mixed-full arm still trails KF-full by **0.510419 dB**. Increasing the common diagnostic budget from 1000 to 5000 did not restore a dense advantage in this setup. This does not establish that dense can never help, nor test all-arrived dense inventories. All nine verification checks pass, including equal snapshot/initial scores, scope-pair selection order, held-out exclusion, frozen SH geometry, fixed topology and exact saved-map reload scores. **All 5000 updates occur after EOS**; 28.2619 dB is not strict streaming evidence.

## Current decision

- Dense full-Gaussian routing is not adopted: Aria +0.092 dB does not transfer to RPNG (−0.197 dB).
- The two IMU refresh defects are reproduced and repaired in an isolated adapter, with six CPU regression tests. Their PSNR changes (+0.028/−0.012 dB) do not explain the missing gain.
- Pose-only alignment partly improves mixed-full, but uses additional work and stays below KF-only.
- More repeated learning alone does not reverse mixed-vs-KF ordering in the two tested budgets.
- No whole-history vs window experiment was performed here. No conclusion against full-history pools is justified.
- Production and source-locked legacy harness remain unchanged. UTMM scope expansion is deferred because the common improvement failed the RPNG check.

The remaining recovery question is whether causally estimated dense camera poses and the admitted view inventory can provide consistent supervision at the same mapping cost. Historical fixed-trajectory gains cannot be transferred by assuming those conditions match. A follow-up must compare these factors separately before changing pool/sampler or claiming paper alignment.

## 2026-09-25 source audit — historical conditions and narrower conclusions

This is a source/artifact audit, not a new GPU experiment. It corrects any
interpretation that the 5000-step diagnostic matched the historical +3 dB test.

- Historical Exp66 A1 used **100 seconds**, not 5000 steps. Raw CSV records
  KF-RGB 23,320–23,846 updates and D12-RGB 23,335–23,936. KF-RGBDN received
  only 18,524–18,972 updates in the same time. Therefore its 0.28–0.58 dB
  deficit is not a step-matched isolation of depth/normal regularization.
- The retained controlled-refinement code also adds `get_loss_mapping_rgbd`
  to RGB L1+SSIM; that helper includes another masked RGB L1 term as well as
  depth. A clean depth/normal ablation must hold the full RGB objective fixed.
- Exp66 KF-RGB and D12-RGB both use RGB-only loss and nearly equal update
  counts, so their approximately +3 dB within-protocol difference survives
  the original loss-mode confound. This does not make it a strict-online result.
- Old fixed training poses come from `traj_filler(vigs.images)` after EOS
  (`demo.py` around 6108). In the cited historical commit **b05e981d**, the
  filler uses interpolation only as initialization, extracts RGB features,
  connects each non-keyframe to its two neighboring retained keyframes, and
  performs **six motion-only graph updates**. The current dense training path
  uses causal interpolation plus raw-IMU rotation shaping. Correcting residual
  refresh bugs does not reproduce the missing visual pose refinement.
- Seed0 historical pools: KF=88, D02=132 (only 11 overlap KF), D12=784 (69
  overlap KF). Current captured diagnostic pool: KF=91 plus 102 admitted dense.
  Historical D12 is a temporal set, not the current KF+dense union. D02 already
  helped historically, so view count alone is not an established explanation.
- Historical Adam moments are reset; the current diagnostic restores them.
  Initial maps and their optimization histories also differ. RGB-only
  refinement of a depth/normal-trained map does not erase that history.
- Historical curve set has 124 views and `curve_psnr` is
  `-10 log10(mean per-view MSE)`. Current fixed evaluation has 262 views and
  reports mean per-view PSNR. Neither raw levels nor cross-protocol gains
  should be treated as identical metrics.

Evidence: `VIGS-SLAM-paper-full/exp66_axes/viewset_density/stage_a1_summary.csv`,
`manifests/seed0/{KF,D02,D12}.json`, `manifests/eval_split.json`,
`demo.py`, `vigs/gs_backend.py`, and `git show
b05e981d:vigs/util/trajectory_filler.py`.

Updated interpretation: the tested 1000/5000 budgets did not restore dense
benefit; a general budget explanation has NOT been excluded. Pose estimation,
view membership, optimizer state and map history remain confounded across old
and new protocols. Depth/normal interaction remains open, but cannot alone
explain the existing RGB-only mixed-vs-KF reversal. A causal diagnostic should
cross auxiliary KF-vs-dense RGB service with depth/normal on-vs-off, preserving
RGB weighting, view/step schedules, Adam/render counts and evaluation. This is
an unrun diagnostic proposal, not a change to the active geometry-preserving
recipe. Any improved dense pose estimation must use only observations already
available and account for its cost; never train on the evaluation trajectory.
