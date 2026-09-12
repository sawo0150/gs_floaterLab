# exp77 — RTX 3070 inner packet-RR ablation

2026-09-13. 상태: **52개 run 완료. 예산15에서 기존 ERCB와 coverage1 모두 RR 대비 6/6 개선 재현.**

최종 결과와 주장 범위는 [FINAL_REPORT.md](FINAL_REPORT.md), 전체 검증 수치는
[evidence/final_ablation.json](evidence/final_ablation.json)을 우선 참조한다.
아래 실행 중/예약 항목은 당시 기록이며 현재 모든 예약 run은 종료됐다.

## Seed0 결과

### 예산 ablation seed0 완료 (2026-09-13)

| Scene | update/event | ERCB − RR | coverage1 − RR |
|---|---:|---:|---:|
| UTMM | 15 | +0.4446 | +0.4295 |
| UTMM | 30 | +0.1345 | +0.2106 |
| UTMM | 60 | −0.0358 | +0.0005 |
| RPNG | 15 | +1.1765 | +1.1832 |
| RPNG | 30 | −0.0229 | −0.0253 |
| RPNG | 60 | −0.1988 | +0.0810 |

추가12 runs 및 기존60 reference의 matched 계약 검사를 통과했다.
낮은 예산15에서는 양쪽 scene에서 양수지만 budget30 RPNG는 소폭 음수다.
따라서 모든 budget에서 이긴다는 주장이 아니다. training CUDA 시간은 같은 budget15
RR/ERC B/coverage1 UTMM 4.24/4.18/4.21s, RPNG 13.15/13.16/13.05s로 비슷하다.
GPU 시간 차이를 전체 mapping overhead 또는 실시간 SLAM 증거로 취급하지 않는다.
15-budget seed1/2 재현성은 다음 단계로 계속 실행한다.

### Coverage1 seed 반복 완료 (2026-09-13)

| coverage1 − RR (dB) | seed0 개발 | seed1 | seed2 | 3-seed 평균 |
|---|---:|---:|---:|---:|
| UTMM | +0.0005 | −0.0556 | +0.1220 | +0.0223 |
| RPNG | +0.0810 | +0.2109 | +0.2594 | +0.1838 |

seed1/2 12 runs 완료, 네 matched group 계약 검사 통과. 독립 seed 평균 +0.1342 dB,
4개 중 3개 양수. 6개 개발+반복 pair 평균 +0.1031 dB이나 seed0는 선택 편향이 있다.
RPNG는 3/3 양수지만 interval-base 대비 추가 이득은 +0.0027/+0.0169/+0.0253에
불과하다. UTMM에서는 interval-base 대비 +0.1443/+0.1642/+0.2126으로 보정 효과가
뚜렷하지만 RR 대비는 작고 부호가 바뀐다. 따라서 범용 가속으로 과장하지 않는다.
coverage1은 6/6에서 zero-service를 RR보다 줄였으나 served-only 평균 delay까지
개선한다고 주장하지 않는다. 후속 event15/30 ablation이 이어서 실행된다.

### 예산 ablation 준비 (미실행)

진행 정정: event15 seed0는 두 장면 완료. RR 대비 ERCB/coverage1은 UTMM
+0.4446/+0.4295, RPNG +1.1765/+1.1832 dB. 그러나 zero-service는 양쪽에서 증가했다.
event30 완료 후 `run_low_budget_validation.py`가 event15 seed1/2 × 두 scene ×
RR/ERC B/coverage1 12개 명령을 재튜닝 없이 실행하도록 예약했다.
manifest: `outputs/exp77_low_budget_validation/manifest.json`. seed0 결과만으로
범용 가속을 주장하지 않으며 event30/60의 불리한 결과도 유지한다.

`run_budget_ablation.py`를 시작해 seed 반복 PID 36650 뒤에 실행 예약했다.
12개 반복 run의 update/평가 기본 계약을 읽어 검증한 뒤에만 준비된 12개 예산 명령을
실행한다. 아직 예산 실험의 GPU run은 시작하지 않았다. GPU 점유/3 GiB reserve 검사 유지.

