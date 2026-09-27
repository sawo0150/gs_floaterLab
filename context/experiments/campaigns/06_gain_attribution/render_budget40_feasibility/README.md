# Is 40 training renders per KF a useful common budget?

2026-09-25: user requested checking the budget before changing the scheduler.

## Preregistered comparison

- Aria1253, RPNG table_06, UTMM square-1, seed0. Official vanilla and current paired architecture.
- Only the common training render budget changes from15 to40. No20/10/10 role allocation, new Growth/count policy, Carve, topology cutoff, or production change.
- Fixed-work phase: same causal tracker events, poses/depths, held-out split and exactly40 renders per map-generation KF admission at every input prefix. Existing native-one-step plus paired KF/dense remainder is retained. Vanilla consumes the same prefix work using its original window+global2 mapping. Native losses and topology remain arm-specific. Auxiliary camera renders and optimizer counts are reported separately. This phase is not a live timing claim.
- Live phase: actual RGB+IMU tracking at native timestamps, frontend4/2 and IMU pose prediction20/20/15; shared40 training render cap. Existing idle-only additional training is unchanged. Mapping optimizer stops at the source end-time; tracking backlog is reported. Same cap does not imply same completed renders or same online poses.
- Fixed-work results assess quality under the stated amount of work. Live results assess whether the current implementation realizes that work without falling behind. Failure to consume40 is not proof of a GPU hardware maximum below40.
- Judge held-out PSNR, completed native/KF/dense renders, map coverage, latency and elapsed time. Compare against the preserved15/KF runs. No threshold or recipe selected per scene. No post-EOS polishing.
- Seed0 is a feasibility screen, not training reproducibility or statistical significance. Saved maps are evaluated twice with identical inputs using the existing evaluator.
- The earlier~130 conversion describes a mature normal mapping call, not an exact universal per-KF cost.40 is a candidate budget, not a proven real-time point.

## Execution

Runner: `benchmarks/online_gs/campaigns/gain_attribution/run_budget40_feasibility.py`.
Results: `results/campaigns/gain_attribution/render_budget40_feasibility/`.
The existing15-named fixed-work runners retain their historical paths and15 defaults; explicit40 support only changes argument validation and reported budget metadata.

## Results

Pending. Per-run outcomes, including failures, are appended below.

**2026-09-25 (40 renders/KF / fixed / aria / paired):** execution=True, PSNR=24.859212001771418. Result=/home/intern/gs_floaterLab/results/campaigns/gain_attribution/render_budget40_feasibility/v1/fixed/aria/paired

```json
{
  "phase": "fixed",
  "dataset": "aria",
  "scene": "aria1253",
  "arm": "paired",
  "seed": 0,
  "output": "/home/intern/gs_floaterLab/results/campaigns/gain_attribution/render_budget40_feasibility/v1/fixed/aria/paired",
  "returncode": 0,
  "valid_execution": true,
  "evaluation": {
    "protocol": "saved_map_independent_double_evaluation_v1",
    "cooldown_seconds": 15,
    "input_sha256": {
      "ply": "3e0f52b453952be64fdf5376afca7d7075d0e10d6b96e359e852803026ccd3b2",
      "full_trajectory": "6f6c3c2b9cfe586bc0031f399fad88e3dca9a439714433d1edd9036a753ce197",
      "kf_trajectory": "24b8cb2bcf2452ce8083bb96fb7c47b056f14a191ce7edd28462a4c0dc99bcdb",
      "mapped_uids": "63fb40e3fc9e360741bc02b65a71fb0689c1f88e7c77f9457f5a93f134e7c207",
      "fixed_manifest": "40df31333e5bddd13ba178c7246d7d8fb364a32886a1345ac0d5e9748572713f"
    },
    "checks": {
      "unchanged_inputs": true,
      "same_views": true,
      "same_gaussian_count": true,
      "same_fixed_view_count": true,
      "psnr_agrees": true,
      "ssim_agrees": true,
      "lpips_agrees": true
    },
    "max_abs_per_view_difference": {
      "psnr": 0.0,
      "ssim": 0.0,
      "lpips": 0.0
    },
    "fixed_psnr_first": 24.859212001771418,
    "fixed_psnr_second": 24.859212001771418,
    "pass": true
  },
  "evaluation_error": null,
  "psnr": 24.859212001771418,
  "source_changed": [],
  "mapping_seconds": 51.43308878294192,
  "renders": {
    "all": 4876,
    "no_grad": 116,
    "training": 4760,
    "backward": 4760
  },
  "checks": {
    "common_commits_match_adam": true,
    "photometric_counts_match_adam": true,
    "recent_counts_match_committed_history": true,
    "whole_pool_growth_capacity": true,
    "full_available_pools": true,
    "paired_turns": true,
    "role_recent_counts": true,
    "native_window_only": true,
    "final_map_dense_used": true,
    "render_backward_matches": true,
    "render_service_matches": true,
    "no_render_errors": true,
    "exact_kf_credit": true,
    "prefix_budget_matches": true,
    "per_kf_budget": true
  }
}
```

**2026-09-25 (40 renders/KF / fixed / aria / vanilla):** execution=True, PSNR=20.751371936943695. Result=/home/intern/gs_floaterLab/results/campaigns/gain_attribution/render_budget40_feasibility/v1/fixed/aria/vanilla

