# Online dense training — active goal

## Objective and acceptance contract (2026-09-25)

Authoritative objective: `/home/colin/.codex/attachments/8d27da10-dc4f-4b97-b4d2-1d063f4b52b9/pasted-text-1.txt`.
Offline diagnostics are supporting evidence, never the completion criterion.

- Fixed scenes: Aria `aria1253`, RPNG `table_06`, UTMM `square-1`.
- One common recipe, seed 0 exploration; final candidate and both controls repeat seeds 0/1/2.
- Controls: current production mapper; KF-only in the new training architecture.
- Ablations: new KF-only, immediate dense+RR, growth+RR, growth+ERVS.
- Final acceptance: higher cross-scene mean held-out PSNR than both controls
  under the same total mapping time budget, including dense pose preparation and transfers.
  Inspect every scene and paired seeds; systematic scene regression cannot be masked by averaging.
- Stream quality curves must demonstrate earlier attainment of comparable quality;
  endpoint quality alone cannot establish fast convergence.
- No future training observations/poses, no held-out RGB in training or pose preparation,
  no final trajectory in training, no updates after the last input/deadline.
- Preserve Gaussian birth and required geometry supervision. No additional carve/pruning variables.
- Keep failures and source/config/input locks; supply reproducible launch/evaluation commands.

## Initial implementation decision

Isolated backend worktree: `/home/intern/VIGS-SLAM-online-view-training`,
branch `research/online-view-training`, baseline `d8c2eb76`.
The current paper backend remains untouched while the candidate is developed.

`vigs/online_view_training.py` owns only causal membership, the paper's normalized
variance/entropy probabilities, and successful RGB service counts. It has no GPU
or optimizer access. Native RGB-D and common photometric optimization commit into
the same count history. Admission costs kappa successful optimizer steps, while
per-image selection counts reflect every RGB contribution in a successful batch.
No selection request, pose solve, or failed optimizer step earns service credit.

Initial common policy: kappa=16, tau=0.01, photometric batch=1, original native
geometry service retained. These are exploratory policy values, not tuned by scene.
RR and ERVS share membership and optimizer/loss code. Existing camera CPU history
is distinct from GPU cache membership. Pose refinement uses current training KF anchors.

Time contract will use the same 1.5x timestamp-paced stream/deadline in all arms.
An explicit clocked harness mode is required: the old fixed-work R4 launcher rejects
some finite-clock flag combinations, and those restrictions must not be bypassed by
mislabeling clocked runs as unbounded. Intermediate evaluation is offline from saved
maps; no evaluator image/pose is passed back into mapping.

## Requirement evidence ledger

| Requirement | Evidence | State |
|---|---|---|
| Growth/ERVS completed RGB counts | v16 recent-photo memory, total growth credit preserved; 24 helper/policy/integration checks and actual ledger reconstruction pass | Implemented; recent-memory policy remains exploratory |
| Causal pose and dataset exclusion | Current-KF brackets, held-out origin/service checks, deferred preparation through v16; color/cache diagnostics use training prefixes only | Exercised in arrival harness; no evaluator inputs to mapper |
| Shared photometric optimizer | Actual backend native/photo steps through v16; resident keyframe targets reused | Implemented; dense quality superiority incomplete |
| Same total mapping time / zero-tail | v15 nine controls, six Growth/sampling runs and v16 three runs all pass setup/full-wall/Adam/input guards | Frozen tracking; concurrent SLAM throughput unmeasured |
| Three-scene seed0 comparisons | v15 controls/ablation and v16 complete; Growth vs immediate +2.440dB mean, v16 vs RR +0.004dB mean | v17 complete, mean +0.0411dB vs KF but RPNG−0.2245; policy not accepted |
| Stream quality curves | v6 real saved maps, shared-coordinate exports, independently repeated evaluation | All three paired curves complete; coarse sampling and material Aria alignment residual limit interpretation |
| Three-seed candidate and controls | No accepted final candidate | Pending |
| Both controls surpassed without systematic scene regression | v17 mean +0.0411dB vs KF, but RPNG−0.2245 and Aria−0.0316 | Not satisfied; repeated seeds also missing |
| Production/live-loop integration and paper alignment | Isolated backend/harness only; production checkout clean | Pending; no concurrent full-SLAM throughput claim |


Goal remains active. Unit tests are correctness evidence, not quality evidence.

## 2026-09-25 implementation checkpoint

- Core 8 CPU tests PASS: objective stationarity, shared native/photo counts, successful-step growth,
  held-out/future-anchor rejection, RR incremental epoch, ablation membership, stale commit/reset, extreme tau.
- Added backend common full-Gaussian RGB optimizer and native commit hook in isolated worktree.
- Added explicit clocked harness callback API; effective runtime is recorded as finite 1.5x.
- v1 KF-only launch failed before mapping: legacy observation gate required dense_rr_imu profile.
  Preserved `v1/.../mapping.log`. v2 uses the same geometry profile and explicit skip_dense_input,
  so KF-only avoids unnecessary dense RGB preparation without changing the geometry recipe.
- v2 Aria KF-only clocked pilot running. This is implementation progress, not acceptance.

## v2 Aria KF-only pilot — completed

Held-out262 images **27.620639dB**. Finite1.5x budget97.649998s, mapping97.636774s.
Native830 + common RGB14682 = actual Adam15512; physical renders27858.
All native/photo service counts agree with actual optimizer completions; held-out mapping/birth overlap0,
post-EOS updates0, optimizer completions after deadline0, independent double evaluation PASS.
Multiple map resets are isolated into generation histories (completed steps0/0/31/0/15481).
This is the new architecture control, not a goal success. Production and dense ablations remain pending.
Artifact: `online_dense_training/v2/aria/aria1253/kf_only/seed0/result.json`.

## v2 Aria growth+ERVS pilot — quality failure

Held-out **26.419423dB**, KF-only27.620639 대비 −1.201217dB.
Finite1.5x97.65s 내 97.648181s; native827+photo7157=Adam7984, renders20300.
Final generation: KF91, eligible dense924, admitted497, trained455.
Visual pose676 calls/14.688828s. Counts/deadline/held-out/zero-tail/double-eval PASS.
품질 목표 미달.
같은 Growth의 RR 대조와 production baseline을 이어서 실행한다.
단순히 dense 사용을 크게 늘리고 global count를 연결하는 것으로 online 이득이 복원되지 않았다.
Artifact: `online_dense_training/v2/aria/aria1253/growth_ervs/seed0/result.json`.

### v2 growth membership audit — oldest-first admission defect

Of924 eligible dense frames,497 admitted UID6–688. UID800–1303:343 eligible,0 admitted,0 service.
UID0–399:290 admitted/5982 services; UID400–799:207 admitted/685 services.
The implementation always popped the oldest backlog item, so growing membership failed to incorporate
newer scene coverage despite causal arrivals. This is a specific implementation defect, not proof against dense RGB.
Next v3 intervention (after current RR control finishes): batch current offers atomically,
then admit temporal maximin candidates relative to existing KF+dense training timestamps/UIDs,
using only already-observed candidates, with newest UID as deterministic tie break.
Keep kappa/tau/pose algorithm/native work unchanged to isolate membership selection.

## v2 Aria growth+RR control — completed

Held-out25.831409dB,97.633724s; renders20335,Adam8039; finiteclock/zero-tail/held-out/double-eval PASS.
ERVS26.419423 is +0.588013 over RR in this flawed oldest-first membership architecture,
but both lose to KF-only27.620639. This does not establish a successful combined system.

## v3 change and test preregistration

- Atomic offer + temporal-maximin admission implemented. 10 CPU tests PASS including
  new interval coverage with a large old backlog and input-order independence.
- Preserve9 v2 source files under `source_v2/index.json` before modification.
- Report actually selected common-pool dense UIDs in mapper runtime/mapped_uids,
  rather than relying on the now-unused legacy replay queue. Held-out split remains fixed.
- Next: v3 Aria growth+ERVS and timed production control, same kappa/tau/native recipe/1.5x budget.

## v3 Aria growth+ERVS — coverage repaired, quality still below control

Held-out26.949130dB (+0.529707 vs v2; −0.671510 vs KF-only).
Mapping97.637988s, renders19371, Adam7055; all deadline/held-out/zero-tail/double-eval checks PASS.
439 dense admitted, max UID1266;144 admitted beyond UID800 (v2:0). Photo6228 commits.
Pose calls1078 / 22.529990s; admission change recovered coverage and quality but not the goal.
Next hypothesis: κ16 admits more views than can be repeatedly refined after paying pose preparation.
Explore common κ64 (not per-scene), retaining temporal coverage selection and the same τ/native service.

## v3 Aria production control — completed

Held-out25.810882dB,97.632708s/97.649998s budget; renders23260,Adam10973.
Finiteclock/zero-tail/no-deadline-overrun/held-out/double-eval PASS.
V3 growth+ERVS beats production by1.138247dB but loses to the new KF-only by0.671510dB; goal not met.
This is the current production R4 recipe run under the explicitly clocked adapter, with its existing idle service.
Next v4 common κ64 keeps all other policy values unchanged. Candidate parameters are written into contract.json.

## v4 κ64 Aria result — no further gain

Held-out26.882017dB (κ16 temporal coverage26.949130; KF-only27.620639).
Mapping97.646266s/97.649998s; Adam10362, renders22708; all execution/evaluation checks PASS.
161 dense admitted,9532 photo commits;688 visual solves/13.846276s.
Reducing preparation work increased updates but did not improve quality. No success claim.
Continue the same κ64 recipe on RPNG table_06 and UTMM square-1 against production and new KF-only,
using `run_online_dense_panel.py`. No further Aria-only policy tuning before those transfer results.
Pending investigation: pose cache currently checks anchor poses but not depth revisions; verify/fix
that readiness contract separately. Reusing converged image correspondences for anchor-only pose updates
is another possible cost reduction, not implemented or claimed yet.

### Panel v4_k64/rpng/table_06/production/seed0

held-out 24.400529dB, 138.361/138.367초, 3373 Adam/25770 renders, 실행 계약 PASS.
Artifact: `online_dense_training/v4_k64/rpng/table_06/production/seed0/`.

### Panel v4_k64/rpng/table_06/kf_only/seed0

held-out 25.226998dB, 138.351/138.367초, 6695 Adam/32757 renders, 실행 계약 PASS.
Artifact: `online_dense_training/v4_k64/rpng/table_06/kf_only/seed0/`.

### Panel v4_k64/rpng/table_06/growth_ervs/seed0

held-out 24.807749dB, 138.351/138.367초, 3172 Adam/25224 renders, 실행 계약 PASS.
Artifact: `online_dense_training/v4_k64/rpng/table_06/growth_ervs/seed0/`.

## Pose cache / correspondence preparation checkpoint

`vigs/dense_pose_inputs.py` now fingerprints the sampled anchor depths consumed by
DROID plus camera calibration. Four CPU tests pass, including an in-place depth
edit with unchanged pose/object identity. This helper is not wired into v4, whose
source remains fixed while the cross-scene panel runs.

Prepared an isolated `dense_visual_pose_reuse.py` cost ablation. Cold path uses the
same six neural graph updates; warm path reuses image correspondence targets and
weights, but performs motion-only BA with current anchor poses and depths. This
is not reuse of an old corrected pose. Cached measurements live on CPU. Replaced
RGB objects, changed calibration, or changed anchor pairs take the cold path.
No quality claim yet; the module is not imported by the active v4 panel.

Before integration, run `check_dense_correspondence_reuse.py` after the panel
releases the GPU. Its synthetic checks change the online world scale/depth with
fixed image correspondences and require recovery of the corresponding dense
translation while leaving anchor poses/depth unchanged. Then freeze v4 source,
wire the depth cache fix, and compare full neural vs correspondence reuse under
the same online time contract. Current syntax check passes; CUDA checks pending.

### Panel v4_k64/utmm/square-1/production/seed0

held-out 21.092689dB, 80.727/80.714초, 7658 Adam/15569 renders, 실행 계약 PASS.
Artifact: `online_dense_training/v4_k64/utmm/square-1/production/seed0/`.

## RPNG v4 diagnosis and deferred pose-refresh candidate

RPNG production24.400529, new KF-only25.226998, growth+ERVS24.807749dB.
Candidate is +0.407220 over production but -0.419249 below KF-only. The three-scene
acceptance remains unmet. Candidate native/photo Adam1567/1605 versus KF1831/4864.
Visual solve cost2.777664s (117 solves,718 cache hits) alone is insufficient to
explain the service deficit. Candidate repair audit instead records27 eager
refresh calls affecting31,054 dense cameras, despite only49 admitted dense images.
This establishes redundant work; its exact runtime contribution needs measurement.

Prepared `vigs/dense_pose_lazy_refresh.py` in the isolated backend. A PGBA refresh
marks history stale; a selected dense camera is interpolated/IMU-corrected with
current training anchors immediately before visual refinement. Full history and
membership are retained. Three CPU tests PASS: current-anchor preparation before
training, no unselected/repeated work, history restoration after failure and
retry, replacement-camera invalidation, and KF bypass. Not wired into v4.
This is now the first cost intervention to test; correspondence reuse remains a
separate prepared ablation rather than mixing both changes at once.

Budget audit caveat: v4 UTMM production reports mapping80.726514s versus
budget80.714126s (+0.012389s), although all actual Adam completion timestamps are
within deadline. The current result.json `no_deadline_overrun` checks Adam only;
it must not be cited as proof that *all* mapping work finishes within budget.
Add an explicit total-mapping overrun field/check in the next runner version and
preserve the original v4 result. Final acceptance requires the full cost contract.

### Panel v4_k64/utmm/square-1/kf_only/seed0

held-out 22.481081dB, 80.706/80.714초, 17925 Adam/25915 renders, 실행 계약 PASS.
Artifact: `online_dense_training/v4_k64/utmm/square-1/kf_only/seed0/`.

### Panel v4_k64/utmm/square-1/growth_ervs/seed0

held-out 22.592412dB, 80.733/80.714초, 8960 Adam/16887 renders, 실행 계약 PASS.
Artifact: `online_dense_training/v4_k64/utmm/square-1/growth_ervs/seed0/`.

## v4 transfer completed / v5 preregistration

UTMM KF-only22.481081, dense22.592412dB (+0.111331), production21.092689dB.
Aria/RPNG dense still lose to new KF-only. V4 UTMM dense mapping80.733022s exceeds
80.714126s budget by18.896ms although no Adam completed after the deadline.
These two UTMM overruns prevent full-budget acceptance; do not hide them under
old Adam-only `valid` fields. V5 now explicitly checks total mapping wall time.

Preserved nine active v4 sources in `source_v4/index.json` before editing.
Installed depth/calibration cache identity checks in the visual pose wrapper.
Both v5 arms use this correction; v5_depth_lazy additionally defers dense pose
refresh until training preparation. New candidates prepare against current
anchors before their first selected use as well. No growth/ERVS/native geometry
parameters change (common kappa64/tau.01/seed0/1.5x). Correspondence reuse is NOT
part of either arm, so the first cost comparison isolates deferred preparation.
Runner: `run_online_pose_preparation_panel.py`, RPNG then Aria then UTMM, each
v5_depth and v5_depth_lazy. Both compare to existing controls; no acceptance yet.

### Numerical pose checks

Initial check launcher failed before GPU work because its Python import path
omitted benchmarks/online_gs; preserved `pose_preparation_checks/*.log`. Corrected
script path and saved successful v2 logs separately. Actual backend interpolation
plus IMU repair: four current-anchor/bracket changes give eager vs deferred max
absolute pose error0 in every case,12 vs4 view refreshes. CPU tests7 PASS.
Prepared correspondence-reuse solver also passes synthetic CUDA checks: changing
world scale/depth1.0→1.5 with immutable matches recovers translation with error
5.91e-8/4.04e-7; anchor poses/depth unchanged. This validates a numerical mechanism,
not mapping quality, and remains a separate unintegrated candidate.

### Pose preparation panel v5_depth/rpng/table_06/growth_ervs/seed0

held-out 24.573715dB, 138.351/138.367초, 3100 Adam; 전체시간 포함 계약 PASS.
Artifact: `online_dense_training/v5_depth/rpng/table_06/growth_ervs/seed0/`.

### Pose preparation panel v5_depth_lazy/rpng/table_06/growth_ervs/seed0

held-out 24.486636dB, 138.351/138.367초, 3088 Adam; 전체시간 포함 계약 PASS.
Artifact: `online_dense_training/v5_depth_lazy/rpng/table_06/growth_ervs/seed0/`.

## v5 RPNG paired result / snapshot evaluation infrastructure

