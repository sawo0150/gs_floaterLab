# 02 — 문헌 조사: 자유공간(free space)을 확률로 다루는 법

> 목적: [01](01_current_formulation_audit.md)에서 나온 결함 A~H 각각에 대해,
> **이미 확립된 수학적 처방이 있는지** 확인한다. 결론부터: 전부 있다. 우리가
> 재발명한 것들이 각각 어느 문헌의 어느 형태에 대응하는지 매핑한다.
>
> 조사일 2026-09-01. 각 항목은 "이 프로젝트에 무엇을 주는가"까지 적는다.

---

## 1. 점유격자(occupancy grid) — 결함 A/B/C/D의 정본

### 1.1 log-odds 베이즈 갱신 (표준)

Elfes(1989), Thrun-Burgard-Fox *Probabilistic Robotics* ch.9, OctoMap(Hornung et al.,
Autonomous Robots 2013)의 공통 형태:

```
l(m_v | z_{1:t}) = l(m_v | z_{1:t−1}) + l(m_v | z_t) − l₀
l(x) = log( p(x) / (1 − p(x)) )
```

즉 **로그 오즈에서는 증거가 그냥 덧셈**이고, `l(m_v|z_t)`가 inverse sensor model,
`l₀`가 사전분포다.

**우리에게 주는 것:**
- 결함 D 직행. `terminal_weight=3.0`은 `l_occ / |l_free|` 비의 손튜닝 대체물이다.
  OctoMap 기본 `l_occ=0.85, l_free=−0.4`(비 ≈2.1)와 자릿수가 같다는 게 우연이 아니다.
  **이 비는 센서 노이즈/outlier율에서 유도되는 양이지 튜닝 상수가 아니다.**
- 결함 A 직행. `l₀`가 곧 미관측 voxel의 기본값. log-odds 0 = p=0.5 = "모름"이며,
  현재 코드의 "미관측 → score 0 → 확실히 점유"와 정면으로 다르다.
- 덧셈 구조라 **스트리밍/causal에 그대로 맞는다** (과거 ray 재방문 불필요).
  causal carve가 자체적으로 만족시키려 애쓴 성질이 공짜로 나온다.

### 1.2 Beta / Dirichlet 사후, 그리고 evidential 확장

`transit/(transit+w·terminal)`은 §1.1의 확률 버전이자 **Beta(α,β) 사후 평균**이다.
Beta로 명시하면 **분산**이 따라온다:

```
E[p_free] = α/(α+β)
Var[p_free] = αβ / ((α+β)²(α+β+1))
```

evidential(Dempster-Shafer) 문헌은 여기서 한 발 더 나가, **"자유"와 "점유" 사이의
갈등**과 **"정보 없음(ignorance)"**을 별도 자유도로 분리한다 — Dirichlet 사후와
DS belief function 사이에 전단사 대응이 있다는 게 표준 결과다.

**우리에게 주는 것:**
- 결함 B 직행. `transit=1`과 `transit=100`을 분산이 구분해준다.
- 결함 E 직행. 사후분포가 있으면 `gate_score=0.95`를 **"P(free) > 0.95를 신용구간
  하한이 넘을 때"**라는 검정으로 바꿀 수 있다. 그제서야 0.95가 확률이 된다.
- ignorance 분리는 우리 상황(스트리밍 초기 = 대부분 미관측)에 특히 유용하다.
  "아직 안 봤다"와 "봤는데 비어 있다"를 섞지 않는 것 자체가 exp69 실패
  (frontier 근처 과잉 삭제) 진단에 쓸 수 있는 축이다.

### 1.3 상관 관측 / 유효표본수

점유격자 문헌의 알려진 약점이 정확히 우리 결함 C다: 표준 베이즈 갱신은
**측정 간 독립을 가정**하는데, 고프레임 카메라는 이를 심하게 위반해
로그 오즈가 포화(±clamp)되고 과신한다. OctoMap이 log-odds에 `clamping threshold`를
두는 것 자체가 이 문제의 실용적 인정이다.

정공법은 유효표본수(ESS)로 나누는 것:
```
α_eff = α / κ,  β_eff = β / κ     (κ = 중복도, 관측 기하에서 추정)
```

