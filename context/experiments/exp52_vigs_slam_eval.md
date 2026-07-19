# exp52 — VIGS-SLAM(ECCV2026, cvg) 평가: 클론·빌드·베이스라인 실행

> 목적: exp51에서 아이디어만 참고하던 VIGS-SLAM을 실제로 클론·빌드해서 (1) 우리가 exp51
> 문서화 때 논문/코드 스캔만으로 추정했던 메커니즘을 소스 직접 읽기로 검증/정정하고,
> (2) 우리 1253 데이터(Aria RGB+IMU)에 실제로 돌려서 "실시간(라이브) 지향 단안 파이프라인이
> 어느 수준까지 나오는가"를 직접 관찰한다. **VIGS 알고리즘 코드는 무수정 — 환경/빌드
> 호환성 패치만.**

## 셋업

- `https://github.com/cvg/VIGS-SLAM` → `/home/wosas/Desktop/26-1_RPM/gsProjects/VIGS-SLAM` clone
  (submodule 전체 `git submodule update --init --recursive`)
- `repos/main/VIGS-SLAM` 심링크 연결 (Photo-SLAM과 동일 관례)
- conda env `vigs-slam-5090` (RTX 5070 Ti, sm_120, Blackwell — README 타깃인 5090과 동일 세대)

### `environment_5090.yaml` 그대로는 4번 실패 — 실제로 고친 것

1. **`lietorch==0.2`가 PyPI에 없음** — 그 자체가 `thirdparty/lietorch_5090` fork의 자체 버전
   태그일 뿐. pip 배치에서 제외하고 README 3단계(`python setup.py install`, repo root)로
   `vigs_backends`+`lietorch_backends`를 함께 빌드해야 함(gencode에 `compute_120,sm_120` 포함
   — `thirdparty/lietorch_5090/setup.py` 자체는 sm_75까지만 있어 **직접 빌드하면 안 됨**,
   root `setup.py`가 진짜 빌드 경로).
2. **`torch-scatter`가 torch 설치 전에 먼저 빌드되려 함** — 배치에서 제외, torch 설치 후
   `--no-binary=:all: --no-build-isolation`으로 별도 설치(README 그대로).
3. **`nvidia-cuda-runtime-cu12` 명시적 pin이 torch 요구 버전과 충돌** — pin 제거, torch에
   위임.
4. **`pycuda`(TensorRT 전용 옵션 기능)가 CUDA 헤더 없어 빌드 실패** — TensorRT/ONNX 관련
   패키지 전부 제외(옵션 기능, 평가엔 불필요).
5. **`diff-gaussian-rasterization`이 `uint32_t`/`std::uintptr_t` 미정의로 컴파일 실패** —
   `cuda_rasterizer/rasterizer_impl.h`에 `#include <cstdint>` 한 줄 추가로 해결(신 컴파일러에서
   흔한 3DGS 래스터라이저 호환성 버그, 우리 3dgs-custom/Photo-SLAM에서도 이미 겪었던 패턴).
6. **conda-forge식 CUDA 툴킷 레이아웃** — `cuda.h`가 `$CUDA_HOME/include/`가 아니라
   `$CUDA_HOME/targets/x86_64-linux/include/`에 있음 → `CPATH`로 지정. `CUDA_HOME`은 우리
   `envs/3dgs`(CUDA 12.8, nvcc 있음)를 재사용하되 **PATH엔 append**(prepend 금지 — 앞에 붙이면
   `python`/`pip`가 3dgs env 걸로 잘못 resolve돼 cp39 wheel이 섞여 들어가는 사고가 실제로
   한 번 남).

### SIGSEGV 근본원인 — `PYTHONFAULTHANDLER=1`로 특정

데모 실행이 keyframe 1 처리 중 재현성 있게 SIGSEGV. gdb는 멀티프로세스(spawn) 구조와
충돌해(파이프 핸드셰이크 깨짐, `EOFError: EOF when reading a line`) 못 잡았고,
`PYTHONFAULTHANDLER=1 python -X faulthandler`로 Python 프레임 스택을 직접 잡아냄:

```
vigs/imu.py:170 in integrate_once  →  deltaR = sp.SO3.exp(dt * gyr)
```

`sophuspy`가 **numpy 2.x와 ABI 불일치인 PyPI 프리빌트 wheel**로 깔려 있었음(README가
`--no-binary=:all:`을 명시한 이유였는데, 처음엔 `-U`만 줘서 실제 재빌드가 안 됐던 게 원인).
`pip install --force-reinstall --no-binary=:all: --no-cache-dir sophuspy`로 소스 재빌드 →
해결. 부수적으로 numpy가 2.4.6까지 끌려올라가 opencv-python(`<2.3.0` 요구)과 충돌해서
`numpy<2.3.0,>=2`로 재고정.

## 소스 코드 직접 분석 — exp51 당시 추정과 대조

`vigs/gs_backend.py`, `vigs/gaussian/scene/gaussian_model.py`, `vigs/gaussian/utils/slam_utils.py`
정독:

| 항목 | exp51 시점 추정 | 실제 코드 확인 |
|---|---|---|
| isotropic scale loss | 몰랐음 | `torch.abs(scaling - scaling.mean(dim=1))` λ=10, **신규 확인 — 우리 exp51엔 없음** |
| scale clamp | 몰랐음 | 매 `map()` 호출 후 `scaling.clamp(max=0.1)`, **신규 확인** |
| 비가시 opacity 선별 리셋 | "reset_opacity_nonvisible로 윈도우 밖 영역을 살린다"고 추정 | 코드는 있으나(비가시만 0.4로, 가시는 보존) **공개 config 5개 전부 `gaussian_reset: 2000000001`로 사실상 비활성**. 진짜 동작은 "선택적 리셋"이 아니라 **"주기적 전체 리셋을 아예 안 한다"** — exp48이 겪은 문제에 대한 우리 해석이 부분적으로 틀렸음 |
| init 렌더-alpha 중복방지 | "공개코드엔 미완성"이라 추정 → exp51 축B로 직접 구현 | `transmittance = 1.0 - alpha`를 매 keyframe마다 계산은 하지만 **호출 이후 어디서도 안 씀(dead code 100% 확인)** — 축B가 실제로 새로운 기여였음이 확증됨 |
| depth supervision | inverse-depth L1 추정 | `l1_depth = |1/depth·mask - 1/gt_depth·mask|`, `alpha·l1_rgb + (1-alpha)·l1_depth·5` (기본 alpha=0.95) — **우리 exp51 축A와 구조적으로 동일**, 설계가 맞았음을 확증 |
| normal supervision | 몰랐음 | Omnidata 예측 normal map과 depth-to-normal 일관성 loss(`get_loss_normal`, λ=0.5) — **신규 발견, 우리 exp51엔 없는 축**. 바늘형 floater는 정상적인 표면 normal을 가질 수 없어 특히 효과적일 후보 |

## 베이스라인 실행 결과 (알고리즘 무수정)

### RPNG AR Table 데모 (저장소 기본 데이터, 단안 RGB+IMU, DROID-SLAM 트래킹)

| 지표 | 값 |
|---|---:|
| held-out mean PSNR | 25.75dB |
| held-out SSIM / LPIPS | 0.871 / 0.115 |
| keyframe mean PSNR | 26.80dB |

### 301_1253 (우리 프로젝트 데이터, `--gsmapping`)

**입력 준비**: VIGS는 단안 RGB+IMU라 우리 스테레오 SLAM 파이프라인과 입력이 다름.
`projectaria_tools`로 원본 VRS에서 **RGB 카메라-IMU 외부파라미터(Tcb)를 직접 추출**
(`get_transform_device_camera("camera-rgb")`, `get_imu_calib("imu-right").get_transform_device_imu()`
→ `Tcb = inv(T_device_rgb) @ T_device_imu`) — 회전 성분이 기존 `01_euroc_openmavis_input/Aria.yaml`의
`IMU.T_b_c1`과 소수점 6자리까지 일치해 추출 파이프라인 자체를 교차검증함. 카메라 모델은
`03_rgb_3dgs_full`과 동일 핀홀(fx=fy=500, cx=cy=512, 1024×1024). IMU 노이즈는 Aria.yaml의
기존 ORB-SLAM3용 계산값(998.4Hz) 재사용. RGB 1303장·IMU 65,425샘플 그대로 입력(다운샘플 없음).

| 지표 | 값 |
|---|---:|
| held-out mean PSNR | **26.85dB** |
| held-out SSIM / LPIPS | 0.887 / 0.174 |
| **keyframe mean PSNR** | **30.90dB** |
| keyframe SSIM / LPIPS | 0.906 / 0.163 |
| 129 keyframe (1303 프레임 중) / 최종 가우시안 | 201,160개 |
| 총 소요시간 | 약 6~8분 (트래킹+매핑+최종 BA+색 정제 전부 포함) |

exp51 축A+B(held-out 25.29dB, Photo-SLAM 기반)보다 held-out이 높고 keyframe은 30dB를
넘었다 — 단, **평가 방식(held-out 정의)이 우리 llffhold-8 관례와 다를 수 있어 직접 비교는
참고 수준**. 렌더 육안 확인(방 구조 인식 가능, 선명도 양호) — 다만 Aria RGB 센서가 세로
마운트라 이미지가 회전된 채로 나오는 건 우리 기존 `03_rgb_3dgs_full` 관례와 동일(버그 아님).

⚠ **중요: 이 수치는 실시간 수치가 아님.** 최종 PSNR은 트래킹이 다 끝난 뒤 붙는
"Global GS Refinement"(26,000 iteration, 약 3분 38초 오프라인 폴리싱)를 포함한다. VIGS
자체에 `--pure_online`(최종 BA·궤적 채움·맵 정제를 스킵) 플래그가 있다는 것 자체가 이
폴리싱이 실시간이 아님을 개발자도 인지하고 있다는 뜻 — **다음 확인 항목은 pure_online
PSNR과 프레임당 실제 처리 속도(FPS)**.

### 301_1253_rot (같은 방, 회전 궤적)

동일 절차(Tcb는 같은 물리 기기라 1253과 동일 — VRS에서 재추출해 소수점까지 일치 확인),
RGB 1498장·IMU 75,917샘플.

| 지표 | 값 |
|---|---:|
| held-out mean PSNR | 25.08dB |
| held-out SSIM / LPIPS | 0.877 / 0.186 |
| keyframe mean PSNR | 30.31dB |
| keyframe SSIM / LPIPS | 0.904 / 0.174 |
| 최종 가우시안 | 266,423개 |
| 총 소요시간 | 약 12.5분 (파일 타임스탬프 기준 정확히 측정: 트래킹 ~6분 + 최종 정제 ~6.5분) |

