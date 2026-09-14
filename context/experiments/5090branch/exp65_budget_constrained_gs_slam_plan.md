# exp65 — Budget-Constrained GS-SLAM → Backpolish-Free 재프레이밍 (논문 트랙 실행 계획)

- 상태: **계획 수립 완료, 실행 전 (2026-08-18, ADDENDUM 1+2 반영으로 재프레이밍 완료)**.
  최초 계획(§0 원 문장)은 "iteration당 효율을 올린다"였는데, 사용자가 같은 날 두 번의
  ADDENDUM으로 목표를 **"backpolish(전역 refinement 단계)를 아예 없앤다"(C0)** 로 재정의하고,
  그 근거로 **"DoF를 줄인다는 건 그 자유도를 prior가 대신 채운다는 뜻"** 이라는 원칙(M1.5/M3″)을
  추가했다. 아래 M0~M4/E0~E5는 최초안 그대로 유지, M1/M3/§0/§1/§5/§7/§8/§9/§10에 ADDENDUM
  내용이 삽입/치환됐다(각 절 앞에 표시). **아직 코드 실행 없음.**
- **실행 브랜치 전략 (사용자 요청, 신규)**: VIGS-SLAM 저장소(`/home/wosas/Desktop/26-1_RPM/gsProjects/VIGS-SLAM`)는
  현재 `main` 브랜치에서 exp63/64 변경이 **아직 커밋 안 된 채로 dirty**(`demo.py`,
  `vigs/gs_backend.py`, `vigs/track_frontend.py` 등, 2026-08-18 확인). 이 계획(M1b/M3′/M3″ 등)은
  init 파이프라인과 `map()`의 파라미터화 자체를 바꾸는 등 **기존 VIGS custom 함수 구조와 크게
  달라질 수 있는 변경이 많으므로**, exp63/64의 미완결 작업과 뒤섞이지 않도록 **새 git branch를
  파서 그 위에서 진행**한다(예: `exp65-backpolish-free`). 착수 전 우선 exp63/64의 현재 dirty
  변경분을 별도 커밋으로 정리(또는 최소한 stash)한 뒤 분기할 것 — 이후 M0 계측 삽입부터
  이 브랜치에서 시작.
- 선행 연결: [exp51](exp51_dense_supervision_plan.md)(incremental 25.29dB, 잔여 갭=depth-init
  바늘형 floater로 시각진단됨), [exp57](exp57_causal_background_polishing_plan.md)(strict
  streaming 27dB 1차 목표 달성, freeze800), [exp63](exp63_vigs_slam_robust_general_mapping_tuning.md)/
  [exp64](exp64_map_polish_time_share_governor.md)(map↔polish GPU 시간 배분이 예산-의존
  병목이라는 게 반복 확인됨 — §0 문제의식과 직접 연결, 특히 §0의 `available_backpolish_iters`가
  exp63의 `replay_time_scale` 스윕/exp64의 시간-비율 거버너가 다뤘던 바로 그 자원), carve loss
  트랙(`round8_carve_loss_design`→exp38~44d2, 33.799dB/먼지 234) — carve loss가 이미 배치에서
  검증된 자산임.

## 0. 논문 프레이밍

### 재작성된 핵심 주장 (2026-08-18 ADDENDUM-1, [§0 치환])

> **"실시간 GS-SLAM이 고품질 렌더링을 위해 전역 refinement 단계에 의존하는 한, 품질은
> 확보 가능한 iteration 예산에 종속되고 그 예산은 scene마다 통제 불가능하다.
> 우리는 dense correspondence가 제공하는 기하 사전지식으로 init과 map의 자유도를
> 제약해, 전역 refinement 단계 없이 목표 품질에 도달한다."**

기존 문장(아래)은 **여전히 유효한 fallback**이지만 주장이 약하다:

> "실시간 GS-SLAM의 렌더링 품질은 iteration 예산이 결정하는데, 그 예산은 scene마다
> 통제 불가능하게 달라진다. 우리는 예산을 늘리는 대신 iteration당 효율을 올려, 예산이
> 1/10로 줄어도 품질이 유지되는 mapping을 만든다."

위 재작성 문장이 성립하면 §9(리스크)의 "엔지니어링으로 읽힘" 리스크가 구조적으로
해소된다 — 모듈 추가가 아니라 **파이프라인 단계 하나를 제거**하는 것이기 때문.

- **문제 정의**: `PSNR = f(available_backpolish_iters)` 이고, `available_iters`는
  frontend/backend GPU 경쟁 때문에 scene 의존적(600~6000). **이건 이미 exp63의
  `replay_time_scale` 스윕(1.5/2.0/3.0 → 23.84/28.10/25.97dB, 역-U자형)과 exp64의
  시간-비율 거버너 실험에서 직접 관측된 현상과 정확히 같은 축이다.**
- **기존 접근**: 예산 확보(frontend 축소, map freeze) → per-scene 튜닝 → 일반화 실패.
  (exp53/54/56이 frontend·mapping 속도를, exp63/64가 스케줄링을 각각 다뤘지만 전부
  "주어진 예산 안에서 어떻게 배분할까"였음.)
- **우리 접근**: 예산 수요 자체를 줄인다 → **더 나아가 이 ADDENDUM에서는 예산이 필요한
  단계(backpolish) 자체를 없앤다.**
  - **(A) 구조적 사전지식으로 DoF 축소** — DROID dense correspondence의 위상(topology)에
    Gaussian을 묶음(M3), 또는 각 Gaussian의 이동 방향 자체를 제약(M3′/M3″)
  - **(B) free-space 사전지식으로 잘못 놓인 Gaussian을 *지우지 않고 이동*** — carve loss
    복귀(M4)
  - **(C) appearance는 iteration이 아니라 closed-form solve** — visibility-weighted LS(M2,
    현재는 C0 실패 시의 보험으로 후순위)

### DoF 축소는 곧 prior로의 위임이다 (2026-08-18 ADDENDUM-2, [§0 추가])

> **"DoF를 줄인다는 건 '그 자유도가 담당하던 값을 prior가 대신 결정한다'는 뜻이다.
> 따라서 우리 방법의 PSNR 상한은 곧 prior의 품질 상한이고, prior가 틀린 곳에서
> 제약은 곧 오차가 된다."**

이 문장이 함의하는 것:

1. **prior 품질을 먼저 감사(audit)해야 한다** — 안 하면 M3′ 실패 시 원인 규명 불가
   (제약이 나쁜 건지, prior가 나쁜 건지 구분 안 됨) → **M1.5**
2. **제약 강도는 균일하면 안 된다** — prior 신뢰도에 비례해야 한다 → **M3″, 핵심 novelty 후보**

### Claim 후보 (재배치, 강도 순, ADDENDUM-1 [§0 치환])

| ID | 내용 | 변경 |
|---|---|---|
| **C0 (신규, 최상위)** | backpolish(전역 refinement)를 완전히 끈 상태에서, 기존 backpolish-포함 파이프라인의 품질에 준하는 PSNR 달성 | **신규 — 메인 주장** |
| C1 | 동일 iteration 예산에서 baseline 대비 PSNR 우위 | 유지(C0 실패 시의 fallback 주장) |
| C2 | 단일 하이퍼파라미터 세트로 전 scene 동작 | **격상** — backpolish가 없으면 freeze 타이밍·시간배분 파라미터 자체가 사라진다. C2가 C0의 **부산물**이 됨 |
| C3 | geometry(depth L1/normal consistency) 동시 개선 또는 유지 | 유지 |
| C4 | frontend 부하가 변해도 성능 저하가 완만함(robustness to compute contention) | **재해석** — backpolish가 없으면 frontend↔backend GPU 경쟁의 한 축이 소멸. E3의 성격이 "완화"에서 "제거"로 바뀜 |

> **주장 순서 주의**: C0을 못 만들면 논문이 죽는 게 아니라 C1으로 내려앉는다. 그래서
> **M2(closed-form solve)는 C1 라인의 보험으로 계속 살려둔다**(§7 일정에서 W7로 후순위
> 이동, C0 실패 시 즉시 최우선 복귀).

## 1. Reference 저장소 목록

`refs/` 폴더에 clone. 각각 **무엇을 훔칠지**를 명시. 전부 읽지 말고 지정된 파일만.

### 1.1 필수 — 직접 코드 이식 (원안)

| Repo | URL | 훔칠 것 |
|---|---|---|
| **Splat-SLAM** | `github.com/google-research/Splat-SLAM` | DROID + 3DGS 결합의 정석. keyframe 관리, depth→Gaussian 초기화, proxy depth 활용 방식. **VIGS custom과 구조 비교용 1순위** |
| **DROID-Splat** | `github.com/ChenHoy/DROID-Splat` | 같은 조합의 다른 구현. **2DGS / MCMC 백엔드를 이미 붙여봄** → 우리가 2D surfel로 갈 때 그대로 참고 |
| **2D Gaussian Splatting** | `github.com/hbb1/2d-gaussian-splatting` | surfel 표현 + rasterizer. depth/normal이 alpha-blending "expected depth" 모호성 없이 나옴 |
| **SuGaR** | `github.com/Anttwo/SuGaR` | mesh에 Gaussian 바인딩하는 파라미터화(`bound gaussians` 부분). **삼각형 위 barycentric 파라미터화 코드가 핵심** |
| **Scaffold-GS** | `github.com/city-super/Scaffold-GS` | anchor 기반 DoF 축소. anchor→neural Gaussian 디코딩. **DoF 축소가 수렴을 얼마나 가속하는지의 레퍼런스** |

### 1.1b 필수 등급으로 승격/추가 — backpolish-free 직접 대응 (2026-08-18 ADDENDUM-1, [§1 추가])

| Repo / Paper | 위치 | 왜 필요한가 |
|---|---|---|
| **PAGaS**(Pixel-Aligned 1DoF GS) | arXiv 2604.22129 | ⚠️ **가장 가까운 선행연구.** world space에서 고자유도 3D Gaussian을 최적화하는 대신, 픽셀당 Gaussian 1개를 두고 **back-projected camera ray 방향으로만 움직이도록 제약**해 문제를 순수 2D 최적화로 재정식화. occlusion-aware rasterizer도 자체 제안. **M3′ 설계의 직접 청사진이자 최대 scoop 위험** |
| **RGS-SLAM** | `github.com/Breeze1124/RGS-SLAM`(arXiv 2601.00705) | ⚠️ **직접 경쟁자.** residual-driven densification을 dense correspondence 기반 one-shot triangulation init으로 **대체**. 고정 개수 anisotropic Gaussian을 한 번에 생성하고 이후엔 pose와 Gaussian 파라미터만 refine → stationary objective. 수렴 ~20% 가속, TUM/Replica. **"우리도 init으로 densification을 대체한다"는 부분이 겹침** |
| **GaussianImage** | `github.com/Xinjie-Q/GaussianImage`(ECCV 2024) | **M1b(2D 단계)의 도구.** 2D Gaussian 하나당 파라미터 8개(위치·공분산·색)만 쓰고, alpha blending/정렬 대신 accumulated summation 렌더링 → fitting 5배 빠름, GPU 메모리 1/3. **키프레임당 2D 최적화를 실시간 예산 안에 넣을 수 있는 유일한 현실적 후보** |
| **Augmented Radiance Field**(Inverse Gaussian Splatting) | arXiv 2602.19916 | **"2D 맞추고 → 3D로 올린다"의 유일한 기존 구현.** 각 시점에서 2D primitive를 최적화한 뒤 world space로 back-project. **rotation/scale을 Weighted PCA로 결정**하고 scale을 별도 캘리브레이션. 우리 M1b의 lift 단계 레시피를 그대로 참고 |
| **3DGS-SLAM Survey** | arXiv 2602.04251 | §C "Reconstruction Speed"가 **Gaussian init 가속을 하나의 하위분야로 정리**해둠(MGSO/GPS-SLAM: DSO 포인트·SDF 기반 dense prior init, MemGS: Patch-Grid 샘플링). related work 골격을 여기서 그대로 가져올 것 |