Depth-aware eager24.573715, deferred24.486636dB (−0.087079).
Both complete within138.367s with zero-tail/held-out/Adam/full-wall checks PASS.
Eager pose refresh30,132 views versus deferred73 (1.174958s measured deferred
preparation). Visual solves115→108; native/photo Adam1561/1539→1633/1455.
Scheduler completed packets178→192 and dropped-oldest74→60; photometric wall
10.198→10.554s. Deferred preparation reduces redundant work and input lag but
has not improved RPNG quality or increased photometric optimizer count. It is
not adopted as the final recipe. Aria and UTMM pairs remain running.

Prepared independent stream-quality infrastructure (NOT wired into active v5):
- `vigs/online_map_snapshots.py`: immutable CPU copies of rendered Gaussian
  parameters, actual training KF poses, origin/service UIDs, actual completion
  count/time, observer copy time, skipped targets and deadline flags. No optimizer
  aliases, no evaluator inputs. Quarter-stream targets are observation-only;
  they never open/close a mapping or topology phase. All arms must share observer.
- `snapshot_camera_alignment.py`: post-run similarity transform between shared
  training-camera worlds; records center and orientation residuals and rejects
  degenerate centers. Does not assume all tracker changes are a global gauge.
- `export_online_snapshot.py`: PLY plus aligned evaluation trajectory export;
  strips inactive SH coefficients because the existing evaluator infers active
  degree from PLY fields. Existing output directories are never overwritten.
- Eight CPU tests PASS (4 snapshot,3 alignment,1 export): immutable state after
  future updates, held-out rejection, honest late capture, deadline skip, known
  Sim(3) recovery, nonrigid residual visibility, degeneracy rejection, SH/pose
  export consistency. These are infrastructure checks, not convergence evidence.

Remaining before curve claims: wire observer after v5 source freeze, verify a
real captured state renders identically before/after export, inspect real
snapshot alignment residuals, and compare identical held-out cohorts across time.
No final-evaluation trajectory or image is ever passed to the mapping observer.

### Pose preparation panel v5_depth/aria/aria1253/growth_ervs/seed0

held-out 26.704641dB, 97.631/97.650초, 10142 Adam; 전체시간 포함 계약 PASS.
Artifact: `online_dense_training/v5_depth/aria/aria1253/growth_ervs/seed0/`.

### Pose preparation panel v5_depth_lazy/aria/aria1253/growth_ervs/seed0

held-out 26.791474dB, 97.660/97.650초, 9793 Adam; 전체시간 포함 계약 FAIL.
Artifact: `online_dense_training/v5_depth_lazy/aria/aria1253/growth_ervs/seed0/`.

### Pose preparation panel v5_depth/utmm/square-1/growth_ervs/seed0

held-out 22.362610dB, 80.722/80.714초, 8353 Adam; 전체시간 포함 계약 FAIL.
Artifact: `online_dense_training/v5_depth/utmm/square-1/growth_ervs/seed0/`.

## Deferred RGB preparation candidate (not yet connected to v5)

RPNG event ledger totals ~80.1–80.3s packet work and ~10.2–10.6s photo work,
leaving ~47.7–47.9s including archive preprocessing, ingestion, and idle waits.
This residual is NOT all attributed to RGB decoding without instrumentation.
Source inspection confirms `archive.dense_records` eagerly decodes/undistorts
EVERY candidate before growth admission, and `register_causal_dense_views`
constructs a GPU Camera then moves RGB back to CPU for every candidate. Only
~40–50 dense views were ultimately admitted in these RPNG runs.

Prepared `vigs/deferred_dense_observations.py`: arriving intervals register UID
metadata only; a selected, admitted image is decoded and IMU-shaped once, then
materialized as a Camera. Full arrived inventory is retained independently of
training membership and GPU residency. No archived/final interpolation pose is
used as an initial estimate: a placeholder must be replaced by current-anchor
lazy preparation before visual refinement. Enforce that wrapper is installed.
Four CPU tests PASS: no decode on arrival, only admitted selections decode,
held-out/unobserved/missing-anchor rejection before I/O, and reset reconstruction
without forgetting already-arrived observations. Live integration and GPU quality
are pending; v5 source remains fixed until its panel finishes.

Aria v5 eager26.704641, lazy26.791474dB (+0.086833), both below KF27.620639.
Lazy total mapping97.660484 exceeds97.649998 by10.486ms, correctly marked invalid
by the new total-cost check; all Adam steps still end before deadline. Preserve
this failure. Candidate scope must also guard input/preparation costs, not only
optimizer launches. Final proof cannot waive small overruns.

### Pose preparation panel v5_depth_lazy/utmm/square-1/growth_ervs/seed0

held-out 22.331859dB, 80.716/80.714초, 8691 Adam; 전체시간 포함 계약 FAIL.
Artifact: `online_dense_training/v5_depth_lazy/utmm/square-1/growth_ervs/seed0/`.

## v5 completion / v6 integrated preparation pilot

UTMM v5 eager22.362610/lazy22.331859dB, both below KF22.481081 and both exceed
full wall budget (8.262/1.450ms). Together with Aria/RPNG this rejects lazy pose
refresh alone as a quality restoration. All v5 attempts and source11 files are
preserved (`source_v5/index.json`); no failures are re-labelled as valid.

V6 connects the deferred RGB inventory to the actual harness dense-arrival
callback and the common trainer's admission/selection boundary. The trainer sees
all arrived UID metadata, not only materialized cameras. Selected dense views
are decoded/IMU-shaped/materialized inside the same live clock and then rebased
on current training anchors by the lazy wrapper before visual refinement.
No archived/final interpolation pose is used for initialization. Birth and native
RGB-D work remain unchanged. Added archive RGB call/cache-miss/wall telemetry.

The common read-only stream observer is now connected with CPU copy time inside
the live budget, and CPU-only disk serialization afterward. V6 uses a common
100ms shutdown reserve (v5 used20ms and repeatedly overran during preparation).
The total budget remains1.5x and no post-input Adam is allowed. All fresh v6
controls must use the same reserve and observer; old v4/v5 numbers are context,
not a fully matched acceptance comparison for v6.

First pilot: RPNG table_06 growth_ervs kappa64/tau.01/seed0, tagv6_deferred,
`--lazy-dense-refresh --defer-dense-preparation --snapshots --deadline-reserve-ms100`.
Backend policy/snapshot tests14 PASS; deferred inventory tests4 already PASS.
Next: inspect pilot execution, real snapshot gauge/export consistency, then fresh
KF-only/production controls and other two scenes with identical instrumentation.
Goal remains active; no final candidate or full ablation/3-seed evidence yet.

### Deferred panel v6_deferred/rpng/table_06/growth_ervs/seed0

held-out 25.006464dB, 138.268/138.367초, 4501 Adam; 전체시간 계약 PASS.
Artifact: `online_dense_training/v6_deferred/rpng/table_06/growth_ervs/seed0/`.

## v6 RPNG pilot completed / real snapshot roundtrip

Held-out25.006464dB;138.267609/138.367006s,4501 Adam/30,451 renders.
Finiteclock/zero-tail/held-out/synchronized Adam/full-wall checks PASS. This is
higher than v5_lazy24.486636 but reserve/observer differ, so use fresh v6 controls
for acceptance. Still below the earlier KF-only25.226998 context result.

Deferred store saw1989 eligible observations, prepared65; dense RGB preparation
0.615796s, IMU shaping0.120074s, Camera creation0.076988s, inventory0.663490s.
All archive RGB calls4958 with251 cache misses cost2.244858s. CPU snapshot copies
at34.872/69.270/104.369s cost0.010034s total. Saved snapshots contain49,492 /
153,908 /253,012 Gaussians. All captures completed before deadline.

Actual three-snapshot PLY roundtrip verified with the project's GPU renderer:
three saved training camera views per snapshot,9/9 max absolute render error0.
No ground-truth RGB or evaluation trajectory was used in this serialization test.
`stream_snapshots/roundtrip/result.json` and `snapshot_roundtrip.log` preserve evidence.
Post-run camera-world alignment center RMSE0.00800/0.00707/0.00620m, max orientation
1.93/1.37/1.59degrees; these nonzero residuals must accompany any quality curve.
Exports under `stream_evaluation/` remain marked alignment_quality_accepted=false;
no convergence superiority claim is made from these artifacts alone.

Started `run_online_deferred_panel.py`: reuse source/contract-verified RPNG pilot,
then fresh KF-only/production and remaining Aria/UTMM candidate+two controls.
All use snapshots,100ms reserve,1.5x total budget,seed0. Individual outcomes are
recorded automatically in card/INDEX/STATUS. Main quality/3seed/ablation/curves
acceptance remains incomplete.

### Deferred panel v6_deferred/rpng/table_06/kf_only/seed0

held-out 25.229089dB, 138.275/138.367초, 6711 Adam; 전체시간 계약 PASS.
Artifact: `online_dense_training/v6_deferred/rpng/table_06/kf_only/seed0/`.

## Fresh v6 RPNG KF-only / curve evaluator preparation

Fresh KF-only25.229089 vs deferred dense25.006464 (−0.222625), with identical
1.5x/100ms reserve/snapshot instrumentation and full-wall checks PASS. Candidate
has2677 single-image photo commits versus KF4879; native commits1824 vs1832.
The input preparation change therefore has not restored RPNG dense superiority.

Prepared `evaluate_online_stream.py`: uses the existing dataset-specific double
evaluator for each exported state, then explicitly enforces one identical held-out
UID cohort across all states and the endpoint. Records actual state availability
(copy completion time), optimizer count, alignment residuals and per-view PSNR.
Three CPU tests PASS for fixed-cohort aggregation, changed-cohort/time rejection,
and duplicate/nonfinite data rejection. No GPU curve evaluation launched while
v6 panel owns the GPU; no exact continuous first-attainment claim is made.

Open source-backed hypothesis, not a diagnosed cause: native map accumulates
`loss_mapping += view_loss` before backward with no batch averaging; common photo
uses one image loss and the same Gaussian Adam. Actual candidate native batch
sizes11/12/15/16/17 occur54/580/7/7/1176 times; photo is1 image for2677 steps.
KF-only native sizes are similar. The shared optimizer sees unlike gradient
scales/distributions. Determine this effect with explicit controlled diagnostics;
do not silently change loss weights or claim that depth/normal is the cause.
Other Aria/UTMM matched v6 comparisons continue before another policy change.

### Deferred panel v6_deferred/rpng/table_06/production/seed0

held-out 24.456206dB, 138.274/138.367초, 3476 Adam; 전체시간 계약 PASS.
Artifact: `online_dense_training/v6_deferred/rpng/table_06/production/seed0/`.

## RPNG service balance and location diagnostic

Saved `v6_deferred/rpng/table_06/growth_ervs/seed0/service_balance_diagnostic.json`.
Final generation:70 admitted dense /186 KF; median accumulated service9 /136.
Dense accounts for1601/2677 photometric contributions (~59.8%), while native
RGB-D service remains separate mandatory work. With the exact final count vector,
current tau.01 gives dense probability mass.35955; diagnostic-only tau.003/.001
would give.53832/.82447. These are probability calculations, not executed runs or
proof that stronger balancing improves quality. Do not change per-scene knobs.

Fixed held-out frames grouped by chronological quartiles (138/139/139/139 views):
- indices0–685: dense22.9525 /KF22.9243 (+0.0282)
-690–1380:24.9013 /25.1396 (−0.2383)
-1385–2075:26.1398 /26.5724 (−0.4326)
-2080–2766:26.0175 /26.2634 (−0.2459)
This is a final-map regional diagnostic, NOT a convergence curve. Most of the
loss is outside the earliest quartile. Continue the fixed v6 three-scene panel;
remaining hypotheses include pose preparation cost, actual gradient scale, and
insufficient balancing under the mandatory native service distribution.

### Deferred panel v6_deferred/aria/aria1253/growth_ervs/seed0

held-out 26.848187dB, 97.559/97.650초, 9896 Adam; 전체시간 계약 PASS.
Artifact: `online_dense_training/v6_deferred/aria/aria1253/growth_ervs/seed0/`.

### Deferred panel v6_deferred/aria/aria1253/kf_only/seed0

held-out 27.521864dB, 97.553/97.650초, 16000 Adam; 전체시간 계약 PASS.
Artifact: `online_dense_training/v6_deferred/aria/aria1253/kf_only/seed0/`.

## v6 Aria comparison / repeated pose work

Fresh Aria KF-only27.521864 vs dense26.848187 (−0.673677); both satisfy full-wall
budget/zero-tail/held-out checks. This does not meet goal acceptance.
`v6_deferred/pose_repetition_diagnostic.json` groups actual visual solves by
(uid,left,right). RPNG65 first pairs cost1.903901s and251 repeat pairs4.807140s;
Aria148 first pairs cost3.736683s and493 repeat pairs9.560723s. This identifies
where correspondence reuse could reduce repeated neural work, NOT measured
savings. The prepared solver already passed synthetic current-depth/pose CUDA
checks; online quality/cost remains untested. Finish fixed v6 transfer first,
then compare that one preparation change with kappa/tau/native losses unchanged.

Exported Aria real snapshot states for later GPU evaluation. Their camera-world
alignment (25/50/75% targets) has center RMSE0.00292/0.01124/0.07133m and maximum
orientation errors0.190/0.512/3.315degrees. The last residual is material;
these curves cannot be labelled pure photometric convergence without addressing
or qualifying online trajectory changes. Keep alignment acceptance false and
compare common evaluation coordinates/cohorts across arms before any claim.

### Deferred panel v6_deferred/aria/aria1253/production/seed0

held-out 25.872583dB, 97.554/97.650초, 10953 Adam; 전체시간 계약 PASS.
Artifact: `online_dense_training/v6_deferred/aria/aria1253/production/seed0/`.

### Deferred panel v6_deferred/utmm/square-1/growth_ervs/seed0

held-out 23.175359dB, 80.647/80.714초, 11075 Adam; 전체시간 계약 PASS.
Artifact: `online_dense_training/v6_deferred/utmm/square-1/growth_ervs/seed0/`.

### Deferred panel v6_deferred/utmm/square-1/kf_only/seed0

held-out 22.405205dB, 80.683/80.714초, 18103 Adam; 전체시간 계약 PASS.
Artifact: `online_dense_training/v6_deferred/utmm/square-1/kf_only/seed0/`.

## Paired snapshot pose diagnostic (2026-09-25)

Saved `v6_deferred/{aria/aria1253,rpng/table_06}/paired_snapshot_pose_diagnostic.json`.
Candidate versus KF-only common keyframe w2c matrices are exactly equal at all
three captured states: Aria23/45/67 and RPNG32/90/147 common KFs. Thus Aria
75% final-trajectory alignment residual is shared by these arms, not evidence
of candidate-only pose bias. Use a common coordinate transform and fixed
evaluation cohort for relative online quality; do not label this pure
photometric convergence. RPNG production differs from KF-only by maximum
w2c element0.001113/0.007334/0 at the respective states. Actual capture times
also differ and must remain on the curve. No GPU snapshot PSNR measured yet.

### Deferred panel v6_deferred/utmm/square-1/production/seed0

held-out 21.381898dB, 80.678/80.714초, 7752 Adam; 전체시간 계약 PASS.
Artifact: `online_dense_training/v6_deferred/utmm/square-1/production/seed0/`.

## v6 complete / v7 correspondence reuse preregistration (2026-09-25)

| scene | production | KF-only | dense | dense minus KF |
|---|---:|---:|---:|---:|
| RPNG table_06 |24.456206|25.229089|25.006464|−0.222625|
| Aria1253 |25.872583|27.521864|26.848187|−0.673677|
| UTMM square-1 |21.381898|22.405205|23.175359|+0.770154|
| mean |23.903563|25.052053|25.010003|−0.042049|

All nine finite1.5x runs pass whole mapping wall, zero-tail, held-out checks.
Dense improves production by1.106441dB mean but fails new-KF comparison and
scene-regression requirement. This seed0 candidate is NOT accepted. Frozen
`source_v6/index.json` preserves13 Python sources matching trial source locks.

Next single-change test: `v7_correspondence`, same three scenes, kappa64/tau.01,
native geometry/topology unchanged, deferred CPU RGB/current-anchor lazy refresh,
snapshots and100ms reserve unchanged. Reuse image correspondences for repeated
dense image/anchor pairs; refit pose using current anchor poses and depths. New
image/pair/calibration recomputes six neural updates. This avoids reusing stale
pose/depth; it remains experimental because correspondence estimates may depend
on their original solve geometry. No quality/speed gain assumed in advance.

Refiner factory is opt-in; neural-update audit distinguishes cold6/warm0.
Cached source tensor references prevent identity recycling. CUDA synthetic
checks pass changed world scale1/1.5 with translation errors5.91e-8/4.04e-7,
anchor/depth unchanged.25 CPU unit tests pass; runner/refiner compile passes.
Pytest is absent in this environment; the repository tests were run with their
native unittest runner. CUDA artifact: `pose_preparation_checks/v3/`.
Runner: `run_online_correspondence_panel.py`; each arm records results automatically.

