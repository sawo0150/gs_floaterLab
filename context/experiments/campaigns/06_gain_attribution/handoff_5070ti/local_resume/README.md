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
