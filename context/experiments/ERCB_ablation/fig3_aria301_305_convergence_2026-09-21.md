# HumanTeck Fig. 3 — Aria301_305 전체 held-out 곡선과 3개 inset 후보

## 요청과 실행

사용자가 선택 검토할 frame 1180 / 1220 / 980의 Fig. 3 세 버전을 만들기 위해,
기존 normalized-variance Ours와 native VIGS baseline을 seed 0으로 재실행했다.
원래 run은 endpoint map만 보관하므로 신규 output에 50 step마다 PLY를 저장했다.
학습 코드/정책은 수정하지 않고 외부 wrapper가 완료된 Gaussian Adam step을 관측했다.
GPU에 다른 compute process가 없는 것을 확인한 뒤 실행했다. desktop graphics process는 유지했다.

- 기존 pair: `results/experiments/exp94_normalized_metric_v2_fixed_eval/aria/aria301_305/`
- 신규 pair: `results/figure03_convergence_20260921/aria301_305/`
- 원본 자료는 보존. Carve off, causal frozen tracker, unbounded fixed-work mapping 조건.
- 양쪽 총 training renders 17,620, step Ours 1,344 / baseline 1,376로 기존과 동일.
- 원본 active training source hash 일치. 변경된 옛 panel launcher 3개는 이번 실행에서 사용하지 않았다.
- baseline은 새 Ours runtime의 동일 render-credit 계약을 따른다.
- Snapshot 저장 시간: Ours 3.52초 / baseline 4.20초. 실행 시간은 속도 benchmark로 사용하지 않는다.

## 평가

Ours 27개, baseline 28개, 총 **55 checkpoint × 동일 held-out 539뷰**를 평가했다.
일부 학습 step에서 map reset이 있어도 누적 optimizer step은 다시 0으로 만들지 않는다.
PSNR은 각 이미지의 기존 GT>0 mask를 적용해 계산한 값의 산술평균이다.
동일 원본 전처리·평가 pose·held-out UID 집합을 유지했고, 학습 중 평가를 수행하지 않았다.
평가 pose는 기존 evaluator의 고정 post-EOS trajectory이며 mapper supervision에 제공하지 않는다.
양쪽 held-out mapping/origin overlap 0, post-EOS optimizer updates 0이다.

| 기준 | Baseline | Ours | Ours − Baseline |
|---|---:|---:|---:|
| 600 step | 13.8302 | 14.5427 | +0.7125 |
| 1,000 step | 16.6069 | 17.6259 | +1.0190 |
| 1,300 step | 17.6621 | 23.2054 | +5.5433 |
| 각 run 마지막 | 21.8552 | 25.0936 | +3.2383 |

원래 endpoint 대비 PSNR 변화는 baseline −0.07151, Ours −0.01886 dB.
Gaussian 수는 baseline 197,515→197,319, Ours 214,288→214,221로 완전 동일 재현은 아니다.
새 곡선은 새 run의 endpoint까지 일관되게 사용했고, 이전 endpoint로 마지막 점을 교체하지 않았다.

## 핵심 해석 제한 — 늦은 pose correction

같은 causal archive의 event 145 pose correction은 Ours 1,295–1,317 step,
baseline 1,327–1,347 step에서 처리됐다. 1,300 step inset은 Ours는 이 이벤트를
처리 중이고 baseline은 아직 처리 전이므로 큰 품질 차이가 pose 상태 차이를 포함한다.
전반부에도 event 120 pose correction(Ours 1,057–1,079 / baseline 1,083–1,103)이 있다.
고정 평가 pose 대비 map alignment가 변하는 영향을 optimizer 자체 수렴과 분리하지 않았다.

따라서 이 도판은 **전체 mapping 시스템의 iteration별 지도 품질**을 보여준다.
ERCB만의 순수 수렴 가속·동일 입력 prefix의 refinement 가속·wall-clock 가속 근거로 쓰지 않는다.
전체 render 예산은 동일하지만 각 중간 iteration의 관측 범위와 render 수는 다르다.
1,300 step의 입력 prefix는 Ours 2632 / baseline 2578이다.
후반 보정 구간을 회색으로 표시하고 percentage speedup은 주장하지 않는다.
Same PSNR 화살표는 baseline endpoint에 대한 **사후 선형 보간 도달 위치 비교**다.
50-step 간격 사이의 실제 crossing 시점은 측정되지 않았다.

## 도판

세 도판은 같은 539-view 곡선·축·색·600/1000/1300 checkpoint를 공유한다.
Inset만 A=frame1180, B=1220, C=980으로 다르며 모든 시점에서 해당 카메라/ROI를 고정했다.
ROI는 의미 있는 책상/의자 영역을 고른 것으로, 세 variant 간 crop PSNR을 최대화하지 않았다.
실제 checkpoint 렌더링을 그대로 삽입했고 생성형 이미지·블러 합성·선명화는 사용하지 않았다.

- [결과 및 세 버전](../../../humanteck/sections/02_method/figure03/output/README.md)
- CSV/JSON/per-view 원본: `results/figure03_convergence_20260921/aria301_305/evaluation/`
- checkpoint PLY/provenance: 신규 pair 각 arm의 `checkpoints/`, `capture_manifest.json`
- 단일 단 폭 86.49 mm, 높이 63.42 mm. SVG→Inkscape PDF→Poppler PNG 순서로 검수.

## 실패·수정 기록

### 2026-09-21 추가: frame 1180 선택·평가 범위 진단

사용자가 frame1180을 선택했다. 저장된 per-view PSNR의 CPU 재집계 결과,
1180 자체도 600/1000/1250 step 차이가 약 +0.16/+0.10/+0.02 dB인 반면
1300에서 +15.53 dB다. 1100–1300의 고정 41뷰도 후반 급증은 그대로다.
따라서 전체 trajectory 평균만 바꾸어 점진적 수렴 격차가 드러난다고 볼 수 없다.
공통 입력·pose 상태의 local refinement 추가 실험을 제안했으며 아직 실행하지 않았다.
→ [진단 CSV·설계](../../../humanteck/sections/02_method/figure03/analysis/metric_redesign_2026-09-21.md)

- 최초 source-lock 검사는 사용하지 않는 panel launcher 3개의 변경까지 검출해 학습 시작 전 중단됐다.
  실행하지 않는 launcher만 별도 기록하고 active source lock은 유지했으며 환경 구성은 명시적으로 복제했다.
- 최초 도판의 초기 inset이 곡선에 근접해 위로 옮겼으나 header가 plot 상단선과 겹쳤다.
  inset y를 150으로 조정한 최종 PDF에서 header와 곡선의 간격을 확보했다.
- 실험은 완주했으나, **큰 후반 차이를 순수 학습 수렴의 증거로 해석하는 주장은 미검증**이다.