```json
{
  "phase": "fixed",
  "dataset": "aria",
  "scene": "aria1253",
  "arm": "vanilla",
  "seed": 0,
  "output": "/home/intern/gs_floaterLab/results/campaigns/gain_attribution/render_budget40_feasibility/v1/fixed/aria/vanilla",
  "returncode": 0,
  "valid_execution": true,
  "evaluation": {
    "protocol": "saved_map_independent_double_evaluation_v1",
    "cooldown_seconds": 15,
    "input_sha256": {
      "ply": "53767f009efb9c5888da232ea195be66d08e5f2206078e8770d6a7fbbd3505b3",
      "full_trajectory": "6f6c3c2b9cfe586bc0031f399fad88e3dca9a439714433d1edd9036a753ce197",
      "kf_trajectory": "24b8cb2bcf2452ce8083bb96fb7c47b056f14a191ce7edd28462a4c0dc99bcdb",
      "mapped_uids": "da80e77eb37bf1c87b6ad0608cb34168f5973d8d6917967df46c9942832d9e3e",
      "fixed_manifest": "40df31333e5bddd13ba178c7246d7d8fb364a32886a1345ac0d5e9748572713f"
    },
    "checks": {
      "unchanged_inputs": true,
      "same_views": true,
      "same_gaussian_count": true,
      "same_fixed_view_count": true,
      "psnr_agrees": true,
      "ssim_agrees": true,
      "lpips_agrees": true
    },
    "max_abs_per_view_difference": {
      "psnr": 0.0,
      "ssim": 0.0,
      "lpips": 0.0
    },
    "fixed_psnr_first": 20.751371936943695,
    "fixed_psnr_second": 20.751371936943695,
    "pass": true
  },
  "evaluation_error": null,
  "psnr": 20.751371936943695,
  "source_changed": [],
  "mapping_seconds": 24.653538647922687,
  "renders": {
    "all": 4876,
    "no_grad": 116,
    "training": 4760,
    "backward": 4760
  },
  "checks": {
    "prefix_budget_matches": true,
    "training_render_matches_telemetry": true,
    "render_backward_matches": true,
    "no_render_errors": true,
    "all_renders_match": true,
    "optimizer_hooks_match": true,
    "heldout_disjoint": true,
    "finite_gaussians": true,
    "causal_render_uids": true,
    "zero_tail": true
  }
}
```

**2026-09-25 (40 renders/KF / fixed / rpng / paired):** execution=True, PSNR=24.833668686462953. Result=/home/intern/gs_floaterLab/results/campaigns/gain_attribution/render_budget40_feasibility/v1/fixed/rpng/paired

```json
{
  "phase": "fixed",
  "dataset": "rpng",
  "scene": "table_06",
  "arm": "paired",
  "seed": 0,
  "output": "/home/intern/gs_floaterLab/results/campaigns/gain_attribution/render_budget40_feasibility/v1/fixed/rpng/paired",
  "returncode": 0,
  "valid_execution": true,
  "evaluation": {
    "protocol": "saved_map_independent_double_evaluation_v1",
    "cooldown_seconds": 15,
    "input_sha256": {
      "ply": "24c91543d1ac040a0d813a5695525c57f56092a14efb43e4476065f5798babdb",
      "full_trajectory": "d3f29fceddbcd0a492e5877e7c354b8803433bcfdb32b67da2f1e951575e0437",
      "kf_trajectory": "e8495750161db009db339f4ed467b2ac9a569a2984df679acb4bbef6d1bda97a",
      "mapped_uids": "329f177c0b5a3e2ffaa6eb165adaa53cba1a2c0b17025d79661a636613025f39",
      "fixed_manifest": "dc75e1ce0c7a40611c0cf208091d1fc9c47b19127e2efcddd1c0ac8a952e406a"
    },
    "checks": {
      "unchanged_inputs": true,
      "same_views": true,
      "same_gaussian_count": true,
      "same_fixed_view_count": true,
      "psnr_agrees": true,
      "ssim_agrees": true,
      "lpips_agrees": true
    },
    "max_abs_per_view_difference": {
      "psnr": 0.0,
      "ssim": 0.0,
      "lpips": 0.0
    },
    "fixed_psnr_first": 24.833668686462953,
    "fixed_psnr_second": 24.833668686462953,
    "pass": true
  },
  "evaluation_error": null,
  "psnr": 24.833668686462953,
  "source_changed": [],
  "mapping_seconds": 123.0398855790263,
  "renders": {
    "all": 9303,
    "no_grad": 223,
    "training": 9080,
    "backward": 9080
  },
  "checks": {
    "common_commits_match_adam": true,
    "photometric_counts_match_adam": true,
    "recent_counts_match_committed_history": true,
    "whole_pool_growth_capacity": true,
    "full_available_pools": true,
    "paired_turns": true,
    "role_recent_counts": true,
    "native_window_only": true,
    "final_map_dense_used": true,
    "render_backward_matches": true,
    "render_service_matches": true,
    "no_render_errors": true,
    "exact_kf_credit": true,
    "prefix_budget_matches": true,
    "per_kf_budget": true
  }
}
```

**2026-09-25 (40 renders/KF / fixed / rpng / vanilla):** execution=True, PSNR=22.46096884925086. Result=/home/intern/gs_floaterLab/results/campaigns/gain_attribution/render_budget40_feasibility/v1/fixed/rpng/vanilla

