# exp59 — strict streaming 27dB 레시피의 타 데이터 전이 검증

- 상태: **완료 (2026-08-03) — 4개 데이터 전부 재현 실패. 원인은 freeze 경계 하드코딩(305 붕괴의 대부분도 포함) + PGBA 크래시(원인 미확정, 배경스레드 가설은 기각) + 1.5× 데드라인 초과 3종으로 확정**
- 선행: [exp57](exp57_causal_background_polishing_plan.md)에서 채택한 freeze800 strict-disjoint
  recipe(pre-IMU gate + append-only PPM birth + freeze800 + background RNG0/shuffle-epoch/idle-guard0ms
  + dense offsets1,4 + late-iters3(650) + PGBA cutoff1120)는 전부 `aria1253`(301-1253, 1303프레임,
  65.1초) 단일 장면에서만 검증됐다.
- 목적: 같은 레시피를 **그대로**(재튜닝 없이) 다른 Aria 녹화에 적용했을 때 strict 27dB가
  재현되는지 확인하고, 실패하면 원인을 규명한다. CLAUDE.md 1차 목표(strict 27dB)는 재현성
  검증까지 포함하므로, 단일 장면 과최적화 여부를 확인하는 게 이 실험의 목적이다.

## 대상 데이터

| 이름 | 원본 | 관계 | 프레임 | 녹화 길이 | 1.5× 예산 |
|---|---|---|---:|---:|---:|
| aria1253 (기준) | `0416_301-1253` | — | 1,303 | 65.10s | 97.65s |
| aria1253rot | `0416_301-1253-2_rot` | **같은 방, 회전 궤적**(exp52 확인) | 1,498 | 76.05s | 114.07s |
| aria301_305 | `0416_301-305` | **다른 장면**(301→305 복도/여러 방 이동) | 2,688 | 134.38s | 201.57s |
| aria301_12F | `0416_301-12F` | **다른 장면**(12층) | 2,201 | 110.00s | 165.00s |

Tcb(camera-rgb↔imu-right 외부파라미터)는 네 데이터 모두 소수점 8자리까지 완전히 동일 —
같은 물리 Aria 기기로 촬영되어 calibration/`config/exp57_verify_freeze800.yaml`을 그대로
재사용할 수 있음을 확인했다. `aria301_305`/`aria301_12F`는 VRS→VIGS(RGB rectify
1024×1024 fx=fy=500 + imu-right 추출) 변환 스크립트가 없어서 새로 작성했다
(`scripts/incremental/build_vigs_aria_input.py`, `scripts/pipeline/full_traj_to_rgb_3dgs.py`의
rectification과 OpenMAVIS EuRoC 변환기의 IMU 추출 패턴을 재사용).

## 결과 1 — aria1253rot, 경계값 그대로(freeze800/pgba1120/late650/bgpolish700) — 품질 붕괴 없이 완주, 그러나 −1.85dB

| 지표 | aria1253 freeze800(기준, 2-run 평균) | aria1253rot as-is |
|---|---:|---:|
| fixed held-out PSNR | 27.8464 | **26.0001** |
| fixed SSIM / LPIPS | 0.8599 / 0.2544 | 0.8338 / 0.3069 |
| wall time / 1.5× 예산 | 97.25s / 97.65s (여유 +0.40s) | **115.57s / 114.07s (초과 −1.50s)** |
| zero-tail | 0 update | 0 update (유지) |
| keyframe | 118 | 169 |
| Gaussian | 83,898 | 114,166 |

frame bin(fixed-eval만):

| bin | PSNR |
|---|---:|
| 0–199 | 26.486 |
| 200–399 | 27.256 |
| 400–599 | 27.217 |
| 600–799 | 27.674 |
| 800–999 | 26.388 |
| 1000–1199 | 26.114 |
| 1200–1400 | 23.574 |
| 1400–1498 | **20.751** |

