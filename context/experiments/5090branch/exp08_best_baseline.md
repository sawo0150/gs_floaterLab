# exp08 — 현재 Best Baseline

- 날짜: 2026-06-16
- result dir: `results/experiments/exp08_openmavis_full_dens_until7000_prune001_beta1_low_20260616_124504`
- W&B run: `qd2nqxji` (project `geekseek/3dgs-keyframe`)
- 데이터: MPS init 1311장 full, 30k iter

## 설정 (default 대비 diff)

```text
--densification_interval 200
--densify_grad_threshold 0.0004
--densify_until_iter 7000
--scaling_lr 0.0025
--min_opacity_prune_threshold 0.01
--optimizer_beta1 0.85
```

## 결과

| 항목 | 값 |
|---|---:|
| PSNR@30k | **33.012** |
| Gaussian count | 323,864 |
| Low opacity ratio | 0.3902 |
| Large scale ratio | 0.0578 |
| Opacity median | 0.1522 |
| Scale median | 0.0265 |
| Ambiguity positive ratio | 33.3% |
| Z-outlier @30k | 1,474 (\|Z\|max 42.71m) |

## Verdict

**채택** — 이후 모든 full 30k 실험의 비교 기준. 단 Pop1(SLAM init outlier)과 Pop2(densification floater)는 미해결 상태의 baseline임 (`knowledge/floater_populations.md`).
