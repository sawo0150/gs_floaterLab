# 데이터셋 후보 (v01, 2026-09-08)

> **제약: 우리 입력은 단안 RGB + IMU.**
> 렌더 품질이 주장이므로 **RGB 필수**, tracking 이 IMU 를 쓰므로 **IMU 필수**.
> 이 둘을 동시에 만족하는 공개 데이터셋이 생각보다 적다 —— 그게 이 조사의 이유다.

## ★ Aria 계열 — 센서가 우리와 같다

| 데이터셋 | RGB | IMU | GT | 비고 |
|---|:-:|:-:|---|---|
| **Aria Digital Twin (ADT)** ICCV'23 [arXiv 2306.06362] | ✓ | ✓ (2 stream) | **6DoF pose · depth map · photorealistic 합성 렌더** | 흑백 2 + RGB 1 + IMU 2. **깊이맵과 합성 렌더까지 GT** → held-out 렌더 평가에 이상적 |
| **Aria Everyday Activities (AEA)** [arXiv 2402.13349] | ✓ | ✓ | 전역 정렬 3D 궤적 + scene point cloud | 1~2인 착용, 일상 활동 |
| Aria Synthetic Environments | ✓ | ✓ | 완전 합성 | |

★ **우리가 Aria glasses 를 쓰므로 센서가 동일하다.** 자체 촬영분과 같은 파이프라인이 그대로 돌고,
*"자기 데이터에서만 되는 것 아니냐"* 를 막아준다. **1순위 후보.**

## VI-SLAM 표준 벤치마크

| 데이터셋 | RGB | IMU | 비고 |
|---|:-:|:-:|---|
| EuRoC MAV | **흑백** | ✓ | VI 표준이지만 **렌더 품질 평가에 부적합**. VIGS-SLAM 도 *"EuRoC provides grayscale images, while the others offer RGB"* 라고 명시하고 렌더는 다른 데이터셋에서 본다 |
| TUM-VI | 흑백 fisheye | ✓ | 어안 스테레오 |
| **RPNG AR Table** | ✓ | ✓ | VIGS-SLAM 사용. motion-capture GT |
| **UTMM** | ✓ | ✓ | MM3DGS-SLAM 의 자체 데이터셋 (RGB-D + IMU) |
| **FAST-LIVO2** | ✓ | ✓ | + LiDAR. GT 를 LiDAR 로 |
| VECtor | ✓ | ✓ | CaRtGS 사용. event + frame + IMU + LiDAR |
| OpenLORIS-Scene | ✓ | ✓ | RGB-D + IMU + odometry, 일상 환경 |
| Newer College | ✓ | ✓ | handheld + LiDAR |

## GS 전용 신규 벤치마크

| | |
|---|---|
| **SLAM&Render** (2025) [arXiv 2504.13713] | **SLAM × neural rendering 교차점 전용.** 40 시퀀스, RGB-D + IMU + 로봇 kinematics. 로봇 매니퓰레이터 촬영이라 카메라 모션 재현 가능. ★ **train/test 궤적이 분리되어 있어 held-out 정의 문제를 통째로 없앤다** (llffhold-8 함정 회피). CC-BY 4.0, GitHub 공개 |

## IMU 없음 (렌더 평가용 참고)

Replica · TUM-RGBD · ScanNet — GS-SLAM 최다 사용이지만 **IMU 가 없다.**
쓰려면 *"IMU 없이 어떻게 돌렸는가"* 를 §4.1 에서 설명해야 한다.

## 참고 — 다른 논문의 선택

| 논문 | 데이터셋 |
|---|---|
| VIGS-SLAM | EuRoC · RPNG AR Table · UTMM · FAST-LIVO2 · 자체(Manifold Odin 1, GT 는 MindCloud LiDAR-VI fusion) |
| CaRtGS | Replica · TUM-RGBD · VECtor (mono / RGB-D / stereo 세 카메라 계통) |
| MonoGS | TUM-RGBD (3 seq) · Replica (8 seq) + 자체(Realsense d455) |
| Taming3DGS | Tanks&Temples · Deep Blending · MipNeRF360 |
| chen2026cover | Tanks&Temples · MipNeRF360 + 자체(휴대폰) 3장면 |

**공통 패턴: 표준 2~3개 + 자체 1개.** 자체 데이터셋을 넣는 것이 관행이다.

## 지금 기울어 있는 쪽

> **자체 Aria 촬영분 + ADT**

같은 센서이고 GT depth·합성 렌더까지 있어 **held-out PSNR 의 근거가 튼튼**하다.
셋째를 넣는다면 **SLAM&Render**(train/test 분리) 또는 **RPNG AR Table**(VIGS-SLAM 과 겹쳐 비교 용이).

## 결정해야 할 것

- 표준 데이터셋 1개인가 2개인가
- ADT 의 어느 시퀀스를, 몇 개
- 자체 촬영분의 GT 를 무엇으로 잡을 것인가 (MPS 는 strict 계약상 supervision 에 못 쓰지만 **평가용 GT 로는** 쓸 수 있는가 — 별도 판단 필요)
- IMU 없는 표준 데이터셋(Replica 등)을 넣을 것인가. 넣으면 그 이유를 §4.1 에 써야 한다