**GaussianImage++ 주의사항**: GaussianImage는 densification 메커니즘이 없어 Gaussian
개수를 내용에 맞게 조절하지 못한다는 한계가 지적됨(GaussianImage++, AAAI). 우리는
**DROID depth/normal이 이미 배치 정보를 주므로** densification 대신 **기하 기반 배치**를
쓴다 — 이게 우리 쪽 이점이자 논문에 쓸 문장.

### 1.1c Prior 관련 신규 — M1.5/M3″ 대응 (2026-08-18 ADDENDUM-2, [§1 추가])

| Paper | 위치 | 훔칠 것 |
|---|---|---|
| **DN-Splatter** | WACV 2025(openaccess) | **gradient-aware depth loss** — image gradient 큰 엣지에서 depth 정규화를 낮추고 저텍스처 영역에서 강화. 로그 페널티가 선형·이차보다 부드러운 재구성. **우리 `c`(신뢰도) 설계의 직접 레시피.** 초기화도 back-projected sensor depth 100만 점 기준 |
| **Metric3D v2** | arXiv 2404.15506 / TPAMI | metric depth + surface normal 동시 제공. joint depth-normal 최적화 모듈. mono-SLAM scale drift 완화 사례 |
| **ConfidentSplat** | arXiv 2509.16863 | DSPO 레이어에서 multi-view 기하와 mono prior를 scale/shift로 정렬하는 방식. **VIGS와 구조가 거의 같아서 이식 비용 낮음** |
| **VarSplat** | CVPR 2026 | splat별 variance 학습 → per-pixel uncertainty를 tracking 가중치로. **우리와 가장 가까운 confidence 사용례이자, "loss weight에 머물렀다"는 대조군** |
| **DSINE** | Bae & Davison 2024 | mono normal 대안. per-pixel ray direction 기반 활성화, 이웃 normal 간 상대 회전 학습 |

### 1.2 참고 — 아이디어/수치 비교용

| Repo / Paper | URL | 용도 |
|---|---|---|
| **3DGS-LM** | `github.com/lukasHoel/3DGS-LM` | ADAM→LM 교체. "ADAM 6000/8000 iter 후 LM으로 전환하면 같은 품질에 더 빨리 도달" — 우리 backpolish를 2차 최적화로 바꾸는 옵션(C0 실패 시 fallback 라인). CUDA Jacobian 캐시 커널 구조 참고 |
| **FastGS** | `github.com/fastgs/FastGS` | 100초 학습. multi-view consistent densification + targeted pruning. Scaffold-GS/Mip-splatting 등 여러 백본에 붙는 형태. **densify 정책 대안** |
| **HI-SLAM2** | `hi-slam2.github.io` | mono prior + learning-based dense SLAM. proxy depth로 init하고 나중에 pose와 재결합 |
| **S3LAM** | arXiv 2507.20854 | SLAM에서 2D surfel + adaptive surface rendering. surfel Jacobian 유도 |
| **Instant Colorization of GS** | `github.com/dlieber01/Instant-Colorization-of-Gaussian-Splats` | visibility-weighted least squares로 색을 closed-form solve. gradient descent 대비 최대 1자릿수 speedup. (C) 방향의 직접 근거 |
| **FlashSplat** | arXiv 2409.08270 | alpha blending이 label에 대해 선형 → closed-form. 이론적 근거 |
| **TIDI-GS** | arXiv 2601.09291 | floater pruning 최신 baseline. **carve loss의 비교군** |
| **StableGS** | `github.com/…/StableGS`(arXiv 2503.18458) | cross-view depth consistency로 floater 제거. carve loss 비교군 2 |

### 1.3 서베이 (주기적으로 재확인, scoop 방지)

- `github.com/KwanWaiPang/Awesome-3DGS-SLAM`
- `github.com/3D-Vision-World/awesome-NeRF-and-3DGS-SLAM`
- `mrnerf.github.io/awesome-3D-gaussian-splatting`

> **주의**: 2D Gaussian Primitive SLAM(Neurocomputing 2026), EGG-Fusion(SIGGRAPH Asia 2025),
> RGS-SLAM(one-shot dense init), MDGS-SLAM 등이 인접 영역. **매주 1회 이 리스트 diff를
> 확인**하고 겹치면 즉시 프레이밍 조정.

### 1.4 clone 스크립트

```bash
mkdir -p refs && cd refs
for r in \
  google-research/Splat-SLAM \
  ChenHoy/DROID-Splat \
  hbb1/2d-gaussian-splatting \
  Anttwo/SuGaR \
  city-super/Scaffold-GS \
  lukasHoel/3DGS-LM \
  fastgs/FastGS \
  dlieber01/Instant-Colorization-of-Gaussian-Splats ; do
  git clone --depth 1 "https://github.com/$r.git"
done
# ADDENDUM-1: backpolish-free 직접 대응
git clone --depth 1 https://github.com/Xinjie-Q/GaussianImage.git
git clone --depth 1 https://github.com/Breeze1124/RGS-SLAM.git
# PAGaS / Augmented Radiance Field / 3DGS-SLAM Survey는 arXiv 논문만 존재 — 코드 없으면 PDF만 refs/papers/에 보관
# ADDENDUM-2: Metric3D v2 / DN-Splatter 코드는 라이선스·weight 배포 방식 확인 후 개별 추가
```

`refs/NOTES.md`에 repo별로 **"우리가 참고한 파일 경로 + 함수명 + 왜"** 를 3줄씩 기록.
나중에 related work가 그대로 나온다.

## 2. 계측 인프라 (M0) — 여기부터 시작 (원안 그대로 유지)

**아무 아이디어도 구현하기 전에**, 현재 VIGS custom에서 다음을 로깅할 수 있어야 한다.
이게 없으면 이후 모든 실험이 해석 불가.

> 우리는 이미 부분적 자산이 있다: exp56 Phase 5의 `map_call` 로그(iters/n_view/n_gauss별
> 회귀분석, `scripts/analysis/exp56_fit_timing_model.py`)와 exp63/64의 `VIGS_TIMING_LOG`
> 상시 계측(`_Sect`, 그리고 exp64가 추가한 always-on wall-clock 타이머)이 §2.1의
> `per_frame`/`per_iteration` 항목 상당수를 이미 커버한다. M0는 이걸 재사용하되
> **파라미터 그룹별 이동량(Δxyz/Δscale/Δrot/Δopacity/ΔSH)** 로깅만 신규로 필요하다 —
> 이건 지금까지 어떤 exp에서도 계측한 적 없음.

### 2.1 로깅해야 할 것

```
per_iteration:
  - global_step, wall_clock_ms, thread_id (frontend/map/backpolish)
  - psnr_eval (N iter마다), loss_photo, loss_depth, loss_normal
  - n_gaussians
  - mean |Δxyz|, mean |Δscale|, mean |Δrot|, mean |Δopacity|, mean |ΔSH|
    ^ 파라미터 그룹별 이동량. **(C) 방향의 성패를 여기서 판단**
per_frame:
  - frontend_gpu_ms, map_gpu_ms, backpolish_gpu_ms, idle_ms
  - backpolish_iters_completed_cumulative
per_scene:
  - total_backpolish_iters, final PSNR/SSIM/LPIPS, ATE, depth_L1
```

### 2.2 M0 Acceptance Contract

- [ ] 임의 scene에서 `budget_curve.csv` 생성 → x축 `backpolish_iters`, y축 PSNR
- [ ] 최소 5개 scene에서 이 곡선을 뽑아 겹쳐 그림 → **scene별 예산 편차가 실제로
      문서화됨**(논문 Fig.1 후보)
- [ ] 파라미터 그룹별 이동량 로그가 나옴

### 2.3 M0에서 나올 결정

> **backpolish 동안 `Δxyz`가 지배적인가, `ΔSH/Δopacity`가 지배적인가?**
> - SH/opacity 지배 → **(C) closed-form appearance solve가 본체**. 가장 싸고 확실한 승부수.
> - xyz 지배 → **(A)+(B) 구조/위치 사전지식이 본체**.
> - 둘 다 → (A)로 위치를 잡고 (C)로 색을 풀고, 남는 iter만 자유 최적화 = 3단 구조.

## 3. 구현 단계

### M1 — Init 품질 상한 측정 (2026-08-18 ADDENDUM-1 [§3 치환]으로 3+1단계 분해)

원안의 M1("iter-0 PSNR 측정" 하나)은 **naive lift 하나만** 재고 있었다. ADDENDUM-1이
이걸 M1a/M1b/M1c 세 단계로, ADDENDUM-2가 M1a와 M1b 사이에 **M1.5(prior 감사)** 를
추가로 끼워 넣었다. 목표는 **"어느 단계에서 몇 dB이 나오는지"의 계단표**를 만드는 것.

#### M1a — Naive lift (원안 M1 그대로, 계단의 바닥)

**질문**: DROID dense correspondence + normal만으로 Gaussian을 깔면 iter 0에서 PSNR
몇인가?

- 각 keyframe의 dense disparity → unproject → 3D point
- normal map으로 각 point의 orientation 설정
- scale = 인접 픽셀 간 거리 기반(또는 depth/focal 비례)
- color = 해당 픽셀 RGB, opacity = 고정값(예: 0.9), SH degree 0
- **최적화 0 iter 상태에서 렌더링 → PSNR 측정**

> 이 숫자 하나가 전체 방향의 성패를 가름. **최우선 실행.**
>
> 참고할 기존 수치: exp37(OpenMAVIS 트랙, dense confidence+monodepth init 148,564pts,
> plateau 없음)은 **plateau 없는 순수 init만으로 32.621dB@30k**를 냈지만 이건 배치
> 30k-iter 최종 수치라 iter-0과는 다른 질문이다. incremental 쪽 exp51은 SLAM+PPM
> init에서 held-out 25.29dB(수렴 후)까지 갔지만 iter-0 자체를 측정한 적은 없음 —
> M1a는 정말 처음 재는 숫자.

#### M1.5 — Prior 감사(Prior Audit) (2026-08-18 ADDENDUM-2 [§3 신규], M1a와 M1b 사이 삽입)

M1a와 M1b **사이에** 삽입. 측정만 하고 구현은 없음. 반나절이면 끝나지만 없으면 이후
전부 눈감고 감.

**감사 항목**:

| prior | 소스 후보 | 측정 지표 | 왜 |
|---|---|---|---|
| **depth** | DROID disparity / mono(Metric3D v2) / 둘의 융합 | GT 대비 abs-rel, δ<1.25, **그리고 픽셀별 오차 분포** | ray 위 위치 `t`를 이게 결정 |
| **normal** | depth로부터 유한차분 / mono normal(Metric3D v2, DSINE) | 각도 오차 평균·중앙값, **11.25°/22.5°/30° 이하 비율** | Gaussian rotation을 이게 결정 |
| **confidence** | DROID flow covariance / mono 모델 uncertainty | **오차와의 상관계수** | 신뢰도가 실제 오차를 예측하는지가 M3″의 전제 |
| **scale** | 인접 픽셀 간 3D 거리 / depth·focal 비례 | 렌더 후 hole 비율, 과중첩 비율 | Gaussian 크기를 이게 결정 |

**반드시 볼 것 — 오차의 공간 분포**: 전체 평균 오차는 쓸모없다. 필요한 건:
- depth 오차가 큰 곳이 **어디인가**(텍스처 없는 벽 / 깊이 불연속 경계 / 반사면 / 원거리)
- normal 오차가 큰 곳이 depth 오차 큰 곳과 **겹치는가 분리되는가**
- **DROID confidence가 낮은 곳과 실제 오차가 큰 곳이 일치하는가** → 일치하지 않으면
  confidence를 제약 강도 결정에 쓸 수 없다. 대안 신호를 찾아야 함

**mono prior 도입 판단**: Metric3D v2는 metric depth와 surface normal을 **한 모델에서
동시에** 내놓고, depth 데이터를 써서 normal 추정을 개선하는 joint depth-normal
최적화 모듈을 갖는다. 또한 monocular SLAM의 scale drift를 완화해 metric-scale dense
mapping을 돕는다고 명시. → **depth와 normal을 따로 두 모델 돌리는 것보다 일관성·비용
양쪽에서 유리**. 다만 실시간 예산에 들어가는지는 별도 확인. Aria는 stereo+IMU라 metric
scale이 이미 있으므로, mono depth는 **scale이 아니라 저텍스처 영역 보완** 용도로만
쓴다. ConfidentSplat이 DSPO 레이어에서 multi-view geometry와 mono prior를 scale/shift
파라미터로 정렬하는 방식이 그대로 참고 대상.

**M1.5 Acceptance**:

- [ ] depth/normal 오차 히트맵이 나옴(논문 Fig 후보)
- [ ] confidence ↔ 실제 오차 상관계수 산출. **|r| < 0.3이면 M3″ 설계 변경 필요**
- [ ] "DROID만" vs "DROID+mono 융합" 두 조건의 normal 각도 오차 비교 → mono 도입 여부 결정

#### M1b — 2D 최적화 후 lift (2026-08-18 ADDENDUM-1 [§3 치환] 신설, ADDENDUM-2 [§3 추가]로 보강)

**아이디어**: 3D에서 헤매지 말고, 키프레임 이미지 평면에서 먼저 2D Gaussian으로
이미지를 정확히 맞춘 뒤 depth/normal로 3D에 올린다. 2D 단계는 occlusion도
view-dependency도 없어 **최적화 문제가 훨씬 쉽고 빠르다**.

**절차**:

1. 키프레임 RGB에 대해 2D Gaussian 집합을 fit(GaussianImage 방식: 위치·2D 공분산·색)
   - 초기 배치는 랜덤이 아니라 **DROID depth의 gradient / edge map 기반**으로 배분
   - 반복 횟수는 실시간 예산에 맞춰 상한(예: 키프레임당 수십 iter)
2. 각 2D Gaussian을 3D로 lift — **prior 전면 투입 버전(ADDENDUM-2가 원안 표를 교체)**:

   | Gaussian 파라미터 | prior 없이(원안) | **prior 활용(교체안, 채택)** |
   |---|---|---|
   | 위치 | depth로 unproject | 동일 + **confidence 낮은 픽셀은 아예 생성 안 함**(밀도를 신뢰도로 조절) |
   | 회전 | 카메라 평면 평행(기본값) | **normal map으로 표면에 눕힘** ← 필수 |
   | 스케일 | depth/focal 비례 등방 | 2D fit 공분산 × depth/focal, **normal 방향으로는 납작하게(surfel화)**, 접평면 방향은 2D 공분산 유지 |
   | opacity | 고정 0.9 | **confidence 비례** — 불확실한 영역은 낮게 시작해 후속 최적화가 지우기 쉽게 |
   | 색 | 픽셀 RGB | 2D fit 결과(SH deg 0) |

   > ⚠️ **normal 없이 lift하면 안 된다.** SurfelSplat이 지적하듯, feed-forward로 예측한
   > surfel은 normal이 실제 표면이 아니라 **이미지 평면에 평행하게 정렬되는 실패 모드**가
   > 있고, 그러면 surfel이 한 픽셀 영역만 덮어 covariance를 학습할 정보가 부족해진다.
   > 우리는 학습이 아니라 기하로 normal을 주므로 이 함정을 피할 수 있는데, **그게 곧
   > 우리 이점**이다.
   - rotation/scale 결정은 Augmented Radiance Field의 **Weighted PCA 캘리브레이션** 참고
3. **lift 직후, 3D 최적화 0 iter에서 PSNR 측정**

**측정해야 할 핵심 수치 — "lift loss"**:

```
Δ_lift = PSNR(2D fit, 원본 이미지)  −  PSNR(lift 후 3D 렌더, 같은 뷰)
```

같은 뷰에서 재렌더했는데 떨어진 만큼이 **2D→3D 변환에서 잃는 양**이다.

- 원인 후보: alpha blending 의미 변화(GaussianImage는 정렬 없는 누적합을 씀), depth
  불연속 경계에서 하나의 2D Gaussian이 전경/배경 픽셀을 함께 덮는 문제(Augmented
  Radiance Field가 클러스터링으로 분리한 바로 그 문제), normal 추정 오차.
- **Δ_lift가 크면 M1b 전략 자체가 무의미**하므로 이 숫자를 먼저 확인.

**추가 측정 — normal ON/OFF ablation**(ADDENDUM-2): lift 시 normal 적용 유무만 바꿔
iter-0 PSNR 비교. 이 차이가 곧 "normal prior의 가치" 수치. 논문에 그대로 들어감.

#### M1c — Multi-view 누적 시의 열화 측정 (ADDENDUM-1)

M1b는 키프레임 단독 기준. 여러 키프레임의 lift 결과를 합치면 중복·불일치로 PSNR이
떨어진다.

- **held-out 뷰**에서 측정(train 뷰가 아님)
- 중복 제거 정책 2안 비교: (i) depth-기반 중복 억제 (ii) 무처리
- StreamGS가 프레임 간 대응으로 중복 Gaussian을 병합해 밀도를 낮춘 사례 참고

#### M1 통합 Acceptance Contract (원안 교체)

| 항목 | 통과 기준 | 실패 시 |
|---|---|---|
| M1a iter-0 PSNR | ≥ 15dB | DROID depth 자체 병목 → mono-depth 융합 선행 |
| M1b Δ_lift | ≤ 3dB | 2D→3D 변환 손실 지배 → **M1b 폐기, M1a+M3′로 축소** |
| M1b held-out iter-0 | **M1a 대비 +3dB 이상** | 2D 단계가 값을 못 함 → 폐기 |
| M1c multi-view 열화 | 단일뷰 대비 -5dB 이내 | 중복 병합 정책 필요 |

> **이 4개 숫자가 계단표를 만든다.** 논문 Table 1 후보이자, C0 달성 가능성의 조기 판정.
> (원안 M1의 단일 게이트 "≥18dB"는 이 4단계 계약으로 대체됨 — M1a 자체의 통과선은
> 15dB로 다소 낮아졌고, 대신 M1b/M1c가 추가 관문을 건다.)

### M2 — (C) Closed-form appearance solve (원안 그대로, 우선순위만 변경)

> **우선순위 변경(ADDENDUM-1)**: C0(backpolish 제거) 검증 순서상 M2는 §7 일정에서
> W2→W7로 후순위 이동. M2는 "backpolish를 효율화"하는 물건인데 backpolish 자체를
> 없애는 게 목표라면 최우선이 아니다. **단, E6에서 C0가 실패해 C1로 후퇴하면 M2가
> 즉시 최우선으로 복귀**한다.

가장 구현 비용이 낮고 효과가 즉시 보이는 것부터.

**아이디어**: geometry(xyz, scale, rot)를 고정하면, 렌더링은 각 Gaussian의 색에 대해
**선형**(alpha blending의 가중합). → normal equation으로 한 번에 푼다.

**구현**:

1. rasterizer에서 각 픽셀에 대한 per-Gaussian blending weight `w_ij` 추출(기존
   backward에서 나오는 값 재활용)
2. Gaussian `j`에 대해 `A_j = Σ_i w_ij²`, `b_j = Σ_i w_ij · residual_i` 누적
3. `c_j ← c_j + b_j / (A_j + λ)` — Jacobi 방식(전체 정규방정식을 풀지 않고 대각 근사)
4. 2~3회 반복(occlusion/blending 결합 때문에 완전 선형은 아님)

**Acceptance (M2)**:

- [ ] 동일 geometry에서, ADAM으로 색만 500 iter 돌린 것과 solve 1회의 PSNR 비교 →
      **solve가 동등 이상**
- [ ] solve 1회 비용 ≤ ADAM 20 iter 비용
- [ ] 통과 시: backpolish 스케줄을 `[solve → geometry ADAM k iter → solve → …]` 로 교체

> 근거: FlashSplat이 alpha blending의 label 선형성으로 closed-form 최적해를 증명했고,
> Instant Colorization이 visibility-weighted LS + normal equation으로 gradient descent
> 대비 최대 10배 speedup을 보고했다.
>
> 우리 코드 기준 침투 지점: `background_polish_step()`이 이미 rasterizer의 per-pixel
> blending weight에 접근 가능한 구조라(그 forward pass를 그대로 쓴다), M2 구현은 별도
> rasterizer 없이 기존 `render()` 호출 안에서 weight를 뽑아내는 정도로 침습 범위가
> 작을 가능성이 높음 — 단, 실제 CUDA 커널이 이 weight를 중간 버퍼로 노출하는지는 아직
> 미확인(M2 착수 시 첫 확인 항목).

### M3 — (A) Topology-anchored Gaussians (원안 그대로, M3′/M3″와 직교 축으로 병존)

**아이디어**: DROID dense correspondence는 이미 픽셀 간 이웃 관계(=위상)를 준다.
이걸 삼각형 패치로 묶고, Gaussian을 패치에 종속시켜 최적화 변수를 줄인다.

**설계(3안, 비용 오름차순)**

| 안 | 내용 | DoF |
|---|---|---|
| **A1: Anchor-offset** | keyframe depth를 격자로 다운샘플 → anchor point. 각 anchor가 K개 Gaussian을 관장하고, Gaussian은 anchor 상대 offset만 가짐. anchor만 최적화 | N/K |
| **A2: Surfel-on-patch** | 픽셀 삼각화 → 각 삼각형에 2D Gaussian(surfel) 1개. 위치·회전은 삼각형 꼭짓점이 결정, Gaussian은 색/불투명도만 | 꼭짓점 수 |
| **A3: Hierarchical release** | A2로 시작 → 수렴 후 residual 큰 영역만 바인딩 해제해 자유 3D Gaussian으로 승격 | 적응적 |

**권장**: **A1 먼저**(Scaffold-GS 코드 거의 재사용 가능, rasterizer 수정 불필요). A2는
2DGS rasterizer 교체가 필요해 리스크 큼. **A3가 논문의 최종 그림**이지만 A1/A2 검증 후.

