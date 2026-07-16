# exp49 — Photo-SLAM 기반 Incremental 3DGS 이관

- 상태: **계획 수립 (2026-07-16). 빌드 완료, 파이프라인 검증 착수 전.**
- 배경: [exp48](exp48_incremental_plan.md)에서 vanilla 3dgs-custom 위에 windowed/online 학습을 얹는 자체 구현이 근본 한계에 도달(15~18dB, 통제 배치 30.2dB). reset_opacity·LR감쇠·윈도우 이탈 문제를 우리가 맨땅에서 재발견 중이었고, 이 문제들을 **이미 설계로 해결한 검증된 online 3DGS-SLAM(Photo-SLAM, CVPR 2024)** 으로 baseline을 이관하기로 결정.

## 왜 Photo-SLAM인가 (exp48 종결 근거의 연장)

survey list(Awesome-3DGS-SLAM 등) 조사 결과, "incremental이 검증된" 후보 중 우리 구조와 가장 맞는 것:

- **Photo-SLAM**: ORB-SLAM3 트래킹 + GS 매핑. EuRoC config(`cfg/ORB_SLAM3/Stereo/EuRoC`, `cfg/gaussian_mapper/Stereo/EuRoC`)에서 확인한 핵심 — **`opacity_reset_interval: 0`(끔), `position_lr_init==final`(상수 LR), `new_keyframe_times_of_use`+"전원 사용권 소진 시 +1" 방식으로 옛 keyframe을 hard-evict 안 하고 낮은 빈도로 계속 리프레시**. exp48 가설 라운드2에서 우리가 하나씩 꺼봤다가 실패한 것들이 여기선 geometry-based densification과 묶여 통째로 적용돼 있음.
- egocentric_splats(Meta): 센서 분리는 검증됐으나 **배치만** — incremental은 우리가 또 만들어야 함. 그래서 후순위.
- VINGS-Mono: visual-inertial 전제, 우리 입력과 어긋남. reference로만 보유.

## 빌드 완료 상태 (2026-07-16)

`repos/main/Photo-SLAM` 심링크 연결(`/home/wosas/Desktop/26-1_RPM/gsProjects/Photo-SLAM`). RTX 5070 Ti(Blackwell, compute 12.0) + CUDA 12.8(vings env) + LibTorch 2.9 + 자체빌드 OpenCV 4.13(CUDA) 조합으로 **전체 빌드 성공**. 로직 변경 없이 호환성 패치만:

- 서드파티: glm 로컬설치, OpenCV 4.13.0(4.8.0은 Thrust 2.x 충돌), CUDA 헤더/npp 심링크 보강(conda `targets/` 레이아웃)
- 빌드 인프라: `CMAKE_POLICY_DEFAULT_CMP0146=OLD`(CMake 3.28의 FindCUDA 제거 우회), `CUDA_ARCHITECTURES 75;86→120`
- 소스 패치: `<cstdint>`/`<cfloat>` 누락 헤더, `torch::cat({...})→torch::cat(std::vector)`, `c10::guts::to_string→static_cast<void*>`, `glm::perspective` float 캐스트, `c10Alloc::Stat/StatType→c10::CachingAllocator::`
- 산출물: `bin/{euroc_stereo, train_colmap, replica_mono/rgbd, tum_mono/rgbd, view_result}` + `lib/{gaussian_mapper, cuda_rasterizer, simple_knn}.so`

## ⚠ 핵심 기술 제약: Fisheye624 vs 스톡 ORB-SLAM3

우리 Aria SLAM 카메라(`data/01_euroc_openmavis_input/Aria.yaml`)는 **`Camera.type: "Fisheye624"`** (6 radial + 2 tangential + 4 thin-prism). 이건 OpenMAVIS(MAVIS)가 자체 지원하는 모델이고, **Photo-SLAM이 번들한 스톡 ORB-SLAM3는 Pinhole/KannalaBrandt8(KB4)만 지원 → Fisheye624 트래킹 불가**.

