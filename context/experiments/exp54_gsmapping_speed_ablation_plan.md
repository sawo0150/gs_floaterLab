# exp54 — GS Mapping 연산 시간 ablation: gaussian 개수·밀도·해상도가 rasterize/backward에 미치는 영향

- 상태: **진행중 (2026-07-22). 축1~3 완료. 축1 채택, 축2·축3은 기각(효과 없음/역효과). 축4~7 미착수.**
- 배경: [exp52](exp52_vigs_slam_eval.md)에서 GS Mapping 루프를 12단계로 세분화한 결과
  **rasterize+backward+loss_compute가 81.4%**를 차지함을 확인(map() 내부 미계측
  12.9%도 매 iteration 전체 gaussian에 대해 도는 isotropic_loss 등이라 사실상 같은
  축). 이 셋 다 "씬에 gaussian이 몇 개 있고, 그중 몇 개가 화면에 찍히는가"에 직접
  비례 — exp54는 이 gaussian 개수/밀도/해상도 관련 축을 체계적으로 흔들어 실제
  rasterize/backward 시간과 품질(PSNR)에 미치는 영향을 정량화한다.
- exp52/53과의 역할 분담: exp52=mapping 실시간성 전반, exp53=frontend 전담,
  **exp54=gs_mapping 내부 연산량 자체를 줄이는 ablation 전담**(exp52 "다음 단계"의
  "gs_mapping 자체 연산량 감소" 항목을 구체화한 트랙).
- 계측 인프라는 exp52에서 이미 구축 완료 — `gs_backend.py`의 `map()` 5단계
  (rasterize/loss_compute/backward/optimizer_step/densify_prune) +
  `_process_track_data_impl()` 6단계(pose_scale_update/w2c_compute/camera_init/
  render_for_mask/add_next_kf/add_next_kf_init) 계측을 그대로 재사용.

## 실험축

| 축 | 내용 | 현재값 | rasterize/backward에 미치는 경로 |
|---|---|---|---|
| **1. Keyframe gaussian 밀도** | `Dataset.pcd_downsample` — 일반 keyframe에서 depth-unprojected 포인트클라우드를 얼마나 랜덤 다운샘플할지(`random_down_sample(1/N)`) | 64 | 매 신규 keyframe이 추가하는 gaussian 수에 직접 비례, 이후 모든 프레임의 rasterize/backward 비용에 누적 |
| **2. Init gaussian 밀도** | `Dataset.pcd_downsample_init` — **첫 keyframe만** 별도로 더 촘촘하게(2배) 샘플링 | 32 | 씬 전체의 기반 gaussian 수를 한 번에 결정 — 축1과 달리 시퀀스 시작부터 끝까지 **compounding**되는 별도 축(1과 병합 금지, 영향 규모가 다름) |
| **3. `iters`(map() 반복 횟수)** | 일반 keyframe=10, 첫 keyframe=`init_itr_num//len(window)`, PGBA=20 | 상황별 상이 | rasterize/backward/loss_compute/optimizer_step **네 개 전부에 곱으로 걸리는** 가장 직접적인 배율 레버 |
| **4. 렌더 해상도** | `call_gs`에서 트래킹 해상도(1/8)를 매핑 시 원해상도로 업샘플(`intrinsics * 8`) | 원해상도 | 픽셀 수에 거의 제곱으로 비례(rasterize/loss_compute) — 축1~2보다 효과가 더 클 가능성 |
| **5. `max_viewpoints`** | iteration당 처리하는 view 개수 상한 | 일반 20 / PGBA 12 | view 수만큼 rasterize/backward 반복 — 곱셈 레버 |
| **6. Densify 공격성** | `densify_grad_threshold`/`gaussian_th`/`gaussian_extent`/`size_threshold` | opt_params 기본값 | 축1~2(초기 생성량)와 별개로 **학습 중 증식 속도**를 결정 — 시간이 지날수록 gaussian 수를 얼마나 빨리 불리는지 |
| **7. PPM 기반(content-adaptive) 샘플링** | VIGS의 `create_pcd_from_image_and_depth()`가 쓰는 `pcd_tmp.random_down_sample(1/N)`(uniform random)을 우리 exp44/48에서 검증된 **Sobel-gradient 기반 PPM**(`scripts/incremental/build_depthmono_ppm_chunks.py`의 `ppm_sample()`)으로 교체 | uniform random | 같은 gaussian 예산을 edge/디테일 영역에 우선 배정(`p ∝ Sobel gradient magnitude + 낮은 균일 바닥`) — exp44에서 "PPM=품질 왕"으로 검증됨(같은 개수로 더 높은 PSNR). **exp54 관점에서는 반대 방향으로 활용**: 동일 PSNR을 더 적은 gaussian 개수로 달성 가능한지 검증 → 가능하면 rasterize/backward가 공짜로 줄어듦 |

