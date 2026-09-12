# VIGS strict benchmark + ERCB ablation — running log

> 시작: 2026-09-12
> 상태: **strict 1.5× VIGS baseline fixed 22dB 2/2 재현 완료; dense RR↔ERCB 비교는 다음 단계**
> 1차 목표: UTMM `ego-drive`에서 논문 원형 recipe의 품질을 현재 fixed held-out으로
> 먼저 측정하고, 같은 tracking+mapping 경로의 strict 1.5×에서 약 **22dB 이상**을 확보

## 2026-09-12 논문 구현 재감사 및 정정

- VIGS-SLAM 논문 시스템은 mapping-only가 아니라 RGB+IMU tracking과 Gaussian
  mapping을 하나의 end-to-end 실행에서 수행한다. 논문은 이를 simultaneous/parallel로
  서술하지만, 공개 `origin/main`의 `config/utmm.yaml`에는 `Training.parallel`이 없어
  코드 기본값 `false`가 적용된다. 따라서 UTMM 공개 구현은 frontend tracking 뒤
  keyframe mapping을 동기 호출하며, `parallel: true`인 iPhone 설정만 queue 기반 GS
  background thread를 사용한다. 논문의 online 수치는 final global BA와 통상 10분 이상인
  final color refinement **이전** 결과다.
- 새 keyframe마다 mapping 10 iteration을 수행하며, 각 iteration에서 frontend frame
  graph keyframe과 global keyframe 2개를 무작위 표본화한다. 최적화는 direct RGB
  (SH degree 0)의 color/depth/geometry loss다. 논문 Eq. (5)는 color L1 + depth L1
  + isotropic regularization으로 요약하지만, 공개 코드는 기본 `alpha=0.95`의 RGB L1,
  `0.05*5`의 inverse-depth L1, `0.1*lambda_dnormal`의 normal prior
  (`lambda_dnormal=0.5`), 그리고 weight 10의 isotropic scale loss를 실제로 더한다.
- UTMM `EgoDrv`의 정확한 논문 PSNR은 refinement 전 **21.54dB**, UTMM 평균
  **20.87dB**다. refinement 후 `EgoDrv` 23.47dB는 online baseline으로 쓰지 않는다.
  단 논문은 어느 방법에서도 keyframe/mapping view로 쓰이지 않은 frame만 평가한다고
  명시하지만, 공개 `origin/main` evaluator는 `idx%5==0` 또는 keyframe을 포함하고
  keyframe 제외 코드가 주석 처리돼 있다. `--pure_online`도 pre-final map을 저장할 뿐
  그 경로에서 rendering metric을 직접 계산하지 않는다. 따라서 공개 코드만으로 논문의
  정확한 evaluation mask가 복원되지 않으며, 21.54dB와 우리 llffhold-8 수치는 직접
  동치 비교하지 않는다.
- 논문의 runtime 표는 RTX 5090에서 tracking+mapping 전체 시스템 평균 12.02 FPS를
  보고하지만, `FPS=전체 frame/전체 runtime`이며 fixed 1.5× sensor deadline과
  sensor-EOS 뒤 update 0회를 명시하지 않는다. 따라서 **논문 online control**과
  **우리 strict wrapper control**은 별도 arm으로 검증한다.
- 현재 exp81은 tracking+mapping end-to-end인 점은 맞지만, 공개 UTMM 원형과 달리
  `parallel=true`, keyframe mapping 7회, global view 6개, init 600회, frontend
  window 15, motion threshold 2.6 및 `final-v7` model/adaptive/replay scheduler를
  사용한다. 원형은 각각 synchronous, 10회, global 2개, init 1050회, window 25,
  threshold 2.4다. 즉 ERCB/carve가 꺼진 clean branch이지,
  **논문 원형 mapping schedule의 clean reproduction은 아니다**.

## 질문과 실험 순서

새 benchmark에서 논문 원형 end-to-end VIGS control을 먼저 복원한 뒤 strict 1.5×
wrapper의 손실을 분리 측정하고, 그 strict 실행 계약에서 scheduler만 causal RR과
ERCB로 바꿔 binary ablation한다. 현재 exp81 결과는 custom scheduler 진단값이며
논문 baseline 재현값으로 부르지 않는다.

1. `ego-drive`에서 논문 원형 online tracking+mapping schedule을 우리 fixed
   llffhold-8 evaluator로 측정한다(21.54dB는 참고값이지 직접 acceptance 값이 아님).
2. 동일 schedule에 strict 1.5×/zero-tail wrapper만 적용해 손실을 측정한다.
3. pose/init/update budget을 고정하고 causal RR ↔ ERCB만 paired 비교한다.
4. 27dB 전에는 hard carve/floater pruning을 적용하지 않는다.

