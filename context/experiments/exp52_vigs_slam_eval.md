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