**축1·2 vs 축7의 차이**: 축1/2는 "몇 개를 남기는가"(양), 축7은 "어떤 기준으로 남기는가"(질적 배분) — 독립적인 두 차원이라 조합 실험(예: PPM + 낮은 밀도)도 유효한 후속 셀.

**축7 이식 참고자료**: 같은 1253 씬에 대해 이미 PPM 결과물이 존재함
(`data/scenes/301_1253/05_incremental_dense/chunk_*/sparse/0/ppm_points3D.txt`,
exp48 `results/experiments/exp48_v2_ppm*`) — 새로 구현하는 게 아니라 검증된 방법을
VIGS의 `create_pcd_from_image_and_depth()` 함수 안에 이식하는 작업.

## 측정 계획

- 각 축을 **한 번에 하나씩**, baseline(현재 config) 대비 변경.
- 측정 지표: ①`map()` 5단계 + `process_track_data` 6단계 시간(exp52 계측 그대로) ②GS
  Mapping 스레드 총합 ③최종 gaussian 개수(`self.gaussians._xyz.shape[0]`) ④held-out/
  keyframe PSNR(`--pure_online` 하네스) — 속도만 보고 품질 붕괴를 놓치면 안 됨.
- 1253 전체 시퀀스, `_gs_parallel: true`(현재 권장 설정) 기준으로 통일.
- **Pass 기준 없음(exp53과 달리 절대적 실시간 목표가 아니라 트레이드오프 곡선 탐색)**
  — 각 축의 "시간 대 PSNR" 산점도를 그려서 어느 축이 가장 효율적인 레버인지 순위를
  매기는 게 목적.

## 축1~3 실행 결과 (2026-07-22, `/loop` 자동 실행)

baseline(모든 축은 exp53 축A 채택 전, `iters1=4`/`iters2=2` 위에서 단독 스캔) 대비 1253
전체 시퀀스 + evo_ape(Sim3):

| 축 | 설정 | 온라인 루프 총합 | 실시간 배수 | PSNR(mean/kf) | evo APE Sim3 RMSE | 판정 |
|---|---|---:|---:|---:|---:|---|
| baseline | ds=64, ds_init=32, iters=10 | 98.94s | 1.52배 | 22.60 / 22.92 | 1.30cm | 기준 |
| **1** | `pcd_downsample: 128` | **95.70s (−3.3%)** | 1.47배 | 22.55 / 22.78 (거의 동일) | 1.31cm | **채택** — 소폭이지만 순수 이득, 부작용 없음 |
| 2 | `pcd_downsample_init: 64` | 100.12s (**+1.2%, 역효과**) | 1.54배 | 22.84 / 23.11 (오히려 상승) | 1.32cm | **기각** — 아래 참조 |
| 3 | `map()` `iters` 10→5 | 97.45s (−1.5%) | 1.50배 | 22.14 / 22.44 (−0.46~0.48dB) | 1.32cm | **기각** — ROI 나쁨, 아래 참조 |