## Shared-coordinate exports prepared

`export_paired_online_snapshots.py` requires identical final reference trajectories
and identical common online KF poses. Actual RPNG and Aria candidate/KF snapshots
pass, and all six exported pairs have byte-identical evaluation trajectory files.
RPNG pair-only common KFs33/90/147 (earlier three-arm diagnostic used32/90/147);
Aria23/45/67. Original Gaussian tensors/membership remain unchanged; fitting uses
the intersection of training KFs only. Each export records both source snapshot
hashes and actual copy-completion times. Outputs: each arm's
`stream_evaluation_shared/`; paired summary `shared_snapshot_export.json`.

Evaluator opt-in `--shared-coordinates` requires these prepared exports and locks
PLY/trajectory/membership/provenance, producing `stream_quality_shared.json`.
Seven curve/alignment/export CPU tests pass. No GPU intermediate PSNR measured
yet; v7 owns the GPU. Alignment residuals and exact-first-attainment limitations
remain explicit. Curves measure integrated online map quality, not isolated
photometric optimization.

### Correspondence reuse panel v7_correspondence/rpng/table_06/growth_ervs/seed0

held-out 24.996542dB, 138.273/138.367초, 4410 Adam; 전체시간 계약 PASS.
Artifact: `online_dense_training/v7_correspondence/rpng/table_06/growth_ervs/seed0/`.

## v7 manipulation failure: correspondence reuse never activated

RPNG24.996542dB (full mapping138.272800/138.367006s,4410 Adam, whole-wall
contractPASS). Visual calls308, warm0/cold308,6.586568s. This is NOT a successful
correspondence-reuse intervention: do not interpret the near-v6 PSNR as evidence
about reuse quality. Cache key includes Python tensor identity, but native packet
processing creates new Camera/RGB tensors for the same immutable archive UID
(`gs_backend.py` camera_init). Existing DROID features already cache by UID.
The key therefore conflates observation identity with temporary tensor identity.

Stopped our v7 panel launcher before UTMM; Aria had already started and is
allowed to finish for cost/provenance rather than corrupting its running sources.
Preserved14 Python source files in `source_v7/index.json`. Next repair uses
run-scoped immutable observation UID plus calibration/shape and anchor pair as
measurement identity, preserving current-depth/pose BA. Verify warm activity
in an actual run before evaluating cross-scene benefit. No production change.

## v7 interruption correction / v8 UID cache repair

After stopping the owned launcher, Aria child also ended before publishing
runtime/result; it did NOT complete. Preserve partial log and `interrupted.json`;
no quality value exists. UTMM was not started. Prior intention to let the Aria
child finish was not realized; no source edits occurred while it remained alive.

`v8_correspondence_uid` fixes the cache key to immutable archive UID, anchor
pair, calibration and shape, consistent with the existing UID-based DROID feature
cache. No changed-image-under-same-UID protocol is supported within one engine.
CUDA regression recreates all RGB tensors before each warm solve and changes
world scale/depth: warm path remains active and current-anchor correctness passes.
UID/calibration changes invalidate the key. Artifact `pose_preparation_checks/v4/`.
The panel now stops if an actual finished run has zero warm calls. Three scenes,
kappa64/tau.01,1.5x,100ms reserve and native mapping are otherwise unchanged.

Snapshot evaluator additionally rejects nonfinite/negative state times and
verifies paired source provenance before evaluation;4 curve tests pass.

### Correspondence reuse panel v8_correspondence_uid/rpng/table_06/growth_ervs/seed0

held-out 24.842682dB, 138.273/138.367초, 5110 Adam; 전체시간 계약 PASS.
Artifact: `online_dense_training/v8_correspondence_uid/rpng/table_06/growth_ervs/seed0/`.

## v8 RPNG activated: lower pose cost but no quality gain

Warm336/409 actual visual solves. Pose work3.275290s (warm1.197654s) versus
v6 total6.711041s; Gaussian Adam5110 versus4501 (+609). Full mapping wall
138.272533/138.367006s, all contractsPASS. Independently repeated held-out
PSNR24.842682 versus v6 dense25.006464 (−0.163782) and KF25.229089
(−0.386407). The intervention is now active and cheaper, but the additional
steps did NOT improve RPNG quality. Do not accept it on speed alone.
Differences may involve correspondence accuracy and the changed online work
schedule; neither is isolated yet. Same-policy Aria/UTMM transfer continues.
`reuse_cost_comparison.json` preserves measurements; `source_v8/index.json`
freezes14 source files. Production checkout still clean.

### Correspondence reuse panel v8_correspondence_uid/aria/aria1253/growth_ervs/seed0

held-out 27.181781dB, 97.556/97.650초, 11014 Adam; 전체시간 계약 PASS.
Artifact: `online_dense_training/v8_correspondence_uid/aria/aria1253/growth_ervs/seed0/`.

### Correspondence reuse panel v8_correspondence_uid/utmm/square-1/growth_ervs/seed0

held-out 23.334466dB, 80.620/80.714초, 12683 Adam; 전체시간 계약 PASS.
Artifact: `online_dense_training/v8_correspondence_uid/utmm/square-1/growth_ervs/seed0/`.

## v8 three-scene summary (2026-09-25)

All three runs pass complete1.5x mapping budget and zero-tail.
| Scene | v8 PSNR | vs v6 dense | vs KF-only | vs production |
|---|---:|---:|---:|---:|
| RPNG |24.842682|−0.163782|−0.386407|+0.386476|
| Aria |27.181781|+0.333594|−0.340083|+1.309198|
| UTMM |23.334466|+0.159107|+0.929261|+1.952568|

Mean25.119643 (+0.067591 vsKF, +1.216081 vsproduction), but RPNG/Aria
deficits remain: NOT accepted, no persistent-regression or3seed criterion met.
Warm solves RPNG336/409,Aria628/794,UTMM493/689; pose seconds3.2753/6.4953/6.7048.
A cheaper preparation path helps Aria/UTMM, but cannot alone explain RPNG loss.
RPNG native commits1824→1832 and photo2677→3278; saved cost actually increases
photo work. Pose-correction quantiles saved but are NOT pose-accuracy metrics.

Prepared entropy-scale diagnostic (not a trial): final v8 RPNG265 images,
current tau.01 gives dense mass.3844; tau=1/N would yield.5138 on the same
counts. Aria262 images changes.7537→.8556. For the implemented exact Gibbs
logits, fixed tau makes a given relative count deficit less influential as
pool size increases (denominator tau*(sum counts+1)). A common1/N entropy
weight is a possible next mechanism test, not a quality claim or adopted policy.
Artifact `v8_correspondence_uid/entropy_scale_diagnostic.json`.

UTMM's v6 paired snapshot export also passes identical common poses and
reference trajectory (19/33/49 commonKFs). All three scene pairs now ready.
Launched `run_online_stream_panel.py`: evaluate v6 dense/KF at actual25/50/75%
states plus endpoint, fixed held-out cohort, common evaluation coordinates.
This is post-run rendering only with no extra optimization. Per-arm results
are recorded automatically.

### v6 saved-state quality curve

rpng/table_06/growth_ervs: 34.87s:14.3192dB, 69.27s:22.6367dB, 104.37s:23.9627dB, 138.27s:25.0065dB. Fixed held-out cohort 555; common evaluation coordinates; post-run rendering only. Alignment residuals remain unaccepted; no exact first-attainment claim.

## Prepared v9: common pool-scaled entropy weight (not run yet)

Hypothesis from exact implemented logits: at fixed relative count deficits,
fixed tau weakens correction as the active training pool grows. Added opt-in
`entropy_weight_policy=per_view`, effective tau_t=rho/N_t using only current
training membership. Predeclared rho1 (no scene-specific search), kappa64,
UID-based correspondence reuse and all other v8 settings unchanged. The original
`fixed` default remains byte-equivalent in selection math. This is a change in
entropy weighting policy and must be stated if adopted; no paper text changed.

Runner `run_online_entropy_scale_panel.py`, tag `v9_entropy_scale`, passes
`--tau 1 --entropy-weight-policy per_view`. Audit records configured/effective
weights.27 CPU tests pass including separately evaluated objective stationarity
and preservation of relative-count priority as pool size increases10→100.
Compile checks pass. No GPU v9 launched while stream evaluation owns the GPU.
Do not equate increased dense probability with quality benefit; compare all
three scenes and both controls before adoption.

### v6 saved-state quality curve

rpng/table_06/kf_only: 34.90s:14.3551dB, 69.29s:22.7394dB, 104.35s:23.9699dB, 138.27s:25.2291dB. Fixed held-out cohort 555; common evaluation coordinates; post-run rendering only. Alignment residuals remain unaccepted; no exact first-attainment claim.

## First complete paired stream curve: RPNG v6

Same555 held-out images/common evaluation coordinates, independent double
evaluation passed at every state. Dense/KF PSNR at actual ~34.9/69.3/104.4/138.3s:
14.3192/14.3551,22.6367/22.7394,23.9627/23.9699,25.0065/25.2291.
Deltas−0.03585/−0.10269/−0.00717/−0.22263. No observed checkpoint shows dense
advantage; these points do NOT prove faster convergence. Near equality at75%
and larger endpoint deficit motivates checking late service balance as well as
preparation cost. Actual sample times retained; no interpolation-based crossing
claim. Artifact `v6_deferred/rpng/table_06/paired_stream_comparison.json`.

Code audit confirms KF and dense RGB share `FrozenTrackerArchive.load_rgb`,
including the same undistortion/crop/resize path; no separate dense-only raw-RGB
preprocessing path found. This is source evidence, not a pixel-by-pixel runtime
comparison. Production live-loop integration remains pending; current tests use
the real mapper with a causal frozen-tracker arrival harness and therefore do
not demonstrate concurrent full-SLAM tracking throughput.

### v6 saved-state quality curve

aria/aria1253/growth_ervs: 24.53s:11.7732dB, 48.83s:16.5234dB, 73.24s:18.0409dB, 97.56s:26.8482dB. Fixed held-out cohort 262; common evaluation coordinates; post-run rendering only. Alignment residuals remain unaccepted; no exact first-attainment claim.

### v6 saved-state quality curve

aria/aria1253/kf_only: 24.43s:11.5658dB, 48.83s:16.2714dB, 73.24s:17.8717dB, 97.55s:27.5219dB. Fixed held-out cohort 262; common evaluation coordinates; post-run rendering only. Alignment residuals remain unaccepted; no exact first-attainment claim.

### v6 saved-state quality curve

utmm/square-1/growth_ervs: 20.18s:8.8491dB, 40.39s:14.2707dB, 60.54s:19.9868dB, 80.65s:23.1754dB. Fixed held-out cohort 324; common evaluation coordinates; post-run rendering only. Alignment residuals remain unaccepted; no exact first-attainment claim.

### v6 saved-state quality curve

utmm/square-1/kf_only: 20.18s:8.8651dB, 40.36s:14.1811dB, 60.54s:19.6820dB, 80.68s:22.4052dB. Fixed held-out cohort 324; common evaluation coordinates; post-run rendering only. Alignment residuals remain unaccepted; no exact first-attainment claim.

## v6 paired stream evaluation complete / v9 running

All6 arms x3 saved states independently evaluated twice, plus their existing
endpoints. Fixed cohort sizes555/262/324 for RPNG/Aria/UTMM. Paired plots and
JSON: `v6_deferred/paired_stream_quality.{png,svg}` and
`paired_stream_summary.json`. Plot visually inspected; markers are measurements
and dashed lines guides, with per-checkpoint differences shown separately.

Dense minusKF at25/50/75/100% checkpoints:
- RPNG:−0.03585/−0.10269/−0.00717/−0.22263dB.
- Aria:+0.20742/+0.25194/+0.16915/−0.67368dB.
- UTMM:−0.01598/+0.08958/+0.30484/+0.77015dB.

Aria initially leads then ends behind; UTMM gains grow later. This motivates
late service allocation but does NOT isolate it as the cause. Sparse states
do not establish exact first attainment. UTMM first observed crossing of the
KF endpoint PSNR is only at the endpoint checkpoint, so its36ms timestamp
difference is NOT evidence of meaningful faster convergence. Shared alignment
residuals (Aria75%7.13cm/3.31deg) remain material and unaccepted for pure
photometric convergence interpretation. Integrated quality only.

Launched v9 common tau=1/N policy after all GPU curve evaluation completed.
`source_v9/index.json` preserves14 files; kappa64/native geometry/pose reuse/
1.5x/100ms remain unchanged. New result not yet available.

Startup-cost source audit: `CausalImuDensePoseShaper` currently loads/parses
raw IMU before replay_start, and KF-only skips it. Current depth integration,
visual solve, selected RGB decode/transfers are inside the clock. The one-time
IMU preparation cost is NOT included in reported mapping wall and must be
measured/moved under the clock before final full-cost acceptance; don't edit
locked sources mid-v9. Startup/config/GS initialization scope also needs an
explicit common definition for final comparisons.

### Pool-scaled entropy panel v9_entropy_scale/rpng/table_06/growth_ervs/seed0

held-out 25.009712dB, 138.273/138.367초, 4878 Adam; 전체시간 계약 PASS.
Artifact: `online_dense_training/v9_entropy_scale/rpng/table_06/growth_ervs/seed0/`.

## Startup cost measured / first v9 result

Post-run CPU diagnostic (not retrospective per-run timing): IMU shaper
initialization Aria69.680ms/RPNG35.251ms/UTMM7.639ms; archive metadata
initialization5.271/7.697/2.843ms. Artifact `startup_cost_diagnostic.json`.
The IMU initialization is candidate/production preparation skipped by KF-only,
so include it in the clock for final acceptance. Existing reported budget
passes refer to the implemented replay-start scope, not yet corrected setup.
No retroactive budget pass is inferred from these separate timings.

V9 RPNG25.009712dB, +0.167030 vs v8 and−0.219377 vs newKF. Recorded
tau1 /per_view, effective endpoint tau.00381679,4878 Adam (native1824,
photo3054),138.273287/138.367006s. Same current clock checksPASS.
Entropy change is active and improves this run despite fewer photo steps than
v8, but KF-only remains ahead. Finish common Aria/UTMM transfer before choosing
another policy. Three-seed/factorial/live-loop integration remain pending.

### Pool-scaled entropy panel v9_entropy_scale/aria/aria1253/growth_ervs/seed0

held-out 27.005081dB, 97.551/97.650초, 11122 Adam; 전체시간 계약 PASS.
Artifact: `online_dense_training/v9_entropy_scale/aria/aria1253/growth_ervs/seed0/`.

### Pool-scaled entropy panel v9_entropy_scale/utmm/square-1/growth_ervs/seed0

held-out 22.929621dB, 80.756/80.714초, 12654 Adam; 전체시간 계약 FAIL.
Artifact: `online_dense_training/v9_entropy_scale/utmm/square-1/growth_ervs/seed0/`.

## v9 complete: not accepted; v10 clock/boundary correction

RPNG25.009712, Aria27.005081; UTMM22.929621 is INVALID because mapping
80.755808s exceeds80.714126s by41.683ms. Do not use a three-scene v9 mean
as valid acceptance evidence. Last UTMM event78 started near the deadline,
rendered17 views but completed0 Adam steps; its recorded mapper body lasted
60.883ms. Existing checks acted at optimizer boundaries, after packet decode
and map mutation had already begun.

V10 keeps the common v9 policy (rho1/N,kappa64,pose reuse) and compares fresh
production/KF controls. Same100ms reserve; no increased margin or scene tuning.
Finite adapter now checks time before control/dense input and before/after
packet decoding. Scheduler exits cleanly if input preparation rejects work.
Input rejections have their own counter, not topology rejections. A setup
clock option starts at GSBackEnd construction, before IMU loading and policy
setup; all three arms use it. Fixed calibration/archive metadata and library
initialization remain pre-stream harness setup; actual mapper construction,
method-specific initialization and streaming work are included.

Three CPU boundary tests pass: dense/control rejection is clean and prevents
subsequent mapping; real packet guard rejects before Adam without miscounting
topology. Compilation passes. Runner `run_online_setup_clock_panel.py`, tag
`v10_setup_clock`,9 matched arms. Record startup and input-boundary telemetry
as well as full-wall, held-out and zero-tail checks. No final quality gain
is asserted, and no source is changed while the panel runs.

### Setup-clock panel v10_setup_clock/rpng/table_06/growth_ervs/seed0

held-out 24.987951dB, 138.270/138.367초, 4987 Adam; 전체시간 계약 PASS.
Artifact: `online_dense_training/v10_setup_clock/rpng/table_06/growth_ervs/seed0/`.

## First v10 setup-inclusive run / next low-risk cost diagnostic prepared

