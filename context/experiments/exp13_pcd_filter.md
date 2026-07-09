# exp13 — Camera-bound PCD Filter (Pop1 해결)

- 날짜: 2026-06-30
- result dir: `results/experiments/exp13_pcd_filter_full30k_20260630_140634`
- 데이터: MPS init 1311장 full, 30k iter
- 관련 라운드: `rounds/round5_findings_summary.md`

## 목적

SLAM 삼각화 실패로 생긴 극단적 init outlier(Pop1)를 초기화 전에 제거하면 Z-outlier floater가 사라지는지 검증.

## 설정 (exp08 대비 diff)

- `scene/dataset_readers.py`에 `_filter_pcd_by_camera_bound()` 추가
- 카메라 center `C = -R @ T` (버그 수정: 이전 `-R.T @ T`)
- Z bound [-3.05, +3.03]m → 46,276 pts 제거 (7.38%)

## 결과

| Metric | exp08 | exp13 | Δ |
|---|---:|---:|---:|
| Z-outlier @500 | 46,264 | 507 | -99% |
| Z-outlier @30k | 1,474 | 385 | -74% |
| \|Z\|max @30k | 42.71m | 4.85m | -89% |
| PSNR@30k | 33.012 | 32.855 | -0.16 dB |
| Ambiguity ratio | 33.3% | 35.0% | +1.7pp (악화) |

## Verdict

**채택 (Pop1 한정)** — PSNR -0.16dB 비용으로 Pop1 완전 해결. 그러나 ambiguity는 오히려 악화 → Pop2(densification floater, |Z|=3-6m)는 별도 intervention 필요. 이 실험으로 "floater는 두 집단" 프레임 확정.

핵심 figure: `results/diagnostic/exp13_final_comparison.png`, `results/diagnostic/round5b_intervention_results.png`
