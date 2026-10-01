# T5 — Keyframes only vs + in-between frames

작성: 2026-10-01. 상태: **계획 작성 완료 / 최종 산출물 미제작**. ID는 논의용이며 최종 LaTeX 번호가 아니다.

## 목적

KF만 쓰는 경우와 중간 RGB 관측까지 쓰는 경우를 비교한다. 실제 VIGS mapper 결과를 우선 검토하고 기존 3dgs-custom replay도 별도 근거로 보존한다.

## 만들 구성

- 본 표: Dataset | Supervision | PSNR ↑ | SSIM ↑ | LPIPS ↓ | #G. 행은 KF-only / + in-between frames.
- 예산이 여러 개면 15/40 render VIGS panel과 60/120 update historical replay panel을 분리한다.
- VIGS에서 dense slot을 KF RGB-only로 바꾼 대조군은 same RGB loss를 유지한 비교로 사용한다. 필요하면 KF native loss 행을 보조 panel로 둔다.
- 기존 replay는 `causal_rr` 공통으로 KF eligibility만 제한/해제한 paired 실험이다.
- 성능이 높은 구현을 채택하더라도 양쪽 arm을 같은 구현으로 함께 비교하고 최종 시스템과의 대응을 우선한다.

## 비교 조건과 해석

절대 PSNR이 높은 서로 다른 코드/scene/budget 결과끼리 이어 붙이지 않는다. 특정 scene마다 유리한 구현을 바꾸지 않는다. historical 60/120 비교는 LR horizon과 densification 일정도 바뀌므로 예산만의 인과효과로 단정하지 않는다. 현재 dense↔KF RGB-only 대조에서도 quota 재분배 때문에 RGB-only 횟수/LR 위치가 일부 다르므로 그 제한을 공개한다.

[공통 프로토콜](../../../plan/visual_assets/protocol.md) · [원본 확인 기록](../../../plan/visual_assets/source_audit.md) · [방법 후보](../../../plan/visual_assets/baseline_registry.md)

## 확인한 원본과 관련 자료

- [README.md](../../../../context/experiments/ERCB_ablation/dense-supervision/README.md)
- [prepare_manifest.py](../../../../context/experiments/ERCB_ablation/dense-supervision/prepare_manifest.py)
- [ablation_dense_supervision_20260918.csv](../../../results/tables/ablation_dense_supervision_20260918.csv)
- [SUMMARY.md](../../../../context/experiments/campaigns/06_gain_attribution/kf_rgb_control/SUMMARY.md)
- [SUMMARY15.md](../../../../context/experiments/campaigns/06_gain_attribution/unified_rr_ervs/SUMMARY15.md)

## 다음 제작 작업

동일 cohort에서 VIGS 통제 대조와 과거 replay를 먼저 나란히 감사하고 사용할 panel을 정한다. 60에서는 RPNG 평균이 음수였다는 결과도 남긴다. 단순 더 큰 gain을 기준으로 코드/예산을 사후 교체하지 않는다.

## 산출물 및 완료 기준

- 데이터 출처: run ID, code/config hash, scene/evaluation IDs, checkpoint, budget unit을 provenance에 보존한다.
- Figure: scripts → output 검토본 → PDF 재렌더 확인 → current의 PDF/SVG/PNG/caption/provenance.
- Table: raw metric 참조 → 경량 집계 데이터 → output의 TeX/preview → 수치·단위·평균 확인 → current.
- 값이 없는 칸은 —(미측정), 실패 F, 적용 불가 NA, 목표 미도달 NR로 구별한다.
- 이번 단계는 MD 계획만 작성한다. GPU 실험·논문 TeX 삽입·휴먼테크 원본 교체는 수행하지 않았다.

## 값 미삽입 표 틀

| Dataset | Code / Budget | Supervision | PSNR ↑ | SSIM ↑ | LPIPS ↓ | #G |
|---|---|---|---|---|---|---|
| — | — | Keyframes only | — | — | — | — |
| — | 동일 비교 조건 | + in-between frames | — | — | — | — |