1253 대비 held-out -1.77dB·keyframe -0.59dB로 소폭 하락하지만 **여전히 keyframe 30dB를
유지** — 회전 궤적에서도 크게 무너지지 않음. 렌더 육안 확인(문·키패드·비상구 인식 가능,
좌표계 정렬 정상). 소요시간은 1253(~8분)보다 다소 늘었지만(~12.5분, 1.5배 정도) 극단적인
차이는 아님 — **정정: 처음에 `ps aux`의 누적 CPU 시간(17:07)을 경과 시간으로 잘못 읽어
"24분/3배"라고 썼던 건 오류였음**, 파일 타임스탬프로 재확인한 수치가 정확함.

## 병목 분석 (2026-07-18) — 결론: 병목은 온라인 루프가 아니라 고정비용 오프라인 폴리싱

`vigs.py`(top-level phase: motion_filter/frontend/gs_mapping/offline_backend/offline_color_refinement)와
`gs_backend.py::map()`(내부: render_forward/backward/densify_prune/optimizer_step) 양쪽에
`torch.cuda.synchronize()`로 감싼 타이머를 삽입(`VIGS_TIMING_LOG` env var로 opt-in, 기본
동작 무변경 — 알고리즘 무수정 원칙 유지). 1253 데이터 250프레임 서브셋(실제 녹화 시간
약 25초 분량)으로 A(트래킹만)/B(트래킹+매핑) 절제 실험 + GPU 활용률 동시 샘플링.

**A(트래킹만, 250프레임): 57.3초. B(트래킹+매핑+오프라인 폴리싱, 250프레임): 280.8초.**

B의 phase별 분해(실측):

| phase | 시간 | 비중 |
|---|---:|---:|
| motion_filter (250프레임) | 8.1초 | 3.3% |
| frontend (로컬 BA, 250프레임) | 10.6초 | 4.3% |
| **gs_mapping (온라인 매핑, 19회 호출)** | **23.3초** | **9.5%** |
| offline_backend (7+12 iter 전역 BA) | 6.7초 | 2.7% |
| offline_final_call_gs (재정렬) | 1.2초 | 0.5% |
| **offline_color_refinement (26,000 iter, 고정)** | **195.9초** | **79.7%** |

**핵심 발견: `offline_color_refinement`(26,000 iteration) 하나가 전체 시간의 80%.** 이건
`self.gaussians.max_steps`(config `position_lr_max_steps`)로 고정된 값이라 **씬 길이·프레임
수와 무관하게 항상 26,000회** 돈다 — 250프레임짜리 20여 초 분량 데이터에서도, 1303프레임
전체에서도 똑같은 절대시간이 붙는다는 뜻. 즉 앞서 본 "키프레임 30dB"의 상당 부분은 이
고정비용 폴리싱이 사주는 것이지, 온라인 루프 자체가 30dB급으로 수렴한 게 아니다.

**온라인 구간(motion_filter+frontend+gs_mapping)만 떼어놓고 보면 41.9초/250프레임**.
**⚠ 정정(2026-07-19, 사용자 확인)**: 처음엔 "Aria 캡처 ~10fps"로 가정해 "실시간의
1.7배"라고 썼는데, 실제 RGB 타임스탬프(첫~끝 프레임)로 직접 계산하니 **1253 전체
1303프레임의 실제 녹화 시간은 65.1초 = 약 20fps**였다(10fps 아님). 250프레임 기준
실녹화는 25초가 아니라 **약 12.5초** → **온라인 루프는 실시간의 약 3.35배 느린 수준**
(1.7배가 아니라 그 두 배 가까이 느림). 온라인 구간 안에서는 **gs_mapping이
23.3초로 트래킹(motion_filter+frontend, 18.7초)보다 큰 단일 비중** — `map()` 내부 분해로는
render_forward(12.8초)+backward(8.1초)가 map() 비용의 97.9%(densify_prune·optimizer_step은
무시할 수준). (뒤쪽 "실시간의 1.6~2.3배" 서술도 같은 오류 — 정정판은 이 문서 맨 아래
"실녹화 시간 정정" 절 참조.)

GPU 활용률 병행 샘플링(1Hz, 180개 샘플): 평균 56%, 21.7%가 50% 미만 — 온라인 트래킹
구간이 순수 GPU-연산이 아니라 Python/CPU 오버헤드에도 상당히 걸쳐 있음을 시사(정밀한
phase-GPU 시계열 매칭은 안 함, 대략적 신호로만 사용).

**결론 및 다음 스텝**:
1. **실시간화의 최우선 과제는 온라인 루프 최적화가 아니라 "오프라인 폴리싱을 압축하거나
   스킵하는 것"** — 26,000 iteration 색 정제를 줄이면(또는 `--pure_online`으로 통째로
   스킵하면) 총 시간이 4~5배 단축될 잠재력. 단, 이 폴리싱이 실제로 PSNR에 얼마나
   기여하는지(20dB대→30dB대 도약분 중 몇 dB가 여기서 나오는지)는 아직 측정 안 함 —
   `3dgs_before_final.ply`를 직접 평가해서 정량화 필요.
2. 온라인 구간 안에서는 gs_mapping(특히 render+backward)이 트래킹보다 비싸다 — 윈도우
   크기(`window_size`)나 매핑 iteration 수를 줄이는 게 다음 최적화 레버.
3. normal supervision(Omnidata 기반)을 우리 exp51 파이프라인에 이식할 가치가 있는지 —
   바늘형 floater 타깃으로 축E(carve loss) 대비/병행 후보.
4. floater(자유공간 먼지) 지표는 아직 측정 안 함 — 우리 free-space 지표로 VIGS 결과물도
   채점해볼 가치 있음.

**계측 인프라 메모**: `vigs/vigs.py`(`_timed` 헬퍼, `track()`/`terminate()`에 삽입)와
`vigs/gs_backend.py`(`_Sect` 컨텍스트매니저, `map()`에 삽입) 수정 — 둘 다 `VIGS_TIMING_LOG`
환경변수 미설정 시 완전 no-op(알고리즘 동작 무변경 확인됨, syntax/동작 검증 완료). 재현:
`VIGS_TIMING_LOG=<path> python demo.py ... --gsmapping`, 분석은
`aggregate_timing.py`(스크래치패드, 필요시 `scripts/`로 옮길 것).

## `--pure_online` 실측 (2026-07-18) — "keyframe 30dB"는 대부분 오프라인 폴리싱이 만든 숫자