```json
{
  "phase": "fixed",
  "dataset": "rpng",
  "scene": "table_06",
  "arm": "vanilla",
  "seed": 0,
  "output": "/home/intern/gs_floaterLab/results/campaigns/gain_attribution/render_budget40_feasibility/v1/fixed/rpng/vanilla",
  "returncode": 0,
  "valid_execution": true,
  "evaluation": {
    "protocol": "saved_map_independent_double_evaluation_v1",
    "cooldown_seconds": 15,
    "input_sha256": {
      "ply": "67db92c6a989016425ecb9cefe55febe500683b49104b8130719dfb5028fe2f0",
      "full_trajectory": "d3f29fceddbcd0a492e5877e7c354b8803433bcfdb32b67da2f1e951575e0437",
      "kf_trajectory": "e8495750161db009db339f4ed467b2ac9a569a2984df679acb4bbef6d1bda97a",
      "mapped_uids": "6d6f6f78d72e572f010582682dea5efa13c1b5a0312fd7ea48db4401ec9d5ebf",
      "fixed_manifest": "dc75e1ce0c7a40611c0cf208091d1fc9c47b19127e2efcddd1c0ac8a952e406a"
    },
    "checks": {
      "unchanged_inputs": true,
      "same_views": true,
      "same_gaussian_count": true,
      "same_fixed_view_count": true,
      "psnr_agrees": true,
      "ssim_agrees": true,
      "lpips_agrees": true
    },
    "max_abs_per_view_difference": {
      "psnr": 0.0,
      "ssim": 0.0,
      "lpips": 0.0
    },
    "fixed_psnr_first": 22.46096884925086,
    "fixed_psnr_second": 22.46096884925086,
    "pass": true
  },
  "evaluation_error": null,
  "psnr": 22.46096884925086,
  "source_changed": [],
  "mapping_seconds": 77.57612006901763,
  "renders": {
    "all": 9303,
    "no_grad": 223,
    "training": 9080,
    "backward": 9080
  },
  "checks": {
    "prefix_budget_matches": true,
    "training_render_matches_telemetry": true,
    "render_backward_matches": true,
    "no_render_errors": true,
    "all_renders_match": true,
    "optimizer_hooks_match": true,
    "heldout_disjoint": true,
    "finite_gaussians": true,
    "causal_render_uids": true,
    "zero_tail": true
  }
}
```

**2026-09-25 (40 renders/KF / fixed / utmm / paired):** execution=True, PSNR=21.417964429031183. Result=/home/intern/gs_floaterLab/results/campaigns/gain_attribution/render_budget40_feasibility/v1/fixed/utmm/paired

```json
{
  "phase": "fixed",
  "dataset": "utmm",
  "scene": "square-1",
  "arm": "paired",
  "seed": 0,
  "output": "/home/intern/gs_floaterLab/results/campaigns/gain_attribution/render_budget40_feasibility/v1/fixed/utmm/paired",
  "returncode": 0,
  "valid_execution": true,
  "evaluation": {
    "protocol": "saved_map_independent_double_evaluation_v1",
    "cooldown_seconds": 15,
    "input_sha256": {
      "ply": "877f850642ce0418823c156421b3161eead8a8d4d8dbcc6a91b44372f2dcd468",
      "full_trajectory": "2e5dda345db17cd26b29378f44248ef1ece9f67b84732f9a864d6ae4c1ceb140",
      "kf_trajectory": "10ed236e5429d0c7ef0fe77a77f92a8f25f6632ca4e1056619c1da47b2270ad7",
      "mapped_uids": "2044bd1c4b260fdd42a3004074e912c796cb93f6324e745119e8c0c1fbcc94de",
      "fixed_manifest": "6a54fdd3ccf272b762c4c4ebca13803f09e28efe4f43cbddf940cbb80dba8e26"
    },
    "checks": {
      "unchanged_inputs": true,
      "same_views": true,
      "same_gaussian_count": true,
      "same_fixed_view_count": true,
      "psnr_agrees": true,
      "ssim_agrees": true,
      "lpips_agrees": true
    },
    "max_abs_per_view_difference": {
      "psnr": 0.0,
      "ssim": 0.0,
      "lpips": 0.0
    },
    "fixed_psnr_first": 21.417964429031183,
    "fixed_psnr_second": 21.417964429031183,
    "pass": true
  },
  "evaluation_error": null,
  "psnr": 21.417964429031183,
  "source_changed": [],
  "mapping_seconds": 51.53679657494649,
  "renders": {
    "all": 3687,
    "no_grad": 87,
    "training": 3600,
    "backward": 3600
  },
  "checks": {
    "common_commits_match_adam": true,
    "photometric_counts_match_adam": true,
    "recent_counts_match_committed_history": true,
    "whole_pool_growth_capacity": true,
    "full_available_pools": true,
    "paired_turns": true,
    "role_recent_counts": true,
    "native_window_only": true,
    "final_map_dense_used": true,
    "render_backward_matches": true,
    "render_service_matches": true,
    "no_render_errors": true,
    "exact_kf_credit": true,
    "prefix_budget_matches": true,
    "per_kf_budget": true
  }
}
```

**2026-09-25 (40 renders/KF / fixed / utmm / vanilla):** execution=True, PSNR=18.824628406100803. Result=/home/intern/gs_floaterLab/results/campaigns/gain_attribution/render_budget40_feasibility/v1/fixed/utmm/vanilla