**우리에게 주는 것:** Fisher LUT(§01 2.1)와 `prune_persistence`(§01 2.2)를
**하나의 κ**로 통합할 근거. 그리고 κ는 ray 방향 산포 행렬 `Σ dᵢdᵢᵀ`에서 직접
계산되므로 13-line 양자화가 필요 없다.

### 1.4 연속 점유 표현

Gaussian Process Occupancy Maps(O'Callaghan & Ramos 2012), Hilbert Maps
(Ramos & Ott 2016), Bayesian Hilbert Maps(Senanayake & Ramos 2017): voxel 격자
대신 연속 함수로 점유를 두고 불확실성까지 낸다.

**우리에게 주는 것:** 장기적으로 `voxel=0.10m` 격자 해상도 상수를 없앨 수 있는 경로.
다만 **지금 채택하지 않는다** — 실시간 예산에 부담이고, 결함 A~H를 고치는 데
필수가 아니다. 격자 유지 + 사후분포 도입이 비용 대비 이득이 훨씬 크다.

---

## 2. 볼륨 렌더링 자체가 주는 자유공간 가능도 — 결함 F의 정본

이게 **가장 중요한 항목**이고, 현재 구현에 완전히 빠져 있는 관점이다.

NeRF/3DGS의 렌더링 모형은 이미 확률모형이다. ray를 따라 밀도 `σ(t)`가 있을 때

```
투과율   T(t) = exp( − ∫₀ᵗ σ(s) ds )
종료밀도 h(t) = T(t) · σ(t)          ← ray가 t에서 멈출 확률밀도
```

`h(t)`는 진짜 확률밀도다(∫h = 1 − T(∞)). 그러면:

> **"이 ray가 깊이 D까지 아무것에도 막히지 않고 도달했다"는 사건의 확률은 정확히 `T(D)`이고,
> 그 음의 로그 가능도는 `−log T(D) = ∫₀^D σ dt` = 표면 앞 누적 광학두께다.**

즉 **자유공간 carve loss는 발명할 필요가 없다. 렌더러가 이미 정의하고 있고,
그 값은 "표면 앞에 쌓인 광학두께"다.** 3DGS에서 한 Gaussian `j`가 이 적분에
기여하는 양은 `o_j × (그 ray 위에서의 Gaussian 밀도 선적분)`이므로,
**Gaussian의 scale과 방향이 자동으로 들어온다** — 현재 `score_j · σ(o_j)`가
버린 바로 그 의존성이다(결함 F).

---

## 3. depth 감독을 확률로 쓰는 계열 — 결함 H의 정본

### 3.1 DS-NeRF (Deng et al., CVPR 2022)

기댓값 depth의 L1을 쓰지 않고, **ray 종료 분포에 대한 KL**을 쓴다:

```
D̂_ij ~ N(D_ij, σ̂_i)                                  # COLMAP depth를 노이즈 측정으로
L_depth = E[ KL( δ(t − D̂) ‖ h(t) ) ]
        = E_x[ − Σ_k log h_k · exp( −(t_k − D_ij)² / (2σ̂_i²) ) · Δt_k ]
```

핵심 두 가지:
1. **깊이에 명시적 불확실성 `σ̂_i`가 있다** (COLMAP은 재투영 오차로 준다).
2. **다봉 분포를 올바르게 다룬다.** 기댓값 depth를 안 쓰므로 [01 §4]의 4번 문제
   (floater 있으면 기댓값이 중간에 떠서 진짜 표면까지 민다)가 구조적으로 없다.

**우리에게 주는 것:** frontier carve의 hinge를 대체할 정확한 형태.
그리고 우리는 COLMAP이 아니라 DROID/BA depth를 쓰므로 `σ̂`를 **BA 공분산에서
진짜로 가져올 수 있다** — DS-NeRF보다 유리한 위치다.

### 3.2 Urban Radiance Fields (Rematas et al., CVPR 2022) — line-of-sight loss

lidar ray에 대해 (a) 표면 앞 구간의 가중치를 0으로 미는 **empty-space 항**과
(b) 측정 깊이 주변에 가우시안 모양의 가중치를 요구하는 **near-surface 항**을 나눠 건다.
DS-NeRF와 함께 "적분 기반 depth 감독"의 두 표준 형태로 통용된다.

**우리에게 주는 것:** 우리 carve(자유공간)와 기존 depth loss(표면)를 **따로 튜닝되는 두
loss로 두지 말고 하나의 가능도에서 나오는 두 항으로 묶으라**는 설계 근거.
현재 `carve_lambda=0.05`와 depth L1의 `×5` 가중치가 서로 독립으로 튜닝되고 있는데,
같은 측정에서 나온 두 항이라면 상대 가중치는 **노이즈 모형이 결정**해야 한다.

### 3.3 Mip-NeRF 360 distortion loss (Barron et al., CVPR 2022)

깊이 감독 없이도 `h(t)`가 **한 곳에 모이도록** 하는 정규화. floater는 본질적으로
`h(t)`의 가짜 mode이므로 직접 겨냥한다.

**우리에게 주는 것:** depth가 없는/못 믿는 영역(Aria monocular의 먼 영역)에 쓸
보조 항. 우리 결함 목록에는 없지만 30dB 단계에서 후보.

### 3.4 depth outlier 모형 (Vogiatzis & Hernández 2011)

깊이 측정을 **inlier Gaussian + outlier Uniform 혼합**으로 두고, inlier 비율에
Beta 사전을 걸어 같이 추정한다. SVO/REMODE 계열의 depth filter 표준.

**우리에게 주는 것:** [01 §4]의 3번(hinge가 outlier에 무한 반응) 해결.
그리고 Beta가 여기서도 나온다는 점이 중요 — **§1.2의 점유 Beta와 §3.4의 inlier Beta를
같은 프레임에 놓을 수 있다.** 03에서 실제로 그렇게 묶는다.

---

## 4. 3DGS floater 문헌 (2024–2026) — 남이 뭘 했는지

| 방법 | 접근 | 확률모형인가 | 비고 |
|---|---|---|---|
| SparseGS (Xiong et al. 2023) | mode-selected depth vs alpha-blended depth의 상대차로 floater mask → 학습 말미 prune | ✗ (임계값 휴리스틱) | 다봉 진단 아이디어는 유용 |
| Floaters No More (Philip & Deschaintre, EGSR 2023) | 카메라 근처 gradient scaling | ✗ | 원인(근거리 과적합) 특정은 명확 |
| Nerfbusters (Warburg et al., ICCV 2023) | 3D diffusion prior로 "그럴듯한 국소 기하" 학습 후 정리 | 학습된 prior | 데이터 필요, 온라인 부적합 |
| StableGS (2025) | cross-view depth 일관성 + dual-opacity. 저자들이 자기 방법을 **"TSDF fusion의 명시적 버전"**이라 서술 | 준-확률 | **우리와 문제의식이 같다** |
| EFA-GS (2025) | floating artifact 제거 | ✗ | |
| TIDI-GS (2026) | Gaussian별 **evidence log** 유지: 낮은 opacity / 낮은 multi-view visibility / 낮은 최적화 활동 / 높은 공간적 고립 | ✗ (약신호 합산) | **현재 우리 causal carve와 거의 같은 계열** — 즉 우리 방식이 유별나게 나쁜 건 아니지만, 이 계열 전체가 확률모형이 아니다 |
| BDGS-SLAM (2025) | 베이지안 필터링 + co-visible keyframe 다중뷰 확률 갱신 | ✓ | 동적 물체 대상이지만 **갱신 구조가 우리가 원하는 형태** |
| VBGS-SLAM (2026) | 변분 베이즈, 폐형(closed-form) 갱신 | ✓ | exp65 M2(closed-form 색)가 기각된 이력이 있으니 참고만 |

> **문헌 조사에서 나온 가장 쓸모 있는 사실:** 3DGS floater 문헌의 주류(TIDI-GS,
> SparseGS, EFA-GS)는 **우리와 똑같이 휴리스틱 증거 점수 방식**이다. 즉
> "남들은 다 확률모형인데 우리만 엔지니어링"이 아니다. 그러나 **점유격자/depth 감독
> 쪽(§1, §3)에는 30년 된 정본이 있고, 3DGS 쪽이 그걸 아직 제대로 안 가져다 썼다.**
> 이건 비판이 아니라 **기회**다 — 우리가 이미 SLAM ray를 갖고 있으므로
> 그 접목을 할 수 있는 위치에 있고, 그게 논문거리다.

---

## 5. 결함 → 처방 매핑 (요약)

| 결함 | 처방 | 출처 |
|---|---|---|
| A 사전분포 없음 | log-odds `l₀`, Beta(α₀,β₀) | §1.1, §1.2 |
| B 불확실성 미사용 | Beta 사후 분산 / evidential ignorance | §1.2 |
| C 독립성 위반 | ESS 보정 κ = ray 방향 산포에서 | §1.3 |
| D `w_t=3.0` | inverse sensor model에서 유도 | §1.1 |
| E score가 확률 아님 | 사후확률 복원 + 신용구간 검정 | §1.2 |
| F opacity 가중치 미유도 | `−log T(D) = ∫σdt` (렌더러 자체 가능도) | §2 |
| G 삭제 오류율 없음 | Bayes 위험 최소화 결정규칙 | §1.2 + 결정이론 |
| H frontier hinge | ray 종료분포 KL + inlier/outlier 혼합 | §3.1, §3.2, §3.4 |

---

## Sources

- [Depth-supervised NeRF: Fewer Views and Faster Training for Free (ar5iv)](https://ar5iv.labs.arxiv.org/html/2107.02791) / [arXiv PDF](https://arxiv.org/pdf/2107.02791)
- [Depth-Supervised NeRF 개요 (emergentmind)](https://www.emergentmind.com/papers/2107.02791)
- [Occupancy Grid Map (OGM): Fundamentals](https://www.emergentmind.com/topics/occupancy-grid-map-ogm)
- [MRFMap: Online Probabilistic 3D Mapping using Forward Sensor Models (RSS 2020)](https://www.roboticsproceedings.org/rss16/p060.pdf)
- [Tightly-Coupled LiDAR-Visual-Inertial SLAM and Large-Scale Volumetric Occupancy Mapping](https://arxiv.org/pdf/2403.02280)
- [Deep Inverse Sensor Models as Priors for evidential Occupancy Mapping](https://arxiv.org/html/2012.02111)
- [DS-K3DOM: 3-D Dynamic Occupancy Mapping with Kernel Inference and Dempster-Shafer Evidential Theory](https://arxiv.org/pdf/2209.07764)
- [A Simulation-based End-to-End Learning Framework for Evidential Occupancy Grid Mapping](https://arxiv.org/pdf/2102.12718)
- [EvidMTL: Evidential Multi-Task Learning for Uncertainty-Aware Semantic Surface Mapping](https://arxiv.org/html/2503.04441v2)
- [SparseGS: Sparse View Synthesis using 3D Gaussian Splatting](https://arxiv.org/pdf/2312.00206)
- [StableGS: A Floater-Free Framework for 3D Gaussian Splatting](https://arxiv.org/pdf/2503.18458) / [개요](https://www.emergentmind.com/topics/stablegs)
- [TIDI-GS: Floater Suppression in 3D Gaussian Splatting for Enhanced Indoor Scene Fidelity](https://arxiv.org/html/2601.09291)
- [EFA-GS: Eliminating Floating Artifacts in 3DGS](https://www.emergentmind.com/topics/eliminating-floating-artifacts-gaussian-splatting-efa-gs)
- [BDGS-SLAM: A Probabilistic 3D Gaussian Splatting Framework for Robust SLAM in Dynamic Environments](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12610981/)
- [VBGS-SLAM: Variational Bayesian Gaussian Splatting SLAM](https://arxiv.org/html/2604.02696)
- [FreeSplat++: Generalizable 3DGS for Efficient Indoor Scene Reconstruction](https://arxiv.org/pdf/2503.22986)

---

다음: [03 — 제안 확률모형](03_probabilistic_model.md)
