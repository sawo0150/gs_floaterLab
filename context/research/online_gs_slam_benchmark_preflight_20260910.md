# Online GS-SLAM 논문 벤치마크 사전 조사

> 2026-09-10 후속 실행: 사용자가 현재 워크스페이스 정리 및 RPNG+UTMM 다운로드를
> 승인했다. 정리로 30.3957GiB를 확보했고 저장소 설치는 보류했다.
> 다운로드 시작 뒤 ZIP 디렉터리를 확인한 두 데이터의 해제 크기는 합계
> 52,206,780,347 bytes(약 48.62GiB), 압축본 포함 약 95.33GiB다.
> 아래의 해제 용량 미확인 표기는 사전 조사 당시 상태다.
> 실행 결과는 [정리 audit](intern_cleanup_applied_20260910/README.md)와
> `data/benchmarks/manifests/`에서 확인한다.
> **15:03 KST 완료:** RPNG·UTMM 모두 다운로드·SHA256 기록·ZIP CRC 검증·해제를
> 완료했고 16개 시퀀스의 필수 입력 파일을 확인했다. 저장소 설치·SLAM 실행은 하지 않았다.
> [확정 dataset manifest](../../benchmarks/online_gs/prepared_datasets.json).

확인일: 2026-09-10. 데이터·checkpoint 다운로드, git clone, 패키지 설치, GPU 연산은 하지 않았다. 웹 문서·공개 API·HTTP HEAD와 로컬 읽기 전용 명령으로 조사했다. 아래 용량 중 압축 파일은 Content-Length 실측, 압축 해제·환경·결과 용량은 계획 추정이다.

## 제안

- 1차: RPNG AR Table 8개 + UTMM 8개, VIGS-SLAM upstream / 우리 방법 / HI-SLAM2 / Splat-SLAM / VINGS-Mono.
- 우선 VIGS upstream과 우리 방법으로 각 데이터셋 1개 시퀀스의 입력·평가 adapter를 검증하고 확대한다.
- VIGS 자체 데이터 18개는 후속 강건성 검증으로 사용한다. 렌더 평가용 추가 프로토콜은 별도로 고정한다.
- EuRoC와 FAST-LIVO2는 논문 범위 확장용. MM3DGS는 모달리티가 다른 별도 비교 후보다.
- 신규 대용량 저장소는 `/ssd/gs_slam_benchmark`를 제안한다. 현재 `/ssd`는 root:root 0755여서 colin 계정에 쓰기 권한이 없다. 실제 준비 단계에서 전용 하위 디렉터리만 권한 설정한다. 이번에는 권한을 변경하지 않았다.

## 1. 로컬 실측

| 항목 | 확인값 |
|---|---|
| OS | Ubuntu 24.04.3 LTS |
| CPU | Intel Core i9-12900, 16 core / 24 thread |
| RAM | 31GiB, 확인 시 available 약 19GiB; swap 사용 약 5.2GiB |
| GPU | RTX 5090, 32,607MiB; 확인 시 GUI 프로세스가 약 3,809MiB 사용 |
| Driver | 580.173.02 |
| CUDA toolkit | nvcc 12.8.93; nvidia-smi의 CUDA 13.0은 driver 지원값 |
| `/` | 3.6TiB, available 528GiB, 85% 사용 |
| `/ssd` | 938GiB, available 891GiB; 현재 계정 쓰기 불가 |
| 기존 Conda | `/home/colin/miniconda3`; envs 231GiB, package cache 24GiB |
| 기존 VIGS env | `/home/colin/miniconda3/envs/vigs-slam-5090`, 약 15GiB |

확인한 VIGS data 경로에는 Aria 계열만 있었다. 전체 디스크의 모든 위치를 검색한 결과는 아니므로 다른 위치의 중복 데이터 유무는 다운로드 직전 manifest로 재확인한다. 기존 VIGS 환경이 있다는 사실은 upstream 무수정 재현성을 보장하지 않는다.

## 2. 데이터 다운로드 가능 여부

