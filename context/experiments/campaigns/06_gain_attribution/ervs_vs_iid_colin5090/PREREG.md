# Preregistration — ERVS K16 vs uniform (iid, K16) on extra scenes, colin RTX 5090 (2026-10-03, before any run)

User request: extend the sampler comparison to other datasets and use colin's idle RTX 5090 in parallel.

## Setup

Clean worktrees on colin (shared checkouts untouched; colin's VIGS-SLAM-custom has uncommitted terminal-prune work):
`/ssd/intern/paperExperiments/worktrees/vigs_b_6d200f0f` (VIGS-SLAM-custom 6d200f0f, adopted B) and
`/ssd/intern/paperExperiments/worktrees/gsfl_b_ablation` (gs_floaterLab). Machine profile
`benchmarks/online_gs/campaigns/gain_attribution/colin5090_worktree_profile.json` relocates only these code roots.
Runner `run_ervs_colin5090.py`: same arms, patches and gates as ervs_vs_iid_scenes (ervs_k16, uniform_iid,
uniform_k16), budget 25, seeds 0–2. Results are a separate GPU set (RTX 5090) and are not pooled with RTX 5070 Ti
cells without saying so.

## Scenes

1. aria301_12F (cvpr_assets frozen tracker archive and fixed_work_12f_v1 setup; 440 held-out views): 9 runs.
2. Next: Oxford Spires (cam0 + IMU + calibration downloaded; tracker archives and setups to be prepared and
   preregistered as an amendment before any run).

## Metrics

As ervs_vs_iid_scenes: seed-mean ΔPSNR, Δmin-bin, Δworst-Q1 for ERVS − uniform_iid, uniform_k16 − uniform_iid and
ERVS − uniform_k16; temporal curves. All scenes reported.

## Amendment 1 — Oxford Spires (2026-10-03, before any Oxford mapping run)

Five short sequences: 2024-07-09-new-college-01/02/04, 2024-03-20-christ-church-05, 2024-05-20-bodleian-library-02
(3,099–4,966 frames at 20 Hz). `prepare_oxford_vigs.py`: cam0 equidistant fisheye rectified to a 720×540 pinhole
(R = I, balance 0), IMU to ns/gyro/accel, calibration root from each sequence's INPUTS.json (nearest session),
Tcb = T_cam0_imu (C_q_CI, C_r_CI), held-out every 5th frame + final (same rule as aria301_12F). Tracker contract =
official Aria adapter (unchanged tracking parameters) with the Oxford IMU block. `prepare_oxford_capture.py`: frozen
official tracker capture (22ffe24, TRT dynamic RTX 5090 profile, seed 0), archive validation, native setup capture;
mapping config = vigs_final_v7_aria.yaml with the sequence IMU block. GT trajectories are not used. Then the same
3 arms × 3 seeds (45 runs). A sequence whose tracker capture or validation fails is reported and excluded, not tuned.

## Amendment 2 — Oxford long sequences and 700-view FIFO pools (2026-10-03, user decision; before any capped run)

christ-church-05 and bodleian-library-02 overflowed the tracker keyframe buffer (700) and are re-captured with
`--buffer 2048` (capacity only; the three passing captures are kept). On user instruction, all five Oxford sequences
are mapped with the KF pool and the dense pool each capped at the newest 700 views (FIFO, `pool_cap.py`, B_POOL_CAP=700;
dropped views stop being sampled, the map and membership are unchanged), phase `scenes_cap700`, 3 arms × 3 seeds,
45 runs. Uncapped Oxford runs already finished (phase `scenes`) are kept as a supplementary record (dense pools reached
768/712 on new-college-02/04, so they are not the same condition). Gate: pool_cap.json present with cap 700.
