# 동료 연구자용 실행 안내 — 확정 mapping 설정

**2026-09-29 인계본.** 실행 설정의 단일 기준은
[selected_mapping_recipe.json](../../../../../benchmarks/online_gs/campaigns/gain_attribution/selected_mapping_recipe.json)이다.
실행은 [run_selected_mapping.py](../../../../../benchmarks/online_gs/campaigns/gain_attribution/run_selected_mapping.py)만 사용한다.
이 문서의 설정은 2026-09-28에 채택한 **3:3:6 / 40 renders/KF / init1.25배 /
보호 opacity pruning**이다. 다른 실험 runner의 기본값이나 논문의 예전 설명을
조합해서 실행하지 않는다.

이 인계본은 **현재 5090 서버에서 세 장면을 재현하는 fixed-work mapper replay**다.
Online tracker가 당시 추정한 causal packet을 재생한다. Tracker 동시 실행,
실시간 deadline 달성, 다른 서버로의 독립 설치까지 검증한 release는 아니다.
코드와 설정은 Git에 포함하지만 데이터·tracker archive·CUDA binary·conda 환경은
서버에 있는 외부 의존성이다.

## 1. 확정 설정

| 항목 | 채택값 / 의미 |
|---|---|
| 예산 | 지도 세대 내 KF admission마다 40 training camera renders; 마지막 입력 뒤 추가 학습 없음 |
| Worker 입력 | Arrival당 하나의 unified mapping packet |
| 영상 선택 묶음 | 최대 12장, **최근 KF 3 / 전체 KF 3 / admitted dense 6** |
| Optimizer | **영상당 Adam 1회**. 12장 선택 묶음이 Adam 1회를 뜻하지 않음 |
| 최근 KF | 현재 window에서 무작위 선택 |
| 전체 KF / dense | 각각 full-history pool에서 ERVS, 묶음 내 중복 방지 |
| 선택 횟수 | 누적 횟수; window 선택도 포함. 최근 구간 횟수 아님 |
| Growth | κ=16, `dense_only` admission-capacity 정책 |
| Entropy | τ₀=4, 각 pool 크기 N에 대해 실제 weight=4/N |
| KF loss | Window와 전체 KF 모두 RGB-D/normal loss |
| Dense loss | RGB-only; 도착한 영상과 causal pose 사용 |
| 초기화 | PPM/Sobel, causal online-rank mean=2.5 / span=2.0 |
| 생성량 | 공통 downsample multiplier=0.8; init=51.2 / regular=204.8, 기존 64/256 대비 약 1.25배 |
| Pruning | Opacity <0.1인 오래된 Gaussian만 제거 |
| Pruning 주기 | 완료된 training render 300회 단위, packet 경계로 지연; 마지막 별도 정리 없음 |
| 보호 | 최근 **10개 nonempty KF birth batch**, stable point ID 기준 |
| Scale projection | ON, 기존 최대 scale=0.1 유지 |
| Densify / split / clone | OFF |
| Carve / blur filter / size prune / KF cap | OFF |
| Seed | 0 |

`--disable-densify-prune`는 기존 통합 topology 경로를 끄는 옵션이다.
채택 설정에서는 `--protected-opacity-prune`가 별도 보호 pruning만 켠다.
두 옵션이 함께 있다고 pruning 전체가 꺼진 것은 아니다.

Bootstrap 때 pool이 작거나 packet의 남은 예산이 12보다 작으면 실제 비율은
3:3:6과 조금 다를 수 있다. 예산을 채우기 위해 선택 묶음을 반복하지만 Adam은
계속 영상별로 실행한다. 지도 reset 시 pool과 count도 새 generation으로 시작한다.

## 2. 처리 흐름과 full-history의 의미

1. Timestamp 순으로 RGB·IMU 및 해당 시점까지 추정한 pose/depth를 받는다.
2. 새 KF의 관측으로 Gaussian을 생성한다. PPM 생성량만 공통 0.8 배율로 조정한다.
3. Growth 정책이 도착한 dense 후보의 training-set admission을 허용한다.
4. 최근 KF / 전체 KF / dense에서 3:3:6으로 선택하고 각 영상을 한 번씩 학습한다.
5. 실제 완료한 영상 선택을 누적 count에 반영한다. 예산 내에서 반복한다.
6. Pruning 시점이 되었으면 packet 경계에서 보호 대상 외의 낮은 opacity 점을 제거한다.

