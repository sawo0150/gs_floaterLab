# gsSLAM vs vanilla VIGS-SLAM: B/C metric 비교 계획

작성: 2026-09-14  
상태: **입력 lock 완료 — D1-native render-matched B protocol로 정정, active Full 확정 전**

> **2026-09-17 metric benchmark v2 상태:** R4 shortfall을
> normalized-variance ERCB로 교체하는 전체 17-scene B-track 검증은
> RPNG `table_01` 첫 direct-file gate에서 **25.6197→20.7874dB**로
> 급락해 중단했다. 동일 work/held-out 불변 검증은 통과했지만 새 vanilla
> pair와 후속 scene은 실행하지 않았으므로 normalized 모델의 전체 benchmark
> 이득은 주장하지 않는다. 이 문서의 B/C 정의는 유지하며 v2 실행 계약·결과는
> [별도 기록](../benchmark_custom/metric_benchmark_v2_normalized_variance_20260917/README.md)에 둔다.

## 0. 결론

논문 본문의 핵심 비교는 다음 두 실험으로 제한한다.

| 실험 | 핵심 질문 | 고정하는 것 | 방법에 맡기는 것 |
|---|---|---|---|
| **B. Mapping-only isolation** | 같은 online 관측과 총 rendering work에서 gsSLAM mapper가 더 좋은가? | D1이 실제 service한 tracker packet/KF, held-out, 총 physical training render 수 | 각 방법 고유 loss, Adam grouping, replay와 topology 정책 |
| **C. Strict streaming system** | 실제 입력 속도와 deadline에서도 개선이 유지되는가? | sensor stream, hardware, deadline, evaluator | tracking/KF/mapping/skip 정책 |

B는 **방법론의 mapping 효과**, C는 **실시간 시스템 효과**를 증명한다. Paper reproduction은
appendix sanity check로만 사용하고, unbounded upper bound는 strict 결과 해석에 꼭 필요할 때만
선택적으로 실행한다.

---

## 1. VIGS-SLAM 논문 방식과 이 계획의 차이

VIGS-SLAM 논문은 구현체별 KF 수를 같게 고정하지 않았다.

- 각 방법은 자체 tracker와 KF selection을 사용하므로 sequence별 KF 수와 timestamp가 다를 수 있다.
- `10 mapping iterations per new keyframe`은 VIGS 자체 설정이며 모든 baseline에 강제한 공통
  budget이 아니다.
- 따라서 VIGS 내부에서도 KF가 많아지면 sequence 전체 mapping iteration과 supervision 양이
  늘어난다.
- rendering 평가는 어떤 방법에서든 KF였던 view를 제외하는 all-method non-KF 집합을 사용하지만,
  그 공통 UID 목록은 공개 artifact에서 복구되지 않는다.
- 논문의 비교에는 tracker, KF policy, mapper와 총 mapping work의 차이가 함께 들어간다.

이 방식은 자체 설정을 포함한 system comparison에는 적절하지만 mapper isolation은 아니다.
따라서 우리 계획은 다음처럼 분리한다.

- **B:** 모든 방법의 KF 수와 timestamp를 동일하게 고정한다.
- **C:** 방법별 KF 수를 고정하지 않는다. KF selection과 그 계산비도 system design으로 평가한다.

우리 B/C 수치는 VIGS paper table과 동일 protocol이라고 주장하지 않는다. 개선량은 동일 B/C
harness에서 다시 실행한 local vanilla VIGS를 기준으로 계산한다.

---

## 2. 두 실험의 공통 불변 조건

### 2.1 데이터와 인과성

- 입력은 timestamp 오름차순만 허용한다.
- timestamp `t`의 update는 `t` 이후 frame, KF, pose, depth, residual을 참조할 수 없다.
- MPS 후처리 trajectory/depth/point cloud와 GT pose/depth는 mapping 입력으로 금지한다.
- calibration은 sequence 시작 전에 고정된 값만 허용한다.
- RGB 해상도, crop, color conversion과 normalization을 방법 간 동일하게 고정한다.

### 2.2 공통 held-out

