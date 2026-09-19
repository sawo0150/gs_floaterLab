# 우리 overall pipeline 설계 v01

날짜: 2026-09-19. 단계: 배치 검토용 개념 설계. 구현·실험 검증 또는 최종 도판 아님.

## 1. 한 문장 메시지

도착한 관측을 실제 최적화 진행에 맞춰 편입·재학습하고, 가용 depth evidence로 지도 기하를 함께 제약하는 온라인 Gaussian mapping.

## 2. 그림이 답할 세 질문

- (a) **언제 더 많은 관측을 학습에 포함하는가?** 완료된 mapping update에 맞춰 포함한다.
- (b) **포함된 관측 중 무엇을 다시 학습하는가?** 누적 선택 횟수가 적은 관측을 선호하되 무작위성과 그룹 내 중복 방지를 유지한다.
- (c) **그 학습이 어떤 기하를 유도하는가?** 관측된 빈 공간과 표면 evidence를 구분해 ray상의 opacity를 제약한다.

## 3. 최소 상태와 화살표

| 출발 | 도착 | 의미 / 주의 |
| --- | --- | --- |
| RGB + IMU | Online frontend | 기반 시스템 입력. depth 센서를 추가하지 않는다. |
| Frontend pose + depth | Gaussian initialization → Gaussian map | 관측 기하 기반 초기화·확장. 별도 contribution 색상 없음. |
| 도착한 RGB 영상 | (a) Growth → Training-view pool | keyframe 사이 관측도 후보. 미래 영상은 없음. 기존 편입 영상 유지. |
| Mapping update 완료 | (a) Growth | 완료된 작업량 S(t). 영상 도착 횟수나 loss 감소량이 아니다. 점선 feedback. |
| Training-view pool | (b) Sampling → 선택 영상 → Mapping update | 영상은 복사/참조되어 학습되며 pool에서 제거되지 않는다. |
| 선택 이력 | (b) Sampling | 누적 선택 횟수 n_i. loss나 정보가치 점수가 아님. |
| Gaussian map | Mapping update | 현재 지도에서 렌더링하고 appearance loss 계산. |
| Mapping update | 같은 Gaussian map | 지도 parameter update. 지도는 매번 새로 만드는 출력 객체가 아니다. |
| 검증된 frontend depth evidence + 현재 ray opacity | (c) Geometry Constraints | keyframe depth rays 등 확보된 evidence. 모든 non-keyframe에 depth GT가 있는 것으로 그리지 않는다. |
| (c) Geometry Constraints | Mapping update | 최적화 목적에 작용하는 loss. hard pruning이나 학습 후 정리가 아님. |

### Method의 기준 식 — 그림에는 유도 없이 직관만

- Growth: `N_max(t) = min(M(t), N_0 + floor(S(t)/κ))`. S(t)는 완료된 update, M(t)는 그 시점까지 도착한 가용 영상.
- Sampling: `p_s(i) ∝ exp(-β_s n_i)`. entropy로 무작위성을 유지하며 K개를 비복원 선택해 다음 K updates에 사용. K개를 한 번의 거대 batch update로 그리지 않는다.
- Geometry: 현재 TeX에는 Carve/Hit/조합 후보가 남아 있다. 도판에는 공통 ray-space 직관만 표현하고 최종 loss·가중치·검증 성과를 고정하지 않는다.

기준: [Method TeX](../../../../paper/latex/sec/4_method.tex)의 View Growth, View Sampling, Causal Ray-Space Geometry Supervision.

## 4. 배치와 표현

- 가로 전체폭 figure, 약 2.2:1 비율을 초기 시안으로 검토한다. 최종 180mm 지면에서 축소 가독성을 다시 확인해야 한다.
- 위쪽 좁은 회색 영역: 기존 frontend 및 초기화. 본문에서는 개요 한 문장으로 설명.
- 가운데 주 경로: 도착한 영상 → 주황 Growth → pool → 파랑 Sampling → Mapping update.
- 오른쪽: 반복 갱신되는 Gaussian map. 입력과 출력의 서로 다른 지도로 오해하지 않도록 연결.
- 오른쪽 아래 보라 Geometry: ray와 surface-depth band로 표현하고 위의 Mapping update에 loss 입력.
- 실선: 데이터/감독. 점선: 스케줄링 feedback. 점선은 바깥 통로를 이용하고 본문·노드와 겹치지 않게 한다.
- 질문형 짧은 label로 직관을 전달. 정식 방법명과 설명은 caption/본문에 둔다.

## 5. 그림을 따라 쓸 Method 요약의 골격

1. **개요:** frontend의 online pose·depth로 Gaussian을 초기화하고 관측을 이용해 계속 개선한다. 그림의 회색 기반에 대응.
2. **(a):** 관측 추가는 감독 정보를 늘리지만 반복 학습을 분산시킨다. 완료된 update로 학습 집합의 성장 속도를 정한다.
3. **(b):** 성장하는 집합에서는 편입 시점에 따른 누적 선택 기회가 다르다. 횟수를 고려한 확률 선택과 비복원 선택을 사용한다.
4. **(c):** 관측을 더 잘 학습해도 색 일치만으로 기하는 정해지지 않는다. 가용 depth evidence로 free-space와 surface 기여를 구분한다.

이번에는 문단 자체를 확정하지 않는다. 그림 검토 후 각 방법 2–3문장 수준으로 압축하고, 지면에 따라 개요와 합친다. 전체 학술논문의 Introduction 구조는 변경하지 않는다.

## 6. 실용적 이득을 보여줄 별도 결과 그림

수상자의 수치·정성 비교 전략은 실제 실험 결과에 적용한다. 입력/GT, baseline, ours의 같은 시점 crop과 명시된 update 또는 시간 예산을 사용한다. 이미지 생성으로 성능 비교나 GT를 만들지 않는다.

학습 효율은 동일 update에서의 held-out 품질로, 시간 가속은 동일 품질까지의 실제 시간으로 검증 범위를 구분한다. geometry 개선과 floater 감소는 별도 측정·실제 비교가 있어야 한다. 학습 완료 카운트를 수렴 판정으로 묘사하지 않는다.

## 7. 생성 이미지 검수 항목

- 세 기여의 label이 모두 있는가? 기반 초기화와 색으로 구분되는가?
- 이미지 pool growth와 Gaussian densification이 혼동되지 않는가?
- Geometry가 Sampling 뒤의 후처리처럼 보이지 않는가?
- S(t), n_i 피드백의 출발과 도착이 올바른가?
- frontend depth가 입력 센서 depth 또는 모든 영상의 GT처럼 보이지 않는가?
- 생성 room/map은 설명용으로 표시되었는가? 가짜 결과·수치가 없는가?
- 영문 label, 화살표 방향, 축소 가독성이 괜찮은가?

생성 그림의 배치가 위 설계와 다르면, 그림을 근거로 Method를 바꾸지 않고 QA에 차이를 기록한다.
