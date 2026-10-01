# T3 — Geometry 정량 비교

작성: 2026-10-01. 상태: **계획 작성 완료 / 최종 산출물 미제작**. ID는 논의용이며 최종 LaTeX 번호가 아니다.

## 목적

기하 항이 free-space 오류를 줄이면서 표면 coverage와 RGB 품질을 보존하는지 정량화한다.

## 만들 구성

- 행: VIGS-SLAM, Ours without proposed geometry, Ours with proposed geometry.
- 열: Dataset/Scene | Method | Accuracy ↓ | Completeness ↓ 또는 completeness ratio ↑ | F-score ↑ | Free-space violation ↓ | PSNR ↑ | #G.
- 단위, 거리 threshold, visibility mask, geometry 추출 방식을 caption과 evaluator 문서에 명시한다.
- 독립 3D reference가 없는 scene은 지원 지표만 사용하고 나머지는 NA로 둔다.
- F6의 정성 비교와 F7의 마지막 checkpoint가 이 표와 대응한다.

## 비교 조건과 해석

최종 Carve/Hit/D3를 혼용하지 않는다. 학습에 쓴 depth 자체를 유일한 GT로 삼지 않는다. 적게 남겨서 오류가 줄어드는 경우를 배제하려면 completeness/coverage를 함께 보고한다. loss 유무 외의 topology/init/sampling 조건을 고정한다.

[공통 프로토콜](../../../plan/visual_assets/protocol.md) · [원본 확인 기록](../../../plan/visual_assets/source_audit.md) · [방법 후보](../../../plan/visual_assets/baseline_registry.md)

## 확인한 원본과 관련 자료

- [4_method.tex](../../../latex/sec/4_method.tex)
- [SUMMARY.md](../../../../context/experiments/campaigns/06_gain_attribution/geometry_main_validation/SUMMARY.md)

## 다음 제작 작업

기하 담당자와 최종 목적함수·적용 gradient·독립 reference 경로를 맞춘 뒤 평가한다. 현재 PSNR 검증을 geometry 검증 완료로 표기하지 않는다.

## 산출물 및 완료 기준

- 데이터 출처: run ID, code/config hash, scene/evaluation IDs, checkpoint, budget unit을 provenance에 보존한다.
- Figure: scripts → output 검토본 → PDF 재렌더 확인 → current의 PDF/SVG/PNG/caption/provenance.
- Table: raw metric 참조 → 경량 집계 데이터 → output의 TeX/preview → 수치·단위·평균 확인 → current.
- 값이 없는 칸은 —(미측정), 실패 F, 적용 불가 NA, 목표 미도달 NR로 구별한다.
- 이번 단계는 MD 계획만 작성한다. GPU 실험·논문 TeX 삽입·휴먼테크 원본 교체는 수행하지 않았다.

## 값 미삽입 표 틀

| Dataset / Scene | Method | Accuracy ↓ | Completeness | F-score ↑ | Free-space error ↓ | PSNR ↑ | #G |
|---|---|---|---|---|---|---|---|
| — | VIGS-SLAM | — | — | — | — | — | — |
| — | Ours w/o geometry | — | — | — | — | — | — |
| — | Ours with geometry | — | — | — | — | — | — |