`mapping_freeze_after_frame=800`은 aria1253에서는 전체의 63.8% 지점이지만 1,498프레임
시퀀스에서는 53.4% 지점이라, "PPM birth만으로 버텨야 하는" post-freeze 구간이
453프레임(36.2%)→698프레임(46.6%)으로 늘었다. `pgba_disable_after_frame=1120`도
89.4%→74.8% 지점으로 앞당겨져 global BA가 더 일찍 꺼진다. 실제 bin도 이 가설과 일치:
freeze 지점 근처부터 서서히 무너지다 마지막 100프레임(전체의 93%~100% 지점)에서 20.75dB로
붕괴 — aria1253의 후반부 붕괴 패턴이 그대로, 더 이르고 크게 재현됐다.

## 결과 2 — aria1253rot, 경계값을 1498/1253 비율로 재조정 — 재현되는 CUDA 크래시

경계값을 `freeze_after_frame=956`, `pgba_disable_after_frame=1339`,
`late_mapping_start_frame=777`, `background_polish_start_frame=837`(전부 원래 비율 유지)로
바꿔 같은 커맨드를 **두 번** 실행했다. 두 번 모두 keyframe~116(frame≈1000, `freeze_after_frame`
직후) 부근에서 동일한 오류로 죽었다:

```
IndexKernelUtils.cu:16: vectorized_gather_kernel: Assertion
  `ind >=0 && ind < ind_dim_size` failed
→ vigs.py:_track_impl → factor_graph.py:update_pgba → depth_video.py:cuda_pgba
  → projective_ops.py:projective_transform → pinhole.py:iproj_pinhole
```

두 크래시 모두 메인 트래킹 스레드(PGBA)와 background polish 워커 스레드
(`Thread-1 _gs_worker`, `gs_backend.py:background_polish_step`)의 CUDA 호출 로그가
같은 시점에 인터리빙되어 있어, 둘이 동시에 GPU를 쓰다 CUDA context가 깨진 것으로 보인다.
소스 확인 결과 `pgba_disable_after_frame`/`late_mapping_start_frame` 등은 단순
"이 프레임 이후 스위치" 비교값일 뿐 어떤 버퍼 크기와도 연결되지 않는다(`vigs.py`의
사용처 전부 `if t < self._pgba_disable_after_frame` 류 단순 비교). 따라서 두 값 자체가
직접 원인은 아니고, 유력 가설은 **`background_polish_start_frame`을 700→837로 늦춘 것이
background 스레드의 GPU 커널 타이밍을 바꿔, 기존엔 안 드러나던 PGBA loop-closure 코드의
경계조건 버그를 노출시켰다**는 것이다. 확정하려면 `background_polish_start_frame`만
되돌린 대조군이 필요하지만, 사용자 판단으로 추가 검증 없이 여기서 축을 닫았다.

첫 시도는 크래시 후 메인 프로세스가 종료되지 않고 GPU 메모리 13.4GB를 물고
**약 9시간 행(hang)** 됐다(백그라운드 워커 스레드 예외가 메인 프로세스를 안 죽임).
`timeout` 래퍼 없이 백그라운드 실행하면 이런 무한 행이 조용히 방치될 수 있다는
운영상 교훈을 얻었다 — 이후 모든 재현 스크립트에 `timeout` 래퍼를 강제한다.

## 결과 3 — aria301_305 (진짜 다른 장면), 경계값 그대로 — 훨씬 심한 붕괴, 후반부 국한 아님

| 지표 | aria1253 freeze800(기준) | aria301_305 as-is |
|---|---:|---:|
| fixed held-out PSNR | 27.8464 | **16.9497** |
| fixed SSIM | 0.8599 | 0.7482 |
| wall time / 1.5× 예산 | 97.25s / 97.65s | **204.84s / 201.57s (초과 −3.27s)** |
| keyframe (총 프레임 대비) | 118/1303 (9.1%) | 147/2688 (**5.5%**) |
| Gaussian | 83,898 | 84,175 |

