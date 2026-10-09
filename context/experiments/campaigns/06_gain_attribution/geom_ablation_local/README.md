# TUM10 mapper/geometry ablation — local RTX 5070 Ti replication of colin's suite (2026-10-09, user: /loop run it)

**Source (read-only snapshot, colin untouched).** colin `03_benchmark_contract/mapper_geometry_ablation` (created by another
session on 2026-10-09 13:44–13:56) + its plan `results/campaigns/03_benchmark_contract/mapper_geometry_ablation_20261009_v1/
{plan.json, scene_selection.json}`; VIGS-SLAM-custom state identical to the recipe-D C snapshot (4ad39496 + same diff).
Archives + SHA256SUMS: `results/campaigns/gain_attribution/geom_ablation_snapshot_20261009/`. Code unpacked to
`gsProjects/c_benchmark_contract_snapshot_20261009b/`. Profile `results/local_machine_profiles/rtx5070ti_geom_ablation.json`
(C snapshot profile + this 03 snapshot + the plan path → `results/campaigns/gain_attribution/geom_ablation_local/v1`).
**Plan (unchanged from colin).** TUM RGB-D, 10 scenes (fr1 desk/desk2/floor/plant, fr2 desk/xyz, fr3 cabinet/
long_office_household/structure_notexture_far/structure_texture_near), seed 0, 6N budget, cumulative arms:
R1 KF window only (12:0:0, uniform-density init) → R2 + global KF pool ERVS (3:3:6, kf_native) → R2-I + content-aware
init (online-rank gradient-weighted) → R3 + immediate dense pool with KF normal + dense metric depth → R4 + online SEW3
carving (= C geometry; immediate membership). R4 runs first per scene and captures the causal frontend tape; other arms
replay it. Pilot fr1_desk includes an R4 replay-validation run; expansion only if capture/replay equivalence passes.
Readouts per arm (terminal stages) PSNR/SSIM/LPIPS, Gaussians, depth geometry. 51 runs.
**Local check.** `check_adapters.py` 10/10 PASS (immediate admission, bounded eviction, tape digest, RNG restore, ...).
**Run.** `run_suite.py --output <plan dir>` (same supervisor; waits for an idle GPU). VRAM-limited scenes are reported, not
retried (user rule for the 16 GB card).