**축1 (`pcd_downsample` 64→128) 채택**: keyframe당 초기 gaussian 수를 절반으로 줄여
rasterize/backward 부담을 낮춤. 속도 이득은 −3.3%로 예상보다 작았지만(gaussian 수가
줄어도 densify가 일부 보충) 품질·궤적 손실이 전혀 없어 **exp53 축A와 조합 가능한
독립적인 순이득 레버**로 확정 — 이후 모든 조합 실험의 새 기준값으로 채택.

**축2 (`pcd_downsample_init` 32→64) 기각 — 반직관적 발견**: 첫 keyframe만 2배 성기게
초기화하면 초기 gaussian 수는 확실히 줄지만, 최종 gaussian 개수가 오히려 **더 커짐**
(202,089 vs 축1의 122,957) — `densify_and_prune`이 성긴 초기화를 보충하려 학습 중 더
공격적으로 증식한 결과로 진단. 그 결과 총 시간은 절감은커녕 baseline보다 **살짝 늘어남
(+1.2%)**. **교훈**: init 밀도 축(축2)과 densify 공격성 축(축6)은 서로 독립이 아니라
직접 상쇄(compensate)하는 관계 — 축2 단독으로는 레버로 못 씀, 축6과 반드시 함께
묶어야 의미 있는 실험이 됨(다음 라운드 후보).

**축3 (`map()` iters 10→5) 기각 — ROI 나쁨 + tracking-bound 규명**: rasterize/backward/
loss_compute/optimizer_step 네 개 전부에 곱으로 걸리는 가장 직접적인 레버라 기대가
컸으나, 실측 −1.5% 시간 절감에 PSNR −0.46~0.48dB 손실로 트레이드오프가 나쁨. 원인
분석 결과 이 시점(iters1=4/iters2=2 baseline 기준)엔 **tracking 자체가 이미 88.999초로
전체의 91%를 차지** — mapping을 반으로 깎아도 병렬 구조에서 critical path가 tracking
쪽에 걸려 있어 총 시간이 거의 안 줄어드는 구조였음. **이 발견이 exp53(frontend) 우선
순위를 끌어올린 직접적 근거** — mapping 단독 축소는 tracking이 더 무거운 한 한계가
뚜렷함.

**exp53과의 조합**([exp53](exp53_frontend_realtime_plan.md) 참조): 축1(ds128)을
exp53 축A(`iters1=1`/`iters2=0`)와 합치면 **72.91s(1.12배)** — 이 세션 최고 기록.
추가로 `pcd_downsample=256`까지 밀어붙이는 시도는 **실패**: 72.68s로 사실상 변화
없음(mapping이 더 이상 병목이 아니게 된 tracking-bound 구간에 재진입) + PSNR만
21.07/21.38로 −1.3dB 추가 손실 → **128이 이 축의 최적점으로 확정**, 256은 기각하고
config를 128로 되돌림.

**코드 상태**: `config/aria1253.yaml`의 `pcd_downsample: 128`(`pcd_downsample_init: 32`
유지)을 새 기준값으로 **채택·유지**(uncommitted, VIGS-SLAM은 dirty 상태로 실험 유지).

## 다음 단계 (미착수)

1. 축6(densify 공격성)을 축2(init 밀도)와 **묶어서** 재시도 — 단독으로는 상쇄됐던 두
   레버를 같이 조여야 진짜 절감이 나올지 검증.
2. 축4(렌더 해상도)·축5(`max_viewpoints`) — 아직 하나도 안 건드린 축, 축1·3과 별개
   메커니즘이라 조합 여지 있음.
3. 축7(PPM) 이식 — `create_pcd_from_image_and_depth()`에 `ppm_sample()` 로직 연결,
   `depth_cal`(SLAM point 보정) 배선 필요. 아직 미착수.
4. exp53 축B~E(frontend 추가 절감)와 이번 축1을 넘어서는 조합을 계속 탐색 — 현재
   72.91s(1.12배)에서 남은 ~12%(65.1s까지)를 메우는 게 다음 목표.
