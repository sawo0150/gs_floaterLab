# 5070ti_vanilla_matched_time — unified-pool custom comparison

날짜: 2026-09-14
상태: **하네스 구축 및 대표 장면 RR/ERCB pair 실행 중**

## 목적

원본 VIGS의
[`benchmark_vanila/5070ti_1.5x_streaming`](../../benchmark_vanila/5070ti_1.5x_streaming/README.md)
결과가 실제로 사용한 online map 완료 wall-clock을 custom의 입력 replay
deadline으로 그대로 옮긴다. 이 표는 strict 1.5x 성과가 아니라 **동일 시간 예산에서
mapping 구조와 selector의 품질·수렴 효율을 비교하는 보조 실험**이다.

## 예산 정의

각 장면의 배수는 수동으로 정하지 않고 vanilla evidence에서 계산한다.

```text
matched_elapsed = 1.5 * source_duration + vanilla_mapping_lateness
matched_scale   = matched_elapsed / source_duration
```

평가, PLY 저장, metric 계산 시간은 포함하지 않는다. vanilla의 map drain은 원 실행이
실제로 품질에 사용한 시간이므로 matched elapsed에는 포함한다. custom은 같은 총시간을
마지막 RGB timestamp까지 균일하게 펼쳐 replay하며, final capture deadline 뒤에는
optimizer/topology update를 허용하지 않는다. 따라서 terminal polish는 없다.

## 비교 계약

- GPU: RTX 5070 Ti
- 입력: timestamp 순 RGB+IMU, MPS/post-hoc pose/depth 없음
- 범위: vanilla timing evidence가 있는 UTMM 8 + RPNG 8 장면
- mapping: 하나의 arrived KF+dense pool, 하나의 optimizer loop
- update 단위: render 1 + backward 1 + `Adam.step()` 1인 물리 B1
- KF action: RGBD+normal, full Gaussian parameter, native topology
- dense action: RGB, appearance+opacity only
- selector: 같은 pool/optimizer에서 `rr` 또는 ERCB 계열만 교체
- 금지: background polish, terminal replay, topology freeze, 절대 frame/iteration phase cutoff
- 평가: vanilla와 custom 양쪽에서 keyframe이 아닌 동일 UID 교집합의 PSNR/SSIM/LPIPS
- 별도 audit: 입력/track deadline, zero-tail, physical Adam step, KF/dense service

Aria는 기존 `5070ti_1.5x_streaming`에 대응하는 full-preservation timing evidence가
없으므로 임의 배수를 만들지 않는다. Aria matched-time은 vanilla timing을 먼저 얻은
뒤 같은 생성기로 추가한다.

## 파일

- `build_budget_manifest.py`: vanilla evidence → 장면별 예산 JSON/CSV
- `evidence/budget_manifest.{json,csv}`: 고정된 입력 예산
- `config/`: family별 upstream recipe + parallel queue overlay
- `run_one.sh FAMILY SCENE SELECTOR [OUTPUT]`: 단일 custom run
- `run_panel.sh`: 대표 4-scene RR/ERCB resume-safe queue
- `run_admission_panel.sh`: RR/ERCB를 고정하고 unified work-credit
  admission(`required_opportunities=4`)을 비교하는 대표 2-scene queue
- `collect_metrics.py`: 동일 UID 품질, deadline, 실제 B1 step 집계
- `summary.md`: 실행 중 자동 갱신되는 결과표