- 평가 UID는 실험 전에 manifest로 고정한다.
- held-out RGB는 loss, birth, densification, replay, selector score, residual cache와 pruning evidence에
  절대 사용하지 않는다.
- tracker가 held-out RGB를 localization에 사용한 것은 허용하되 이를
  **mapping-disjoint held-out**이라고 명시한다.
- PSNR/SSIM/LPIPS는 B와 C에서 동일 evaluator와 동일 UID로 계산한다.
- metric render 자체는 실행시간에서 제외하며 map이나 pose를 변경할 수 없다.

### 2.3 실행 환경

- 동일 GPU, CUDA, PyTorch, rasterizer commit과 precision을 사용한다.
- TensorRT tracker를 쓰는 실험은 engine hash, build GPU, profile과 fallback 여부를 기록한다.
- random seed와 deterministic 옵션을 manifest에 기록한다.
- dataset별 tuning은 금지하고 calibration·resolution처럼 필요한 adapter만 허용한다.
- failure를 평균에서 숨기지 않고 성공 scene 수와 실패 수 `F`를 함께 적는다.

---

## 3. B — Mapping-only isolation

### 3.1 목표와 해석 범위

B는 다음 주장만 검증한다.

> 동일한 causal tracking state, KF와 mapping work를 사용할 때 gsSLAM의 supervision 축적,
> replay, loss와 topology 정책이 vanilla VIGS mapper보다 높은 held-out 품질을 만든다.

B는 tracker 실행시간과 tracker--mapper 자원 경쟁을 격리하므로 **mapping mechanism의 품질**만
주장한다. B의 wall time만으로 real-time mapper나 end-to-end real-time SLAM을 주장하지 않는다.
실제 자원 경쟁과 deadline은 C에서만 검증한다.

### 3.2 Frozen causal tracker archive

official VIGS tracker를 pure-online으로 한 번만 실행하고 immutable archive를 만든다. packet은
최소한 다음 필드를 가진다.

- sequence ID, frame UID, sensor timestamp
- 전처리된 RGB의 hash와 원본 RGB 참조
- 해당 시점까지 online으로 추정한 pose
- online depth, confidence와 유효 mask
- 현재 시점에서 확정된 KF 여부
- calibration ID와 해상도
- packet 생성 시 사용한 code/config/engine hash

금지되는 archive 필드:

- final BA 또는 trajectory filling 뒤의 pose
- 미래 KF를 사용해 수정한 depth/normal
- 전체 sequence를 본 뒤 계산한 priority, visibility와 residual
- MPS/GT에서 가져온 geometry

archive 생성 후 내용과 순서를 바꾸지 않고 vanilla, dense control, gsSLAM이 같은 hash를 읽는다.

### 3.3 KF와 supervision 집합

- B에서는 frozen archive의 동일 KF UID와 동일 KF timestamp를 모든 방법에 강제한다.
- current/window KF supervision의 UID와 순서도 동일하게 유지한다.
- dense 후보는 그 시점까지 도착한 mapping-eligible non-KF RGB만 사용한다.
- held-out과 KF는 dense replay pool에 넣지 않는다.
- 같은 UID가 KF pool과 dense pool에서 중복 service되지 않도록 audit한다.
- vanilla가 dense 후보를 사용하지 않는 것은 official policy로 인정하지만, 모든 방법에는 동일한
  후보 접근 가능성을 제공한다.

### 3.4 Primary: D1-native render-matched causal mapper isolation

논문의 주 B 표는 **Adam step 수가 아니라 실제 training rasterization 수**를 맞춘다. 여러 view의
loss를 한 Adam step에 합치는 vanilla와 한 dense view마다 별도 Adam step을 하는 D1은 같은 step
수로 만들면 서로 다른 optimizer가 되기 때문이다. `vanilla 10회 + dense 3회` 같은 공통 합성
scheduler도 만들지 않는다.

1. 먼저 gsSLAM Full을 의도한 native causal scheduler로 실행한다. 일반 frontier, 별도 dense replay,
   optimizer grouping과 topology는 원본 D1 계열 구현의 의미를 유지한다.