병목 분석에서 나온 가설("폴리싱이 PSNR을 몇 dB나 사주는가")을 실제로 `--pure_online` 플래그로
전체 데이터셋(1253 1303프레임, 1253_rot 1498프레임)을 재실행해 검증. `--pure_online`은
`traj_filler`/`eval_rendering` 호출 자체를 스킵하게 돼 있어(README: "skip final BA and
traj_filler"), **평가 목적에 한해서만** `demo.py`에 opt-in 훅(`VIGS_EVAL_PURE_ONLINE=1`)을
추가 — 온라인 루프가 끝난 시점(`ONLINE_LOOP_DONE_EPOCH` 마커, 시간 측정은 이 마커 **이전**
기준이라 eval 자체의 비용은 온라인 시간에 안 섞임) 직후에 최종 BA·색정제 없이
`traj_filler`+`eval_rendering`만 호출해 순수 온라인 상태의 PSNR을 직접 측정.

| | 1253 | 1253_rot |
|---|---:|---:|
| **pure_online held-out PSNR** | **22.73dB** | **23.53dB** |
| pure_online SSIM | 0.758 | 0.776 |
| **pure_online keyframe PSNR** | **22.95dB** | **23.61dB** |
| **pure_online 온라인 루프 시간(실측)** | **207.6초(3.46분)** | **344.7초(5.74분)** |
| (대조) 폴리싱 포함 최종 held-out | 26.85dB | 25.08dB |
| (대조) 폴리싱 포함 최종 keyframe | 30.90dB | 30.31dB |
| **폴리싱이 사주는 dB (held-out / keyframe)** | **+4.12 / +7.95** | **+1.55 / +6.70** |

**확정 결론: "keyframe 30dB" 헤드라인 수치의 대부분(6~8dB)은 26,000-iteration 오프라인
색정제 + 전역 BA가 만든 것이지, 온라인 재구성 자체의 품질이 아니다.** 순수 온라인 품질은
held-out 기준 **22.7~23.5dB** — 이는 우리 자체 incremental 트랙(exp51 축A+B, held-out
25.29dB)**보다 오히려 낮다.** 즉 지금까지 "VIGS가 우리보다 우월하다"고 봤던 인상은 **폴리싱
포함 수치 vs 우리 무폴리싱 수치를 비교한 불공정 비교**였음이 확정됨 — 정정 필요.

온라인 루프 시간도 재확인: 1253(1303프레임) 온라인 루프 207.6초 vs **실제 녹화 시간
65.1초**(RGB 타임스탬프 첫~끝 직접 계산, ~20fps로 확인됨 — 초기엔 ~10fps로 잘못 가정해
"실녹화 약 130초분/실시간의 1.6배"라고 썼던 걸 정정) → **실시간의 약 3.19배**,
1253_rot(1498프레임) 온라인 루프 344.7초 vs 실제 녹화 74.85초(마찬가지로 ~20fps) →
**약 4.60배**(초기엔 "실녹화 150초분/2.3배"로 오기재, 마찬가지로 정정) —
회전 궤적이 온라인 단계에서도 더 느림(더 많은 correlation/local BA 필요 추정). 전체
데이터셋 기준 phase 분해(250프레임 서브셋과 동일 경향 재확인): gs_mapping이 온라인 루프의
40%(83.9s/207.6s, 1253) 안팎으로 최대 비중, frontend가 그다음.

**결론 갱신**: 실시간화 과제는 두 갈래로 명확해짐 — ① 폴리싱을 스킵/압축하면 시간은
크게 줄지만 품질도 22~24dB대로 같이 떨어짐(트레이드오프, 공짜가 아니었음) ② 순수 온라인
품질 자체(22.7~23.5dB)가 우리 exp51보다 낮으므로, **VIGS 아키텍처를 그대로 가져오기보다는
"무엇이 온라인 폴리싱 없이도 우리 축A+B(25.29dB)를 능가하게 만들 것인가"가 더 정확한
질문** — normal supervision(exp51에 없는 축)을 온라인 단계에 넣는 실험이 다음 후보로
격상됨.

## 온라인 루프 세분화 병목 분석 (2026-07-18) — 함수/커널 단위

앞선 병목 분석은 "트래킹 vs 매핑" 정도의 거친 단위였음. `factor_graph.py::update()`(트래킹
BA 내부: correlation lookup / update-operator 신경망 forward / CUDA BA solve / upsample)와
`motion_filter.py::track()`(feature_encoder / Omnidata prior_extractor / context_encoder /
flow_check)에도 같은 opt-in 타이머를 삽입해, 1253 전체(1303프레임) `--pure_online` 온라인
루프(총 208.2초)를 커널/함수 단위로 완전히 분해.

| 대분류 | 세부 항목 | 시간 | 온라인 루프 대비 비중 |
|---|---|---:|---:|
| **gs_mapping (84.9초)** | rasterize (CUDA 래스터라이저 forward) | 29.2초 | 14.0% |
| | **backward (래스터라이저+로스 역전파)** | **33.6초** | **16.1%** |
| | loss_compute (normal consistency + RGBD L1) | 15.8초 | 7.6% |
| | optimizer_step / densify_prune | 1.0초 | 0.5% |
| **frontend (61.0초)** | **bundle_adjust (CUDA BA solve, `vigs_backends`)** | **28.6초** | **13.7%** |
| | update_op_forward (DROID GRU 신경망) | 12.5초 | 6.0% |
| | corr_lookup / build_corr_volume / upsample | 4.6초 | 2.2% |
| | (frontend 내 미계측 오버헤드) | 15.4초 | 7.4% |
| **motion_filter (26.7초)** | **prior_extractor (Omnidata depth+normal, 키프레임 316회만)** | **14.5초** | **7.0%** |
| | feature_encoder (매 프레임 1303회, 건당 2.2ms로 저렴) | 2.9초 | 1.4% |
| | flow_check / context_encoder | 3.1초 | 1.5% |
| | (motion_filter 내 미계측 오버헤드) | 6.2초 | 3.0% |
| **미계측 오버헤드(모델 로딩·IPC·Python 제어흐름 등)** | | ~35.5초 | **~17%** |

**순위(단일 항목 기준)**:
1. **gs_mapping/backward — 33.6초(16.1%)**: 가우시안 래스터라이저+로스의 역전파. rasterize(순전파)와 합치면 **62.8초(30.2%)로 온라인 루프 전체의 가장 큰 단일 원인**.
2. **frontend/bundle_adjust — 28.6초(13.7%)**: 우리가 직접 빌드한 CUDA 커널(`vigs_backends`)의 Gauss-Newton BA 솔브.
3. **gs_mapping/loss_compute — 15.8초(7.6%)**: normal consistency(depth→normal 변환 포함) + RGBD L1.
4. **motion_filter/prior_extractor — 14.5초(7.0%)**: Omnidata depth+normal 추론. 키프레임(316개, 전체 프레임의 24%)에서만 도는데도 건당 평균 46ms(최대 3.8초 스파이크)로 무겁다 — **TensorRT 가속을 안 쓰고 있다는 점이 직접 원인**(우리 환경은 pycuda/TensorRT 빌드를 제외했음, exp52 셋업 섹션 참조).
5. **frontend/update_op_forward — 12.5초(6.0%)**: DROID의 GRU 업데이트 신경망.
6. **미계측 오버헤드 총합 ~62초(약 30%)**: 위 어떤 단일 커널로도 설명 안 되는 부분 — 모델 로딩(1회성), reader 프로세스와의 큐 IPC, Python 제어흐름, GPU 동기화 대기 등으로 추정. 더 파려면 `torch.profiler`나 `py-spy` 수준으로 내려가야 함(다음 단계로 보류).

**결론**: **가우시안 매핑(rasterize+backward, 30%)이 트래킹의 핵심 연산(BA solve, 13.7%)보다
확실히 무겁다** — "실시간화하려면 트래킹보다 매핑 최적화가 레버리지가 크다"는 이전 결론이
함수 단위로도 재확인됨. 다만 **Omnidata(TensorRT 미사용)도 무시 못 할 7%**를 차지하고,
**미계측 오버헤드가 30%나 돼서 이것도 무시할 수 없는 비중** — 순수 커널 최적화만으로는
안 되고 파이프라인 자체의 오버헤드(IPC, 동기화)도 봐야 함.

**계측 인프라 확장**: `factor_graph.py`(`_Sect`, `graph_update` 라인)·`motion_filter.py`
(`_Sect`, `motion_filter_sub` 라인) 추가, `gs_backend.py`의 `render_forward`를
`rasterize`+`loss_compute`로 분리. 전부 `VIGS_TIMING_LOG` 미설정 시 no-op(syntax 검증 완료,
동작 무변경). 재현: `VIGS_TIMING_LOG=<path> python demo.py ... --gsmapping --pure_online`,
분석은 `aggregate_timing.py`(스크래치패드, 세분화 버전).

## 미계측 오버헤드 해소 (2026-07-18) — PGBA 발견 + IMU 프리적분 확인, ~30%→~12%로 축소

앞선 분해에서 온라인 루프의 ~30%가 어떤 단일 커널로도 설명이 안 됐음. `depth_video.py`
(IMU 프리적분 `imu_integrate_python_fallback`/`append_total`)·`track_frontend.py`
(`rm_factors`/`add_proximity_factors`)·`demo.py`(`queue_get_wait`/`model_loading`/
`vigs_track_total` — `vigs.track()` 호출 자체를 감싸는 외곽 경계)·`vigs.py`(**PGBA 블록
`pgba_run`/`pgba_call_gs` — 이전엔 완전히 미계측**)에 타이머 추가 후 1253 전체 재실행.

**핵심 발견 1 — PGBA(pose-graph loop-closure 보정)가 이전엔 완전히 안 보이던 구간이었음**:
`vigs.py::track()`의 `if len(viz_idx) and self.pgba: ... run_pgba(...) ... call_gs(...)`
블록 — loop closure가 감지되면 포즈 그래프 최적화 + 그 보정을 반영한 재매핑을 돈다.
**`pgba_run` 4.42초 + `pgba_call_gs` 5.42초 = 9.84초(온라인 루프의 4.7%)** — 이전 분석엔
전혀 없던 항목.

**핵심 발견 2 — `vigs.track()` 자체를 외곽에서 감싸보니(`vigs_track_total`) 거의 완전히
설명됨**: 온라인 루프 209.4초 중 `vigs_track_total`(motion_filter+frontend+PGBA+gs_mapping을
전부 포함하는 `vigs.track()` 호출 자체) = **183.8초(87.8%)**, 그 내부는
`motion_filter(27.0)+frontend(61.6)+pgba_run(4.4)+pgba_call_gs(5.4)+gs_mapping(85.3)` =
183.7초로 **거의 100% leaf 단위까지 설명됨**(motion_filter 내부 97.5%, gs_mapping 내부
93.6% 설명). **`track()` 바깥의 진짜 미계측은 25.6초(12.2%)뿐** — `queue_get_wait`(4.1초,
reader 프로세스 IPC 대기) + `model_loading`(0.9초, 1회성) + 잔여 ~20.6초(프레임별
`self.images[t]=image` 텐서 복사, `pbar` 갱신 등 자잘한 Python 오버헤드로 추정, 개별
계측은 안 함).

**IMU 프리적분(pure Python fallback) 확인**: `imu_integrate_python_fallback` 총 12.42초
(n=540 — 키프레임 316회의 개별 적분 + IMU 초기화 시점 `reintegrate_all()`의 일괄 재적분
~224회 포함). README가 명시한 **"IMU C++ 모듈을 안 빌드하면 순수 Python으로 폴백"** 이
실제로 우리 환경의 상태(빌드 안 함) — 이 12.42초는 `imu_cpp` 모듈을 빌드하면 상당 부분
줄어들 여지가 있는 항목으로 확인됨(별도 시도는 안 함, 이번 스코프 밖).

**갱신된 결론**: 매핑(rasterize+backward, 30%)이 여전히 최대 단일 원인이라는 점은
불변. 다만 이번 분해로 (a) PGBA가 무시 못 할 4.7%를 차지한다는 것, (b) `track()` 바깥
오버헤드는 실제로는 12%대에 불과해 이전 추정(~30%)보다 훨씬 작다는 것, (c) IMU
프리적분이 순수 Python 폴백이라 최적화 여지가 있다는 것이 새로 확인됨.

## TensorRT 가속 실측 (2026-07-18) — Omnidata 78% 단축, 온라인 루프 전체 5.1% 단축

병목 분석에서 지목된 "TensorRT 미사용"을 실제로 해결. `tensorrt-cu12`/`pycuda`/`onnx`
계열 재설치(이전엔 pycuda가 CUDA 헤더 문제로 빌드 실패해 전부 제외했었음 — 이번엔 같은
`CPATH` 픽스로 해결, 런타임에는 `libcurand.so.10` 경로도 `LD_LIBRARY_PATH`에 추가 필요).
`trtexec` CLI 바이너리는 pip wheel에 없어서(전체 SDK 별도 배포) **Python TensorRT API로
직접 엔진 빌드**(`Builder`/`OnnxParser`/FP16 config, `trtexec --fp16`과 동등). Omnidata
depth/normal 모델만 ONNX 익스포트(`scripts/export_omnidata.py`, `onnxscript` 추가 설치
필요) → `onnxsim` 단순화 → FP16 엔진 빌드(각 85초 소요, 1회성). DroidNet feature
encoder/update module 엔진은 빌드 안 함(shape가 동적이라 복잡도 높고, 애초 비중도 작아
스코프 밖으로 보류).

| | no-TRT | TensorRT(Omnidata만) | 변화 |
|---|---:|---:|---:|
| **prior_extractor(키프레임당)** | 46.45ms | **10.15ms** | **−78%** |
| motion_filter 총합 | 27.03초 | **15.80초** | −41.5% |
| **온라인 루프 총합(1303프레임)** | 209.36초 | **198.66초** | **−5.1%(−10.7초)** |
| held-out PSNR | 22.73dB | 22.54dB | 오차범위 내 동일 |
| keyframe PSNR | 22.95dB | 22.72dB | 오차범위 내 동일 |

**결과 해석**: Omnidata 자체는 78% 단축됐지만(FP16 TensorRT의 전형적 효과), 애초 전체
온라인 루프에서 차지하던 비중이 7%였기 때문에 총 시간 절감은 5.1%에 그침 — **"기대한
것보다 작지만, 정확히 이론대로"**(motion_filter 감소분 −11.23초가 거의 그대로 온라인
루프 감소분 −10.7초로 이어짐, model_loading이 TensorRT 엔진 역직렬화로 +0.56초 늘어난
게 유일한 상쇄 요인). PSNR은 완전히 동일(품질 손실 없음, FP16이 문제 안 됨). **더 큰
잠재적 이득은 DroidNet의 update_module(12.5초, 6.0%)이나 feature_encoder를 TensorRT화
하는 쪽**이지만, 이건 동적 shape(엣지 수·윈도우 크기가 프레임마다 달라짐) 대응이 필요해
훨씬 복잡함 — 이번 스코프에서는 시도 안 함, 향후 후보로 기록.

