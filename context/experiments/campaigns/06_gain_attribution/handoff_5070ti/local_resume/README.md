# Local RTX 5070 Ti resume — 2026-10-01

## Verified

- Lab main pulled through `362fcbd`; custom main through `50286727`.
- RTX 5070 Ti 16 GB, driver 595.84, Python environment `vigs-slam-5090`, PyTorch 2.8.0+cu128.
- All 119 locked sources and locked extension files match Colin hashes; both D3 and official vanilla imports succeed.
- RPNG/UTMM RGB for all 16 scenes match Colin under recursive rsync checksum comparison. Aria inputs and frozen archives are transferred separately.
- A process-local path profile preserves original source/manifest/setup bytes; runtime files and outputs are on the separate data volume. No optimizer/sampling/resolution change.
- [Aria pilot summary](aria_pilot_summary.json): all 4 runs pass execution checks and saved-map double evaluation. Vanilla also passes matched prefix-render and trajectory checks.

| Training renders/KF | D3 held-out PSNR | Vanilla held-out PSNR |
|---|---:|---:|
|15|23.463187|18.954431|
|40|25.760522|20.856435|

These are frozen causal tracker fixed-work results, not concurrent tracking or real-time claims. D3 proxy rendering remains extra work. This is a hardware migration pilot, not an isolated geometry-loss ablation.

## Resume plan

`resume_cvpr_5070ti.py` observes the initial pilot and transfer PIDs, validates inputs, completes the three-scene 12-run pilot and its checkpoint evaluation, then runs controls. The 19 passed Colin controls are excluded by dataset/scene/budget/arm identity; 121 remain. Pilot controls use fresh local references; other scenes use archived Colin references with no cross-GPU time comparison. The queue evaluates control checkpoints after training.

Failed or partial runs stop the queue; no output is overwritten or silently relabeled as passed. Checkpoint alignment rejection remains visible and does not support convergence claims. Geometry zero-weight controls and original 15/30/60 sampler reproduction remain subsequent work; FIFO/time panels remain deferred.

Local runtime status: `results/campaigns/gain_attribution/cvpr_assets/rtx5070ti_controls_v2/queue_status.json`. The companion queue log and per-run logs identify failures. The 3-scene pilot and remaining-input transfers were still in progress when this card was written.

## Checkpoint and historical-source audit

Aria pilot checkpoint evaluation finished: 4 runs × (6 immutable snapshots + final) = 28/28 evaluated, all 28 pass the pose-alignment acceptance gate. See [curve audit](aria_curve_audit.json). These use the predeclared 64-view convergence subset, not the full endpoint cohort.

The local original sampler worktree contained later edits. A new detached worktree `3dgs-custom-benchmark-b-handoff-20261001` was created at the historical `2debc8a` base. [Restoration patch](original_sampler_source_restore.patch) recovers the exact train/scheduler hashes recorded in all 152 historical benchmark-B executions; the original dirty worktree is untouched. The packet scheduler also matches. All 114 selected jobs' initial clouds match their historical `input.ply`; 171 metadata/schedule files are hashed in the [prepared manifest](original_sampler_manifest.json).

The new `resume_cvpr_5070ti_followup.py` waits for the verified controls coordinator and requires its successful endpoint/curve completion before running 20 clean D3 zero-weight controls and then the 114 historical sampler runs. It excludes live/time panels. Original replay checks camera cohorts and sampler histories against archived runs and evaluates the saved map twice for PSNR/SSIM/LPIPS. This follow-up was prepared but had not executed GPU jobs at this update.

## Archived-control coverage correction

The local controls coordinator covers 121 new runs. The 19 previously passed Colin runs also need checkpoint evaluation and table aggregation. Their raw maps/snapshots/metrics are now being transferred, without rerunning training. Follow-up v1 was stopped while still waiting (no GPU job started) and preserved with `superseded_before_gpu_work`; follow-up v2 includes these 19 evaluations before the geometry stage.