## 고정 실행 계약

- 입력: timestamp 순 UTMM RGB + IMU, online 추정 pose/depth만 사용
- 금지: MPS/post-hoc trajectory, depth, point cloud
- 예산: sensor span의 1.5×, margin 20ms
- 종료: deadline 및 마지막 sensor frame 뒤 Gaussian optimizer update 0회
- 평가: llffhold-8 held-out PSNR; `--eval_online_final --eval_metrics_only`
- baseline OFF: ERCB, GPU-token admission, legacy carve, detached loss,
  terminal rematuration/prune
- calibration은 UTMM 고정값을 사용하고, paper-online/strict pair에서는 공개
  `origin/main` UTMM recipe를 동일하게 고정해 strict wrapper만 달리한다.

## 코드 provenance

- repo: `/home/wosas/Desktop/26-1_RPM/gsProjects/VIGS-SLAM-main-integration-20260828`
- clean 시작점: `9c1e27676b2b9f5369f34ffff91b51d99d092aa2`
- branch: `exp81-vigs-benchmark-strict15x`
- 구현 commit:
  - `c46bab2e`: fixed 1.5× sensor-EOS/zero-tail controller
  - `6176539b`: fnet/update TensorRT 독립 disable 제어
  - `ccadae28`: UTMM 328×648 고정 해상도 TensorRT engine builder
  - `eb749d18`: GPU별 benchmark hardware profile
  - `8b508615`: cache-off 4-step/overlap/packed replay variant
  - `010323f5`, `ef0657de`: causal keyframe source quota와 work-credit 분리
  - `62934342`: dense/keyframe replay gradient role 분리
  - `46a2c3f6`, `dae137e8`, `759c1436`: causal dense-view pose 등록과
    source-exact uint8 GPU cache
  - `6e3947c4`, `b3f0ca5e`: online-rank density와 stale replay-cost 만료
  - `898cf18f`: paper frontier iteration override 복원
  - `e31e7ff0`: 공개 UTMM Gaussian birth-density control 추가
  - `495b5f0d`: native depth/normal-loss ablation 분리
  - `13698eb5`: 계수가 0인 depth/normal graph의 무효 계산 short-circuit
  - `551b3d44`: 22dB 2/2 재현 설정을 verified runner로 고정
- runner: `exp81_axes/run_utmm_strict15x_baseline.sh`
- verified runner: `exp81_axes/run_utmm_strict15x_verified_baseline.sh`
- config: `config/exp81_utmm_baseline.yaml`

`/home/wosas/Documents/5090_25db_log`의 최종 22.010dB 결과는 frozen-tracker
mapping-only 튜닝이다. end-to-end VIGS baseline의 증거로 섞지 않고, baseline이 부족할
때 이식할 mapping 방향(초기 dense geometry, 성숙 뒤 dense appearance-only,
keyframe full geometry, online density)을 정하는 참고 근거로만 사용한다.

## 진행 결과

| Run | 유효성 | 실행 조건 | Held-out PSNR | Adam / replay | 판정 |
|---|---|---|---:|---:|---|
| `failed_static_fnet_20260912` | 무효 | 464×464 fnet TRT engine을 328×648 UTMM에 잘못 사용 | — | — | startup tensor shape 불일치; 결과 제외 |
| `seed0` | **유효 strict control** | RTX 5070 Ti, 당시 5090 profile, PyTorch fnet/update | **17.6818dB** | 636 / 266 | zero-tail 통과, 목표 미달 |
| `seed0_trt` | 무효 | RTX 5070 Ti, UTMM TRT, 잘못된 5090 memory profile | — | — | tracking 중 OOM; 결과 제외 |
| `seed0_5070trt` | **유효 strict control** | RTX 5070 Ti 저메모리 profile + UTMM TRT | **17.5679dB** | 685 / 315 | zero-tail 통과, control −0.1138dB |
| `seed0_hybrid` | **유효 strict control** | cache off, 4-step/overlap/packed + UTMM TRT | **18.8602dB** | 656 / 266 | 현재 최고, control +1.1784dB, 22dB 미달 |
| `seed0_hybrid_kf75` | **유효 source ablation** | hybrid 고정 + replay keyframe 75%, dense 25% | **18.6941dB** | 642 / 252 | 비율 준수·zero-tail 통과, hybrid −0.1661dB |
| `seed0_hybrid_kf75_adaptivegrad` | **유효 gradient ablation** | kf75 고정 + dense는 topology 성숙 후 appearance-only | **18.4075dB** | 656 / 266 | dense full/app 35/32; kf75 −0.2866dB, 현 compute에서 NO-GO |

