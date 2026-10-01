# 5070 Ti 실험 재개 가이드

2026-10-01 인계. 사용자의 요청으로 기존 GPU queue와 실행 중인 worker를 중단했다.
**새 컴퓨터 설치와 CUDA 재빌드는 그 컴퓨터의 에이전트가 이어서 진행한다.**
현재 production mapper는 유지하고 아래의 시간 제한 없는 측정부터 수행한다.

## 현재 완료 상태

| 작업 | 상태 |
|---|---|
| 20 scenes × 15/40 renders/KF × D3/vanilla | 80/80 완료 |
| 위 80 runs의 중간 map checkpoint 평가 | 80/80 완료 |
| RR/ERVS · dense/KF-RGB · native geometry 대조 | 19/140 완료, 나머지 미완료 |
| shared tracking FIFO live panel | 8개 pilot만 완료, 나머지 보류 |
| clean D3 zero-weight 대조 / 실제 teaser capture | 미시작 |
| original 3dgs-custom 15/30/60 sampler | 이전 실측 PSNR 요약 회수, 새 재현 미완료 |

`state.json`에 완료·중단 기록을 보존했다. 중단된
`current_controls_v1/render40/rpng/table_03/rr_kf_rgb`는 완료로 취급하지 않는다.
이 output과 log를 삭제하거나 덮어쓰지 말고 재시도는 새 namespace에서 진행한다.

## 1. 두 저장소 확보

```bash
git clone https://github.com/sawo0150/gs_floaterLab.git
git clone https://github.com/sawo0150/VIGS-SLAM-custom.git
```

gs_floaterLab의 `context/STATUS.md`, 이 문서와 `state.json`을 읽는다.
현재 코드·recipe를 먼저 고정하고 양쪽 `git rev-parse HEAD`를 실행 기록에 남긴다.
논문의 이전 주장과 최신 D3 구현은 동일하지 않으므로 논문 이름만으로 loss를 켜지 않는다.

## 2. Git 외부 입력 전송

**clone만으로 학습이 시작되지는 않는다.** 원본 RGB·IMU·calibration, frozen causal
tracker archive, native setup, CUDA source/binary와 기존 raw 결과는 Git에 없다.
이 폴더의 `scene_inventory.json`에 전체20 scenes의 정확한 입력 경로와 manifest
SHA256이 있다. `transfer_inputs_all.txt`는 모든 입력,
`transfer_inputs_pilot.txt`는 Aria1253/table_06/square-1 세 장면만 포함한다.
`transfer_runtime.txt`는 코드 외의 환경·rasterizer·reference 결과 경로다.
목록은 기존 서버의 절대경로에서 첫 `/`를 뺀 rsync files-from 형식이다.

기존 경로를 유지하는 이식 예시(새 컴퓨터에서 실행; `<OLD_HOST>`와 목적지 root 수정):

```bash
rsync -arL --info=progress2 --files-from=transfer_inputs_pilot.txt <OLD_HOST>:/ /path/to/transfer-root/
rsync -arL --info=progress2 --files-from=transfer_runtime.txt <OLD_HOST>:/ /path/to/transfer-root/
```

`-L`은 기존 서버의 symlink 대상도 함께 복사한다. 전송은 학습 GPU를 점유하지 않는다.
Runtime 목록에는 큰 환경과 기존 결과가 있어 전송량을 확인한 뒤 필요한 장면부터
축소해도 된다. 기존 `/home/intern`·`/home/colin` 경로를 새 컴퓨터에서 그대로
확보하거나, process-local path adapter와 별도 machine profile을 만든다.
원래 source lock/manifest는 보존하고 새 경로·재빌드 binary SHA를 새 provenance에 남긴다.

환경 기준은 Python3.11, CUDA12.8 계열 Blackwell 지원 PyTorch다.
실측 package 버전은 `environment_snapshot.json`에 보존했다.
`VIGS-SLAM-custom/environment_5090.yaml`과 geometry_merge의 빌드 도구를 참고한다.
현재 바이너리를 그대로 쓸 수 있는지는 새 컴퓨터에서 import/CUDA smoke로 확인해야 한다.
단순히 GPU 이름이 다르다는 이유로 sampling/학습량/해상도를 변경하지 않는다.
16GB VRAM 때문에 OOM이 발생하면 원인을 기록하고 checkpoint/평가 capture 크기부터
검토한다. 학습 정책을 조용히 바꾸지 않는다.

중요 경로:

- `VIGS-SLAM-custom/scripts/selected_mapping/source_lock.json`: 기존 sources/extensions lock
- `results/campaigns/gain_attribution/geometry_main_validation/raster_fixed`: 패치된 rasterizer
- lock의 `extensions`: current CUDA stream을 사용하는 VIGS/LieTorch build
- `VIGS-SLAM-official-exp78`: 공식 vanilla `22ffe24c6df81d0bf63bd20057565c00c51d2996`
- `VIGS-SLAM-paper-full`, `VIGS-SLAM-visible-lazy-carve/thirdparty`: legacy helper의 import 의존성