**결론**: TensorRT가 진짜 효과가 있다는 걸 확인했지만(Omnidata는 4.6배 빨라짐), 실시간화의
승부처는 여전히 **gs_mapping(30%)** 이다 — Omnidata TensorRT화만으로는 온라인 루프를
5%밖에 못 줄인다. 우선순위는 그대로: 매핑 최적화(윈도우 크기·iteration 수 축소) >
DroidNet TensorRT화 > 나머지.

## imu_cpp + DroidNet(fnet·update_module) TensorRT 추가 (2026-07-18)

### 빌드

- **`imu_cpp`**(README step 5, 선택 C++ IMU 프리적분 모듈): 시스템 패키지(`libeigen3-dev`,
  `libomp-dev`, cmake/g++)가 이미 설치돼 있어 `cmake .. -DCMAKE_BUILD_TYPE=Release && make`
  그대로 빌드 성공. `depth_video.py`가 `imu_cpp/build/imu_integrator_cpp*.so` 존재를
  자동 감지해서 쓰므로 별도 설정 불필요.
- **DroidNet fnet(feature encoder)·update_module TensorRT화**: README의 예시 shape
  (344×616, H43×W77 등)는 다른 데이터셋 기준이라 우리 1253 데이터엔 안 맞음 — 실제
  런타임 텐서 shape을 디버그 프린트로 직접 측정(`fnet 입력 = 고정 (1,1,3,464,464)`,
  `update_module의 net/inp/corr/flow = H=W=58 고정 + num(edge 개수) 동적, 실측 3~52`).
  `scripts/export_droidnet_aria1253.py`(신규, 우리 shape 전용) → fnet은 고정 shape로,
  update_module은 `num`만 동적 축으로 ONNX export → Python TensorRT API로 FP16 엔진
  빌드(fnet: 고정, update_module: `IOptimizationProfile`로 min/opt/max=1/24/80 및
  PGBA용 1/40/150 두 버전).

### 결과 — 1253 전체(1303프레임), imu_cpp+Omnidata+fnet+update_module TensorRT 전부 적용

| 항목 | 이전(폴백 전부) | 이번(가속 전부) | 변화 |
|---|---:|---:|---:|
| **imu_integrate** | 12.42초 (Python fallback) | **0.19초** (C++) | **−98.5%** |
| feature_encoder(fnet) | 2.93초 | **0.64초** | **−78%** |
| prior_extractor(Omnidata) | 14.68초 | **3.31초** | **−77%** |
| update_op_forward(update_module) | 12.54초 | 13.62초 | **+8.6% (효과 없음, 오히려 소폭 악화)** |
| bundle_adjust(CUDA BA solve, 미가속) | 28.86초 | 21.06초 | −27%(설명 안 됨, GPU 경합/노이즈 추정) |
| motion_filter 총합 | 27.03초 | **9.36초** | **−65.4%** |
| **온라인 루프 총합** | 209.36초 | **180.10초** | **−14.0%(−29.3초)** |
| held-out / keyframe PSNR | 22.73 / 22.95dB | 22.90 / 23.09dB | 오차범위 내 동일 |

**핵심 발견 — update_module TensorRT는 효과가 없었다**: fnet·Omnidata와 달리
update_op_forward는 TensorRT화해도 안 빨라짐(오히려 8.6% 느려짐). 원인 추정: ① 이
네트워크 자체가 이미 가벼움(콜당 평균 6~8ms)이라 TRT의 커널 퓨전 이득이 작음 ②
`num`(edge 개수)이 호출마다 달라져 `context.set_input_shape()`를 매번 다시 호출해야
하는 동적 shape 오버헤드 ③ `self.agg()`(그래프 집계)는 TRT로 못 내보내 PyTorch로
따로 도는데, 이 TRT↔PyTorch 경계 자체가 동기화 비용을 추가함. **"뭐든 TensorRT로
바꾸면 빨라진다"가 아니라 컴포넌트별로 실측 확인이 필요하다**는 걸 보여주는 사례.

**imu_cpp가 가장 확실한 승리**: 98.5% 감소, 사실상 공짜에 가까운 최적화(빌드 5분,
알고리즘 무수정, PSNR 무변화).

**bundle_adjust의 −27%는 우리가 건드리지 않은 항목**이라 인과관계를 주장할 수 없음 —
런간 GPU 클럭/온도, 동시 실행 커널 수 변화 등에 의한 노이즈로 추정, 별도 검증 안 함.

## 온라인 루프 세분화 병목 분석 — 최종판(전체 가속 적용 후, 2026-07-18)

앞의 "온라인 루프 세분화 병목 분석"(가속 전, no-TRT/Python IMU 폴백 기준) 표를
**imu_cpp + Omnidata TensorRT + fnet TensorRT + update_module TensorRT를 전부 적용한
뒤**로 다시 만든 버전. 원본 분석은 그대로 남겨두고(비교용), 이게 최종 상태.

**온라인 루프 총합: 180.10초** (가속 전 209.36초 대비 −14.0%)

**실시간 대비**: 1253의 실제 녹화 시간은 **65.1초**(RGB 첫~끝 타임스탬프로 직접 계산,
~20fps — 이전에 ~10fps로 잘못 가정했던 걸 사용자 확인으로 정정, 위 "실녹화 시간 정정"
메모 참조). 즉 이번 가속(imu_cpp+TensorRT 3종) 다 넣어도 **180.10초 / 65.1초 = 실시간의
약 2.77배** — 가속 전(209.36초 기준 3.22배)보다는 나아졌지만 여전히 3배 가까이 느림.

| 대분류 | 세부 항목 | 시간 | 온라인 루프 대비 비중 |
|---|---|---:|---:|
| **gs_mapping (90.5초, 50.2%)** | backward (래스터라이저+로스 역전파) | 34.7초 | 19.3% |
| | rasterize (CUDA 래스터라이저 순전파) | 31.4초 | 17.4% |
| | loss_compute (normal consistency + RGBD L1) | 16.8초 | 9.3% |
| | optimizer_step / densify_prune | 1.3초 | 0.7% |
| **frontend (43.2초, 24.0%)** | bundle_adjust (CUDA BA solve, `vigs_backends`, 미가속) | 21.1초 | 11.7% |
| | update_op_forward (DROID GRU, **TensorRT 적용해도 무변화**) | 13.6초 | 7.6% |
| | corr_lookup / build_corr_volume / upsample | 6.9초 | 3.8% |
| | (frontend 내 미계측) | 1.6초 | 0.9% |
| **PGBA (10.0초, 5.5%)** | pgba_call_gs (루프클로저 반영 재매핑) | 5.8초 | 3.2% |
| | pgba_run (포즈그래프 최적화) | 4.2초 | 2.3% |
| **motion_filter (9.4초, 5.2%)** | prior_extractor (Omnidata, **TensorRT −77%**) | 3.3초 | 1.8% |
| | flow_check | 2.9초 | 1.6% |
| | context_encoder | 0.7초 | 0.4% |
| | feature_encoder (fnet, **TensorRT −78%**) | 0.6초 | 0.4% |
| | (motion_filter 내 미계측, append_total 포함 — imu_cpp로 사실상 0) | 1.8초 | 1.0% |
| **`track()` 바깥 오버헤드 (27.0초, 15.0%)** | model_loading(엔진 6개 역직렬화 포함, 1회성) | 1.5초 | 0.8% |
| | queue_get_wait (reader IPC 대기) | 4.4초 | 2.4% |
| | 잔여(이미지 텐서 복사·`pbar` 등, 개별 미계측) | 21.1초 | 11.7% |

**순위 변동**: 가속 전엔 gs_mapping(rasterize+backward)이 30.2%로 압도적 1위였는데,
가속 후엔 **50.2%로 비중이 오히려 더 커짐** — motion_filter·frontend 일부가 줄어들면서
분모(온라인 루프 총합)가 작아진 데다, gs_mapping 자체는 절대시간도 소폭 늘었음
(85.3→90.5초, 노이즈 범위로 추정). **"매핑을 최적화하지 않는 한 다른 걸 아무리
가속해도 절반 이상은 여전히 매핑"** 이라는 게 최종 결론 — 이번 가속 라운드(imu_cpp
+ TensorRT 3종)로 확실히 검증됨.

## 구조적 접근 — `_gs_parallel: true` (async tracking/mapping overlap, 2026-07-19)

**질문의 전환**: 위 결론(gs_mapping이 최대 50.2%)을 본 뒤 "그럼 gs_mapping을 0으로
수렴시키면 실시간이 되는가?"를 직접 계산해보면 — 180.10초에서 gs_mapping(90.5초)을
전부 빼도 89.6초가 남는데, 이는 이미 1253의 실제 녹화 시간 65.1초를 넘는다. **즉
매핑을 공짜로 만들어도 현재 구조(순차 실행: tracking 끝나야 mapping 시작)로는
원리적으로 실시간이 불가능** — 컴포넌트 최적화가 아니라 **구조(아키텍처) 자체를
바꿔야 한다**는 결론. "tracking을 CPU로, mapping만 GPU로" 분리안은 기각(TensorRT는
GPU 전용이고 tracking의 무거운 부분은 dense correlation/GRU/BA — CPU가 GPU보다
느림; `nvidia-smi`로 GPU 1장뿐임도 확인). 대신 코드베이스에 이미 내장된 대안,
**`_gs_parallel: true`(비동기 tracking/mapping 오버랩, 같은 GPU 한 장 공유)**를
검증.

**업스트림 레이스 컨디션 발견·수정**: `_gs_parallel: true`로 처음 돌리자
`IndexError: Dimension out of range`가 `gs_backend.py`의 `map()`(`scaling.mean(dim=1)`)
에서 발생. 원인 추적: IMU 재초기화 시점(`track_frontend.py:257`,
`self.t1 == self.imu_late_init_from`)에 메인(tracking) 스레드가
`self.video.gs.remove_all_gaussians()`를 **락 없이** 호출해 `self.gaussians`를
빈 `GaussianModel(0, ...)`로 통째로 교체하는데, 이게 백그라운드 `_gs_worker` 스레드의
락 보호 `process_track_data()`/`map()`과 경합함(`process_track_data()`는
`self._gaussian_lock`을 잡지만 `remove_all_gaussians()`는 안 잡음) — 업스트림
VIGS-SLAM의 진짜 버그(`config/iphone.yaml`도 `parallel: true`라 죽은 코드는 아님,
경합 창이 좁아서 안 걸렸을 뿐). `gs_backend.py`의 `remove_all_gaussians()` 본문을
`process_track_data()`/`rescale()`과 동일하게 `with self._gaussian_lock:`로 감싸서
수정.