```json
{
  "phase": "fixed",
  "dataset": "utmm",
  "scene": "square-1",
  "arm": "vanilla",
  "seed": 0,
  "output": "/home/intern/gs_floaterLab/results/campaigns/gain_attribution/render_budget40_feasibility/v1/fixed/utmm/vanilla",
  "returncode": 0,
  "valid_execution": true,
  "evaluation": {
    "protocol": "saved_map_independent_double_evaluation_v1",
    "cooldown_seconds": 15,
    "input_sha256": {
      "ply": "4f6ab9000acd6d0cddc2afc84c4ccac08c99ebf7b8970bc8ee7b8c9844c31d8c",
      "full_trajectory": "2e5dda345db17cd26b29378f44248ef1ece9f67b84732f9a864d6ae4c1ceb140",
      "kf_trajectory": "10ed236e5429d0c7ef0fe77a77f92a8f25f6632ca4e1056619c1da47b2270ad7",
      "mapped_uids": "c325d740f4ec137acfc0ab2d52ebace4c47ea5d224d73fa3642429c07eb427fa",
      "fixed_manifest": "6a54fdd3ccf272b762c4c4ebca13803f09e28efe4f43cbddf940cbb80dba8e26"
    },
    "checks": {
      "unchanged_inputs": true,
      "same_views": true,
      "same_gaussian_count": true,
      "same_fixed_view_count": true,
      "psnr_agrees": true,
      "ssim_agrees": true,
      "lpips_agrees": true
    },
    "max_abs_per_view_difference": {
      "psnr": 0.0,
      "ssim": 0.0,
      "lpips": 0.0
    },
    "fixed_psnr_first": 18.824628406100803,
    "fixed_psnr_second": 18.824628406100803,
    "pass": true
  },
  "evaluation_error": null,
  "psnr": 18.824628406100803,
  "source_changed": [],
  "mapping_seconds": 34.175370769924484,
  "renders": {
    "all": 3687,
    "no_grad": 87,
    "training": 3600,
    "backward": 3600
  },
  "checks": {
    "prefix_budget_matches": true,
    "training_render_matches_telemetry": true,
    "render_backward_matches": true,
    "no_render_errors": true,
    "all_renders_match": true,
    "optimizer_hooks_match": true,
    "heldout_disjoint": true,
    "finite_gaussians": true,
    "causal_render_uids": true,
    "zero_tail": true
  }
}
```

**2026-09-25 (40 renders/KF / live / aria / vanilla):** execution=True, PSNR=19.935029801521594. Result=/home/intern/gs_floaterLab/results/campaigns/gain_attribution/render_budget40_feasibility/v1/live/aria/vanilla

```json
{
  "phase": "live",
  "dataset": "aria",
  "scene": "aria1253",
  "arm": "vanilla",
  "seed": 0,
  "output": "/home/intern/gs_floaterLab/results/campaigns/gain_attribution/render_budget40_feasibility/v1/live/aria/vanilla",
  "returncode": 0,
  "valid_execution": true,
  "evaluation": {
    "protocol": "saved_map_independent_double_evaluation_v1",
    "cooldown_seconds": 15,
    "input_sha256": {
      "ply": "7d2ece22eab960b887bd38cab14977ea689079e9da3c575259f78410094e98b1",
      "full_trajectory": "b2bdf0847cba585ed5407d3b64de6c376fda2c17d66def38f3f3af4935a5feb6",
      "kf_trajectory": "24b482990bbee9330d1064b8d30c57c137887554191de3553d1d8e0b1bf46563",
      "mapped_uids": "b3d16512ca142ceff80699c1fb7c0eb69d5da1ed635ebf05214425e094013479",
      "fixed_manifest": "40df31333e5bddd13ba178c7246d7d8fb364a32886a1345ac0d5e9748572713f"
    },
    "checks": {
      "unchanged_inputs": true,
      "same_views": true,
      "same_gaussian_count": true,
      "same_fixed_view_count": true,
      "psnr_agrees": true,
      "ssim_agrees": true,
      "lpips_agrees": true
    },
    "max_abs_per_view_difference": {
      "psnr": 0.0,
      "ssim": 0.0,
      "lpips": 0.0
    },
    "fixed_psnr_first": 19.935029801521594,
    "fixed_psnr_second": 19.935029801521594,
    "pass": true
  },
  "evaluation_error": null,
  "psnr": 19.935029801521594,
  "source_changed": [],
  "runtime": {
    "dataset": "aria",
    "scene": "aria1253",
    "arm": "official_vanilla_budgeted",
    "gpu": "NVIDIA GeForce RTX 5090",
    "image_size_hw": [
      464,
      464
    ],
    "duration_seconds": 65.09999891300004,
    "tracking_elapsed_seconds": 65.75809661694802,
    "model_load_seconds": 0.9649281399324536,
    "input_frames": 1303,
    "tracked_frames": 1303,
    "training_renders": 4159,
    "backward_renders": 4159,
    "committed_renders": 4146,
    "kf_admissions": 104,
    "unique_mapper_kfs": 90,
    "renders_per_kf_admission": 39.86538461538461,
    "frontend_iterations": [
      4,
      2
    ],
    "IMU_poseinit_after": 20,
    "tracking_kfs_final": 115,
    "renders_per_kf_cap": 40,
    "start_lag_ms": {
      "50": 4.10125101916492,
      "95": 2169.8401549714613,
      "99": 2560.2327149477787,
      "100": 2676.628215936944
    },
    "end_lag_ms": {
      "50": 54.16586098726839,
      "95": 2219.836324558127,
      "99": 2610.2321498002857,
      "100": 2726.603077026084
    },
    "track_call_ms": {
      "50": 10.958197060972452,
      "95": 132.0060027996078,
      "99": 251.43153891898694,
      "100": 1816.837582970038
    },
    "mapper_queue_max": 2,
    "zero_tail_observed": true,
    "error": null,
    "worker_errors": [],
    "quality_evaluated": false,
    "source_unchanged": true,
    "official_commit": "22ffe24c6df81d0bf63bd20057565c00c51d2996"
  }
}
```

