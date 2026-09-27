# Causal visual dense pose — 2026-09-25

Status: Aria/RPNG causal replay and Aria fixed-map pose isolation complete. Dense benefit recovered in the fixed-map diagnostic; consistent online recovery not yet demonstrated.

Hypothesis: dense RGB stopped helping partly because current interpolated/IMU
poses lack the image-based motion-only refinement used by historical Exp66.

## Intervention

Reuse the pretrained DROID feature/context encoders, `FactorGraph.update`, and
native motion-only BA. Use only two currently retained, non-held-out mapper
keyframes bracketing the selected dense image. Endpoint RGB, pose and depth come
from the current causal mapper; no final/evaluation trajectory, MPS, future
packets, or held-out RGB is used. Six recurrent updates (historical filler count),
two native BA iterations per update, optimize the dense pose only. Initial dense
pose remains current IMU-shaped pose, so visual refinement is the intervention.

Mapper full-resolution depth is sampled onto the frontend 1/8 grid. This is
not byte-identical to the historical tracker buffer's native disparity/context
state: context is re-encoded and no historical graph is reconstructed. Record
this limitation. Preserve endpoint poses/depth and Gaussian parameters.

Refine on first service and after dense/endpoint poses change. Cache immutable
image features. If no causal bracket is available, leave that view unchanged.
Apply the previously tested IMU-refresh repair to both paired paths. Preserve
all native RGB-D service, dense admission/selection and Gaussian scope (full).
Record every refinement, endpoint IDs, pose displacement, network-update count,
extra wall time and cache skips. Reject nonfinite outcomes rather than hiding
them. This first experiment adds pose computation, so is map-work matched but
NOT total-compute matched or strict-live evidence.

## Sequence and criteria

1. GPU smoke test: identical RGB/depth/pose must stay near identity; injected
   pose perturbation should be reduced; endpoint poses and depth stay unchanged.
2. Aria1253 paired causal replay: existing repaired-full control vs visual-full.
   Verify same render/Adam, archive, admitted views, dense selection order,
   held-out exclusion and zero-tail. Independently evaluate saved maps twice.
3. Use causally produced corrected poses in the identical existing fixed-map
   checkpoint diagnostic (1000 map steps, same image order) to isolate pose from
   evolving map effects. Keep KF-only and uncorrected mixed references.
4. Transfer the same configuration to RPNG table_01 if the intervention is
   valid. Report negative results and incremental cost. No parameter sweep.

Positive mean PSNR alone does not prove that the historical dense advantage is
restored. Report whether corrected mixed surpasses KF-only, the fraction of the
old mixed deficit recovered, and whether the online change transfers. No recipe
promotion or depth/normal changes in this experiment.

## Aria causal replay — complete

Control (repaired-full) **25.839955 dB**, visual-full **25.824042 dB**, delta **−0.015913 dB**. Equal 13,620 mapping renders / 1,055 map Adam updates, admission and ordered dense selections; zero-tail/held-out/double evaluation all pass. The refiner processed 122 calls /100 unique dense views, 732 recurrent graph updates; added 3.064476 seconds plus 0.030290 seconds network load. Mapping wall changed39.832→42.712 seconds. No quality benefit observed in this pilot. The diagnostic smoke reduced an injected pose-matrix error0.034640→0.000293 with identity error0.000240; all native BA calls asserted fixed anchor poses and depth.

## Fixed-map isolation clarification (before execution)

Online cached corrections may precede the final PGBA update, so directly copying those world poses into the older EOS checkpoint would mix coordinate states. Instead, recompute the same six-step visual refinement against the original checkpoint training KFs at EOS. All observations are already available at that point, but the computation is explicitly post-EOS and is not used in the causal online experiment. No evaluation trajectory/RGB enters training. Verify byte-identical Gaussian tensors/Adam and all camera fields except dense R/T; then run the identical1000 mixed-full map steps. Keep both original mixed-full and KF-full as controls. This replaces step3 cached-pose transfer with a stricter same-map, same-endpoint test.

## RPNG causal replay — complete

Repaired-full control **25.366390 dB**, visual-full **25.482587 dB**, delta **+0.116197 dB**. Equal38,302 map renders /3030 map Adam, ordered dense selection/admission, zero-tail/held-out and independent double evaluation pass. Native historical selection order matches: True. 481 refiner calls /2886 graph updates add10.513194 seconds plus0.041901 load. Mapping wall171.823→183.489 seconds. This recovers some full-scope dense loss on RPNG but is a single-seed result with extra pose computation; not a universal dense advantage.