**2차 장애 — 좀비 프로세스가 GPU 메모리를 물고 있던 문제**: 레이스 수정 전 크래시된
런에서, `_gs_worker`는 **daemon 스레드**라 그 스레드가 죽어도(uncaught exception)
메인 프로세스는 안 죽고 계속 돌아감 — 결과적으로 매핑이 조용히 멈춘 채 트래킹만
끝까지 진행되는 "좀비" 프로세스가 되어 GPU 메모리 10.83GiB를 프로세스 종료 시점까지
계속 점유. 레이스 수정 후 재실행한 두 번째 시도가 이 좀비와 GPU 메모리를 다투다
`torch.OutOfMemoryError`(TensorRT 엔진 할당 실패 826MB/1550MB) 로 크래시했고, 이
두 번째 프로세스마저 CUDA 컨텍스트 손상으로 인해 **정상 종료하지 못하고 행(hang)**
되어(`State: S (sleeping)`, GPU 메모리 4.2GiB 계속 점유) 남아있었음. `ps aux`/
`nvidia-smi --query-compute-apps`로 두 정체 프로세스 모두 확인 후 `kill -9`로 정리,
GPU 메모리가 실제로 반환됨을 확인한 뒤 동일 커맨드를 깨끗한 GPU 상태에서 재실행 —
이번엔 에러 없이 완주(`shell_exit: 0`).

**결과 — 온라인 루프 180.10초 → 133.04초 (−26.1%), 품질 무손실**:

| | 순차 실행(imu_cpp+TensorRT, gs_parallel 없음) | `_gs_parallel: true`(레이스 수정 포함) | 변화 |
|---|---:|---:|---:|
| 온라인 루프 총합 | 180.10초 | **133.04초** | **−26.1% (−47.06초)** |
| held-out / keyframe PSNR | 22.90 / 23.09dB | 22.63 / 22.89dB | 오차범위 내 동일 |
| 실시간 대비(÷65.1초) | 2.77배 | **2.04배** | 여전히 느리지만 유의미하게 개선 |
| `TRACK_LOOP_DONE`→`ONLINE_LOOP_DONE` 갭 | — | 0.05ms | 종료 시점 매핑 잔여 백로그 없음(끝까지 tracking 속도를 따라잡음) |

**왜 줄었는지 — 실측 오버랩**: 메인(tracking) 스레드에서 측정한 `gs_mapping`
태그는 이제 0.70초(큐에 작업 넣고 즉시 리턴)뿐이고, 실제 매핑 연산
(`map()` 내부: rasterize 38.86초+loss_compute 22.74초+backward 22.91초+
optimizer_step/densify_prune 1.72초 = **86.24초**, 47회 호출)은 `_gs_worker`
백그라운드 스레드에서 트래킹과 **동시에** 돈다. 트래킹만의 비용(frontend 74.28초+
motion_filter 15.56초+pgba_run 5.07초+gs_mapping 큐잉 0.70초 ≈ **vigs_track_total
103.72초**)과 매핑 86.24초를 단순히 더하면 순차 실행 시 189.96초가 되어야 하는데
실측 총합은 133.04초 — 즉 **매핑 비용의 약 66%(56.92초)가 GPU 유휴 시간에 흡수되어
공짜에 가까웠고, 나머지 34%(29.20초)만 GPU 경합(같은 GPU 한 장을 두 스레드가 공유)
으로 critical path에 새어나옴.**

**남은 직렬 비용 — PGBA**: `pgba_call_gs`(루프클로저 반영 재매핑, 4회 호출 합
6.16초)는 `_gs_parallel` 하에서도 큐를 우회해 **동기적으로** 실행됨(루프클로저는
포즈가 크게 바뀌므로 매핑을 즉시 갱신해야 함 — 설계상 타당). 다음 최적화 여지가
있다면 이 부분이지만 절대 비중은 작음(온라인 루프의 4.6%).