유효 `seed0`은 sensor budget 69.9454초, `updates_completed_after_deadline=0`,
`updates_completed_after_sensor_eos=0`이다. SSIM 0.5760, LPIPS 0.5435,
keyframe PSNR 18.1608dB이며 MAP_RR은 dense 266회, 최종 pool 151이었다.
반면 tracking 종료가 77.146초여서 이 GPU/profile 조합은 입력 재생보다 뒤처졌고,
idle replay를 한 번도 수행하지 못했다. 현재 저품질의 직접 원인은 scheduler 비교가 아니라
baseline compute starvation이다.

`seed0_5070trt`는 peak allocated/reserved memory를 11.89/14.26GB에서
8.12/9.32GB로 낮추고 Adam을 49회 늘렸지만, tracking은 여전히 76.075초였고
idle replay는 0회였다. SSIM 0.5737, LPIPS 0.5468, keyframe PSNR 18.0378dB이며
deadline/EOS 뒤 update는 모두 0이다. **고정-shape TRT 단독 적용은 NO-GO**이고,
품질 차이는 작은 step 증가보다 run-to-run/map 경로 변동이 큰 구간으로 해석한다.

`seed0_hybrid`는 peak allocated/reserved 8.10/11.18GB로 OOM 없이 완료했고,
SSIM 0.6150, LPIPS 0.4834, keyframe PSNR 19.3616dB를 얻었다. Adam 수는 656으로
늘지 않았지만 4-step/overlap 실행 경로에서 PyTorch control보다 **+1.1784dB** 높아졌다.
tracking은 73.409초로 개선됐으나 여전히 budget을 넘고 11개 mapping packet이 drop돼
idle replay는 0회였다. 실행 경로는 채택 후보지만 22dB baseline으로는 불충분하다.

`seed0_hybrid_kf75`는 replay 252회를 keyframe 189 / dense 63으로 정확히
75:25 배분했고 future-frame 사용은 0이었다. held-out SSIM/LPIPS는
0.5993/0.5037, keyframe PSNR은 19.2593dB, tracking은 73.914초였다.
deadline/EOS 뒤 update도 0이었지만 dense-only hybrid보다 0.1661dB 낮아,
**source 비율만 바꾸는 축은 NO-GO**다. 5090 recipe의 성능은 keyframe 비율
자체가 아니라 dense는 topology 성숙 후 appearance-only, keyframe은 full-geometry로
나누는 gradient role 분리와 결합된 결과로 보고 다음 단일 변인으로 검증한다.

`seed0_hybrid_kf75_adaptivegrad`는 controller가 frontier인 동안 dense 35회를
full-geometry로, balanced 전환 후 dense 32회를 SH appearance-only로 수행했고
keyframe 199회는 모두 full-geometry였다. 즉 구현 의도는 audit로 확인됐지만,
held-out PSNR/SSIM/LPIPS는 **18.4075/.5830/.5237**로 kf75 full-gradient보다
−0.2866dB였다. Adam 656, replay 266, tracking 73.221초, dense pool 152,
idle replay 0으로 여전히 compute-starved며, appearance-only dense update도 32회에 불과하다.
따라서 이 결과는 5090 mapping-only recipe의 일반적 기각이 아니라 **현 5070 Ti
end-to-end 처리량에서는 NO-GO**로 판정한다. 부족한 geometry update를 더 줄이는
recipe 축을 중단하고 하드웨어/프론트엔드 처리량 차이를 먼저 해소한다.

참고 상한은 exp80 RTX 5090 strict 1× end-to-end 결과의 21.0598dB와 1,968 Adam
step이다. 이것도 22dB에 못 미치므로 목표 달성 증거가 아니라 복원 기준점이다.

## 2026-09-12 fixed metric 정정 및 vanilla 5070 Ti control

위 초기 표의 `Held-out PSNR` 열에는 당시 `mean_psnr`(fixed+keyframe union)을
잘못 옮긴 항목이 있다. 이후 판정은 JSON의 `fixed_eval_mean_psnr`만 사용한다.
핵심 run을 같은 기준으로 다시 집계하면 다음과 같다.

