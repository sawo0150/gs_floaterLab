# T1/T2 비교 방법 후보와 입력 호환성

조사일: 2026-10-01. 값은 미측정이며 방법 이름 자리만 마련한다. 공개된 모든 논문을 망라했다는 뜻은 아니며, 아래는 확인한 RGB/visual-inertial Gaussian mapping 비교군이다.

## 표에 미리 넣을 방법

| Method | 입력 그룹 | 자리 / 확인 근거 | 비교 전 확인할 조건 |
|---|---|---|---|
| VIGS-SLAM | RGB+IMU | 직접 baseline. [논문](https://arxiv.org/html/2512.02293v2) | official source, zero-tail adapter, 예산, frontend 설정 |
| Ours | RGB+IMU | 현재 개발 mapper | geometry 항/renderer/config 확정 |
| VINGS-Mono | RGB+IMU | [논문](https://arxiv.org/abs/2501.08286), [공식 코드](https://github.com/Fudan-MAGIC-Lab/VINGS-Mono) | dataset adapter, refinement/학습 종료, primitive 정의 |
| Splat-SLAM | RGB | [공식 코드](https://github.com/google-research/Splat-SLAM) | IMU 미사용 표시, pose filling 및 post-refinement 분리 |
| HI-SLAM2 | RGB | [공식 프로젝트](https://hi-slam2.github.io/), [코드](https://github.com/Willyzw/HI-SLAM2) | monocular prior, 최종 refinement 분리 |
| MonoGS | RGB | [공식 코드](https://github.com/muskie82/MonoGS) | mono 설정 사용, sensor depth 미사용, 동기화/종료 조건 |
| Photo-SLAM | RGB | [공식 코드](https://github.com/HuajianUP/Photo-SLAM), [논문](https://arxiv.org/abs/2311.16728) | monocular 설정, 온라인 종료 지도, ORB frontend 비용 |
| CaRtGS | RGB | [논문](https://arxiv.org/html/2410.00486v2)에서 monocular 평가 확인 | 같은 RGB stream, backend/refinement/계산량 계측 |
| IG-SLAM | RGB | [공식 코드](https://github.com/Liouvi/IG-SLAM), [논문](https://arxiv.org/abs/2408.01126) | mono 설정, online depth, timing/후처리 범위 |

VIGS-SLAM의 rendering 비교군에는 VINGS-Mono, Splat-SLAM, HI-SLAM2가 포함된다. 여기서는 추가로 공개 mono Gaussian mapping 구현도 후보 행에 넣었다. RGB-only 방법은 같은 image stream으로 평가 가능한 비교군이지만 RGB+IMU와 같은 센서 입력이라고 쓰지 않는다. 엄격한 동일 modality 비교는 RGB+IMU 그룹 안에서 한다.

## 조건부 / 대기 후보

- **MM3DGS-SLAM (monocular+IMU variant)**: [논문](https://arxiv.org/abs/2404.00923), [공식 코드](https://github.com/VITA-Group/MM3DGS-SLAM). 기본 공개 실행은 RGB/depth/IMU를 사용한다. VIGS 문헌은 predicted monocular depth 변형을 언급하지만 해당 모드의 코드/설정을 복원하기 전 동등 비교군으로 확정하지 않는다. T1/T2 layout에는 조건부 행을 별도로 예약한다. sensor depth를 주입한 결과는 우리 RGB+IMU 표와 섞지 않는다.
- **IMGS-SLAM**: [공식 저장소](https://github.com/Xiaosz-s/IMGS-SLAM)는 monocular Gaussian reconstruction을 설명하지만 확인 시점 파일 목록은 README/assets 중심이었다. 실행 코드·원문 평가 조건 확보 전 확정 baseline 표에 넣지 않고 대기 목록으로 보존한다.

## 같은 표의 직접 후보에서 제외하는 종류

- RGB-D 전용 실행의 SplaTAM/RTG-SLAM/Gaussian-SLAM 등을 depth 센서 없이 실행되는 것처럼 추가하지 않는다. RGB-only 변형이 검증되면 재검토한다.
- ORB-SLAM3, DROID-SLAM, DBA-Fusion, VINS-Mono 등의 pose-only 결과는 Gaussian rendering PSNR/#G 비교 행이 아니다. tracking 비교에 별도로 활용할 수 있다.
- offline 3DGS/GT pose 재구성은 online baseline이 아니다. 넣으면 oracle 또는 offline reference 패널로 분리한다.

## 공정한 행 추가 조건

각 방법의 dataset adapter, 공통 held-out split, 해상도, 실제 input modalities, learned prior, 종료 시점, 추가 refinement 유무, #G 정의를 감사한다. 같은 평가가 불가능하면 값은 —/NA로 남기고 그 이유를 명시한다. 공개 논문의 다른 데이터셋·해상도·후처리 수치를 빈칸에 대신 채우지 않는다.

동일-work 비교를 위해 각 코드에 render/optimizer 계측이 필요하다. 동일-time 비교는 실제 hardware/input clock/deadline을 공유한다. 모든 후보를 지금 실행하라는 계획은 아니며 우선 VIGS-SLAM/Ours를 완료한 뒤 조건이 맞는 방법부터 채운다.
