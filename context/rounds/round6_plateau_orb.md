# Round 6 — Plateau Loss 구현 & ORB 검증 (완결, 2026-07-05)

## 구현

**파일**: `3dgs-custom/eval/plateau_loss.py`

- 전체 Gaussian에 loss가 감 (photometric loss는 visible Gaussian만 커버하는 한계 보완)
- Cyclic sampler: sample_size=8192, ceil(N/8192)회마다 전체 커버 보장
- YAML toggle: `configs/plateau_loss/*.yaml`
- pop2_zclip: iter 5000부터 Z≥2.0m Gaussian 매 1000 iter 제거
- 속도 비용: ~68 it/s → ~38 it/s (약 44% 감소)

**3가지 타입**:

| 타입 | 앵커 | 특징 |
|---|---|---|
| spherical | SLAM filtered 6,492 pts | tau = clip(0.6·h_j, 0.05, 0.60) |
| ellipsoidal | SLAM filtered 6,492 pts | kNN PCA 법선, tau_n tight / tau_t loose |
| monodepth | Metric3D 9,110 / DepthPro 7,338 pts | virtual anchors |

**앵커 필터링 (확정)**: Z-bound + obs≥3 + kNN isolation(k=5, 3×median) → 7,182 → 6,492 pts

## 수정한 버그 (재발 주의)

1. `gaussian_model.py:409` — `densify_and_prune` 후 `tmp_radii=None`일 때 Z-clip의 `prune_points`가 None 인덱싱 crash → None 체크 추가
2. `train.py` — plateau `post_backward`를 densification 블록 **이후**로 이동 (이전 위치면 radii 크기 불일치 → CUDA device-side assert)

## 실험 결과 (ORB init 656 frames, baseline 29.023)

| 실험 | 타입 | 앵커 | PSNR@7k | PSNR@30k | Δ |
|---|---|---|---:|---:|---:|
| exp_orb_baseline | 없음 | - | 25.324 | **29.023** | - |
| exp15 | spherical | ORB 6,492 | 24.901 | 27.908 | -1.10 |
| exp16 | ellipsoidal | ORB 6,492 | 25.072 | 28.924 | -0.10 |
| exp17 | ellipsoidal | Metric3D 9,110 | 24.528 | 27.668 | -1.35 |
| exp18 | ellipsoidal | DepthPro 7,338 | **25.386** | 28.934 | **-0.09** |

## 결론

1. 어떤 plateau 설정도 baseline을 못 이김 (최선 exp18도 -0.09dB)
2. **ellipsoidal >> spherical**: 동일 앵커에서 +1.0dB (spherical은 앵커 주변 과밀집 → low_opacity_ratio 32→63% 급증 → photometric이 투명화)
3. **앵커 품질 > 앵커 수**: DepthPro(7,338) ≈ ORB(6,492) >> Metric3D(9,110)
4. exp18은 PSNR@7k에서 baseline을 +0.06 초과 → 초기 floater 억제 효과는 있으나 후반 중립화
5. ORB 좌표계 Z-clip은 Pop2를 거의 못 잡음 (exp15에서 12개만 제거) → MPS 트랙에서 재설계 필요

→ 다음: MPS full 데이터에서 lambda/tau/schedule 변형 sweep = `round7_plateau_mps.md`