RPNG dense24.987951dB; mapper_setup_wall_seconds0.167696 is inside
138.270186/138.367006s mapping.4987 Adam, declared setup clock and input
boundary checksPASS, held-out/zero-tailPASS. This run stopped via idle boundary
(input rejection count0), so it does not yet reproduce the late-packet rejection
case. Fresh KF/production and other scenes continue.14 sources frozen in
`source_v10/index.json`; production checkout clean.

Prepared `check_dense_ba_batching.py` (compiled, NOT GPU-tested yet): current
warm correspondence path calls motion-only BA six times with2 iterations each,
and each call repacks targets/weights and initializes backend work. With fixed
correspondences, combining the same12 iterations into one BA call may remove
overhead without changing the pose solution. The standalone CUDA diagnostic
will compare both numerical results and time across4 synthetic world scales,
asserting anchors/depth unchanged. Do not change the active v10 refiner before
the panel finishes; no equivalence or speed improvement has been claimed.

### Setup-clock panel v10_setup_clock/rpng/table_06/kf_only/seed0

held-out 25.251334dB, 138.272/138.367초, 6904 Adam; 전체시간 계약 PASS.
Artifact: `online_dense_training/v10_setup_clock/rpng/table_06/kf_only/seed0/`.

### Setup-clock panel v10_setup_clock/rpng/table_06/production/seed0

held-out 24.447656dB, 138.280/138.367초, 3332 Adam; 전체시간 계약 PASS.
Artifact: `online_dense_training/v10_setup_clock/rpng/table_06/production/seed0/`.

### Setup-clock panel v10_setup_clock/aria/aria1253/growth_ervs/seed0

held-out 26.934161dB, 97.565/97.650초, 11164 Adam; 전체시간 계약 PASS.
Artifact: `online_dense_training/v10_setup_clock/aria/aria1253/growth_ervs/seed0/`.

### Setup-clock panel v10_setup_clock/aria/aria1253/kf_only/seed0

held-out 27.626149dB, 97.552/97.650초, 15800 Adam; 전체시간 계약 PASS.
Artifact: `online_dense_training/v10_setup_clock/aria/aria1253/kf_only/seed0/`.

## v10 RPNG comparison / native binary provenance

RPNG candidate24.987951, freshKF25.251334, production24.447656dB. All
setup-inclusive clock checks pass. Candidate remains−0.263383 vsKF and
+0.540295 vsproduction, so the timing fix has not restored dense superiority.
Aria candidate26.934161dB also passes; its matched controls are running.

Actual v10 worker `/proc/3465482/maps` confirmed3 native libraries load from
`VIGS-SLAM-visible-lazy-carve`, not the isolated worktree. Preserved their
exact bytes/hashes in `runtime_dependencies_v10/index.json`. `vigs_kernels.cu`
and `vigs.cpp` hashes match the isolated tree, and the loaded binary contains
SparseBlock::update_lhs/update_rhs/solve symbols. The code copies H/RHS to
CPU Eigen and the solved update back to CUDA in each BA iteration. This
source/binary evidence motivates cost diagnostics; no measured batching gain
or GPU-only solver equivalence has been established yet.

Added a stdlib-only `online_runtime_dependencies.py` probe: resolved3 native
paths and hashes exactly match the running process's mapped binaries, without
importing Torch/warming CUDA. Saved `resolution_probe.json`: Torch2.8.0+cu128,
torchvision0.23.0+cu128,NumPy2.1.2,SciPy1.16.2,OpenCV4.12.0.88. Future
runner source locks should include these binaries and check before/after runs;
do not change active v10 source inputs.

Live integration audit: real `_gs_worker` in `vigs/vigs.py` dispatches packets
through `process_track_data` and currently runs legacy `idle_map_rr_step` during
idle opportunities. It drains `_dense_polish_pending` eagerly. The common
trainer/deferred inventory is still configured by the experiment harness only.
Final integration must connect these actual live boundaries and preserve queue,
current-anchor, RGB residency, and stop semantics; no live integration claim yet.

### Setup-clock panel v10_setup_clock/aria/aria1253/production/seed0

held-out 25.866480dB, 97.555/97.650초, 10994 Adam; 전체시간 계약 PASS.
Artifact: `online_dense_training/v10_setup_clock/aria/aria1253/production/seed0/`.

### Setup-clock panel v10_setup_clock/utmm/square-1/growth_ervs/seed0

held-out 23.187510dB, 80.614/80.714초, 12810 Adam; 전체시간 계약 PASS.
Artifact: `online_dense_training/v10_setup_clock/utmm/square-1/growth_ervs/seed0/`.

### Setup-clock panel v10_setup_clock/utmm/square-1/kf_only/seed0

held-out 22.851490dB, 80.614/80.714초, 18106 Adam; 전체시간 계약 PASS.
Artifact: `online_dense_training/v10_setup_clock/utmm/square-1/kf_only/seed0/`.

### Setup-clock panel v10_setup_clock/utmm/square-1/production/seed0

held-out 21.359501dB, 80.615/80.714초, 7737 Adam; 전체시간 계약 PASS.
Artifact: `online_dense_training/v10_setup_clock/utmm/square-1/production/seed0/`.

### 2026-09-25 — v10 setup-clock panel complete: candidate rejected

All nine seed-0 runs pass the declared 1.5× whole mapping clock, including mapper/IMU/policy startup, input preparation guards, held-out disjointness and zero-tail. This is clocked mapper replay, not concurrent live SLAM tracking.

| Scene | Production | KF-only | Growth + ERVS | Delta vs KF |
|---|---:|---:|---:|---:|
| rpng | 24.447656 | 25.251334 | 24.987951 | -0.263383 |
| aria | 25.866480 | 27.626149 | 26.934161 | -0.691987 |
| utmm | 21.359501 | 22.851490 | 23.187510 | +0.336020 |

Candidate mean 25.036541 dB: +1.145328 versus production but −0.206450 versus KF-only. RPNG and Aria regress; **not accepted**. No final seed replication or convergence claim follows. UTMM candidate actually rejected one late input preparation and stopped at 80.614243 / 80.714126 s; this exercises the new boundary guard, unlike the other two candidates.

Artifacts: `results/campaigns/gain_attribution/online_dense_training/v10_setup_clock/{summary,panel_progress}.json`; each run preserves contract/source/runtime/evaluation evidence. Source v10 remains preserved; new runs will also lock resolved native libraries and check hashes after mapping and evaluation.

### 2026-09-25 — Fixed-correspondence BA batching: synthetic equivalence and next ablation

`pose_preparation_checks/v5_ba_batching/result.json`: four scene scales, 6 calls × 2 iterations versus 1 call × 12 iterations yield bit-identical final poses, preserve anchor poses/depth, and reduce truth errors. Mean per-pose time changes from about 2.07 ms to 1.55 ms on this synthetic fixture (not an end-to-end speedup). Original diagnostic source is preserved beside results.

The isolated `CorrespondenceRefiner` warm path now uses one 12-iteration call; its cold path remains six neural updates. The actual wrapper test `pose_preparation_checks/v6_batched_wrapper/check.log` passes changed online anchor/depth scale and recreated image tensors, with translation error below 4.1e-7 and `ba_calls=1`. No real mapping quality claim yet.

Next predeclared panel: `v11_batched_sampling`, seed0, the same three scenes and whole setup-inclusive clock, κ64, 100ms reserve, snapshots, deferred preparation, lazy current-anchor refresh and correspondence reuse. Compare `growth_ervs` (effective τ=1/N) with `growth_rr` under the same batched pose implementation. This separates selection behavior from dense pose preparation; growth admissions may consequently differ because growth credits follow completed optimizer work. Preserve all original native RGB-D/birth behavior. Fixed source snapshot: `source_v11/index.json` (16 Python files); runner now hashes the actually resolved native dependencies before and after mapping/evaluation. Reproduction: `python benchmarks/online_gs/campaigns/gain_attribution/run_online_batched_sampling_panel.py`. Production checkout remains clean; live worker integration is still pending.

### Batched pose / sampling panel v11_batched_sampling/rpng/table_06/growth_ervs/seed0

held-out 25.009189dB, 138.275/138.367초, 5070 Adam; 전체시간 계약 PASS.
Artifact: `online_dense_training/v11_batched_sampling/rpng/table_06/growth_ervs/seed0/`.

### Batched pose / sampling panel v11_batched_sampling/rpng/table_06/growth_rr/seed0

held-out 25.047526dB, 138.269/138.367초, 4903 Adam; 전체시간 계약 PASS.
Artifact: `online_dense_training/v11_batched_sampling/rpng/table_06/growth_rr/seed0/`.

### Batched pose / sampling panel v11_batched_sampling/aria/aria1253/growth_ervs/seed0

held-out 27.244456dB, 97.584/97.650초, 11274 Adam; 전체시간 계약 PASS.
Artifact: `online_dense_training/v11_batched_sampling/aria/aria1253/growth_ervs/seed0/`.

### Batched pose / sampling panel v11_batched_sampling/aria/aria1253/growth_rr/seed0

held-out 27.066925dB, 97.554/97.650초, 10724 Adam; 전체시간 계약 PASS.
Artifact: `online_dense_training/v11_batched_sampling/aria/aria1253/growth_rr/seed0/`.

### Batched pose / sampling panel v11_batched_sampling/utmm/square-1/growth_ervs/seed0

held-out 23.202066dB, 80.614/80.714초, 12009 Adam; 전체시간 계약 PASS.
Artifact: `online_dense_training/v11_batched_sampling/utmm/square-1/growth_ervs/seed0/`.

### 2026-09-25 — v11 first two paired scenes and pose-fit diagnostic

RPNG ERVS 25.009189 / RR 25.047526 dB; Aria ERVS 27.244456 / RR 27.066925 dB. All four pass the full setup-inclusive clock and source/dependency checks. Both policies remain below v10 KF-only on these scenes. These seed0 comparisons do not establish a universal selection-policy fix or an isolated BA-batching quality effect. UTMM ERVS/RR continues under unchanged v11 source.

RPNG ERVS: 3,231 photo steps, 1,913 dense; RR: 3,093 photo steps, 1,080 dense (59.2% vs 34.9%). Native steps 1,839 vs 1,810; wall-clock runs allow downstream work and topology to diverge. v10 complete-work accounting is saved at `v10_setup_clock/work_accounting.json`: dense candidates have roughly 30–38% fewer photo steps than KF-only, with preparation included. This does not alone attribute the quality gap.

Read-only `/proc/3470515/maps` additionally identified `simple_knn._C`, used by Gaussian construction, beyond the three native files currently in the automated lock. All four project extensions are now copied/hashed in `runtime_dependencies_v11/index.json`. Add simple-knn to the automated pre/post lock after the active panel; do not retroactively claim its pre-run verification.

Prepared `vigs/dense_pose_quality.py`: weighted reprojection fit to current training anchors/depths and image correspondences, plus support fraction. It uses no evaluator inputs and makes no selection or pose changes. Undefined support returns None rather than a misleading zero error. Four CPU checks pass (known translation, rotation/different intrinsics, no support, invalid measurements); sources preserved in `pose_quality_checks/v1/`. **Not yet integrated or measured on real frames**; actual residual is measurement fit, not true pose error. This enables investigating reliability without choosing a speculative gate threshold.

### Batched pose / sampling panel v11_batched_sampling/utmm/square-1/growth_rr/seed0

held-out 23.400459dB, 80.614/80.714초, 12968 Adam; 전체시간 계약 PASS.
Artifact: `online_dense_training/v11_batched_sampling/utmm/square-1/growth_rr/seed0/`.

### 2026-09-25 — v11 complete, no accepted policy; v12 pose-fit audit

| Scene | Growth ERVS | Growth RR | v10 KF-only |
|---|---:|---:|---:|
| RPNG | 25.009189 | 25.047526 | 25.251334 |
| Aria | 27.244456 | 27.066925 | 27.626149 |
| UTMM | 23.202066 | 23.400459 | 22.851490 |

All six v11 executions pass full setup-inclusive time and input/optimizer/held-out checks. Three-scene means ERVS 25.151904 / RR 25.171637 / KF 25.242991 dB. Both selection policies lose on RPNG and Aria. Preserve `v11_batched_sampling/summary.json`; do not call either a successful final policy.

The measurement-fit audit now has an opt-in `QualityAuditedRefiner` wrapper and runner flag `--audit-dense-pose-fit`. Real CUDA warm-wrapper synthetic tests preserve current anchors/depth and yield RMS below 2.2e-7 grid pixels at both scale1/1.5. It reports only fit/support, without altering poses, admission or selection; missing depth does not count as geometric support. Transfers and reduction/synchronization are inside existing timed preparation. This extra diagnostic overhead can change the number of completed online steps, so v12 quality is not an isolated efficacy test.

Predeclared v12: same three scenes, seed0 ERVS, κ64/effectiveτ1/N, deferred/lazy/batched preparation, full setup clock, 100ms reserve, snapshots. **No confidence gate or scene-specific tuning.** `source_v12/index.json` preserves 19 files. Reproduce with `python benchmarks/online_gs/campaigns/gain_attribution/run_online_pose_fit_panel.py`. Automated pre/post native lock now covers all four extensions observed in `/proc` (including simple-knn); no-Torch resolver exactly matches their preserved hashes.

### Pose-fit diagnostic panel v12_pose_fit/rpng/table_06/growth_ervs/seed0

held-out 24.990947dB, 138.270/138.367초, 4847 Adam; 전체시간 계약 PASS.
Artifact: `online_dense_training/v12_pose_fit/rpng/table_06/growth_ervs/seed0/`.

### Pose-fit diagnostic panel v12_pose_fit/aria/aria1253/growth_ervs/seed0

held-out 26.775464dB, 97.551/97.650초, 11160 Adam; 전체시간 계약 PASS.
Artifact: `online_dense_training/v12_pose_fit/aria/aria1253/growth_ervs/seed0/`.

### Pose-fit diagnostic panel v12_pose_fit/utmm/square-1/growth_ervs/seed0

held-out 23.308588dB, 80.614/80.714초, 12535 Adam; 전체시간 계약 PASS.
Artifact: `online_dense_training/v12_pose_fit/utmm/square-1/growth_ervs/seed0/`.

### 2026-09-25 — v12 correspondence fit complete; sparse current-anchor refresh

All three v12 diagnostic arms pass the setup-inclusive clock: RPNG24.990947, Aria26.775464, UTMM23.308588 dB. No acceptance claim. `v12_pose_fit/pose_fit_summary.json` and `analyze_online_pose_fit.py` preserve the measurements: median full-resolution correspondence RMS0.804/0.962/0.774 pixels; p99 RPNG2.225, Aria2.021, UTMM1.196 pixels (see JSON for exact quantiles). All calls have positive support, but these learned-correspondence fits are not true pose errors and repeated warm calls are not independent observations. No rejection threshold was introduced.

A concrete preparation inefficiency was found: the native `_refresh_causal_dense_poses` converted every retained keyframe pose to SE3, even when the lazy wrapper refreshed only one selected dense camera. v10 `lazy_refresh.json` reports total refresh time RPNG3.8653s, Aria5.9341s, UTMM1.5338s (this includes the rest of refresh, not just pose conversions).

`dense_pose_sparse_refresh.py` groups selected dense cameras by their existing current brackets and converts only required endpoints. The isolated backend delegates its native refresh to this implementation; IMU repair, visual refinement, metadata, full history, Gaussian birth and geometric losses stay intact. Frozen-v12 CUDA comparison includes current pose changes, a changed bracket, an unbracketed camera, right-multiplied residual, and existing causal IMU/lazy wrappers: all five pose differences exactly0. It converted8 rather than497 keyframe poses across these selected refreshes. For100-keyframe single-view refresh, synthetic timing17.858→0.644ms. The actual integrated backend eager/lazy check also yields zero differences in all four cases. Artifacts: `pose_preparation_checks/v7_sparse_refresh/` and `v8_sparse_integrated/`. These are numerical/cost checks, not PSNR evidence.

Predeclared v13 keeps v12 ERVS, pose-fit audit, κ64, τ1/N, full setup clock, snapshots and100ms reserve, changing only endpoint conversion in native refresh. The added `sparse_refresh.json` reports actual conversions. Three seed0 scenes; source21files preserved in `source_v13/index.json`. Run: `python benchmarks/online_gs/campaigns/gain_attribution/run_online_sparse_refresh_panel.py`. Production checkout not modified. Final three-seed/ablation/convergence/live integration requirements remain open.

### Sparse pose refresh panel v13_sparse_refresh/rpng/table_06/growth_ervs/seed0

held-out 25.077266dB, 138.273/138.367초, 5316 Adam; 전체시간 계약 PASS.
Artifact: `online_dense_training/v13_sparse_refresh/rpng/table_06/growth_ervs/seed0/`.

### 2026-09-25 — v13 RPNG actual preparation cost