frame bin(fixed-eval만, 8구간 균등분할):

| bin(frame idx) | PSNR |
|---|---:|
| 0–335 | 15.222 |
| 335–671 | 15.370 |
| 671–1007 | 15.272 |
| 1007–1343 | 22.304 |
| 1343–1679 | 14.815 |
| 1679–2015 | 16.734 |
| 2015–2351 | 19.974 |
| 2351–2687 | 15.936 |

aria1253rot과 달리 **초반 bin부터 이미 15dB대**다. `mapping_freeze_after_frame=800`은
freeze 이전 구간(0–800, 전체의 29.8%)에도 영향을 못 미치므로, 이건 freeze 경계
스케일 문제가 아니라 **더 근본적인 실패**(SLAM 트래킹 자체 또는 Gaussian
초기화/scene-extent 가정)로 보인다. keyframe 비율도 9.1%→5.5%로 크게 낮아졌는데, 이는
tracker가 신뢰할 만한 신규 keyframe을 덜 만들었다는 뜻이라 트래킹 품질 저하와 방향이
일치한다. 로그에는 `nan`/`lost`/`reinit` 등 명시적 오류 신호는 없었다 — 조용한
degradation이라 원인은 이 시점에 미확정이었다. **후속 축 D(아래) 검증 결과, 이 붕괴의
대부분은 freeze/pgba-cutoff가 이 장면엔 너무 이른 지점(29.8%/41.7%)에 걸려 있었기
때문임이 확인됐다** — `init_gaussian_extent` 등 scene-scale 가정 문제라기보다는
문제 1(경계 하드코딩)의 심한 사례였다.

## 결과 4 — aria301_12F (진짜 다른 장면, 12층), 경계값 그대로 — 중반은 건강, 마지막 22%만 붕괴

`0416_301-12F` VRS도 `build_vigs_aria_input.py`로 변환했다(2,201프레임, 110.00초,
1.5× 예산 165.00초). Tcb는 이번에도 aria1253과 소수점까지 동일했다.

| 지표 | aria1253 freeze800(기준) | aria301_12F as-is |
|---|---:|---:|
| fixed held-out PSNR | 27.8464 | **26.1338** |
| fixed SSIM / LPIPS | 0.8599 / 0.2544 | 0.8684 / **0.3859** |
| wall time / 1.5× 예산 | 97.25s / 97.65s | **168.28s / 165.00s (초과 −3.28s)** |
| keyframe (총 프레임 대비) | 118/1303 (9.1%) | **304/2201 (13.8%)** |
| Gaussian | 83,898 | 134,113 |

frame bin(fixed-eval만, 8구간 균등분할):

| bin(frame idx) | PSNR |
|---|---:|
| 0–275 | 26.789 |
| 275–550 | 28.733 |
| 550–825 | **29.025** |
| 825–1100 | 28.741 |
| 1100–1375 | 27.249 |
| 1375–1650 | 27.690 |
| 1650–1925 | 23.334 |
| 1925–2200 | **17.735** |

aria301_305와 달리 12F는 **중반(550–1650, 전체의 25~75%)이 오히려 aria1253급으로
건강하다**(28~29dB). keyframe 비율도 13.8%로 aria1253(9.1%)보다 높아 트래킹 자체는
잘 작동한 것으로 보인다. 다만 `mapping_freeze_after_frame=800`(전체의 36.3% 지점,
aria1253의 63.8%보다 훨씬 이름)에도 불구하고 실제 붕괴는 그보다 한참 뒤인 마지막
22%(1925–2200)에서야 급격히 나타났다 — PPM append-birth만으로도 상당 구간은
버티지만 완전히 무너지는 지점은 freeze 경계 자체보다 시퀀스 후반부 특성(예: 이
구간에서 카메라가 12층의 새 미탐색 공간으로 더 깊이 들어갔을 가능성)에 더 좌우되는
것으로 보인다. LPIPS(0.386)는 PSNR/SSIM 대비 유난히 나빠 지각 품질 저하가 픽셀 오차보다
크다는 뜻이고, 1.5× 데드라인도 다시 초과했다(+3.28s, aria301_305의 +3.27s와 거의 동일한
초과폭 — 데드라인 초과가 데이터 종류와 무관하게 체계적임을 강화).

