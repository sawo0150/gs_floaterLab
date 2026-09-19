# 세부 기여 시각화: 논문 도판 조사와 적용안

2026-09-19. 대상: 현재 3영역 overall figure 내부의 관측 종류, pool 성장, sampling, loss 표현. Introduction/Method TeX 내용은 변경하지 않는다.

## 1. 결론: 상태뿐 아니라 변화와 선택 근거를 보여준다

v05는 관측 영상, pool, 지도를 보여주지만 중요한 동작을 독자가 문구로 추측해야 한다. 이번 설계에서는 **관측의 정체성 → 집합의 변화 → 선택의 근거와 결과 → 감독이 작용하는 대상**을 이어 보여준다.

| 현재 모호한 점 | 새 시각적 증거 | 참고 도판 |
| --- | --- | --- |
| 입력에서 K/I를 구분했지만 pool에서는 차이가 사라짐 | 동일 K/I badge와 영상 ID를 입력·pool·선택 출력까지 유지 | iMAP Fig. 4의 frame identity 유지, GSORB Fig. 2의 관측 누락 문제 |
| 큰 pool 한 장으로는 증가를 알 수 없음 | 기존 영상을 유지한 3→4→5장 스냅샷, 추가 영상에만 주황 표시 | On-the-Fly GS Fig. 2의 관측 추가와 반복 상태 전개 |
| 파란 막대가 무엇인지, 왜 그 영상이 선택됐는지 불명확 | 같은 영상 열에 count와 probability를 맞추고 선택 결과까지 표시 | iMAP Fig. 4, CaRtGS Fig. 3의 학습 기회 분석 |
| ray에 Gaussian이 있다는 것만 보임 | 관측 표면 D와 앞쪽 잘못된 opacity를 같은 깊이축에서 보여줌 | GSORB Fig. 3, DS-NeRF Fig. 3, mip-NeRF 360 Fig. 6 |
| loss 화살표가 연결 의미를 대신함 | RGB의 관측/예측 쌍, depth evidence/현재 ray 상태를 별도로 보여준 뒤 공동 update | PGSR Fig. 4·9, DS-NeRF Fig. 1 |

위 적용안은 조사에 기반한 **우리 설계 제안**이다. 아래 논문들이 우리와 같은 admission/count/geometry 방법을 제안했다는 뜻은 아니다.

## 2. 실제 도판을 확인한 7개 논문

### 2.1 iMAP — 선택 근거와 선택 결과를 같은 열에 배치

