# 수렴 그래프 문헌 조사와 incremental 평가 제안

2026-09-20. 사용자 질문: 대표 장면만 실험할지, incremental PSNR의 평가 범위,
15/30/60 updates/interval을 어떻게 그릴지. 신규 학습이나 성능 판정은 수행하지 않았다.

## 확인한 문헌

- **3DGS-LM**, Fig.1/4 및 §4: 대표 장면의 PSNR–시간 곡선과 13-scene benchmark를
  함께 사용한다. Fig.4는 Garden에서 initialization iteration 수를 바꾸는 진단이다.
  고정 데이터셋의 offline optimization이며 growing-map 평가를 그대로 해결하지 않는다.
  https://arxiv.org/html/2409.12892v2
  https://lukashoel.github.io/3DGS-LM/static/3DGS-LM_paper.pdf
- **3DGS²**, Fig.4 및 §5: 6개 대표 사례의 local optimization/loss 감소 곡선을
  제시하며 별도 benchmark를 함께 보고한다. 그림의 감소하는 loss를 held-out PSNR로
  바꾸어 설명하지 않는다. 대표 그림과 전체 검증의 역할이 다르다는 참고다.
  https://arxiv.org/html/2501.13975v2
- **CaRtGS**, Fig.2 및 §III-A2: Replica Room2에서 keyframe별 optimization 횟수와
  PSNR의 long-tail을 진단한다. 시간에 따른 동일 held-out 대상의 수렴 곡선이 아니며,
  학습 keyframe PSNR을 우리 held-out 품질 지표로 대체하지 않는다.
  https://arxiv.org/html/2410.00486v3
- **HAMMER**, Fig.5 및 §IV-B2: Home/Basement 두 실세계 장면에서
  x=Map Optimization Step, y=Evaluation PSNR. 장치당 10개 고정 held-out frame을 사용한다.
  본문은 evaluation views가 전체 장면을 포괄하여 coverage의 영향이 있음을 설명한다.
  이는 online에서 전체 고정 evaluation set을 쓰는 실제 사례다. 다만 coverage와
  기존 관측의 refinement를 분리하는 지표는 아니다.
  https://arxiv.org/html/2501.14147v2

아래는 위 논문들의 공통 표준을 인용한 것이 아니라 우리 실험에 대한 설계 제안이다.

## 실험 범위와 표시 범위를 구분

본 검증은 사전 고정한 전체 scene panel에서 두 비교를 수행한다. 현재 후보는 기존
19-scene ablation panel이다. 본문의 상세 곡선은 소수 대표 장면을 사용할 수 있으나
가장 좋은 scene/seed만 선택하지 않는다. 복수 seed의 평균과 변동을 제시하고, 전체 장면
결과/곡선을 보충자료에 공개한다. 대표 한 run으로 일반적인 수렴 가속을 확정하지 않는다.

비교 A: KF-only+공통 random 대 KF+중간 RGB+동일 random.
비교 B: 동일 view pool·admission trace에서 random 대 현재 Method의 ERCB.
Random은 현재 표와 맞추면 random reshuffling이며 independent uniform sampling과 구별한다.

## 두 개의 진행 축

입력 event e와 누적 optimizer update u를 구분한다. 일정한 B updates/event replay에서
대략 u=B e이나 bootstrap/예외 event는 실제 로그를 사용한다.
같은 u에서 B=15와 B=60은 이용 가능한 관측 범위가 다르다. 따라서 6개 선을 한 iteration
축에 겹친 뒤 순수 optimizer efficiency라고 해석하면 안 된다.

- 같은 B 안의 두 arm: 같은 u에서 arrival 범위도 맞출 수 있다.
- 다른 B 사이: 같은 e는 같은 입력 진행을 뜻하나 같은 연산량을 뜻하지 않는다.
- u/u_final은 이 replay에서 대체로 입력 진행률에 가깝다. 실제 시간이나 iteration 절감률이 아니다.

## y축의 세 가지 의미

1. **고정 전체 held-out PSNR**: 각 checkpoint의 지도가 최종 평가 궤적을 얼마나 설명하는가.
   미래 미관측 영역의 coverage를 포함한다. 무효한 지표는 아니지만 순수 refinement와 다르다.
   held-out 미래 영상은 평가에만 사용하며 mapper/scheduler로 환류하지 않는다.
2. **현재까지 도착한 held-out prefix의 PSNR**: 지금까지 본 궤적에 대한 map quality.
   두 arm의 같은 입력 시점 비교에는 의미가 있지만 평균 대상이 계속 변해 곡선의 기울기만으로
   convergence rate를 판단할 수 없다. 어려운 새 구간의 추가로 평균이 하락할 수 있다.