Rasterizer 재빌드 시 depth-backward recursion guard와 warp backward 패치를 보존한다.
`geometry_merge/port_raster_fixes.py`는 이미 패치된 source에 중복 적용하지 않는다.
원본 CUDA source도 runtime 전송 목록의 raster_fixed 폴더에 있다.

## 3. 먼저 실행할 실험

순서: **3-scene fixed-work smoke → 미완료 RR/ERVS·dense 대조 → 그 대조의 checkpoint
수렴 평가 → geometry 대조 → original sampler 재현**.
실제 센서 1×/1.5× FIFO, tracking capacity 및 동일시간 비교는 뒤로 미룬다.

현재 recipe: seed0, quotas3:3:6, 영상별 Adam, cumulative ERVS,
κ16, τ₀4(pool entropy weight4/N), init sampling divisor×0.8,
opacity0.1/300renders/최근10birth 보호, densify OFF, blur filter OFF.
Fixed-work에서는 실제 완료한 training renders/KF를 15/40으로 통제한다.
D3 proxy renders를 별도 계측하며 동일 총 계산량이라고 주장하지 않는다.
Frozen tracker의 causal pose/depth를 재생하므로 tracking 동시 실행 결과가 아니다.

아래는 **경로·환경 이식과 source 검증 이후** 사용할 기존 CLI다.
기존 서버 경로를 유지했을 때의 예시이며 새 설치가 이미 검증됐다는 뜻은 아니다.

```bash
cd /home/intern/gs_floaterLab
MIGRATION_PYTHON=/home/colin/miniconda3/envs/vigs-slam-5090/bin/python
nvidia-smi
"$MIGRATION_PYTHON" benchmarks/online_gs/campaigns/gain_attribution/run_cvpr_measurements.py \
  --output results/campaigns/gain_attribution/cvpr_assets/rtx5070ti_fixed_pilot_v1 \
  --scenes aria1253 table_06 square-1 --budgets 15 40 --arms d3 vanilla --snapshots
```

기존 setup을 옮겼다면 새 output의 `inputs/<dataset>/<scene>/setup`에 byte-identical하게
복사해 capture를 다시 수행하지 않아도 된다. 새 setup capture를 실행할 경우 pretrained
model 등 tracker 초기화 의존성도 필요하다.

현재 control CLI:

```bash
"$MIGRATION_PYTHON" benchmarks/online_gs/campaigns/gain_attribution/run_cvpr_ablations.py \
  --output results/campaigns/gain_attribution/cvpr_assets/rtx5070ti_controls_v1 \
  --scenes aria1253 table_06 square-1 --budgets 15 40 \
  --cases rr_dense ervs_kf_rgb rr_kf_rgb native_geometry --snapshots
```

**주의할 코드 의존성:** control runner의 reference는 현재 `fixed_work_v1`과
`fixed_work_12f_v1`에 고정돼 있다. 기존 reference를 전송하거나 새5070Ti reference
namespace를 가리키는 runner/path adapter를 만들고 진행한다. 기존 reference로 검사해도
고정 렌더/trajectory/cohort 비교는 가능하지만 5090과5070의 시간은 합산 비교하지 않는다.
가능하면 새5070에서 양쪽 arm을 다시 실행한 reference를 사용한다.

모든 candidate를 돌릴 때는 `--scenes`를 생략한다. 시작부터 전체를 재실행하지 말고
`completed_controls.json`의 19개와 미완료를 확인한다. 기존 runner는 summary에 들어간
실패도 자동 skip할 수 있으므로 실패 재시도는 새 output namespace를 사용한다.
중간 checkpoint 평가 명령은 `evaluate_cvpr_checkpoints.py --help`를 확인한다.
Original T4 15/30/60은 현재 online15/40 sampler와 다른 실험이며 아카이브 요약을
새 GPU 재현으로 표시하지 않는다.

## 4. 완료 판정과 기록

`render_result.json`의 valid_execution·checks, 동일 prefix training render 수,
동일 trajectory·held-out cohort, zero-tail 및 saved-map double evaluation을 확인한다.
완주나 train PSNR만으로 성공 판정하지 않는다. 5070Ti hardware·driver·PyTorch/CUDA·
binary SHA·source commit을 각 결과에 기록한다. scene별 절대 phase cutoff는 추가하지 않는다.
결과 card, INDEX 한 줄, STATUS 최근 흐름의 새 항목을 함께 기록한다.

Paper 자산은 `paper/figures`, `paper/tables`, `paper/scripts`에 있다. teaser/overview만
전체 너비다. 일부 figure/표는 아직 dummy/미완료 상태이며 기존 provenance를 유지한다.
Git에는 코드·문서·현재 자산·가벼운 측정 CSV를 올리고 raw map/환경/데이터는 별도로 전송한다.