→ 두 갈래:
1. **(권장) SLAM 트래킹을 아예 안 씀 — 이미 완주한 OpenMAVIS export를 replay.** exp48 철학 그대로. `examples/train_colmap.cpp`가 **`GaussianMapper`를 `pSLAM=nullptr`로 구동**(COLMAP 씬에서 직접 읽기)하는 걸 확인 — 즉 Photo-SLAM의 **우수한 매핑 백엔드(geometry densification, no-reset, times-of-use 슬라이딩 윈도우)만 떼어내 우리 데이터로 먹일 수 있음.** Fisheye624 문제를 통째로 우회.
2. **(후순위) OpenMAVIS의 Fisheye624 카메라 모델을 Photo-SLAM의 ORB-SLAM3에 이식** — 라이브 트래킹+루프클로저까지 원할 때. C++ 대공사지만 OpenMAVIS가 이미 구현해둔 걸 옮기는 것. Phase 3 이후로 연기.

## Phase 계획

### Phase A — 파이프라인 생존 검증 (수정 0줄) ✅ 완료 (2026-07-16)
목표: 빌드된 바이너리가 실제로 학습/렌더까지 도는지, GPU에서 안 죽는지 확인.
- A1: `train_colmap`을 우리 1253 RGB(`03_rgb_3dgs_full`)로 실행. **결과 성공.**
- 성공기준: 크래시 없이 완주 + 렌더 육안 정상.

**A1 실행 결과:**
- 데이터: `03_rgb_3dgs_full`을 pycolmap으로 txt→bin 변환. **train_colmap이 전 이미지를 학습 전 GPU 선적재(line 145)하는 배치 구조라 1303장(1024²×float32≈16GB)은 16GB 카드에서 OOM** → 매 8번째 163장 서브샘플 + iter 3000/densify_until 2000로 축소해 스모크.
- 학습 정상 완주: iter 3000, ema_loss 0.085→0.055, densify로 가우시안 84k→206k 단조증가.
- **train PSNR 평균 26.33dB**(163뷰, 3000iter·서브셋이라 낮음 — 절대수치 의미 없음, 배관 검증용). 렌더 육안: frame_00633(exp48 최악 화이트보드/선반 구역)이 방 구조 알아볼 수 있게 복원 — **매핑 백엔드가 우리 RGB에서 정상 동작 확인.**
- ⚠ **알려진 사소한 버그**: 종료 시 `saveSparsePointsPly`에서 크래시(`sparse_points_xyz_`가 COLMAP 모드에선 undefined tensor). **가우시안 PLY(`point_cloud/iteration_N/point_cloud.ply`)·렌더·메트릭은 그 전에 정상 저장됨** — SLAM sparse point PLY 덤프만 실패. Phase B에서 패치 필요(해당 호출 가드 또는 sparse tensor 초기화).
- 미실행: A2(`euroc_stereo`) — Fisheye624 트래킹 제약(위)으로 replay 경로 확정했으니 스킵.

### Phase B — Photo-SLAM 네이티브 품질 baseline (우리 1253 RGB, 배치)
목표: **동일 코드베이스에서 배치 상한을 먼저 확보** — exp48이 "배치 30.2dB vs 우리 incremental 18dB"를 코드베이스가 달라 불공정 비교했던 문제를 해소.
- `train_colmap` 경로로 우리 1253 RGB 씬(`03_rgb_3dgs_full`, COLMAP 포맷 이미 있음)을 Photo-SLAM GaussianMapper로 배치 학습.
- **평가 하네스 정합 필수**: exp48에서 발견한 eval 버그(llffhold-8이 test.txt를 무시) 교훈 반영 — Photo-SLAM 렌더 결과를 우리 held-out 163뷰(llffhold-8 기준으로 매핑 확정된 그 세트)와 **동일 프레임**으로 PSNR 비교. 3dgs-custom 배치 챔피언(32~35dB)과 같은 잣대로.
- 성공기준: Photo-SLAM 배치가 3dgs-custom 배치와 동급 품질(±2dB) → 매핑 백엔드 자체는 신뢰 가능 확정.

### Phase C — Incremental replay 진입점 (진짜 기여) ✅ v1 완주 (2026-07-16)
목표: keyframe을 **시간 순서대로** GaussianMapper에 공급하는 스트리밍 진입점 작성.