RPNG v13 passes all full-clock checks:25.077266dB,138.272613/138.367006s. Current-anchor refresh3.472981→0.479187s versus identical-contract v12; prepared cameras280 and converted keyframe poses560 instead of the31466 available across those calls. Photo optimizer steps3015→3492 (+477); native1832→1824. PSNR delta+0.086319dB in this seed0 observation, still−0.174068dB versus v10 KF-only. **Cost reduction is verified in the real mapper; final quality acceptance is not.** Aria/UTMM continue with unchanged locked source. Reproduce analysis with `python benchmarks/online_gs/campaigns/gain_attribution/compare_online_pose_preparation.py`; partial/complete status is explicit in `v13_sparse_refresh/preparation_comparison.json`.

### Sparse pose refresh panel v13_sparse_refresh/aria/aria1253/growth_ervs/seed0

held-out 27.459756dB, 97.553/97.650초, 11842 Adam; 전체시간 계약 PASS.
Artifact: `online_dense_training/v13_sparse_refresh/aria/aria1253/growth_ervs/seed0/`.

### Sparse pose refresh panel v13_sparse_refresh/utmm/square-1/growth_ervs/seed0

held-out 23.231007dB, 80.614/80.714초, 12603 Adam; 전체시간 계약 PASS.
Artifact: `online_dense_training/v13_sparse_refresh/utmm/square-1/growth_ervs/seed0/`.

### 2026-09-25 — v13 complete; separate growth credit from selector count scope

All three sparse-refresh arms pass full time/causality checks: RPNG25.077266, Aria27.459756, UTMM23.231007dB. Mean25.256010, +0.013019 versus v10 KF-only and +1.364797 versus production; **not accepted**, since RPNG−0.174068 and Aria−0.166392 remain below KF-only while UTMM+0.379517 raises the average. Endpoint conversion removes measured preparation cost on all scenes, but does not prove final quality or faster convergence. Full costs at `v13_sparse_refresh/preparation_comparison.json`.

New hypothesis: native RGB-D/normal batches and the dedicated RGB L1+SSIM refinement stage may not provide interchangeable evidence of photometric progress. The current shared counter gives each native keyframe view one service per joint native step, which can strongly deprioritize KF views during dedicated refinement. On the *same final v13 pools*, recomputing probabilities with dedicated-photo-only counts changes dense mass Aria86.3%→57.2%, RPNG52.9%→20.3%, UTMM87.8%→65.7%. These are static counterfactual probabilities, not tested trajectories or proof that shared counts are wrong (`count_scope_counterfactual.json`).

Opt-in `selection_count_scope=photometric` now keeps both count histories. Native and RGB steps still earn exactly the same growth credits, native RGB-D/normal/Gaussian birth are unchanged, and the complete all-RGB ledger is retained. Only ERVS reads dedicated RGB counts. Fourteen CPU policy checks pass, including original default behavior and source-scope/growth-credit separation; final runtime additionally asserts sum of dedicated counts equals completed photo optimizer steps.

Predeclared v14: same three scenes, seed0, same v13 sparse/lazy/deferred/correspondence preparation and fit audit, κ64, τ1/N, setup-inclusive clock, snapshots,100ms reserve; change only selector count scope. The default remains all_rgb. Source23files preserved including the otherwise git-ignored test. Reproduce: `python benchmarks/online_gs/campaigns/gain_attribution/run_online_photo_count_panel.py`. If adopted, the paper must explicitly define n_i as selections by the dedicated RGB refinement sampler, separate from the mapping-step growth credit. No paper claim changed yet.

### Photometric count-scope panel v14_photo_counts/rpng/table_06/growth_ervs/seed0

held-out 25.140033dB, 138.270/138.367초, 4928 Adam; 전체시간 계약 PASS.
Artifact: `online_dense_training/v14_photo_counts/rpng/table_06/growth_ervs/seed0/`.

### Photometric count-scope panel v14_photo_counts/aria/aria1253/growth_ervs/seed0

held-out 27.549634dB, 97.551/97.650초, 12045 Adam; 전체시간 계약 PASS.
Artifact: `online_dense_training/v14_photo_counts/aria/aria1253/growth_ervs/seed0/`.

### Photometric count-scope panel v14_photo_counts/utmm/square-1/growth_ervs/seed0

held-out 23.282853dB, 80.614/80.714초, 12544 Adam; 전체시간 계약 PASS.
Artifact: `online_dense_training/v14_photo_counts/utmm/square-1/growth_ervs/seed0/`.

### 2026-09-25 — v14 completed; shared image residency fix and v15 protocol

v14 count-scope 완료: 25.1400/27.5496/23.2829dB, 평균KF+0.0812이나 RPNG−0.1113/Aria−0.0765로 미채택. GPU 상주 영상 중복전송 제거: CPU2검사·실제Camera CUDA검사 PASS(픽셀차이0). 동일수정 대조군 포함 v15 9run 준비.

ERVS counts now cover dedicated RGB optimization selections; Growth still credits all completed mapping steps. All three v14 full-clock/count contracts pass. Seed0 improvement versus v13 is +0.06277/+0.08988/+0.05185dB, not final acceptance. See `v14_photo_counts/summary.json`.

Photo training previously ignored Camera.original_image_gpu and retransferred native keyframe targets on temporary-cache misses. Reuse the resident tensor; keep bounded LRU for nonresident dense images. Actual Camera check has identical pixels, pointer reuse and cached dense uploads. The initial v1 checker failed before exercising this behavior because its intrinsics fixture was 3x3 instead of length4; v1 is preserved and corrected v2 passes. Artifacts: `image_residency_checks/v2/check.log`, frozen 26 sources `source_v15/index.json`.

Next v15_image_residency: all three scenes, seed0, candidate/KF-only/production remeasured with same source and whole-clock budget (setup, pose, transfers, snapshots,100ms reserve). Candidate retains v14 photo counts, kappa64, entropy tau1/N, pose-fit audit and sparse/lazy preparation. No held-out inputs, extra tail, geometry changes or scene knobs. Command: `python benchmarks/online_gs/campaigns/gain_attribution/run_online_image_residency_panel.py`. Full live worker integration, ablations, repeated seeds and final quality curves remain pending.

### Image residency panel v15_image_residency/rpng/table_06/growth_ervs/seed0

held-out 24.988356dB, 138.275/138.367초, 5436 Adam; 전체시간 계약 PASS.
Artifact: `online_dense_training/v15_image_residency/rpng/table_06/growth_ervs/seed0/`.

### Image residency panel v15_image_residency/rpng/table_06/kf_only/seed0

held-out 25.225849dB, 138.276/138.367초, 6985 Adam; 전체시간 계약 PASS.
Artifact: `online_dense_training/v15_image_residency/rpng/table_06/kf_only/seed0/`.

### 2026-09-25 — v15 Growth/sampling ablation prepared, not started

After the nine v15_image_residency arms finish, run the same frozen implementation with growth_rr and immediate_rr on all three scenes, seed0. Keep photo-count scope, sparse/lazy/deferred current-anchor pose preparation, pose-fit audit, native RGB-D/birth, kappa64, 100ms reserve, snapshots and full setup-inclusive clock. This directly separates set growth from ERVS rather than choosing another hyperparameter from held-out results. Preparations and view membership can affect completed work under the fixed time budget; that cost is part of the online result. Immediate membership may make kappa inactive by definition.

Command: `python benchmarks/online_gs/campaigns/gain_attribution/run_online_growth_sampling_ablation.py`. Protocol and runner copy: `v15_growth_sampling/protocol.json`, `runner_source.py`. Runner requires all nine preceding controls valid and exact v15 source bytes before starting. This is a preregistered experiment, not a measured improvement.

### Image residency panel v15_image_residency/rpng/table_06/production/seed0

held-out 24.446187dB, 138.279/138.367초, 3467 Adam; 전체시간 계약 PASS.
Artifact: `online_dense_training/v15_image_residency/rpng/table_06/production/seed0/`.

### 2026-09-25 — v15 RPNG paired diagnostic and open hypothesis

Candidate24.988356 versus fresh KF25.225849dB: −0.237493. Candidate photo steps3110→3611 versus v14, while fresh KF5160 (v10 5066). Actual KF image traffic:5161 resident hits,0 upload requests. Candidate2211 resident hits,878 temporary-cache hits,523 uploads. Pixel reuse works, but more completed steps did not improve the candidate endpoint.

Post-run fixed held-out comparison (555 views,197 improve) gives filename-order quarter deltas −0.680931/−0.205346/−0.154637/+0.087752dB; see `v15_image_residency/rpng/table_06/heldout_diagnostic.json`. This is a descriptive final-map diagnostic, not a stream convergence curve, phase rule, or training input.

Open hypothesis, not established cause: older images may need renewed refinement after pose/map revisions although their cumulative counts remain high. Code retains selection counts through ordinary `_apply_pose_scale_updates`; only map reset resets the trainer. Offline fixed-pose diagnostics do not have this nonstationarity. No counter-reset policy, phase threshold or extra geometry loss is introduced; first complete the preregistered Growth/ERVS controls.

### Image residency panel v15_image_residency/aria/aria1253/growth_ervs/seed0

held-out 27.393702dB, 97.552/97.650초, 11860 Adam; 전체시간 계약 PASS.
Artifact: `online_dense_training/v15_image_residency/aria/aria1253/growth_ervs/seed0/`.

### Image residency panel v15_image_residency/aria/aria1253/kf_only/seed0

held-out 27.581262dB, 97.554/97.650초, 16827 Adam; 전체시간 계약 PASS.
Artifact: `online_dense_training/v15_image_residency/aria/aria1253/kf_only/seed0/`.

### Image residency panel v15_image_residency/aria/aria1253/production/seed0

held-out 25.894696dB, 97.555/97.650초, 11139 Adam; 전체시간 계약 PASS.
Artifact: `online_dense_training/v15_image_residency/aria/aria1253/production/seed0/`.

### Image residency panel v15_image_residency/utmm/square-1/growth_ervs/seed0

held-out 23.247956dB, 80.614/80.714초, 12896 Adam; 전체시간 계약 PASS.
Artifact: `online_dense_training/v15_image_residency/utmm/square-1/growth_ervs/seed0/`.

### Image residency panel v15_image_residency/utmm/square-1/kf_only/seed0

held-out 22.935859dB, 80.614/80.714초, 19175 Adam; 전체시간 계약 PASS.
Artifact: `online_dense_training/v15_image_residency/utmm/square-1/kf_only/seed0/`.

### Image residency panel v15_image_residency/utmm/square-1/production/seed0

held-out 21.382108dB, 80.620/80.714초, 7875 Adam; 전체시간 계약 PASS.
Artifact: `online_dense_training/v15_image_residency/utmm/square-1/production/seed0/`.

### 2026-09-25 — paired endpoints reveal a shared retention pattern

RPNG/Aria/UTMM candidate-minus-KF mean deltas: −0.237493/−0.187559/+0.312097dB. Fixed held-out cohorts555/262/324; improved views197/127/206. Filename-ordered earliest-quarter means are −0.680931/−1.612583/−1.148311dB, while latest-quarter means are +0.087752/+0.360079/+0.535268dB. Thus UTMM positive average also hides worse earliest-view reconstruction in this seed0. See `v15_image_residency/retention_diagnostic.json` and each `paired_endpoint_seed0.json` (source hashes included). Reproduce with `python benchmarks/online_gs/campaigns/gain_attribution/analyze_online_paired_endpoints.py --dataset <dataset> --scene <scene>`.

These are post-run, correlated-view descriptions, not temporal convergence measurements or proof that pose revisions caused the loss. No scene/frame cutoff is added. The pending growth-RR comparison will test whether cumulative-count selection contributes to this pattern before considering any revised accounting.

### 2026-09-25 — v15 nine-arm panel complete, not accepted

| Scene | Production | New KF-only | Growth+ERVS | Candidate minus KF |
|---|---:|---:|---:|---:|
| RPNG table_06 |24.446187|25.225849|24.988356|−0.237493|
| Aria aria1253 |25.894696|27.581262|27.393702|−0.187559|
| UTMM square-1 |21.382108|22.935859|23.247956|+0.312097|

All9 full setup-inclusive budget/zero-tail/disjoint-input checks pass. Candidate mean versus production +1.302341dB, versus KF-only −0.037652dB: **not accepted**. Shared resident-image reuse eliminates extra photo target uploads in KF-only (RPNG5161/Aria15998/UTMM18633 resident hits; exact counters in summary). Candidate dense images retain bounded uploads; all three candidate endpoints are below v14 by0.152/0.156/0.035dB. This does not prove resident reuse harms pixel quality (targets are identical); timed optimization trajectories differ. See `v15_image_residency/summary.json`, regenerated by `summarize_online_image_residency.py`.

Start the predeclared6-arm growth_rr/immediate_rr ablation without changing any mapper source or scene settings. Source snapshot `source_v15_ablation/index.json` includes the same26 sources plus three runner/analysis files. Keep v15 candidate and fresh controls as paired comparators. Final repeated seeds, live worker integration and current stream curves remain incomplete.

### Growth/sampling ablation v15_growth_sampling/rpng/table_06/growth_rr/seed0

held-out 25.021991dB, 138.269/138.367초, 전체시간 계약 PASS.
Artifact: `online_dense_training/v15_growth_sampling/rpng/table_06/growth_rr/seed0/`.

### 2026-09-25 — actual completed service allocation audit

Added `analyze_online_service_age.py`; it joins all successful native/photo service records to actual Gaussian Adam completion times and checks ledger length and held-out exclusion. The 4x4 tables use elapsed time and sensor-time quarters only for post-run description, never to control training. Native RGB services count images in a batch, not equal-cost optimizer steps.

In the last elapsed-time quarter, earliest-observation-quarter photo shares for candidate versus KF-only are RPNG2.49%vs17.96%, Aria13.38%vs29.24%, UTMM12.43%vs32.43%. These are actual selections, not inferred probabilities. Reproduce per run: `python benchmarks/online_gs/campaigns/gain_attribution/analyze_online_service_age.py --run-dir <run>`.

RPNG Growth+RR completes25.021991dB, versus ERVS24.988356 (+0.033635), still below KF25.225849 (−0.203858). Relative to RR, ERVS earliest-quarter held-out quality is −0.588313dB but latest-quarter is +0.337981dB. This paired policy change supports a retention/new-view tradeoff; one seed does not establish the full cause or an accepted replacement. Full source-locked comparison: `v15_growth_sampling/analysis.json`, generated by `analyze_online_growth_sampling.py`.

### Growth/sampling ablation v15_growth_sampling/rpng/table_06/immediate_rr/seed0

held-out 22.041612dB, 138.271/138.367초, 전체시간 계약 PASS.
Artifact: `online_dense_training/v15_growth_sampling/rpng/table_06/immediate_rr/seed0/`.

### Growth/sampling ablation v15_growth_sampling/aria/aria1253/growth_rr/seed0

held-out 27.538596dB, 97.554/97.650초, 전체시간 계약 PASS.
Artifact: `online_dense_training/v15_growth_sampling/aria/aria1253/growth_rr/seed0/`.

### Growth/sampling ablation v15_growth_sampling/aria/aria1253/immediate_rr/seed0

held-out 25.091564dB, 97.562/97.650초, 전체시간 계약 PASS.
Artifact: `online_dense_training/v15_growth_sampling/aria/aria1253/immediate_rr/seed0/`.

### 2026-09-25 — recent-service ERVS helper staged, not enabled

Motivation: final-quarter service ledgers and Growth+RR comparisons show older-view underallocation with lifetime counts; this is not proof that pose error is absent. Aria Growth+RR27.538596 versus ERVS27.393702 and immediate-RR25.091564 reinforces both the growth benefit and the sampling tradeoff.

A pure helper `recent_selection_counts.py` retains the last N−1 successfully committed photo selections before the next single-image draw, where N is the currently observed training-pool size. The Gaussian map and full image history remain unchanged. No total-sequence length, absolute frame/iteration cutoff, or per-scene setting is used. Cumulative counts and growth credits remain conceptually separate and unchanged. This helper is not imported by the active mapper, so v15 sources/behavior are unchanged.

Five CPU tests pass, including independent objective-stationarity checks with expiration, nonmutating reservation, pool-size changes, and restored priority for an image with high lifetime work but no recent service. Staged helper/test/analysis sources and observed test result are preserved at `count_memory_checks/v1/`. Counterfactual next-draw probabilities on the actual final v15 pools (`count_memory_counterfactual.json`) restore earliest-quarter mass from4.35/10.22/9.28% to39.66/31.54/32.55% for RPNG/Aria/UTMM, respectively. These are changed probabilities on a frozen history, not a simulated trajectory or measured PSNR gain. Reproduce with `analyze_online_count_memory.py`.

