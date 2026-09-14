# exp61 — 팀원 OKVIS2→3dgs-custom 벤치마크(`aria-online-3dgs-bench`) RTX 5070 Ti 재현·비교

- 상태: **완료 (2026-08-09) — OKVIS2 빌드부터 chunk tree·PPM init·view pool·refilter까지
  전 단계를 우리 GPU에서 재현해 팀원 3090 수치와 정합성 확인. 실제 학습 진입점
  (`train_incremental.py`)은 팀원 로컬 미푸시 커밋(real-time 예산 스케줄러)이 없어서
  정식 recipe(G2_budget2000) 재현은 보류하고, 대신 같은 스크립트를 예산 제약 없이
  돌려 순수 학습 wall time(89초/49 events)을 실측했다. VIGS-SLAM과의 구조·트래킹
  정확도·매핑 품질 비교, 그리고 진짜 tracking‖mapping 병렬 실행에 뭐가 필요한지
  코드 레벨로 감사(audit)까지 완료.**
- 배경: 팀원(martian35)이 우리 VIGS-SLAM-custom을 baseline으로 놓고 OKVIS2/OpenMAVIS
  stereo+IMU 트래킹 → 저희 `3dgs-custom`을 incremental로 확장한 매퍼(`train_incremental.py`,
  사실상 저희 exp48의 동일 계보)로 붙인 별도 벤치마크(`martian35/aria-online-3dgs-bench`)를
  돌리고 있었고, 그 결과 VIGS-SLAM 재현 수치가 우리 것(27.86dB)과 크게 달라(1253=24.38,
  305=27.14, 12F=23.64) 원인 규명 요청이 들어왔다.

## 1. 팀원 VIGS 재현치가 낮았던 원인 — 데이터 아니라 하드웨어 + 스크립트 오용

- `build_vigs_aria_input.py`로 aria1253 raw VRS를 다시 변환(1,311 native frame, 우리
  기존 데이터 1,303장과 거의 동일)해서 우리 RTX 5070 Ti로 `run_aria1253_strict27.sh`를
  그대로 돌리자 **27.7735dB**(baseline 27.8464dB 평균과 오차범위 내, background update
  5,994회로 baseline 범위 5,768~6,081과 일치, deadline 97.38/97.65s 통과, tail0)로
  재현됐다. **데이터 준비 과정은 원인이 아님을 확정.**
- 팀원 저장소 `paths.toml`에 GPU가 **RTX 3090**으로 명시돼 있고, `docs/HANDOFF.md` 최상단에
  "target hardware is a 5090, this is a 3090"이라고 스스로 적어뒀다. `vigs.py`의
  `background_polish`는 `idle_long_enough`(메인 tracking/mapping 큐가 비고 idle일 때만)
  게이트라 **GPU가 느릴수록 idle 시간이 줄어 background polish 양 자체가 준다** — 우리
  recipe의 데드라인 여유가 0.27~0.4초로 극도로 타이트해서, 3090에서는 같은 데이터로도
  구조적으로 낮게 나온다. 팀원 자신도 `docs/REPRODUCE.md`에 "VIGS PSNR is ±1 dB run-to-run
  — 22.16–24.38 on 1253-plain across runs"라고 기록(우리 재현성 0.02~0.09dB보다 훨씬 넓음,
  타이트한 예산이 느린 GPU에서 비결정적으로 흔들리는 신호).
- 305/12F/1253rot에 쓴 `run_aria1253_strict27.sh`는 `--length 1253`, `calib/aria1253.txt`,
  `freeze800/pgba1120/late650`이 전부 1253호 전용 하드코딩 — 다른 장면 데이터 경로만
  바꿔 넣으면 시퀀스가 잘리고 경계 비율이 깨진다(exp59에서 이미 진단한 문제와 동일 계열).
  305가 유독 높게 나온 이유(27.14dB, 우리 어떤 305 결과보다 높음)도 이 truncation으로
  뒤쪽 drift 누적 구간이 잘려서였을 가능성이 높다.
- 결론: 팀원분께 (1) 305/12F/1253rot는 `run_aria_strict27.sh <data> <calib> <실제프레임수> <out>`로
  재실행, (2) 1253호 자체 낮은 수치는 GPU 확인용으로 `BACKGROUND_POLISH_DONE steps=` 로그
  공유 요청.

## 2. `aria-online-3dgs-bench` 구조