**결론: aria301_305의 "초반부터 전체 붕괴"는 12F로 재현되지 않았다.** 즉 305의 실패는
freeze 스케줄 문제가 아니라 그 장면 고유의(아마도 트래킹) 문제였을 가능성이 높아졌고,
12F는 오히려 aria1253rot과 같은 "freeze 경계 비율 불일치 → 후반 coverage 붕괴" 계열
문제의 세 번째 재현 사례가 됐다.

## 확정된 문제 3종 (다음 축 후보)

1. **freeze/PGBA-cutoff 등 프레임 경계값이 절대 프레임 번호로 하드코딩**되어 있어
   시퀀스 길이가 달라지면 그대로 못 씀 — aria1253rot에서 재현, 비율 보정이 합리적
   가설이나 그 자체로 새 크래시를 유발함(결과 2).
2. **1.5× 데드라인을 시스템이 스스로 못 지킴** — aria1253(2-run)은 +0.38~0.42s 여유였지만
   aria1253rot(+1.50s), aria301_305(+3.27s), aria301_12F(+3.28s) 셋 다 예산을 넘겼다.
   **초과폭이 305/12F에서 거의 동일(+3.27/+3.28s)한 건 시퀀스 길이(2× 이상 김)에 비례하는
   체계적 문제일 가능성을 시사**하지만, 정확한 원인(background polish backlog vs 순수
   오버헤드)은 세밀한 per-step 타이밍 로그 없이는 미확정.
3. **background polish 워커 스레드와 메인 PGBA 스레드의 GPU 동시 사용이 CUDA
   device-side assert로 이어지는 재현 가능한 크래시**가 있음(결과 2). 예외가
   메인 프로세스를 안 죽이고 GPU 메모리를 문 채 무한정 행(hang)되는 2차 버그도 있음
   (운영 이슈로 별도 기록).

**aria301_305의 겉보기 이상치는 축 D로 대부분 해소됐다.** 처음엔 12F(중반 28~29dB
건강, 마지막 22%만 붕괴, freeze 비율 불일치 패턴)와 달리 305는 초반부터 균일하게
15dB대라 별개의 트래킹 붕괴로 보였지만, freeze/pgba-cutoff/시간제약을 전부 뺀 축 D
검증 결과 22.96dB로 대부분 회복됐다(→ 위 "축 D" 항목). 즉 305도 근본적으로는
**문제 1(freeze 경계 하드코딩)의 특히 심한 사례**였다. 다만 unconstrained 22.96dB도
다른 세 장면의 strict 결과(26~28dB)보다 4~5dB 낮게 남아 있어, 305가 다른 세 장면보다
**진짜로 더 어려운 장면**이라는 잔여 효과는 별도로 남는다(원인 미확정).

## 다음 문제 축 후보

각 축은 결과 1~4에서 확정된 문제 중 하나를 겨냥한다. 서로 대체로 독립적이라 순서를
바꿔도 되지만, 비용/리스크가 가장 낮은 것부터 배치했다.

### 축 C — PGBA×background-polish 동시성 크래시 원인 확정 (문제 3) — **가설 기각**

- **가설(기각됨)**: `background_polish_start_frame`을 700→837로 늦춘 것이 background
  워커 스레드의 GPU 커널 타이밍을 바꿔, 기존엔 안 드러나던 PGBA loop-closure 코드의
  경계조건 버그를 노출시켰다.
