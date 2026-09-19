# Overall pipeline 이미지 시안

**현재 작업본:** [v12 구도에 맞춘 실제 Aria 1253 벡터 그림](production/README.md), [원본 v12와 비교](production/qa/v12_vs_vector_comparison.png). 원본 생성 시안은 `plan/`으로 이동된 상태이며, 아래 기존 이력의 v01–v12 링크는 이 경로를 기준으로 확인한다. 이후 제작 스크립트는 새 파일 대신 diff로 수정한다.

**벡터 제작 시작:** 수상작 Times New Roman을 적용한 [production 작업 폴더](production/README.md)에 SVG source, PDF layout proof, 실제 RGB 후보 비교판을 저장했다. 아래 v01–v12는 생성형 구도 탐색 이력으로 보존한다.

참고한 원문 도판은 [reference_figures/](reference_figures/README.md)에 별도로 정리했다. Loss 도판 9개와 조사에 사용한 전체 페이지 18개를 보관하며, 아래 생성 시안과 구분한다.

현재 **frontend depth·normal 표시 검토본**: [overall_pipeline_v12.png](plan/overall_pipeline_v12.png). Online observations에 Keyframe depth와 Keyframe normal을 병렬 배치했고 v10의 sampling 분포를 유지했다. [v11–v12 QA](plan/overall_pipeline_v12_qa_2026-09-19.md)와 기존 QA의 연결선 문제가 남아 있어 제출본은 아니다. Overview reference는 DN-Splatter Fig. 1과 PGSR Fig. 4다.

**용도는 구조·배치 논의다. 제출용 최종 도판이나 실험 결과가 아니다.** 이미지와 Gaussian map은 생성된 설명용 표현이다. Overleaf에는 아직 삽입하지 않았다.

| 버전 | 목적 | 상태 |
| --- | --- | --- |
| [v01](plan/overall_pipeline_v01.png) | 처음 전체 배치 생성 | depth 경로·양방향 feedback·임의 확률 수치 문제로 참고 이력만 보존 |
| [v02](plan/overall_pipeline_v02.png) | 데이터 경로와 feedback, 확률 label 수정 | depth 선이 Growth 영역을 통과하는 모호성 잔존 |
| [v03](plan/overall_pipeline_v03.png) | depth 경로를 영역 밖으로 이동 | 이전 구도. Sampling 내부 작은 영문 오타 등 최종 정리 필요 |
| [v04](plan/overall_pipeline_v04.png) | 기능별 3영역, 공유 pool·지도 중심으로 새 구도 생성 | 라벨 박스 나열에서 시각 객체 중심으로 변경. 연결·외곽 노이즈 문제 |
| [v05](plan/overall_pipeline_v05.png) | 새 구도 유지, 외곽 정리와 데이터 경로 편집 | 현재 디자인 검토본. loss 연결과 일부 label·feedback은 추가 수정 필요 |
| [v06](plan/overall_pipeline_v06.png) | K/I 유지, 3→4→5 pool, count/probability, ray profile과 loss 합류 | 핵심 기여 표현을 구체화. 영상 identity와 feedback 연결은 미완성 |
| [v07](plan/overall_pipeline_v07.png) | v06 일관성 수정 시도 | 완료 update 점선은 개선. 일부 수정은 실패했고 Ray detail 오연결이 생겨 제출용 아님 |
| [v08](plan/overall_pipeline_v08.png) | Overview reference로 오른쪽 loss 표현 재설계 | 기본 loss 묶음과 opacity 억제 도식 반영; callout 및 prior 연결 미완성 |
| [v09](plan/overall_pipeline_v09.png) | v08의 오른쪽 경로 교정 | depth-derived normal 및 map→ray callout 추가; prior 경로와 선 교차는 추가 정리 필요 |
| [v10](plan/overall_pipeline_v10.png) | Count 12→0, 확률 10→33%의 admission-history 예시 | 분포와 annotation 반영; sampling/depth 연결선은 추가 교정 필요 |
| [v11](plan/overall_pipeline_v11.png) | Online frontend 아래 depth·normal 병렬 표시 | 두 thumbnail 추가; 출력선 source 불명확 |
| [v12](plan/overall_pipeline_v12.png) | frontend 주변 출력선 교정 시도 | normal 옆 잘못된 출력선 제거; fork 접합과 전체 source–destination은 미완성 |

