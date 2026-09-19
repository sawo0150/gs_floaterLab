# 새 geometry loss를 설명하는 도판 조사

원문 그림 바로 보기: [참고 도판 갤러리](../figures/reference_figures/README.md). 도판 crop과 캡션을 포함한 전체 페이지를 함께 저장했다.

> 후속 사용자 결정: 디자인 reference는 **overview figure만** 사용한다. 아래 조사 중 독립 loss 도식·ablation은 배경 조사로만 보존한다. §4의 두 분포 대비안은 이번 overview에 적용하지 않으며, 기본 supervision 묶음과 작은 기하 도식으로 대체한다. 실제 적용 시안은 [v09](../figures/overall_pipeline_v09.png), 미완성 경로는 [검수 기록](../figures/overall_pipeline_v09_qa_2026-09-19.md)을 따른다.

2026-09-19. Sampling 표현과 overall figure의 세 영역은 유지한다. 이번 작업은 **새 loss의 시각적 설명을 설계하기 위한 원문 조사**이며, 이미지를 재생성하거나 Method의 후보 objective를 확정하지 않는다.

## 1. 현재 그림의 부족한 점

v07에는 ray, Gaussian, termination profile, depth marker가 있지만, 독자가 다음을 구분하기 어렵다.

1. 입력으로 주어진 기하 evidence와 학습 대상인 Gaussian map은 무엇인가?
2. 기존 supervision이 작게 평가할 수 있는 잘못된 상태는 무엇인가?
3. 제안 loss는 그 상태의 어느 부분에 벌점을 주는가?

즉, 재료를 나열한 것에 비해 **새 목적함수가 구분하는 상태**가 잘 보이지 않는다. `Geometry loss` 상자나 수식을 늘리는 것만으로 해결되지 않는다.

## 2. 원문 도판에서 확인한 설명 방식

도판 번호와 페이지는 `humanteck/ref/figure_design/`에 저장한 버전 기준이다. 해당 PDF 페이지 전체를 렌더링하여 확인하고 관련 본문·수식을 함께 읽었다. 아래 구분은 조사한 사례를 바탕으로 한 설계상의 분류이며, 모든 논문이 따르는 표준이라는 뜻은 아니다.

| 논문 / 위치 | 실제 시각화 | 배울 점 | 그대로 가져오면 안 되는 점 |
| --- | --- | --- | --- |
| **DN-Splatter**, Fig. 1, PDF p.2; §4, Fig. 2, p.5 | Overview에서 관측·예측 RGB/depth/normal을 loss에 연결한다. 별도의 작은 기하 도식에는 Gaussian, 표면, depth 방향, normal 방향, smoothing 관계가 함께 표시된다. Fig. 2는 실제 normal-map 비교다. | **전체 구조에서 loss의 위치를 보여주는 층**과 **작은 공간 도식에서 작용 대상을 보여주는 층**을 병행할 수 있다. 여러 기존 loss를 없애지 않고 새 설명에 시선을 집중시킨다. | DN-Splatter의 Gaussian-axis normal과 우리의 rendered-depth-derived normal을 같은 정의로 그리지 않는다. 모든 원문 loss를 우리 그림에 추가하지 않는다. |
| **mip-NeRF 360**, Fig. 6, PDF p.6; §4 | Ray상의 step-function weights를 그리고 수평·수직 화살표로 distortion regularizer가 간격·폭·weight에 작용하는 양상을 나타낸다. Fig. 5의 실제 ablation은 별도로 제시한다. | Loss 기호 대신 **어떤 분포를 어떤 방향으로 제약하는가**를 직접 그린다. 작용 원리와 실험 결과를 분리한다. | 원문의 distortion loss는 우리 loss가 아니다. 원문 화살표를 복사하면 Carve까지 위치 이동을 유도하는 것처럼 잘못 읽힐 수 있다. |
| **DS-NeRF**, Fig. 3, PDF p.4; §3 | Ray 상의 density, alpha, transmittance, termination distribution의 관계를 구별한다. | 공간상의 Gaussian과 아래 그래프를 같은 depth 축에 정렬하면, 그래프가 무엇을 뜻하는지 이해하기 쉽다. | Gaussian density, effective alpha, termination weight를 모두 `opacity`라고 부르지 않는다. 개념 정의 도식 자체만으로 새 loss의 필요성이 설명되지는 않는다. |
| **DS-NeRF**, Fig. 6, PDF p.8 | NeRF / depth-MSE / 제안 KL-divergence objective의 실제 rendering을 비교한다. | 단순한 전체 방법 on/off보다 **가장 가까운 기존 supervision과 제안 loss의 차이**가 중요할 수 있다. | 생성한 장면을 이런 ablation처럼 제시하면 안 된다. 현재 overall figure에는 원리 도식만 넣는다. |
| **2D Gaussian Splatting**, §5, Fig. 6, PDF p.7 | Normal consistency 제거, depth distortion 제거, full model의 normal maps를 나란히 제시한다. | Loss가 만들어 내는 기하 차이를 RGB만이 아니라 **normal map 등 민감한 출력**으로 검증한다. | Fig. 3의 surfel projection 도식은 표현·렌더링 설명이지 loss 도식이 아니다. Fig. 6은 실제 결과이므로 개념 그림으로 대체할 수 없다. |
| **PGSR**, Fig. 4, PDF p.4; Fig. 9, p.8 | Rendered quantities와 supervision의 연결, 대응 patch와 기하 projection 관계를 보여준다. | 추상적인 loss 상자 대신 **무엇과 무엇을 비교하는지**를 구체적으로 표시한다. | PGSR의 planar/multi-view 제약을 우리의 ray-space objective인 것처럼 그리지 않는다. |

