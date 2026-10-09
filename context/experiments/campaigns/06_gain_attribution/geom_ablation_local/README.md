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

## Local plan revision (2026-10-09, user, before any run)
Insertion is compared on the KF-window base: **R1 → R1-I → R2-I → R3 → R4** (R1-I = R1 with online-rank gradient-weighted
initialization; colin's R2 = KF pool with uniform init is dropped). Local copy only: `plan.json` (original kept as
`plan_colin_original.json`), `run_suite.py` order/condition list/summary arms, `run_arm.py` `--arm` choices. Arm behaviour
stays property-driven by plan.json; audits check quotas/membership/losses/carving from the same properties. 51 runs.

## Bug in the snapshot harness (affects colin too) and local fix (2026-10-09)
fr1_desk R4 and R4-replay-validation completed; R1 stopped at start: `install_initialization` (uniform init for R1)
reads `inspect.getsource` of `GaussianModel.create_pcd_from_image_and_depth`, but `recipe_setup` has already replaced it
by the online-density wrapper `with_frame_uid` (exp78b_replay_gsslam_mapping.install_online_density_policy), so the
expected source line is not found ("Uniform initialization patch no longer matches locked upstream method"). colin's
identical code will stop the same way at R1 (its R2 also uses uniform init). **Local fix** (copy only; original kept as
`ablation_support.py.colin_original`): patch the wrapped original inside the wrapper's closure and keep the wrapper
(tested: wrapper identity kept, inner method patched). R1 attempt archived under `failed_attempts/uniform_init_wrapper/`;
R1 row reset to queued; suite source locks regenerated (R4 runs did not execute the changed branch).