`build_measured_control_tables.py --panels ... --output-dir ... --require-complete` audits both old and new control summaries with their explicit paired references. It rejects conflicting cells and incomplete paired cohorts, and writes a review bundle without overwriting current manuscript assets. A real six-control subset passed source/pose/prefix/cohort/metric checks (8 unique rows including references); strict completion correctly rejected its incomplete coverage. See [validation](control_table_builder_validation.json). This is validation of the table pipeline, not a new training result.

## Local pilot independent free-space evaluation

The immutable local Aria maps were evaluated on the same hash-locked manual empty-space voxel mask and evaluation-only ORB trajectory. Registration median/p90 is 2.42/3.84 cm, common across all four maps. No optimizer or GPU training operation was performed for this evaluation.

| Training renders/KF | D3 count (opacity > .3) | Vanilla count | D3 opacity support mass | Vanilla opacity support mass |
|---|---:|---:|---:|---:|
|15|229|1098|265.851|805.572|
|40|155|447|188.507|324.063|

[Full result](aria_manual_regions.json) includes eroded/nominal/dilated-mask sensitivity, hashes, held-out quality and alignment details. This is a single-scene whole-system comparison; it does not isolate the D3 term and provides no dense-surface accuracy/completeness measurement. The separate zero-weight control is still pending.

## Archived controls evaluated while inputs transfer

All 19 existing Colin control maps completed checkpoint evaluation on the local GPU: 133 immutable/final states evaluated, 133 accepted by the pose-alignment gate. No training was repeated. See [audit](archived_control_curve_audit.json). The waiting local coordinator was held only to serialize GPU use and was automatically resumed after evaluation; its original input-transfer wait continues. The later follow-up will recognize and skip these already completed curve evaluations.

## Input-ready scheduling (controls v2 / follow-up v3)

Before any new control training, the waiting coordinators were superseded and preserved. The replacement still requires the complete three-scene pilot, but then admits each remaining scene only after its own full input hash audit. It evaluates already trained checkpoints while waiting for additional scenes. All 121 missing controls, the declared 20-scene cohort, source/configuration locks and final gates are unchanged; ordering uses file availability, never quality scores. Completion still waits for the full input transfer before the geometry follow-up.

A real-input readiness check found that RPNG v2 geometry references are bundled-file strings, while Aria v3 uses split depth/normal dictionaries. The orchestration validator now follows the frozen reader's support for both formats. The original archives and mapper reader were not changed. Complete Aria inputs pass both readiness and hash validation; the incomplete RPNG archive correctly remains ineligible. The missing-control count remains 121.

Active paths are `rtx5070ti_controls_v2`, `rtx5070ti_references_v2`, and `rtx5070ti_followup_v3`. The pilot remains `rtx5070ti_fixed_pilot_v1`; all completed pilot and archived-control evaluations are reused.

## First RPNG pilot passed

All three pilot inputs passed manifest/event hash and file-readiness checks; the pilot transfer exited successfully. RPNG table_06 D3 at 15 training renders/KF passed all execution checks and saved-map double evaluation: 3,405 training renders, PSNR 23.861218 dB. Vanilla at the same budget then started. This extends the completed Aria pilots; the full three-scene 12-run pilot remains in progress. See [current measured progress](pilot_progress.json). The new scene runs use the controls-v2 machine provenance, copied into the pilot output as `remaining_scenes_machine_provenance.json`.

## RPNG15 pair and workload scope

RPNG table_06 at 15 training renders/KF passed both arms, including execution gates, saved-map double evaluation, matched prefix-render and trajectory checks. D3/vanilla held-out PSNR is 23.861218/20.943542 dB. The 40-render D3 arm then started.

[Workload audit](rpng15_workload_audit.json): both arms perform 3,405 training renders, but D3 has 3,405 Gaussian Adam updates and vanilla has 445 (its logged optimizer-completion list). D3 adds 1,901 proxy renders. This is matched **training-render** work, not matched optimizer steps or total computation. The collector now reports vanilla's recorded Adam count instead of leaving it missing. No training code or recipe was changed for this bookkeeping correction.