**결론**: 사용자의 구조적 직관("gs_mapping을 0으로 줄여도 순차 구조로는 실시간
불가")이 실측으로 확인됐고, 코드베이스에 이미 있던 `_gs_parallel` 오버랩 아키텍처가
실제로 유효한 해법 방향임을 검증(−26.1%, 품질 무손실). 다만 133.04초/65.1초=2.04배로
**아직 실시간에는 못 미침** — 남은 격차(주로 GPU 경합으로 새어나오는 34% 매핑 비용
+ frontend의 bundle_adjust/update_op_forward)를 줄이려면 매핑 자체의 연산량 감소
(예: iteration 수·해상도·densify 빈도 조정)나 멀티 GPU 분리가 다음 방향.

## 트래킹 전용 fps 스윕 — ORB(exp50) vs VIGS 비교 (2026-07-19)

**질문**: `_gs_parallel`로 매핑을 분리해도 여전히 2.04배(미달)였던 것을 보고 —
"그럼 tracking 자체가 무거워서 tracking만으로도 실시간이 안 되는 거 아니냐"는
합리적 의심 제기. VIGS 자체의 tracking(dense 단안, DROID-style)은 이 프로젝트가
최종적으로 채택할 아키텍처가 아니므로(최종 시스템은 exp50의 ORB-SLAM3 기반 흑백
stereo-inertial 트래킹을 씀), 두 트래킹 아키텍처를 **동일 조건에서 직접 비교**해
"VIGS가 느린 게 아키텍처 문제인지, 그냥 이 정도가 트래킹의 일반적 비용인지"를 확인.

**방법**: 1253 흑백 SLAM 카메라(cam0/cam1) 첫 60초(1201프레임, 원본 ~20fps)를 기준
윈도우로 고정, stride 1/2/4로 20fps/10fps/5fps 3조건 생성(동일 60초 구간 내에서만
subsample — 데이터 다른 구간을 섞지 않음).
- **ORB(exp50, DiskChunGS `euroc_stereo_inertial`)**: stride별 `times.txt`(1201/601/
  301줄)를 미리 만들어 그대로 로더에 공급(코드 무수정). `TrackStereo()` 콜별
  wall-clock을 매 프레임 즉시 flush하도록 계측 추가(크래시 시에도 데이터 보존 목적).
- **VIGS**: 기존 `--length 1201 --stride {1,2,4}` 옵션으로 동일 60초 창 subsample,
  `_gs_parallel: true` 하에서 `vigs_track_total`(트래킹만, 매핑은 백그라운드 큐잉만)
  태그 합산 — 위 절에서 이미 검증된 트래킹/매핑 분리 계측을 그대로 재사용.
- 두 스윕을 **동시에 실행했다가 VIGS가 GPU 경합으로 OOM 크래시**(정확히 앞 절의
  `_gs_parallel` OOM과 동일 패턴)로 오염된 걸 확인 → 순차 실행(한쪽 완전히 끝난 뒤
  다음 시작)으로 재실행해 격리.

**부수 발견 — DiskChunGS 매퍼 스레드의 새 CUDA 버그 + 방어적 수정**: 벤치마크 중
`processScaleRefinement()`(exp50 문서에 이미 기록된 미구현 스텁, 여전히 `throw`)와는
별개로 71% 지점(931/1311프레임)에서 **새로운 CUDA 버그**(`invalid configuration
argument`, rasterizer backward 안)로 매퍼 스레드가 죽으며 프로세스 전체가 종료됨
(uncaught exception → `std::terminate()`, 위 VIGS 레이스 컨디션과 동일한 실패 모드).
매핑 품질이 아니라 **트래킹 wall-clock 측정만**이 목적이므로, `GaussianMapper::run()`
의 초기/증분 매핑 루프 본문 전체를 `try/catch(std::exception&)`로 감싸 매퍼 예외가
트래킹 스레드를 더 이상 죽이지 못하게 방어적으로 수정(`mapper_core.cpp`) — 매핑은
해당 iteration만 스킵하고 트래킹은 끊김 없이 계속됨. exp50 자체의 Phase C 매핑
정확도 검증에는 아직 미반영(이 버그의 근본 원인 진단은 exp50 범위로 남겨둠).

**결과**:

| fps | 프레임수 | ORB(exp50) 트래킹 총합 | ORB 실시간 대비 | VIGS 트래킹 총합 | VIGS 실시간 대비 |
|---|---:|---:|---:|---:|---:|
| 20fps | 1201 | 40.55초(1회성 IMU 초기화 스파이크 ~10.2초 포함) | **0.68배** | 87.68초 | **1.46배** |
| 10fps | 601 | 25.52초 | **0.43배** | 77.60초 | **1.29배** |
| 5fps | 301 | 17.06초 | **0.28배** | 66.80초 | **1.11배** |

(60초 실측 창 기준, 1.00배=실시간; VIGS PSNR은 22.12~23.13dB로 fps에 따른 뚜렷한
추세 없음 — stride만 다르고 알고리즘/전체 프레임 예산은 동일하므로 예상대로.)

**핵심 발견 — fps 하향의 효과가 두 아키텍처에서 정반대**:
- **ORB**: 프레임당 순수 트래킹 비용이 fps와 거의 무관하게 고정(20fps 25.3ms,
  10fps 25.9ms, 5fps 24.2ms, 1회성 스파이크 제외). 즉 총 시간이 **프레임 수에 거의
  선형 비례** — fps를 낮추면 실시간 여유가 그만큼 그대로 커짐. 20fps 네이티브에서도
  이미 여유(0.68배).
- **VIGS**: 프레임당 비용이 fps를 낮출수록 오히려 커짐(73→129→222ms) — dense
  correlation 탐색 범위와 BA 반복량이 프레임 간 이동량(=fps 역수)에 비례해서 커지는
  구조적 특성. 그 결과 **fps를 4배 낮춰도 총 시간은 24%만 줄어듦**(87.68→66.80초) —
  **5fps까지 낮춰도 여전히 실시간보다 느림(1.11배)**. fps 조절이라는 손쉬운 레버가
  이 아키텍처엔 거의 안 통함.

**결론**: 앞 절의 "gs_mapping이 문제"라는 진단에 이어, **트래킹 아키텍처 자체도
VIGS(dense 단안)보다 우리가 실제로 채택할 exp50의 ORB-SLAM3 기반 stereo-inertial
쪽이 실시간에 훨씬 유리함**을 동일 조건 비교로 확정. exp52의 "VIGS 아키텍처를 통째로
가져오기보다 유효 레버만 이식" 결론에 트래킹 관점의 근거가 하나 추가됨 — 매핑뿐
아니라 트래킹도 exp50 경로가 실시간화에 더 유리한 출발점.

## 트래킹 궤적 정확도 — MPS 기준 evo 평가 (2026-07-19)

**방법**: 위 fps 스윕에서 나온 6개 궤적(ORB `KeyFrameTrajectory.txt`, VIGS
`traj_kf_beforeBA.txt`)을 모두 MPS의 `closed_loop_trajectory.csv`(디바이스 자체
클로즈드루프 SLAM, 이 프로젝트의 사실상 GT)를 기준으로 `evo_ape`로 평가. 두 방식
모두 정렬: **SE3**(회전+평행이동만, 스케일 보정 없음 — "그대로 나온" 궤적의 실사용
품질)와 **Sim3**(스케일까지 보정 — "형태"만 분리해서 보는 진단용).

| fps | ORB APE RMSE(SE3) | ORB 스케일 보정계수 | ORB APE RMSE(Sim3) | VIGS APE RMSE(SE3) | VIGS 스케일 보정계수 | VIGS APE RMSE(Sim3) |
|---|---:|---:|---:|---:|---:|---:|
| 20fps | 0.188m | 0.969 | 0.131m | 0.209m | 1.048 | **0.013m** |
| 10fps | 0.160m | 0.980 | 0.133m | 0.132m | 1.030 | **0.013m** |
| 5fps | 0.248m | 0.953 | 0.128m | 0.111m | 1.025 | **0.013m** |

**핵심 발견 — 실시간성은 ORB가 유리하지만 궤적 "형태" 정확도는 VIGS가 10배 좋음**:
스케일 보정계수 자체는 둘 다 작음(3~5% 수준, ORB가 약간 더 안정적 — 아래 원인 참조).
그런데 이 작은 스케일 오차를 제거(Sim3)하면 **ORB는 여전히 13cm대 잔차가 남는 반면
VIGS는 1.3cm로 사실상 GT와 일치** — fps를 바꿔도 두 값 다 흔들리지 않아 매우 안정적인
차이. 즉 VIGS의 dense correlation 기반 트래킹은 궤적의 상대적 기하 형태를 ORB의
sparse feature 매칭보다 훨씬 정밀하게 복원하고, 다만 절대 스케일에 IMU 초기화발
체계적 편향이 실려 있어서 raw(SE3) 비교에서는 그 차이가 가려짐.

**결론**: 실시간성만 보면 exp50(ORB) 경로가 압도적으로 유리하다는 앞 절의 결론은
안 바뀜(최종 시스템도 stereo라 VIGS식 IMU 단독 스케일 문제 자체가 없음). 다만
**"ORB가 빠르지만 궤적 정확도는 VIGS보다 떨어진다"는 트레이드오프가 실측으로 확정**
됐고, 이 정확도 차이의 근본 원인(sparse vs dense correspondence)은 매핑 기하
품질에도 직접 영향을 준다 — 아래 절에서 메커니즘을 상세히 분석.

## 왜 dense correspondence가 tracking과 mapping 둘 다에 유리한가 (아키텍처 분석, 2026-07-19)

사용자 질문: "VIGS의 dense correspondence 때문에 성능도 좋고 mapping 기하도 더
좋은 거 아니냐 — tracking 모듈이 정확히 어떻게 영향을 끼치는지" → 소스 코드
(`vigs/motion_filter.py`, `vigs/factor_graph.py`, `vigs/depth_video.py`,
`vigs/vigs.py`, `vigs/gs_backend.py`)를 직접 추적해 확인.

### 1) Tracking 정확도: sparse 대응점 개수·구속력의 근본적 차이

- **ORB(exp50)**: 프레임당 ORB 특징점 ~3,000개를 뽑지만(`[diag2] N=3010`), 우리의
  넓은 시야각 Fisheye624 스테레오에서 실제 좌우 매칭에 성공하는 건 **150~166개뿐**
  (~95% 손실 — `[diag2] nStereoMatched=166`). 포즈 추정·BA는 이 적은 수의 이산적
  코너 특징점에만 의존 — 개별 매칭 노이즈(왜곡·저텍스처·반복 패턴에서의 오매칭)가
  평균화되지 못하고 그대로 포즈 불확실성으로 남음.
- **VIGS(DROID 계열)**: `factor_graph.py`의 `add_factors()`가 프레임 쌍 전체에 대해
  **4D dense correlation volume**(모든 픽셀 대 모든 픽셀, `CorrBlock`)을 만들고,
  학습된 GRU(`self.update_op`, DroidNet update module)가 이걸 반복적으로 읽어
  **픽셀 단위 dense flow/disparity 수정값 + 신뢰도(confidence weight)**를 산출.
  이 dense 수정값+신뢰도가 `cuda_ba`(bundle adjustment)의 residual/information으로
  직접 들어감 — 즉 코너 특징점 100~200개가 아니라 **사실상 이미지 전체 픽셀이
  포즈 추정에 기여**. 구속조건이 훨씬 많고 조밀하며, end-to-end 학습으로 저텍스처·
  블러 등 코너 검출기가 취약한 조건에도 강건.
- 이 차이가 정확히 위 evo 결과(Sim3 기준 ORB 13cm vs VIGS 1.3cm)로 나타남 —
  dense correspondence는 "이론상 더 정확해야 한다"가 아니라 **실측으로 10배 차이가
  확인된 사실**.

### 2) 그런데 왜 VIGS는 스케일이 틀리나 — 정확도(형태)와 스케일은 별개 축

- ORB는 스케일을 **캘리브레이션된 스테레오 기준선**(Aria.yaml `Stereo baseline:
  0.142716`, 하드웨어로 고정된 물리 상수)에서 얻음 — 매 스테레오 프레임마다
  삼각측량으로 계속 재확인되는 값이라 매우 안정적(보정계수 0.953~0.980, fps 무관).
- VIGS는 단안+IMU라 스케일을 **IMU 융합 최적화로 추정**해야 함(config의
  `imu_late_init_from: 20` — 20번째 keyframe 근방에서 짧은 1회성 초기화 최적화로
  스케일을 확정). 이 짧은 초기화 구간에 충분한 가속도 여기(excitation)가 없으면
  스케일 하나가 전역적으로 살짝 틀어진 채(1.025~1.048, ~3~5%) 이후 전체 궤적에
  균일하게 곱해짐 — Sim3 정렬이 이 하나의 전역 스칼라만 제거하면 형태는 거의
  완벽하게 남는 이유.
- 즉 **"dense correspondence → 형태 정확도"와 "IMU 초기화 → 절대 스케일"은
  독립적인 두 축**. 우리 최종 시스템은 흑백 stereo라 스케일은 처음부터 ORB처럼
  캘리브레이션에서 나오므로(VIGS식 단안 스케일 문제 자체가 없음), dense
  correspondence의 형태-정확도 이점만 순수하게 가져올 여지가 있음.

### 3) 매핑 기하로의 직접 연결 — depth가 "따로 도는 추정"이 아니라 "포즈와 공동 최적화된 상태"

가장 중요한 아키텍처 차이. 소스 추적 결과:

- `motion_filter.py`의 `prior_extractor()`가 Omnidata로 초기 monocular
  depth+normal을 뽑고, `depth_video.py`의 **JDSA**(Joint Dense Scale-aware
  Bundle Adjustment, `disps, dscales, _ = JDSA(target, weight, eta, poses,
  disps, intrinsics, self.disps_prior, dscales, ii, jj, self.mono_depth_alpha)`)
  가 이걸 **약한 prior**(`mono_depth_alpha: 0.01` — 매우 작은 가중치)로만 쓰고,
  실제 `disps`(dense depth 상태)는 **correlation 기반 dense flow 증거로 매
  스텝 계속 갱신됨** — 즉 최종 depth는 Omnidata를 그대로 쓰는 게 아니라 여러
  keyframe 간 multi-view 기하 증거로 정제된 값.
- 결정적으로, `vigs.py`의 `call_gs()`가 Gaussian mapper로 넘기는 depth는
  **`1./self.video.disps_up[viz_idx]`** — 방금 그 **포즈와 같은 BA에서 공동
  최적화된 dense depth 그 자체**임(별도 코드 확인, `vigs/vigs.py:169`). 반면
  normals는 `self.video.normals[viz_idx]`로, 이건 BA로 안 다듬어진 **Omnidata
  raw 출력을 그대로** 씀(보조적 normal-consistency loss `lambda_dnormal`용).
- **즉 VIGS에서 tracking과 mapping은 "같은 correlation·BA 파이프라인이 만든 하나의
  일관된 기하"를 공유한다.** 포즈가 정확해지면 depth도 같이 정확해지고(동일 최적화
  변수), 그 depth가 그대로 Gaussian 초기화·RGBD supervision(`get_loss_mapping_rgbd`)
  에 들어감 — 여러 keyframe에서 같은 3D 지점을 봤을 때 서로 다른 위치에 놓일 여지가
  구조적으로 적음.
- **우리(exp50/51) 파이프라인과의 대비**: exp50은 ORB-SLAM3의 **희소** 스테레오
  매칭점(keyframe당 ~150개)만으로 트래킹하고, 매핑용 dense depth는 **완전히 별도
  프로세스**(depth-pro IPC)가 트래킹과 무관하게, keyframe 이미지만 보고 독립적으로
  추정. exp51의 depth supervision 축(A)이 +2.42dB을 냈지만 VIGS 급(순수 온라인
  22.7~23.5dB로 여전히 우리(25.29dB)보다 낮았던 것과는 별개로, "형태 정확도"
  관점에서) 온전한 상한까지 못 간 이유가 여기 있음 — **우리 depth prior는 트래킹의
  포즈·기하와 공동 최적화되지 않은, 매 keyframe 독립적인 정적 추정치**라서 view
  간 기하 일관성이 VIGS의 `disps_up`만큼 보장되지 않음. 이게 바로 이 프로젝트가
  처음부터 쫓아온 **floater(자유공간 먼지)의 근본 원인 중 하나**와 정확히 같은
  메커니즘 — 같은 3D 지점이 서로 다른 view에서 서로 다른 위치로 삼각측량/supervise
  되면 그 불일치가 부유하는 Gaussian으로 남음.

