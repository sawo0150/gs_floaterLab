# ERVS group size K on B (2026-10-02)

Status: **EVIDENCE — complete, 12 runs**, seed 0, tuning scenes only (aria1253rot, square-1).

[PREREG](PREREG.md) (committed `bac458f` before any run). Patch `benchmarks/online_gs/campaigns/gain_attribution/group_k_patch.py`
keeps one ERVS group queue per pool (keyframe, dense) across batches and packets; every run passed the gate (groups > 0
in both pools). K_batch = current B (group = one selection batch: keyframe 3, dense 6), reused from b_ablation_v2/pilot.
Raw: `results/campaigns/gain_attribution/ervs_group_k/v1/`.

## Results (held-out PSNR, dB)

| K | rot 15 | rot 25 | square-1 15 | square-1 25 | 4-cell mean | min-bin mean | worst-Q1 mean | SSIM | LPIPS |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| K_batch (current) | 23.812 | 24.532 | 20.765 | 21.370 | 22.620 | **21.589** | **19.793** | 0.7820 | **0.3088** |
| **K16** | 23.792 | **24.652** | **20.941** | **21.539** | **22.731** | 21.513 | 19.719 | **0.7855** | 0.3094 |
| K32 | **23.869** | 24.393 | 20.855 | 21.285 | 22.600 | 21.538 | 19.759 | 0.7821 | 0.3129 |
| K64 | 23.797 | 24.500 | 20.875 | 21.328 | 22.625 | 21.487 | 19.746 | 0.7823 | 0.3140 |

## Reading against the PREREG

- **Selected K = 16** (highest 4-cell mean, 22.731; next best is 0.105 dB lower). K16 − K_batch: −0.02 / +0.12 / +0.18 /
  +0.17 dB (3/4 cells higher; square-1 well above its 0.019 noise, rot within its 0.152 noise).
- Mean PSNR and SSIM favour K16, but min-bin PSNR and worst-Q1 are slightly lower than K_batch (−0.08 / −0.07 dB) and
  LPIPS is about equal. Larger K (32, 64) does not help.
- K16 is fixed for the next step (ERVS vs uniform on the held-out scenes aria1253, table_06), which needs a new approval.