## Three-scene migration pilot completed

All 12 endpoint runs pass their execution checks and saved-map double evaluation; see [endpoint audit](pilot_endpoint_audit.json). RPNG table_06 at 40 training renders/KF gives D3/vanilla 25.127686/22.595688 dB. UTMM square-1 gives 20.963081/15.884417 dB at 15, and 22.092829/18.871978 dB at 40. The pilot queue has moved to checkpoint evaluation; missing controls have not started yet at this update. These remain fixed training-render comparisons, with different Adam counts and extra D3 proxy renders.

## Checkpoint evaluator failure and recovery

The UTMM square-1 vanilla15 checkpoint evaluator terminated its leader with signal 11 and left worker threads alive. Its partial output is preserved as `curve_evaluation_failed_signal11`; the remaining threads of that owned evaluator were terminated, causing the old controls-v2 and follow-up-v3 queues to stop with failure records. The root cause is not established. An unchanged evaluation retry passed all 7 states and alignment gates. No map was retrained and no recipe changed. See [retry audit](checkpoint_retry_audit.json).

The coordinator now accepts a previously completed 12-run migration pilot when starting a fresh queue, instead of requiring only the initial four Aria runs. Active queues are **controls_v3 / references_v3 / followup_v4**. Completed evaluations are skipped; failed artifacts and old queue logs are preserved. Python fault reporting is enabled for the retry queue.

All 12 pilot runs now have their 84/84 checkpoint/final states evaluated; 84/84 pass the alignment gate. See [curve audit](pilot_curve_audit.json). The local queue has started the 21 pilot-scene controls, the first subset of 121 missing controls.

## First complete local 2×2 control cell

RPNG table_06, seed0, 15 training renders/KF; all four cells pass execution, paired prefix/trajectory/cohort checks and double evaluation. Each performs 3,405 training renders and Adam updates. [Measured CSV](rpng15_factorial.csv).

| Photometric RGB source | RR PSNR | ERVS PSNR | ERVS − RR |
|---|---:|---:|---:|
| dense |23.392751|23.861218|+0.468467|
| keyframe |23.802125|23.793913|−0.008212|

Dense minus keyframe is +0.067306 dB under ERVS and −0.409374 dB under RR. This single scene/seed does not establish aggregate benefit or statistical significance; the paired 2×2 layout preserves the interaction rather than claiming independent additive gains. Keyframe-vs-dense substitution remains a whole-system service comparison, not a claim of identical realized role histories. The 40-budget controls are running next.

## RPNG 40-budget 2×2 completed

The same scene/seed at 40 training renders/KF passes the paired execution and double-evaluation gates in all four cells; [CSV](rpng40_factorial.csv).

| Photometric RGB source | RR PSNR | ERVS PSNR | ERVS − RR |
|---|---:|---:|---:|
| dense |24.936771|25.127686|+0.190915|
| keyframe |24.947570|25.105440|+0.157870|

Dense minus keyframe is +0.022246 dB under ERVS and −0.010800 dB under RR. The RGB-source effect is small here; a general dense-view gain is not established by this scene. Native-geometry comparison at 40 is now running.

## RPNG pilot-scene controls completed

All seven table_06 controls pass the paired execution and saved-map double-evaluation gates; see [measured summary](rpng_controls_summary.json). At 40 training renders/KF, native geometry reaches 25.164496 dB versus D3 25.127686 dB: D3 is lower by 0.036810 dB on this scene. This does not demonstrate a photometric benefit from D3. Free-space/surface claims still require independent geometry metrics and the pending zero-weight control. Control checkpoint evaluation is pending; endpoint success alone does not establish convergence. The queue has moved to UTMM square-1.

## UTMM square-1 15-budget 2×2 completed

All four cells pass execution and double-evaluation gates; paired controls match prefix renders, poses, and held-out cohort. [Measured CSV](utmm15_factorial.csv).

| Photometric RGB source | RR PSNR | ERVS PSNR | ERVS − RR |
|---|---:|---:|---:|
| dense |21.275085|20.963081|−0.312004|
| keyframe |20.736773|20.716585|−0.020187|