> ⚠ 명명 주의: 이 카드의 "A2"(topology anchor 설계안)는 exp63의 "축 A2"(트래킹
> `motion_filter.thresh=2.6`+`iters1=2` 레시피, 305 +7.00dB)와 **완전히 다른 개념**이다.
> 우연히 같은 이름이 겹쳤을 뿐 — 실행 로그/커밋에서 "A2"를 볼 때 어느 카드인지 반드시
> 문맥으로 구분할 것.

**Acceptance (M3)**:

- [ ] 동일 iteration 예산 500 / 1000 / 2000에서 baseline 대비 PSNR 우위
- [ ] Gaussian 수가 baseline 대비 감소(메모리/렌더 속도 부가 이득)
- [ ] **주의**: DoF 축소는 상한을 낮출 수 있음 → 6000 iter 지점에서 baseline보다
      크게 낮으면 A3(해제 단계) 필수

### M3′ — DoF-제약 map(): Ray-Constrained Optimization (2026-08-18 ADDENDUM-1 [§3 신규])

기존 M3(A1 anchor-offset)와 **별개 축**. A1은 "여러 Gaussian을 anchor로 묶기"이고,
M3′는 **"각 Gaussian의 움직임 방향 자체를 제약하기"**다. 둘은 직교하므로 조합 가능.

**설계**: DROID dense correspondence가 각 픽셀의 depth를 주므로, Gaussian은 이미
**올바른 ray 위**에 있다. 틀린 건 주로 **ray 위에서의 거리**다. 따라서:

- **R1(1-DoF ray)**: Gaussian 중심을 `p = o + t·d` 로 파라미터화하고 **`t`만 학습**.
  방향 `d`는 픽셀에서 고정. → 위치 자유도 3 → 1
- **R2(normal-locked)**: rotation을 normal map으로 고정, scale은 등방 1-DoF만.
  → 회전 4 + scale 3 → 1
- **R3(선택적 해제)**: photometric residual이 큰 영역만 제약 해제해 자유 3D Gaussian으로
  승격. 기존 M3의 A3와 동일 사상(M3″에서 이 R3가 residual 대신 confidence 기반으로
  대체됨).

전체 DoF: 3(xyz)+4(rot)+3(scale)+1(opacity)+3(SH0) = **14 → R1+R2 적용 시 6**

**근거 및 차별화**: PAGaS가 정확히 이 제약(픽셀당 Gaussian 1개 + back-projected ray
방향으로만 이동, 구형 Gaussian으로 rotation 자명화, depth 의존 scale)을 도입해
재구성을 순수 2D 최적화로 재정식화했다. 다만 PAGaS의 목표는 **depth refinement / mesh
품질**이고 뷰를 하나씩 처리하는 오프라인 방식이다.

> **우리 차별화 문장**: PAGaS는 제약된 자유도를 *기하 정밀도*를 위해 썼고, 우리는 같은
> 제약을 *실시간 예산 하의 렌더링 수렴 속도*를 위해 쓴다. 그리고 SLAM 루프 안에서
> 온라인으로, 전역 refinement 없이 쓴다.

⚠️ **PAGaS가 occlusion-aware rasterizer를 별도로 만들어야 했다는 점**은 경고 신호다.
제약된 Gaussian은 occlusion 처리가 기존 rasterizer와 안 맞을 수 있으므로, M3′ 착수 시
**첫 확인 항목**으로 둘 것.

**M3′ Acceptance Contract**:

- [ ] R1만 적용: 동일 iteration에서 baseline 대비 수렴 속도(목표 PSNR 도달 iter 수) 단축
- [ ] R1+R2: Gaussian당 optimizer state 메모리 감소 확인
- [ ] **상한 확인**: 충분히 큰 iteration(6000)에서 baseline 대비 -2dB 이내. 초과 시
      R3(해제) 없이는 진행 불가
- [ ] map() 1회 호출 wall-clock이 baseline 대비 증가하지 않음(제약이 오히려 느리면 무의미)

### M3″ — Confidence-Adaptive DoF Allocation (2026-08-18 ADDENDUM-2 [§3 신규], 핵심 novelty 후보)

M3′(ray 제약)의 확장. R3(선택적 해제)를 **residual 기반이 아니라 prior confidence
기반**으로 바꾼다.

**설계**: 각 Gaussian의 자유도를 prior 신뢰도 `c ∈ [0,1]` 에 따라 **연속적으로 할당**:

| 신뢰도 | 위치 | 회전 | 스케일 | 총 DoF |
|---|---|---|---|---|
| **높음**(c > τ_hi) | ray 위 `t` 1-DoF, 초기값에 강한 prior 페널티 | normal로 **고정** | 등방 1-DoF | ~6 |
| **중간** | ray 위 `t`, 페널티 약함 | normal 중심 소각도 편차 허용 | 이방 2-DoF | ~9 |
| **낮음**(c < τ_lo) | **자유 3-DoF** | 자유 | 자유 | 14(기존) |

구현은 하드 스위치가 아니라 **prior anchoring penalty의 가중치**로:

```
L_prior = Σ_g  c_g · [ λ_t ‖t_g − t_g^prior‖²  +  λ_n (1 − ⟨R_g e₃, n_g^prior⟩)  +  λ_s ‖log(s_g/s_g^prior)‖² ]
```

`c_g`가 0이면 제약이 사라져 자유 3DGS와 동일. → **하드 파라미터 τ 없이 연속 조절**,
그리고 이게 §C2(scene 간 파라미터 불변성) 주장을 강화한다.

**신뢰도 `c` 의 재료**(M1.5 결과로 선택):

- DROID flow covariance(RAFT 계열 대응의 confidence)
- 이미지 gradient — DN-Splatter가 **image gradient가 큰 edge 영역에서 depth
  regularization을 낮추고**, 광도 손실만으로 어려운 매끄러운 저텍스처 영역에서 더
  강하게 거는 gradient-aware depth loss를 씀. 우리 `c` 설계의 직접 레시피
- depth·normal 상호 일관성(depth에서 유도한 normal vs 예측 normal의 각도차)
- 다중뷰 관측 횟수

**선행연구와의 결정적 차이 — 논문에 한 문단으로 써야 함**: confidence-aware GS-SLAM은
이미 여럿 있다:

- **ConfidentSplat**: multi-view geometric 제약과 학습된 mono prior의 confidence 기반 융합
- **VarSplat**: splat별 appearance variance를 함께 학습, 렌더된 per-pixel uncertainty를
  tracking·registration의 **가중치**로 사용. depth 불연속·occlusion 경계에서 높은
  불확실성 관측
- **MCGS-SLAM**: 위치 안정성·불투명도·형상 품질·공간 중요도·엣지 특이성으로 Gaussian
  신뢰도 추정 후 **confidence-based weighting**
- **CDGS**: confidence-aware depth **regularization**
- **RGS-SLAM**: confidence-weighted correspondence로 초기화하고 이후 topology를 고정한
  채 mean/covariance/opacity/color를 refine

> **공통점: 전부 confidence를 loss weight 또는 init 필터로 쓴다. 파라미터화(자유도
> 구조) 자체를 confidence로 바꾼 사례는 없다.**

이게 gap statement다. 우리 주장:

> "기존 연구는 confidence로 *얼마나 믿을지*를 정했다. 우리는 confidence로 *무엇을
> 학습할지*를 정한다 — 신뢰할 수 있는 곳에서는 파라미터를 아예 제거해 최적화 비용을
> 지불하지 않는다."

이 프레이밍이면 **연산 예산 축과 자연스럽게 연결**된다. loss weighting은 비용을 안
줄이지만, DoF 제거는 optimizer state·gradient 계산·수렴 iter를 전부 줄인다.

**M3″ Acceptance**:

- [ ] 균일 제약(M3′) 대비 동일 iteration에서 PSNR 우위
- [ ] 6000 iter 상한에서 **자유 3DGS와의 격차가 M3′보다 작음**(제약의 천장 문제 완화 확인)
- [ ] `c` 분포 시각화 — 저텍스처 벽은 강제약, 깊이 불연속 경계는 자유, 라는 그림이
      나와야 함. 안 나오면 `c` 설계 실패
- [ ] optimizer state 메모리·iter당 시간이 실제로 감소(안 줄면 "비용을 지불하지 않는다"는
      주장이 거짓)

### M4 — (B) Carve loss 복귀 (원안 그대로)

기존 carve loss를 **floater 제거 방법이 아니라 수렴 가속 방법으로 재포지셔닝**.

**논리**: SLAM point까지의 ray는 free-space다. 잘못 놓인 Gaussian을 *지우면* 그
자리를 다시 채우는 데 iter가 든다. *옮기면* 이미 학습된 색/스케일을 재활용한다 →
**iter 절약**.

**3요소 각각을 ablation 가능하게 분리**:

- B1: free-space pruning(지우기)
- B2: free-space opacity 억제(누르기)
- B3: **anchor force field로 표면 방향 이동** ← 차별점

> 우리 기존 carve loss(exp38~44d2, `round8_carve_loss_design`)의 3요소(soft/prune/gate
> + force)는 이미 B1/B2/B3와 거의 1:1로 대응한다 — **B1/B2는 재구현이 아니라 기존
> `carve_loss.py`의 prune/gate 항을 그대로 재사용 가능할 것으로 보임.** B3(force)도
> exp40a("3D force 부활 실증, 무비용")로 이미 배치에서 검증됐다. **새로 필요한 건
> "수렴 가속" 프레이밍에 맞춘 재평가뿐** — 즉 M4의 실제 신규 작업은 코드가 아니라
> **같은 메커니즘을 "동일 예산에서 PSNR 우위"라는 다른 지표로 재측정하는 것**.
> exp55 Phase3(carve loss 온라인 근사, `exp55_score_carve_vigs.py`)가 이미 incremental
> 환경에서의 carve 이식 사례이므로 그 코드/지표를 먼저 확인하고 시작할 것.

**Acceptance (M4)**:

- [ ] B3만 켰을 때 vs B1만 켰을 때 → **동일 예산에서 B3가 우위**임을 보여야 함. 이게
      carve loss의 존재 이유
- [ ] 비교군: TIDI-GS(visibility+neighbor+importance pruning), StableGS(cross-view
      depth consistency), 단순 opacity threshold pruning

## 4. 실험 축 (Experiment Matrix)

### E0 — 예산 곡선(모든 실험의 기본 단위, 원안)

모든 변형에 대해 **고정 iteration 예산 sweep**: `{200, 500, 1000, 2000, 4000, 6000}`
→ 주 결과 그림은 "PSNR vs iteration budget" 곡선 6개. 단일 PSNR 숫자는 부차적.

### E1 — 컴포넌트 ablation (원안)

| ID | A(anchor) | B3(carve force) | C(solve) | 비고 |
|---|---|---|---|---|
| base | ✗ | ✗ | ✗ | VIGS custom 현재 |
| +C | ✗ | ✗ | ✓ | 가장 싼 승부수 |
| +A | ✓ | ✗ | ✗ | |
| +B | ✗ | ✓ | ✗ | carve loss 단독 |
| +AC | ✓ | ✗ | ✓ | |
| full | ✓ | ✓ | ✓ | |

### E2 — 일반화(C2 증명, **논문의 핵심**, 원안)