`prepare_budget_ablation.py`로 기존 event60 arrival을 event30/event15로 정확히
재매핑했다. 전체 frame/event 및 순서 유지, 첫 update1, last-arrival 종료 유지.
각 예산 RR/기존 ERCB/coverage1 × 두 scene seed0 총12개 명령을
`outputs/exp77_budget_ablation_plan/manifest.json`에 고정했다. 아직 학습하지 않았다.
기존 event60 결과도 함께 보고하고 유리한 예산만 선택하지 않는다. LR horizon은
각 예산에 맞춰 동일 정규화하므로 예산 간 절대 차이는 LR 효과와 분리되지 않지만
각 예산 내 scheduler 비교의 LR은 동일하다. 현재 seed 반복 결과를 먼저 확인한다.

### Window screen 완료 (2026-09-13)

| RR 대비 최종 dB | UTMM | RPNG |
|---|---:|---:|
| window_control | −0.0612 | −0.1627 |
| window ERCB | −0.0934 | −0.1588 |

4개 run 계약 검사를 통과했지만 모든 평가 지점에서 RR 미달이다. window 후보는
현재 설정에서 기각한다. zero-service는 RR 136/233 대비 window 140/234로 개선되지 않았다.
draw CPU는 window 27.4/84.8 ms로 가볍지만 품질 개선 없이 가벼운 것만으로 채택하지 않는다.
이어서 coverage1 seed1/2 재현성 12 runs가 시작됐다. 조건/예산 변경은 없다.

### 후속 coverage 개발 screen (2026-09-13, 완료)

재현성 단계: `run_coverage_validation.py`로 seed1/2 × 두 scene ×
RR/interval-base/coverage1의 12개 명령을 사전 고정했다. window screen 완료 뒤에만
순차 실행한다. quota1/gamma log3/K8/예산을 재튜닝하지 않으며 seed별 실행 순서는
미리 회전시켰다. 출력 `outputs/exp77_coverage_validation/manifest.json`.
이것은 같은 개발 장면의 seed 반복이지 독립 장면 검증은 아니다.

| RR 대비 최종 dB | UTMM | RPNG |
|---|---:|---:|
| interval-base | −0.1438 | +0.0784 |
| coverage1 | +0.0005 | +0.0810 |
| coverage2 | −0.0578 | −0.0585 |

6개 run의 update/arrival/held-out/grid 검사를 통과했다. coverage1은 유일하게
두 장면에서 비음수지만 UTMM은 사실상 동률이고 초기 두 평가에서는 두 장면 모두
RR보다 낮다. 아직 가속/일반화 성공이 아니다. RPNG interval-base도 비슷한 개선이라
RPNG coverage1 이득을 count bonus에 단독 귀속할 수 없다. window screen이 이어서 시작됐다.

Window 후속 screen도 `run_window_screen.py`로 예약했다. coverage PID 35165의
실제 cmdline이 살아 있는 동안 대기하고 6개 summary 존재 확인 후에만 시작한다.
두 scene × window_control/window, seed0 고정으로 총 4 runs이다. window_control은
동일 32-ticket 예약 및 Gumbel shuffle에 count bonus만 0으로 두어 예약/재셔플 효과와
count 보정 효과를 분리한다. manifest는 `outputs/exp77_window_screen_s0/manifest.json`.
실제 GPU 직전 충돌 검사는 각 run wrapper가 수행한다. 아직 이 screen의 결과는 없다.

追加 구현 `runtime/window_ercb.py`: causal RR queue의 다음 최대 32 ticket만 예약하고
frame-count relative-floor 점수+Gumbel로 순서를 재배치한다. interval top-K는 사용하지 않는다.
`test_window.py`의 8 seeds에서 gamma0 exact RR, 정적 pool epoch별 각 frame 1회,
동적 admission의 선택 적법성 및 actual count 합 검사를 통과했다. 아직 GPU 품질 미검증.
주의: 동적 pool에서는 예약된 window 안으로 신규 frame이 들어가지 못하므로 원래 RR과
동일 draw multiset이라는 보장은 없다. window 완료까지 신규 삽입 영향이 최대 31 updates
지연될 수 있으며, 전체 first-service의 상한을 보장하는 것은 아니다.

CPU 구조 진단: `audit_interval_measure.py`에서 K=8, interval 크기 [1,1,1,1,1,1,1,32]이면
gamma0에서도 각 interval 비율이 정확히 1/8로 측정된다(8,000 draws).
frame-uniform 목표의 큰 interval 비율 32/39와 다르다. top-K interval exclusion은
size base measure를 전체 블록 marginal에 보존하지 않는다. 이는 수학적 반례이지
실제 PSNR 손실 원인 확정은 아니다. 다음 구조 후보는 epoch coverage를 유지하면서
count deficit이 순서만 조절하도록 만드는 방향이며, 아직 구현/품질 검증 전이다.