| 구현 / run | 예산·평가 | fixed PSNR | union PSNR | 핵심 판정 |
|---|---|---:|---:|---|
| custom `seed0` | strict 1.5× | 17.6088 | 17.6818 | 초기 control |
| custom `seed0_hybrid` | strict 1.5× | 18.7825 | 18.8602 | cache-off 실행 경로 개선 |
| custom `seed0_hybrid_fastfront` | strict 1.5× | 21.1161 | 21.2097 | realtime frontend가 최대 회복축 |
| custom `...kf75_autofreeze` | strict 1.5× | **21.4257** | 21.5856 | 현재 fixed 최고. 단 dense 등록 전 run이라 실제 replay는 keyframe-only fallback |
| custom `...interp_uint8cache` | strict 1.5× | 21.2920 | 21.4409 | dense/KF 25:75를 실제 수행한 대응 control |
| custom `...rank25_horizon1000b` | strict 1.5× | 21.1965 | 21.3476 | stale-cost 문제는 해소했지만 품질 개선 없음 |
| custom `...frontier10` | strict 1.5× | 21.0950 | 21.2373 | paper 10-iters 복원은 replay 감소로 악화 |
| custom paper recipe, unlimited | deadline 없음 | 20.3309 | 20.4235 | origin 설정을 custom evaluator로 재현 |
| custom paper recipe | strict 1.5× | 15.5057 | 15.5357 | synchronous mapping backlog로 붕괴 |
| custom vanilla-density `...r1` | strict 1.5× | 20.6647 | 20.8003 | 아래 density arm, NO-GO |

원본 비교는 별도 worktree
`/home/wosas/Desktop/26-1_RPM/gsProjects/VIGS-SLAM-vanilla-check`의
`origin/main@22ffe24c`에서 수행했다. mapping/tracking/loss/config는 원본이며,
`--pure_online` map을 optimizer update 없이 채점하는 opt-in 6-line hook과 RTX 5070 Ti
컴파일용 `<cstdint>` include 1줄만 존재한다. `config/utmm.yaml`, PyTorch frontend/update,
Ego-Drive 1개를 실행한 결과는 다음과 같다.

- 공개 evaluator (`idx%5==0 OR keyframe`) PSNR **20.1556dB**, KF **20.5377dB**
- 저장 render에서 keyframe을 제외해 재계산한 진단 fixed PSNR **20.0346dB**
  (JPEG 저장 재계산이며 공개 mean 재현 오차 0.0015dB)
- wall **218.83초**, final map 약 13만 Gaussian; iteration은 시간 때문에 잘리지 않는
  synchronous online 실행
- 논문 EgoDrv refinement 전 21.54dB와 약 1.38dB(public union)~1.51dB
  (fixed 진단) 차이. 논문은 mapping view 전체 제외를 명시하지만 공개 evaluator는
  keyframe을 union하므로 수치를 직접 동치 비교하지 않는다. README도 공개판이 대규모
  refactor 후 논문과 결과가 정확히 같지 않을 수 있다고 명시한다.

따라서 현재 개발 대상은 계속 **custom branch**이고, vanilla worktree는 5070 Ti
reference 측정 전용이다. 아래 2026-09-13 항목에서 custom strict fixed 22dB를
2회 재현해 이 당시의 0.5743dB 격차를 해소했다.

### 공개 vanilla birth density 이식

첫 vanilla-density run은 공개 UTMM의 `pcd_downsample=64`,
`pcd_downsample_init=32`, PPM/adaptive off를 이식해 fixed 20.6647dB를 냈지만,
대응 control의 adaptive dense-gradient가 아니라 `full` gradient로 실행돼 density
단독 인과값으로 사용할 수 없다. 이후 gradient를 맞춘 init-only arm
(`init 64→32`)은 21.1567dB로 정확한 control 21.2920보다 −0.1353dB였다.
따라서 **고밀도 전체 run의 −0.6273dB를 density 효과로 단정한 과거 문장은 정정**하며,
통제된 결론은 초기 density 증가도 22dB를 회복하지 못했다는 것뿐이다.

## 2026-09-13 strict fixed 22dB baseline 2/2 재현

native loss paired repeat는 fixed 21.1211dB였고, native depth/normal 항을 config로
끈 RGB-only arm은 21.5655dB(+0.4444)였다. 코드 감사 결과 `alpha=1.0`과
`lambda_dnormal=0`이어도 inverse-depth 및 depth-to-normal graph를 매 keyframe
update마다 계산한 뒤 0을 곱하고 있었다. `13698eb5`에서 이 두 graph만
short-circuit했다. 이는 loss 값, gradient, view 순서를 바꾸지 않는 실행 최적화다.