## Fixed-map 1000-step result and predeclared extension

Identical map/Adam and image sequence: uncorrected mixed **26.311760**, visually corrected mixed **26.728807**, KF-only **26.780733 dB**. Pose intervention recovers **+0.417047 dB**, about **88.93%** of the0.468973 dB mixed-vs-KF deficit, but mixed still trails KF by0.051926 dB. Only dense R/T changed; all other snapshot fields and KF poses were checked. Saved/reloaded evaluation is exact. Additional pose computation is outside the matched1000 map steps and is post-EOS diagnostic work.

Before running: extend the same corrected snapshot and identical seed/order to5000 map steps, matching the existing 5000-step controls. No new pose optimization, hyperparameter change, or view admission change. Use a separate result root `causal_visual_dense_pose_fixed_map_5k`; compare with the already recorded original mixed27.751467 and KF28.261885. This tests whether the pose recovery persists with repeated refinement, not a new online recipe.

## Fixed-map 5000-step result — dense advantage recovered in diagnostic

KF-only28.261885 dB; original mixed27.751467; visual mixed **28.581193 dB**. Pose intervention gains **+0.829726 dB** and corrected mixed exceeds KF-only by **+0.319307 dB**. Exact map/Adam, same image order and count, unchanged KF pose, held-out disjointness and saved/reload checks pass. Pose refinement was computed once at EOS from training snapshots (101 views,2.762933 seconds plus0.036205 model load), then reused across the1000/5000 trials. No strict/live claim.

Preregistered additional control before execution: recompute only correctly bracketed SE3 interpolation+raw-IMU residual for the same original snapshot dense cameras, leaving unbracketed UID2 unchanged, and run5000 identical mixed-full updates. This separates known refresh defects from the additional value of feature-based visual pose refinement. No visual matching is used in this control.

## Refresh-only control — complete

At the same5000 mixed-full map steps, corrected-bracket SE3+IMU poses reach
**27.976400 dB**, compared with original mixed27.751467 (+0.224934) and visual
mixed28.581193. Visual poses outperform this nonvisual repair control by
**+0.604792 dB**. Endpoint/KF pose, Gaussian/Adam state, non-pose camera fields,
image sequence, held-out set, topology and saved/reloaded evaluation gates pass.
Unbracketed UID2 is unchanged in both pose interventions. This shows the visual
pose result is not explained solely by the previously identified refresh bugs.
The visual solve starts from the original snapshot poses; the repair control
uses recomputed current-bracket poses. Both are separately evaluated against the
same immutable Gaussian map and optimizer state.

## Final interpretation for hypothesis 1

| Aria fixed-map condition,5000 map steps | Held-out mean PSNR |
|---|---:|
| KF-only |28.261885|
| KF+dense, original poses |27.751467|
| KF+dense, current-bracket IMU repair only |27.976400|
| KF+dense, feature-based visual pose refinement |28.581193|

Pose estimation is an important causal factor in the tested fixed-map deficit:
changing dense poses alone reverses the mixed-vs-KF ranking. No depth/normal
loss change is required for this recovery (all fixed-map arms already RGB-only).
This is pilot evidence from one scene/seed, not a general proof or a replication
of every historical condition.

Online results remain mixed: Aria−0.015913 dB and RPNG+0.116197 dB relative to
same-scope, IMU-repaired controls. Native historical KF selection order is also
identical in both online pairs. Extra feature-based pose computation is3.064/
10.513 seconds respectively, and total-compute fairness/strict1.5x live budget
have NOT been established. Fixed-map28.581 dB uses5000 post-EOS map updates and
post-EOS pose computation; it is not strict27 achievement.

No production or frozen legacy harness source was modified. All new runners
and adapters are under `benchmarks/online_gs/campaigns/gain_attribution/`.
Artifacts are under `results/campaigns/gain_attribution/` in
`causal_visual_dense_pose`, `causal_visual_dense_pose_fixed_map`,
`causal_visual_dense_pose_fixed_map_5k`, and `refresh_only_fixed_map_5k`.

The next unresolved question is transferring this fixed-map benefit into the
causal mapper: separate evolving endpoint pose/depth from sparse dense service,
without removing native RGB-D constraints or hiding visual pose computation.
Do not treat the current small online changes as recovered online dense gain.