`run_coverage_screen.py`: 기존 두 장면·seed0·예산·loss·초기화 그대로 유지하고
interval_base(gamma0), coverage1(첫 1회까지), coverage2(첫 2회까지)를 비교한다.
공통 inner persistent RR, K8, coverage의 gamma=log3. coverage2는 repo에 이미
있는 TwoPass 구현이며 새 방법이라고 주장하지 않는다. coverage1은 같은 식의 quota1이다.
`w_j=|G_j| exp(gamma max(0,1-c_j/(quota |G_j|)))`로 초기 서비스 완료 후 보정이 사라진다.
가중치 없는 interval-base도 full-pool RR과 같지 않으므로 별도 대조군으로 둔다.
전체 6개 명령은 시작 전에 `outputs/exp77_coverage_screen_s0/manifest.json`에 고정했다.
5 seeds gamma0 추출 동일성 및 causal count sanity 검사를 통과했다.
이 데이터는 개발용이며 양수 결과가 나와도 독립 검증이 필요하다. 기존 실패 결과는 유지한다.

| Scene | RR | ERCB | packet | packet − RR |
|---|---:|---:|---:|---:|
| UTMM square-1 | 18.7095 | 18.6738 | 18.7271 | +0.0175 |
| RPNG table_01 | 24.0392 | 23.8403 | 23.8348 | −0.2044 |

held-out 평균 PSNR(dB). UTMM 202 / RPNG 314 views. 실제 updates 4,741 / 14,581,
post-update 평가, 동일 arrival/held-out/evaluation grid 및 ERCB–packet outer hash 검사를 통과했다.
packet은 두 장면 모두 25%·50% update 시점에서 RR보다 낮았다. 최종 UTMM의 미소
양수만으로 가속/재현성을 주장하지 않는다. seed1은 자동 실행하지 않았다.

- ERCB의 late-third는 RR 대비 UTMM +0.0103 / RPNG +0.4305 dB지만 전체는
  각각 −0.0358 / −0.1988 dB다. 하위/후반 개선과 전체 품질은 구분된다.
- zero-service (RR/ERC B/packet): UTMM 136/95/222, RPNG 233/205/256.
  packet은 ERCB 대비 미학습 frame 및 served-only 첫 서비스 평균 지연을 늘렸다
  (UTMM 216→394, RPNG 250→380 updates). 미서비스 frame은 지연 평균에서 제외된다.
- CUDA training 시간 RR/ERC B/packet: UTMM 15.28/14.59/14.71 s,
  RPNG 50.81/51.02/50.82 s. 로딩·평가 제외, 단일 seed·고정 순서라 속도 우위 근거로 삼지 않는다.
- 근거: `outputs/exp77_full_v2_seed0/{utmm_square1_full,rpng_table01_full}/comparison_s0.json`.
  이는 fixed pose/init·topology replay 결과이지 strict online SLAM 검증이 아니다.

## 실제 실행 (2026-09-13)

- 사용자 복사 완료 확인 후 `run_full_v2.py` 실행. UTMM → RPNG, 각 RR → ERCB → packet.
- 출력: `outputs/exp77_full_v2_seed0/`. 세 arm 완료 시 scene별 comparison JSON 자동 생성.
- UTMM full의 깨진 서버 절대경로 링크 1,614개를 기존 로컬 원본으로 연결했다.
  원본 이미지 삭제/복사는 없으며 이전 링크는 출력의 `link_repairs.json`에 보존했다.
- COLMAP 이름의 절대경로/상위 디렉터리 이동은 계속 차단하되 외부 원본을 가리키는
  이미지 symlink를 preflight에서 허용했다.
- UTMM 4,741 / RPNG 14,581 updates, resolution4, seed0, 고정 topology.
- 남은 디스크 3 GiB 미만 또는 arm 실패 시 후속 실행 중단. 자동 삭제/재튜닝 없음.
- final VIGS pose 및 누적 geometry 초기화의 **noncausal scheduler isolation**이다.

## 질문과 고정 비교

