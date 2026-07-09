# Round 2-3 — Gradient 분석 & Perturbation (완결, 2026-06-30)

exp08 checkpoint 기준. Round 1은 `round1_findings_summary.md`, 전체 루프 설계는 `diagnostic_loop_plan.md` 참조.

## Round 2 — Z-gradient 가설 검증 (P12 기각)

- result dir: `results/rounds/round2_grad_diag_z_axis_gradient_verification_20260630_132024`
- key figure: `results/diagnostic/round2_gradient_analysis.png`

**P12 원래 가설 (기각)**: Z gradient weakness (예측 0.094×X) → Z drift
**실측**: grad_z/grad_x = **1.41 (mean)**, range 0.77~2.39 → Z가 X보다 오히려 강함

**진짜 메커니즘 (확정)**:
SLAM 삼각화 실패 → 극단적 sparse point (|Z|max=907,582m) → 초기화 시 46,264개(14.3%)가 FOV 밖 → gradient=0 → opacity reset+pruning으로 97% 제거 → 1,440개 survivor가 |Z|=42m에 frozen.

Z-outlier 시계열:

```text
iter   500: 46,264 (14.3%), |Z|max = 907,582m   ← SLAM 삼각화 실패
iter  3500:  1,144,        |Z|max = 41.83m      ← opacity reset+pruning (-97%)
iter  7000:  1,440                               ← densification +296개
iter 15000:  1,442 (frozen)
```

**P04 확인**: 카메라가 X 방향으로 이동 → X가 true depth 축 → X gradient 상대적으로 약함.

## Round 3 — Perturbation Analysis (완결)

Surface Gaussian ±0.1m perturbation의 loss 민감도:

| 축 | 민감도 |
|---|---:|
| X | 0.053 (flattest — P04 확인) |
| Y | 0.056 |
| Z | 0.078 |

- Z-outlier floater perturbation 민감도: ~1e-6 (surface의 1/53) → **loss에 사실상 invisible**
- Z-outlier gradient = surface gradient의 27% (4x 약함, 0은 아님)

## 결론

- Pop1 floater는 gradient로 못 고침 (loss에 안 보임) → **초기화 전 필터링이 정답** → Round 5 (exp13)
- ambiguity @30k: 픽셀의 33.3%가 depth ambiguity 보유 → Pop2 문제로 연결
