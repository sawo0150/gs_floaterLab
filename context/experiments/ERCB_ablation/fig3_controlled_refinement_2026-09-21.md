# Fig.3 — 공통 입력 event의 controlled refinement

## 사전 고정 설계

사용자가 전체 trajectory 평가 대신 관측 이후 refinement 방식의 실제 figure 제작을 요청했다.
기존 native online 곡선과 별도 실험이며 기존 세 도판·run은 보존한다.

- 장면: Aria301_305, seed0. Inset frame1180.
- PSNR을 확인하기 전에 입력 frame 500/950/1400/1850/2300 이후 첫 keyframe update를 선택.
  공통 event17/38/68/98/119, 실제 입력 prefix513/960/1411/1851/2302.
- 기존 mapper를 원래 정책으로 각 event 끝까지 재실행한 후 독립 분기. 이후 입력은 처리하지 않음.
- 두 방법은 각자의 online map/optimizer 상태로 시작. 동일 초기 map에서 분기한 sampler ablation은 아님.
- Ours: 기존 appearance replay `idle_map_rr_step(iters=1,batch_size=1)`와 ERCB.
- Baseline: native vanilla `map(current_window,iters=1,max_viewpoints=1)`.
  원래 multi-view iteration을 1-view iteration으로 바꾼 controlled baseline이며 별표로 표시.
- 추가 0/5/10/20/30/45/60/90/120 Gaussian Adam step에서 PLY 저장.
  양쪽 매 step 실제 training render=1인지 확인. 별도 phase cutoff/topology freeze 도입 없음.
  각 방법의 기존 topology/gradient-scope 정책은 유지.
- held-out은 직전 300 input frame 범위 중 해당 시점 KF pose로 보간 가능한 고정 집합.
  Mapping supervision과 겹침 0. Input packet은 causal archive를 공유.
- evaluator pose는 현재 KF pose 사이의 SE3 보간. 두 arm이 같은 pose/UID 집합인지 검증.
  보간 방식은 기존 causal dense pose 방식과 동일. post-EOS trajectory 사용 없음.
- 각 event의 고정 view 평균을 구하고 5개 event를 동일 가중 평균. 모든 x에서 동일 event/cohort 사용.
- 이미지는 event68 / frame1180 / 추가0,30,120 step, 기존과 같은 crop.

## 주장 범위

입력과 평가 pose를 고정한 추가 refinement 진단이다. 원래 strict streaming의 zero-tail
평가나 native end-to-end 속도 benchmark로 제시하지 않는다. training pool과 gradient scope,
초기 map 품질 등이 달라 ERCB만의 효과로 해석하지 않는다. 최종 gap이 크더라도 추가
update 이전 gap과 구분하며 수렴률/threshold 도달은 실제 곡선을 확인한 뒤 판단한다.

## 실행 경로

- 실험: `results/figure03_refinement_20260921/aria301_305/`
- 사전 설계: `plan.json`; active source 검증: `source_audit.json`
- 코드: `humanteck/sections/02_method/figure03/scripts/*refinement*.py`
- GPU compute 점유가 없는 것을 확인한 뒤 10개 분기를 순차 실행. 다른 프로세스 종료 없음.

## 결과

10/10 분기, 90/90 map 평가 완료. Held-out cohort는 45/59/56/56/58뷰,
합계 274개 서로 다른 view다. 총 4,932회 평가했다. 모든 pair의 평가 pose 차이 0,
UID 집합 동일, held-out 학습 overlap 0, 추가 step/render=1:1 확인.
분기 시작까지 training render 차이는 1/7/10/0/6회로 완전히 같지는 않으며,
추가 구간에서는 정확히 양쪽 120/120이다.

| 추가 iteration | Baseline PSNR | Ours PSNR | 차이 |
|---:|---:|---:|---:|
| 0 | 21.4908 | 21.4359 | −0.0549 |
| 30 | 21.5272 | 21.4376 | −0.0896 |
| 120 | 20.7582 | 21.3775 | +0.6193 |

시작 대비 Ours **−0.0584 dB**, baseline **−0.7326 dB**.
**빠른 수렴 가설은 이 실험에서 입증되지 않았다.** 최종 양의 gap을 수렴 가속이라고
해석하지 않는다. Baseline Gaussian 수 변경이 event38/119의 60–90 step,
event17/68/98의 90–120 step에 관측돼 PSNR 하락과 겹친다. 원인별 기여는 미분리다.
Ours는 event68 하나만 +0.0657 dB이고 나머지 4개 event는 소폭 음수다.
Inset frame1180은 Ours 25.0472→25.3876, baseline 23.8346→20.8257 dB다.

시작점이 이미 해당 event의 mapping 완료 이후이며 Ours는 appearance replay,
baseline은 single-view로 조정된 native map이다. 따라서 이 결과로 다른 refinement
설계 전체가 불가능하다고 일반화하지 않는다. 현재 분기는 native streaming 성능표를
대체하지 않는 진단용 도판으로 보존한다.

- [도판·SVG·PDF·CSV·캡션](../../../humanteck/sections/02_method/figure03/output/REFINEMENT.md)
- `output/qa/refinement_validation.json`: pose/step/render/평균/PDF 검증 결과.
