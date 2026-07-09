# exp27 / 27b / 27c — Anchor를 init point cloud로 (anchor 품질 검증)

- **날짜**: 2026-07-09
- **질문**: exp25가 쓴 plateau anchor(v4 depth_pro, 7,338 pts)는 충분히 좋은가? → init으로 직접 써서 검증
- **데이터**: MPS full 1311장 (exp08과 동일 images/poses), 하이퍼파라미터 exp08 동일, plateau 없음
- **스크립트**: `scripts/experiments/run_exp27_anchorinit.sh`, `run_exp27b_randominit_control.sh`, `run_exp27c_anchorinit_aligned.sh`
- **scene**: `results/datasets/mps_anchorinit_v4_depthpro_scene`, `mps_random7338_scene`, `mps_anchorinit_aligned_scene`

## 결과

| Run | init (모두 7,338 pts) | PSNR@7k | PSNR@30k | Gaussians@30k | \|Z\|>4m |
|---|---|---:|---:|---:|---:|
| exp08 (참조) | MPS semidense 626k | 28.35 | **33.012** | 323,864 | — |
| exp27 | anchor 미정렬 (Atlas world 그대로) | 25.54 | 29.540 | 97,702 | 1,788 |
| exp27b | MPS 랜덤 7,338 (개수 대조군) | 26.25 | 30.583 | 118,200 | 173 |
| **exp27c** | **anchor 정렬 (Atlas→MPS)** | 26.90 | **31.611** | 128,737 | **8** |

## 핵심 발견 1 — anchor는 MPS world가 아니었다 (좌표계 버그)

- anchor npy는 옛 SLAM run의 **raw Atlas world** (map_points.jsonl과 NN 0.000m 일치로 확인).
- MPS 학습 world 대비: 표면 NN median **0.476m**, p90 1.97m, **scale x0.950**.
- 정렬: keyframes.jsonl(57 KF) timestamp ↔ `closed_loop_trajectory.csv` 매칭 → Umeyama (rmse 2cm). 정렬 후 표면 NN median **0.021m**.
- 변환/정렬본 저장: `results/diagnostic/plateau_ellipsoid_v4_20260705_041132/{T_atlas_to_mps.npz, anchors_all_depth_pro_mpsaligned.npy, ALIGNMENT_NOTE.md}`

**→ exp19~26 (Round 7)은 전부 이 미정렬 anchor로 plateau를 돌렸다** (`eval/plateau_loss.py`는 anchor_path를 무변환 로드). Round 7 결과의 정합적 재해석:
- exp25(tau 확대)만 선방한 이유: plateau가 커져 어긋난 중심임에도 진짜 표면을 포함
- λ 강화(exp20/21/26) 악화: 틀린 위치로 강하게 견인
- exp23(adaptive prune) 붕괴: 틀린 plateau 밖 표면 Gaussian을 삭제

**Round 7의 "tau > λ" 등 설계 결론은 misalignment 조건에서 얻은 것 — 정렬 anchor로 재검증 필요.**

## 핵심 발견 2 — 정렬만 하면 anchor 품질은 합격

- exp27c(정렬 anchor) **31.61** > exp27b(같은 개수의 확실한 표면점 랜덤) **30.58**: +1.03dB.
  균등 커버리지(kNN isolation + voxel 시딩 + monodepth 보완)가 랜덤 표면점보다 init으로 우수.
- 정렬 효과 자체: exp27 → exp27c **+2.07dB**.
- exp08과의 잔여 격차 -1.40dB는 init 개수/최종 capacity 차이 (7.3k init → 129k Gaussian vs 626k init → 324k).
- floater 관점: exp27c는 |Z|>4m Gaussian **8개** (극도로 깨끗). init에 outlier가 없으면 densification도 크게 오염되지 않음을 시사.

## 한계

- PSNR은 train viewpoint 기준 (기존 exp들과 동일 조건 비교).
- exp27b 랜덤 추출에는 Pop1 outlier가 비율대로 포함됨 (626k의 outlier 비율만큼) — 그래도 |Z|>4m 173개에 그침.
- anchor 생성 시 depth 피팅은 confidence 필터 없이 전 SLAM 점 사용 (Huber로만 방어) — 개선 여지.