2. 이 실행에서 실제 service한 tracker packet event ID, KF UID와 모든 mapping render 호출을
   append-only ledger로 고정한다. 미래 입력, held-out, terminal update는 0이어야 한다.
3. official vanilla는 정확히 같은 packet/KF trace를 다시 받고, D1의 **총 physical render 횟수**만큼
   자기 native KF window/global sampler와 RGB-D·normal loss로 학습한다. D1 dense view를 vanilla에
   넣거나 dense update를 흉내 내지 않는다.
4. vanilla의 native iteration은 causal 누적 render credit을 넘지 않는 범위에서만 실행한다. 끝에서
   나눠떨어지지 않는 잔여 view만 한 번의 partial native update로 맞춘다. event별 Adam 수는 같게
   강제하지 않는다.
5. D1에서 render/backward 뒤 Adam 직전에 preempt된 횟수가 있으면 vanilla에는 그 수까지 유효한
   KF 학습 credit으로 준다. 이는 baseline에 유리한 보수적 처리이며 committed/attempted 수를 모두
   공개한다.
6. B는 tracker 경쟁을 제거한 quality isolation이다. D1 reference trace가 실제 deadline 안에서
   생성 가능한지는 C의 native 1.0×/1.5× 실행에서 별도로 검증한다.
7. birth와 topology 비용은 render 수에 포함되지 않으므로 횟수, wall/GPU time, peak VRAM,
   Gaussian 수를 별도 보고한다.
8. 마지막 causal event 뒤 optimizer, birth, densify/prune와 terminal replay는 0회다.

과거 exact D1의 auto-freeze 결과는 이 계약을 검증하는 provenance diagnostic일 뿐 최종 논문
Full이 아니다. Active Full은 장면별 frame/iteration/count cutoff 없이 final-v7의 관측 기반
unknown-horizon state를 사용한 뒤 자기 native render ledger를 새로 생성해야 한다.

### 3.5 Secondary: mapper-only time-throughput diagnostic

동일 `1.5×` 또는 `1.0×` wall-clock을 mapper에 단독 배정하는 결과는 보조 진단으로만 둔다.
동일 archive, reserve, queue/drop policy와 zero-tail을 사용해 구현별 처리율과 병목을 설명할 수는
있지만 tracker와의 실제 CPU/GPU 경쟁이 없으므로 논문의 real-time 주장이나 B primary 품질표로
쓰지 않는다. 실제 실시간 판정은 C에만 둔다.

### 3.6 B 비교 행

| 행 | 입력·KF | Work budget | 목적 |
|---|---|---|---|
| **B0 Official vanilla VIGS** | Full D1과 동일한 packet/KF trace | Full D1의 총 render 수를 vanilla native KF update로 소비 | 주 local baseline |
| **B1 Custom vanilla parity control** | B0와 동일 | B0 render ledger 재현, contribution 전부 off | custom code path confound 제거 |
| **B2 D1 backbone** | B0와 동일 + causal non-KF RGB | Full과 동일 render ceiling | 별도 dense replay와 online birth backbone |
| **B3 Proposed pre-carve** | B2와 동일 | native D1 scheduler가 만든 render ledger | C1 + IMU dense-pose + C2 ERCB + online-rank birth + observation-based adaptive topology |

B3가 strict held-out 27dB를 통과한 뒤에만 C3 causal carving을 붙여 최종 **Full**로 승격한다.
그 전에는 B3를 `Full`이라고 부르지 않는다. 최종 Full 확정 뒤에는 `Full−C1`,
`Full−IMU-dense-pose`, `Full−C2`, `Full−online-rank-density`,
`Full−adaptive-topology`, `Full−C3`를 같은 Full render ceiling에서 실행한다.

B3의 현재 development 후보값은 dataset 이름이나 전체 길이를 사용하지 않는다. C1은 temporal
maximin으로 정렬한 causal interval마다 **global seed 전체 1장만** 무료로 허용하고, 이후 완료된
dense-view update 22회당 1장을 admit한다. waiting candidate가 없으면 남은 credit을 폐기한다.
C2는 count-softmax ERCB `beta=0.02, block=128`, dense pose는 오른쪽 KF timestamp까지의 raw gyro와
고정 `Tcb`만 사용한다. 이 숫자들은 validation을 열기 전에 development panel에서 채택/기각한다.