- scene을 **dev(3개) / test(5개 이상)** 로 분리
- dev에서만 하이퍼파라미터 결정 → **test는 단 한 번, 고정 파라미터로 실행**
- baseline은 (a) dev 튜닝 파라미터 그대로 (b) test별 최적 튜닝 — 둘 다 보고
- **주장**: 우리는 (a)로도 baseline (b)에 근접/우위

> **지금 "scene마다 param이 달라 문제"였던 것이, 여기서 baseline의 약점으로
> 전환된다.** — 이건 정확히 exp59가 겪은 실패(freeze800을 305/12F에 재튜닝 없이
> 옮겼다가 26.00/16.95dB로 붕괴)를 가리킨다. dev/test 후보 배정 시 exp59가 이미
> 실측해둔 4개 장면(aria1253, aria1253rot, aria301_305, aria301_12F)을 그대로
> dev/test 시드로 쓸 수 있음 — 처음부터 새 장면을 찾을 필요 없음.

### E3 — Compute contention robustness(C4, 원안 + ADDENDUM-1 재해석)

frontend에 인위적 부하를 주입(dummy GPU kernel, 또는 frontend iteration 강제 증가)
→ 확보 가능한 backpolish iter를 {100%, 50%, 25%, 10%}로 강제
→ **PSNR 저하 기울기**를 baseline과 비교. 우리 방법이 완만하면 그게 곧 "예산 강건성"
증명.

> C0(backpolish 완전 제거)가 성립하면 이 축의 성격이 "완화"에서 "제거"로 바뀐다 —
> backpolish가 아예 없으면 frontend↔backend GPU 경쟁의 한 축 자체가 소멸하므로,
> E3은 M3′/M3″만 켠 상태(backpolish 없음)에서 frontend 부하를 흔들어도 PSNR이 거의
> 안 흔들리는지를 보는 실험이 된다.
>
> **exp63의 `replay_time_scale` 스윕(1.5/2.0/3.0)과 exp64의 시간-비율 거버너가 이미
> 이 축의 예비 실험이다** — 다만 그쪽은 "예산을 늘려서 회복"이었고 여기선 "예산이
> 줄어도(또는 아예 없어도) 덜 무너지는 방법"이 목표라 방향은 반대. exp63 스윕에서
> 이미 관측된 역-U자형 비단조성(scale 3.0 역행)은 E3 설계 시 "예산이 늘면 무조건
> 좋다"는 가정을 깨는 반례로 인용 가능.

### E4 — Geometry(C3, 원안)

depth L1, normal consistency, (가능하면) mesh F-score. **PSNR만 오르고 geometry가
무너지면 SLAM 논문으로서 실패**.

### E5 — 시스템 지표 (원안)

FPS, tracking ATE, peak VRAM, Gaussian 수. 실시간 주장의 방어선.

### E6 — Backpolish 제거 실험 (2026-08-18 ADDENDUM-1 [§4 신규], **C0의 직접 증명 — 논문의 메인 표**)

기존 E0(예산 곡선)은 이 표의 보조가 된다.

| 설정 | init | map DoF | backpolish | 측정 |
|---|---|---|---|---|
| S0(baseline) | 기존 | 자유 | **ON**(6000 iter) | 기준 PSNR |
| S1 | 기존 | 자유 | **OFF** | 얼마나 떨어지는지 = 갭의 크기 |
| S2 | M1b(2D fit + lift) | 자유 | **OFF** | init만으로 얼마나 메우는지 |
| S3 | 기존 | M3′ 제약 | **OFF** | map 제약만으로 얼마나 메우는지 |
| **S4** | M1b | M3′ 제약 | **OFF** | **← 목표 설정** |
| S5 | M1b | M3′ 제약 | ON | 상한 확인(제약이 천장을 낮추지 않았는지) |

**핵심 지표**: `PSNR(S4) − PSNR(S0)`. 이게 0에 가까우면 C0 성립.

**보조 지표**: `PSNR(S5) − PSNR(S4)` — 이 값이 작아야 "backpolish가 정말 불필요"하다는
주장이 선다. 크면 backpolish가 여전히 일을 하고 있다는 뜻.

**추가로 반드시 보고**:

- backpolish 제거 시 **frontend가 회수하는 GPU 시간** → tracking ATE 개선으로
  이어지는지(이게 나오면 "품질 유지 + tracking 개선"이라는 두 번째 셀링 포인트)
- 전체 파이프라인의 **하이퍼파라미터 개수 감소**(freeze 타이밍, 시간배분 비율 등이
  통째로 소멸) → C2를 정성적으로 뒷받침

> **48시간 내 최우선 측정**: E6의 S1(지금 코드에서 backpolish만 끄면 몇 dB인가)이
> "메워야 할 갭"의 크기를 정하고 전체 프로젝트 난이도를 결정한다(§10).

## 5. 데이터셋

| 용도 | 데이터 |
|---|---|
| dev(튜닝 허용) | Aria Glass 자체 촬영 3 scene |
| test(튜닝 금지) | Aria Glass 나머지 + **공개 벤치마크 필수** |
| 공개 벤치마크 | **Replica + TUM RGB-D 고정**(2026-08-18 ADDENDUM-1 [§5 추가], 원안 "Replica/TUM/EuRoC/ScanNet++ 중 2종"에서 확정) |

> RGS-SLAM(§1.1b의 직접 경쟁자)이 **TUM RGB-D와 Replica**에서 평가했다. 직접
> 경쟁자와 표를 겹치려면 이 둘은 필수.
>
> **Aria만으로는 리뷰어가 안 받아준다.** VIGS-SLAM이 쓴 데이터셋과 최소 2개
> 겹쳐야 표를 만들 수 있다. Aria는 "추가 실험 / 실환경 검증" 위치로.

## 6. Claude Code 루프 운영

### 6.1 디렉토리

```
project/
├── refs/                  # clone된 참고 repo (읽기 전용)
│   └── NOTES.md
├── src/                   # VIGS custom fork
├── configs/               # YAML 하나 = 실험 하나
├── exp/
│   └── {EXP_ID}/
│       ├── config.yaml    # 스냅샷
│       ├── git_sha.txt
│       ├── metrics.csv
│       ├── budget_curve.csv
│       └── report.md      # 자동 생성
├── tools/
│   ├── run_sweep.py
│   ├── make_budget_curve.py
│   └── compare.py
└── RESULTS.md             # 전체 실험 leaderboard (append-only)
```

> 이 구조는 `gs_floaterLab`의 `context/experiments/` + exp 카드 관례(카드 하나 =
> 실험 축 하나, INDEX.md가 leaderboard)와 목적이 같다. 다만 이 계획은 실행을
> VIGS-SLAM 소스트리 밖의 **별도 fork(`src/`)** 에서 하는 걸 전제로 한다 — exp62가
> 그랬듯 신규 코드는 dirty worktree를 건드리지 않는 별도 경로에 둘 것.
>
> **브랜치 전략(사용자 요청, 신규)**: 위 `git_sha.txt` 스냅샷 관례와 별개로, VIGS-SLAM
> 저장소 자체도 착수 시점에 `main`에서 새 브랜치(예: `exp65-backpolish-free`)로
> 분기해 그 위에서 작업한다. 이유: M1b(2D fit+lift로 init 자체를 교체)와 M3′/M3″
> (Gaussian 파라미터화 자체를 바꿈)는 exp63/64가 다뤄온 스케줄링/freeze 레벨 변경과
> 달리 **`gaussian_model.py`/`map()`/init 경로의 구조 자체를 바꿀 가능성이 높아**,
> 현재 `main`에 아직 커밋 안 된 exp63/64 변경분과 뒤섞이면 원인 분리가 어려워진다.
> 착수 전 exp63/64 dirty 변경분을 먼저 커밋(또는 최소 stash)해 `main`을 깨끗이 한
> 뒤 분기할 것.

### 6.2 Claude Code에 주는 규칙

1. **한 실험 = 한 config 파일 = 한 커밋.** config에 없는 값을 코드에 하드코딩 금지.
2. **모든 실험은 acceptance contract를 config에 명시**하고, 종료 시 통과/실패를
   `report.md`에 자동 기록.
3. **seed 3개 이상** 반복. 단일 실행 결과로 결론 내지 않음. Splat-SLAM 저자들도
   동일 seed/환경에서 GPU 하드웨어에 따라 결과가 달라진다고 명시함.
4. baseline 재현을 **매 세션 시작 시 1회** 실행해 환경 drift 감지.
5. 실패한 실험도 `RESULTS.md`에 남김. 삭제 금지.
6. **커널 수정 시 반드시 gradient check**(analytical vs finite difference).

> 3번(seed≥3)·5번(실패도 기록)은 이 저장소가 이미 지키고 있는 원칙과 정확히
> 같다(exp30/43이 run-to-run 노이즈 ±0.24~0.33dB를 실측해 "단일 run 비교 금지"를
> 확정한 것, INDEX.md가 기각된 실험도 전부 남기는 것). 6번(gradient check)도
> exp56 Phase 11(renderCUDA 커널 batch화)에서 실제로 밟은 절차(수치 검증 →
> atomic-noise 수준 확인 후에만 승격)와 동일 — 새 원칙이 아니라 기존 관행의
> 명문화.

### 6.3 루프 프롬프트 템플릿

```
[목표] M2 acceptance contract 통과
[제약] src/ 만 수정. refs/ 는 읽기 전용.
[현재 상태] exp/M2_003 까지 진행, 실패 원인은 report.md 참조
[이번 작업] {구체적 1개 변경}
[검증] tools/run_sweep.py --config configs/M2_004.yaml --seeds 3
[산출] exp/M2_004/report.md 에 contract 통과 여부 기록
```

### 6.4 주의

- **Claude Code에게 "성능 올려줘"라고 시키지 말 것.** 반드시 단일 가설 + 단일
  변경 + 사전 정의된 통과 조건.
- **자동 하이퍼파라미터 탐색을 dev scene 밖에서 돌리지 말 것.** E2의 주장이 무너진다.

## 7. 일정 (2026-08-18 ADDENDUM-2가 재조정한 최종판, ADDENDUM-1의 1차 재배치를 다시 덮어씀)

| 주 | 내용 | 게이트 |
|---|---|---|
| W1 | M0 계측 + **M1a** + **E6 S1(backpolish OFF 갭)** | 갭 크기 확정 |
| W1.5 | **M1.5 Prior 감사** | confidence↔오차 상관계수. mono 도입 여부 결정 |
| W2 | M1b(prior 전면 투입 버전) + normal ON/OFF ablation | 계단표 완성 |
| W3 | E6 예비(S0/S1/S2) | 논문 축(C0 vs C1) 최종 결정 |
| W4 | M3′(균일 ray 제약) | 제약의 기본 효과, S3 확보 |
| W5 | **M3″(confidence-adaptive DoF)** | **novelty 확보 지점** |
| W6 | E6 전체(S4/S5) | **C0 판정** |
| W7 | 남은 갭에 맞춰 M2(색) 또는 M4(위치/carve) | 갭이 색이면 M2, 위치면 M4 |
| W8 | E2 일반화 + 공개 벤치마크 | |
| W9 | 작성 | |

> ADDENDUM-1의 1차 재배치(M1b→W2, E6 예비→W3, M3′→W4-5, E6 전체→W6, M2/M4→W7)를
> ADDENDUM-2가 W1.5(M1.5)와 W5(M3″)를 끼워 넣어 최종 확정한 형태. 기존 원안 대비
> **M2를 W2에서 W7로 후순위 이동**한 이유는 §0 Claim 표 아래 각주와 동일(C0가
> 우선이고, M2는 C1으로 후퇴할 때만 최우선 복귀).

