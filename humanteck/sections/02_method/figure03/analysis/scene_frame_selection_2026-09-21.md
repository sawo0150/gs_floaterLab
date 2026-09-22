# Fig. 3 scene/run/frame 후보 선정

상태: 원본 RGB, 기존 최종 지도 렌더링, 실행 이벤트를 읽은 잠정 추천.
학습·GPU 렌더링·중간 PSNR 측정은 수행하지 않았다.

## 1순위: RPNG table_01, F18, frame index 330

- View UID: `1662915742346800804.png`.
- ROI: 전처리된 기존 렌더 이미지 좌표 `(384, 208, 508, 332)`의 파란 테이블 천 무늬.
- [기존 실제 비교판](../../figure02/candidates/F18_comparison.png).
- 초반 raw frame 200에서 테이블 천을 이미 관측하는 것을 확인했다.
  고정 frame 330의 ROI가 각 checkpoint에서 어느 정도 관측됐는지는 중간 map으로 추가 확인한다.
- Baseline event 20은 입력 prefix 333에서 누적 optimizer step 197이다.
  따라서 frame 330은 실행 초기에 위치한다. 이것을 모든 ROI 표면의 정확한 첫 관측 시점으로 간주하지 않는다.
- 최종 지도 PSNR은 전체 held-out 기준 23.9288 → 25.5814 dB.
  최종 optimizer step은 baseline 3,027 / ours 3,030.
- 전체 결과의 평균적인 scene이라고 주장하지 않는다. 고정 view의 질감 개선을
  읽기 쉽게 보여주기 위한 예시 후보이며, 빠른 도달 여부는 곡선 측정 후 판정한다.

Run pair (공통 seed 0):

```text
results/experiments/exp94_normalized_metric_v2_fixed_eval/rpng/table_01/
  native_vanilla_render_matched_s0/
  normalized_variance_s0/
```

기존 Fig. 2와 동일한 수정된 fixed evaluator·matched-render 비교 계열이며 Carve는 off다.
이 run은 mapping 비교다. 전체 tracking+mapping 실시간 속도나 Carve 포함 기하 수렴의 증거로 확대하지 않는다.

## Inset에서 고정할 것

세 시점 모두 **동일 frame 330의 동일 카메라·ROI**를 각 checkpoint map으로 렌더링한다.
Input frame 번호는 평가 카메라를 식별하고, x축 iteration은 지도 학습 상태를 식별한다.
각 checkpoint마다 다른 입력 frame을 보여주지 않는다.
곡선은 이 frame의 PSNR이 아니라 고정 전체 held-out 집합의 평균이다.

우선 저장할 inset checkpoint 후보는 **600 / 1,500 / 2,700 optimizer iterations**.
이는 약 3,000 step 실행을 기준으로 정한 초기 설계값으로, 관측된 결과나 확정 수치가 아니다.
첫 checkpoint에서 ROI의 미관측 영역/지도 재초기화 영향이 큰지 확인한다.
조건 때문에 바꾸는 경우 이유를 남기고, 최대 성능 격차를 찾기 위해 시점을 바꾸지 않는다.
양쪽 모두 실제 누적 Gaussian optimizer step을 사용하고, 각 시점의 입력 prefix와
training render 수를 기록한다. 다른 view 수를 처리하는 step을 동일 compute로 단정하지 않는다.

## 대안

| 우선순위 | 기존 후보 | 장면 / frame | 이유와 제한 |
|---|---|---|---|
| 2 | F04 | table_06 / 1420 | Fig. 2의 포스터와 연결됨. 작은 crop에서 로고가 읽히지만 초반부터 같은 면을 관측하는지 불확실 |
| 3 | F07 | table_08 / 425 | 초기 frame이며 테이블 경계·무늬가 있음. 비스듬한 crop, 최종 약 7,400 step으로 첫 제작 비용이 큼 |

table_06의 raw frame 200은 F04와 다른 포스터 면, raw frame 800은 판의 옆면을 보인다.
Baseline이 prefix 1427을 처리한 event에서 누적 step은 1,280이다.
따라서 F04를 초기 3시점 개선 예시로 바로 재사용하기보다 영역 가시성을 먼저 확인해야 한다.
이 두 raw sample만으로 정확한 첫 관측 시점을 확정하지 않았다.

## 확인한 파일 가용성

table_01, table_06, table_08, aria1253 각각 baseline/ours run 디렉터리를 재귀 확인했다.
모두 저장 Gaussian map은 `3dgs_before_final.ply` 하나이며, 중간 `.ply/.pt/.pth` 모델은 없다.
이벤트 로그는 중간 work와 입력 prefix를 알려주지만 중간 지도의 appearance를 복구하지 못한다.
최종 map을 열화해 중간 렌더처럼 만들지 않는다.

기존 실행 조건과 source provenance를 확인한 뒤 별도 output 디렉터리에서
checkpoint를 추가하는 paired 실행이 필요하다. 기존 결과는 보존한다.
약 100 step마다 map을 저장하면 이 길이에서는 약 30개의 곡선 평가점이 생긴다.
정확한 step 경계 저장을 지원해야 하며 저장 때문에 학습 배분이 달라지지 않게 한다.
사후 고정 held-out 평가로 곡선을 만들고 3개 checkpoint에서 동일 ROI를 렌더링한다.

## 제작 방식

실측 곡선을 코드로 SVG path로 출력하고 실제 crop PNG를 삽입한다.
Inkscape에서 라벨·색·연결선·inset 위치를 정리해 PDF를 내보낸다.
곡선 값과 crop 내용은 수작업 또는 생성형 도구로 바꾸지 않는다.
v03의 초기 주황 연결선 오류는 각 방법의 해당 step marker에 연결해 교정한다.
단일 단 약 86 mm에서 세 inset의 무늬가 식별되는지 검수한다.