**결론**: dense correspondence는 "성능이 좋다"는 막연한 인상이 아니라, ①
포즈 추정의 구속조건 밀도(수백 배)로 인한 실측 10배 형태 정확도, ② 그 정확한
depth 상태가 mapping supervision과 **같은 최적화 루프를 공유**한다는 두 가지
구체적 메커니즘으로 mapping 기하에 기여함. 우리 파이프라인이 이걸 온전히
가져오려면 단순히 "더 좋은 monocular depth 모델을 쓰는" 수준이 아니라, **depth
추정을 트래킹의 포즈 최적화와 공동으로(jointly) 정제하는 구조**가 필요 —
현재 exp51처럼 depth를 keyframe별 독립 정적 prior로 붙이는 방식의 구조적 한계.
다음 실험 후보로 남겨둠(exp51 범위 밖, 우리 트래킹이 ORB 기반이라 dense-correlation
자체 도입은 별도 아키텍처 결정 필요).

## 원 논문 대조 — DROID-SLAM/VIGS-SLAM 실시간 claim 검증 (2026-07-20)

`context/reference/papers/droid_slam_2108.10869.pdf`, `vigs_slam_2512.02293.pdf`
(arXiv 2108.10869, 2512.02293)를 직접 다운받아 읽고 우리 실측과 대조.

**DROID-SLAM(Teed & Deng, NeurIPS 2021) 원문의 "Timing and Memory" 절**:
> "Our system can run in real-time **with 2 3090 GPUs**. Tracking and local BA is
> run on the first GPU, while global BA and loop closure is run on the second.
> On EuRoC, we average 20fps by **downsampling to 320×512 and skipping every
> other frame**. On TUM-RGBD, 30fps by downsampling to 240×320 + skip every
> other frame. **On TartanAir, due to much faster camera motion, we are unable
> to run in real-time, averaging 8fps.**"

즉 DROID-SLAM 원 논문 자체도 "실시간"을 ① **GPU 2장**(frontend/backend 분리) ②
해상도 다운샘플+프레임 스킵이라는 조건부로만 주장했고, 카메라 모션이 빠른
데이터셋(TartanAir)에서는 **원 저자도 실시간을 못 냈다고 명시**함. 우리가 관찰한
"DROID 계열 트래킹이 실시간이 빡빡하다"는 현상이 우리 구현·데이터 특이 문제가
아니라 **이 아키텍처 계열의 원래부터 있던 특성**임을 원문으로 확인.

**VIGS-SLAM 부록 Table 9 (Runtime Evaluation, RPNG 데이터셋, RTX 5090+i7-14700K)**:

| | Tracking만 [FPS] | Tracking+Mapping [FPS] |
|---|---:|---:|
| ORB-SLAM3 | 22.02(평균) | — |
| **VIGS-SLAM(저자 자체)** | **39.83(평균)** | **12.02(평균)** |

(RPNG 데이터셋 자체 RGB FPS=30, Table 8 기준)

**핵심**: 저자 최고급 GPU(RTX 5090, 우리 RTX 5070 Ti보다 raw FP32 연산량 약
2배+)에서도 **Tracking만은 39.83fps로 30fps 목표를 여유 있게 넘지만, Mapping을
합치면 12.02fps로 급락**(목표의 40% 수준) — **"매핑이 실시간의 최대 병목"이라는
우리 결론이 저자 자신의 공식 벤치마크로도 독립 재확인됨.** 우리 RTX 5070 Ti에서
vigs_track_total이 저자 수치(39.83fps)보다 훨씬 느렸던 건(4.5~13.7fps 상당) GPU
세대차 + 우리 데이터가 20fps 네이티브(저자는 30fps, 더 조밀해서 프레임 간
모션이 작음)인 것의 복합 효과로 추정.

또한 부록 6절 "Real-time Demo Implementation Details": 저자들의 실시간 데모
자체가 **iPhone 17 Pro(캡처) → RTX 5090 데스크탑(i7-14700K)** 조합 — 즉 저자들이
"실시간"이라 부르는 기준 하드웨어가 우리 현재 장비보다 확실히 상위임을 명문화된
근거로 확인.

## Frontend Tracking 내부 구조 상세 — ConvGRU 입출력·반복·슬라이딩 윈도우 (2026-07-20)

Fig.2(논문 System Overview)의 초록 `Frontend Tracking` 박스를 `factor_graph.py`
`get_network_update()`/`track_frontend.py` 소스와 대조해 정확한 메커니즘 확정.

**ConvGRU 입출력** (`factor_graph.py::get_network_update()`):
```python
coords1, _ = self.video.reproject(ii, jj)                  # 현재 pose+depth로 재투영한 대응점
motn = cat([coords1 - coords0, target - coords1])          # motion feature(유도 flow + 이전 잔차)
corr = corr(coords1)                                        # coords1 위치의 correlation lookup
self.net[:,mask], delta, weight, damping, upmask = \
    self.update_op(self.net[:,mask], self.inp[:,mask], corr, motn, ii, jj)
self.target[:,mask] = coords1 + delta                       # p*_ij = r_ij + p_ij (revision 반영)
```
- 입력: hidden state(`self.net`, iteration 간 이어짐) + context feature(`self.inp` =
  `depth_video.py`의 `self.inps`, 프레임당 **1회만** 뽑아 캐싱, 128채널) + correlation
  feature(현재 추정 위치 룩업) + motion feature.
- 출력: 새 hidden state + revision(`delta`, dense 2D 보정) + confidence(`weight`) +
  damping(λ, BA용) + upmask(8×8 학습된 업샘플 마스크, `disps`→`disps_up` 변환에 사용).
- **GRU는 depth/pose를 직접 안 냄** — dense flow 보정값과 신뢰도만 내고, 실제
  pose/depth 갱신은 별도 `bundle_adjust`(DBA layer, Gauss-Newton solve)가 함 —
  그래서 `update_op_forward`와 `bundle_adjust`가 별개 타이밍 태그로 분리돼 있었음.

**왜 반복하나**: `track_frontend.py`에 `iters1=4`(메인), `iters2=2`(보조 refine)
하드코딩. 1회차의 correlation 룩업은 아직 부정확한 pose/depth 기준이라, BA로 한 번
갱신한 뒤 **새 추정치로 재투영해서 다시 룩업(재선형화)**해야 더 정확해짐 — 고전
Gauss-Newton BA의 반복 원리와 동일. hidden state가 iteration 간 이어지므로 GRU는
누적 맥락을 갖고 보정.

**슬라이딩 윈도우 구조**(오해 정정): "윈도우 채우고 다음 윈도우로 넘어간다"가
아니라, **매 keyframe마다 그 시점 최근 `frontend_window=25`개 안의 가까운
keyframe들과 연결**(`frontend_radius=2`, `frontend_nms=1`)하고 6iter 최적화 →
윈도우 밖으로 밀린 오래된 edge는 버려짐(`remove=True`) → 컨베이어벨트처럼 한 칸씩
계속 밀려가며 도는 구조.

**"dense correspondence"의 정확한 의미**: 그래프(edge) 개수 자체는 오히려
sparse(관측된 edge 수 3~52개, `frontend_radius`/`nms`로 제한) — ORB의
covisibility graph와 비슷한 수준. "dense"는 **edge 하나 안에서** frame i의 전체
픽셀 × frame j의 전체 픽셀이 대응된다는 뜻(ORB는 이 자리에 keypoint 150개짜리
sparse 매칭). 즉 "몇 개랑 연결되는가"는 sparse, "각 연결이 얼마나 촘촘한가"는
dense — 두 축이 독립적임.

## ⚠ 정정 — "VIGS는 fps 낮출수록 프레임당 비용이 커진다"는 오해의 소지가 있는 서술이었음 (2026-07-20)

위쪽 "트래킹 전용 fps 스윕" 절에서 "VIGS는 프레임당 비용이 fps를 낮출수록
커짐(73→129→222ms)"이라고 썼는데, **fps별 timing.csv를 call-count/per-call
기준으로 재분해하니 이 해석이 부정확했음**을 확인:

| | 20fps | 10fps | 5fps |
|---|---:|---:|---:|
| bundle_adjust 평균(1콜) | 12.7ms | 14.1ms | 15.1ms |
| update_op_forward 평균(1콜) | 8.0ms | 7.5ms | 7.6ms |
| corr_lookup 평균(1콜) | 1.08ms | 0.99ms | 1.00ms |
| **frontend 총합** | 48.3초 | 40.7초 | 32.9초(fps 낮을수록 오히려 감소) |

**per-call 비용은 거의 안 변함**(bundle_adjust만 12.7→15.1ms로 소폭 증가 — 이건
"baseline 커지면 BA가 더 어려워진다"는 애초 가설이 맞긴 하나 효과가 작음).
"프레임당 73→222ms 증가"는 **frontend 총 시간(거의 안 줄어듦)을 입력 프레임
수(4배 줄어듦)로 나눈 평균이 인위적으로 뻥튀기된 것**이었음 — 계산 자체는
틀리지 않았으나 "계산 하나하나가 더 힘들어진다"는 인과관계 해석이 오해.

**진짜 원인**: keyframe 선정이 optical flow 임계값(`motion_filter.thresh=2.4`)
기준이라 **실제 카메라 이동량**으로 정해지지, 입력 fps와 거의 무관함 — 같은
60초 구간이면 카메라가 움직인 절대량이 같으니 keyframe 개수도 거의 그대로.
아래 keyframe-fps 분석 참조.

## Keyframe 발생률(keyframe-fps) 분석 — VIGS vs ORB (2026-07-20)

같은 60초 구간, 3개 입력 fps(20/10/5)에서 실제 keyframe 개수와 초당 발생률:

| | 20fps 입력 | 10fps 입력 | 5fps 입력 | 개수 변화(20→5fps) |
|---|---:|---:|---:|---:|
| **VIGS keyframe 개수** | 122 | 116 | 114 | **−6.6%** |
| VIGS keyframe-fps(Hz) | 2.033 | 1.933 | 1.900 | |
| **ORB keyframe 개수** | 106 | 104 | 84 | **−20.8%** |
| ORB keyframe-fps(Hz) | 1.767 | 1.733 | 1.400 | |
| (참고) 입력 프레임 개수 | 1201 | 601 | 301 | −75.0% |

**두 시스템 다 keyframe 발생률이 입력 fps(4배 차이)에 거의 비례하지 않음** —
입력 프레임을 4배 줄여도 keyframe은 20% 안팎만 줄어듦. 이건 두 시스템 다
keyframe 선정 기준이 "몇 프레임마다"가 아니라 **실제 모션/시차 누적량** 기반이기
때문(VIGS: optical flow 임계값, ORB-SLAM3: covisibility·신규 맵포인트 비율 등
유사 원리). 다만 **VIGS(−6.6%)가 ORB(−20.8%)보다 훨씬 더 fps에 둔감** — VIGS의
motion_filter가 매 원본 프레임마다 lightweight correlation으로 flow를 재는 반면
(즉 입력 fps가 낮아져도 "이번 후보가 이전 keyframe 대비 얼마나 움직였는지"를
정확히 재는 방식이라 결정 품질이 덜 흔들림), ORB는 프레임 간 매칭 성공률이
입력 밀도에 좀 더 민감하게 반응하는 것으로 추정(직접 검증은 안 함).

