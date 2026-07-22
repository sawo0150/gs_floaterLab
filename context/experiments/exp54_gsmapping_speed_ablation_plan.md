# exp54 — GS Mapping 연산 시간 ablation: gaussian 개수·밀도·해상도가 rasterize/backward에 미치는 영향

- 상태: **완료 (2026-07-22). 축1~7 전부 실행. 채택: 축1(pcd_downsample=128)+축7(PPM). 기각: 축2·축3·축5·축6+2조합. 검증된 보조 레버(미채택): 축4(render_downsample). exp53과 합쳐 실시간 배수 1.52배→0.94배(실시간 돌파) 달성.**
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

## 축4~7 실행 결과 (2026-07-22, 같은 `/loop` 세션 — exp53 축B·C 채택 위에서 스캔)

exp53 축B(`thresh=3.6`)+축C(`frontend_window=15`/`frontend_radius=1`)를 먼저 적용해
60.65s(0.93배, 이미 실시간 돌파 — 상세는 [exp53](exp53_frontend_realtime_plan.md))로
내려온 지점을 새 기준선으로 삼아 축4~7을 스캔. 아래 표의 "설정"은 전부 이 기준선 위에
**하나씩** 추가한 것(baseline 행 = 60.65s, PSNR 22.82/23.39, Sim3 1.93cm):

| 축 | 설정 | 온라인 루프 총합 | PSNR(mean/kf) | evo APE Sim3 RMSE | 판정 |
|---|---|---:|---:|---:|---|
| **4** | `Training.render_downsample: 2`(신규 구현, 매핑 렌더를 절반 해상도로) | 58.09s (−4.2%) | 21.99 / 22.71 (−0.83/−0.68dB) | 1.91cm | **검증된 보조 레버, 미채택** — 이미 실시간이라 이 손실을 감수할 이유 없음, 더 느린 GPU로 갈 때를 위해 코드만 남김 |
| 5 | `max_viewpoints` 20→10 | 60.20s (−0.7%, 사실상 무변화) | 21.09 / 21.41 (−1.73/−1.98dB) | (생략, ROI로 즉시 기각) | **기각** — 최악의 ROI, 되돌림 |
| 6+2 | `pcd_downsample_init: 64` + `densify_grad_threshold: 0.0006`(축2·축6 결합) | 60.76s (+0.2%) | 22.75 / 23.10 (오차범위) | 2.45cm | **기각** — 최종 gaussian 수는 116,143로 성공적으로 억제(축1의 122,957보다도 적음, 상쇄 가설 확인됨)했으나 **시간은 그대로** → 이 지점에선 gaussian 개수 자체가 더 이상 병목이 아님이 재확인, 되돌림 |
| **7** | `Dataset.ppm_sampling: true`(신규 구현, 동일 예산) | 61.18s (+0.9%, 오차범위) | **22.98 / 23.50 (+0.16/+0.11dB)** | 1.92cm | **채택** — 속도 변화 없이 품질만 순수 개선(exp44 "PPM=품질 왕"이 VIGS에서도 재확인), 공짜 이득이라 부담 없이 채택 |
| 7+1' | PPM + `pcd_downsample: 192`(예산을 더 줄여 품질 여유를 속도로 환전 시도) | 59.62s (−1.7%) | 22.64 / 22.98 (−0.18/−0.41dB) | (미측정, 순ROI 나쁨) | **기각** — PPM의 품질 여유를 속도로 못 바꿈(이미 tracking-bound라 mapping을 더 깎아도 총 시간 거의 안 줆), 192는 되돌리고 128 유지 |

**축4(render_downsample) 신규 구현**: VIGS는 원래 항상 `intrinsics * 8`로 원해상도까지
업샘플해서 매핑 — `vigs/vigs.py::call_gs()`에 `Training.render_downsample`(기본 1) 설정을
추가, 2 이상이면 `images`/`depths`/`normals`를 `F.interpolate(..., mode='area')`로
추가 다운샘플하고 intrinsics 배율을 `8/render_downsample`로 낮춰 일관되게 축소. held-out
평가 시 렌더 해상도와 GT 해상도가 달라 `IndexError`가 나던 문제도 `eval_utils.py`의
`eval_rendering()`에 해상도 불일치 시 렌더를 GT 해상도로 업샘플하는 방어 코드를 추가해
해결(해상도가 이미 같으면 no-op, 다른 실험엔 영향 없음). **결과 자체는 유효한 레버**
(−4.2%/−0.8dB)지만 이미 실시간을 넘긴 시점이라 지금은 채택 안 함 — 코드는 남겨둠.

