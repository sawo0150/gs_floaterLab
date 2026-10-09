# Recipe D — C recipe + our fixes, built and validated locally (setup log, 2026-10-09)

**Name.** Recipe D = colin's Custom C recipe (SEW3 geometry + terminal opacity + FM, 6N) + scale cap 0.5 + selective
births 0.5/0.02. (Not to be confused with the gap-ladder rungs D1/D2/D4.)

**C snapshot (read-only from colin; colin files untouched).**
- VIGS-SLAM-custom main `4ad39496` fetched into local ref `colin-c/main`; local worktree
  `gsProjects/VIGS-SLAM-custom-c-snapshot-20261009` = 4ad39496 + colin's uncommitted diff (591 lines, 12 files) + 32
  untracked files (C recipe, geometry_c incl. SEW3 .cu, bounded RGB pool).
- 03_benchmark_contract code (other session's, untracked on colin) copied to
  `gsProjects/c_benchmark_contract_snapshot_20261009/03_benchmark_contract`.
- Archives (not in git) under `results/campaigns/gain_attribution/c_snapshot_20261009`, sha256:
  - fff600c03c1e022cb5468ca245a79b44817219629c082cf623370c4059438942  c_uncommitted.diff
  - c2d6e2dcacba35731af7a9ab3503ebac0f35236c450ef0eb1bf3952580cd28a5  c_untracked.tgz
  - 8bc291ae2f8d9aa2a8ad0728cd5e48f5740a353cef9bec1b0db54b32dcbc3cab  benchmark_contract_code.tgz
- RPNG table_06 6N input (scene contract, archive, reference scene; 2 MB) copied to `data/c_inputs/`; RGB frames already local.
**Local profile.** `results/local_machine_profiles/rtx5070ti_c_snapshot.json` (extra_datasets profile + C snapshot,
03_benchmark_contract, 6N inputs, RPNG raw, TRT profile → locally built engines in gsProjects/VIGS-SLAM/pretrained_models,
mapper_baselines outputs → results/campaigns/gain_attribution/recipe_d/mapper_baselines). CUDA_HOME=miniconda3/envs/3dgs
(nvcc 12.8 = torch cu128) for the SEW3 JIT kernels.
**Check.** `run_c_large_pool_v2.py --check-only` on table_06: preflight PASS, training budget 12,996 (6N).
**Reference.** colin C on table_06 (custom_c_remaining_dense1024_20261008_v1): PSNR 23.670, SSIM 0.792, LPIPS 0.185,
193,131 Gaussians.
**Next (GPU, needs approval).** (1) local C parity on table_06; (2) D = C + scale cap 0.5 + selective births via a
runtime shim around run_custom_c_large_pool_6n.py (no file edits in the C code).

## PREREG — C parity and recipe D on RPNG table_06 (2026-10-09, user approved: check the gain holds on the GPU)
Recipe D = C + scale cap 0.5 + selective births (already-explained pixels 0.02, others 0.5); nothing else changes.
`run_recipe_d.py --recipe C|D` loads the snapshot launcher run_c_large_pool_v2.py; for D only the training subprocess goes
through `d_recipe_shim.py` (runtime patches; C files untouched; writes recipe_d.json with projection calls and birth stats).
Runs (seed 0, --evaluate): C then D on table_06, queued after the RPNG decomposition (C requires an idle GPU).
Read-out: PSNR/SSIM/LPIPS vs colin C (23.670) and local C; D − C.

## First attempt failed: static TensorRT engines (2026-10-09)
C and D on table_06 both stopped within seconds: the profile pointed the TRT root at the locally built Aria engines
(static 464×464) while C expects colin's dynamic-shape profile (RPNG input 344×616). Archived under
`results/campaigns/gain_attribution/recipe_d/failed_attempts/static_trt_engine_table_06/`.
**Fix:** rebuilt the official-README dynamic profile on this GPU with the same builder
(`benchmarks/online_gs/build_exp78a_official_readme_trt.py`), TensorRT 10.13.0.35 (= colin), from ONNX with the same
SHA-256 as colin's README (DROID fnet 718acb9c…, update c5c4ef81… fetched read-only; Omnidata 538559de…, e2bb4f7d…).
Output: recipe_d/trt_profile_5070ti/pretrained_models (fnet min/opt/max 328²/368×584/656², update edges 1/24/60,
PGBA 1/85/120). ETH3D sofa_1 and TUM fr1_desk RGB copied read-only to data/c_raw (profile mappings added).

## PREREG amendment — 5 datasets (2026-10-09, user approved)
C and D (seed 0, --evaluate) on RPNG table_06, Aria 0416_301-1253, FAST-LIVO2 Retail_Street, ETH3D sofa_1,
TUM fr1_desk (10 runs; per scene C then D). Read-out per scene: local C vs colin C, D − C (PSNR/SSIM/LPIPS), recipe_d.json.

## 5-dataset run issues and fixes (2026-10-09, rerun approved)
- Evaluation failed for every finished run: `lpips` missing in the local vigs-slam-5090 env (training outputs intact).
  Installed lpips 0.1.4 (--no-deps; torchvision 0.23.0 present, alexnet weights cached). Evaluation-only pass via
  `eval_recipe_d.py` (launcher's evaluate_run.py + audit with its C environment; no training).
- table_06 D: CUDA OOM at 7,296/12,996 renders (16 GB card; colin C peaks 15.5 GB on a 32 GB card). Runs whose training did
  not finish are moved to recipe_d/failed_attempts/*_oom_or_incomplete and rerun with
  PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True (allocator setting only).

## Scope change (2026-10-09, user): skip VRAM-limited scenes
Scenes where C or D does not finish within 16 GB are skipped (no OOM reruns): RPNG table_06 (D OOM at 7,296 renders) and
FAST-LIVO2 Retail_Street (C OOM at 4,608, D OOM). Comparison on the scenes where both finish: Aria 0416_301-1253,
ETH3D sofa_1, TUM fr1_desk (evaluation-only pass; ETH3D/TUM GT depth copied read-only for the evaluator).

## Result — C vs recipe D on the scenes that fit in 16 GB (2026-10-09, seed 0, 6N, audits passed)
ETH3D sofa_1 C/D and TUM fr1_desk C were re-evaluated after GT depth was copied (first evaluation dirs archived as
failed_attempts/*_evaluation_missing_depth). `independent_GT` is false for Aria (MPS oracle reference), as on colin.
| dataset / scene | colin C | local C | D | D − C PSNR | D − C SSIM | D − C LPIPS | Gaussians C → D |
|---|---:|---:|---:|---:|---:|---:|---|
| Aria 0416_301-1253 | 27.004 | 27.029 | **27.459** | **+0.430** | −0.0002 | +0.0045 | 178,947 → 111,577 |
| ETH3D sofa_1 | 28.230 | 28.205 | **28.491** | **+0.285** | +0.0014 | +0.0012 | 105,202 → 41,566 |
| TUM fr1_desk | 19.924 | 19.897 | 19.962 | +0.066 | +0.0006 | +0.0057 | 103,573 → 46,663 |
Local C reproduces colin C within ±0.03 dB on all three. D: scale projection active (82–110 calls), 87–92% of new points
start at 0.02. PSNR improves on 3/3 (+0.07…+0.43), SSIM ≈ unchanged, LPIPS slightly worse (+0.001…+0.006), with
38–60% fewer Gaussians. Skipped for VRAM: RPNG table_06 (D OOM), FAST-LIVO2 Retail_Street (C and D OOM).

## Deployed on colin (2026-10-09, user request)
No colin file was edited (VIGS-SLAM-custom and 03_benchmark_contract stay as they are). gs_floaterLab was pushed
fast-forward to colin's sync repo (`/home/intern/git-sync/gs_floaterLab.git`, d6f29b01 → f7e9eb55) and cloned to a
separate folder `/home/intern/gs_floaterLab_recipe_d` (the shared `/home/intern/gs_floaterLab` checkout was not pulled).
`--check-only` of recipe D on ETH3D sofa_1 on colin: preflight PASS, budget 3,666 (6N). lpips present there.
**Run recipe D on colin** (same contract/output conventions as run_c.py; output must be a new folder):
```
cd /home/intern/gs_floaterLab_recipe_d/benchmarks/online_gs/campaigns/gain_attribution
/home/colin/miniconda3/envs/vigs-slam-5090/bin/python run_recipe_d.py --recipe D \
  --scene-contract <.../inputs/<dataset>/<scene>/v1/scene_contract.json> --output <new dir> --seed 0 --evaluate
```
`--recipe C` runs colin's C launcher unchanged through the same entry point. D = C + scale cap 0.5 + selective births
(already-explained pixels start at opacity 0.02); `<output>/recipe_d.json` records projection calls and birth counts.
