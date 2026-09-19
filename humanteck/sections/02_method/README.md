# 2. Method 요약 및 그림

현재 단계: **선행 그림 조사 → 우리 pipeline 구상 → imagegen 초안 → 사용자 검토 → 본문 압축**.

## 작업 파일

- [우측 view 후보 12개](figures/production/candidates/01_view_candidates.png), [후보별 RGB·depth·normal](figures/production/candidates/02_modalities_all.png), [실제 궤적 시안](figures/production/candidates/03_trajectory_options.png)
- [실제 pose 표현·후보 비교·폴더 정리 결정](plan/09_real_pose_and_view_candidates_2026-09-19.md)

- [현재 overview: v12 구도 + 실제 Aria 1253 자산](figures/production/README.md), [승인 디자인 비교판](figures/production/qa/v12_vs_vector_comparison.png)
- [v12 기준 재제작·검수 계획](plan/08_v12_faithful_redesign_2026-09-19.md)

- [2절 한국어 문구 계획 — Carve 기준, 결과 그림·캡션 포함](writingplan/01_korean_methodology_wording_2026-09-19.md)
- [그림 비교와 수상자 팁](plan/01_pipeline_reference_review_2026-09-19.md)
- [그림 설계 및 문단 대응](plan/02_overall_pipeline_design_2026-09-19.md)
- [v01 생성 프롬프트](figures/plan/overall_pipeline_v01_prompt.md)
- [기능별 구조 재설계](plan/03_pipeline_functional_redesign_2026-09-19.md)
- [세부 표현을 위한 7개 논문 도판 조사](plan/04_detail_visualization_literature_2026-09-19.md)
- [새 loss의 작용을 보여주는 도판 조사·재설계안](plan/05_loss_visualization_study_2026-09-19.md)
- [LaTeX용 벡터 도판 제작·실데이터 교체 계획](plan/06_publication_figure_production_2026-09-19.md)
- [수상작 글꼴 기준 및 벡터 제작 실행 계획](plan/07_vector_overview_execution_2026-09-19.md)
- [벡터 제작 작업 폴더: 코드·layout proof·실제 RGB 후보](figures/production/README.md)
- [현재 frontend depth·normal 시안 v12](figures/plan/overall_pipeline_v12.png), [loss 배치 시안 v09](figures/plan/overall_pipeline_v09.png), [그림 이력·캡션](figures/README.md), [v11–v12 검수 기록](figures/plan/overall_pipeline_v12_qa_2026-09-19.md)

## 유지할 내용

문구 계획과 본문 초안은 `writingplan/`에서 업데이트한다. 그림 조사·설계·제작 계획은 `plan/`에서 관리한다.

1. 시스템 기반: online frontend의 pose·depth와 Gaussian 초기화.
2. Optimization-Guided View Growth: 완료된 update에 맞춰 학습 영상 집합을 확대.
3. Entropy-Regularized View Sampling: 누적 선택 횟수와 무작위성을 고려한 학습 배분.
4. Causal Ray-Space Geometry Supervision: 가용 depth evidence로 ray상의 opacity를 제약.

2와 3은 **어떤 관측으로 학습하는가**, 4는 **어떤 기하를 유도하는가**에 작용한다. 세 기여를 단순 직렬 파이프라인으로 그리지 않는다. 초기화는 기여가 아니라 시스템 기반이다.

수상자 팁에 따라 그림의 (a)–(c)와 본문 설명을 대응시킨다. 결과를 이 절 끝에 2–3문장과 실제 비교 그림으로 포함할지는 지면을 보며 결정한다. 아직 Method 영문 본문이나 Overleaf 파일을 수정하지 않았다.