Only after the locked v15 ablation finishes should the helper be wired as an explicit optional recent_photometric scope and tested through actual mapper commits/cancellation/reset. If quality supports adoption, the paper must define n_i as recent refinement selections rather than lifetime cumulative counts. No manuscript claim changed at this stage.

### Growth/sampling ablation v15_growth_sampling/utmm/square-1/growth_rr/seed0

held-out 23.285823dB, 80.615/80.714초, 전체시간 계약 PASS.
Artifact: `online_dense_training/v15_growth_sampling/utmm/square-1/growth_rr/seed0/`.

### Growth/sampling ablation v15_growth_sampling/utmm/square-1/immediate_rr/seed0

held-out 21.394431dB, 80.614/80.714초, 전체시간 계약 PASS.
Artifact: `online_dense_training/v15_growth_sampling/utmm/square-1/immediate_rr/seed0/`.

### 2026-09-25 — v15 ablation complete; v16 recent counts integrated

| Scene | Immediate+RR | Growth+RR | Growth+ERVS | KF-only |
|---|---:|---:|---:|---:|
| RPNG |22.041612|25.021991|24.988356|25.225849|
| Aria |25.091564|27.538596|27.393702|27.581262|
| UTMM |21.394431|23.285823|23.247956|22.935859|

All6 ablation runs pass the full execution contract. Mean Growth minus immediate +2.439601, ERVS minus RR -0.072132, Growth+RR minus KF +0.034480dB. Positive RR mean does not establish acceptance: RPNG and Aria still regress, and the requested combined ERVS system has not succeeded. Detailed early/late held-out and service allocation: `v15_growth_sampling/analysis.json`.

After the panel closed, added explicit `recent_photometric` selection scope. Actual commit appends only successful dedicated RGB selections to its history; native work still earns growth credit and all cumulative RGB/photo counts stay intact. A proposed next draw uses the last N−1 committed photo selections for the current N-image pool; no full-sequence horizon or scene phase is used. Cancelled requests never age/append history. Actual trainer reset preserves the selected scope and retains the preceding generation report.

10 recent-count helper/integration tests and14 existing policy regression tests PASS (24 total). New tests include actual OnlinePhotometricTrainer reset, independent sliding-window objective stationarity, cancellation and native/admission separation. `count_memory_checks/v2/test.log`; exact sources frozen in `source_v16/index.json` (36 files including ignored tests). Runner now independently reconstructs recent counters from the actual committed service ledger and requires `recent_count_history` to pass.

Predeclared v16_recent_counts: same three scenes/seed0, kappa64, tau1/N, same sparse/lazy/deferred/correspondence pose preparation and fit audit, same images/native geometry/Gaussian birth, snapshots and setup-inclusive1.5x budget with100ms reserve. Only selection-count memory changes from v15 candidate. Existing all_rgb/photometric policies retain their computations; final repeated controls must run the final accepted source. Command: `python benchmarks/online_gs/campaigns/gain_attribution/run_online_recent_count_panel.py`. Production checkout remains unchanged. Recent-policy quality, repeated seeds, stream convergence and live integration remain unproven.

### Recent selection-count panel v16_recent_counts/rpng/table_06/growth_ervs/seed0

held-out 25.055159dB, 138.272/138.367초, 5422 Adam; 전체시간 계약 PASS.
Artifact: `online_dense_training/v16_recent_counts/rpng/table_06/growth_ervs/seed0/`.

### Recent selection-count panel v16_recent_counts/aria/aria1253/growth_ervs/seed0

held-out 27.559728dB, 97.555/97.650초, 11892 Adam; 전체시간 계약 PASS.
Artifact: `online_dense_training/v16_recent_counts/aria/aria1253/growth_ervs/seed0/`.

### Recent selection-count panel v16_recent_counts/utmm/square-1/growth_ervs/seed0

held-out 23.243007dB, 80.614/80.714초, 12596 Adam; 전체시간 계약 PASS.
Artifact: `online_dense_training/v16_recent_counts/utmm/square-1/growth_ervs/seed0/`.

### 2026-09-25 — v16 complete; sampling-memory improvement is insufficient

RPNG25.055159/Aria27.559728/UTMM23.243007dB. All3 complete mapping/causal/disjoint/zero-tail/recent-counter audits pass. Mean versus lifetime ERVS +0.075960dB, versus RR +0.003828dB, versus KF +0.038308dB, versus production +1.378301dB. **Not accepted**: RPNG−0.170690 and Aria−0.021534 remain below KF, repeated seeds and fast-convergence evidence are missing. RPNG last-quarter early-view sampling share recovered2.49%→21.63%; earliest-quarter held-out improved+0.606718dB over lifetime ERVS. Aria and UTMM earliest-quarter improvements are+0.699221/+0.753122dB, with some later-view quality lost. This supports the measured sampling tradeoff, not a full recovery of dense benefit. See `v16_recent_counts/summary.json` and its fixed-cohort source locks.

### 2026-09-25 — encoder input convention discrepancy verified

Source audit found capture/official demo explicitly converts OpenCV BGR to RGB, official MotionFilter reverses channels again, and official post-EOS PoseTrajectoryFiller directly normalizes RGB. The isolated dense refiner recomputes both anchor and target features directly from RGB. Official checkout is22ffe24c6df81d0bf63bd20057565c00c51d2996. Preserved sources/snippets: `pose_input_conventions/v1/audit.json`.

Executed the actual official MotionFilter.track and PoseTrajectoryFiller.fill methods plus current VisualRefiner.features on the same synthetic colored RGB tensor, intercepting encoder input before any learned feature/pose computation. Tracker input differs from filler by max4.305011 after normalization; filler and current refiner input tensors are identical. GPU checker passes; `pose_input_conventions/v2/{check.log,result.json,check_source.py}`. No held-out image, evaluator pose, Gaussian update or mapper/evaluator modification was involved. This proves an input-convention discrepancy in the checked code; it does not prove a pose error or explain the PSNR gap by itself.

Next independent diagnostic: use already-observed training anchor/depth packets and non-held-out intermediate images to compare consistent-RGB, legacy-filler-compatible anchor preprocessing, and consistent-tracker preprocessing. Keep poses/initialization/network/solver fixed and never feed evaluator poses into the solve. Inspect actual pose differences and common-support photometric reprojection residuals as diagnosis only; keep the existing held-out evaluator and archives unchanged. Further policy changes should wait for evidence from this interface check. No active GPU job remains after v16/checker completion; final source integration/repeated seeds/stream curves/paper alignment remain pending.

### 2026-09-25 — causal-prefix pose color probe complete

`pose_input_conventions/v5_pose_probe/` contains nine examples (three per fixed scene), three feature preprocessing modes per example: current RGB/RGB, legacy-filler-compatible BGR/RGB, and tracker-consistent BGR/BGR. All use the same two already-observed training anchors/depths, non-held-out dense target, interpolated initializer, frozen network and six neural updates. No evaluator poses, held-out RGB, Gaussian optimization, mapper/evaluator changes or post-EOS input are used by the solve. This is offline diagnostic work, not measured online performance. Source/calibration/image/model and resolved native dependency hashes pass pre/post checks; the independent synthetic projection-sign test passes.

Eight examples have less than0.4% absolute common-support RGB reprojection-residual change; RPNG UID1941 improves3.36% with legacy preprocessing and3.28% with tracker-consistent preprocessing. The nine-case median changes are approximately−0.0110% and−0.0188%, respectively. Correspondence residuals stay roughly0.55–1.10 full-resolution pixels. These photometric/support statistics are not ground-truth pose errors or mapping PSNR; nine selected examples cannot establish general pose accuracy. This does not justify changing the mapper's RGB convention or the evaluation trajectory.

Failure provenance: `v3_pose_probe.log` stopped at import (missing benchmark search path); `v4_pose_probe.log` completed three Aria examples then stopped because the diagnostic assumed split depth/normal references while RPNG retains a combined geometry path. Both failures are preserved; v5 supports both archive schemas. Existing mapper sources were unchanged.

Next diagnostic isolates cached correspondence reuse after anchor/depth revisions: compare a warm solve against newly estimated correspondences on the same later causal training packet. This tests whether initially estimated correspondences retain early pose/depth error. It does not alter native geometry supervision or add Carve/pruning variables.

### 2026-09-25 — cached correspondence revision probe complete

`pose_input_conventions/v6_refresh_probe/` compares warm cached correspondences and fresh six-update neural solves on nine later causal training packets, following an earlier solve on the same anchor/image pair. Cases stop across mapper resets and invalidate changed anchor pairs. Both paths use the same current anchor poses/depth and interpolated initializer; fresh solves reuse image features only. No held-out input/evaluator pose/Gaussian update/mapper source change. Projection-sign and source/dependency immutability checks pass.

Fresh versus cached common-support RGB reprojection residual changes range−0.18% to+0.68%, median−0.029%; no consistent improvement. Both substantially reduce residual versus interpolation in these examples. These are diagnostic residuals, not GT pose error, actual online service trajectories, or mapping PSNR. No correspondence-cache replacement is adopted.

Existing v16 actual timing: RPNG cold82/2.456s + warm346/1.338s; Aria cold184/4.770s + warm787/3.088s; UTMM cold194/5.256s + warm456/1.898s. These timings include the optional correspondence-fit audit introduced for diagnosis. Next separate the observer cost from the unchanged solver before another online quality run.

### 2026-09-25 — optional pose-fit observer cost; v17 solver-only preregistration

`pose_input_conventions/v7_audit_overhead/` alternates20 warm solves per mode/scene after warmup on identical causal training triplets. With/without optional correspondence-fit audit, pose output matrices are bit-identical (maximum difference0 for all60 pairs). Median audit/solver milliseconds: Aria3.589/2.748, RPNG3.543/2.697, UTMM3.540/2.667. The observer costs approximately0.84–0.87ms per warm solve in this microbenchmark; this is not an online speed or PSNR result. Native dependency and source pre/post checks pass.

Preregistered v17_solver_only removes only `--audit-dense-pose-fit` from the v16 recipe. Native geometry, actual motion-only pose solver, correspondence reuse, deferred/lazy preparation, recent ERVS, kappa64, tau1/N, snapshots, setup-inclusive budget,100ms deadline reserve, image/evaluator splits remain unchanged. This removes a research observer, not a pose correction or safety check. All causal/fixed-anchor/finite-pose/zero-tail checks remain. No method or paper claim changes. Exact41-source snapshot `source_v17/index.json`; run `python benchmarks/online_gs/campaigns/gain_attribution/run_online_solver_only_panel.py`. Three fixed scenes/seed0; compare v16 and same-source v15KF/production controls as exploratory evidence only. Final repeats and live integration remain pending.

### Solver-only panel v17_solver_only/rpng/table_06/growth_ervs/seed0

held-out 25.001349dB, 138.268/138.367초, 5475 Adam; 전체시간 계약 PASS.
Artifact: `online_dense_training/v17_solver_only/rpng/table_06/growth_ervs/seed0/`.

### Solver-only panel v17_solver_only/aria/aria1253/growth_ervs/seed0

held-out 27.549683dB, 97.551/97.650초, 11927 Adam; 전체시간 계약 PASS.
Artifact: `online_dense_training/v17_solver_only/aria/aria1253/growth_ervs/seed0/`.

### 2026-09-25 — next unresolved interface: mixed optimizer loss scale (source audit only)

`optimizer_scale_audit/v1/audit.json` preserves the relevant backend/trainer/loss sources. Native `map()` sums per-view `_frontier_mapping_view_loss` (masked RGB L1 + inverse depth + normal), and only divides by view count for the legacy `replay_iteration` branch, which the common trainer does not use. Common RGB service uses single-image L1+SSIM with the same Gaussian Adam optimizer. Thus native batch cardinality affects the relative gradient scale feeding the shared moments. This source fact does **not** establish the measured gradient ratio, conflict, the cause of dense regression, or a normalization benefit.

Next: instrument or replay actual native/photo steps with isolated gradient/Adam-state diagnostics. Distinguish batch reduction from depth/normal supervision. Keep RGB weighting fixed if removing a geometry term diagnostically; preserve native geometry in any proposed active recipe. A potential gradient-scale experiment must leave pre-optimizer screen-space densification evidence/cadence unchanged, so it does not silently become a topology-threshold ablation. Compare both dense and KF-only; offline behavior is diagnostic only and must subsequently pass the existing full-time online contract. No optimizer or loss modification has yet been made.

### Solver-only panel v17_solver_only/utmm/square-1/growth_ervs/seed0

held-out 23.315265dB, 80.614/80.714초, 13296 Adam; 전체시간 계약 PASS.
Artifact: `online_dense_training/v17_solver_only/utmm/square-1/growth_ervs/seed0/`.

### 2026-09-25 — v17 solver-only complete; quality goal not achieved

| Scene | v17 | vs v16 | vs KF-only | vs production | Native/photo steps |
|---|---:|---:|---:|---:|---:|
|rpng|25.001349|-0.053810|-0.224500|+0.555161|1831/3644|
|aria|27.549683|-0.010045|-0.031579|+1.654987|831/11096|
|utmm|23.315265|+0.072258|+0.379406|+1.933157|542/12754|

All3 runs pass the complete setup-inclusive clock, causal/held-out exclusion, committed-count reconstruction, independently repeated evaluation and zero-tail checks. Source/control contracts differ from v16 only in disabling the optional pose-fit observer; the same actual CorrespondenceRefiner remains. Mean versus v16+0.002801, KF+0.041109, production+1.381102dB. RPNG−0.224500 and Aria−0.031579 remain below KF; **not accepted**, no fast-convergence or repeated-seed claim. Observer removal is behavior-equivalent for individual checked solves, but online time-dependent service schedules change; endpoint differences are not paired equal-step effects.

Artifact: `v17_solver_only/summary.json`, per-run result/contracts/source locks/audits and snapshots, `v17_solver_only_panel.log`; all41 preserved sources in `source_v17/index.json`. GPU idle after completion; production checkout remains clean.

Next concrete diagnostic: measure native multi-view versus single-image photo gradients and shared Adam moments on actual training inputs. Native sums and photo single-image reductions differ, but their harmful interaction remains unproven. Do not turn off depth/normal, alter topology thresholds, select scene-specific phases, or reset Adam in the accepted recipe based on this suspicion. Any offline isolation must preserve the RGB term and make its after-EOS status explicit; any candidate must then pass the same online controls. Final 3-seed comparisons, final stream-quality curves, production worker integration and manuscript alignment remain incomplete.

### 2026-09-25 — native/photo Adam observer prepared

`optimizer_moment_probe.py` reads up to4096 evenly strided coordinates per Gaussian parameter group before each sampled actual Adam step. It separates native/KF-photo/dense-photo from the real pending selection and per-view native loss calls, preserves the original deadline guard, and later joins each record to the completed service ledger. It reports gradient RMS, old moments, old/current contributions to the predicted Adam delta, directional cosine, and agreement with the actual parameter delta. It does not change any gradients, moments, selection, losses, learning rates or topology. It is intentionally a replay-only diagnostic adapter; do not install the global Adam hook in concurrent live tracking.

Four CPU tests pass: parameters/gradients/Adam state unchanged versus unobserved optimization, independent Adam-delta prediction, deliberately conflicting momentum detection, zero/missing gradients, and actual installer source/batch/step labels. This tests observer correctness, not dense quality.

Preregistered `optimizer_scale_audit/v2_online_probe`: all three fixed scenes, v17 growth+recent-ERVS policy, every32nd attempt separately by native/KF-photo/dense-photo, observations included in the existing total clock, no held-out evaluation needed because this run diagnoses training dynamics only. No new policy or geometry loss intervention. Exact sources and native dependencies are locked before/after each worker. `run_online_optimizer_probe.py`; quality and the active goal remain unproven.

### 2026-09-25 — actual optimizer observer complete: no dense-specific momentum failure established

All three diagnostic replays pass source/native-dependency immutability, full time/zero-tail/held-out contracts and exact record-to-service joins: RPNG173, Aria370, UTMM405 sampled steps (948 total). Four observer tests passed before execution. `optimizer_scale_audit/v2_online_probe/{progress.json,gradient_summary.json}` and per-scene reports preserve raw group statistics and source/step IDs. These observer runs are not PSNR comparisons.

Final-generation median native batch size is17; photo steps use1 image. Median sampled xyz gradient RMS native/KF-photo/dense-photo: RPNG3.531e-4/2.078e-4/1.865e-4, Aria2.719e-4/1.171e-4/1.118e-4, UTMM3.489e-4/2.041e-4/1.853e-4. History/current contributions to the Adam delta are around2.2–2.9 across all sources, not a dense-specific imbalance. Estimated whole-model first-order ascent fraction is0 for all dense samples in each scene; KF is0 except1/136 Aria samples. Group-wise occasional ascent is not whole-model failure. Actual/predicted Adam deltas differ only at small floating-point rounding scale (raw errors retained), consistent with unchanged step behavior.

