# ERCB bundle-wide tuning protocol — UTMM

> 고정일: 2026-09-11
> 상태: **완료 — seed-0 tuning 후 고정 설정을 seed-1/2로 검증**

## 목적

전체 논문의 binary module ablation에 사용할 ERCB 파라미터를 새 benchmark 묶음 하나에서
고르고, 동일한 전체 시스템에서 causal random reshuffling(RR) 대비 ERCB의 held-out 품질
기여를 측정한다. 데이터 묶음은 UTMM으로 고정하며 장면별 파라미터는 사용하지 않는다.

## 데이터 선택

UTMM은 서로 다른 motion pattern과 native depth를 포함하고 전체 RGB가 약 8.4k장이라,
약 40.7k장의 유사 table capture로 구성된 RPNG보다 scheduler 파라미터 반복에 적합하다.
exp80 fixed-1x VIGS seed-0 결과 중 아래 tracking gate를 사전에 적용한다.

- gate: VIGS run complete 및 Sim(3) ATE < 10 cm
- 사용: `ego-centric-1`, `ego-centric-2`, `ego-drive`, `fast-straight`,
  `slow-straight-2`, `square-1`
- 제외: `slow-straight-1`(VIGS tracking failure), `square-2`(ATE 92.7613 cm)

각 replay는 exp80의 final-online full-frame pose, 실제 keyframe timestamp interval,
누적 geometry-only depth-anchor point를 arm 사이에 고정한다. 따라서 scheduler-isolation
ablation이며 strict online localization 결과로 주장하지 않는다.

## 공통 계약

- llffhold-8 held-out evaluation
- 60 optimizer updates/keyframe event
- 마지막 VIGS keyframe 이후 RGB는 sensor-EOS event에 도착
- sensor EOS 뒤 optimizer update 0회(zero-tail)
- resolution 4
- 모든 arm에 동일 pose, point initialization, update budget

## 튜닝과 최종 비교

1. Seed 0에서 `K=8`, `rho in {0.25, 0.5, 0.75}`,
   `exp(gamma) in {1.1, 1.25, 1.5, 2, 3}`의 ERCB 설정과 RR을 실행한다.
   최초 `1.5/2/3` grid의 두 ego-centric sequence 결과에서 낮은 gamma가 우세해
   `1.1/1.25`를 refinement로 추가했으며 이 adaptive search 과정도 결과에 기록한다.
2. 두 ego-centric 시퀀스에서 모든 설정을 1차 screening하고, 평균 paired PSNR 기준
   상위 3개를 나머지 네 시퀀스로 확장한다. 2026-09-11 shortlist는
   `(rho, exp(gamma)) = (0.75,1.1), (0.25,1.5), (0.75,1.5)`이다.
3. 상위 `(rho, gamma)=(0.75, log(1.5))`에서 `K in {4,8,16}`을 6개 시퀀스
   seed 0으로 비교한다.
4. 6개 시퀀스의 paired held-out PSNR delta를 시퀀스 동일 가중 평균하고 가장 높은
   ERCB 설정 하나를 선택한다. 정확한 동률일 때만 worst-Q1 delta로 결정한다.
5. 선택된 설정과 RR만 seed 1, 2로 추가 실행한다.
6. 최종 표는 6 scene x 3 seed의 PSNR 평균, paired delta, scene/seed win count와
   ERCB 목적 확인용 worst-Q1을 보고한다.

Seed-0 선택 결과는 `K=8, rho=0.75, exp(gamma)=1.5`이다. RR 대비 6-scene
동일 가중 평균 PSNR은 `+0.1343 dB`, worst-Q1은 `+0.2427 dB`, scene win은
`4/6`이었다. 이후 이 설정을 변경하지 않고 seed 1, 2를 검증했다.

## 최종 결과

| seed | mean PSNR delta | worst-Q1 delta | RR-hard-Q1 delta | PSNR wins |
|---:|---:|---:|---:|---:|
| 0 (tuning) | +0.1343 | +0.2427 | +0.4969 | 4/6 |
| 1 (frozen) | +0.0484 | +0.0901 | +0.3434 | 4/6 |
| 2 (frozen) | +0.0265 | -0.0142 | +0.1558 | 3/6 |
| **18-pair aggregate** | **+0.0698** | **+0.1062** | **+0.3321** | **11/18** |

18쌍의 held-out PSNR 평균은 RR `21.9148dB`, ERCB `21.9845dB`다. 장면별
3-seed 평균은 다음과 같다.

| scene | RR | ERCB | delta | wins |
|---|---:|---:|---:|---:|
| ego-centric-1 | 22.9530 | 23.1965 | +0.2435 | 3/3 |
| ego-centric-2 | 21.2404 | 21.4794 | +0.2390 | 2/3 |
| ego-drive | 21.8775 | 21.9021 | +0.0246 | 2/3 |
| fast-straight | 22.1826 | 21.8869 | -0.2957 | 0/3 |
| slow-straight-2 | 20.9076 | 21.1347 | +0.2271 | 2/3 |
| square-1 | 22.3274 | 22.3075 | -0.0200 | 2/3 |

K sensitivity(seed 0)는 `K=4/8/16`의 mean delta가 각각
`+0.1015/+0.1343/+0.0135dB`였고, 사전 선택 규칙에 따라 K=8을 유지했다.

Selection-count CV는 RR `0.8030`에서 ERCB `0.9389`로 악화했다. 따라서 이 결과는
global count equality나 최종 service shortfall 감소의 근거가 아니다. 품질 주장은
**UTMM validation bundle에서 평균 PSNR과 RR-hard-Q1을 소폭 개선**한 것으로 제한한다.
특히 fast-straight의 음수 결과와 동일 bundle tuning/evaluation을 함께 보고한다.

Grid screening은 저장된 8-bit held-out render/GT PNG에서 PSNR과 worst-Q1만 계산한다.
run당 수 분이 드는 LPIPS는 파라미터 선택에 사용하지 않으며, 논문 표에서 필요할 경우
선택된 ERCB/RR 최종 run에만 별도로 계산한다.

이 표는 UTMM validation-set module ablation으로 부르며, 같은 결과를 독립적인 test-set
generalization 근거로 중복 주장하지 않는다.

## 구현 및 산출물

- causal replay dataset: `data/benchmarks/ercb_utmm_tuning_v1/`
- VIGS source: `data/benchmarks/vigs_sources/fixed1x_5090_exp80/utmm/`
- runner: `3dgs-custom/scripts/incremental/run_ercb_utmm_tuning.sh`
- summarizer: `3dgs-custom/scripts/incremental/summarize_ercb_utmm_tuning.py`
- full output: `context/experiments/ERCB_ablation/evidence/utmm_tuning_v1/`
- compact evidence: `context/experiments/ERCB_ablation/evidence/utmm_tuning_v1_compact.json`
- 최종 36개 RR/ERCB run은 scheduler/seed/파라미터/update 합/EOS/zero-tail manifest audit 통과