- 생성 방식: 내장 imagegen. v01 새 생성과 v02–v03 편집, v04 새 생성과 v05 편집. CLI fallback 미사용.
- 크기: 각 1860 × 846 px.
- [최초 프롬프트](plan/overall_pipeline_v01_prompt.md), [v02 수정 프롬프트](plan/overall_pipeline_v02_prompt.md), [v03 수정 프롬프트](plan/overall_pipeline_v03_prompt.md)
- [기능별 재설계](../plan/03_pipeline_functional_redesign_2026-09-19.md), [v04 프롬프트](plan/overall_pipeline_v04_prompt.md), [v05 편집 프롬프트](plan/overall_pipeline_v05_prompt.md)
- [v04–v05 디자인 검수](plan/overall_pipeline_v05_qa_2026-09-19.md)
- [v06 프롬프트](plan/overall_pipeline_v06_prompt.md), [v07 편집 프롬프트](plan/overall_pipeline_v07_prompt.md), [v06–v07 검수](plan/overall_pipeline_v07_qa_2026-09-19.md)

v06–v07도 내장 imagegen으로 생성/편집했다. CLI fallback은 사용하지 않았다. 이미지 크기는 버전에 따라 다르며 v01–v05는 1860×846, v06–v07은 별도 원본 크기를 유지한다.
- [검수 및 남은 작업](plan/overall_pipeline_qa_2026-09-19.md)
- [v08 prompt](plan/overall_pipeline_v08_prompt.md), [v09 prompt](plan/overall_pipeline_v09_prompt.md), [v08–v09 검수](plan/overall_pipeline_v09_qa_2026-09-19.md)
- [v10 prompt·확률 근거](plan/overall_pipeline_v10_prompt.md), [v10 검수](plan/overall_pipeline_v10_qa_2026-09-19.md)
- [v11 prompt](plan/overall_pipeline_v11_prompt.md), [v12 prompt](plan/overall_pipeline_v12_prompt.md), [v11–v12 검수](plan/overall_pipeline_v12_qa_2026-09-19.md)

## 캡션 초안 — 그림 역할 설명용

Overall pipeline of online Gaussian mapping. The online frontend provides poses and depth evidence for Gaussian initialization and geometric supervision. (a) View Growth admits additional arrived views according to completed mapping updates. (b) View Sampling allocates updates using cumulative selection counts while retaining randomness. (c) Geometry Constraints use available depth evidence to constrain ray-space opacity during map optimization. Solid arrows denote data or supervision; dashed arrows denote scheduling feedback. All scene imagery in this concept sketch is illustrative.

최종 캡션에는 세 방법의 정식 이름을 본문과 맞추고, 그룹 내 비복원 선택 및 geometry loss의 최종 확정 범위를 확인한다. 현재 그림은 선택된 두 영상을 한 update에 동시에 학습한다는 의미가 아니다.

## v06–v07 캡션 초안

Overview of online Gaussian mapping. Keyframes (K) and intermediate views (I) supply mapping observations, while the online frontend provides poses and available keyframe depth evidence. (a) Previously admitted views are retained, and additional arrived views are admitted according to completed mapping updates; the snapshots illustrate successive admissions when candidates are available. (b) Selection counts determine a stochastic preference for under-selected views, with distinct views selected for consecutive updates. (c) Available depth evidence constrains the map's ray-space opacity and termination behavior. RGB supervision, shown as a representative component of the base mapping objective, and geometric supervision contribute to the same map update. Pool sizes, bars, ray profiles, and scene images are schematic, not measured results.
