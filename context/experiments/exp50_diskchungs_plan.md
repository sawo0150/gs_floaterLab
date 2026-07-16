# exp50 — DiskChunGS: Out-of-Core Memory Management 기반 점진적 3DGS 매핑 및 Stereo-Inertial 연동

- 상태: **Phase A & B 완료. B1(Fisheye624 라이브 트래킹) 성공 (2026-07-16 밤). Phase C(GS 매핑 연동)는 카메라 모델 분리 필요 — 진행 중.**
- 배경: [exp49](exp49_photoslam_plan.md)에서 Photo-SLAM 기반 Replay 매핑(Phase C)을 통해 held-out PSNR **22.14dB**를 기록하며 `exp48` 자체 구현의 18.23dB 천장을 돌파하였습니다. 사용자 제안으로, Photo-SLAM의 확장판이자 최신 out-of-core 가우시안 SLAM 기법인 **DiskChunGS (ETH Zurich, 2025.11 발표)**를 사용해 대규모 장기 매핑 및 디스크 스왑 기반 가우시안 매핑 성능을 탐색하고, **Stereo-Inertial (visual-inertial)** 입력과의 연동을 검증하는 새 실험 트랙 `exp50`을 런칭합니다.

## 왜 DiskChunGS인가?

1. **디스크 스왑 (Out-of-Core) 메모리 관리**: 
   - 3DGS SLAM은 장면이 커질수록 가우시안 수가 급증해 GPU 메모리 OOM에 직면합니다.
   - DiskChunGS는 전체 가우시안 맵을 **공간적 청크(spatial chunks)**로 분할하고, 카메라 근처의 활성(active) 청크만 GPU 메모리에 유지하며, 멀어진 비활성(inactive) 청크는 디스크로 스왑 아웃시킵니다.
   - 이를 통해 GPU 메모리 용량 한계를 완전히 우회하여 대규모/장시간 점진적 매핑을 지원합니다.
2. **Photo-SLAM 백엔드 계승**:
   - DiskChunGS는 Photo-SLAM 매핑 백엔드를 포크/확장하여 작성되었으므로, `times-of-use` 슬라이딩 윈도우 및 geometry-based densification 등의 우수한 점진적 학습 특징을 그대로 공유합니다.
3. **IMU_STEREO (Stereo-Inertial) 지원**:
   - 매퍼 내부(`GaussianMapper::initializeSensorType`)에 `ORB_SLAM3::System::IMU_STEREO` 형식을 기본 지원하며, ORB-SLAM3의 `TrackStereo` 함수를 통해 IMU 가속도/자이로 데이터를 비주얼 트래킹과 퓨전하여 전달할 수 있습니다.
   - IMU 융합을 통해 빠른 카메라 회전 시에도 트래킹이 깨지지 않는 극대화된 로버스트성을 획득합니다.

---

## 🛠 Phase 계획 및 수행 결과

### Phase A — Submodule 동기화 및 호환 빌드 (완료)
- **수행 내역**:
  1. `DiskChunGS/CMakeLists.txt` 및 `scripts/build.sh`에서 Docker 용 하드코딩 경로를 로컬 미니콘다 `vings` 환경 및 `Photo-SLAM` 내부 빌드 라이브러리 경로로 재배치.
  2. GCC 13.3.0 호환성 확보: Sophus 서드파티 라이브러리 빌드 시 `-Werror` 플래그 제거를 통해 array-bounds 경고로 인한 빌드 중단 우회.
  3. **TensorRT 의존성 완화 (Mocking 및 Fallback)**:
     - 호스트 환경에 TensorRT 라이브러리(`NvInfer.h` 등)가 미설치된 상태임에 따라, `depth_anything_tensorrt` 모듈을 모킹 처리.
     - `stereo_depth` 추론을 위한 Fast ACVNet 모델 역시 TensorRT를 사용하는 대신, OpenCV의 고품질 CPU 스테레오 매칭 알고리즘인 **StereoSGBM Fallback**으로 코드를 교체 구현하여 동작 신뢰성 및 빌드 통과 성공.
  4. PyTorch C++ API 호환성 패치: PyTorch 버전에 따라 다른 `c10::cuda::CUDACachingAllocator::Stat` 통계 대신 표준 CUDA API인 `cudaMemGetInfo()`를 사용하여 GPU VRAM 사용량을 추적하도록 `GaussianModel` 및 `GaussianMapper` 코드 수정.
  5. `torch::linalg::inv`가 누락된 버전을 위해 표준 호환 인버스 함수인 `torch::inverse`로 `GuidedMVS` 코드 패치.
  6. GLFW/GLM 라이브러리의 `glm::perspective` 호출 시 `Float32` 타입 불일치 에러 해결 (`static_cast<float>` 추가).