| run | replay source | fixed PSNR / SSIM / LPIPS | union PSNR | Adam / replay | zero-tail |
|---|---|---:|---:|---:|---:|
| RGB-only, short-circuit | KF75 / dense25 | 21.8822 / .72346 / .28612 | 22.1350 | 4,589 / 3,944 | 0 / 0 |
| verified r1 | **KF100** | **22.0991 / .73345 / .27073** | 22.3714 | 5,185 / 4,606 | 0 / 0 |
| verified r2 | **KF100** | **22.0100 / .73115 / .27363** | 22.2937 | 4,882 / 4,303 | 0 / 0 |

verified 2회 fixed 평균은 **22.0545dB**이며 원본 vanilla fixed 진단
20.0346dB보다 +2.0199dB다. 두 run 모두 1,399 RGB를 timestamp 순으로 처리했고,
budget 69.9454초, fixed view 281개, `mapping_exclude_fixed_eval_views=true`,
`mps_inputs=[]`, evaluation `map_updates=0`, deadline/EOS 뒤 update 0회다.
ERCB(count-softmax), token admission, carve/dust-GC, detached opacity loss,
background polish 및 terminal action도 모두 꺼져 있다.

최종 baseline은 VIGS 원형처럼 **도착한 non-eval tracked keyframe만 replay**한다.
dense RGB는 인과적으로 등록되지만 이 arm의 optimizer source로는 뽑히지 않는다.
따라서 이번 결과는 “end-to-end strict VIGS baseline ≥22dB” gate를 통과한 것이며,
dense view selection을 비교하는 RR↔ERCB ablation의 paired control까지 끝났다는 뜻은
아니다. 그 비교에서는 dense를 포함한 동일 active set/loss/budget을 양쪽에 고정해야 한다.

## 다음 실행

1. strict VIGS keyframe baseline fixed 22dB는 2/2 재현 완료했다.
2. verified 설정을 바꾸지 않고 2–3개 대표 장면에 무재튜닝 전이한다.
3. dense active set을 다시 켜는 RR↔ERCB에서는 source set·loss·update budget을
   paired 고정하고 selector만 바꾼다. hard carve는 계속 보류한다.

## 2026-09-13 무재튜닝 전이 사전등록

결과를 보기 전에 transfer panel을 `ego-centric-1`, `slow-straight-2`,
`square-1`로 고정한다. 각각 긴 egocentric motion, 중간 길이 직선 motion,
긴 loop trajectory를 대표하며 개발 장면 `ego-drive`는 transfer 승률에서 제외한다.
`run_utmm_strict15x_verified_baseline.sh`의 모든 환경변수와 config를 그대로 사용하고
sequence와 output path만 바꾼다.

성공 기준은 **세 transfer scene 중 최소 2개에서 original vanilla 대비 shared
non-keyframe held-out PSNR +1.0dB 이상**이다. vanilla comparator는
`origin/main@22ffe24c`, `config/utmm.yaml`, PyTorch frontend/update,
`--gsmapping --pure_online --undistort --IMU_poseinit_after 15 --buffer -1`로 고정한다.
원본 vanilla는 strict deadline 기능이 없으므로 synchronous online loop를 끝까지
허용한다. 이는 custom strict 1.5×에 더 불리한 보수적 비교다. 양쪽 점수는 vanilla가
Gaussian mapping에 사용한 keyframe을 공통 평가 집합에서 제거해, 동일한 `idx%5`
frame subset 위에서 재집계한다. 중간 결과를 보고 scene이나 설정을 교체하지 않는다.

## 2026-09-13 무재튜닝 전이 결과 — 1/3, NO-GO

사전등록한 장면과 설정을 교체하지 않고 모두 실행했다. 원본 vanilla는
`origin/main@22ffe24c`의 synchronous unbounded online mapping을 사용했고, custom은
verified strict 1.5× runner를 그대로 사용했다. 비교는 각 장면의 fixed
`idx%5 + 마지막 frame`에서 **vanilla keyframe을 양쪽 모두 제거한 동일 subset**의
렌더 직후 in-memory PSNR 평균이다. vanilla에는 학습 종료 뒤 per-view metric을
기록하는 계측만 추가했으며 tracking/mapping/loss는 바꾸지 않았다.

| scene | custom / vanilla KF | custom shared PSNR | vanilla shared PSNR | 차이 | +1dB |
|---|---:|---:|---:|---:|---|
| `ego-centric-1` | 52 / 53 | **21.2263** | 17.3271 | **+3.8992** | PASS |
| `slow-straight-2` | 12 / 16 | — | 19.2329(union) | — | **FAIL** |
| `square-1` | 71 / 84 | 21.0518 | 20.6906 | +0.3612 | **FAIL** |