ETH 파일 6개 모두 비인증 HTTP HEAD 200, Content-Type application/zip, Accept-Ranges bytes였다. 이는 URL 접근·명시 크기를 확인한 것이며, 전체 전송 성공·압축 무결성·실제 다운로드 속도를 검증한 것은 아니다. archive 내부 목록이나 payload는 읽지 않았다.

| 데이터 | 파일 | 정확한 bytes | GiB | 용도 |
|---|---|---:|---:|---|
| RPNG AR Table | rpngar.zip | 27,989,564,533 | 26.07 | 실내 RGB+IMU, 주 비교 |
| UTMM 전처리본 | UTMM_Dataset.zip | 22,158,268,512 | 20.64 | 실내 RGB+IMU, 주 비교 |
| VIGS 자체 데이터 | VIGS-SLAM.zip | 25,124,588,140 | 23.40 | 어려운 궤적·강건성 확장 |
| EuRoC 전처리본 | euroc.zip | 20,478,097,911 | 19.07 | grayscale+IMU, tracking 확장 |
| FAST-LIVO2 전처리본 | fast-livo2-dataset.zip | 12,597,641,120 | 11.73 | 저주파 RGB+IMU, 확장 |
| RPNG demo | demo.zip | 749,851,667 | 0.70 | 설치 smoke run; 최종 benchmark 대체 아님 |