추가로 **Urban Radiance Fields**, §4.2, PDF p.4를 확인했다. Expected-depth matching과 line-of-sight supervision을 구별하고, ray를 empty / near-surface / distant 구간으로 나눠 수식을 제시한다. 이는 우리 도판의 구간 해석을 점검하는 데 유용한 **방법론 참고**이지, 이 페이지에 독립적인 loss schematic이 있다는 뜻은 아니다. 특히 URF는 surface 뒤 distant 구간에도 penalty를 둔다. 이를 복사해 우리 도판에서 표면 뒤를 관측된 빈 공간으로 칠하면 안 된다.

### 요약

- Overview: 어떤 관측·출력으로 loss를 계산하며 어디에 합치는가?
- Mechanism inset: 어떤 잘못된 상태에 어떤 제약을 가하는가?
- Ablation: 실제로 무엇이 개선됐는가?

현재 필요한 것은 두 번째다. 첫 번째는 간결하게 유지하고, 세 번째는 향후 실제 결과 그림에서 담당한다.

## 3. 우리 Method와 일치하는 내용

권위 문서: `paper/latex/sec/4_method.tex`, §3.3. 현재 파일에는 Carve / Hit / factorized Carve+Hit가 **후보**로 함께 남아 있다. 모두 확정된 별도 loss인 것처럼 그리면 안 된다.

- Evidence는 해당 시점에 가용한 multi-view-verified keyframe의 BA-refined depth다. 센서 GT depth가 아니다.
- Rendered mean depth는 contributor들을 한 scalar로 압축한다. 따라서 그 값의 일치만으로 ray상의 분포가 유일하게 정해지지는 않는다.
- **Carve:** 관측 표면 앞에서의 premature termination을 억제한다. 현재 명시된 detached-geometry 경로에서는 opacity만 낮춘다. 혼자서 surface coverage를 만들거나 모든 Gaussian을 표면으로 옮기지 않는다.
- **Hit:** depth 관측을 설명하는 finite first hit를 유도한다. 단순히 전체 분포를 Gaussian target과 pointwise matching하는 KL loss는 아니다.
- **Carve+Hit:** free-space와 surface 구간을 나누고 surface-local transmittance를 사용한다. 그림에서 전역 Carve와 전역 Hit를 무조건 더하는 것으로 단순화하지 않는다.
- Base mapping supervision과 새 objective가 합쳐져 하나의 map optimization으로 이어진다. Loss별로 별도 지도를 만드는 구조가 아니다.

### Mean-depth ambiguity를 설명할 수 있는 최소 예시

이상화한 ray에서 total termination mass를 1로 두고, 관측 depth를 D=2로 놓는다.

- 분리된 분포: z=1과 z=3에 각각 weight 0.5 → mean depth 2.
- 표면에 집중한 분포: z=2에 weight 1 → mean depth 2.

둘은 같은 mean depth를 갖지만 첫 번째는 표면 앞 termination mass를 포함한다. 이것은 **scalar depth만으로 구분되지 않는 상태를 보여주는 수학적 개념 예시**다. 실제 Gaussian fitting 결과나 모든 RGB/depth/normal supervision의 실패 증명이 아니다. 확률 질량을 그리는 경우 원시 Gaussian opacity가 아니라 `termination weight w`라고 표기한다.

## 4. 권장 구성: 오른쪽 optimization 영역 안의 작은 비교 확대도

### 4.1 기본 supervision은 남기되 시각적 비중을 낮춘다

Map → rendering → `Base supervision: RGB · depth · normal`을 한 묶음으로 유지한다. 정확한 기호·가중치는 최종 objective에 맞춰 본문/캡션에 적는다. 모든 loss마다 큰 독립 상자를 만들 필요는 없다.