This weakens the specific hypothesis of dense-only destructive shared momentum. It does not prove equal conditioning, exclude longer-term objective interactions, or establish the effect of batch normalization. Do not reset/divide Adam or rescale native gradients based solely on batch size. Production and active mapper sources remain unchanged.

Next isolate the previously untested depth/normal interaction with a controlled offline factorial: KF-only versus visually corrected mixed RGB pool, crossed with depth/normal present versus absent, restoring the same checkpoint/Adam and holding RGB terms, native carrier views, photo schedules, render/step counts, topology and evaluation fixed. This is a causal-factor diagnostic after EOS, not an active recipe change or online success claim.

### 2026-09-25 — controlled depth/normal factorial preregistration

Prepared `diagnose_geometry_interaction.py`. The Aria pilot uses the existing visually corrected training-only checkpoint from `causal_visual_dense_pose_fixed_map/aria/aria1253`, with exactly the same Gaussian parameters, Adam state and training poses in all four arms: KF-RGB, mixed-RGB, KF-RGBDN, mixed-RGBDN. Each arm performs5000 dedicated RGB steps and312 fixed native steps with17 KF carriers (10304 training renders,5312 Adam steps). Native carrier schedule is identical across all arms; each RGB-vs-RGBDN pair has identical photo selections. Both retain the native masked RGB term unchanged; only inverse-depth and normal weights differ. Normal computation remains in both branches to avoid hiding a changed render workload. Isotropic prior remains off, matching the established backend default. No new birth/prune events occur in this frozen-map diagnostic.

The every16-photo/native cadence is a common **offline diagnostic schedule**, not an adopted streaming policy or scene-specific phase; it does not reproduce all live scheduling or learning-rate history. All training is afterEOS and is explicitly reported as5312 tail steps. Evaluator cameras remain separate and are used only for initial/intermediate/final and saved-map repeat evaluation. Final result is the interaction `(mixed−KF) with geometry − (mixed−KF) without geometry`, not a streaming success claim.

`check_geometry_interaction.py` exercises the actual RGB-D/normal helpers on CUDA: toggling geometry leaves image gradients bit-identical, turns only depth gradients off/on, preserves the RGB mask, and retains identical native schedules across pools. The source/checkpoint/native library hashes are checked before/after each arm. Start with Aria, where the prior RGB-only dense benefit was measured; expand to the other two fixed goal scenes after validating the pilot contract. Do not remove native geometry from the active mapper on the basis of an offline result.

### 2026-09-25 — geometry factorial v1 failed; masked inverse-depth arithmetic repaired in diagnostic only

Aria KF-RGB v1 stops at its first native batch with `Nonfinite native loss`; no final score or comparison is valid. Logs, selection and exact runner are preserved in `geometry_interaction/v1/aria/aria1253/` and `aria_v1.log`. The first native batch's17 observed depth maps are finite and strictly positive. The existing loss computes inverse rendered depth before masking, so zero rendered depth can yield inf×0 even when the geometry coefficient is zero.

A CUDA edge-case check reproduces that helper failure with zero rendered depth. Diagnostic v2 preserves the same masked RGB L1, alpha, inverse-depth validity threshold and all-pixel mean, but replaces invalid depths before reciprocal. Valid-input image/depth gradients are bit-identical to the legacy formula; invalid-input losses/gradients are finite. Geometry on/off image gradients remain identical. `geometry_interaction/check_v2/result.json`. The actual first batch now records rendered/observed zero/nonfinite counts and separate legacy/normal finiteness to verify the failure mechanism in real data. The active native mapper helper is unchanged; do not claim its live runs suffered this failure without live evidence.

Rerun the same preregistered four-arm Aria diagnostic under `geometry_interaction/v2/`; no source overwrite or reuse of v1 results.

### 2026-09-25 — correction to v1 failure localization

The v1 exception log does not record the native batch ordinal. It failed before the first250-photo checkpoint, but the prior entry incorrectly called it the first native batch. v2's explicitly measured first batch has no zero/nonfinite rendered depths and finite legacy RGB-D/normal terms in all17 views. The synthetic invalid-depth edge case is confirmed, but the exact real v1 failure location/cause still requires replaying its unchanged loss with per-batch failure capture. Keep that distinction; v2 progress alone is not proof of the precise v1 failure mechanism.

### 2026-09-25 — Aria depth/normal factorial v2 complete

| Pool | Native RGB only | Same RGB + depth/normal |
|---|---:|---:|
| KF |29.006171|28.791550|
| Mixed, visually corrected dense |29.508954|29.223642|
| Mixed−KF |+0.502783|+0.432091|

Geometry interaction is−0.070692dB. Thus the dense benefit survives geometry supervision in this particular controlled offline setting; depth/normal alone does not explain the online disappearance here. It does not exclude growth/topology/pose-age/cost interactions during real streaming. All four arms share exact checkpoint/initial score/Adam initialization, photo-pair and native schedules,10304 renders/5312 updates, fixed Gaussian count, held-out exclusion and saved-map reevaluation. This is explicitly afterEOS optimization and does not satisfy the online goal. `geometry_interaction/v2/aria/aria1253/comparison.json`, native dependency/source locks, per-arm schedules/curves/maps/results.

The v2 first-batch validity record remains entirely finite; exact v1 failing-batch capture is still pending. No active mapper depth/normal loss was changed. Next transfer this exact offline protocol to the other two goal scenes, without parameter changes.

### 2026-09-25 — growth capacity accounting, candidate hypothesis only

`growth_capacity_audit/v1/result.json` preserves v17 endpoint arithmetic: RPNG186KF+85dense=271 images after5475 steps; Aria91+185=276 after11895; UTMM70+207=277 after13296. Existing kappa64 limits added dense views alone to floor(completedRGBsteps/64), without accounting for mandatory KF inventory. This is an intentional existing rule, not a demonstrated counting bug. Native steps contain multiple images, so steps/pool is not actual per-image service.

Candidate to test after geometry diagnostics: require room for the **whole current training set** before another optional image is admitted: `allowance=max(0,floor(completedRGBsteps/kappa)−|KF union admitted_dense|)`. Keep kappa64, current actual-work credit, temporal-maximin candidate selection, native geometry/birth, recent ERVS and CPU history unchanged. Mandatory new KFs may temporarily exceed this heuristic capacity; never reject a KF or evict previously admitted dense images. Resume optional growth when observed work earns room; promotion of an admitted frame to KF must not charge it twice. This uses only current work/inventory and no scene identity, sequence horizon, phase cutoff or evaluator feedback.

At the frozen v17 endpoint work counts, this would leave optional-image room0/94/137 before subtracting existing dense membership. Those numbers are **not predicted online admissions or quality**: changed preparation costs and training would change the trajectory. The hypothesis is budget competition, particularly in the high-KF/low-free-work RPNG stream. It is not evidence that rejecting dense images guarantees improvement. The active mapper is unchanged; eventual acceptance still requires both controls, ablations, all-scene repeats and real stream curves.

### 2026-09-25 — three-scene depth/normal factorial complete

All12 arms pass the fixed-work/source/topology/held-out/saved-map contracts. Dense−KF gains, RGB-only / same RGB+depth-normal: Aria +0.502783/+0.432091dB, RPNG +0.037869/+0.048939dB, UTMM +0.594632/+0.408544dB. Geometry interactions are −0.070692/+0.011071/−0.186089dB respectively. Thus geometry attenuates the gain in two scenes but does not remove it; RPNG has little offline marginal dense benefit even without geometry. Keep native supervision unchanged. All results are afterEOS frozen-topology diagnostics, not online quality or acceptance. Artifact: `geometry_interaction/v2/summary.json`.

### 2026-09-25 — exact v1 failure reproduced

The preserved v1 source fails at native batch3, after48 photo steps and2 completed native steps. Views1016 and978 have1 and2 zero rendered-depth pixels, finite GT depth and finite normal terms; legacy RGB-D scalars are nonfinite while the v2 valid-depth reciprocal returns a finite total on the same batch. This establishes the original offline failure mechanism and corrects the earlier uninstrumented first-batch claim. Active mapper unchanged; this is not evidence of online gradient corruption. Artifact: `geometry_interaction/v1_failure_reproduction/result.json`, preserved training tensors and source locks.

### 2026-09-25 — whole-pool capacity v18 preregistration

Implemented opt-in `growth_budget_scope=whole_pool` with legacy `dense_only` default preserved. A dense admission requires resulting unique KF+dense pool size <= floor(completed RGB optimizer steps/64). Mandatory KF arrivals remain unconditional, old dense images stay available, and promotion is counted once. Native RGB-D carriers, Gaussian birth/topology, pose solver, recent ERVS and full CPU history are unchanged. Runtime records each admission capacity and fails on a violation. Six new policy cases plus26 existing policy/recent-count/residency tests pass under the actual conda environment; initial system-Python attempt lacked torch and was rerun successfully. Actual trainer reset preserves the new scope. Sources preserved in `source_v18/index.json`.

Preregistered seed0 panel: three fixed scenes × (growth_ervs, KF-only, production), same source and full setup-inclusive 1.5× time budgets with100ms reserve and intermediate-map snapshots. This is a frozen-causal-tracker online mapper replay, not concurrent live tracking. No scene tuning; candidate remains unaccepted until results, both controls, repeats and quality curves support it. Runner `run_online_whole_pool_panel.py`; results `v18_whole_pool/`.

### Whole-pool panel v18_whole_pool/rpng/table_06/growth_ervs/seed0

held-out 25.211392dB, 138.277/138.367초, 6766 Adam; 전체시간 계약 PASS.
Artifact: `online_dense_training/v18_whole_pool/rpng/table_06/growth_ervs/seed0/`.

### 2026-09-25 — common evaluation coordinates and live integration audit

Prepared `export_group_online_snapshots.py` for candidate plus both controls in one shared evaluation gauge, retaining each map and actual capture time. Two CPU tests pass: per-map geometry/timestamps preserved with shared trajectories; mismatched common KF poses rejected before export. No intermediate quality values produced yet, and similarity-alignment residual acceptance remains open. Independent helper does not alter locked v18 mapper sources.

Read-only `live_worker_integration_audit/v1/audit.json` identifies actual worker idle routing, eager dense registration, error/EOS queue cleanup and instance-scoped mapper guards still needing integration. Replay-global Adam guard must not affect a concurrent tracker. Production checkout is clean; no strict concurrent-live claim.

### Whole-pool panel v18_whole_pool/rpng/table_06/kf_only/seed0

held-out 25.233022dB, 138.271/138.367초, 6977 Adam; 전체시간 계약 PASS.
Artifact: `online_dense_training/v18_whole_pool/rpng/table_06/kf_only/seed0/`.

### Whole-pool panel v18_whole_pool/rpng/table_06/production/seed0

held-out 24.450921dB, 138.288/138.367초, 3434 Adam; 전체시간 계약 PASS.
Artifact: `online_dense_training/v18_whole_pool/rpng/table_06/production/seed0/`.

### 2026-09-25 — live guard/worker primitives prepared, not yet connected

Added opt-in `mapper_execution_guard.py` and `online_mapping_worker.py` in the isolated backend. Instance-local optimizer hooks avoid touching tracking optimizers; actual post-sync completions are audited and overruns fail rather than disappear as cancelled work. FIFO worker explicitly cancels queued packets at EOS, catches idle/packet exceptions and completes queue bookkeeping so waiters are released. Five guard tests plus five worker lifecycle tests pass on CPU (same Adam parameters/moments, deadline rejection with tracker unaffected, EOS race detection, generation/thread ownership, FIFO ordering, pending cancellation and both error paths). Preserved exact sources/tests in `live_worker_integration_audit/v1/`.

These helpers are not imported by the active v18 mapper/production worker and do not establish a live end-to-end claim. CUDA owned-stream completion behavior and integration with tracker packet/PGBA synchronization remain unverified; existing locked v18 source files remain unchanged.

### Whole-pool panel v18_whole_pool/aria/aria1253/growth_ervs/seed0

held-out 27.732228dB, 97.553/97.650초, 13120 Adam; 전체시간 계약 PASS.
Artifact: `online_dense_training/v18_whole_pool/aria/aria1253/growth_ervs/seed0/`.

### Whole-pool panel v18_whole_pool/aria/aria1253/kf_only/seed0

held-out 27.560364dB, 97.552/97.650초, 16823 Adam; 전체시간 계약 PASS.
Artifact: `online_dense_training/v18_whole_pool/aria/aria1253/kf_only/seed0/`.

### Whole-pool panel v18_whole_pool/aria/aria1253/production/seed0

held-out 25.852154dB, 97.552/97.650초, 11024 Adam; 전체시간 계약 PASS.
Artifact: `online_dense_training/v18_whole_pool/aria/aria1253/production/seed0/`.

### Whole-pool panel v18_whole_pool/utmm/square-1/growth_ervs/seed0

held-out 23.484316dB, 80.614/80.714초, 13869 Adam; 전체시간 계약 PASS.
Artifact: `online_dense_training/v18_whole_pool/utmm/square-1/growth_ervs/seed0/`.

### 2026-09-25 — separate live integration worktree and backend optimizer boundary

Created `/home/intern/VIGS-SLAM-online-worker-integration` on `research/online-worker-integration`, base d8c2eb76 plus27 exact current candidate/helper/test overlays (`live_worker_integration_audit/v1/worktree_overlay.json`). The running v18 source and production checkout remain untouched.

Routed all16 backend optimizer.step sites plus the common photometric step through a mapper-owned boundary, default guardNone preserving the original optimizer call. Instance hooks distinguish main/auxiliary work and rebind an optimizer on map generation changes. The first static check caught a missed plural-named keyframe optimizer; it is now included. A transient indentation error was fixed before tests passed. Eight CPU guard/backend tests pass, including unchanged Adam parameters/moments, EOS rejection, auxiliary coverage and unrelated tracking optimizer independence. Exact sources/results: `live_worker_integration_audit/v2_backend_boundary/`.

The actual VIGS worker, arrived RGB/IMU store, topology/control boundaries and owned CUDA stream are not connected or validated yet. These implementation checks are progress only; they are not a live quality result. Final recipe/repeats/curves/paper alignment remain incomplete.

### Whole-pool panel v18_whole_pool/utmm/square-1/kf_only/seed0

held-out 22.932163dB, 80.614/80.714초, 19073 Adam; 전체시간 계약 PASS.
Artifact: `online_dense_training/v18_whole_pool/utmm/square-1/kf_only/seed0/`.

### Whole-pool panel v18_whole_pool/utmm/square-1/production/seed0

held-out 21.366874dB, 80.618/80.714초, 7456 Adam; 전체시간 계약 PASS.
Artifact: `online_dense_training/v18_whole_pool/utmm/square-1/production/seed0/`.

### 2026-09-25 — arrived-input store and synchronous control futures

In the separate worker integration tree, `ArrivedSensorStore` accepts only explicit timestamp-ordered CPU RGB/adjusted IMU samples; it retains no held-out pixels, external poses, depth or future manifest. It exposes the load_rgb/load_dense_interval interface used by deferred preparation and immutable observed IMU prefixes. Three CPU tests pass for producer-buffer reuse, held-out/future exclusion, timestamp order and EOS rejection.

Worker submissions now return Futures so blocking pose/control operations can stay on the mapper thread. Both failures and EOS resolve/cancel pending Futures and queue accounting; seven worker tests pass. Exact sources/results: `live_worker_integration_audit/v3_sensor_and_control/`. VIGS routing, current-IMU shaper adaptation and CUDA integration are still pending, with no claimed quality or live result.

### 2026-09-25 — v18 whole-pool seed0 panel complete

| Scene | Candidate | KF-only | Production | Candidate−KF |
|---|---:|---:|---:|---:|
|rpng|25.211392|25.233022|24.450921|-0.021630|
|aria|27.732228|27.560364|25.852154|+0.171864|
|utmm|23.484316|22.932163|21.366874|+0.552153|

All9 whole-clock/zero-tail/held-out/source/count contracts pass. Mean delta KF +0.234129dB, production +1.585996dB, prior candidate v17 +0.187213dB. Common evaluation cohorts/reference trajectories and time budgets verified. RPNG remains slightly negative; no final acceptance or persistent-regression conclusion from seed0. Intermediate curves, final3-seed comparisons, actual worker integration and paper alignment are still incomplete. Candidate remains whole_pool/kappa64/recent ERVS/tau1/N with native geometry/birth unchanged. Sources43 files in source_v18; full report v18_whole_pool/summary.json.

### 2026-09-25 — v18 shared-coordinate export strict check failed; observed-anchor subset protocol