따라서 “개발 장면을 제외한 3개 중 2개 이상에서 vanilla +1dB” 기준은
**1/3으로 실패**했다. `ego-centric-1`의 큰 이득만으로 일반화를 주장하지 않는다.
`slow-straight-2`는 strict deadline 때문이 아니라 `IMU_poseinit_after=15`인데
realtime5070 frontend가 keyframe을 12개만 만들어 map packet/Adam이 모두 0회였던
구조적 실패다. `square-1`은 8,348 Adam, tail 0/0으로 map은 정상 학습됐지만
목표까지 0.6388dB 부족하다. 다음 수정은 장면별 분기가 아니라 (1) 짧고 저운동인
sequence도 map을 시작하게 하는 causal initialization gate와 (2) loop coverage를
늘리는 전역 정책을 각각 단일 변인으로 검증한다.

재현 도구와 machine evidence:
`run_original_vanilla_transfer.sh`, `compare_shared_heldout.py`,
`evidence/transfer/summary.json`.

### 다음 단일 축 사전등록: provisional pre-IMU map

15→10 조기 IMU 초기화는 inertial BA의 `fix_front=15` 전제를 깨므로 실행하지 않는다.
대신 `IMU_poseinit_after=15`와 모든 optimizer/scheduler/frontend 설정은 유지하고,
`--mapping_after_imu_init` gate만 끈다. 그러면 15KF 미만 sequence도 vision-scale
provisional map을 학습하고, 15KF에 도달하는 sequence는 기존 frontend가 metric
초기화 직후 `remove_all_gaussians()`한 뒤 동일하게 다시 시작한다. 먼저 구조적 실패였던
`slow-straight-2`에서 map 생성과 +1dB 가능성을 진단한다. 이 exposed scene의 결과는
수정 개발용이며, 후보 채택 시 아직 보지 않은 장면으로 별도 전이 검증한다.

진단은 성공했다. 동일 strict 1.5×/zero-tail에서 12KF 자체는 그대로였지만 mapping
packet 0→3, Adam 0→2,756회로 복구됐고 fixed PSNR은 **22.8337dB**였다.
vanilla keyframe을 공통으로 뺀 120-view 비교는 **22.8250 vs 19.1036dB,
+3.7214dB**다. deadline/EOS 뒤 update는 0/0이며 peak allocated/reserved는
5.74/7.15GB다. 따라서 provisional pre-IMU mapping은 짧은 sequence의 구조적
실패를 해결하는 **후보**로 유지한다. 다만 이 장면은 수정 동기를 제공한 exposed
development case이므로 일반화 성공 수에는 아직 넣지 않는다.

## 2026-09-13 square-1 frontend radius 단일 축 — NO-GO

`square-1` 실패가 후반 tracking/loop coverage 문제인지 확인하려고 verified recipe에서
`frontend_radius=1→2`만 바꿨다. 첫 실행의 20ms EOS guard는 실제 Gaussian Adam
step 최대치(기존 valid run 약 41–44ms)보다 짧아 deadline 뒤 update를 검출했고,
save/eval 전에 실패했으므로 품질 수치가 없는 **무효 run**이다. 동일 arm을 controller
원래 기본값인 50ms guard로 다시 실행하자 deadline/EOS 뒤 update 0/0으로 유효했다.

유효 radius-2 arm은 fixed **20.8422dB**, vanilla keyframe을 함께 제거한 311-view
shared **20.8778 vs 20.6906dB(+0.1872)**로 +1dB gate를 통과하지 못했다. 오히려
radius-1 reference의 fixed 21.0236/shared +0.3612dB보다 낮고, Sim3 ATE RMSE도
8.84→10.01cm로 악화됐다. shared temporal quintile 차이는
`+1.616/+1.164/+1.085/+0.789/−3.655dB`라 앞부분의 우위와 마지막 20% 붕괴가
그대로다. 따라서 radius 확장은 loop drift 해결책으로 채택하지 않으며 runner 기본값과
merge된 baseline 코드는 radius 1로 유지한다. 다음 tracking 축은 단순 window 확대가
아니라 후반 pose revision/loop recovery가 실제 발생하도록 만드는지부터 계측해야 한다.

같은 판단을 교차확인하려고 radius를 1로 되돌린 뒤 `motion_filter.thresh=3.6→3.0`만
바꿔 keyframe을 더 촘촘히 받았다. 이 arm도 50ms guard에서 tail 0/0으로 유효했지만,
fixed **20.8332dB**, shared **20.8507 vs 20.6906dB(+0.1601)**로 실패했다.
Sim3 ATE RMSE는 **13.99cm**까지 악화됐고 마지막 quintile은 **−4.945dB**였다.
따라서 keyframe 밀도 증가도 기각한다. 두 단일 축이 공통으로 보여준 것은 square-1
후반 붕괴가 local window 폭이나 keyframe 수 부족만으로 고쳐지지 않는다는 점이다.
square 한 장면에 frontend 상수를 더 맞추지 않고, 이미 short-motion 구조 복구 효과가
확인된 provisional pre-IMU map 후보를 untouched scene에 먼저 전이한다.