### 3.7 B 보고 지표

품질:

- held-out PSNR, SSIM, LPIPS
- scene macro-average, median, 최저 scene과 실패 수
- floater 단계에서는 동일 region GT metric

work와 자원:

- total/committed physical training render와 physical Adam/optimizer step
- regular KF view-update와 auxiliary dense view-update
- unique KF/non-KF supervision UID
- UID별 service count와 keyframe 반복 수
- topology event와 final Gaussian 수
- mapper wall-clock, GPU time과 peak VRAM

B pass 조건:

- archive/KF/held-out hash 동일
- D1과 vanilla의 총 physical training render 정확히 일치; Adam 수는 보고만 하고 강제하지 않음
- vanilla dense path 0, D1 dense view를 vanilla KF view로 바꾸지 않고 vanilla native sampler만 사용
- D1이 실제 service한 packet event와 KF UID 집합을 vanilla가 정확히 재현
- 미래 UID access 0
- held-out mapping access 0
- unbudgeted terminal update 0
- final event snapshot과 post-EOS update counter 존재

### 3.8 본 실험 전 vanilla parity gate

custom repo 경로 자체가 결과를 바꾸지 않는지 확인하기 위해 B0를 두 구현 경로로 먼저 실행한다.

- `official_vanilla`: official VIGS commit의 Gaussian mapper
- `custom_vanilla`: custom repo를 사용하되 dense replay, custom density, adaptive topology와
  contribution을 모두 끄고 official YAML/policy를 적용한 mapper
- 최소 두 development 장면을 사용하며 RPNG와 UTMM을 각각 하나 이상 포함한다.
- 두 경로는 동일 archive SHA-256, held-out manifest, seed와 D1 render ledger를 사용한다.

결과를 보기 전에 다음 통과 기준을 고정한다. **각 장면이 전부** 만족해야 한다.

- fixed-held-out `|delta PSNR| <= 0.15 dB`, `|delta SSIM| <= 0.005`,
  `|delta LPIPS| <= 0.01`
- total rasterized view-update가 정확히 일치하며, optimizer step 차이는 공개한다. final Gaussian 수
  차이는 parity control에서만 상대 `<= 5%`
- processed packet과 unique mapped UID 집합 정확히 일치; drop/preemption 0
- held-out/mapping overlap, future access와 post-EOS Gaussian update는 양쪽 모두 0

하나라도 넘으면 B0--B3를 시작하지 않고 first-divergence event와 mapper state를 추적한다.
최소 pair는 UTMM `square-2`와 RPNG `table_01`이며, 경계 결과나 실패가 있으면 나머지 dev 장면인
UTMM `ego-drive`, RPNG `table_06`까지 확대한다.

---

## 4. C — Strict streaming system

### 4.1 목표와 해석 범위

C는 다음 주장을 검증한다.

> 센서가 실제 속도로 계속 도착할 때 각 방법의 tracking, KF selection과 mapping policy가
> deadline 안에서 어느 품질의 지도를 만드는가?

C에서는 구현체마다 KF 수가 달라도 된다. KF를 적게 선택해 시간을 확보하거나 많이 선택해
품질을 높이는 trade-off 자체가 system 결과에 포함된다.

### 4.2 Sensor producer와 ingress

- 모든 방법에 동일한 RGB+IMU stream을 원본 timestamp 속도로 방출한다.
- offline storage jitter를 제거하기 위해 producer가 decode한 동일 packet을 공급하되 producer는
  consumer 속도에 맞춰 멈추지 않는다.
- harness backpressure와 harness drop-oldest/newest는 금지한다.
- 방법 자체의 causal frame/KF skip은 허용하지만 policy와 모든 count를 공개한다.
- prebuilt TensorRT engine과 calibration load는 sequence 시작 전에 완료할 수 있으며 양 방법에
  동일하게 적용한다.