**2026-09-25 (40 renders/KF / live / aria / paired):** execution=True, PSNR=19.30309359717915. Result=/home/intern/gs_floaterLab/results/campaigns/gain_attribution/render_budget40_feasibility/v1/live/aria/paired

```json
{
  "phase": "live",
  "dataset": "aria",
  "scene": "aria1253",
  "arm": "paired",
  "seed": 0,
  "output": "/home/intern/gs_floaterLab/results/campaigns/gain_attribution/render_budget40_feasibility/v1/live/aria/paired",
  "returncode": 0,
  "valid_execution": true,
  "evaluation": {
    "protocol": "saved_map_independent_double_evaluation_v1",
    "cooldown_seconds": 15,
    "input_sha256": {
      "ply": "2a4697526031048aec551ed4ff3a648d2a3815b48d6b013f94cc9d2c0ebcdf8a",
      "full_trajectory": "61094bac967c323a272ebda6ea94080b35ca9bd021a77185ef1ddaa2c23689fb",
      "kf_trajectory": "8046a40a3915c8059766e97bbdd728a183eb29ad54f2582fcb5ef2b3d1540b2d",
      "mapped_uids": "d01a67f4aa6d3ae562c4dc95302a16d391f6340d2a6ff208a8eee62581cafe0d",
      "fixed_manifest": "40df31333e5bddd13ba178c7246d7d8fb364a32886a1345ac0d5e9748572713f"
    },
    "checks": {
      "unchanged_inputs": true,
      "same_views": true,
      "same_gaussian_count": true,
      "same_fixed_view_count": true,
      "psnr_agrees": true,
      "ssim_agrees": true,
      "lpips_agrees": true
    },
    "max_abs_per_view_difference": {
      "psnr": 0.0,
      "ssim": 0.0,
      "lpips": 0.0
    },
    "fixed_psnr_first": 19.30309359717915,
    "fixed_psnr_second": 19.30309359717915,
    "pass": true
  },
  "evaluation_error": null,
  "psnr": 19.30309359717915,
  "source_changed": [],
  "runtime": {
    "dataset": "aria",
    "scene": "aria1253",
    "gpu": "NVIDIA GeForce RTX 5090",
    "image_size_hw": [
      464,
      464
    ],
    "input_frames": 1303,
    "tracked_frames": 1303,
    "duration_seconds": 65.09999891300004,
    "tracking_elapsed_seconds": 66.91413634293713,
    "model_load_seconds": 1.044885347946547,
    "renders_per_kf_cap": 40,
    "frontend_iterations": [
      4,
      2
    ],
    "IMU_poseinit_after": 20,
    "training_renders": 1767,
    "backward_renders": 1767,
    "committed_renders": 1767,
    "native_committed_renders": 1067,
    "additional_committed_renders": 700,
    "kf_admissions": 102,
    "unique_mapper_kfs": 88,
    "renders_per_kf_admission": 17.323529411764707,
    "tracking_kfs_final": 115,
    "start_lag_ms": {
      "50": 34.287741989828646,
      "95": 2676.206695719154,
      "99": 3602.2529390174896,
      "100": 3735.5677490122616
    },
    "end_lag_ms": {
      "50": 85.2037409786135,
      "95": 2726.2025065254397,
      "99": 3652.2408143174835,
      "100": 3785.564000951126
    },
    "track_call_ms": {
      "50": 6.688706926070154,
      "95": 156.84484624071044,
      "99": 339.16490673087577,
      "100": 2380.8453519595787
    },
    "mapper_queue_max": 1,
    "peak_cuda_allocated_bytes": 5746797056,
    "worker": {
      "accepted": 100,
      "completed": 100,
      "cancelled": 0,
      "failed": 0,
      "unfinished_tasks": 0,
      "closed": true,
      "stopped_at": 985412.053655594,
      "productive_idle_calls": 700,
      "input_wait_seconds": 43.745512150460854,
      "error": null
    },
    "zero_tail_observed": true,
    "overruns": [],
    "error": null,
    "source_unchanged": true,
    "quality_evaluated": false
  }
}
```

**2026-09-25 (40 renders/KF / live / rpng / vanilla):** execution=True, PSNR=21.298174990404835. Result=/home/intern/gs_floaterLab/results/campaigns/gain_attribution/render_budget40_feasibility/v1/live/rpng/vanilla