세 주요 데이터 합계 **70.10GiB**, 전체 5종은 **100.91GiB**. 출처: [ETH 공개 인덱스](https://cvg-data.inf.ethz.ch/vigs-slam/). 원격 README는 자체 데이터 외 archive가 재현 편의를 위한 전처리본임을 명시한다: [DATASET_INFO](https://cvg-data.inf.ethz.ch/vigs-slam/DATASET_INFO.md).

### RPNG 원본과 전처리본

[원본 저장소](https://github.com/rpng/ar_table_dataset)는 RGB 30Hz, IMU 400Hz, Optitrack 기반 trajectory GT, calibration을 제공한다. RGB에 정렬된 depth도 있으나 원 저자는 untested로 표시한다. 따라서 depth를 정밀 geometry GT로 바로 채택하지 않는다.

8개 원본 bag의 표기 용량 합은 76.94GB. Google Drive에 raw/compressed 링크가 있으며, 이번 환경에서는 Drive 다운로드 링크의 실제 file endpoint 검증이 완료되지 않았다. 반면 ETH 전처리본은 HEAD 200을 확인했다. 논문 재현 첫 단계에서는 ETH본 하나만 받고 원본 bag은 필요한 채널 누락이나 전처리 검증이 있을 때 추가한다.

### UT-MM 원본과 전처리본

[Hugging Face 원본](https://huggingface.co/datasets/neel1302/UT-MM)은 `UTMM_Dataset.zip` 6,752,470,196 bytes = **6.29GiB** 하나를 제공한다. 공개 API와 파일 HEAD 200 확인; HF LFS SHA256은 `b11fd4356ed2020f57beb832b432db3184005159e79b3fddc7f9bcd8d8229164`.

ETH본과 파일 이름은 같지만 크기는 다르다. ETH는 전처리본임이 명시돼 있으나, 정확한 이미지 인코딩·채널·시퀀스 trimming 차이는 압축 내부 미열람으로 미확인이다. 같은 파일로 취급하거나 같은 경로에 덮어쓰면 안 된다.

원본은 RGB/depth/IMU/LiDAR/pose topic을 갖는다. VIGS 재현에는 우선 ETH본, MM3DGS의 원래 다중센서 조건을 실행할 때 원본 bag을 검토한다. 원본 변환 문서는 ROS 의존성을 안내한다. host Ubuntu에 ROS를 바로 추가하기보다 변환 도구 전용 환경/컨테이너로 분리하는 것이 좋다.

### 라이선스

VIGS 자체 데이터는 [CC BY 4.0](https://cvg-data.inf.ethz.ch/vigs-slam/LICENSE). ETH의 타 데이터 전처리본에는 원본 데이터의 조건이 적용된다. UT-MM card는 `license: cc`로만 적혀 있어 정확한 CC 변형이 불명확하다. RPNG는 credit/citation 안내를 제공한다. 재현용 내부 사용과 별개로 데이터 재배포 계획이 생기면 원본 조건을 추가 확인한다.

## 3. 비교 저장소와 설치 예상

다음 revision은 GitHub API로 확인한 조사 시점 main SHA이며 논문 제출 당시 commit이라고 단정하지 않는다. GitHub size는 저장소 메타데이터로, submodule·weight·build·환경을 포함한 설치 크기가 아니다.

| 후보 | 입력/역할 | 공개 환경과 설치 판단 | SHA (축약) |
|---|---|---|---|
| [VIGS-SLAM](https://github.com/cvg/VIGS-SLAM) | RGB+IMU, 필수 upstream baseline | 5090용 PyTorch 2.8/cu128 경로와 Docker 제공. 준비 난도 상대적으로 낮음 | 22ffe24c6df8 |
| [HI-SLAM2](https://github.com/Willyzw/HI-SLAM2) | RGB, 핵심 visual GS 비교 | environment.yaml: torch 2.1.2/CUDA11.8. 5090용 재빌드·호환 패치 필요 예상 | 76c833c7d8ed |
| [Splat-SLAM](https://github.com/google-research/Splat-SLAM) | RGB, 핵심 visual GS 비교 | README CUDA11.7/11.8; custom kernels·torch-scatter. archived 상태지만 공개 접근 가능 | 16b0667a44a3 |
| [VINGS-Mono](https://github.com/Fudan-MAGIC-Lab/VINGS-Mono) | RGB+IMU, 같은 센서 계열 비교 | Python3.9.19/torch2.0.1/cu118, GTSAM vio·DBAF·surfel rasterizer. 가장 큰 이식 작업 예상 | 8edb1dc6f82c |
| [MM3DGS-SLAM](https://github.com/VITA-Group/MM3DGS-SLAM) | RGB+depth+IMU 등 다중센서 별도 비교 | YAML torch1.12.1/CUDA11.6, README toolkit11.8. UTMM config 있음. 초기 핵심 4 baseline 이후 | 1fae9f5d1ad5 |

모든 저장소의 공개 GitHub API 접근은 200이었다. recursive clone·submodule checkout·컴파일은 아직 검증하지 않았다. GitHub metadata size는 순서대로 25,853 / 62,392 / 1,482 / 757 / 562,493KiB. 라이선스 감지값은 Apache-2.0 / BSD-3-Clause / Apache-2.0 / 미표기 / NOASSERTION이었다. 각 submodule의 라이선스는 별도다.

구체적인 준비 이슈:

- VIGS upstream `environment_5090.yaml`에는 torch2.8+cu128 외에 CUDA13.2 conda 라이브러리 및 pip CUDA12.9 계열 항목도 섞여 있다. README만 믿고 export 전체를 복제하기보다 실제 필요한 의존성을 추려 독립 환경에 lock하고 solver/ABI 검증한다. 최신 torch로 무조건 올릴 필요는 없다.
- HI-SLAM2/VIGS 공통 Omnidata checkpoint 2개는 각각 약 1.947GB, 합계 약 **3.63GiB**. Zenodo HEAD 200 확인. 동일 SHA의 weight만 공유하고 TensorRT engine은 GPU/runtime/shape별로 분리한다.
- VINGS `set_env.sh`는 env를 생성하지만 activate 명령이 없고, DBAF 설치에 `sudo python setup.py install`을 사용한다. 원문 스크립트 통째 실행을 피하고 명시적 env interpreter로 각 단계를 분리한다. `triton==2.0.0`, mmcv1.7.2 등도 새 torch와 정합성 검토가 필요하다.
- VINGS README의 metric-depth checkpoint 예시에 `blob/main` 링크가 있다. 실제 설치 시 `resolve/main` 파일 endpoint를 사용하고 checksum을 확인해야 한다.
- Splat-SLAM은 최종 BA 전 평가 옵션이 있지만 일반 종료 경로에 final refinement도 있다. VIGS 역시 demo가 pre-final PLY와 beforeBA trajectory를 저장한 뒤 terminate에서 final BA/refinement를 수행한다. online artifact 선택과 online runtime 계측을 분리해야 한다.

[PyTorch Blackwell 지원 안내](https://pytorch.org/blog/pytorch-2-7/)에 근거해 5090 기본 후보는 torch2.8/cu128로 둔다. 오래된 CUDA11 환경을 Docker 안에 넣는 것만으로 GPU 아키텍처 문제가 해결되지는 않는다. 이식 성공 여부는 설치 이후에만 판정할 수 있다.

## 4. 평가 계약: 원문 확인과 제안 구분

[VIGS-SLAM v2](https://arxiv.org/html/2512.02293v2)의 online 정의는 final BA/color refinement 이전이다. 렌더 평가는 모든 비교 방법의 mapping 사용 뷰를 제외한다. VINGS 비교는 metric depth/loop closure를 끈 수정본이며, MM3DGS는 공개 pure-VI 지원 제약으로 문헌 tracking 수치를 사용한다. 따라서 공개 기본 설정과 논문 수치가 자동으로 일치하지 않는다.

아래는 우리 benchmark 설계 제안이다.

| 항목 | 고정할 내용 |
|---|---|
| 입력 | RGB / RGB+IMU / RGB-D+IMU를 표에 별도 표기. GT pose/depth의 학습 유입 금지 |
| online checkpoint | 마지막 입력 처리와 정상 online queue 종료 경계, pre-final map/trajectory, tail update 수 기록 |
| rendering | 공통 evaluation frame ID, resolution, crop, invalid mask, exposure, LPIPS 구현, 평가 camera pose 출처 |
| tracking | ATE RMSE, recall, 실패 여부; trajectory association 및 Sim(3)/SE(3) alignment 명시 |
| runtime | tracking+mapping 전체 FPS/RTF와 peak VRAM/RAM, 입력 지속시간, tail wall time; 순수 renderer FPS와 구분 |
| 통계 | scene별 수치 및 scene 평균, 독립 seed 3회 권장. 실패 장면을 평균에서 조용히 제외하지 않음 |
| scheduler 논문용 | overall PSNR 외 lower quartile/late-bin/anytime, Gaussian 수, 완료 optimizer update 수 |

공식 `eval_rpng_mono.py`는 `evo_ape tum -vas`를 써 scale alignment를 수행하고 scale error도 산출한다. `ape_se3`라는 파일명만 보고 SE(3) 정렬로 오인하면 안 된다: [upstream evaluator](https://github.com/cvg/VIGS-SLAM/blob/22ffe24c6df81d0bf63bd20057565c00c51d2996/eval_rpng_mono.py).

논문 재현 평가와 strict wall-clock 평가를 각각 protocol ID로 구분한다. final refinement 배제만으로 기존 프로젝트의 fixed1.5×/sensor-EOS-zero-tail을 만족했다고 주장하지 않는다.

공통 held-out는 mapping 사용 frame의 합집합을 제외해야 한다. 우리 dense mapper까지 포함하면 남는 frame이 적을 수 있다. 따라서 (a) 원문 방식 재현에는 실제 사용 뷰 manifest를 모으고, (b) 우리 방법 비교에는 미리 공통 reserved split을 정해 모든 mapper에서 제외하는 별도 실험을 제안한다. 기존 llffhold-8은 (b)의 후보이며 원문 split과 같다는 뜻은 아니다. 평가 frame의 tracking 사용 허용 여부도 별도 명시한다.

Floater/geometry는 PSNR만으로 판정하지 않는다. Aria의 기존 region GT를 새 장면에 그대로 옮길 수 없다. 새 장면의 검증된 GT depth/mesh/region label 가용성을 먼저 확인하며, 이번 metadata 조사만으로 이 세 데이터셋의 완전한 surface GT를 확보했다고 주장하지 않는다.

## 5. 저장·환경 관리안

제안 경로이며 아직 생성하지 않았다.

```text
/ssd/gs_slam_benchmark/
  repos/{vigs-upstream,hislam2,splat-slam,vings-mono,mm3dgs}/
  datasets/
    rpng/{raw,prepared/eth-20260315}/
    utmm/{raw/hf-<revision>,prepared/eth-20251202}/
    vigs/{raw,prepared/eth-20260314}/
    manifests/
  weights/<model>/<sha256>/
  envs/{vigs,hislam2,splat,vings,eval}/
  cache/{conda-pkgs,pip,huggingface,torch}/
  build/<method>/<env-id>/
  runs/<protocol>/<method>/<commit>/<dataset>/<sequence>/<seed>/
```

실험 설정·adapter·patch·provenance는 워크스페이스 `benchmarks/online_gs/` 같은 작은 관리 디렉터리에 두고, 대용량 데이터와 결과만 위 경로를 참조하도록 제안한다. 기존 `repos/main/VIGS-SLAM` 링크의 대상을 변경하지 않는다.

- 원본/전처리본 각각 한 벌만 유지하고 각 repo의 기대 `data/` 경로에서 symlink 또는 read-only bind mount한다.
- dataset manifest: URL, revision/Last-Modified, bytes, 다운로드 후 SHA256, sequence/frame/timestamp/calibration, conversion command·commit, evaluation split hash.
- repo manifest: origin, 정확한 SHA, recursive submodule SHA, compatibility patch hash. 우리 알고리즘 변경과 baseline 호환 변경을 구분한다.
- method별 독립 Conda prefix. 사용자 base나 기존 연구 env를 수정하지 않는다. 평가 env도 별도로 잠근다.
- `CONDA_PKGS_DIRS`, `PIP_CACHE_DIR`, `HF_HOME`, `TORCH_HOME`, `TORCH_EXTENSIONS_DIR`는 benchmark 경로로 지정한다. CUDA extension build/cache는 method·torch·CUDA·GPU별로 분리한다.
- CUDA toolkit와 GPU driver는 host 것을 기준으로 명시한다. Docker를 사용하면 method별 image digest와 bind mount를 고정하고, image layer의 중복도 용량에 포함한다.
- env lock/spec와 `pip freeze`, compiler version, exact run command를 결과에 저장한다. weight는 같은 hash만 공유한다.
- 반복 run은 metrics/trajectory/pre-final PLY/log를 기본 보관하고 전 프레임 render·영상·중간 checkpoint는 대표 run만 보관하는 정책을 제안한다. 기존 파일 삭제는 하지 않는다.

## 6. 공간 계획과 실행 순서

압축 내부를 읽지 않았으므로 해제 크기는 미확인이다. 다음은 구매/확보를 위한 계획 범위다.

| 범위 | 예약 용량 추정 |
|---|---:|
| 우선 RPNG+UTMM: 압축 46.70GiB + 해제본 + 2~3 method env/build + 제한된 결과 | 250~350GiB |
| 주요 3종 + 핵심 4 baseline + 우리 방법, 반복 결과 제한 보관 | 400~600GiB |
| 전체 5종 + 대량 render/checkpoint/여러 seed | 600GiB 이상 가능 |

루트 528GiB에서 작은 pilot은 가능하나 반복 연구 전체를 넣기에는 여유가 작다. `/ssd` 891GiB에 전용 공간을 준비하고 150GiB 정도 여유를 남기는 운영을 제안한다. archive 검증 후 삭제 여부는 추후 결정하며, 위 추정은 원본 archive도 보유하는 방향이다.

준비 순서:

1. 평가 protocol·공통 split·우선 scene 목록 및 artifact 보존 정책 고정.
2. 전용 저장 위치 권한 준비. 작은 repo 및 환경부터 고정.
3. VIGS upstream의 별도 env와 pre-final export/evaluator 검증.
4. RPNG/UTMM 전처리본 확보·checksum·manifest·adapter 검증. 최초 실행은 scene별 한 개.
5. HI-SLAM2, Splat-SLAM, VINGS 순으로 5090 호환 작업 및 동일 evaluator 연결.
6. main paired 실험 후 VIGS 자체 데이터, 필요시 EuRoC/FAST-LIVO2로 확대.

현재 미확인: 압축 해제 실제 크기, 장기 다운로드 대역폭/무결성, Google Drive 원본 endpoint, 모든 submodule 접근과 빌드, VINGS 원문 수정본과 upstream의 정확한 대응, 전처리본의 geometry GT 채널과 평가 frame 세부 규칙. 이 항목들은 설치/다운로드 완료로 간주하지 않는다.
