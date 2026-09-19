# Overall figure 재설계 — 기능 구조와 시각적 위계

날짜: 2026-09-19. 사용자와 합의한 방향을 반영한 v04 설계. v01–v03은 이력으로 보존한다.

## 무엇을 기준으로 구조화하는가

큰 구조는 **온라인 관측 → 학습 관측 관리 → Gaussian 지도 최적화**다. 세 contribution 이름을 병렬 박스로 늘어놓는 대신, 실제 객체와 그 객체에 작용하는 방법을 보여준다. 기존 논문 비교 근거는 [도판 조사](01_pipeline_reference_review_2026-09-19.md)에 있다.

CaRtGS의 localization / geometry mapping / rendering 역시 최상위에서는 시스템 기능 구분이다. 우리도 기능을 바탕으로 두되, frontend를 축약하고 새 방법이 작동하는 mapping을 확대한다. 전체 tracking 구조를 자세히 복제하지 않는다.

## 배치와 디자인 원칙

| 기능 영역 | 주인공인 시각 객체 | 그 위에 표시할 동작 |
| --- | --- | --- |
| Online observations — 약 21% | camera trajectory, keyframe/중간 영상 filmstrip, frontend depth | online pose·depth 추정. 초기화는 회색 기반 경로 |
| Training-view management — 약 35% | 보존되는 학습 영상 배열과 편입 대기 관측 | (a) 배열 경계에서 편입, (b) 동일 배열 안에서 확률 선택 |
| Gaussian map optimization — 약 44% | 크게 그린 공유 Gaussian 지도, 관측/렌더 영상, 작은 ray inset | rendering·loss·update 반복, (c) 최적화 안의 기하 감독 |

- 기능 영역은 옅은 배경과 제목 정렬로 구분한다. 모든 요소를 테두리 박스 안에 넣지 않는다.
- 화면을 채우는 것은 긴 문구나 화살표가 아니라 영상 배열과 지도다. 지도는 가장 큰 단일 시각 객체로 둔다.
- Growth는 입장 경계, Sampling은 배열 내부 강조와 확률 막대, Geometry는 ray와 표면으로 나타낸다.
- 색은 역할을 가진다: 주황 admission, 파랑 selection, 보라 geometry, 회색 기존 시스템. 색에만 의존하지 않고 (a)–(c)와 문구도 붙인다.
- 데이터는 짧은 실선, 스케줄링 feedback은 점선. 초기화는 위쪽, depth evidence는 아래쪽 통로로 분리한다.
- 전체를 약 2.2:1로 구성한다. 실제 인쇄 폭의 가독성 검증은 최종 벡터 도판 단계에서 별도로 한다.

## 수상자 팁과 본문의 대응

독자는 관측을 보고, 어떤 영상으로 학습하는지 보고, 그 영상과 depth가 지도를 어떻게 갱신하는지 읽는다. 본문도 기반 설명 → (a) → (b) → (c)로 따른다. (a), (b)는 같은 pool에 작용하고 (c)는 loss이므로 세 기여를 직렬 처리 단계로 오해하게 하지 않는다.

수치 기반 실용성은 별도 실제 결과 도판이 맡는다. 생성된 방·영상·Gaussian은 구조 설명용이며 성능 증거가 아니다. 검증되지 않은 속도 향상이나 floater 제거 결과를 붙이지 않는다.

## Method와 맞춰 지킬 사항

- 완료 update 수는 수렴 판정이나 loss 감소량이 아니다.
- 이미 도착한 관측만 편입하며, 이전 학습 영상은 보존한다. 선택은 pool에서 영상을 제거하지 않는다.
- 누적 선택 횟수는 영상 정보가치가 아니다. 무작위성을 남기며 K개 선택은 다음 K updates에 한 장씩 사용한다.
- depth는 frontend가 제공하는 가용 keyframe evidence다. 모든 중간 영상에 depth GT가 있다고 그리지 않는다.
- Geometry는 공유 지도 최적화에 들어가는 loss다. hard pruning 또는 학습 후 정리가 아니다.
- Carve/Hit/조합의 최종 선택은 아직 Method에 열려 있으므로 도판에서 특정 조합을 확정하지 않는다.

기준: [현재 Method](../../../../paper/latex/sec/4_method.tex). 그림과 식이 다르면 그림을 고친다.

## 산출물

- [v04 생성 프롬프트](../figures/overall_pipeline_v04_prompt.md)
- 이미지 생성은 내장 imagegen으로 새 구도를 만들며 기존 그림을 덮어쓰지 않는다.
- v04는 구조·디자인 검토용이다. Overleaf에는 아직 삽입하지 않는다.