```json
{
  "phase": "live",
  "dataset": "rpng",
  "scene": "table_06",
  "arm": "vanilla",
  "seed": 0,
  "output": "/home/intern/gs_floaterLab/results/campaigns/gain_attribution/render_budget40_feasibility/v1/live/rpng/vanilla",
  "returncode": 0,
  "valid_execution": true,
  "evaluation": {
    "protocol": "saved_map_independent_double_evaluation_v1",
    "cooldown_seconds": 15,
    "input_sha256": {
      "ply": "73734384120a68fdb00cb817e1da8e3a60a007abd257adf723c0b57f5e11f269",
      "full_trajectory": "3316159122784692b06b0df7238e5c79a30a23f57ff70ee1228795a97c88268b",
      "kf_trajectory": "e70718008cc0237b83ab83983b9098bdddcf9548b07741c1c93f6a0bff570e7a",
      "mapped_uids": "eabb71dcbe6708b27129b5fcc5a9ac9a3db0b0168f40b09b6b2005f8f003806f",
      "fixed_manifest": "dc75e1ce0c7a40611c0cf208091d1fc9c47b19127e2efcddd1c0ac8a952e406a"
    },
    "checks": {
      "unchanged_inputs": true,
      "same_views": true,
      "same_gaussian_count": true,
      "same_fixed_view_count": true,
      "psnr_agrees": true,
      "ssim_agrees": true,
      "lpips_agrees": true
    },
    "max_abs_per_view_difference": {
      "psnr": 0.0,
      "ssim": 0.0,
      "lpips": 0.0
    },
    "fixed_psnr_first": 21.298174990404835,
    "fixed_psnr_second": 21.298174990404835,
    "pass": true
  },
  "evaluation_error": null,
  "psnr": 21.298174990404835,
  "source_changed": [],
  "runtime": {
    "dataset": "rpng",
    "scene": "table_06",
    "arm": "official_vanilla_budgeted",
    "gpu": "NVIDIA GeForce RTX 5090",
    "image_size_hw": [
      344,
      616
    ],
    "duration_seconds": 92.24467062950134,
    "tracking_elapsed_seconds": 150.4881940750638,
    "model_load_seconds": 0.9609430999262258,
    "input_frames": 2767,
    "tracked_frames": 2767,
    "training_renders": 4560,
    "backward_renders": 4560,
    "committed_renders": 4560,
    "kf_admissions": 114,
    "unique_mapper_kfs": 86,
    "renders_per_kf_admission": 40.0,
    "frontend_iterations": [
      4,
      2
    ],
    "IMU_poseinit_after": 20,
    "tracking_kfs_final": 232,
    "renders_per_kf_cap": 40,
    "start_lag_ms": {
      "50": 47170.031474670395,
      "95": 60961.09868584899,
      "99": 61429.9262877414,
      "100": 61689.940138487145
    },
    "end_lag_ms": {
      "50": 47206.099188071676,
      "95": 60994.441467220895,
      "99": 61463.26693852199,
      "100": 61723.282432882115
    },
    "track_call_ms": {
      "50": 11.313630966469646,
      "95": 213.07707518571974,
      "99": 750.242014129183,
      "100": 1991.9022029498592
    },
    "mapper_queue_max": 2,
    "zero_tail_observed": true,
    "error": null,
    "worker_errors": [],
    "quality_evaluated": false,
    "source_unchanged": true,
    "official_commit": "22ffe24c6df81d0bf63bd20057565c00c51d2996"
  }
}
```

**2026-09-25 (40 renders/KF / live / rpng / paired):** execution=True, PSNR=17.819775564176542. Result=/home/intern/gs_floaterLab/results/campaigns/gain_attribution/render_budget40_feasibility/v1/live/rpng/paired