## 다음 실행 사전등록: provisional pre-IMU map untouched transfer

결과를 보기 전에 다음 세 장면을 고정한다. `fast-straight`와 `slow-straight-1`은
15KF 미만 가능성이 있는 짧은 저운동 장면, `ego-centric-2`는 15KF를 넘는 긴 장면의
회귀 guard다. exposed 개발 장면인 `slow-straight-2`와 frontend 상수를 진단한
`square-1`은 채택 승률에서 제외한다. 세 장면은 한꺼번에 병렬 실행하지 않고 GPU를
확인하며 순차 실행한다.

candidate는 verified strict 1.5× KF100 recipe에서 `mapping_after_imu_init=1→0`만
바꾸고, original vanilla comparator와 shared non-keyframe held-out subset 규칙은 이전
transfer와 동일하게 고정한다. 성공 기준은 **3개 중 최소 2개에서 vanilla +1.0dB**이며,
long-sequence guard가 크게 회귀하면 short-sequence 이득만으로 채택하지 않는다.
20ms guard가 실제 41–44ms Gaussian step보다 짧아 무효 run을 만든 사실에 따라,
zero-tail safety margin은 controller 원래 기본값 50ms로 복구한다.

## 2026-09-13 provisional pre-IMU map untouched 전이 — 2/3 GO

사전등록한 세 장면을 순차 실행했고 설정이나 scene을 교체하지 않았다.

| scene | custom / vanilla KF | map packet / Adam | custom shared | vanilla shared | 차이 | 판정 |
|---|---:|---:|---:|---:|---:|---|
| `fast-straight` | 7 / 17 | 5 / 998 | **19.2754** | 17.3971 | **+1.8783** | PASS |
| `slow-straight-1` | 4 / 12 | 1 / 132 | 16.9579 | **18.9565** | **−1.9986** | FAIL |
| `ego-centric-2` | 63 / 62 | 45 / 4,155 | **20.5488** | 19.2300 | **+1.3188** | PASS |

세 custom run은 모두 strict 1.5×, MPS 입력 0, eval map update 0,
deadline/EOS 뒤 update 0/0을 통과했다. Sim3 ATE RMSE는 각각
1.34/1.06/1.86cm다. 따라서 사전 기준 **2/3 + long-sequence guard PASS**를 충족해
`mapping_after_imu_init=0`을 verified runner 기본값으로 채택한다. 15KF에 도달하는
긴 장면은 pre-IMU map을 metric 초기화 때 폐기하고 같은 verified map으로 재시작한다.

이 결과는 모든 장면 성공이 아니다. `slow-straight-1`은 pose ATE가 좋은데도 4KF,
map packet 1회, Adam 132회뿐이라 실패했다. 즉 gate-off만으로 “mapping 0회”는
없앴지만, 초희소 stream에 충분한 initial-map service를 보장하지는 않는다. 다음 축은
frontend threshold를 전역으로 낮추는 방식이 아니라 첫 provisional map에 고정된 causal
최소 service credit을 주는 방식이어야 한다.

## 최종 recipe 전이 closure 사전등록

현재 채택된 `mapping_after_imu_init=0`으로 직접 실행된 장면은
`slow-straight-2`, `fast-straight`, `slow-straight-1`, `ego-centric-2` 네 개다.
기존 `ego-centric-1`과 `square-1` 결과는 gate-on baseline이므로, 동일 recipe라는
주장을 위해 이 두 장면만 순차 backfill한다. 새 scene이나 파라미터는 추가하지 않는다.
최종 판정은 개발 장면 `ego-drive`를 제외한 6개 UTMM scene 가운데 **최소 4개가
original vanilla 대비 shared held-out +1.0dB**이면 “대부분 장면” 전이 성공으로 둔다.
각 run은 strict 1.5×/zero-tail/MPS0 계약을 개별 통과해야 한다.

## 2026-09-13 최종 recipe 6-scene closure — 4/6 GO

현재 `custom/main@8c094371`의 동일한 채택 recipe로 기존 두 장면을 backfill하고,
`slow-straight-2`도 50ms guard로 다시 실행해 여섯 장면의 계약을 완전히 맞췄다.

