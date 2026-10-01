# F2 — System overview: 휴먼테크 재사용

작성: 2026-10-01. 상태: **계획 작성 완료 / 최종 산출물 미제작**. ID는 논의용이며 최종 LaTeX 번호가 아니다.

## 목적

휴먼테크 overview의 레이아웃과 기존 SVG를 바탕으로 CVPR 방법 설명과 연결한다.

## 만들 구성

- 원본은 `humanteck/sections/02_method/figure01/production/current/overview.svg` 및 동일 이름 PDF/PNG.
- RGB+IMU → frontend → Gaussian initialization/growth → view selection → map optimization 흐름을 유지한다.
- 사용자 선택에 따라 새로 디자인하지 않고 기존 색상·패널·Rendered normal 표기를 재사용한다.
- 최신 구조와 다른 설명만 교정 후보로 적는다: 최근 KF / 전체 KF / dense 역할, growth credit 단위, geometry gradient 경로.
- FIFO를 넣는 경우 입력 대기열과 학습 full-history pool을 별도 요소로 표시한다. 모든 구현 세부를 억지로 추가하지 않는다.

## 비교 조건과 해석

기존 overview의 map은 Carve off run에서 가져온 설명용 cutaway이며 count·확률·ray는 도식이다. 현재 D3를 사용한 결과에 Carve label을 그대로 붙이지 않는다. Ours 정의 확정 후 필요한 최소 라벨만 수정하며 휴먼테크 원본은 보존한다.

[공통 프로토콜](../../../plan/visual_assets/protocol.md) · [원본 확인 기록](../../../plan/visual_assets/source_audit.md) · [방법 후보](../../../plan/visual_assets/baseline_registry.md)

## 확인한 원본과 관련 자료

- [README.md](../../../../humanteck/sections/02_method/figure01/production/README.md)
- [overview.svg](../../../../humanteck/sections/02_method/figure01/production/current/overview.svg)
- [4_method.tex](../../../latex/sec/4_method.tex)
- [HANDOFF.md](../../../../context/experiments/campaigns/06_gain_attribution/selected_recipe/HANDOFF.md)

## 다음 제작 작업

기존 SVG를 제작 시작점으로 지정했다. 실제 복사·라벨 수정·PDF 검수는 제작 단계에서 수행한다.

## 산출물 및 완료 기준

- 데이터 출처: run ID, code/config hash, scene/evaluation IDs, checkpoint, budget unit을 provenance에 보존한다.
- Figure: scripts → output 검토본 → PDF 재렌더 확인 → current의 PDF/SVG/PNG/caption/provenance.
- Table: raw metric 참조 → 경량 집계 데이터 → output의 TeX/preview → 수치·단위·평균 확인 → current.
- 값이 없는 칸은 —(미측정), 실패 F, 적용 불가 NA, 목표 미도달 NR로 구별한다.
- 이번 단계는 MD 계획만 작성한다. GPU 실험·논문 TeX 삽입·휴먼테크 원본 교체는 수행하지 않았다.
