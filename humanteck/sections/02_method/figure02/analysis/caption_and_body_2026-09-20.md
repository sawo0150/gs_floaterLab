# Fig. 2 캡션과 본문 연결 수정

## 후속 사용자 피드백 반영 — 현재 초고

캡션과 본문에서 Carve off 조건 및 상세 render count를 빼고 시스템의 appearance 결과로 간결하게 소개한다. 실제 실행 조건은 바뀌지 않으므로 비출력 주석과 provenance에 유지한다. 세 모듈 모두 활성화한 결과 또는 Carve로 인한 개선이라고 쓰지 않으며, 최종 실험 설정에서 구성을 명확히 밝혀야 한다.

최종 캡션:

> Rendering comparison with VIGS-SLAM on RPNG table_06 under a matched rendering budget. Insets highlight more faithful reproduction of the poster's logo and printed patterns by our system.

최종 연결 본문:

> Figure 2 shows a selected held-out example in which our system more faithfully reproduces the poster's logo and printed patterns. This example illustrates our goal of turning incoming observations into faithful appearance reconstruction within a limited mapping budget.

아래는 최초 수정 기록이며 표시되는 문구는 위 최종안이 우선한다.

검증: Fig. 2 PDF 존재, label 중복 없음, 실제 PDF 직접 include, placeholder 제거를 확인했다. 전체 원고 Tectonic 컴파일은 기존 `humantech.cls`가 요구하는 `Batang` 폰트 미설치로 중단됐다. 템플릿이나 시스템 폰트는 변경하지 않았으며, 전체 원고의 새 PDF 검수는 완료하지 못했다.

## 참고한 수상작의 방식

- `humanteck/ref/1st_humantech.pdf`, 2쪽 Fig. 2: 비교 방법, 데이터셋, 비교 항목을 한 문장으로 소개한다. 이어지는 본문에서 비용 감소와 품질 유지라는 기여를 해석한다.
- 같은 문서의 Fig. 3: 패널 해석이 필요하므로 위/아래 패널의 의미와 주요 관찰을 덧붙인다.
- `humanteck/ref/2nd_humantech.pdf`, 10쪽 Fig. 9–10: 여러 비교 방법과 데이터 조건을 캡션에서 식별한다. 방법의 효과를 설명하는 논의와 캡션의 역할을 구분한다.

우리 그림도 비교 대상과 조건, 확대 영역에서 관찰할 차이를 짧은 두 문장에 담는다. Fig. 2의 모든 실험 기록을 캡션에 넣지 않고, exact render count와 기여 연결은 Evaluation 본문에 둔다.

## 반영한 캡션

> Rendering comparison with VIGS-SLAM on RPNG table_06 under a matched rendering budget. Insets highlight improved reproduction of the poster's logo and printed patterns with our view-management policy (Carve disabled).

원고에는 VIGS-SLAM citation을 유지한다. 약 35단어로, 종전 약 48단어보다 짧다. 이미지에 이미 방법별 열 이름이 있으므로 왼쪽/가운데/오른쪽 설명을 반복하지 않는다.

## 본문 연결

> Figure 2 shows a selected held-out example in which our map more faithfully reproduces the poster's logo and printed patterns. Both methods use 34,437 mapping renders, with Carve disabled in ours. This comparison illustrates the benefit of managing observation admission and training allocation for appearance learning under limited computation.

핵심은 “보기 좋은 포스터”가 아니라 **같은 work 예산에서 관측 유입과 학습 배분을 관리한 결과가 표면 appearance의 재현 충실도로 이어지는 사례**다. 따라서 포스터 로고와 인쇄 패턴을 구체적으로 명명하고, contribution과 연결되는 view admission / training allocation을 본문에서 다시 짚었다.

## 주장 범위

- 선정 프레임은 high-gain example이며 전체 평균의 대표값으로 제시하지 않는다. 전체 평균은 앞 문장의 dataset PSNR 결과가 담당한다.
- 비교는 View Growth와 Sampling을 포함한 joint-policy 결과다. 각 component의 개별 인과 효과는 주장하지 않는다.
- 한 final-map RGB 그림으로 수렴 속도, 동일 wall time 또는 정확한 3D geometry를 입증했다고 쓰지 않는다.
- Carve off를 본문과 캡션에 명시해 RGB 개선을 기하 제약에 귀속하지 않는다.
- 아직 준비되지 않은 Fig. 3은 기존 draft 상태를 유지한다.

## 변경 범위

`humanteck/HumanTeck_Song_s_intern/paper.tex`의 Evaluation 내 Fig. 2 연결 문장, 출처 주석, Fig. 2 블록만 수정했다. 이미지 파일과 다른 문단, 사용자가 수정한 Conclusion은 건드리지 않았다. 제작이 완료된 Fig. 2의 placeholder 분기를 제거하고 실제 PDF를 직접 include한다.
