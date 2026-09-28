# 원문 근거와 선행연구 경계

페이지는 저장한 PDF의 1-based 페이지 번호다. 본문 인쇄 번호와 다를 수 있다. 아래는 원문을 확인한 **요약**이며 직접 인용문이 아니다. 다운로드 버전과 서지정보는 [PAPERS.md](PAPERS.md), 원문 링크는 각 항목에 있다. 논문의 실험을 독립 재현하지 않았다.

## A. Introduction 논리를 직접 지탱하는 연구

### A1. iMAP — 과거 관측을 재학습한다는 문제의 역사

[arXiv 2103.12352](https://arxiv.org/abs/2103.12352) · [PDF](papers/imap_2103.12352.pdf)

- **위치:** p.2 continual learning 논의; p.4 §3.6의 keyframe active sampling/bounded selection.
- **확인:** 과거 keyframe을 memory로 보관하고 loss 기반으로 재학습한다. live 구현은 과거 3개와 최근 KF·현재 프레임을 포함하는 제한된 joint optimization 집합을 쓴다.
- **연결:** 전체 history에 대한 접근과 한 iteration의 계산량 제한은 양립할 수 있다.
- **경계:** MLP의 forgetting을 명시적 Gaussian에 똑같이 가정하지 않는다. replay 자체의 최초성은 주장 불가.

### A2. Co-SLAM — 넓은 history를 작은 계산량으로 사용

[arXiv 2304.14377](https://arxiv.org/abs/2304.14377) · [PDF](papers/co_slam_2304.14377.pdf)

- **위치:** p.5 Bundle Adjustment; p.8 global BA ablation.
- **확인:** keyframe당 약 5% pixels를 저장하고 모든 과거 keyframe의 ray 집합에서 고정 수의 rays를 뽑는다. local/전역 10 KF/all-KF sampling을 비교한다.
- **연결:** 전체 시간 범위의 supervision을 유지하면서 per-step work를 제한하는 선행 사례.
- **경계:** ray 기반 implicit RGB-D BA이다. full-image Gaussian rasterization의 비용이나 dense non-KF의 필요성을 직접 증명하지 않는다. raw full-frame 영구 저장의 근거도 아니다.

### A3. MonoGS — local window-only라는 설명을 교정

[arXiv 2312.06741](https://arxiv.org/abs/2312.06741) · [PDF](papers/monogs_2312.06741.pdf)

- **위치:** pp.4–5 §3.3.2–3.3.3; p.10 supplementary keyframing.
- **확인:** covisibility/translation 기반 KF와 작은 active window를 사용한다. mapping에는 매 iteration 과거 KF 두 개도 포함한다. 제한된 view에서 생기는 Gaussian elongation을 isotropic regularization으로 다룬다.
- **연결:** local fitting과 global retention을 함께 풀어야 한다는 문제, photometric fitting만으로 geometry가 결정되지 않는 문제.
- **경계:** “MonoGS는 local window 밖을 버린다”는 표현 금지. KF 선택 자체도 이미 geometry/visibility를 고려한다.

### A4. HI-SLAM2 — 가장 구체적인 coverage mismatch

[arXiv 2411.17982](https://arxiv.org/abs/2411.17982) · [PDF](papers/hi_slam2_2411.17982.pdf)

- **위치:** p.7 §III-D/E, Fig.5; p.8 refinement 설정.
- **확인:** online photometric/geometric loss의 K는 local window, offline에서는 all keyframes다. Offline post-keyframe insertion은 flow 기반 KF들 사이 부족한 view coverage를 보완한다. 이어 full BA와 pose/map refinement를 수행한다.
- **연결:** 촬영된 trajectory가 충분해도 선택된 mapping views는 부족할 수 있다는 구체적 근거.
- **경계:** offlining은 해당 시스템의 설계이며 결함이라고 단정하지 않는다. 우리 causal admission이 같은 coverage를 회복하는지는 미검증이다. 본 조사는 v3을 사용한다.

### A5. CaRtGS — 풀을 키우면 학습 기회가 달라진다

[arXiv 2410.00486](https://arxiv.org/abs/2410.00486) · [PDF](papers/cartgs_2410.00486.pdf)

- **위치:** p.3 §III-A.2 및 Fig.2; pp.4–5 adaptive optimization, Eq.(5)–(8).
- **확인:** growing KF pool의 uniform replay에서 초기 KF가 더 많이 학습되는 long-tail 현상을 분석한다. KF별 남은 iteration 수와 최신 loss를 기록하고, quota 소진 뒤 큰 loss의 KF에 추가 기회를 준다.
- **연결:** 단순 history 유지나 uniform sampling만으로 newest-region 학습을 보장하지 못한다.
- **경계:** count-aware/compute-aware view allocation의 넓은 아이디어는 선행한다. 논문의 training-view 분석을 우리의 held-out convergence 증거로 옮기지 않는다. count-only가 loss-priority보다 낫다는 증거는 없다.

### A6. Online 3DGS Modeling with Novel View Selection — 가장 가까운 dense-view 선행연구

[arXiv 2508.14014](https://arxiv.org/abs/2508.14014) · [PDF](papers/online_nvs_2508.14014.pdf)

- **위치:** pp.4–5 §3.3; p.9 Appendix B.1; p.11 final refinement ablation.
- **확인:** shape/position-gradient 기반 uncertainty로 non-KF를 선정하고 NMS로 근접 중복을 줄인다. 최근 30 KF 구간의 후보와 이전에 선택된 20 non-KF를 유지하며, top-k non-KF를 최근 KF와 함께 학습한다. Non-KF에는 RGB 및 smoothness loss를 쓴다. Supplement는 Replica 2k, TUM/ScanNet 26k final refinement를 명시한다.
- **연결:** non-KF의 mapping 가치는 직접적인 선행 가설·실험 대상이다.
- **경계:** “non-KF 최초”, “RGB-only additional supervision 최초” 불가. 완전한 최근-window-only 방법도 아니다. reported final score를 zero-tail과 직접 비교하지 않는다.

### A7. EliGSiR — 신규성 검토에서 반드시 포함

[arXiv 2609.20348](https://arxiv.org/abs/2609.20348) · [PDF](papers/eligsir_2609.20348.pdf)

- **상태/위치:** 2026-09-17 v1 preprint; pp.2–3 view scheduling, p.5 evaluation protocol.
- **확인:** RGB-D/주어진 pose 입력. motion·overlap admission과 retained history의 priority 갱신, training residual의 공간별 replay, 측정 부하에 따른 해상도 조절을 결합한다. mapping-end는 stream 종료 뒤 bounded drain을 포함하며 추가 refinement 결과를 별도 표기한다.
- **연결:** admission과 replay를 분리하는 넓은 문제 설정까지 매우 가깝다.
- **경계:** drain 포함과 zero-tail은 다르지만, 상대가 offline-only라는 뜻은 아니다. count 기반 방식의 단순성·overhead·효과를 직접 비교해야 한다. RGB-D와 RGB+IMU 차이만으로 algorithmic novelty를 충분히 입증할 수 없다.

### A8. VIGS-SLAM — 현재 비교 기반의 버전 주의

[arXiv 2512.02293](https://arxiv.org/abs/2512.02293) · [PDF](papers/vigs_slam_2512.02293.pdf)

- **위치:** pp.7–8 §3.3; pp.8–10 baselines/metrics.
- **확인:** 새 KF당 10 mapping iterations; frame graph의 KF들과 global KF 두 개를 사용한다. v2 main evaluation은 final global BA/color refinement **이전** 결과를 보고하고, 평가 영상에서 mapping에 사용된 뷰를 제외한다.
- **연결:** KF 밖 supervision을 추가하는 mapper 개선 대상으로 적절하다.
- **경계:** 로컬 과거 실행에서 polishing 포함 수치를 발견한 사실과 최신 논문의 main protocol을 혼동하지 않는다. “VIGS 논문은 offline refinement로만 품질을 낸다”는 일반화 금지. 동명 2501.13402와도 다른 논문이다.

## B. 대안 설계와 반례

| 연구 | 읽은 위치 | 확인한 설계 | 우리 주장을 제한하는 점 |
|---|---|---|---|
| [SplaTAM](https://arxiv.org/abs/2312.02126) · [PDF](papers/splatam_2312.02126.pdf) | p.5 dense map optimization | 현재 frame+최근 KF+overlap 높은 과거 KF | 기존 GS mapper가 모두 KF만 학습한다고 일반화할 수 없음 |
| [RP-SLAM](https://arxiv.org/abs/2412.09868) · [PDF](papers/rp_slam_2412.09868.pdf) | pp.5–6 §III-C, Eq.(8) | 현재 KF, co-visible KF, 그 밖의 KF를 동적 조합 | local/global mixture 자체는 선행됨 |
| [GS3LAM](https://arxiv.org/abs/2603.27781) · [PDF](papers/gs3lam_2603.27781.pdf) | p.5 §3.3.3; p.12 discussion/ablation | semantic field의 local covisibility bias에 random KF mapping | uniform global 접근도 강한 비교군; semantic/RGB 차이 주의. arXiv 업로드는 2026, 본문/저자 repo는 ACM MM 2024 |
| [RTG-SLAM](https://arxiv.org/abs/2404.19706) · [PDF](papers/rtg_slam_2404.19706.pdf) | pp.5–6 Gaussian optimization | stable/unstable 상태로 update/render를 제한 | 역사 보존을 이미지 replay만으로 풀 필요는 없음 |
| [GLC-SLAM](https://arxiv.org/abs/2409.10982) · [PDF](papers/glc_slam_2409.10982.pdf) | pp.3–4 local mapping | active submap과 uncertainty-aware KF 선택, loop closure | single growing global pool만이 scalability 해법은 아님 |
| [Splat-SLAM](https://arxiv.org/abs/2405.16544) · [PDF](papers/splat_slam_2405.16544.pdf) | pp.4–5 §3.3 | pose/depth update를 Gaussian deformation에 반영 | 과거 RGB 재사용만으로 pose revision 문제를 해결했다고 쓰면 안 됨 |
| [Photo-SLAM](https://arxiv.org/abs/2311.16728) · [PDF](papers/photo_slam_2311.16728.pdf) | pp.3–5 §3.2–3.4 | geometry/localization과 photometric mapping의 역할 분리, pyramid 학습 | tracking–mapping decoupling 일반 개념은 신규가 아님 |
| [MVS-GS](https://arxiv.org/abs/2412.19130) · [PDF](papers/mvs_gs_2412.19130.pdf) | pp.1,3–4 | MVS depth 품질·filtering·초기화와 backend 개선 | initialization 효과와 observation schedule 효과를 나눠야 함 |
| [3DGS](https://arxiv.org/abs/2308.04079) · [PDF](papers/3dgs_2308.04079.pdf) | 초록 및 optimization 절 | calibrated multi-view에서 appearance fitting과 representation 적응 | rendering FPS는 online mapping FPS가 아님 |

GS3LAM이 MonoGS를 local covisibility 범주로 요약하더라도, 본 연구는 MonoGS 원문의 global random KF 두 개를 우선해 기록했다. Related work의 요약만 따라가면 잘못된 대비가 생긴다.

## C. Robotics 동기를 위한 자료

| 연구 | 확인 위치 | 도입에 쓸 연결 | 피해야 할 확대 해석 |
|---|---|---|---|
| [Splat-Nav](https://arxiv.org/abs/2403.02751) · [PDF](papers/splat_nav_2403.02751.pdf) | pp.1–4 navigation/representation | Gaussian map으로 localization과 collision-aware planning | 그 안전성은 지도 정확성까지 무조건 보증하는 것이 아님 |
| [SplatSim](https://arxiv.org/abs/2409.10161) · [PDF](papers/splatsim_2409.10161.pdf) | p.3 Fig.2, §IV | 렌더링된 observation으로 visuomotor policy를 학습 | physics를 GS만으로 표현하는 시스템이 아님; online mapper 검증도 아님 |
| [GS for Autonomy](https://arxiv.org/abs/2505.11794) · [PDF](papers/gs_autonomy_2505.11794.pdf) | p.6 §V-C/VI | 미탐색 환경 navigation, geometry/pose noise와 compute 제약 | 우리 PSNR 향상이 navigation 향상이라는 직접 증거는 아님 |
| [GS-VLA](https://arxiv.org/abs/2608.19066) · [PDF](papers/gs_vla_2608.19066.pdf) | pp.1–3 | VLA input의 viewpoint normalization에 GS 사용 | persistent online scene map이 필수라는 근거가 아님; preprint |

## D. 핵심 비교표 — 무엇이 이미 있고 무엇을 검증할 것인가?

| 방법 | 관측 후보/기억 | 선택·계산 배분 | 평가 주의 | 우리와 반드시 비교할 축 |
|---|---|---|---|---|
| MonoGS | local KF+과거 KF | window+random history | sensor/setup 맞춤 필요 | global replay 유무가 아니라 양·정책 |
| CaRtGS | 성장하는 KF pool | loss와 남은 quota | kernel/topology 이득 포함 | 동일 backend에서 sampler만 비교 |
| Online NVS | non-KF candidates+선별한 과거 non-KF | uncertainty+NMS+top-k | final refinement 명시 | dense 선택·유지·pose 비용 |
| EliGSiR | admitted RGB-D+retained views | map error replay+부하 해상도 | bounded drain과 post-mapping 구분 | admission/replay 비용 및 online curves |
| 우리 최신 문서 | recent KF/full KF/admitted dense | completed-step κ, 역할별 count policy | fixed-render, frozen tracker, zero-tail | wall-clock/live·bounded-memory·geometry 미검증 |

**차별점 후보는 증명할 대상이다.** 상대 논문과 다른 hyperparameter 이름을 쓴다는 사실이나 stricter protocol을 정했다는 사실만으로 더 좋은 알고리즘이 되지는 않는다. 기존 정책을 같은 backend·pose·loss·budget에서 비교하고, native system 성능은 별도 실험으로 보고해야 한다.