**구현:**
- `scripts/incremental/build_photoslam_replay.py` (신규): OpenMAVIS가 정한 57 keyframe을 per-keyframe 바이너리 COLMAP 청크로 생성 (`06_photoslam_replay/chunk_NNN/`). 각 청크 = RGB keyframe 1장(04_incremental) + RGB-cam pose + 그 keyframe의 새 SLAM 점(05_dense extra_points, causal). image_id 유니크(idx+1, scene fid 충돌 방지), 이미지명 `kf_NNN.jpg`.
- `GaussianMapper::trainReplay(replay_dir, iters_per_kf)` (신규 public 메서드, `src/gaussian_mapper.cpp`): 청크를 시간순으로 하나씩 — 카메라 등록(1회) → keyframe 로드+피라미드+times_of_use → 새 점 createFromPcd(청크0)/increasePcd(이후) → `trainForOneIteration` × iters_per_kf. Photo-SLAM의 times-of-use 슬라이딩 윈도우가 옛 keyframe 리프레시 담당(hard evict 없음). 마지막에 tail 최적화 + 렌더 + PLY 저장.
- `examples/train_replay.cpp` (신규, 얇은 진입점) + CMake 타겟. 빌드 성공.
- config: colmap config 기반, `opacity_reset_interval: 0`(EuRoC식 끔), densify_until 30000.

**v1 실행 결과 (iters_per_kf=150 → 총 8550 iter, exp48과 동일 예산):**
- **크래시 없이 57 keyframe 전체 완주.** 가우시안 N: 529 → 716,032 단조증가.
- **train keyframe PSNR(57뷰): 평균 31.12dB, 최저 22.84, 최고 39.37, PSNR<15 = 0개.** exp48이 같은 장면에서 8~17dB로 무너졌던 것과 극적 대비. 렌더 육안: 책상 나뭇결·조명·의자·바닥까지 또렷 — exp48 안개 렌더와 차원이 다름.
- ⚠ **주의: 이건 train view(학습한 57 keyframe)라 exp48의 held-out 18dB와 직접 비교 불가.** 공정 비교엔 held-out 163뷰 평가 필요(다음 단계 C-eval).

**다음 (C-eval):** llffhold-8 기준 held-out 163뷰를 non-train keyframe으로 scene에 추가(times_of_use=0)해서 렌더 → GT와 PSNR. exp48 18dB / 배치 상한 30.2dB와 같은 잣대 비교.

### Phase D — 우리 방법론 이식
- D1: **hybrid init**(RoMA+PPM+depth-mono) — Photo-SLAM의 geometry-based densification과 결합/대체. init이 배치 트랙 단일 지배 레버였으므로 우선순위 높음.
- D2: **carve loss** — Photo-SLAM 학습 루프(`trainForOneIteration`)에 floater 억제 압력 이식. loss 레벨이라 이식 가능성 높음.
- D3: **Aria 센서 분리**(흑백 트래킹/RGB 매핑) — Phase C가 replay라 pose는 이미 RGB 프레임용으로 변환된 걸 공급(exp48 `build_incremental_chunks.py`의 T_rgb 변환 재사용). 라이브 트래킹까지 갈 거면 위 "제약" 2번(Fisheye624 이식).

## 데이터 자산 (이미 보유)
- EuRoC 입력: `data/01_euroc_openmavis_input/mav0/{cam0,cam1,imu0}` (stereo 1311프레임) + `timestamps.txt` + `Aria.yaml`
- RGB 매핑 데이터: `data/03_rgb_3dgs_full` (COLMAP 포맷, 1303프레임, held-out test.txt 존재)
- OpenMAVIS export: `data/02_openmavis_output/orb_export/{keyframes,map_points,observations}.jsonl` (57 keyframe)
- exp48 청크 빌더: `scripts/incremental/build_*.py` (RGB 프레임 최근접 선택 + T_rgb pose 변환 로직 재사용 가능)

## 열린 질문 / 리스크
1. Photo-SLAM GaussianMapper가 pSLAM=nullptr일 때 `cullKeyframes` 등 Atlas 의존 코드가 안전한지 (train_colmap이 이미 그렇게 도니 대체로 OK로 추정, Phase A에서 확인).
2. Photo-SLAM의 카메라 모델(매핑측)이 우리 RGB 카메라 intrinsic(pinhole+왜곡)을 그대로 받는지 — COLMAP 포맷이면 자동일 가능성.
3. carve loss는 CUDA 커널/CPU carve field 의존 — Photo-SLAM의 텐서 파이프라인(LibTorch)과 접합 비용(Phase D2 리스크).
