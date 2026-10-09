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