At this budget, RR exceeds ERVS on both RGB sources; this contradicts a universal ERVS advantage. Dense minus keyframe is +0.246496 dB under ERVS and +0.538312 dB under RR. These are one-scene, one-seed measurements; preserve every scene in the aggregate. The 40-budget controls are now running.

## UTMM controls completed

All seven square-1 controls pass endpoint execution, paired prefix/pose/cohort checks, and double evaluation; [measured summary](utmm_controls_summary.json). Checkpoint evaluation remains pending. The 40-budget [factorial CSV](utmm40_factorial.csv) is:

| Photometric RGB source | RR PSNR | ERVS PSNR | ERVS − RR |
|---|---:|---:|---:|
| dense |22.114579|22.092829|−0.021751|
| keyframe |21.744696|21.814367|+0.069671|

At 40, native geometry reaches 22.161410 dB versus D3 22.092829 dB (D3 −0.068582 dB). Neither this nor the RPNG native comparison establishes a PSNR benefit from D3; geometry claims require their own evidence. The queue has moved to Aria1253 controls.

## Aria controls and second evaluator recovery

All seven Aria1253 controls pass endpoint gates; [summary](aria_controls_summary.json), [15-budget CSV](aria15_factorial.csv), [40-budget CSV](aria40_factorial.csv). Aria40 RR+dense is 25.883835 dB, ERVS+dense 25.760522 dB; native geometry 25.825594 dB. These do not establish a universal ERVS or D3 PSNR benefit.

The first Aria40 RR+dense evaluator wrote metrics but its leader exited with signal11 and left threads alive. Those owned threads were terminated; the failure row/log was preserved. A new evaluation-only sibling directory reused the immutable training map and passed two evaluations at exactly 25.883835 dB, with unchanged inputs and paired prefix/pose/cohort checks. No training was repeated.

The recovery helper then hung in the NTFS3 `lock_two_nondirectories` kernel wait while archiving an old evaluation file. A SIGKILL is pending for that helper (PID3348123); the filesystem wait is unresolved, and its paths are preserved without further mutation. It holds no GPU allocation. The old coordinator was stopped and its pending follow-up exited. A fresh coordinator now reuses all 21 passed pilot-scene controls via an explicit manifest and symlinks, including the successful evaluation-only retry, with original source locks. Active paths: **controls_v4 / references_v4 / followup_v5**; PIDs3348918/3348919. Input-audited aria1253rot training has started, confirming the new queue progresses. Remaining input transfer PID3333438 continues.

## Aria1253rot controls and continuing queue

All seven rotated-Aria controls pass recorded execution, paired prefix/pose/cohort, and independent double-evaluation gates: [summary](aria_rot_controls_summary.json), [15-budget factorial](aria_rot15_factorial.csv), [40-budget factorial](aria_rot40_factorial.csv). The D3 references for this scene are Colin's archived fixed-work maps; no cross-GPU time comparison is made. At 40 renders/KF, RR+dense reaches 25.235143 dB, D3+ERVS+dense 24.998511 dB, and native geometry 24.991874 dB. Thus, the rotated scene also does not support a universal ERVS advantage.

The previous controls-v4 coordinator blocked in NTFS3 metadata lookup while evaluating a completed checkpoint; the earlier evaluation-archiving helper remains in a kernel wait. All 17 nonpilot scene input-readiness checks returned zero missing files. The complete 28-row passed control summary and matching source lock are frozen as [reuse manifest](reused_controls_28.json) and [source lock](reused_controls_28_source_lock.json). The new coordinator reuses their recorded paired audits and double evaluations without reopening the blocked map file; this deliberate exception is recorded in its machine provenance. **controls_v5 / references_v5 / followup_v6** started, with RPNG table_03 training active. The old coordinator and follow-up received termination signals so they cannot resume conflicting work after the filesystem wait clears. Checkpoint curves for the remaining local controls and the full 20-scene tables are still pending.