원문: [공식 PDF](https://openaccess.thecvf.com/content/ICCV2021/papers/Sucar_iMAP_Implicit_Mapping_and_Positioning_in_Real-Time_ICCV_2021_paper.pdf), [로컬](../../../ref/figure_design/imap_iccv2021.pdf). Fig. 3–4, PDF p.4, §3.5–3.6.

- 문제/기여: 증가하는 관측을 모두 매번 최적화하기 어려우므로 keyframe memory와 loss-guided pixel/keyframe sampling으로 연산을 배분한다. 현재 live frame도 최적화에 포함한다.
- Fig. 4: 가로로 놓인 RGB/depth 쌍 위에 각 frame의 loss 막대가 정확히 정렬되어 있다. 빨간 점선 테두리가 실제 선택된 frame을 표시하고, 등록 keyframe 집합과 current frame의 범위도 구분한다.
- Fig. 3: 공간별 loss heatmap과 실제 pixel sample 위치를 나란히 둔다. 점수만 보여주지 않고 그 점수가 어떤 선택으로 이어지는지 보여준다.
- 가져올 원리: 영상 ID, 선택 기준, 선택 결과를 같은 열로 정렬한다. 우리 figure에는 pixel sample 점 대신 **view 단위 선택**을 그린다.
- 차이: iMAP의 기준은 loss이고 우리는 누적 선택 횟수와 entropy다. iMAP의 bounded window/current-frame 강제 포함도 그대로 옮기지 않는다. iMAP이 모든 중간 영상을 영구 보존한다고 설명하지 않는다.

### 2.2 Gaussian On-the-Fly Splatting — 반복 단계를 펼쳐 시간 변화를 설명

원문: [arXiv v1](https://arxiv.org/abs/2503.13086v1), [로컬](../../../ref/figure_design/gaussian_on_the_fly_2503.13086v1.pdf). Fig. 2–3, PDF p.4, §IV-A–D.

- 문제/기여: 영상 획득 중 3DGS를 점진적으로 학습하며 새 영상 및 overlap 이웃에 학습을 배분하고, 영상별 학습 진행에 따라 learning rate를 조절한다.
- Fig. 2: 초기 영상 묶음과 initial GS 다음에 `N0+1`, `N0+2`, `N0+3` 영상이 반복 최적화에 합류하는 과정을 펼쳐 놓는다. 말줄임표는 이 과정의 반복을 나타낸다.
- Fig. 3: 새 영상을 root로 놓고 overlap에 따라 여러 층의 관련 영상을 펼쳐서, image weighting의 근거를 시각화한다.
- 가져올 원리: 같은 상태가 어떻게 이어지고 새 관측이 어디에 추가되는지를 보여준다. 우리의 3→4→5장 nested pool은 이 원리를 적용한 별도 설계다. 원문에 같은 pool 스냅샷 도판이 있다는 뜻은 아니다.
- 차이: 이 논문은 overlap 가중 배분과 마지막 추가 최적화 단계가 있다. 우리 그림에는 overlap tree, offline final optimization, 영상 도착 즉시 무조건 편입을 넣지 않는다.
- 논리상 주의: 이 연구도 오래된/새 영상의 학습량 차이를 다룬다. 따라서 추후 관련연구에서 증가하는 집합의 학습 불균형을 기존 연구가 전혀 고려하지 않았다고 주장하면 안 된다.

### 2.3 CaRtGS — overall과 기여 설명 그림의 역할을 구분

원문: [arXiv v2](https://arxiv.org/abs/2410.00486v2), [로컬](../../../../paper/ref/convergence/cartgs_2410.00486v2.pdf). Fig. 3–4, PDF pp.3–4, adaptive optimization 설명.

- 문제/기여: 연산 병목과 keyframe별 장기 학습 불균형을 다룬다. 빠른 역전파에 더해 loss에 따른 추가 학습 기회를 배정한다.
- Fig. 4: keyframe pool, Gaussian map, render/GT를 기능 영역 안에 배치하고 adaptive optimization을 feedback 경로에 표시한다. 큰 구조는 시스템 기능이며, 기여가 그 안에 들어간다.
- Fig. 3: keyframe index와 iteration/PSNR의 관계를 그래프로 보여주어 오래된/새 keyframe 간 차이를 설명한다. overall만으로 모든 선택 규칙을 설명하려 하지 않는다.
- 가져올 원리: overall에서는 pool→학습 연결을 유지하되, 우리 핵심인 sampling에는 작은 count/probability 설명을 붙인다.
- 차이: 원문의 iteration 곡선을 우리 결과처럼 복제하지 않는다. count 기반 선택을 loss 기반 선택으로 바꾸지 않는다. 막대는 장식이 아니라 실제 의미가 명시된 변수여야 한다.

### 2.4 GSORB-SLAM — 관측 누락과 ray 의미를 구체적으로 그림

원문: [arXiv v2](https://arxiv.org/abs/2410.11356v2), [로컬](../../../ref/figure_design/gsorb_slam_2410.11356v2.pdf). Fig. 1–3, PDF pp.2–4, §III-B.

- 문제/기여: tracking의 feature 기준만으로는 mapping에 필요한 관측이 빠질 수 있음을 지적하며 overlap 기반 keyframe 생성과 hybrid-graph rendering-frame 선택을 제안한다.
- Fig. 2: tracking이 정상이라는 판단 이후 keyframe을 만들지 않아 지도 학습 관측이 누락되는 사례를 실제 영상·특징점·처리 경로로 설명한다.
- Fig. 3: 위쪽의 transmittance 계단 함수와 아래쪽의 camera ray/Gaussian 위치를 깊이 방향으로 대응시킨다. 추상 곡선이 어느 공간 요소를 뜻하는지 읽을 수 있다.
- 가져올 원리: K/I가 함께 들어가는 mapping 경로를 보이고, geometry에는 공간 ray와 1D 분포를 정렬한다.
- 차이: 원문의 rendering frame은 keyframe에서 선택된다. 이 논문을 모든 intermediate view 보존의 선례로 부르지 않는다. transmittance threshold/median surface depth를 우리 objective로 가져오지도 않는다.

### 2.5 PGSR — loss 이름보다 비교 대상을 먼저 보여줌

원문: [arXiv v2](https://arxiv.org/abs/2406.06521v2), [로컬](../../../ref/figure_design/pgsr_2406.06521v2.pdf). Fig. 4 / p.4, Fig. 9 / p.8.

- 문제/기여: RGB 재구성만으로 부족한 surface geometry를 planar Gaussian, unbiased depth rendering, single-/multi-view regularization으로 개선한다.
- Fig. 4: Gaussian 렌더 결과를 RGB, distance, normal, depth로 펼치고, 각 loss에 들어가는 실제 이미지/신호를 연결한다. loss 이름만 단독으로 놓지 않는다.
- Fig. 9: reference/neighbor image plane과 대응 patch를 그려 photometric loss를, 공간 재투영 관계를 그려 geometric loss를 설명한다.
- 가져올 원리: appearance는 관측 RGB와 렌더 RGB의 같은 위치를 비교하도록, geometry는 depth evidence와 ray상의 지도 상태를 비교하도록 표현한다.
- 차이: PGSR의 planar primitive, normal-map loss, patch homography는 우리 방법이 아니다. 해당 그림의 구조 전체를 이식하지 않는다.

### 2.6 DS-NeRF — 색과 깊이가 서로 다른 대상을 감독함을 보여줌

원문: [CVF](https://openaccess.thecvf.com/content/CVPR2022/papers/Deng_Depth-Supervised_NeRF_Fewer_Views_and_Faster_Training_for_Free_CVPR_2022_paper.pdf), [로컬](../../../ref/figure_design/dsnerf_cvpr2022.pdf). Fig. 1 / p.1, Fig. 3 / p.4, §3.

- 문제/기여: 적은 영상에서 잘못된 geometry가 생기는 문제에 SfM depth와 불확실성을 이용한 ray-termination distribution 감독을 추가한다.
- Fig. 1: sparse points에서 오는 depth supervision과 camera/RGB에서 오는 color supervision을 서로 다른 분기로 배치한다.
- Fig. 3: density, alpha, transmittance, ray termination을 구분하고, 영상의 국소 영역과 ray 분포를 대응시킨다. density가 여러 peak를 가지는 것과 termination이 여러 peak를 가지는 것은 같지 않다.
- 가져올 원리: 우리 geometry는 단일 평균 depth 이미지의 오차가 아니라 **ray상의 termination/opacity 배치**에 작용함을 보여준다. surface evidence 출처도 따로 둔다.
- 차이: DS-NeRF의 KL matching이 우리 Carve/Hit objective와 같지는 않다. 그림에 `KL`, 정확한 target distribution fitting, 모든 ray의 depth GT를 넣지 않는다.

### 2.7 mip-NeRF 360 — regularizer가 바꾸는 것을 작은 도식으로 설명

원문: [CVF](https://openaccess.thecvf.com/content/CVPR2022/papers/Barron_Mip-NeRF_360_Unbounded_Anti-Aliased_Neural_Radiance_Fields_CVPR_2022_paper.pdf), [로컬](../../../ref/figure_design/mipnerf360_cvpr2022.pdf). Fig. 5–6, PDF p.6, §4.

- 문제/기여: ray상의 분산된 weight와 관련된 floater/background collapse를 distortion regularizer로 다룬다.
- Fig. 6: 1D histogram에 수평·수직 방향 표시를 더해 regularizer가 interval 위치·폭·weight에 어떻게 작용하는지 설명한다. 결과 이미지 없이도 의도된 동작을 읽을 수 있다.
- 가져올 원리: 잘못된 free-space opacity를 공간/깊이축에서 명시한다. 최종 objective가 확정되면 필요한 작용 방향만 표시할 수 있다.
- 차이: compactness를 선호하는 distortion loss는 관측 depth 기반 제약이 아니다. 우리 그림에 무조건 모든 Gaussian을 한 점으로 당기는 화살표를 넣지 않는다. 실제 개선 전후 데이터가 없으면 after map을 생성해서 성과처럼 제시하지 않는다.

## 3. 세 영역을 유지한 구체적 배치

### 왼쪽: 두 영상 종류가 하나의 mapping 후보 집합으로 들어간다

작은 궤적 아래 chronological filmstrip을 놓고 각 영상에 ID와 type badge를 붙인다. 예: `K1, I2, K3, I4, K5`. K는 keyframe, I는 intermediate view다. badge는 색상뿐 아니라 글자로도 구분한다.

두 종류를 서로 다른 독립 stream처럼 그리지 않는다. **한 stream 안의 서로 다른 역할**이고 두 종류 모두 arrived mapping candidates다. 공통 괄호에서 가운데 영역으로 하나의 경로를 보낸다. frontend의 pose/depth는 별도의 회색 기반 경로로 유지한다.

K/I badge 색과 contribution 색이 충돌하지 않게 K=진회색, I=청록으로 둔다. 주황은 새 편입, 파랑은 이번 선택, 보라는 geometry에만 사용한다. selection은 badge를 지우지 않고 바깥 테두리로 표시한다.

### 가운데 위: 정적인 큰 pool 대신, 보존되는 집합의 성장

왼쪽 정렬된 세 행을 세로로 배치한다.

| 완료 update 상태 | 학습 pool 예시 |
| --- | --- |
| S | K1 · I2 · K3 |
| S + κ | K1 · I2 · K3 · **I4** |
| S + 2κ | K1 · I2 · K3 · I4 · **K5** |

새로 추가되는 I4/K5에만 주황 표시를 붙이고 기존 영상은 같은 위치에 남긴다. 따라서 단순 sliding window가 아니라 retention+growth임이 보인다. 이 예시는 추가 관측이 이미 도착해 대기 중인 조건의 설명이며 실제 frame/실험 로그가 아니다. 정확한 시간 간격이나 최종 pool 크기를 주장하지 않는다.

실제 완료 update feedback은 (a)에만 연결한다. 영상이 도착하는 시간축과 완료 update축을 혼동하지 않는다. 집합의 결정 규칙은 `Nmax = min(M, N0 + floor(S/κ))`이지만 overview에 전체 식을 넣을 필요는 없다.

### 가운데 아래: count → probability → stochastic selection

마지막 pool의 영상 순서와 동일한 열에 다음을 수직 정렬한다.

1. 작은 회색 막대: `Selection count n_i`.
2. 파란 막대: `Sampling probability p_i`.
3. 선택된 영상의 파란 외곽선과 다음 updates에 사용할 작은 queue.

두 막대 높이는 반대 관계여야 한다. 같은 선택 단계에서 적게 뽑힌 영상에 더 높은 확률을 주되, 모든 probability가 0보다 크다. **반드시 가장 높은 막대만 뽑지 않아야** stochastic sampling의 뜻이 남는다. 예시로 낮은-count 영상 하나와 중간-count 영상 하나를 선택할 수 있다.

임의의 실제 성능 수치는 쓰지 않는다. 숫자가 꼭 필요하면 현재 softmax에서 계산한 설명용 예시로 별도 표시한다. 비복원 선택 queue는 K distinct views / next K updates이며, K장의 동시 batch update가 아니다. 원래 pool에서 영상을 빼거나 흐리게 처리하지 않는다.

시각적 과밀이 생기면 별도 sample 복사본 수를 줄이고 `One view per update`만 유지한다. 하지만 count와 probability의 구분은 삭제하지 않는다.

### 오른쪽: 지도보다 감독 관계를 읽을 공간 확보

v05의 room map 크기를 조금 줄이고 loss에 충분한 공간을 배정한다. 지도는 한 개의 공유 상태이며, 아래에 두 가지 감독을 배치한다.

- **Appearance:** 동일 viewpoint의 observed/rendered RGB를 나란히 놓는다. 같은 위치의 작은 crop 표시로 비교 관계를 설명한다. 두 이미지가 `L_rgb`로 들어간다. 가짜 성능 비교가 되지 않게 baseline/ours나 품질 수치를 붙이지 않는다.
- **Geometry:** 같은 지도에서 본 ray 단면과 그 아래의 termination-weight profile을 깊이축으로 정렬한다. 가용 depth evidence에서 온 D와 surface uncertainty band를 표시한다. 표면 앞의 불필요한 opacity는 작은 붉은 표시로 강조한다. label은 `Free space`, `Surface evidence`, `Ray termination` 정도로 제한한다.
- 두 loss의 출력은 **같은 map optimization**으로 모인다. Appearance → Geometry의 직렬 연결은 없다. `L_map = L_base + λ L_geom`이 Method의 상위 구조이며 `L_base`에 RGB 이외 기존 항이 남을 수 있으므로 `L_rgb + L_geom`이 완전한 목적함수라고 단정하지 않는다.

작은 merge 지점에는 `Map loss`라고만 적고, caption에서 RGB branch는 기존 mapping supervision을 대표해 보여준 것임을 설명한다. 기하 evidence는 모든 선택 RGB의 depth라는 뜻이 아니라 가용 verified keyframe rays다.

## 4. 버릴 표현과 그 이유

- 큰 영상 grid 하나 + `growing` 문구: 유지/추가/시간 변화를 구분하지 못한다.
- sampling 막대 하나: count인지 probability인지 불명확하다.
- 가장 낮은-count 영상만 강조: stochastic 규칙을 deterministic least-count로 오해하게 한다.
- 고정 K개 박스에 들어가고 앞 영상이 빠지는 애니메이션: retained growing pool을 sliding window로 바꿔버린다.
- 작은 depth map 두 장만 비교: 평균 depth 일치를 넘어선 ray-space 제약이라는 기여가 사라진다.
- Gaussian에 X 표시 또는 지우개: 학습 loss를 hard pruning으로 오해하게 한다.
- loss마다 최적화된 지도 한 개씩 출력: 두 방법이 같은 parameter를 함께 갱신한다는 관계를 잃는다.
- 상세 도식을 모두 크게 배치: 2쪽 초록에서 그림이 본문을 대체하기보다 또 하나의 긴 본문이 된다. growth/sampling/geometry의 최소 관계만 남긴다.

## 5. 근거와 생성 결과를 분리

설계 기준은 [현재 Method](../../../../paper/latex/sec/4_method.tex)의 §3.1–3.3이다. Carve/Hit/조합은 아직 선택이 열려 있으므로, 이번 geometry는 그 공통 문제와 감독 위치를 설명한다. 특정 candidate의 정확한 gradient 동작이나 수렴 성과를 확정하지 않는다.

수상자 팁의 핵심은 본문과 그림의 읽기 순서 일치다. 이번에도 기반 설명 → (a) 성장 → (b) 선택 → (c) 기하 감독 순서를 유지한다. 생성된 도판의 수치/곡선/장면은 성능 증거가 아니며, 실용성은 별도 실제 결과 그림이 맡는다.

새 이미지의 검수에서는 디자인뿐 아니라 K/I 보존, nested pool, count/probability 관계, loss merge, feedback 출처를 확인한다. 생성 결과가 이 설계를 벗어나면 QA에 남기고 실제 Method는 바꾸지 않는다.