## 8. Kill criteria (미리 정해둘 것)

원안 4건:

- M1(현 M1a)에서 iter-0 PSNR < 15dB이고 mono-depth 융합으로도 개선 안 됨 → **(A) 폐기,
  (C) 단독으로 축소**
- M2 solve가 ADAM 대비 이득 없음 → occlusion 비선형성이 지배적. **(C) 폐기**
- M3(anchor) 안에서 6000 iter 지점에서 baseline 대비 -2dB 이상 → A3(해제 단계) 없이는
  불가. 일정 재검토
- E2에서 test scene 성능이 dev 대비 크게 하락 → **주장 C2 철회**, "예산 강건성"(C4)
  으로 논문 축 이동

ADDENDUM-1 추가 4건([§8 추가]):

- **M1b의 Δ_lift > 3dB** → 2D→3D 변환 손실이 지배. **M1b 폐기**, M1a + M3′로 축소하고
  C0 대신 C1로 후퇴
- **M1c 다중뷰 열화가 -5dB 초과** → 키프레임별 2D fit이 서로 안 맞음. 중복 병합 정책을
  먼저 풀어야 하며, 일정상 무리면 M1b 폐기
- **E6에서 S5 − S4 > 2dB** → backpolish가 여전히 필요. **C0 철회**, C1(예산 효율)로
  논문 축 이동
- **M3′에서 occlusion 처리 때문에 rasterizer를 새로 짜야 함이 확인되면** → 학부생 2인
  리소스로 감당 불가. R1(ray 제약)만 남기고 R2는 포기

ADDENDUM-2 추가 2건([§8 추가]):

- **M1.5에서 confidence ↔ 실제 오차 상관 |r| < 0.3** → 신뢰도 신호가 쓸모없음.
  M3″를 residual 기반 적응(원래 R3)으로 후퇴시키고, "confidence-adaptive DoF" 주장 철회
- **M1b의 normal ON/OFF 차이 < 1dB** → normal prior가 값을 못 함. lift에서 normal을
  빼고 단순화. 동시에 M3″의 회전 제약도 무의미해지므로 R1(위치)만 남김

## 9. 리스크

원안 표(엔지니어링/공개판 관계/리소스는 유지):

| 리스크 | 대응 |
|---|---|
| **엔지니어링으로 읽힘** | 모든 결과를 예산 곡선으로 보고. 단일 PSNR 표는 부록으로. **C0(단계 제거) 주장이 성립하면 이 리스크는 구조적으로 해소됨(§0)** |
| **VIGS-SLAM 코드 공개판과의 관계** | baseline으로 명확히 인용하고, 우리 기여를 "plug-in module"로 포지셔닝. FastGS가 여러 백본에 붙는 형태로 포지셔닝한 전례 참고 |
| **학부생 2인 리소스** | M2 → M3 → M4 순서(원안) 대신 **M1a→M1.5→M1b→E6 예비→M3′→M3″→E6 전체** 순서(§7) 엄수. M2만으로도 워크샵 페이퍼는 가능한 분량(C0 실패 시 fallback) |

**Scoop 항목 재작성(2026-08-18 ADDENDUM-1 [§9 치환])**:

| 리스크 | 심각도 | 대응 |
|---|---|---|
| **RGS-SLAM과의 중복** — dense correspondence init으로 densification을 대체한다는 발상이 겹침 | 🔴 높음 | 차별점을 명확히: 그쪽은 init을 **최적화 가속 수단**으로 써서 ~20% 단축을 얻었고 최적화 단계는 그대로 유지. 우리는 init+제약으로 **전역 refinement 단계를 제거**. 정량 비교표에 RGS-SLAM을 baseline으로 반드시 포함 |
| **PAGaS와의 중복** — ray 제약 1-DoF Gaussian | 🔴 높음 | 그쪽은 오프라인 depth refinement/mesh 목적, 뷰별 처리. 우리는 실시간 SLAM 루프 + 렌더링 품질 + 예산 제약. **인용하고 "우리가 온라인으로 확장했다"로 포지셔닝** |
| **Augmented Radiance Field와의 중복** — 2D fit 후 back-project | 🟡 중간 | 그쪽은 오프라인 품질 향상용 보조 Gaussian 생성. 우리는 이걸 **주 init 경로**로 쓰고 실시간 예산을 지킴 |
| init 가속 분야 자체가 이미 정리된 하위분야(MGSO, GPS-SLAM, MemGS 등) | 🟡 중간 | 서베이(2602.04251)를 인용해 "이들은 모두 **가속**을 목표로 했고, **단계 제거**를 시도한 사례는 없다"로 gap statement 작성 |

**ADDENDUM-2 추가 3건([§9 추가])**:

| 리스크 | 대응 |
|---|---|
| **prior 품질이 곧 천장** — Aria 실내 저텍스처 벽에서 depth/normal이 무너지면 제약이 오히려 해가 됨 | 그래서 M3″(적응적 해제)가 안전장치다. 균일 제약(M3′)만으로 논문 쓰지 말 것 |
| **mono 모델 추론 비용이 실시간 예산을 먹음** | 키프레임에만, 다운샘플 해상도로. 비용이 backpolish 절감분을 넘으면 mono 포기하고 DROID depth만 사용 |
| **confidence-aware 연구가 이미 포화** | 위 gap statement("weight가 아니라 parameterization")를 abstract 첫 문단에 못박을 것 |

## 10. 지금 당장 할 것 (48시간, 2026-08-18 ADDENDUM-1 [§10 치환]로 갱신)

1. `refs/` clone(**GaussianImage, RGS-SLAM 추가**) + `NOTES.md`
2. M0 로깅 삽입 — 파라미터 그룹별 이동량
3. **M1a: iter-0 PSNR 측정**
4. **PAGaS / RGS-SLAM / Augmented Radiance Field 3편 정독** — 각 1페이지 요약을
   `refs/NOTES.md`에 작성. 특히 **"우리와 겹치는 문장 / 겹치지 않는 문장"을 각각 3개씩**
   뽑아둘 것. 이게 나중에 그대로 related work가 되고, scoop 판정 기준이 된다
5. **E6의 S1 먼저 측정** — 지금 코드에서 backpolish를 그냥 끄면 몇 dB인가. 이 숫자가
   "메워야 할 갭"의 크기이고, 전체 프로젝트의 난이도를 확정한다

> 원안의 "5개 scene budget curve"는 C1 라인용이므로 **W3으로 이동**. 48시간 안에는
> **S1(backpolish OFF 갭) + M1a(iter-0) 두 숫자**가 최우선.
>
> 착수 전 선행 작업(§6.1 브랜치 전략): exp63/64의 VIGS-SLAM dirty 변경분을 먼저
> 커밋/정리하고 새 브랜치로 분기.

## 이 저장소 기존 자산과의 매핑 요약 (실행 착수 전 참고용)

실행 시작 전에 "이미 있는 것 vs 진짜 새로 만들 것"을 헷갈리지 않기 위한 표.

| 계획서 항목 | 이 repo에 이미 있는 것 | 진짜 신규 작업 |
|---|---|---|
| M0 계측(시간) | exp56 `map_call` 로그 + 회귀분석, exp63/64 `VIGS_TIMING_LOG`/always-on 타이머 | 파라미터 그룹별 이동량(Δxyz/Δscale/…) 로깅만 신규 |
| M1a init 상한 | exp37(배치, plateau 없는 dense init 32.621dB@30k) — 참고는 되지만 iter-0 수치 아님 | iter-0 PSNR 실측 자체가 신규 |
| M1.5 prior 감사 | 없음 | 완전 신규 |
| M1b 2D fit+lift | 없음 | 완전 신규 — GaussianImage/Augmented Radiance Field 코드 이식 필요 |
| M2 closed-form solve | 없음 | 완전 신규 — rasterizer weight 노출 여부부터 확인 |
| M3 topology anchor | 없음(Scaffold-GS류 anchor를 이 프로젝트에 쓴 적 없음) | 완전 신규 |
| M3′/M3″ ray 제약 | 없음 | 완전 신규 — occlusion-aware rasterizer 필요 여부가 최대 리스크 |
| M4 carve loss "가속" 재해석 | exp38~44d2(배치, prune/gate/force 이미 검증됨), exp55 Phase3(incremental 이식 사례) | 코드는 대부분 재사용, **지표만 "floater 억제"→"동일 예산 PSNR 우위"로 교체** |
| E2 일반화(dev/test) | exp59가 이미 4개 장면 실측 완료(1253/1253rot/301_305/301_12F) | 이 4개를 그대로 dev/test 시드로 재사용 가능 |
| E3 compute contention | exp63 scale 스윕 + exp64 거버너가 예비 데이터 보유 | backpolish 완전 제거 상태에서의 재실행 필요 |
| E6 backpolish 제거(S1) | 없음(exp63/64는 배분만 다뤘지 완전 OFF는 측정한 적 없음) | **48시간 내 최우선 신규 측정** |

## 실행 결과 — E6 S1 1차 측정, aria1253 (2026-08-19)

**상태: 착수, 운영 루프 가동 (방향설계=Claude / 구현·실행=codex 위임 / 검증=Claude, 매
단계 독립 재검증).**

### 브랜치/체크포인트

VIGS-SLAM `main`이 exp63/64의 미커밋 변경분(governor 구현, 디버그 계측, PGBA 버그
수정 등)으로 dirty였던 것을 `Checkpoint exp63/64 WIP...` 커밋(`ca851173`)으로 정리하고,
`main`과 `exp65-backpolish-free` 브랜치를 둘 다 이 커밋으로 맞춘 뒤 이후 exp65 작업은
전부 `exp65-backpolish-free`에서 진행 중.

### 구현 (codex2 위임, 2회차에 성공)

`background_polish_step()`은 코드 전체에서 호출부가 `vigs/vigs.py:406` 하나뿐이고
`self._background_polish`(config의 `Training.background_polish`, 기본 False) 하나로
게이트됨을 직접 grep으로 먼저 확인 — **소스 수정 없이 config YAML 한 줄**(`exp63_axes/recipe/config.yaml`의
`background_polish: true`→`false`)만으로 S1을 만들 수 있음을 설계 단계에서 확정.
`exp63_axes/recipe/run_flags_current.sh`를 직접 읽어 aria1253 호출 인자(calib, length=1303,
전 fractional-boundary 값)를 확보한 뒤, 그 내용을 프롬프트에 그대로 박아 codex가 탐색
없이 기계적으로만 파일을 쓰게 설계.

- 1차 시도(`codex`, 기본 계정): 300초 타임아웃까지 **아무 출력 없이 SIGTERM**(exit 143).
  `exp65_axes/` 디렉터리조차 생성되지 않아 완전 실패 — 원인 미상(레포가 19GB에
  253개 결과 디렉터리라는 점 의심했으나 `git status`는 0.07초로 빠름, 확정 원인 못 찾음).
