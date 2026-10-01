# F1 — Teaser

작성: 2026-10-01. 상태: **계획 작성 완료 / 최종 산출물 미제작**. ID는 논의용이며 최종 LaTeX 번호가 아니다.

## 목적

같은 제한된 예산에서 appearance가 빠르게 개선되고 잘못된 free-space 구조가 줄어드는 모습을 첫 페이지에서 전달한다.

## 만들 구성

- 대표 scene 하나의 VIGS-SLAM / Ours / GT RGB와 동일 ROI 확대를 배치한다.
- 두 시점의 작은 비교 또는 동일 시간 비교를 사용한다. 아래에 geometry 단면을 붙일 수 있다.
- 사진마다 elapsed seconds 또는 training renders를 명시한다. F3/F6의 확정 자산을 재사용한다.
- 제목 문구는 Fast appearance refinement / Reliable geometry 정도로 짧게 두되, 실제 검증한 효과만 표시한다.

## 비교 조건과 해석

RGB 비교와 기하 off/on ablation은 비교 대상이 다르므로 패널별로 명시한다. 기하 항이 확정되지 않으면 geometry 패널은 미완성으로 남긴다. 지도 cutaway를 Carve의 개선 증거로 사용하지 않는다. GT와 모든 방법에 같은 crop과 색상 처리를 적용한다.

[공통 프로토콜](../../../plan/visual_assets/protocol.md) · [원본 확인 기록](../../../plan/visual_assets/source_audit.md) · [방법 후보](../../../plan/visual_assets/baseline_registry.md)

## 확인한 원본과 관련 자료

- [README.md](../../../../humanteck/sections/02_method/figure02/README.md)
- [README.md](../../../../humanteck/sections/02_method/figure01/production/README.md)
- [SUMMARY.md](../../../../context/experiments/campaigns/06_gain_attribution/geometry_main_validation/SUMMARY.md)

## 다음 제작 작업

최종 recipe를 고정한 뒤 F3/F5/F6에서 대표 자산을 선택한다. 숫자·이미지를 생성해서 결과처럼 채우지 않는다.

## 산출물 및 완료 기준

- 데이터 출처: run ID, code/config hash, scene/evaluation IDs, checkpoint, budget unit을 provenance에 보존한다.
- Figure: scripts → output 검토본 → PDF 재렌더 확인 → current의 PDF/SVG/PNG/caption/provenance.
- Table: raw metric 참조 → 경량 집계 데이터 → output의 TeX/preview → 수치·단위·평균 확인 → current.
- 값이 없는 칸은 —(미측정), 실패 F, 적용 불가 NA, 목표 미도달 NR로 구별한다.
- 이번 단계는 MD 계획만 작성한다. GPU 실험·논문 TeX 삽입·휴먼테크 원본 교체는 수행하지 않았다.
