# F9 — RR vs ERCB/ERVS 수렴 ablation

작성: 2026-10-01. 상태: **계획 작성 완료 / 최종 산출물 미제작**. ID는 논의용이며 최종 LaTeX 번호가 아니다.

## 목적

사용자 피드백을 반영해 선택 횟수 heatmap 대신 sampling 정책의 수렴 곡선을 주된 그림으로 만든다.

## 만들 구성

- 15 / 30 / 60 updates per KF interval을 별도 패널로 하고, RR와 ERCB 두 곡선을 그린다.
- x: 각 run에서 완료한 optimizer updates, y: 고정 held-out PSNR. T4와 같은 원본 실험을 쓴다.
- scene 길이가 다른 절대 step 곡선을 무작정 평균하지 않고 대표 scene small multiples를 사용한다.
- 전체 scene endpoint 평균은 T4에 두고, 전체 곡선은 appendix 제작 후보로 보존한다.
- 현재 VIGS ERVS 15/40 비교를 추가하면 별도 패널/그림으로 구분한다. 30 결과를 만들어 채우지 않는다.

## 비교 조건과 해석

benchmark-B fixed-topology 결과와 paper-figures densify-on 곡선을 섞지 않는다. interval ERCB와 현재 per-view ERVS를 같은 코드로 표기하지 않는다. 기존 endpoint만 있으면 신규 checkpoint 수집 전에는 수렴 곡선 완성으로 표시하지 않는다. 숫자가 큰 regime로 arm을 각각 갈아끼우지 않는다.

[공통 프로토콜](../../../plan/visual_assets/protocol.md) · [원본 확인 기록](../../../plan/visual_assets/source_audit.md) · [방법 후보](../../../plan/visual_assets/baseline_registry.md)

## 확인한 원본과 관련 자료

- [prepare_manifest.py](../../../../context/experiments/ERCB_ablation/benchmark-B/prepare_manifest.py)
- [summary.md](../../../../context/experiments/ERCB_ablation/benchmark-B/summary.md)
- [prepare_view_ordering.py](../../../../context/experiments/ERCB_ablation/paper-figures/prepare_view_ordering.py)
- [manifest_view_ordering.json](../../../../context/experiments/ERCB_ablation/paper-figures/evidence/manifest_view_ordering.json)
- [SUMMARY15.md](../../../../context/experiments/campaigns/06_gain_attribution/unified_rr_ervs/SUMMARY15.md)

## 다음 제작 작업

T4 source audit를 공유한다. densify-on manifest는 114/114 완료 기록이 있지만 원본 curve 파일 접근 및 checkpoint 평가를 확인한 뒤 plot한다.

## 산출물 및 완료 기준

- 데이터 출처: run ID, code/config hash, scene/evaluation IDs, checkpoint, budget unit을 provenance에 보존한다.
- Figure: scripts → output 검토본 → PDF 재렌더 확인 → current의 PDF/SVG/PNG/caption/provenance.
- Table: raw metric 참조 → 경량 집계 데이터 → output의 TeX/preview → 수치·단위·평균 확인 → current.
- 값이 없는 칸은 —(미측정), 실패 F, 적용 불가 NA, 목표 미도달 NR로 구별한다.
- 이번 단계는 MD 계획만 작성한다. GPU 실험·논문 TeX 삽입·휴먼테크 원본 교체는 수행하지 않았다.