```
okvis2 (stereo+IMU, CPU) ──┐
                           ├──> chunk tree (COLMAP text + manifest.json) ──> train_incremental.py
OpenMAVIS (stereo+IMU) ────┘                                                 (3dgs-custom fork)
```
- `third_party.lock`: `mapper_3dgs` origin이 `https://github.com/sawo0150/3dgs-custom`
  (우리 소유), pin된 커밋(`1832189...`)이 origin에 없음 — 로컬 미푸시 커밋으로 추정,
  origin/main HEAD(`b184a3d`, 우리 로컬 3dgs-custom과 동일)로 대체해 진행.
- VIGS 트랙에서 사용한 PGBA 크래시 수정도 팀원이 **독립적으로 별도 위치**
  (`vigs/factor_graph.py`, t1 이후 edge drop)에서 찾아 고쳐뒀음을 확인(우리 exp60 수정과
  다른 지점, 같은 버그 계열).

## 3. OKVIS2 빌드 + stage 1~6 재현 (RTX 5070 Ti / Ryzen 7 5700X)

워크스페이스: `/home/wosas/Desktop/26-1_RPM/gsProjects/okvis2_bench_5070ti/`

| 단계 | 내용 | 결과 |
|---|---|---:|
| 빌드 | okvis2 + submodule(DBoW2/brisk/ceres-solver/googletest/opengv), `-DUSE_NN=OFF -DHAVE_LIBREALSENSE=OFF`(LibTorch·realsense 회피) | 100% 클린 빌드, `libatlas-base-dev` 1개만 추가 설치 필요 |
| stage1 트래킹 | stereo(slam-L+slam-R)+imu-right, `1253_online.yaml`(팀원 config 그대로 재사용 — 같은 물리 기기라 T_SC 공유) | **online 49.3s / mapdump 53.1s** (팀원 Threadripper 3960X 82.3s보다 빠름) |
| stage2 chunk tree | `build_okvis_chunks.py` | **49 chunks, mean kf interval 1364ms** — 팀원 데이터셋 스펙과 정확히 일치 |
| stage3 PPM init | `ppm_from_omnidata.py`(우리 `build_depthmono_ppm_chunks.py` 포팅판, omnidata checkpoint 재사용) | SLAM 3,596 / PPM 179,773 포인트, corr_med 0.8487 |
| stage4 view pool | `build_view_pool.py` | 1,041 train views/49 chunks, holdout 교집합 0 확인 |
| stage5 refilter | `refilter_init.py`(cheap variant: cam-target 50/rebuild-every 20/window 30) | SLAM 3,399(−5.5%), PPM 159,141(−11.5%), 28.5ms/event |
| stage6 g1ify | 256px 리사이즈 + intrinsics 재계산 | 완료 |

**환경 재사용**: 팀원의 `conda-3dgs-carve-bench.yml`(colmap+conda-forge cuda 통째, 무거움)을
새로 안 만들고 기존 `3dgs` env(torch 2.8.0+cu128 + diff_gaussian_rasterization/simple_knn/
fused_ssim 이미 설치됨)로 그대로 커버 — 사용자 요청("저장공간 더 차지하는거 싫어서")대로
디스크 추가 사용 없이 재현.

**Python 버전 이슈**: `merge_chunks.py`가 `int | None`(PEP604, 3.10+) 문법을 써서 `3dgs`(3.9)
env에서 실패 → `refilter_init.py`만 `vigs-slam-5090` env(3.10)로 우회.

## 4. 막힌 지점 — real-time 예산 스케줄러 미존재

`run_okvis_pipeline.py`가 `train_incremental.py`에 넘기는 `--mapper_budget_ms`,
`--mapper_min_iters`, `--mapper_max_iters`, `--carve_birth`, `--carve_margin`,
`--benchmark_jsonl`이 우리가 받은 origin/main 버전에는 **없음**(`argparse: error:
unrecognized arguments`). §2에서 확인한 대로 `mapper_3dgs`의 실제 pin 커밋이 origin에
없는 것과 정합 — 이 real-time 예산 스케줄링 기능은 팀원 로컬에만 있고 아직 push 안 된
것으로 보인다. **사용자 결정: 팀원분께 실제 파일/커밋 요청, 직접 재구현은 보류.**

## 5. 예산 없이 직접 실행 — 순수 incremental 학습 wall time 실측