```json
{
  "phase": "live",
  "dataset": "rpng",
  "scene": "table_06",
  "arm": "paired",
  "seed": 0,
  "output": "/home/intern/gs_floaterLab/results/campaigns/gain_attribution/render_budget40_feasibility/v1/live/rpng/paired",
  "returncode": 0,
  "valid_execution": true,
  "evaluation": {
    "protocol": "saved_map_independent_double_evaluation_v1",
    "cooldown_seconds": 15,
    "input_sha256": {
      "ply": "b7a86b669df9b19ef1d1c865c7b1aad4267d92c2a33b82fb0e803c85927a89d5",
      "full_trajectory": "f853623385aac72c96ce4cc202d23fa3ad8bd6abc98f1455021ab616148cbc47",
      "kf_trajectory": "04887436c74b48ad9c2ba5aba0765e6126efc6b60541cc1b0b95dae16d784646",
      "mapped_uids": "6fca1966783a464287964881eeb0686f96ab97e4a96e4c3a2948e474fbbeb98a",
      "fixed_manifest": "dc75e1ce0c7a40611c0cf208091d1fc9c47b19127e2efcddd1c0ac8a952e406a"
    },
    "checks": {
      "unchanged_inputs": true,
      "same_views": true,
      "same_gaussian_count": true,
      "same_fixed_view_count": true,
      "psnr_agrees": true,
      "ssim_agrees": true,
      "lpips_agrees": true
    },
    "max_abs_per_view_difference": {
      "psnr": 0.0,
      "ssim": 0.0,
      "lpips": 0.0
    },
    "fixed_psnr_first": 17.819775564176542,
    "fixed_psnr_second": 17.819775564176542,
    "pass": true
  },
  "evaluation_error": null,
  "psnr": 17.819775564176542,
  "source_changed": [],
  "runtime": {
    "dataset": "rpng",
    "scene": "table_06",
    "gpu": "NVIDIA GeForce RTX 5090",
    "image_size_hw": [
      344,
      616
    ],
    "input_frames": 2767,
    "tracked_frames": 2767,
    "duration_seconds": 92.24467062950134,
    "tracking_elapsed_seconds": 112.11772404192016,
    "model_load_seconds": 1.0149704560171813,
    "renders_per_kf_cap": 40,
    "frontend_iterations": [
      4,
      2
    ],
    "IMU_poseinit_after": 20,
    "training_renders": 1859,
    "backward_renders": 1859,
    "committed_renders": 1859,
    "native_committed_renders": 1859,
    "additional_committed_renders": 0,
    "kf_admissions": 150,
    "unique_mapper_kfs": 138,
    "renders_per_kf_admission": 12.393333333333333,
    "tracking_kfs_final": 211,
    "start_lag_ms": {
      "50": 15143.62839073874,
      "95": 22288.56988082407,
      "99": 22624.007714192852,
      "100": 22846.837337245233
    },
    "end_lag_ms": {
      "50": 15178.38447948452,
      "95": 22321.91303233849,
      "99": 22657.353248996664,
      "100": 22880.17893442884
    },
    "track_call_ms": {
      "50": 10.874335072003305,
      "95": 140.71578272851175,
      "99": 519.1665620380272,
      "100": 2349.788840045221
    },
    "mapper_queue_max": 1,
    "peak_cuda_allocated_bytes": 6296088576,
    "worker": {
      "accepted": 172,
      "completed": 172,
      "cancelled": 0,
      "failed": 0,
      "unfinished_tasks": 0,
      "closed": true,
      "stopped_at": 985753.108837885,
      "productive_idle_calls": 0,
      "input_wait_seconds": 81.55583259044215,
      "error": null
    },
    "zero_tail_observed": true,
    "overruns": [],
    "error": null,
    "source_unchanged": true,
    "quality_evaluated": false
  }
}
```

**2026-09-25 (40 renders/KF / live / utmm / vanilla):** execution=True, PSNR=18.600026333773577. Result=/home/intern/gs_floaterLab/results/campaigns/gain_attribution/render_budget40_feasibility/v1/live/utmm/vanilla

```json
{
  "phase": "live",
  "dataset": "utmm",
  "scene": "square-1",
  "arm": "vanilla",
  "seed": 0,
  "output": "/home/intern/gs_floaterLab/results/campaigns/gain_attribution/render_budget40_feasibility/v1/live/utmm/vanilla",
  "returncode": 0,
  "valid_execution": true,
  "evaluation": {
    "protocol": "saved_map_independent_double_evaluation_v1",
    "cooldown_seconds": 15,
    "input_sha256": {
      "ply": "68c251e503e72fccc845824440a40486ced3d04ec841108bb2d739c48c0e5bcf",
      "full_trajectory": "fed3b226dd5e4e33865f74d19dd522324561be1630a3943deaf707bb964b35cf",
      "kf_trajectory": "b89739a0e2d502479a06f87b81e6a785b8e4b46522b5dcf3b18517379074925b",
      "mapped_uids": "8a873627a23e86f3550be5057a62a1acce7078ea215b645fa5c422cb44591b87",
      "fixed_manifest": "6a54fdd3ccf272b762c4c4ebca13803f09e28efe4f43cbddf940cbb80dba8e26"
    },
    "checks": {
      "unchanged_inputs": true,
      "same_views": true,
      "same_gaussian_count": true,
      "same_fixed_view_count": true,
      "psnr_agrees": true,
      "ssim_agrees": true,
      "lpips_agrees": true
    },
    "max_abs_per_view_difference": {
      "psnr": 0.0,
      "ssim": 0.0,
      "lpips": 0.0
    },
    "fixed_psnr_first": 18.600026333773577,
    "fixed_psnr_second": 18.600026333773577,
    "pass": true
  },
  "evaluation_error": null,
  "psnr": 18.600026333773577,
  "source_changed": [],
  "runtime": {
    "dataset": "utmm",
    "scene": "square-1",
    "arm": "official_vanilla_budgeted",
    "gpu": "NVIDIA GeForce RTX 5090",
    "image_size_hw": [
      328,
      648
    ],
    "duration_seconds": 53.80941700935364,
    "tracking_elapsed_seconds": 54.249028112972155,
    "model_load_seconds": 0.9713826889637858,
    "input_frames": 1614,
    "tracked_frames": 1614,
    "training_renders": 3173,
    "backward_renders": 3173,
    "committed_renders": 3160,
    "kf_admissions": 80,
    "unique_mapper_kfs": 70,
    "renders_per_kf_admission": 39.5,
    "frontend_iterations": [
      4,
      2
    ],
    "IMU_poseinit_after": 15,
    "tracking_kfs_final": 84,
    "renders_per_kf_cap": 40,
    "start_lag_ms": {
      "50": 608.6928570875898,
      "95": 2814.2986212857063,
      "99": 3239.1094820259605,
      "100": 3317.754479125142
    },
    "end_lag_ms": {
      "50": 642.467726371251,
      "95": 2847.599862940842,
      "99": 3272.790786200203,
      "100": 3351.016726344824
    },
    "track_call_ms": {
      "50": 15.413075918331742,
      "95": 113.15663201967249,
      "99": 153.78189458395335,
      "100": 1280.4261751007289
    },
    "mapper_queue_max": 2,
    "zero_tail_observed": true,
    "error": null,
    "worker_errors": [],
    "quality_evaluated": false,
    "source_unchanged": true,
    "official_commit": "22ffe24c6df81d0bf63bd20057565c00c51d2996"
  }
}
```