### 4.3 방법별 KF 정책

- vanilla VIGS는 official KF policy를 사용한다.
- gsSLAM은 자체 causal KF/admission policy를 사용할 수 있다.
- 공통 KF 수나 timestamp를 강제하지 않는다.
- 각 scene에서 selected KF 수, 간격 분포, mapping-call 수, optimizer step과 rendered view 수를
  보고한다.
- KF 수 차이로 생긴 품질과 runtime 변화는 제거 대상이 아니라 C의 system 결과다.

### 4.4 Deadline과 zero-tail

- 최종 real-time primary는 native **1.0× capture duration**이다.
- 현재 개발 milestone은 fixed **1.5× capture duration**이며 bounded-streaming으로 표기한다.
- deadline 시점에 map snapshot을 고정한다.
- deadline 뒤 optimizer, densification, birth, pruning과 pose/map refinement는 0회다.
- final frame을 deadline 전에 처리하지 못하거나 queue가 남으면 strict FAIL이다.
- backlog를 나중에 drain한 map은 원인 분석에는 쓸 수 있지만 strict 성공 PSNR로 승격하지 않는다.

### 4.5 C 보고 지표

품질과 성공:

- deadline snapshot의 held-out PSNR, SSIM, LPIPS
- strict pass/total, 실패 사유와 scene macro-average
- tracking ATE/Recall은 full tracking+mapping claim일 때 함께 보고

streaming과 work:

- emitted, decoded, tracked, mapped, method-skipped와 method-dropped frame 수
- selected KF 수와 KF interval distribution
- tracking/map queue peak와 EOS queue depth
- mean/p95/max latency와 deadline lateness
- optimizer step, rasterized view-update와 topology event
- final Gaussian 수, peak VRAM과 total energy가 가능하면 energy

C pass 조건:

- uninterrupted producer
- harness drop/backpressure 0
- 미래 timestamp access 0
- held-out mapping access 0
- deadline 이내 final sensor processing과 queue empty
- deadline 뒤 map/pose update 0

### 4.6 논문 claim 범위

각 방법의 tracker와 mapper를 모두 실행하면 **end-to-end real-time SLAM**이라고 쓸 수 있다.
공통 tracker가 만든 online packet부터 시작하면 C는 여전히 strict streaming이지만 주장은
**“online tracking state가 주어졌을 때의 real-time incremental 3DGS mapping”**으로 제한한다.
현재 localization을 후순위로 둔 프로젝트 단계에서는 후자의 문구를 사용하고, full tracker
통합 뒤 전자의 claim으로 확장한다.

---

## 5. B와 C에서 의도적으로 달라야 하는 항목

| 항목 | B | C |
|---|---|---|
| Tracker state | frozen common | 각 system 또는 명시한 common online service |
| KF 수/timestamp | 동일하게 고정 | 방법별 자유 |
| Work | event별 Adam 고정; auxiliary view/time 공개 | deadline 안에서 방법별 자유 |
| Packet pacing | event-driven | native timestamp |
| Wall-clock pass | 사용하지 않음 | 핵심 판정 |
| Queue/drop | 구조적으로 제거 | 실제 정책과 backlog 평가 |
| 핵심 delta | mapper 품질 | strict system 품질·성공률 |

B에서 KF를 자유롭게 두면 mapper 차이에 tracker/KF policy가 섞인다. C에서 KF를 고정하면 실제
system이 계산량을 조절하는 능력을 제거한다. 따라서 두 실험의 KF 계약은 의도적으로 달라야 한다.

---

## 6. Dataset split과 과적합 방지

### 6.1 공개 benchmark

- RPNG와 UTMM official scene 전체를 최종 보고한다.
- 이미 반복 사용한 `RPNG table_01`, `RPNG table_04`, `UTMM ego-drive`,
  `UTMM fast-straight`는 development panel로 표시한다.
- 나머지 scene은 config freeze 뒤 한 번 여는 final validation으로 취급한다.
- 최종 표에는 전체 평균과 함께 development/final-validation 평균을 분리한다.
- 한 scene에서 정한 숫자를 다른 scene에서 변경하지 않는다.