`train_incremental.py`(=exp48의 그 스크립트, docstring "exp48 incremental v2 — local
window + freeze-when-stable")를 지원되는 인자만으로 직접 호출:
`--window_size 200 --iters_per_event 177 --init_source hybrid --densify_until_iter 30000
--resolution 1`(177은 G2_budget2000의 평균 iters/event를 그대로 흉내).

**결과: 89초** (22:01:59~22:03:28), 49 events / 8,673 iterations, 최종 N=915,084,
`point_cloud/iteration_8673/point_cloud.ply` 저장 완료. GPU 2.1GB만 사용, 82% util.
⚠ 이건 "GPU가 낼 수 있는 최고 속도"이지 실시간 예산 강제하에 나온 시간이 아니다 — budget
스케줄러가 없어 그냥 끝까지 밀어붙인 결과. 1253 실제 녹화 길이 65.5초 대비 매핑만으로
1.36배; 여기에 트래킹 49.3초를 순차로 더하면(현재 파이프라인은 병렬 실행이 안 됨, §7)
138초로 65.5초의 2배를 넘는다.

## 6. OKVIS2 트랙 vs VIGS-SLAM 비교

**트래킹 정확도(ATE-Sim3, evo, MPS 대비)**

| 장면 | OKVIS2 stereo+IMU | VIGS vanilla(mono) | VIGS 채택 recipe(mono, 속도튜닝) | ORB-SLAM3 stereo |
|---|---:|---:|---:|---:|
| aria1253 | 1.57cm | 1.3cm | 4.9cm | 13.1cm |
| aria1253rot | — | 1.6cm | 8.2cm | — |
| 301_305 | 3.50cm | 20.1cm | 90.9cm | 9.0cm |
| 301_12F | 11.26cm | 40.6cm | 134.8cm | 39.9cm |

OKVIS2는 1253(쉬운 장면)만 VIGS vanilla에 근소하게 밀리고, 305·12F에서는 VIGS vanilla
대비 5.7배·3.6배, 우리 채택 recipe 대비 26배·12배 정확 — 스테레오 캘리브레이션 baseline이
metric scale을 무조건 관측 가능하게 하는 반면, VIGS는 단안+IMU라 305의 실패 원인(exp59:
저-여기(low-excitation) monocular scale drift)이 구조적으로 존재하지 않음.

**매핑 품질(held-out PSNR)**

| 장면 | VIGS 채택 recipe(진짜 실시간 증명됨) | OKVIS2→3dgs-custom(배치 재현, 실시간 미증명) |
|---|---:|---:|
| aria1253 | **27.86dB** | 24.83dB(팀원 H0) |
| 301_305 | 18.74dB | **27.56dB**(팀원 WING_305) |
| 301_12F | 25.90dB | 25.56dB(팀원 B12_g6_best, 거의 동률) |

1253은 VIGS가 이기고 305는 OKVIS2 쪽이 압도적, 12F는 동률. 단, OKVIS2 수치는 시간제약 없이
전체 배치를 돌린 뒤 매퍼 부분에만 사후로 예산을 매긴 것이라 "실시간으로 이 품질이 나온다"는
아니고 "이 아키텍처의 품질 상한"에 가깝다.

## 7. 진짜 병렬(tracking‖mapping) 실행에 뭐가 필요한가 — 코드 레벨 감사

**이미 존재하는 것 (재사용 가능)**:
- OKVIS2 자체에 **라이브 스트리밍 기반이 이미 있다.** `okvis_apps/src/okvis_app_realsense.cpp`가
  `estimator.setBlocking(false)` + `realsense->setImuCallback/setImagesCallback` +
  `estimator.setOptimisedGraphCallback(...)`로 실제 라이브 카메라를 비동기 처리하는
  `while(true) { estimator.processFrame(); ... }` 루프를 이미 구현해 놓았다(RealSense용).
  우리가 지금까지 쓴 `okvis_app_synchronous.cpp`는 `setBlocking(true)`로 전체를 다 읽고
  CSV를 쓰는 배치 모드였을 뿐, **OKVIS2 라이브러리 자체는 이미 비동기/콜백 인터페이스를
  지원한다.**
- 콜백 시그니처(`TrajectoryOutput::processState(state, trackingState, updatedStates,
  landmarks)`, `ThreadedSlam.hpp`의 `landmarksPublish`)가 **포즈뿐 아니라 갱신된 landmark도
  함께 넘겨준다** — `build_okvis_chunks.py`가 필요로 하는 정보(포즈+landmark)가 이미 콜백
  인자에 다 들어있다.

**없는 것 (새로 만들어야 함)**:
1. Aria용 실시간 소스 클래스 — `okvis::Realsense`와 같은 인터페이스(`setImuCallback`/
   `setImagesCallback`/`startStreaming`)를 구현하되, RealSense SDK 대신 라이브 Aria
   하드웨어 또는 VRS를 실시간 페이싱으로 재생(VIGS의 `--realtime_replay
   --replay_time_scale`과 같은 방식)하는 소스가 없음.
2. `build_okvis_chunks.py`를 대체할 **incremental 콜백 핸들러** — 지금은 완성된
   `okvis2-slam_trajectory.csv`를 사후에 파싱하는 구조. `setOptimisedGraphCallback`에
   새 핸들러를 걸어 keyframe이 확정되는 즉시(콜백 인자로 이미 받는 포즈+landmark로)
   그 자리에서 chunk를 만들어야 함.
3. PPM/pool/refilter는 지금 전부 tree 전체를 한 번에 도는 배치 스크립트 — per-event
   증분 처리로 재작성 필요(가장 손이 많이 가는 부분, refilter의 carve-field 재구성
   비용이 12F에서 이미 병목이었던 걸 감안하면(§ exp59/HANDOFF §7l·7q) 실시간 예산
   안에 넣기가 특히 까다로움).
4. `train_incremental.py`는 `manifest = json.loads(...)`로 **매니페스트를 시작 시 한 번에
   고정 리스트로 로드**하고 `for event_idx, chunk in enumerate(manifest)`로 순회한다
   (코드 137/165행 확인) — 큐/디렉토리를 폴링하며 새 chunk를 기다리는 구조가 아니라서,
   라이브 입력을 받으려면 이 루프 자체를 바꿔야 함. 내부 학습 로직(윈도우 풀링, per-event
   iteration)은 그대로 재사용 가능.
5. §4의 real-time 예산 스케줄러(`--mapper_budget_ms`)도 어차피 필요 — 지금은 그마저도
   없어서 있어도 "무제한 속도로 도는" 상태.

**결론**: VIGS-SLAM은 이미 이 전체 문제(트래킹↔매핑 동시성)를 단일 프로세스/스레드
구조로 풀어놓은 상태고, OKVIS2 쪽은 트래킹 라이브러리 자체엔 필요한 콜백 인프라가 이미
있지만 그 위에 얹을 incremental 브릿지·매퍼 폴링 루프가 전혀 없다 — "빈 데서 시작"은
아니지만(1번 항목 덕분에 예상보다 적은 작업), 여전히 신규 엔지니어링이 필요하다.

## 산출물

- `/home/wosas/Desktop/26-1_RPM/gsProjects/okvis2_bench_5070ti/` — OKVIS2 빌드, chunk
  tree, 학습 결과 전체
- `runs/train_g2_manual/point_cloud/iteration_8673/point_cloud.ply` — 89초 학습 결과 PLY
  (N=915,084), Drive `gs_floaterLab/exp61_okvis2_3dgs_bench_5070ti/`로 공유
- `/tmp/.../scratchpad/teammate_bench/aria-online-3dgs-bench` — 팀원 저장소 SSH clone
  (읽기 전용 분석용, 로컬 실행 편의를 위해 경로만 패치)

## 다음 단계 (미착수)

1. 팀원분께 `mapper_3dgs`의 real-time 예산 스케줄러 커밋 요청 → 받으면 G2_budget2000
   정식 recipe로 1253/305/12F 전부 우리 GPU에서 재현, PSNR 재검증
2. §7에서 확인한 "이미 있는 콜백 인프라"를 활용해 Aria 라이브 소스 클래스 프로토타입
   (없어도 되는 나머지 4개 항목보다 훨씬 적은 작업으로 시작 가능)
3. VIGS-SLAM의 GPU-공유 구조적 한계(트래킹↔매핑 제로섬)와 OKVIS2의 CPU/GPU 분리 구조를
   결합하는 하이브리드 아키텍처가 근본 목표(North Star: 흑백 정밀 위치 + RGB 실시간
   고품질 지도)에 더 부합할 수 있음 — 다만 이건 위 3개 미해결 엔지니어링 항목이 끝나야
   판단 가능