과거 KF와 admitted dense는 window 밖으로 나갔다는 이유로 pool에서 제거하지 않는다.
최근 KF quota는 새 지도 영역에 즉시 학습량을 배정하는 장치이며, pool 보관 범위와
별개다. 전체 KF pool에도 최근 KF가 포함된다. 모든 입력 영상을 즉시 학습하거나,
모든 영상을 하나의 ERVS 분포에서 뽑는 구조는 아니다.

최근 영상의 누적 사용 횟수가 높더라도 새로 생성된 Gaussian의 학습량은 부족할 수
있다는 것이 window 몫을 유지하는 설계 근거다. 이 인과 설명 자체를 geometry GT로
입증한 것은 아니다.

## 3. 같은 서버에서 실행하기

아래 명령은 `/home/intern/gs_floaterLab` 기준이다. Output은 **존재하지 않는 새 경로**를
사용한다. GPU에 다른 compute process가 있으면 launcher가 중단한다. 타 작업을
종료하지 말고 비워진 뒤 다시 실행한다.

먼저 GPU를 사용하지 않는 의존성 검사를 실행한다.

```bash
cd /home/intern/gs_floaterLab
/home/colin/miniconda3/envs/vigs-slam-5090/bin/python \
  benchmarks/online_gs/campaigns/gain_attribution/run_selected_mapping.py \
  --dataset aria \
  --output results/campaigns/gain_attribution/selected_reproduction/aria_run1 \
  --check-only
```

`Preflight PASS` 이후 실제 mapping과 held-out 평가를 실행한다.

```bash
/home/colin/miniconda3/envs/vigs-slam-5090/bin/python \
  benchmarks/online_gs/campaigns/gain_attribution/run_selected_mapping.py \
  --dataset aria \
  --output results/campaigns/gain_attribution/selected_reproduction/aria_run1 \
  --evaluate
```

RPNG는 `--dataset rpng`, UTMM은 `--dataset utmm`으로 바꾸고 output도 각각
`rpng_run1`, `utmm_run1`로 지정한다. **한 번에 한 장면씩** 실행한다. 선택되는 장면은
Aria1253 / RPNG table_06 / UTMM square-1이며 scene별 설정 튜닝은 없다.

`--print-command`는 실행 예정 argv만 보여준다. 의존성 검사까지 하려면
`--check-only`를 사용한다. `--evaluate`를 생략하면 mapping과 지도 저장만 수행한다.
평가는 저장된 지도에 대한 두 번의 독립 렌더링이며 optimizer update를 추가하지 않는다.

## 4. 버전·입력 고정 및 다른 서버로 옮길 때

[source_lock.json](../../../../../benchmarks/online_gs/campaigns/gain_attribution/selected_release/source_lock.json)에
확정 source checksum, scene별 setup·manifest·calibration·IMU checksum과 CUDA binary
checksum을 기록했다. Launcher는 실행 전에 이를 확인한다. 불일치를 우회해 다른
설정을 채택 결과로 실행하지 않는다.

- Backend: `/home/intern/VIGS-SLAM-online-worker-integration`
- Backend base commit: `5db67dd59f59752e9ae5ecd9fc0cebb547626c12`
- 그 commit 위의 미커밋 sampler 변경분은
  [backend.patch](../../../../../benchmarks/online_gs/campaigns/gain_attribution/selected_release/backend.patch)에 보존했다.
  RR 지원 코드도 들어 있지만 **채택 recipe는 ERVS만 사용**한다.
- 이 서버의 backend에는 patch가 이미 반영되어 있으므로 다시 적용하지 않는다.
  별도 clean checkout을 준비할 때만 해당 base commit에서 `git apply --check`로
  확인한 뒤 적용한다. 현재 dirty backend를 reset하지 않는다.
- Python: `/home/colin/miniconda3/envs/vigs-slam-5090/bin/python`
- Setup과 extension 경로는 lock의 `datasets` 및 `extensions` 항목에 있다.
  `native_setup.pt`는 **신뢰할 수 있는 프로젝트 산출물만** 사용한다.
- Frozen tracker archive와 원본 RGB는 Git에 포함되지 않는다. Lock의 입력 경로,
  archive manifest가 참조하는 packet/state/trajectory 파일, RGB 및 IMU를 함께
  확보해야 한다. 사전 검사는 원본 RGB 전체의 내용 checksum까지 검사하지 않는다.