입력 가용성은 최소한으로 표시한다.

- RGB: keyframes + intermediate views.
- Depth/normal 및 제안 ray-space 항: 유효한 prior/evidence가 있는 keyframe 경로. 각 항의 실제 활성화 조건은 채택 configuration과 일치시킨다.

이렇게 하면 depth/normal을 숨기지 않으면서도 제안 loss의 기여와 구분할 수 있다.

### 4.2 새 loss에는 같은 depth 축을 공유하는 기하 확대도를 준다

추천 제목: `Beyond mean-depth matching` 또는 더 중립적인 `Ray-space geometry supervision`.

**위쪽 — 문제를 보여주는 작은 대비:** 같은 D marker를 공유하는 두 termination profiles를 나란히 그린다. 하나는 표면 앞·뒤로 분리된 mass, 다른 하나는 표면 근처 mass다. 가운데 `Same mean depth ≠ same geometry`를 짧게 넣는다. 두 profile은 before/after 학습 결과가 아니라 서로 다른 가능한 상태다.

**아래쪽 — 제약의 공간적 의미:** camera ray, 표면 앞 free-space, depth evidence D와 uncertainty band, 그 뒤의 미관측/가려진 영역을 정렬한다. 잘못 놓인 앞쪽 Gaussian 또는 대응 termination mass를 강조하고 `Penalize premature termination`으로 연결한다. 기본 supervision과 대비되는 포인트는 새 loss 이름이 아니라 **표면 앞 mass가 명시적인 제약 대상이라는 것**이다.

지면이 작으면 위·아래를 합친 한 개의 ray/profile 도식으로 줄인다. Gaussian과 profile을 중복 장식으로 늘리기보다, 같은 depth 축의 정렬과 벌점 영역을 우선한다. 안전 margin/uncertainty는 얇은 band로만 표현하고 수식 유도를 넣지 않는다.

최종 후보에 따른 차이:

| 채택 objective | 그릴 작용 | 피할 표현 |
| --- | --- | --- |
| Carve | 앞쪽 Gaussian의 opacity 약화 / free-space 위반 억제 | Gaussian을 표면으로 이동시키는 화살표, surface hit 생성 보장 |
| Hit | 관측 depth 근처에서 first-hit evidence를 설명하도록 유도 | 모든 Gaussian의 일괄 이동, KL histogram matching으로 표기 |
| Carve+Hit | 구분된 free-space 억제와 local surface-hit 설명 | 표면 앞 transmittance를 두 번 세는 전역 두 항 합산 도식 |

최종 선택 전에는 optimizer 방향 화살표보다 **penalty 영역과 depth evidence**를 보여주는 중립적인 표현이 안전하다. 실제 업데이트 전후처럼 보이는 개선 장면은 만들지 않는다.

### 4.3 Loss 합류는 한 곳에만 표시한다

기본 supervision과 새 ray-space objective를 같은 `Map objective`에 합치고 Gaussian map으로 돌아가는 update를 한 번만 그린다. 후보 정리 전의 설명용 표기는 `L_map = L_base + λ L_ray` 정도면 충분하다. 이는 최종 수식을 새로 확정하는 것이 아니다.

## 5. 수상자 팁과의 연결

`humanteck/ref/humanteck_tips`의 핵심은 pipeline을 따라 본문을 읽게 하고, 전공 밖 독자도 동기를 이해하게 하며, 실제 개선은 결과 그림과 수치로 간결하게 전달하는 것이다.

따라서 이 확대도에서 남길 메시지는 다음 정도다.

> 평균 깊이가 맞아도 표면 앞의 잘못된 기하는 남을 수 있다. 새 제약은 관측된 빈 공간과 표면의 evidence를 직접 활용한다.

이는 원리 설명이다. 실제 floater 감소와 품질 유지는 별도의 검증 결과로 보여줘야 한다. Loss schematic에 생성한 “개선된 결과”를 끼워 넣지 않는다.

## 6. 다음 이미지 수정 전에 확인할 사항

1. Sampling 및 세 영역의 전체 구조는 유지.
2. 오른쪽 영역의 기존 RGB loss를 base supervision 묶음으로 정리.
3. 장식적인 ray/profile을 penalty 대상이 명확한 비교 확대도로 교체.
4. Depth source, axis, weight label, surface 뒤 미관측 구간을 명확히 구분.
5. 채택 objective를 확인한 뒤에만 구체적인 gradient/효과 화살표와 최종 loss 이름 확정.
6. 인쇄 축소 시 `same mean / different geometry`와 `premature termination`이 읽히는지 검수.

이번에는 조사·설계 메모만 작성했다. Overall image, TeX, loss 구현은 수정하지 않았다.