### Phase B — Stereo-Inertial 데이터 로더 및 예제 작성 (완료)
- **수행 내역**:
  1. `examples/euroc_stereo_inertial.cpp` 구현 완료:
     - EuRoC 데이터셋 구조 (`cam0/data/`, `cam1/data/`) 및 timestamps, `imu0/data.csv`의 가속도/자이로 원시 데이터를 안정적으로 로드.
     - 카메라 이미지의 Grayscale/Color 채널 수를 자동 감지하여 Gaussian Splatting 학습용 RGB 포맷으로 알맞게 정규화 및 변환 지원.
     - 카메라 프레임 주기에 맞춰 누적된 IMU 측정값을 동적 슬라이딩 윈도우 형태로 취합해 `pSLAM->TrackStereo`에 동시 주입.
     - 실시간 매핑 시뮬레이션을 위해 `slowdown_factor`를 기반으로 이미지 재생 속도 및 IMU 포인트 센서 타임스탬프를 동적으로 스케일링하는 보간 프레임워크 구현 완료.
  2. `CMakeLists.txt`에 신규 Executable Target인 `euroc_stereo_inertial`을 추가하고 `libgaussian_viewer.so`, `libgaussian_mapper.so` 및 `libORB_SLAM3.so`와 정상 링크 완료.
  3. 빌드 테스트 결과 최종 **`✓ Build completed successfully!`** 확인.

### Phase C — DiskChunGS 매핑 수행 및 held-out PSNR 평가 (대기)
- **목표**: EuRoC(예: MH_01_easy 등) 데이터셋을 대상으로 Stereo-Inertial 점진적 매핑을 구동하고, 최종 품질을 held-out 뷰 하네스로 평가합니다.
- **실행 명령 가이드**:
  ```bash
  # 1. EuRoC sequence 또는 원하는 Stereo-Inertial 데이터셋 준비
  # 2. DiskChunGS 실행 바이너리 구동 (slowdown_factor=2.0 으로 충분한 최적화 시간 확보)
  ./bin/euroc_stereo_inertial \
      /home/wosas/Desktop/26-1_RPM/gsProjects/DiskChunGS/third_party/ORB-SLAM3/Vocabulary/ORBvoc.txt \
      /home/wosas/Desktop/26-1_RPM/gsProjects/DiskChunGS/third_party/ORB-SLAM3/Examples/Stereo-Inertial/EuRoC.yaml \
      /home/wosas/Desktop/26-1_RPM/gsProjects/DiskChunGS/cfg/gaussian_mapper/tum_mono.yaml \
      /path/to/EuRoC/MH_01_easy \
      /path/to/EuRoC/MH_01_easy/mav0/cam0/timestamps.txt \
      /home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/results/exp50_output/ \
      no_viewer \
      2.0
  ```
- **평가**:
  - 저장된 가우시안 PLY에 대해 3dgs-custom의 `render.py --eval`로 163 held-out 뷰에 대한 PSNR/SSIM/LPIPS 지표 측정 및 기존 Photo-SLAM(22.14dB)과 성능 비교.

## ⚠ 검증 결과: Phase A/B "완료" 재확인 필요했던 지점 + B1 root-cause 수정 (2026-07-16 밤)

Phase A/B의 빌드 성공 자체는 검증 확인됨(실제 ELF 바이너리, 링크 정상, out-of-core 스왑 코드 `model_memory.cpp`/`model_storage.cpp` 실체 있음, TensorRT fallback 패치 실체 있음). 다만 **Phase C가 실제로 한 번도 실행된 적이 없었고**, 실행해보니 진짜 버그 2건이 드러남:

1. **`output_directory` 인자 버그**: `euroc_stereo_inertial.cpp`가 출력 경로를 `argv[6]`이 아닌 `argv[5]`(timestamps 파일 경로)로 잘못 읽고 있었음(`argv[6]` 미사용). 수정.
2. **Fisheye624 카메라 모델 부재**: DiskChunGS의 ORB-SLAM3도 Photo-SLAM과 동일하게 Pinhole/KannalaBrandt8만 지원 — "IMU 융합으로 로버스트성 획득"이라는 카드의 서술은 **우리 Aria 데이터로는 미검증 상태**였음(표준 EuRoC 카메라 모델 전제).

### B1: Fisheye624 이식 + 라이브 stereo-inertial 트래킹 (성공)

[exp49](exp49_photoslam_plan.md) B1에서 만든 Fisheye624 패치를 DiskChunGS의 ORB-SLAM3 서브모듈에도 이식(포맷만 clang-format 스타일 맞춤, 로직 동일). 첫 실행에서 **Photo-SLAM B1과 동일한 증상**(매 keyframe마다 15점 미만 미니맵 → 리셋 반복) 재발 — IMU_STEREO로 돌려도 개선 없어 "IMU 부재가 원인"이라는 가설이 기각됨.

**3단계 진단으로 근본 원인 확정:**
1. **파일 무결성**: `Fisheye624.{h,cpp}`는 OpenMAVIS 원본과 byte-identical(`diff` 무출력) — 카메라 수학 자체는 무죄.
2. **ORB 추출량 계측**(`[diag2]` N/nStereoMatched 로깅): N(추출 keypoint)은 ~1500으로 정상, 그러나 `nStereoMatched`(L/R 매칭 성공)는 **1500개 중 9~31개(~98% 손실)** — 추출이 아니라 스테레오 매칭 단계의 문제로 확정.
3. **근본 원인 2건** (`[diag3]` 계측으로 확정):
   - **a) `Frame::ComputeStereoFishEyeMatches()`가 `mpCamera`를 무조건 `static_cast<KannalaBrandt8*>`로 캐스팅** — 실제 객체는 `Fisheye624*`인데 다른 타입으로 재해석(UB)하고 그 타입의 `TriangulateMatches`를 호출해 완전히 엉뚱한 왜곡 모델로 삼각측량. `GeometricCamera` 베이스에 `virtual TriangulateMatches`를 추가(OpenMAVIS와 동일 패턴)해 가상 디스패치로 전환 → 처음엔 수치 불변(원인 아직 남음).
   - **b) `Tracking::SetSettings()`의 `mpCamera2` 설정 조건이 `settings->cameraType() == Settings::KannalaBrandt`로 하드코딩** — `Fisheye624Type`이 걸리지 않아 `mpCamera2`가 계속 null로 남고, 트래킹이 (실제론 unrectified wide-FOV 쌍인데) **rectified pinhole용 블록매칭 스테레오 경로**로 잘못 빠짐(`ComputeStereoFishEyeMatches` 자체가 호출도 안 됨 — `[diag3]` 로그가 전혀 안 찍혀서 발견). 조건에 `Fisheye624Type` 추가.

**수정 후 결과**: stereo 매칭 9~31개 → **33~76개(지속)**, 전체 실행 구간 **리셋 0회** (이전엔 매 keyframe마다 리셋). **Aria Fisheye624 IMU_STEREO 라이브 트래킹 최초 성공.**

**남은 이슈**: 트래킹 성공 후 GaussianMapper 단계에서 크래시 — `"Colmap camera model not handled: only undistorted datasets (PINHOLE or SIMPLE_PINHOLE cameras) supported!"`. 이건 새 버그가 아니라 **예상된 다음 관문**: 3DGS 렌더러는 pinhole 가정이 필수라 Fisheye624를 매핑에 직접 쓸 수 없음 — exp49의 "RGB 카메라를 트래킹과 분리 주입" 설계(트래킹=Aria 흑백 fisheye, 매핑=별도 RGB pinhole 카메라)가 바로 이 지점을 위한 것. 다음 단계로 자연스럽게 이어짐.

### 다음 단계
1. **RGB 매핑 카메라 분리 주입**: `Atlas.h::MappingOperation::addKeyFrame`(또는 DiskChunGS의 동등 지점)에서 트래킹용 fisheye 이미지 대신 최근접 RGB 프레임 + RGB pinhole 카메라(변환된 pose)를 매퍼로 보내도록 수정. exp48의 `build_incremental_chunks.py` T_rgb 변환 재사용 가능.
2. 이후 Phase C(실제 매핑+평가) 재개.