**결론**: "fps를 낮추면 일한 횟수가 줄어서 빨라진다"는 ORB에는 어느 정도
성립하지만(그래도 keyframe 개수 기준 20.8%만 감소), **VIGS에는 거의 안
통한다**(keyframe 개수 6.6%만 감소) — VIGS의 실시간화 병목은 "매 프레임 비용이
크다"가 아니라 "**keyframe 하나당 처리 비용(6iter의 GRU+BA)** 자체를 줄이거나,
keyframe 발생 자체를 억제(더 큰 flow 임계값)하는 것"이 유효한 레버라는 뜻 —
`iters1`/`iters2` 축소, `frontend_window`/`radius` 축소, 또는
`motion_filter.thresh` 상향(keyframe 밀도 자체를 낮춤, 단 이건 궤적 정확도에
더 직접적 영향)이 다음 실험 후보.

## ⚠ 중대 정정 — "온라인 루프 총합" 전체가 리더 프로세스의 인위적 20초 슬립을 포함하고 있었음 (2026-07-20)

**발단**: 슬라이드/차트로 정리하던 중 "27.0초 track() 바깥 오버헤드 중 21.1초 미계측
잔여가 정확히 뭔지" 확인 요청 → `demo.py` 메인 루프에 `pbar_update`/`pbar_set_
description`/`save_trajectory_periodic` 계측을 새로 추가해 1253 전체 시퀀스를
재실행. 결과: 이 셋을 다 합쳐도 **0.14초**(pbar_update 0.03s+pbar_set_description
0.10s+save_trajectory_periodic 0.01s)뿐 — 가설(Python 루프 오버헤드)이 완전히
기각됨. 그런데도 `ONLINE_LOOP_START/DONE_EPOCH` 총합과 `demo_loop` 태그 합 사이에
여전히 **~20.85초 갭**이 남아있어 추가 조사.

**근본 원인 확정**: `demo.py`의 리더 서브프로세스(`mono_stream`)가 마지막 프레임을
큐에 넣은 뒤 `time.sleep(20)`(라인 92)을 하고서야 종료하는데, `reader.join()`
(라인 200)이 **타이밍 마커(`TRACK_LOOP_DONE_EPOCH`) 출력보다 먼저** 실행되도록
코드가 짜여 있었음 — 즉 이 인위적 20초 대기가 "온라인 루프"로 측정되는 구간 안에
그대로 포함되어 있었음. 트래킹/매핑 연산과는 완전히 무관한 프로세스 종료 대기.

**수정**: `TRACK_LOOP_DONE_EPOCH`/`ONLINE_LOOP_DONE_EPOCH` 마커 출력을
`reader.join()`(+`mp_backend` 정리)보다 앞으로 옮김 — 리더 프로세스 정리는 순수
후처리(teardown)이지 측정 대상인 온라인 워크로드가 아니므로 타이밍에서 제외.

**영향 범위**: `motion_filter`/`frontend`/`PGBA`/`gs_mapping` 등 **개별 구성요소
수치는 전부 이 버그와 무관**(각자 독립적으로 `_Sect`/`_timed()`로 감싼 실제 연산
시간이라 리더 프로세스 종료 대기와 무관) — **오직 `ONLINE_LOOP_START/DONE_EPOCH`로
계산한 "총합"과 거기서 파생된 "27.0초 오버헤드"·"실시간 대비 배수"만 ~20초 부풀려져
있었음.** fps 스윕(ORB vs VIGS 비교)·evo 궤적 정확도 비교는 이 마커를 안 쓰고
`vigs_track_total` 태그를 프레임별로 직접 합산했으므로 **영향 없음**.

**재검증(1253 전체, imu_cpp+TensorRT 가속, 버그 수정 후 새 런)**:

| | 순차 실행(gs_parallel 없음) | `_gs_parallel: true` |
|---|---:|---:|
| **온라인 루프 총합(수정 후)** | **150.56초** (기존 보고 180.10초 대비 **−29.5초**) | **98.94초** (기존 보고 133.04초 대비 **−34.1초**) |
| 실시간 대비(÷65.1초) | **2.31배** (기존 2.77배) | **1.52배** (기존 2.04배) |
| motion_filter | 8.78초 | 13.49초(경합 지연 포함) |
| frontend | 40.32초 | 63.46초(경합 지연 포함) |
| PGBA | 9.48초 | 10.64초 |
| gs_mapping | 85.77초(직접 실행) | 큐잉 0.56초, 실제 연산은 백그라운드 76.22초 |
| queue_get_wait+model_loading+기타 | 6.00초 | 6.97초 |
| held-out/keyframe PSNR | 22.47/22.64dB | 22.60/22.92dB |

수정 후엔 `demo_loop` 태그 합(150.34초)이 실측 총합(150.56초)과 **0.2초 이내로
거의 완전히 일치** — "미계측 잔여"가 사실상 해소됨(기존 21.1초 → 0.2초).

**오버랩 효율도 재계산**: 순차 합(89.99+76.22=166.21초) 대비 실측(98.94초) →
절약 67.27초, 최대 가능 절약 76.22초 → **오버랩 효율 88.3%**(기존 66.0%에서 대폭
상향 — 새 런의 tracking/mapping 절대치가 달라 직접 비교는 참고용, 다만 방향은
일관되게 개선). **이론적 최선(완벽 병렬)도 max(58.57, 85.77)=85.77초**(기존
90.5초) → **65.1초 대비 1.32배로 여전히 초과하지만 이전 추정(1.39배)보다
격차가 줄어듦.**

**결론**: 이번 정정으로 VIGS-SLAM(gs_parallel)의 실시간 격차가 이전 생각보다
**훨씬 작다**(2.04배→**1.52배**)는 게 확인됨 — exp53의 목표(frontend 경량화)가
달성해야 할 감축폭도 그만큼 작아짐. 다만 결론의 방향 자체(①gs_mapping 연산량
감소가 최우선 ②frontend는 경합 대응이 핵심 ③잔여 오버헤드는 이제 무시 가능한
수준으로 해소됨)는 안 바뀜 — ③번은 오히려 "해결됨"으로 격상. exp52/53 관련
모든 향후 실측은 이 수정된 `demo.py` 기준으로 진행.

## GS Mapping 루프 최대 세분화 (2026-07-20)

**목적**: 기존 `map()` 내부 5단계(rasterize/loss_compute/backward/optimizer_step/
densify_prune)만으로는 `_process_track_data_impl()`(pose/scale 업데이트, camera 생성,
`add_next_kf` 등 map() **바깥**의 부가작업)가 완전히 미계측이었음 — `gs_backend.py`에
`_Sect`를 추가해 이 함수 전체를 계측 범위로 넓힘.

**신규 계측 항목**(`_process_track_data_impl`, `process_track_data,{key},{ms}` 태그):
- `pose_scale_update`: PGBA 보정 시 기존 Gaussian 위치/스케일/회전 갱신(SO3 연산)
- `w2c_compute`: pose 행렬 GPU 변환
- `camera_init`: `Camera.init_from_tracking(...)` — keyframe별 카메라 객체 생성
- `render_for_mask`: 신규 keyframe 판정 시 마스킹용 depth/transmittance 렌더
- `add_next_kf`/`add_next_kf_init`: `extend_from_pcd_seq(...)` — 신규 Gaussian 초기화(unprojection)
- `map_dispatch`: `self.map(...)` 호출 전체(기존 5단계 + **map() 내부 미계측**을 감쌈)

**1253 전체 재실행 결과**(gs_parallel, GS Mapping 스레드 총 **93.0초**, 12단계):

| 순위 | 항목 | 시간 | 비중 |
|---|---|---:|---:|
| 1 | rasterize | 33.69초 | 36.2% |
| 2 | backward | 21.13초 | 22.7% |
| 3 | loss_compute | 20.91초 | 22.5% |
| 4 | **map() 내부 미계측(신규 발견)** | **12.00초** | **12.9%** |
| 5 | add_next_kf | 2.01초 | 2.2% |
| 6 | optimizer_step | 1.27초 | 1.4% |
| 7 | camera_init | 1.19초 | 1.3% |
| 8 | render_for_mask | 0.53초 | 0.6% |
| 9 | densify_prune | 0.15초 | 0.2% |
| 10 | add_next_kf_init | 0.07초 | 0.1% |
| 11 | pose_scale_update | 0.04초 | 0.0% |
| 12 | w2c_compute | 0.03초 | 0.0% |

**핵심 발견**:
1. **rasterize+backward+loss_compute가 81.4%로 여전히 압도적** — `process_track_data`
   부가작업(camera_init+add_next_kf+render_for_mask+pose_scale_update+w2c_compute =
   3.87초, 4.2%)은 애초 가설과 달리 무시할 만한 수준. GS Mapping 최적화는 계속
   rasterize/backward/loss_compute(=map() 내부 핵심 3단계)에 집중하는 게 맞음.
2. **`map_dispatch`(89.15초) − 기존 5단계 합(77.15초) = 12.00초(12.9%)의 새로운
   미계측 포켓 발견**. `map()` 코드를 다시 보면 이 자리엔 (a) 매 iteration마다
   전체 gaussian에 대해 계산하는 `isotropic_loss`(`scaling.mean(dim=1)` 등, gaussian
   개수가 늘어날수록 커짐) (b) `viewpoint_stack`/`random_viewpoint_stack` 구성과
   `torch.randperm` 기반 view 샘플링이 있음 — 둘 다 아직 개별 계측은 안 함(다음 후보).
3. 이번 라운드로 GS Mapping 스레드의 실제 총 작업량은 기존 "raw 76.22초"(map() 내부
   5단계만)보다 **93.0초에 더 가까움**(부가작업 3.87초+map() 내부 미계측 12.00초
   추가분). exp52/53 시나리오 슬라이드의 "gs_mapping raw"는 여전히 76.22초(map()
   내부만) 기준으로 표기 중 — 완전한 GS Mapping 스레드 총 부하를 볼 때는 이 93.0초가
   더 정확한 수치임을 참고.

**exp53 반영**: `map()` 내부 미계측 12.0초(12.9%)를 다음 계측 후보로 추가 —
`isotropic_loss` 계산과 view 샘플링을 각각 `_Sect`로 감싸면 완전히 해소 가능.
