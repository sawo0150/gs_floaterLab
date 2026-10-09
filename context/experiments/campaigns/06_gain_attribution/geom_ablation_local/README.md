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

## Pilot passed; premature start for other scenes (2026-10-09)
fr1_desk pilot 6/6 completed and the capture/replay equivalence passed 7/7 (same tape, identical loss-view sequence,
same budget and mapping UIDs, Gaussian count / PSNR / depth MAE within tolerance; R4 PSNR 19.94). The other 9 scenes'
R4 failed immediately because the TUM 6N scene contracts were still being copied (my ordering error); 36 dependent
conditions were blocked. These attempts are archived under `failed_attempts/inputs_not_yet_copied/` and re-queued after
the copy finishes (no code change).

## Result — 51/51 completed (2026-10-09, TUM10, seed 0, 6N; local revision R1 → R1-I → R2-I → R3 → R4)
Means over the 10 scenes (`results/campaigns/gain_attribution/geom_ablation_local/v1/summary.json`):
| arm | PSNR | SSIM | LPIPS | Gaussians | depth MAE (m) | δ1 |
|---|---:|---:|---:|---:|---:|---:|
| R1 KF window, uniform init | 18.769 | 0.627 | 0.420 | 145,183 | 0.1488 | 0.925 |
| R1-I + content-aware insertion | 18.781 | 0.635 | 0.426 | 130,310 | 0.1503 | 0.924 |
| R2-I + global KF pool (ERVS) | 22.036 | 0.725 | 0.342 | 116,969 | 0.1190 | 0.954 |
| R3 + dense pool, KF normal, dense depth | 22.032 | 0.756 | 0.321 | 105,650 | 0.1139 | 0.958 |
| R4 + SEW3 carving (= C) | 22.018 | 0.756 | 0.322 | 105,720 | 0.1137 | 0.958 |
| R4-F (terminal opacity + FM export) | 21.984 | 0.755 | 0.324 | 89,808 | 0.1138 | 0.958 |
Per step (mean Δ, scenes improved /10): R1→R1-I PSNR +0.01 (5), SSIM +0.008, LPIPS +0.006, depth MAE +0.15 cm (5 better);
R1-I→R2-I PSNR **+3.26 (10/10)**, SSIM +0.090, LPIPS −0.084, depth MAE **−3.1 cm (9/10)**; R2-I→R3 PSNR −0.00 (5),
SSIM **+0.031**, LPIPS **−0.021**, depth MAE **−0.5 cm (9/10)**; R3→R4 ≈ 0 on all (depth −0.01 cm, 6/10);
R4→R4-F PSNR −0.03 (0/10), 15% fewer Gaussians. R4 PSNR on fr1_desk 19.94 (colin C 19.92).
**Reading.** On TUM10 the KF-pool replay is the dominant gain (+3.3 dB, −3 cm); dense pool + normal/depth losses help
SSIM/LPIPS/depth but not PSNR; content-aware insertion on the KF-window base and SEW3 carving are neutral on these
metrics; the terminal FM export trades −0.03 dB for 15% fewer Gaussians.