**축7(PPM) 신규 구현**: `vigs/gaussian/scene/gaussian_model.py::create_pcd_from_image_and_depth()`에
`Dataset.ppm_sampling`(기본 false) 플래그를 추가. true면 Open3D RGBD 파이프라인의
`random_down_sample()`(uniform) 대신, 우리 배치 스크립트(`build_depthmono_ppm_chunks.py::
ppm_sample()`)와 동일한 방식으로 직접 구현: 그레이스케일 Sobel gradient magnitude로
유효 depth 픽셀에 대한 샘플링 확률(`p ∝ sobel + 0.1*mean + eps`)을 만들고
`np.random.default_rng().choice(..., p=...)`로 비복원 추출한 뒤 카메라 내부파라미터로
직접 역투영(카메라→월드는 `W2C`의 역행렬). 같은 함수 안에서 기존 uniform 경로와
분기만 하므로 `ppm_sampling: false`(기본)일 때는 완전히 기존과 동일하게 동작.

**축2+축6 결합 실험이 확정한 것**: 앞서(축1~3 라운드) 발견한 "축2(성긴 init)를 축6
(densify 공격성)과 묶지 않으면 상쇄된다"는 가설을 실제로 검증 — `densify_grad_threshold`를
3배(0.0002→0.0006) 높여 압축 증식을 성공적으로 억제(최종 gaussian 수가 오히려 축1보다도
적어짐)했는데도 **시간은 전혀 안 줄었다**. 즉 가설 자체(축2·축6 상쇄)는 맞았지만, 그
상쇄를 풀어도 이 지점(mapping 49.8s vs tracking 52.3s, 거의 균형)에서는 gaussian
개수가 더 이상 지배적 변수가 아니라는 더 근본적인 결론에 도달 — **밀도/예산 축(축1·2·3·5·6)
전체가 이 지점부턴 소진됨**을 확정.

**축D(exp53, correlation 해상도) 조사 결과 — 구현 불가로 판정**: `vigs/modules/corr.py`의
`CorrBlock`/`AltCorrBlock`이 쓰는 `num_levels=4`, `radius=3`은 `factor_graph.py`/
`droid_net.py`의 사전학습된 ConvGRU(update_module) 호출부에 전부 하드코딩되어 있고,
correlation lookup의 출력 채널 수(`num_levels × (2×radius+1)²`)가 그 **동결된 사전학습
가중치의 입력 채널 수와 고정 결합**되어 있음 — 추론 시점에 radius/num_levels를 바꾸면
텐서 shape가 학습된 conv 가중치와 안 맞아 크래시하거나(더 작게) 무의미한 zero-padding
결과가 됨. **재학습 없이는 손댈 수 없는 축으로 확정**(exp53 원안에서도 이미 "최소
기대효과+최고 위험"으로 최하위 우선순위였던 예상이 실측 조사로 확인됨) — 실행하지 않고
이 결론만 기록.

## 최종 확정 레시피 (exp53과 통합, 2026-07-22)

exp53 축A+B+C와 exp54 축1+축7을 전부 합친 최종 설정으로 1253 전체 재검증:
`iters1=1`/`iters2=0`(`track_frontend.py`), `motion_filter.thresh=3.6`,
`frontend_window=15`/`frontend_radius=1`, `pcd_downsample=128`/`pcd_downsample_init=32`,
`ppm_sampling=true`(나머지 파라미터는 전부 기본값 유지).

| 지표 | 값 |
|---|---:|
| 온라인 루프 총합 | **61.34s** |
| **실시간 배수** | **0.94배 (실시간 돌파)** |
| PSNR (mean/kf) | 22.78 / 23.14 |
| evo APE Sim3 RMSE | 2.41cm (ORB 13cm 대비 5.4배 여유) |
| tracking 총합 | 52.31s (개별 예산 이하) |
| mapping 총합(map_dispatch) | 49.79s (개별 예산 이하) |
| 오버랩 효율 | 81.9% |

baseline(1.52배)에서 시작해 exp53+54 전체 트랙으로 **실시간의 62%를 실제로 깎아
5070 Ti 단일 GPU에서 실시간(<1.0배)을 처음으로 달성**. 남은 미탐색 레버는 축E(커널
튜닝, 고위험·저기대효과라 최후순위 유지)뿐 — 이미 목표를 달성했으므로 우선순위 낮음.

**코드 상태**: 위 6개 파라미터 전부 `config/aria1253.yaml`/`track_frontend.py`에
**채택·유지**(uncommitted, VIGS-SLAM은 dirty 상태로 실험 유지). `render_downsample`
(축4)과 `ppm_sampling`(축7) 스위치는 코드에 남아있으나 전자는 기본 1(off), 후자는
현재 설정에서 true(채택).