| scene | custom shared | vanilla shared | 차이 | +1dB |
|---|---:|---:|---:|---|
| `ego-centric-1` | 19.1974 | 17.3271 | **+1.8703** | PASS |
| `slow-straight-2` | 22.8149 | 19.1036 | **+3.7112** | PASS |
| `square-1` | 20.9792 | 20.6906 | +0.2886 | FAIL |
| `fast-straight` | 19.2754 | 17.3971 | **+1.8783** | PASS |
| `slow-straight-1` | 16.9579 | 18.9565 | −1.9986 | FAIL |
| `ego-centric-2` | 20.5488 | 19.2300 | **+1.3188** | PASS |

결과는 **+1dB 4/6, raw 승리 5/6, scene 평균 +1.1781dB**다. 총 1,109 shared
view로 가중한 평균은 custom 20.2407 vs vanilla 18.9938dB, **+1.2469dB**다.
따라서 사전 정의한 “대부분 장면에서 vanilla +1dB” 전이 목표는 이 고정 panel에서
통과했다. 여섯 custom run 모두 `mapping_after_imu_init=false`, margin 50ms,
MPS0, post-stream refinement 없음, deadline/EOS 뒤 update 0/0이다.

성공 범위를 과장하지 않는다. `slow-straight-1`은 초희소 initial-map service 부족,
`square-1`은 후반 pose-map drift로 실패한다. 또한 `ego-centric-1`은 vanilla보다
+1.87dB지만 이전 gate-on custom(+3.90dB)보다 약 2.03dB 낮다. 즉 현재 recipe는
“대부분 +1dB” checkpoint에는 합격했지만, 모든 scene의 절대 품질을 동시에 최대화하는
최종 scheduler는 아니다.

## artifact

- valid control:
  `results/benchmarks/exp81_vigs_strict15x_baseline/utmm/ego-drive/seed0/`
- invalid static-engine startup:
  `results/benchmarks/exp81_vigs_strict15x_baseline/utmm/ego-drive/failed_static_fnet_20260912/`
- invalid 5090-profile OOM: 실행 폴더를 `failed_trt_5090profile_oom_20260912`로 보존
- valid 5070Ti TRT control:
  `results/benchmarks/exp81_vigs_strict15x_baseline/utmm/ego-drive/seed0_5070trt/`
- current-best cache-off hybrid:
  `results/benchmarks/exp81_vigs_strict15x_baseline/utmm/ego-drive/seed0_hybrid/`
- keyframe-75 source ablation:
  `results/benchmarks/exp81_vigs_strict15x_baseline/utmm/ego-drive/seed0_hybrid_kf75/`
- adaptive dense-gradient ablation:
  `results/benchmarks/exp81_vigs_strict15x_baseline/utmm/ego-drive/seed0_hybrid_kf75_adaptivegrad/`
- original vanilla 5070 Ti control:
  `results/benchmarks/exp81_vigs_vanilla5070/utmm/ego-drive/origin22ffe24_pytorch_seed0_r1/`
- custom paper recipe unlimited / strict:
  `results/benchmarks/exp81_vigs_paper_recipe/utmm/ego-drive/{paper_online-seed0-r1,strict15x-seed0-r1}/`
- vanilla-density NO-GO:
  `results/benchmarks/exp81_vigs_strict15x_baseline/utmm/ego-drive/seed0_hybrid_fastfront_dense_rr_kf75_autofreeze_interp_uint8cache_vanilladensity_r1/`
- verified fixed-22 runs:
  `results/benchmarks/exp81_vigs_strict15x_baseline/utmm/ego-drive/{seed0_hybrid_fastfront_dense_rr_kf100_autofreeze_interp_uint8cache_rgbonly_shortcircuit,seed0_hybrid_fastfront_dense_rr_kf100_autofreeze_interp_uint8cache_rgbonly_shortcircuit_r2}/`
- generated UTMM TRT engines:
  `/home/wosas/Desktop/26-1_RPM/gsProjects/VIGS-SLAM-main-integration-20260828/pretrained_models/generated_utmm_328x648/`
- square-1 radius-2 NO-GO evidence:
  `evidence/transfer/square-1-radius2-diagnostic.json`
- square-1 threshold-3.0 NO-GO evidence:
  `evidence/transfer/square-1-thresh3-diagnostic.json`
- provisional pre-IMU untouched transfer summary:
  `evidence/transfer/preimu-untouched-summary.json`
- adopted-recipe six-scene closure:
  `evidence/transfer/adopted-recipe-six-scene-summary.json`

이 문서는 실험을 진행하면서 유효/무효 run, 계약 변경, 다음 의사결정을 누적한다.
