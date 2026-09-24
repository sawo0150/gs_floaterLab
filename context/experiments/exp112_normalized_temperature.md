# Exp112 — active normalized-variance dense temperature

날짜: 2026-09-24  
상태: **3-family fairness/quality-floor PASS; ERCB PSNR gain 미입증**

## 질문

Exp111의 dense-repeat 구조에서는 dense selection count가 6--7까지 올라갔지만,
기존 `gamma=log(1.5)` normalized-variance sampler가 RR과 실제로 다른 선택을 한
행은 1/2/0개뿐이었다. Normalization을 유지하면서도 실제로 작동하는 하나의
공통 inverse temperature를 고정하면 R4 품질을 유지하고 RR보다 좋아지는가?

## 사전 선택 규칙

온도는 PSNR이나 이미지를 보지 않고, 기존 Exp111의 immutable causal pool을
production queue로 재생해 UTMM `square-1` 한 장면에서만 정했다.

- 고정 수식: `p_i proportional exp(-gamma*n_i/(T+1))`
- `gamma`는 시간·scene·dataset·`T`와 무관한 하나의 상수
- 후보: `log(1.25), log(1.5), log(3), 2, 4, 8, 16, 32, 64`
- 채택: RR 대비 repeat trace 차이 10% 이상이면서 final-generation count CV를
  10% 이상 줄이는 가장 작은 값
- 결과: **`gamma=16`** (`9/71=12.68%` repeat 차이, count CV −12.60%,
  entropy ratio `0.986225`)

`gamma`에 `T+1`을 곱하지 않았으므로 raw-variance sampler를 별도 방법처럼
재포장한 것이 아니다. 재생 코드는
`benchmarks/online_gs/analyze_exp111_normalized_temperature.py`이며 생산
`log(1.5)`/RR trace를 각각 bit-exact하게 복원한 뒤 후보를 비교한다.

## 비교 계약

각 장면을 새 source-locked root에서 네 arm으로 다시 실행했다.

1. R4: primary dense 1 + auxiliary KF 1
2. dense repeat, `gamma=log(1.5)`
3. dense repeat, **`gamma=16`**
4. dense repeat, dense-only zero-energy RR (`gamma=16` 기록, energy=0)

두 repeat slot 중 primary만 admission credit을 만들고 신규 admitted view는 hard
first-service를 받는다. Native historical-KF normalized queue는 모든 arm에서
`gamma=log(1.5)`로 고정했다. 모든 arm은 동일 frozen causal tracker archive,
held-out set, zero-tail, physical render, Adam step, event, admission, topology ticket을
사용한다. `gamma=16`이 같은 장면 R4보다 0.5 dB 넘게 하락하면 즉시 중단하도록
했다.

## 결과

| Scene | R4 | repeat log1.5 | repeat gamma16 | repeat RR | g16−R4 | g16−log1.5 | g16−RR | trace diff |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| UTMM square-1 | 21.215443 | 21.229589 | 21.230649 | 21.225112 | +0.015206 | +0.001060 | +0.005537 | 9/142 |
| RPNG table_01 | 25.581778 | 25.570648 | 25.550914 | 25.576560 | −0.030864 | −0.019734 | −0.025646 | 17/538 |
| Aria aria1253 | 25.733551 | 25.718779 | 25.708201 | 25.715842 | −0.025350 | −0.010578 | −0.007642 | 10/202 |
| **Mean** | — | — | — | — | **−0.013669** | **−0.009751** | **−0.009250** | — |

| Scene | Physical renders / Adam (all arms) | Dense/KF R4 | Dense/KF repeat | RR count CV | g16 count CV | g16 entropy |
|---|---:|---:|---:|---:|---:|---:|
| UTMM square-1 | 9,345 / 757 | 70/70 | 140/0 | .7368 | .6465 | .9862 |
| RPNG table_01 | 38,302 / 3,030 | 267/267 | 534/0 | .6512 | .6076 | .9980 |
| Aria aria1253 | 13,620 / 1,055 | 100/100 | 200/0 | .6847 | .6223 | .9908 |

3장면 12arm 모두 archive/config/event/render/Adam/admission/primary-slot,
held-out disjointness, saved-map double evaluation, zero-tail, topology extra-work=0
검증을 통과했다. Source lock은 lab commit `683f4ac`과 VIGS commit
`9c329fd1`을 기록한다.

## 판정

- **성공:** normalized ERCB가 이제 명목상 flag가 아니라 실제 view ordering과
  service-count dispersion을 바꾼다. R4 대비 평균 −0.0137 dB라 품질은 안전하게
  보존됐고 추가 work가 없다.
- **실패/제한:** `gamma=16`은 기존 `log(1.5)`나 RR보다 평균 약 −0.01 dB다.
  따라서 ERCB가 PSNR 향상의 원인이라고 주장할 근거는 여전히 없다. 이 결과로
  gamma를 추가 PSNR 튜닝하거나 17-scene 공식 panel을 돌리지 않는다.
- **현재 해석:** dense repeat 자체는 contribution-aligned하고 안전하지만, 단순
  count balancing은 어느 dense view가 학습 가치가 높은지를 나타내지 못한다.
  다음 Track-A는 렌더 수를 더 늘리지 않고 저자 공개 코드에서 가져온 local
  residual/topology evidence로 repeat utility를 정의해야 한다. R4/Exp109의 큰
  vanilla 이득은 계속 native KF/window와 건강한 Gaussian population 쪽이 주된
  설명이다.

## 산출물

- 실행기: `benchmarks/online_gs/run_exp112_normalized_temperature.py`
- trace-only selector: `benchmarks/online_gs/analyze_exp111_normalized_temperature.py`
- raw root: `results/experiments/exp112_normalized_temperature/`
- 표: `context/experiments/benchmark_custom/exp112_normalized_temperature_20260924/summary.md`
