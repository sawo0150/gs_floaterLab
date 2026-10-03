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