The first RPNG group export rejected nonidentical common KF poses before writing any map: snapshot0 differs from production on14/32 poses, max matrix difference0.001113; snapshot1 differs on up to6/90, max0.002339; snapshot2 all147 poses match. Candidate/KF are identical except5 recent poses at snapshot1 (max0.000837). Actual capture times differ by up to~0.3s; do not silently treat every pose as identical or loosen a numerical tolerance. Raw diagnostic: `v18_whole_pool/rpng/table_06/shared_group_export_diagnostic.json`; original empty export stdout preserved.

Before any intermediate PSNR evaluation, opt-in `identical_anchor_subset` exports using all and only exactly identical common training-KF poses, requiring at least3 nondegenerate anchors. No PSNR/scene/temporal cutoff determines selection. It preserves original maps/membership/timestamps and records excluded UIDs/matrix differences and alignment residuals. Default strict behavior still rejects differing poses. Three group-export plus4 curve tests pass; evaluator verifies exact group-exporter hash. This common-gauge construction does not establish that remaining nonrigid reference drift is negligible. Review residuals before making a convergence claim.

### 2026-09-25 — v18 shared-subset exports complete; curve diagnostics prepared

All9 states exported for all3 methods with identical evaluation trajectories per scene/checkpoint and unchanged Gaussian parameters. Selected anchors RPNG18/84/147, Aria23/45/67, UTMM18/26/48. Excluded differing poses and exact capture times are preserved in per-scene shared_subset_group_export.json. Global reference-to-snapshot alignment remains imperfect: Aria75% center RMSE0.07133 and max orientation3.315deg; RPNG max orientation1.585deg. Thus upcoming common-coordinate PSNR curves are diagnostic, not yet reliable evidence of exact or pose-independent fast photometric convergence. Need assess the effect of evolving nonrigid trajectory state before final interpretation. Original strict export failure preserved.

Prepared post-run rendering of three intermediate states plus endpoint for all9 seed0 runs, independently repeated fixed-cohort evaluation, no optimizer updates. Runner run_whole_pool_stream_panel.py, preserved8 source/test files in source_v18_stream/index.json. No active mapper source changes during measurement.

### v18 saved-state quality curve

rpng/table_06/growth_ervs: 34.92s:14.3760dB, 69.51s:22.6861dB, 104.28s:23.9729dB, 138.28s:25.2114dB. Fixed held-out cohort 555; common evaluation coordinates; post-run rendering only. Alignment residuals remain unaccepted; no exact first-attainment claim.

### v18 saved-state quality curve

rpng/table_06/kf_only: 34.89s:14.4297dB, 69.33s:22.7280dB, 104.41s:23.8332dB, 138.27s:25.2330dB. Fixed held-out cohort 555; common evaluation coordinates; post-run rendering only. Alignment residuals remain unaccepted; no exact first-attainment claim.

### v18 saved-state quality curve

rpng/table_06/production: 34.62s:14.4119dB, 69.52s:22.6222dB, 104.53s:23.9433dB, 138.29s:24.4509dB. Fixed held-out cohort 555; common evaluation coordinates; post-run rendering only. Alignment residuals remain unaccepted; no exact first-attainment claim.

### v18 saved-state quality curve

aria/aria1253/growth_ervs: 24.42s:11.6880dB, 48.83s:16.5951dB, 73.24s:17.9812dB, 97.55s:27.7322dB. Fixed held-out cohort 262; common evaluation coordinates; post-run rendering only. Alignment residuals remain unaccepted; no exact first-attainment claim.

### v18 saved-state quality curve

aria/aria1253/kf_only: 24.43s:11.6382dB, 48.83s:16.2596dB, 73.24s:17.8599dB, 97.55s:27.5604dB. Fixed held-out cohort 262; common evaluation coordinates; post-run rendering only. Alignment residuals remain unaccepted; no exact first-attainment claim.

### v18 saved-state quality curve

aria/aria1253/production: 24.44s:10.5841dB, 48.83s:15.1050dB, 73.24s:17.7968dB, 97.55s:25.8522dB. Fixed held-out cohort 262; common evaluation coordinates; post-run rendering only. Alignment residuals remain unaccepted; no exact first-attainment claim.

### v18 saved-state quality curve

utmm/square-1/growth_ervs: 20.18s:8.7015dB, 40.36s:14.2734dB, 60.57s:20.0331dB, 80.61s:23.4843dB. Fixed held-out cohort 324; common evaluation coordinates; post-run rendering only. Alignment residuals remain unaccepted; no exact first-attainment claim.

### 2026-09-25 — common runtime connected to actual VIGS worker API

Separate integration tree now accepts `VIGS(args, online_mapping=options)`. Common worker handles native packets and idle photometric service; RGB arrival passes only the adjusted IMU prefix into the CPU store. Mapper-processed training KF intervals feed deferred preparation, preserved gyro shaping/current-bracket repair, correspondence reuse, Growth and recent ERVS. Blocking packet Futures keep pose corrections on the mapper worker. EOS cancels pending work; legacy dense filler and offline termination are bypassed/rejected in this opt-in mode. Native/auxiliary Adam calls retain per-instance guards. Mapper RLock supports nested lazy Camera registration during guarded idle work; pose/photo synchronization is scoped to the current mapper stream.

Three CPU tests exercise the actual VIGS._gs_worker method with fake native rendering: completed native work reaches the common counter; held-out and not-yet-arrived native packets fail before Adam. Three analytic gyro tests verify known curvature, current-bracket convention and invariance to later IMU. Together with related guard/worker/input/reset/residency checks,31 CPU tests pass. This is routing/contract evidence only, not native CUDA rendering or quality. Sources/results preserved in live_worker_integration_audit/v4_vigs_routing.

Remaining explicit limits: no CLI wiring yet; CUDA data/stream dependency and complete reset/control behavior still need real runs. Empty held-out-only pose-control packets currently fail explicitly rather than silently dropping a map correction. Configurations must retain accepted native geometry/topology settings. End-to-end mapper time/zero-tail/quality and final3-seed validation remain unproven. Running v18 snapshot evaluation uses the original isolated backend; production checkout remains clean.

### v18 saved-state quality curve

utmm/square-1/kf_only: 20.18s:8.7536dB, 40.36s:14.1964dB, 60.54s:19.6447dB, 80.61s:22.9322dB. Fixed held-out cohort 324; common evaluation coordinates; post-run rendering only. Alignment residuals remain unaccepted; no exact first-attainment claim.

### v18 saved-state quality curve

utmm/square-1/production: 20.18s:8.3025dB, 40.56s:12.7913dB, 60.54s:18.1897dB, 80.62s:21.3669dB. Fixed held-out cohort 324; common evaluation coordinates; post-run rendering only. Alignment residuals remain unaccepted; no exact first-attainment claim.

### 2026-09-25 — actual packet identity fix and first native CUDA worker check

The integration-only call_gs filtered held-out video indices without filtering corresponding SE3/scale updates. This could apply another frame's correction; native PGBA also indexed filtered tstamp by original video slots. Fixed both: packet-aligned observation/correction filtering before RGB preparation, local packet indices with source_video_idx retained. Exclusively excluded corrections affect no mapped KF; they now return without loading RGB. Ambiguous correction shapes fail explicitly. Actual call_gs construction tests exercise real SE3 tensors and image/depth/normal identity; related CPU suite28 checks pass. This bug was in the new integration glue, not evidence that the already-correct archived v18 packet builder had this bug.

Captured the exact native dense_rr_imu/online_rank/final-v7 configuration before model construction. A separate CUDA check uses the actual VIGS worker + GSBackEnd + common runtime, with the first causal Aria packet and only arrived RGB/IMU. Original native geometry/birth are retained; test stops after1024 common RGB steps on the owner thread, not an adopted temporal phase policy.

Owned-stream check failed at513 committed steps on the first admitted dense view(uid41): visual pose became nonfinite. The same input/configuration on the default stream passed1024 steps with8 dense views, held-out retained0, late Adam0. Native DROID and LieTorch CUDA source contains launches without an explicit current stream. This supports an execution-order defect; an isolated current-stream extension build is the next controlled intervention. No shared/production extension is overwritten. Neither check is a whole-stream timing or quality result.

Evidence: live_worker_integration_audit/v5_packet_identity/{summary.json,cpu_checks.log,source_v1/index.json,aria_setup/,cuda_growth_v1/,cuda_growth_default_v2/}. The initial failure and exact53 source/test files are preserved. The earlier live_dense_pose_refresh module rename and replacement-model topology hooks are included in this snapshot. Final repeated quality, current-policy ablations, accepted convergence evaluation, complete reset/control integration and paper alignment remain incomplete.

### 2026-09-25 — isolated current-stream CUDA extensions remove first-dense failure

Copied native extension sources into v6_current_stream_extensions/source and changed46 two-argument kernel launches to use at::cuda::getCurrentCUDAStream(): VIGS23, correlation2, alternative correlation2, LieTorch19. Built separate vigs_backends.so and lietorch_backends.so with explicit sm120/O2; production/shared binaries unchanged. Reproducible builder: benchmarks/online_gs/campaigns/gain_attribution/build_mapper_stream_extensions.py. Source/binary hashes and build.ninja are preserved; integration check verifies the imported binary paths and hashes against the manifest.

With those extensions the actual worker on its owned CUDA stream completes1024 common RGB optimizer steps, prepares8 dense cameras, executes8 visual pose fits (~0.537s), and retains no held-out pixels. All tested final Gaussian parameter arrays are finite; no optimizer overrun. Same-extension default-stream control also passes1024 steps/8 cameras with identical image selection counts (~0.535s pose work). Final Gaussian counts differ25391 versus25400; no bitwise equivalence or quality equivalence claim is made. The original owned-stream failure at first dense camera is retained in v5. This supports the missing-current-stream diagnosis and closes that first-packet CUDA failure, not the complete online objective.

Evidence: live_worker_integration_audit/v6_current_stream_extensions/{manifest.json,summary.json,python_sources/index.json,cuda_growth_owned/result.json,cuda_growth_default/result.json}; build log v6_build.log. Partial causal-packet test only: it uses archived online tracker output and does not validate concurrent tracking, whole-stream timing or held-out quality. Next integration issue found: DepthVideo.rescale and TrackFrontend.remove_all_gaussians still invoke backend mutations from the producer thread; these must be routed through the owned worker before whole-stream validation. Final3-seed panel, current Growth/ERVS ablations, accepted convergence evaluation and manuscript alignment remain open.

### 2026-09-25 — producer controls routed through worker; first full Aria worker replay

Instance wrappers now send DepthVideo.rescale and TrackFrontend.remove_all_gaussians through the same FIFO/Future worker as native packets. Worker-owned calls execute directly to avoid self-deadlock; producer calls wait for the correct sequence position. Metric scale requires finite positive values. Controls after mapper EOS do not mutate the map. Replacement Gaussian topology hooks are rebound on the owner thread. Non-Adam control completion is separately synchronized/timestamped. Four new control tests plus related suites32 CPU tests pass.

First full raw-arrival Aria1253 replay through the actual common worker completed9137 Gaussian Adam steps(native1016/photo8121), with the archived causal metric-rescale and2 mapper-reset controls applied in order. Dense optimization resumed after resets. Fixed-cohort independent double evaluation gave27.4171606821dB twice, all per-view metrics identical, evaluation inputs unchanged. Actual full tracking is not claimed: this uses timestamp-paced RGB/IMU and frozen causal tracker packets.

Do not accept the first runner's valid_execution field as the complete time contract: its gate checked optimizer deadlines but did not independently timestamp worker stop and producer input preparation completion. That limitation is explicit in aria_growth_seed0/contract_review.json. Added those clocks and committed-history/growth invariants for the next v8 candidate/KF pair. KF-only uses the same recent ERVS so dense inclusion is the changed factor. All original run outputs and sources are preserved; v7 is diagnostic quality evidence, not final acceptance.

Artifacts: live_worker_integration_audit/v7_arrived_worker/{summary.json,cpu_checks.log,aria_growth_seed0/}. The run's source/source_lock preserves pre-v8 code. Current-policy repeat panel, other scenes, ablations, reliable convergence evaluation and manuscript alignment remain open.

### Arrived worker aria/aria1253/growth/seed0

27.340686dB, whole mapping 97.557s; 실행계약/독립이중평가PASS. 동일 ERVS를 사용한 dense 포함/제외 비교. Frozen causal tracker inputs; concurrent tracking claim 없음. Artifact: `/home/intern/gs_floaterLab/results/campaigns/gain_attribution/online_dense_training/live_worker_integration_audit/v8_whole_clock/aria_seed0/growth/seed0`.

### Arrived worker aria/aria1253/kf_only/seed0

27.162762dB, whole mapping 97.557s; 실행계약/독립이중평가PASS. 동일 ERVS를 사용한 dense 포함/제외 비교. Frozen causal tracker inputs; concurrent tracking claim 없음. Artifact: `/home/intern/gs_floaterLab/results/campaigns/gain_attribution/online_dense_training/live_worker_integration_audit/v8_whole_clock/aria_seed0/kf_only/seed0`.

### 2026-09-25 — first complete whole-clock Aria worker pair; productive-polling correction

v8 candidate27.340686dB versus same-worker KF-only27.162762dB, delta+0.177924dB. Both use recent ERVS; mapping time97.55735/97.55737s within97.65s, worker and producer preparation finish separately verified, zero-tail/held-out/growth/count contracts pass, independent double evaluation agrees. This is seed0 only; final acceptance and concurrent tracking claims remain false.

Inspection found that the worker waited up to2ms for an input before every idle optimizer step, even when it could already perform mapping. Candidate7762 photo steps imply at least15.524s accumulated queue-timeout intervals (some can overlap producer work, so this is not a guaranteed recoverable time gain). Revised polling checks queued inputs immediately, performs one productive idle step if available, and waits only when neither input nor mapping work is available. FIFO priority, EOS cancellation and error behavior remain tested. The17 worker/control/guard CPU tests pass, including queued input priority between productive steps and no timeout wait between productive steps. No loss, growth, selector or topology recipe change. Upcoming v9 reruns all3 scenes with this common execution policy.

Artifacts: v8_whole_clock/aria_seed0/summary.json and v9_productive_worker/{cpu_checks.log,source/index.json}. Original v8 source and results preserved. Remaining objective includes cross-scene common-worker comparison, final3 seeds, current-policy Growth/ERVS ablations, accepted convergence evaluation and paper alignment.

### Arrived worker rpng/table_06/growth/seed0

24.460546dB, whole mapping 138.316s; 실행계약/독립이중평가PASS. 동일 ERVS를 사용한 dense 포함/제외 비교. Frozen causal tracker inputs; concurrent tracking claim 없음. Artifact: `/home/intern/gs_floaterLab/results/campaigns/gain_attribution/online_dense_training/live_worker_integration_audit/v9_productive_worker/three_scene/rpng_seed0/growth/seed0`.

### Arrived worker rpng/table_06/kf_only/seed0

24.487964dB, whole mapping 138.309s; 실행계약/독립이중평가PASS. 동일 ERVS를 사용한 dense 포함/제외 비교. Frozen causal tracker inputs; concurrent tracking claim 없음. Artifact: `/home/intern/gs_floaterLab/results/campaigns/gain_attribution/online_dense_training/live_worker_integration_audit/v9_productive_worker/three_scene/rpng_seed0/kf_only/seed0`.

### Arrived worker utmm/square-1/growth/seed0

실패(exit 1); 로그와 상태 보존. 동일 ERVS를 사용한 dense 포함/제외 비교. Frozen causal tracker inputs; concurrent tracking claim 없음. Artifact: `/home/intern/gs_floaterLab/results/campaigns/gain_attribution/online_dense_training/live_worker_integration_audit/v9_productive_worker/three_scene/utmm_seed0/growth/seed0`.

### 2026-09-25 Actual worker selection-share audit

Existing saved service ledgers inspected; no new GPU run. Aria v8: native1016/photo7762/dense896; RPNG v9: native2456/photo3895/dense226; failed UTMM v9 diagnostic: native756/photo10667/dense4705. Dense fraction of all recorded map steps:10.2073%,3.5585%,41.1888%. ERVS step fraction:88.4256%,61.3289%,93.3818%. Native multi-view service counts:14697/34555/9894, so dense fraction of image usages is3.9895%/0.5878%/22.8831%, not a wall-time or gradient-weight share. Critical RPNG finding: all226dense steps belong to generation1 before reset; final generation7 has4817steps,182KFs,zero dense admissions andzero dense steps. whole_pool kappa64 permits floor4817/64=75 total slots at endpoint, below182mandatoryKFs. Final map thus received no direct dense supervision. This is a structural admission failure in this run, not a valid test that dense RGB is ineffective on RPNG. Source: live_worker_integration_audit/{v8_whole_clock/aria_seed0,v9_productive_worker/three_scene/{rpng_seed0,utmm_seed0}}/growth/seed0/worker_result.json under results/campaigns/gain_attribution/online_dense_training/. UTMM execution remains failed; three-scene/repeat goals incomplete.