- **검증**: aria1253rot에서 `background_polish_start_frame`만 700으로 되돌리고
  `freeze_after_frame=956`/`pgba_disable_after_frame=1339`/`late_mapping_start_frame=777`은
  그대로 유지해 재실행(2026-08-03).
- **결과**: **동일한 크래시가 그대로 재현됐다**(keyframe~130, frame~1180, 동일한
  `vectorized_gather_kernel` index-out-of-bounds, 동일 스택: `update_pgba` →
  `cuda_pgba` → `iproj_pinhole`). `background_polish_start_frame`은 크래시 원인이
  아니었다 — **가설 기각.**
- **다음 범위 축소**: as-is 조합(freeze800/pgba1120/late650, aria1253rot에서 재현
  없이 완주함)과 scaled 조합(freeze956/pgba1339/late777, `background_polish_start_frame`
  값과 무관하게 2/2 재현)의 유일한 공통 차이는 freeze/pgba-cutoff/late-mapping 세
  값 자체다. 유력 후보는 **`late_mapping_start_frame=777`(late-iters3 전환)과
  `mapping_freeze_after_frame=956`(freeze+append-birth 전환)이 겹치는 지점(±180프레임)
  근처에서 PGBA가 여전히 활성 상태로 append-birth Gaussian의 좌표/인덱스를 건드리는
  조합**이지만, 세 값을 하나씩 원복해가며 격리해야 확정된다(아직 미실행).
- 첫 크래시와 마찬가지로 이번에도 워커 스레드 예외 후 메인 프로세스가 안 죽고 GPU
  14.3GB를 물었다 — `timeout`으로 잡아 정리(운영 이슈로 계속 재현됨을 재확인).

### 축 B — 1.5× 데드라인 초과 원인 계측 (문제 2)

- **가설**: background polish가 마지막 센서 프레임 도착 이후에도 backlog를 계속 처리하고
  있어(진짜 zero-tail 위반일 수 있음), 초과폭이 시퀀스 길이에 비례한다
  (305/12F 둘 다 +3.27~3.28s로 거의 동일).
- **검증**: 기존 `_timed()`/`VIGS_TIMING_LOG` 계측 패턴을 확장해 마지막 프레임 도착
  시각과 마지막 optimizer update 시각을 직접 로그로 남기고, 그 차이를 측정한다. "정말
  zero-tail을 어겼는지" 자체가 strict 계약 신뢰성 문제라 우선순위가 높다.
- **비용/리스크**: 낮음~중간 — 계측 코드 추가만 필요(로직 변경 없음), run 1~2회.

### 축 D — aria301_305 고유 이상치 원인 규명 — **부분 확인: freeze 경계가 주범, 잔여 갭은 진짜 scene 난이도**

- **가설**: SLAM 트래킹 자체가 이 장면(더 넓은 공간, 방↔복도 이동)에서 저하되었거나,
  `init_gaussian_extent=30`처럼 aria1253 단일 방 규모에 맞춘 고정 파라미터가 안 맞는다.
- **검증**: `--realtime_replay`/`--strict_aria_online`/freeze/pgba-cutoff/late-mapping을
  전부 빼고 `--pure_online`만으로 unpaced 전체 정규 매핑(densify/prune 계속, 시간제약
  없음)을 실행(2026-08-03).
- **결과**: fixed **22.9585dB**(SSIM 0.8115) — as-is 결과(16.95dB)보다 **+6.0dB** 회복했고,
  bin도 [20.3, 19.2, 20.8, **26.5**, 23.8, 22.6, **26.2**, 24.3]로 as-is의 균일한
  ~15dB 붕괴 패턴이 사라졌다. 게다가 unpaced wall time이 **64.2초**(실제 녹화
  134.4초의 0.48배)로, freeze/background-polish 없이도 real-time보다 여유 있게 처리했다
  — 즉 **연산량 부족이 원인이 아니었다.**