- 2차 시도(`codex2`, 별도 계정 — exp63의 `exp63_run_axis.sh` 관례를 따름): 50초 만에
  완료, **JSON 리포트에 `status: "error"`로 자체 보고**(diff에 없는 trailing-line 문제를
  주장). **직접 `diff`/`wc -l`/`cat -A`로 재검증하니 실제로는 정확히 1줄만 다른 완전한
  성공**이었음 — codex의 자체 검증 결과를 곧이곧대로 믿지 않고 독립 재확인한 것이
  유효했던 사례(오탐, false negative). fractional-boundary 로그(`total_frames=1303`)로
  `--length 1303`·calib 경로가 실제 레퍼런스 런과 정확히 일치함도 교차 확인.

### 실행 (codex2 위임, 2회차에 성공)

- 1차 시도: 즉시 실패(`exit_code=1`, `wall_clock_seconds=0.0`) — **codex의 리포트가 이번엔
  정확했음**: `bash script.sh > .../aria1253/run.log` 리다이렉트가 스크립트 내부의
  `mkdir -p`보다 먼저 열려야 해서, 출력 디렉터리가 미리 존재하지 않으면 셸 자체가 실행
  전에 실패하는 선후관계 버그(Claude의 스크립트 설계 실수). Claude가 디렉터리를 직접
  `mkdir -p`한 뒤 동일 프롬프트로 재시도.
- 2차 시도: 140.8초 만에 정상 종료(`exit_code=0`).

### 결과

| | S0 (backpolish ON, HEAD reference) | **S1 (backpolish OFF, 신규)** |
|---|---:|---:|
| mean PSNR | 27.805869dB | **17.436971dB** |
| kf mean PSNR | 27.659968dB | 17.452155dB |
| SSIM | 0.87274 | 0.66255 |
| keyframes 처리 | 123 | 123(동일) |
| 최종 gaussian 수 | 95,954 | 95,426(-0.55%, 거의 동일) |
| background_polish steps | (다수, 정상 작동) | **0**(의도대로 완전 비활성) |
| wall time | 101.06s | 140.8s(+39%, 원인 미확인) |

**E6 핵심 지표 `PSNR(S1) − PSNR(S0) = −10.369dB`.** keyframe/gaussian 수가 두 run에서
거의 동일해 init/map() 파이프라인 자체는 두 run에서 똑같이 작동했음이 확인되고(파이프라인
버그 아님), `background_polish_step_count_in_log=0`으로 의도한 조작이 정확히 걸렸음도
확인됨 — **이건 진짜 측정값**이다. (`ONLINE_FINAL_EVAL map_updates=0` 로그는 카운터가
아니라 `demo.py:2255`의 하드코딩된 리터럴 문자열 출력이라 무관함을 소스로 확인, S0/S1
양쪽에 동일하게 찍혀 red herring이었음.)

**시사점**: -10.4dB는 §8 kill criteria의 "E6에서 S5−S4 > 2dB → C0 철회"에 대응하는
수치는 아니지만(S5/S4는 아직 미측정 — M1b/M3′ 없이 init만 그대로 두고 backpolish만 뺀
수치이므로 S1이지 S4가 아님), **"메워야 할 갭"이 애초 예상보다 훨씬 크다**는 걸 보여준다.
M1b(2D fit+lift)와 M3′/M3″(DoF 제약)가 이 10dB를 실제로 메울 수 있는지가 C0 성립의
관건 — §7 일정대로 M1a(다음 우선순위)를 먼저 측정해 "naive lift 자체의 iter-0 상한"을
알아야 이 갭의 어느 정도가 init 품질 문제이고 어느 정도가 수렴 속도 문제인지 분리 가능.

**wall time 이상치(+39%)는 미해결**: keyframe 페이싱(123개 동일)과 최종 gaussian 수가
거의 동일한데 전체 wall time만 40s 더 걸림 — 콜드스타트/CUDA JIT 컴파일 변동 가설이
유력하나 확인 안 됨. PSNR 결과의 신뢰성과는 무관(파이프라인은 동일하게 작동했음이 이미
확인됨)이라 지금은 기록만 하고 넘어감, 재현성 검증(같은 조건 2회 이상) 시 재확인 필요.

**미검증**: 단일 run(seed 통제 없음), 단일 scene(aria1253만). 이 저장소의 반복 원칙상
(exp30/43: run-to-run 노이즈 ±0.24~0.33dB 실측) 단일 run 결론은 잠정치로만 취급.

## 다음 단계

1. [다음 loop 이터레이션 후보] M1a(naive lift iter-0 PSNR) 측정 — §7 W1 우선순위,
   위 갭을 init 문제/수렴 문제로 분리하는 데 필요.
2. S1을 aria301_305에서도 재현(scene 일반화 확인, 이 저장소의 "단일 장면 결론 금지" 원칙).
3. wall time +39% 이상치 원인 확인(선택, 급하지 않음).

사용자가 다른 지시를 주지 않으면 위 1번(M1a)을 다음 codex 구현/실행 사이클로 이어간다.

### 설계 메모 — 기존 raw birth 경로는 M1a와 다르다 (2026-08-19, M1a 착수 전 확인)

M1a를 새로 구현하기 전에 기존 코드에 이미 비슷한 게 있는지 확인하려고
`add_next_kf()`(`gs_backend.py:3148`)→`extend_from_pcd_seq()`→`create_pcd_from_image_and_depth()`
(`gaussian_model.py:191`, 매 keyframe마다 실제로 쓰이는 raw Gaussian 배치 경로)를 직접
읽었다. 결과:

- **normal을 전혀 안 씀.** `rots[:, 0] = 1`로 모든 새 Gaussian이 항등회전 고정,
  `BasicPointCloud`에 넘기는 `normals`는 `np.zeros((N,3))`(단순 자리채움, 어디서도 안 읽힘).
- scale은 depth/focal 비례가 아니라 `distCUDA2`(최근접 이웃 점 간 거리) 기반 —
  M1a 스펙(§3 M1a)의 "인접 픽셀 간 거리 기반" 조건과 결이 비슷하긴 하나 normal 방향
  납작화(surfel화)는 없음.
- opacity는 고정 `inverse_sigmoid(0.5)`(계획서의 0.9와 다른 상수지만 "고정값" 원칙은 동일),
  색은 픽셀 RGB(계획서와 일치).