같은 growing dense pool에서 기존 ERCB의 interval 선택을 정확히 유지한 채,
inner RR을 작은 묶음의 반복 순환으로 바꾸면 제한된 예산의 held-out PSNR이 개선되는가?

| Arm | Outer | Inner |
|---|---|---|
| rr | causal full-pool RR | 기존 그대로 |
| ercb | exp75 relative-floor, rho=.5, gamma=log(3), K=8 | 기존 persistent RR |
| packet | 위 ERCB와 step별 동일 interval | random packet m=4, r=2회, pass마다 비복원 shuffle |

packet membership은 무작위이며 temporal-stratification은 이번 비교에서 섞지 않는다.
각 add()가 닫힌 interval을 정의한다. interval 내 신규 삽입/분할은 이번 구현 범위 밖이다.
부분 packet도 r회 사용한다. 모든 frame은 pool에 남으며 full cycle에서 r회씩 사용한다.
r=1은 기존 ERCB와 frame 선택까지 정확히 같도록 구현했다.

## 계약

- 사용자 복사 완료 뒤 실제 경로/포맷/pose/init 출처부터 감사한다. 복사 중 데이터는 사용하지 않는다.
- 동일 source, seed, 초기화, 해상도, RGB loss, 도착 schedule, 실제 optimizer update 수.
- `--eval` llffhold-8. `test.txt`는 split 근거로 사용하지 않는다.
- 고정 topology: `--densify_until_iter 0`, carve/plateau 없음. Gaussian 파라미터 최적화는 유지.
- frame admission은 원래 arrival schedule 그대로. 미래 RGB로 init을 만들지 않는다.
- full VIGS pose/init을 가져오면 noncausal scheduler-isolation으로 명시하고 strict SLAM이라 부르지 않는다.
- 도착 schedule의 마지막 training arrival에서 종료, optimizer tail 0. 데이터 경로 없이 임의 schedule을 만들지 않는다.
- 먼저 seed0 세 arm을 실행, 양성 신호가 있으면 seed1 반복. 실패 시 유리한 설정만 찾는 sweep 금지.
- 3070 8GB: 우선 resolution=4, image data_device=cpu, arm은 순차 실행. OOM이면 전 arm 동일 조건 재설정.
- 현재 runner는 동일 COLMAP 초기 PLY로 시작한다. 학습 checkpoint 재개는 sampler history와
  계측 원점이 달라지므로 명시적으로 차단했다. 필요하면 별도 분기 계약을 구현한다.

## 구현상 교란 방지

기존 outer/inner가 같은 Python RNG를 공유한다. candidate는 legacy inner를 shadow로 진행해
그 RNG 소비를 그대로 보존하고, 실제 packet은 별도 RNG로 선택한다. Outer sequence 동일성은
CPU 테스트와 실제 실행의 `outer_trace_sha256`으로 검사한다. shadow 비용도 overhead에 포함한다.

기존 train.py는 마지막 draw의 optimizer step을 생략하고 report/PLY를 step 전에 수행한다.
이번 세 arm은 모두 opt-in `--fixed_topology_step_before_report`를 사용해 마지막을 포함하여
draw마다 update하고 post-update 상태를 평가/저장한다. 기존 default 동작은 유지한다.
CUDA training timing은 이 옵션에서 optimizer까지 포함하며 evaluation 시간은 제외한다.
매-step synchronization이 있으므로 production throughput 수치가 아니라 동일 계측 조건의 비교다.

## 판정/로그

- 주 지표: 동일 update 예산의 held-out PSNR 곡선/최종값. 가능하면 공통 PSNR 도달 GPU 시간.
- 별도 시간 지표: training CUDA ms, 전체 process wall time, scheduler CPU ns.
- 하위 품질: per-view PSNR에서 late-third/worst-Q1. train PSNR을 품질 판정에 사용하지 않는다.
- 기회: unique selected, zero-service 수, 첫 selection까지 update 지연, frame/interval count.
- count 개선/크래시 없는 완주만으로 PSNR 가속을 주장하지 않는다.
- 고정 compute-clock arrival 실험이지 실제 sensor-time 1.5x 실시간 보장은 아니다.
- packet이 first-service를 늦출 수 있다. ERCB나 packet 자체의 bounded latency 보장은 주장하지 않는다.

## 실행 준비물