다른 서버에서는 이 commit만 clone해서 바로 실행되지는 않는다. 경로와 native
extension의 ABI를 함께 이식해야 하며, 현재 launcher는 검증된 같은 서버 경로를
엄격히 사용한다. CUDA binary를 다른 빌드로 바꾼 결과는 별도 재현 실험으로 기록한다.

## 5. 결과 확인

| 출력 | 확인할 내용 |
|---|---|
| `selected_recipe.json` | 이번 실행에 사용한 확정 recipe 복사본 |
| `selected_command.json`, `selected_source_lock.json` | 실행 명령 및 release 의존성 |
| `render_result.json` | `valid_execution`, `checks`, `render_counts`, `main_optimizer_steps`, `training`, `densify_prune_ablation` |
| `birth_sampling.csv` | 실제 KF별 Gaussian 생성 기록 |
| `3dgs_before_final.ply`, `final_map_state.pt` | 최종 지도 |
| `evaluation_consistency.json` | 두 평가의 `pass`와 `fixed_psnr_first` |
| `psnr/strict_fixed_manifest/final_result.json` | 고정 held-out 상세 평가 |

완주는 품질 성공의 근거가 아니다. `valid_execution` 및 평가 `pass`를 확인한 뒤
**fixed held-out PSNR**을 비교한다. Train PSNR로 floater 감소를 판정하지 않는다.
실험을 마치면 결과 카드·INDEX·STATUS 최근 흐름에 실행 경로와 차이를 기록한다.

## 6. 재현 기준과 vanilla 비교

아래는 2026-09-28 채택 실행과 기존 공식 vanilla의 **동일 40 training renders/KF**
결과다. 모든 값은 seed 0 mapper replay이며, 동시 tracking 시간이나 반복 seed
분산은 포함하지 않는다.

| 장면 | Vanilla PSNR | 채택 PSNR | 차이(dB) | 최종 GS vanilla → 채택 | 채택 render / Adam |
|---|---:|---:|---:|---:|---:|
| Aria1253 | 20.751 | 25.783 | +5.031 | 190,533 → 195,316 | 4,760 / 4,760 |
| RPNG table_06 | 22.461 | 25.225 | +2.764 | 234,218 → 202,838 | 9,080 / 9,080 |
| UTMM square-1 | 18.825 | 22.272 | +3.448 | 162,663 → 121,363 | 3,600 / 3,600 |

장면별 차이의 단순 평균 +3.748dB. Vanilla와 Adam 횟수·birth·topology·loss 배분이
다르므로 dense나 ERVS 단독 효과가 아니다. Mapper 시간은 vanilla→채택 순서로
Aria 24.65→34.65초, RPNG 77.58→105.46초, UTMM 34.18→36.53초였다.
동일 render 비교를 동일 시간 비교로 표현하지 않는다. Carve OFF이므로 이 결과를
Carve 또는 geometry 개선의 증거로 사용하지 않는다.

원본 결과 경로:

```text
results/campaigns/gain_attribution/protected_prune/init_increase300_v1/{aria,rpng,utmm}/increase/opacity01/
results/campaigns/gain_attribution/render_budget40_feasibility/v1/fixed/{aria,rpng,utmm}/vanilla/
```

Window quota 비교에서는 1:5:6이 평균 −0.025dB, 0:6:6이 −0.154dB였다.
이는 대안 비교이며 **채택값은 계속 3:3:6**이다. 다음 값들은 이번 release에
포함하지 않는다: 15 renders/KF, 1:5:6 또는 0:6:6, RR, 최근 선택 횟수,
prune 150주기 또는 opacity 0.7, 장면별 init 배율, batch당 Adam 1회.

기존 실험 문서의 “미채택”은 그 실험 당시 판단이다. 현재 인계의 채택 여부는
이 문서와 `selected_mapping_recipe.json`, STATUS의 최신 항목을 따른다.

## 7. 인계 검증 기록

2026-09-29: 세 장면 `--check-only` PASS, CPU 테스트 28개 PASS, 문서 링크 PASS. Backend patch를 임시 디렉터리의 base source에 적용해 현재 sampler와 byte 단위 일치를 확인했다. 인계 작업에서는 새 GPU 학습을 실행하지 않았으며 위 품질 값은 채택 실험의 기록이다.