### 6.2 Aria transfer

- `aria1253`은 기존 tuning이 누적된 development scene으로 표시한다.
- `aria1253rot`과 `aria301_305`는 무재튜닝 transfer 검증으로 사용한다.
- 절대 frame index 기반 freeze/PGBA cutoff는 금지하고 causal state나 sequence-relative rule로
  교체한 뒤 config를 고정한다.
- Aria와 RPNG/UTMM 사이에는 calibration adapter 외 dataset-specific mapper 숫자를 두지 않는다.

### 6.3 Seed

- 전체 scene은 고정 seed로 한 번 완주한다.
- development panel과 대표 transfer scene은 최소 3 seeds를 실행한다.
- 최종 주장은 단일 best run이 아니라 mean, range 또는 표준편차를 사용한다.

---

## 7. 최종 표 형식

### 7.1 B 표

| Dataset | Method | PSNR↑ | SSIM↑ | LPIPS↓ | Opt steps | View-updates | Unique views | GPU time | Peak VRAM |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| RPNG | B0 Official vanilla |  |  |  |  |  |  |  |  |
| RPNG | B1 Custom vanilla |  |  |  |  |  |  |  |  |
| RPNG | B2 Dense RR |  |  |  |  |  |  |  |  |
| RPNG | B3 Proposed pre-carve |  |  |  |  |  |  |  |  |

UTMM과 Aria도 같은 형식으로 별도 block을 둔다. 상세 scene별 표는 appendix에 둔다.

### 7.2 C 표

| Dataset | Method | Budget | Strict pass | PSNR↑ | SSIM↑ | LPIPS↓ | KF | Skip/drop | p95 lag | EOS queue |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| RPNG | Vanilla | 1.0× |  |  |  |  |  |  |  |  |
| RPNG | gsSLAM | 1.0× |  |  |  |  |  |  |  |  |
| RPNG | Vanilla | 1.5× |  |  |  |  |  |  |  |  |
| RPNG | gsSLAM | 1.5× |  |  |  |  |  |  |  |  |

품질 평균만 제시하지 않고 strict pass 분모와 실패 scene을 같은 표에 둔다.

---

## 8. 실행 순서

1. B/C 공통 held-out UID와 evaluator hash를 고정한다.
2. frozen causal tracker archive를 만들고 미래 정보·MPS0·held-out exclusion을 audit한다.
3. vanilla trace에서 B의 event별 Adam/regular-view ledger를 생성한다.
4. B0/B1/B2/B3를 development panel에서 실행해 Adam 고정과 auxiliary-view 회계를 확인한다.
5. mapper config를 freeze하고 B final-validation scene을 실행한다.
6. 같은 config로 C 1.5×를 실행한다.
7. 1.5× 병목을 수정하되 final-validation scene으로 재튜닝하지 않는다.
8. C 1.0×를 최종 real-time gate로 실행한다.
9. scene별 failure와 counter audit를 완료한 뒤에만 평균 표를 만든다.

실험을 시작할 때마다 다음 manifest가 없으면 결과를 채택하지 않는다.

- dataset/scene와 input hash
- held-out UID hash
- tracker archive 또는 sensor stream hash
- source commit과 dirty diff hash
- config와 seed
- GPU/CUDA/TensorRT engine
- optimizer/view budget 또는 wall-clock deadline
- EOS/zero-tail 정책
- evaluator commit과 command

---

## 9. 결과가 허용하는 주장

- **B만 통과:** 동일 causal input/work에서 gsSLAM mapper가 vanilla보다 좋다.
- **C만 통과:** gsSLAM system이 deadline은 지키지만 mapper 자체 우위의 원인은 분리되지 않았다.
- **B와 C 모두 통과:** gsSLAM mapper의 품질 개선이 strict streaming system에서도 유지된다.
- **1.5×만 통과:** `real-time`이 아니라 `bounded streaming within 1.5× capture duration`으로 쓴다.
- **1.0×까지 통과:** 정의한 ingress boundary 안에서 real-time incremental mapping을 주장한다.