- **결론**: as-is 결과의 catastrophic 붕괴(16.95dB, 초반부터 균일하게 나쁨)는 주로
  `mapping_freeze_after_frame=800`(전체의 29.8% 지점)이 이 장면엔 너무 이른 데다,
  `pgba_disable_after_frame=1120`(41.7% 지점)까지 겹쳐 초반 절반 가까이가 저품질로
  굳어버린 게 원인이었다 — **freeze 경계 문제(문제 1)의 특히 심한 사례였지 별개의
  트래킹 붕괴는 아니었다.** 다만 제약 없는 22.96dB도 aria1253/aria1253rot/12F의
  strict 결과(26~28dB)보다 여전히 4~5dB 낮다 — keyframe 비율도 unconstrained에서 역시
  낮은 편(150/2688=5.6%, as-is의 5.5%와 거의 동일)이라, **진짜 더 넓고 복잡한 공간이라는
  scene 난이도 자체의 잔여 효과**는 남아있는 것으로 보인다(정확한 크기는 미확정).

- **가설**: SLAM 트래킹 자체가 이 장면(더 넓은 공간, 방↔복도 이동)에서 저하되었거나,
  `init_gaussian_extent=30`처럼 aria1253 단일 방 규모에 맞춘 고정 파라미터가 안 맞는다.
  12F는 정상이었으므로 "다른 장면 자체"가 아니라 305 고유 문제로 범위가 좁혀졌다.
- **검증**: `--pure_online`(시간 제약 없는 대조군)으로 먼저 트래킹/keyframe 궤적만
  격리해 확인. 트래킹 자체가 나쁘면 keyframe 궤적을 MPS(있다면)와 비교, 정상이면
  `init_gaussian_extent`를 실제 궤적 bounding box 기반으로 계산하도록 바꿔 재시도.
- **비용/리스크**: 낮음 — run 1회(오히려 pure_online이라 시간제약 없이 더 안정적일 수
  있음), 단 구조 원인까지 파려면 후속 조치가 더 필요할 수 있음.

### 축 A — 프레임 경계를 절대값 대신 비율로 받는 옵션 추가 (문제 1)

- **가설**: freeze/pgba-cutoff/late-mapping/background-polish-start 4개를 시퀀스 길이
  대비 비율로 계산하게 하면, 매번 수동 계산 없이 다른 길이 시퀀스에서도 원래 recipe의
  "상대적 동작"이 재현된다.
- **검증**: `demo.py`에 `--mapping_freeze_after_frac`류 옵션을 추가(또는 기존 CLI 위에
  실행 스크립트에서 계산)하고, aria1253rot/aria301_12F에서 재실행해 27dB 근처로
  회복되는지 확인.
- **비용/리스크**: 가장 큼 — 코드 수정 범위가 제일 넓고, 축 C에서 크래시 원인이 안
  밝혀진 채로 진행하면 같은 크래시를 다시 밟을 수 있다. **축 C를 먼저 해결하고
  진행하는 게 안전.**

## 산출물

- `results/experiments/exp59_aria1253rot_freeze800_asis_strict15x`
- `results/experiments/exp59_aria1253rot_freeze800_scaled_strict15x` (크래시 로그만 보존)
- `results/experiments/exp59_aria301_305_freeze800_asis_strict15x`
- `results/experiments/exp59_aria301_12F_freeze800_asis_strict15x`
- `data/aria301_305/{rgb,imu.txt}`, `calib/aria301_305.txt` (신규)
- `data/aria301_12F/{rgb,imu.txt}`, `calib/aria301_12F.txt` (신규)
- `scripts/incremental/build_vigs_aria_input.py` (신규, VRS→VIGS 변환 일반화)
- `scripts/run_aria_strict27.sh`, `scripts/run_aria_strict27_scaled.sh` (VIGS-SLAM repo, 신규)