**결론**: 기존 raw birth는 M1a보다 더 단순한(normal 미사용) baseline이라 M1a를 대체할 수
없다 — normal 기반 orientation은 정말 새로 구현해야 한다(M1.5가 먼저 감사해야 할 그
normal 자체도, motion_filter의 `prior_extractor`가 만드는 monocular normal이 이 birth
경로로 전혀 plumbing 안 되고 있다는 뜻이기도 함 — M1.5에서 "그 normal이 지금 어디에
쓰이고 있는지" 확인 필요).

**부산물로 발견한 공짜 실험 하나(→ 실행해보니 공짜가 아니었음, §S1b 참고)**: `map()`
(`gs_backend.py:3596`)의 densify_and_prune·optimizer.step 전부가
`for mapping_iteration in range(iters):` 루프 안에만 있음을 확인 — 즉
`--late_mapping_start_frac 0.0 --late_mapping_iters 0` + config의 `init_itr_num: 0` 세
값만 CLI/config로 바꾸면(새 코드 0줄) "keyframe마다 raw birth만 되고 어떤 최적화도
전혀 안 닿는" 순수 baseline을 S1과 똑같이 싸게 측정할 수 있을 거라 예상했으나, 실제
실행해보니 두 가지 실제 문제에 부딪혀 이 형태로는 불가능함을 확인함(아래 §S1b).

## 실행 결과 — S1b "birth-only" probe, aria1253 (2026-08-19, 부산물 실험 — 실패 2건, 실제 버그 1건 발견)

**상태: 보류(실행 안 함) — 프레임워크가 진짜 0-iter를 지원하지 않고, 시도 중 `map()`의
잠재 버그를 발견함. 이 probe는 "새 코드 0줄" 전제가 깨졌으므로 지금 우선순위(M1a)로는
가치가 낮아 여기서 중단.**

이번 사이클은 사용자 지시("구현/실행 따로따로")에서 벗어나 구현+실행을 codex2 1회
호출로 합쳐 시작했음(저위험 반복이라고 판단했으나, 아래처럼 실제로는 2번 재시도가
필요했음 — 판단 착오였다고 정직하게 기록).

- **1차 시도**: `--late_mapping_iters 0`으로 실행 → **즉시 실패(4.18초)**.
  `demo.py`가 `if args.late_mapping_iters <= 0: raise ValueError("--late_mapping_iters
  must be positive")`로 명시적으로 막아둠 — **진짜 0-iter는 이 코드베이스가 애초에
  지원하지 않는 설정**임을 확인(설계 가정이 틀렸음, 실행해서 알아낸 사실).
- **2차 시도**: `--late_mapping_iters 1`(허용되는 최솟값)로 낮춰 재실행 →
  **20분 타임아웃으로 codex가 SIGINT**(`exit_code=130`, `wall_clock_seconds=1265.19`).
  로그 분석 결과 keyframe 19→20 처리 중 **`_gs_worker` 백그라운드 스레드가
  `UnboundLocalError: cannot access local variable 'frozen_mask'`로 죽고, 메인
  트래킹 루프는 계속 살아있어 매핑 없이 계속 돌면서 사실상 멈춘 것처럼 보인 것**
  (Python 스레드의 미처리 예외는 그 스레드만 죽이고 프로세스 전체는 안 죽인다 —
  그래서 크래시가 아니라 "20분간 무한 대기"로 나타남).

**근본 원인(코드로 직접 확인)**: `map()`의 `first_mapping` 분기(`gs_backend.py:3056`)는
`iters=self.init_itr_num//len(self.current_window)`를 계산하는데, `init_itr_num=0`이면
`iters=0`이 되고 **이 경로엔 CLI의 `--late_mapping_iters` 같은 사전 검증이 없다**.
`map()` 내부에서 `frozen_mask = self._frozen_gaussian_mask()`(`gs_backend.py:3937`)는
`for mapping_iteration in range(iters):` 루프 **안**에서만 대입되는데, 루프 뒤
"enforce scale not super large" 블록(`gs_backend.py:3993`)은 루프 밖(항상 실행)에서
`if frozen_mask is not None:`으로 그 변수를 참조한다. `iters=0`이면 루프가 한 번도 안
돌아 `frozen_mask`가 결코 정의되지 않고, 루프 뒤 코드가 그걸 참조하는 순간
`UnboundLocalError`. freeze가 걸린 상태(`mapping_freeze_after_frac` 설정, 우리 레시피
전부 해당)에서만 이 코드 경로 자체가 의미를 갖지만, 조건 없이 항상 참조되므로
`iters=0`이면 freeze 여부와 무관하게 무조건 터진다.

**정리**: (1) CLI의 `late_mapping_iters` 검증은 의도된 안전장치, (2) 하지만
`first_mapping` 분기는 같은 안전장치가 없어 `init_itr_num=0`으로 우회 가능하고 우회하면
진짜로 터짐 — **이건 이 세션에서 새로 발견한, exp65와 독립적인 실제 버그**다.
`background_polish_step`도 아니고 `map()` 자체의 결함이라 향후 `init_itr_num`을
0으로 낮추려는 시도가 있으면(예: 다른 실험에서) 반드시 먼저 고쳐야 함 — 지금은 exp65
우선순위(M1a)가 아니므로 고치지 않고 기록만 해둠.

**이 probe 중단 이유**: 진짜 "raw birth만, 최적화 전혀 없음"을 재려면 이 버그를 실제로
고치는 새 코드가 필요해져,애초 이 probe의 장점("새 코드 0줄로 공짜 측정")이 사라진다.
M1a(정식 normal 기반 구현)가 이미 새 코드가 필요한 작업이므로, 이 부차적 probe에 더
투자하지 않고 M1a로 직행한다.

## 실행 결과 — M1a 구현·측정, aria1253 (2026-08-19)

**상태: 구현 완료·검증 완료·1차 측정 완료.** §10의 두 48시간 최우선 항목(E6 S1, M1a)이
둘 다 끝났다.

### 구현 (엄격 분리 유지: 신규 코드라 구현→검증→실행 분리, codex2에 위임)

`viewpoint.normal`(모션필터의 `prior_extractor`, `mono_model: omnidata`가 만든 monocular
normal)이 이미 `get_loss_normal`용으로 매 keyframe마다 채워져 있고,
`create_pcd_from_image_and_depth()`(`gaussian_model.py:191`, 매 keyframe raw birth의
실제 코드 경로, `ppm_sampling: true`가 채택 레시피 기본값)만 이걸 완전히 무시하고
`rots[:,0]=1`(항등회전)·등방 scale로 짓는다는 걸 확인한 뒤, 다음을 구현:

- 신규 opt-in `Dataset.exp65_m1a_normal_orient`(기본 false, 기존 동작 100% 불변) 플래그.
- 켜지면: `cam.normal_gpu`를 camera→world로 변환(`W2C[:3,:3]` 회전 재사용)한 뒤,
  로컬 Z축(0,0,1)을 그 world-frame normal로 정렬하는 **half-way-vector 공식**(scalar-first
  quaternion, `qw=1+n_z, qx=-n_y, qy=n_x, qz=0`, 정규화)으로 회전을 만들고,
  normal 방향 축만 얇게 만드는 anisotropic scale(`Dataset.exp65_normal_flatten_ratio`,
  기본 0.2)을 적용 — surfel형 배치.
- **착수 전 컨벤션 검증**: 이 quaternion 공식이 이 코드베이스의 실제 `build_rotation()`
  (`general_utils.py:75`, scalar-first, R의 3번째 컬럼=로컬 Z축의 world 방향)과
  일치하는지 500개 랜덤 단위벡터로 직접 대조 — **최대 오차 3.4e-7**로 통과
  (`QUATERNION_CHECK_PASSED`, codex 실행 로그 직접 확인).
- **diff 전량 직접 검토**: git diff가 사전에 지정한 코드와 byte-for-byte 일치, 플래그
  꺼졌을 때 else 분기가 원 코드와 수학적으로 동치임도 확인(회귀 없음).

### 실행 설계 — S1b의 크래시를 피해 다른 메커니즘 사용

S1b에서 발견한 `map()` 크래시(`iters=0`일 때 `frozen_mask` 미정의)를 다시 밟지 않기
위해, `late_mapping_iters=0`이 아니라 **exp63에서 이미 검증된 `--mapping_freeze_after_frac
0.0 --mapping_freeze_allow_births`**(즉시 freeze + append-only raw birth만 허용,
`map()` 자체가 아예 호출 안 됨 — 크래시 경로를 원천적으로 피함)로 "raw birth만, 최적화
전혀 없음"을 구현. control(정체성 회전, 기존 방식)과 normalorient(신규 플래그) 두
config/스크립트를 생성하되, **독립 검증 중 스크립트에 `--mapping_freeze_after_frac`가
두 번(기존 0.614 + 신규 0.0) 들어간 실수를 발견**(codex가 "끝에 추가하라"는 지시를
문자 그대로 따른 결과 — `demo.py`의 argparse가 `store` 액션이라 마지막 값이 이겨서
기능적으로는 우연히 맞았지만, Claude가 직접 소스로 확인 후 명확성을 위해 두 파일 다
직접 수정해 중복 제거).

### 결과

| | control (정체성 회전, 등방 scale) | **normalorient (신규, normal 기반 surfel)** |
|---|---:|---:|
| mean PSNR | **16.446dB** | 15.839dB |
| SSIM | **0.6121** | 0.5788 |
| LPIPS | 0.7365 | **0.7005**(더 좋음) |
| 최종 gaussian 수 | 100,414 | 100,407(거의 동일) |
| wall time | 140.84s | 140.69s |
| traceback | 없음 | 없음 |

두 run 다 exit 0, traceback 없음, gaussian 수 거의 동일(같은 freeze/birth 정책이 정확히
같게 작동했다는 대조군 확인) — **파이프라인은 정상, 진짜 측정값**.

**M1a 통합 acceptance 판정**: 카드의 kill criterion "iter-0 PSNR ≥15dB"는 **둘 다 통과**
(15.84/16.45 ≥15) → DROID depth 자체는 병목이 아님, (A) 방향(구조적 DoF 축소) 계속
진행 가능.

**그러나 놀라운 결과**: M1a 스펙 그대로(normal 기반 orientation)가 **더 단순한
identity-rotation isotropic 배치보다 -0.607dB 더 나쁘다**(PSNR/SSIM 기준; LPIPS는
반대로 normalorient가 더 좋음 — 지표 간 불일치, 과잉해석 자제). 가설(미검증,
다음 조사 후보): flatten_ratio=0.2로 만든 얇은 surfel은 normal 추정이 조금만 틀려도
(iter-0라 보정 기회가 전혀 없음) 등방 blob보다 훨씬 view-dependent하게
"사라지기" 쉽다 — 즉 **가공되지 않은(비신뢰도가중) normal prior를 무조건 믿고
DoF를 줄이면 오히려 해가 될 수 있다**는 실측 증거. 이건 계획서 자체가 이미
예견한 원칙(§0 ADDENDUM-2 "DoF 축소=prior로의 위임, prior가 틀리면 제약이 곧
오차")과 정확히 들어맞고, **M1.5(prior 감사)를 거치지 않고 M3″(confidence-adaptive
DoF)로 바로 가면 안 된다는 걸 미리 보여주는 근거 데이터**가 됐다.

**미검증**: 단일 run·단일 장면(aria1253)·단일 flatten_ratio(0.2)만 테스트. 재현성,
flatten_ratio sweep(더 완만한 값이 이 역전을 뒤집는지), aria301_305 재현 전부
다음 후보.

## 다음 단계 (갱신, 2026-08-19)

1. **M1.5(prior 감사)** — normalorient가 왜 졌는지 직접 설명할 수 있는 바로 그 다음
   단계. DROID/omnidata normal의 오차 공간분포, confidence↔실제오차 상관계수를
   먼저 재야 M3″ 설계를 계속할 근거가 생긴다. 이번 M1a 결과가 그 필요성을 실측으로
   뒷받침.
2. flatten_ratio sweep(0.2보다 완만하게, 예: 0.5~0.8)으로 normalorient가 control을
   이길 수 있는지 확인 — M1.5 전에 빠르게 해볼 수 있는 저비용 확인.
3. M1c(multi-view 누적 열화) 및 aria301_305 재현은 위 두 항목 이후로 순연.

사용자가 다른 지시를 주지 않으면 다음 loop 사이클은 1번(M1.5) 또는 2번(flatten_ratio
sweep, 더 저비용이라 우선 후보) 중 하나로 이어간다.

## ⚠ 중대 정정 — E6 S1(17.437dB)은 freeze confound가 섞인 수치였다 (2026-08-19)

**사용자 질문("옛날 vanilla pure_online이 22~23dB였는데 왜 지금 S1은 17dB로 이렇게
낮지?")으로 발견.** 서브에이전트로 exp52~56 카드를 전수조사한 결과, **그 시절
(vanilla pure_online 22.73dB→23.98dB, exp52~56)엔 `mapping_freeze` 메커니즘 자체가
코드에 없었다** — map()이 1303프레임 전체에 걸쳐 끝까지 정상 작동했다.
`mapping_freeze_after_frame`과 `background_polish`는 **둘 다 exp57에서 함께 도입**됐고,
**freeze의 설계 전제 자체가 "map()을 특정 지점(현재 레시피는 61.4%)에서 멈추는 대신
그 GPU 시간을 backpolish가 대신 채운다"** 였다(exp57 causal background polishing
카드 자체가 이 페어링의 도입 기록).

**즉 원래 S1(config에서 `background_polish: false`만 바꾸고 freeze는 그대로 둔 것)은
"backpolish 하나만 뺀 순수 비교"가 아니라, "backpolish가 있다는 전제로 설계된 freeze를
그대로 둔 채 그 전제만 없앤" 상태였다.** frame 61.4%~100%(뒤쪽 약 40%, ~500프레임)는
map()도 멈췄고 backpolish도 꺼서 **문자 그대로 아무 최적화도 못 받고 방치**됐다 —
17.437dB가 비정상적으로 낮았던 진짜 이유.

### 정정 실행 — S1-nofreeze

`run_s1_aria1253.sh`에서 freeze 관련 플래그 3개(`--mapping_freeze_after_frac`,
`--mapping_freeze_allow_births`, `--background_polish_allow_postfreeze_views`)만
제거(diff로 그 외 전부 동일함 직접 확인)한 `run_s1_nofreeze_aria1253.sh`로 재실행:

| | S0(기존) | S1(freeze 유지, 원래 값 — **confound 있음**) | **S1-nofreeze(freeze 제거 — 정정값)** |
|---|---:|---:|---:|
| mean PSNR | 27.806dB | 17.437dB | **23.037dB** |
| fixed-eval PSNR | — | — | 22.819dB |
| 최종 gaussian 수 | ~95,954 | 95,426 | 70,621(더 적음 — freeze 없이 densify_and_prune이 끝까지 정상 작동해 정리됨) |
| exit/traceback | — | 0/없음 | 0/없음 |

**S1-nofreeze(22.819dB, fixed-eval 기준)가 사용자가 기억한 옛 vanilla pure_online
수치(22.73dB, exp52)와 거의 정확히 일치** — 옛 baseline이 실질적으로 "freeze 없는
buckpolish-off" 구성과 같았다는 게 이 재현으로 확인됨.

**E6 지표 정정**: `PSNR(S1)−PSNR(S0)`는 원래 -10.369dB로 기록했으나, freeze confound를
제거하면 **backpolish의 순수 기여도는 27.806−23.037 = 약 -4.769dB**다. 원래 -10.369dB
중 약 5.6dB는 freeze confound가 만든 인공적 페널티였다.

**카드 전체 사용 지침 갱신**: 이후 E6/M0 관련 "backpolish 기여도" 논의는 **S1-nofreeze
(-4.77dB)를 기준으로 삼는다.** 원래 S1(17.437dB, -10.369dB)은 삭제하지 않고 남겨두되,
"freeze confound 포함, 참고용"으로만 취급한다. M1a(control 16.446dB/normalorient
15.839dB)는 이 문제와 무관함 — M1a는애초에 `mapping_freeze_after_frac=0.0`(즉시
freeze)을 **의도적으로** 써서 "진짜 raw birth만, 최적화 전혀 없음"을 재려 한 것이라
freeze 자체가 confound가 아니라 실험 설계의 일부다.

**미해결로 남는 것**: wall time 이상치(S1 계열 전부 ~140s, S0의 101s보다 +39%)는 이번
재확인에서도 그대로(S1-nofreeze도 140.6s) — freeze 유무와 무관하게 나타나므로 원인은
따로 있음, 여전히 미확인.