3. **고정 held-out view 집합의 arrival 이후 PSNR**: 한 번 정한 평가 대상을 이후 map
   checkpoint에서 반복 렌더링한다. 과거/미래 영역을 한꺼번에 평균하는 문제를 줄이며
   관측 이후 appearance refinement를 더 직접적으로 측정한다.

## 권장 주 그림: arrival 기준으로 정렬한 refinement

모든 arm이 공유하는 sensor/KF event를 기준으로 평가 전용 held-out view h의 기준 event a(h)를
정한다. 예를 들어 해당 frame timestamp 이상인 첫 공통 arrival event를 사용한다.
이는 공간 영역의 최초 관측을 보장하지 않으며, 그 주장이 필요하면 별도 공통 visibility
판정이 필요하다. h는 모든 mapping supervision에서 계속 제외한다.

각 budget B에서 h의 기준 event에 대응하는 완료 update u_B(h)를 기록한다.
고정된 h를 map M_B(u_B(h)+d)에서 다시 렌더링한다:

`Q_B(d) = mean_h PSNR(render(M_B(u_B(h)+d), pose_h), RGB_h)`.

- x: 평가 view의 기준 arrival 이후 누적 mapping updates d.
- y: 고정된 평가 view들의 held-out PSNR. train loss나 선택된 training view PSNR이 아니다.
- 각 d에서 다른 view 집합을 평균하지 않는다. 표시 horizon 전체를 EOS 전에 관찰할 수 있는
  공통 집합을 고정한다. 후반 view의 짧은 추적은 별도 분석으로 보고하고 tail 학습은 하지 않는다.
- 장면마다 view 평균을 먼저 계산하고 scene을 동일 가중으로 평균할 수 있다. scene 개수와
  view 개수, seed 불확실성을 구분한다. 긴 scene이 모든 통계를 지배하지 않게 한다.
- 실제 초기 quality가 arm마다 다르면 d=0 값을 그대로 보여준다. 시작점을 임의로 같게
  정규화하지 않는다. 이는 online policy 결과의 refinement이며 공유 상태에서 분기한
  순수 optimizer microbenchmark와 다르다.
- map은 계속 incremental하게 성장한다. 두 arm의 공통 input schedule이 유지되는 같은
  B 안에서 비교한다. 다른 B는 같은 d에서도 도착 관측이 달라 직접 같은-work 비교가 아니다.
- checkpoint가 성기면 정확히 d에서 측정했다고 주장하지 않는다. 사전 grid와 실제 snapshot
  좌표를 저장하고, 보간은 추정임을 표시한다. 기존 로그가 부족하면 재계측이 필요하다.

두 행(관측 집합 비교 / sampler 비교) × 세 열(B=15/30/60)의 구성을 권장한다.
subplot마다 2개 선과 seed 변동만 표시한다. 같은 장면의 축 범위는 공유해 비교 가능하게 한다.
본문에서 모든 scene × budget 패널을 펼칠 필요는 없다. 전체 scene의 arrival-aligned 평균을
주 그림으로 하고 대표 scene과 전체 개별 곡선을 보충하거나, 대표 scene 곡선을 본문에 두되
전체 검증을 별도 요약할 수 있다.

## 반드시 15/30/60을 한 좌표계에 보여줄 때

x를 공통 기준 event 이후의 **입력 event 경과 수** l로 바꾸고, 동일 h를 a(h)+l 시점에
평가한다. 색으로 B, 선 종류로 방법을 구분한 6개 곡선이 가능하다. 각 l에서 주어진 관측의
범위는 같고 B에 따라 투입 연산량이 다르다. 제목은 budget별 online refinement로 두며
같은 compute에서의 속도 비교라고 부르지 않는다. 가독성상 subplot 분리가 우선이다.

별도 전체 스트림 진행 그림은 x=sensor timestamp/frame index 또는 공통 normalized
input progress, y=명시한 prefix/전체 held-out quality로 만들 수 있다. 이것은 online
map-quality evolution이며 주 refinement 곡선을 보완한다.

x=B(15/30/60), y=각 run 최종 PSNR도 유효한 budget–quality 그래프지만 수렴 곡선은 아니다.
예산별 endpoint 3개를 연결하여 한 실행의 학습 궤적인 것처럼 표현하지 않는다.

## Method 연결

§3.1은 추가 RGB supervision이 관측 이후 품질 개선에 유용한지 검증하고,
§3.2는 같은 supervision의 update allocation이 그 개선을 촉진하는지 검증한다.
KF-only 대 모든 dense의 비교만으로 κ-growth의 최적성/효과를 확정하지 않는다.
현재 geometric objective의 빠른 수렴은 이 두 appearance ablation만으로 입증되지 않는다.