**2026-09-25 (40 renders/KF / live / utmm / paired):** execution=True, PSNR=11.446189042962628. Result=/home/intern/gs_floaterLab/results/campaigns/gain_attribution/render_budget40_feasibility/v1/live/utmm/paired

```json
{
  "phase": "live",
  "dataset": "utmm",
  "scene": "square-1",
  "arm": "paired",
  "seed": 0,
  "output": "/home/intern/gs_floaterLab/results/campaigns/gain_attribution/render_budget40_feasibility/v1/live/utmm/paired",
  "returncode": 0,
  "valid_execution": true,
  "evaluation": {
    "protocol": "saved_map_independent_double_evaluation_v1",
    "cooldown_seconds": 15,
    "input_sha256": {
      "ply": "e9e1021acb881dc98c6cb37038ce0b0b520f772b9a29d72ec9fca92a801ff7a4",
      "full_trajectory": "cc2a5bd63b36677696b7163d30c0055024b620c27c2ea051a7b99052c7516ebc",
      "kf_trajectory": "4c27300f3fae65d645849fa58eeecb3119f6584f126bec60a0795afbabb941d1",
      "mapped_uids": "2e463198f9b31d3815c92aa6e88794634d2991c61a894d722a26f400e39c8b1f",
      "fixed_manifest": "6a54fdd3ccf272b762c4c4ebca13803f09e28efe4f43cbddf940cbb80dba8e26"
    },
    "checks": {
      "unchanged_inputs": true,
      "same_views": true,
      "same_gaussian_count": true,
      "same_fixed_view_count": true,
      "psnr_agrees": true,
      "ssim_agrees": true,
      "lpips_agrees": true
    },
    "max_abs_per_view_difference": {
      "psnr": 0.0,
      "ssim": 0.0,
      "lpips": 0.0
    },
    "fixed_psnr_first": 11.446189042962628,
    "fixed_psnr_second": 11.446189042962628,
    "pass": true
  },
  "evaluation_error": null,
  "psnr": 11.446189042962628,
  "source_changed": [],
  "runtime": {
    "dataset": "utmm",
    "scene": "square-1",
    "gpu": "NVIDIA GeForce RTX 5090",
    "image_size_hw": [
      328,
      648
    ],
    "input_frames": 1614,
    "tracked_frames": 1614,
    "duration_seconds": 53.80941700935364,
    "tracking_elapsed_seconds": 54.18981908506248,
    "model_load_seconds": 1.0202500910963863,
    "renders_per_kf_cap": 40,
    "frontend_iterations": [
      4,
      2
    ],
    "IMU_poseinit_after": 15,
    "training_renders": 607,
    "backward_renders": 607,
    "committed_renders": 607,
    "native_committed_renders": 591,
    "additional_committed_renders": 16,
    "kf_admissions": 62,
    "unique_mapper_kfs": 51,
    "renders_per_kf_admission": 9.790322580645162,
    "tracking_kfs_final": 69,
    "start_lag_ms": {
      "50": 42.18261007918045,
      "95": 1095.9661857050376,
      "99": 1250.5382636946151,
      "100": 1461.6091321222484
    },
    "end_lag_ms": {
      "50": 75.95367729663849,
      "95": 1129.2510359897276,
      "99": 1283.8661906158077,
      "100": 1494.907793472521
    },
    "track_call_ms": {
      "50": 16.243033518549055,
      "95": 116.67182195233178,
      "99": 164.48058737558281,
      "100": 1161.7580320453271
    },
    "mapper_queue_max": 1,
    "peak_cuda_allocated_bytes": 4413346816,
    "worker": {
      "accepted": 57,
      "completed": 57,
      "cancelled": 0,
      "failed": 0,
      "unfinished_tasks": 0,
      "closed": true,
      "stopped_at": 985987.576021872,
      "productive_idle_calls": 16,
      "input_wait_seconds": 50.079730465775356,
      "error": null
    },
    "zero_tail_observed": true,
    "overruns": [],
    "error": null,
    "source_unchanged": true,
    "quality_evaluated": false
  }
}
```

## 최종 집계

**2026-09-25 — 40 renders/KF 공통 예산 검증 완료:** fixed-work 6회/live 6회 audit 및 저장 지도 평가2회 일치. 정확한40회 비교에서 우리−vanilla PSNR Aria +4.11/RPNG +2.37/UTMM +2.59dB; online40상한에서는 우리 실제17.32/12.39/9.79회(KF/dense 추가350/350,0/0,8/8)로 공통40회 실현 실패. Vanilla는39.87/40.00/39.50회, 처리65.76/150.49/54.25초(입력65.10/92.24/53.81초). RPNG 최종 tracker KF는 논문232/vanilla232/우리211로 과다 최종KF 근거 없음; mapping-off도111.477초. 40은 품질비교 후보이며 실시간 인증값 아님. 생산 mapper/논문/역할배분 변경 없음.

[검증 표와 해석](SUMMARY.md).