- local repo: `.codex-work/3dgs-custom-main` (main `da1dbda` 위 local patch)
- Python: `/home/wosasa/miniconda3/envs/3dgs/bin/python`
- CUDA compiler: 동일 conda env의 nvcc 11.8, PyTorch 2.1.2+cu118
- GPU: RTX 3070 Laptop 8GB, sm_86
- `prepare_run.py`: 데이터 경로/도착표를 검사하고 실행 명령 manifest 생성. 기본은 학습하지 않음.
- `run_training.py`: 기존 train.py 실행 wrapper, candidate 주입/계측/outer pairing 기록.
- `summarize.py`: 세 arm의 update/arrival/held-out/outer trace 일치를 검사하고 품질·기회·시간 지표 요약.
- CPU tests: repo `tests/test_packet_scheduler.py`

데이터 복사 완료 후 source 디렉터리와 causal arrival JSON 위치를 확인한다.
plain RGB만 있고 pose/init/arrival 정보가 없으면 먼저 변환 계획을 확정해야 한다.

## 준비 체크리스트

- [x] 원격 main과 local 기준 커밋 일치 확인 (2026-09-13)
- [x] packet scheduler opt-in 구현
- [x] CPU 5 tests 통과: outer pairing / r=1 / ragged cycle / count bound / invalid args
- [x] CUDA extension 설치 및 render/backward/KNN synthetic smoke 통과 (`evidence/cuda_smoke.json`)
- [x] main `da1dbda` pull 및 local patch 복원, 기존 CPU 30 + 신규 5 tests 통과
- [x] synthetic 세 arm 각 12 updates → post-update 평가/PLY/summary 전 경로 통과 (`evidence/integration_smoke.json`)
- [ ] 실제 데이터 입력 감사 및 세 arm 명령 생성
- [ ] seed0 실제 학습 및 held-out 결과
- [ ] 필요 시 seed1 및 VIGS 후속 검증

## 서버 동기화 기록

5070Ti 서버 push 뒤 main `8568fd6` → `da1dbda` fast-forward pull 완료.
서버 변경은 신규 latency 모듈/runner 10개 파일이었으며 local train.py/packet 변경과 충돌 없었다.
pull 전 변경은 `local_changes_before_server_sync.patch` 및 repo stash에 보존했다.
동기화 후 변경까지 포함하는 patch는 `local_changes_da1dbda.patch`다.
기존 exp75 상대-floor를 비교 기준으로 유지한다. 새 latency 후보로 baseline을 임의 교체하지 않는다.

빌드한 pinned submodules: rasterizer `0f72892600605c8df6c2feea35da9bd30bf0201e`,
simple-knn `86710c2d4b46680c02301765dd79e465819c8f19`.
기존 3dgs conda env에 두 extension만 설치했고 torch/CUDA 버전은 바꾸지 않았다.
`train.py --help` import/CLI 검사도 통과했다.

## 데이터 복사 완료 후 사용법

`provenance.json`에는 `pose_source`, `init_source` 설명과
`init_uses_future_training_rgb: false`를 실제 출처에 맞게 작성한다.
이는 provenance 선언이지 온라인 인과성을 자동 증명하는 파일이 아니다.

```bash
/home/wosasa/miniconda3/envs/3dgs/bin/python context/experiments/exp77/prepare_run.py \
  --source /absolute/completed/dataset \
  --arrivals /absolute/causal_arrivals.json \
  --provenance /absolute/provenance.json \
  --output /absolute/new/exp77_runs --seed 0 --copy-complete
```

위 명령은 학습하지 않는다. COLMAP camera/이미지 decode/준비된 초기 PLY/llffhold-8 train names/
schedule 단조성/첫 training arrival/zero-tail을 검사하고 `commands_s0.json`을 생성한다.
순차적으로 각 `argv`를 지정 `cwd`에서 실행한다. run wrapper는 기존 output 또는 GPU compute
프로세스가 있으면 거부한다. 원본 데이터에 PLY를 자동 생성하지 않는다.

```bash
/home/wosasa/miniconda3/envs/3dgs/bin/python context/experiments/exp77/summarize.py \
  --runs /absolute/new/exp77_runs --seed 0
```

첫 service 평균은 service를 받은 frame만 대상으로 하므로 `zero_service`와 반드시 함께 해석한다.
총 wall time에는 입력 로딩과 평가가 포함된다. training CUDA 시간과 혼동하지 않는다.
prepared command는 checkpoint 재개나 Blender 포맷을 지원하지 않는다.
