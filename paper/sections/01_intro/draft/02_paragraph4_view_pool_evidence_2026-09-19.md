# 문단 4 검토: keyframe 중심 학습과 growing training-view pool

검토일: 2026-09-19. Method 3.1–3.3과 GS-SLAM 11편의 관측 선택·mapping 관련 절을 대조했다. 논문의 모든 주장이나 구현 전체를 검증한 전수조사는 아니다. 아래 판정은 명시된 논문 버전의 **온라인 Gaussian map 학습에 사용하는 영상**에 관한 것이다. Tracking 입력, Gaussian 생성용 관측, 평가용 영상, 종료 후 refinement를 구분했다.

## 1. 결론

문단 4는 **keyframe 중심으로 제한되는 학습 관측의 범위**를 출발점으로 삼을 수 있다. 그러나 **전체 학습 pool의 크기가 고정되어 확장할 수 없다**는 일반화는 원문과 맞지 않는다.

- **관측 후보 pool:** 나중에라도 mapping에서 다시 선택할 수 있도록 보유한 학습 영상 집합.
- **활성 window/batch:** 특정 mapping 단계 또는 iteration에서 실제로 사용하는 부분집합.
- **편입 규칙:** 새 관측이 후보 pool에 들어오는 조건. Keyframe 선택, 고정 frame 간격, 완료된 update에 따른 admission 등이 해당한다.

작은 활성 window가 전체 pool의 고정 크기를 뜻하지 않는다. 저장된 keyframe이 늘어나는 방식도, tracking keyframe 밖의 RGB 관측을 별도 학습 대상으로 편입하는 방식과는 다르다. 우리가 바꾸는 핵심은 한 번에 더 많은 영상을 렌더링하는 것이 아니라, **학습 후보를 tracking keyframe 밖으로 넓히고 그 편입 속도를 완료된 최적화량에 연결하는 것**이다.

## 2. 원문별 판정

| 연구 | 온라인 map 학습에 사용하는 관측 | 제한의 실체 | 문단 4에서의 사용 |
|---|---|---|---|
| MonoGS | 공가시성 기반 keyframe window와 매 iteration 뽑는 과거 keyframe 2개 | 활성 local window 제한; 과거 keyframe 재사용 가능 | Keyframe 중심 학습의 대표 사례. 전체 pool 고정/과거 영상 영구 삭제의 근거는 아님 |
| Photo-SLAM | Localization이 제공한 keyframe 영상 | 현재 공식 구현은 scene의 keyframe 집합에서 재학습 영상을 선택 | Frontend keyframe과 map supervision의 연결 사례. 작은 고정 pool로 묶으면 안 됨 |
| CaRtGS | 성장하는 keyframe pool에서 학습 잔여 횟수가 있는 keyframe | Pool은 새 keyframe으로 확장; loss로 학습 기회 조정 | 기존 불균형 대응을 인정하고 admission과 구분 |
| VIGS-SLAM | Tracking frame graph의 keyframe과 global keyframe 2개 | 새 keyframe당 mapping iteration 규칙 및 local/global 선택 | 우리의 backbone에 가장 직접적인 사례 |
| HI-SLAM2 | Online local-window keyframe; offline에는 전체 keyframe | Online window와 종료 후 전체 refinement가 다름 | Keyframe 중심 online 학습 및 offline 추가 관측 보완의 직접 근거 |
| Splat-SLAM | Optical flow와 mapping용 선택을 거친 local-window keyframe | Online map update의 local window | Keyframe 중심 사례. 선택이 tracking만 고려한다고 쓰면 안 됨 |
| RP-SLAM | 새 keyframe + 공가시 keyframe 표본 + 비공가시 keyframe 표본 | 전체 keyframe 집합에서 매 iteration window 재구성 | 고정 pool이 아니라 dynamic window 사례 |
| AERGS-SLAM | Localization의 posed keyframe; 시간 정보를 반영한 sliding window 학습 | Keyframe 중심 training set과 window 내 해상도 조정 | Keyframe을 train, 나머지를 test로 명시한 분명한 사례 |
| Gaussian-SLAM | 활성 submap에 속한 keyframe; 새 keyframe에 iteration의 절반 이상 배분 | Submap별 학습 관측; 일정 keyframe 수 뒤 새 submap | 지역별 관측 제한 사례. 전체 시스템 pool 고정이나 tracking-only 선택은 아님 |
| SplaTAM | 현재 frame + 최근 keyframe + overlap이 큰 과거 keyframe | 한 번에 최적화하는 부분집합 | **엄밀한 keyframe-only 주장에서는 제외** |
| RTG-SLAM | 최근 time window의 RGB-D frame + 별도의 global keyframe 학습 | Local frame window와 global replay의 두 경로 | **엄밀한 keyframe-only 주장에서는 제외** |

### MonoGS — Gaussian Splatting SLAM, CVPR 2024

[원문](https://openaccess.thecvf.com/content/CVPR2024/papers/Matsuki_Gaussian_Splatting_SLAM_CVPR_2024_paper.pdf), §3.3.2–3.3.3, PDF p.5.

전체 stream을 joint optimization하는 비용 때문에 작은 keyframe window를 유지한다. Keyframe 선택에는 Gaussian 공가시성·상대 이동을 사용하며, window 밖의 과거 keyframe 두 개도 재사용한다. 원문은 좋은 multiview constraints를 위한 선택을 명시하므로 **mapping을 전혀 고려하지 않은 tracking용 선택**이라고 비판하면 안 된다. 뒷받침되는 주장은 **선택된 keyframe들이 mapping supervision의 범위를 정한다**는 것이다.

### Photo-SLAM — CVPR 2024

[원문](https://openaccess.thecvf.com/content/CVPR2024/papers/Huang_Photo-SLAM_Real-time_Simultaneous_Localization_and_Photorealistic_Mapping_for_Monocular_Stereo_CVPR_2024_paper.pdf), §3.2–3.4; [공식 mapping 코드](https://github.com/HuajianUP/Photo-SLAM/blob/main/src/gaussian_mapper.cpp), 2026-09-19 조회.

논문은 keyframe pose에서 영상을 렌더링하여 appearance를 최적화한다. 코드에서는 새 keyframe을 scene에 추가하고, `generateKfidRandomShuffle`이 scene의 keyframe 수를 사용한다. `useOneRandomSlidingWindowKeyframe`이라는 함수명에도 불구하고 실제 후보는 scene의 keyframe 집합이며 학습 잔여 횟수도 사용한다. 함수명만 보고 고정 sliding-window pool이나 독립 균등 추출이라고 단정하지 않는다. 현재 코드와 게재 당시 구현은 동일 버전으로 간주하지 않는다.

### CaRtGS — arXiv:2410.00486v2

[원문](https://arxiv.org/html/2410.00486v2), §III-A2, §III-B2, Eqs. (6)–(9).

새 keyframe을 기존 pool에 합치는 식을 명시한다. 잔여 학습 횟수가 있는 keyframe 중에서 선택하고, 잔여 횟수를 소진하면 loss에 따라 다시 학습 기회를 배정한다. 따라서 **고정 크기 pool**, **재학습 불균형을 무시**, **아무 학습 배분도 하지 않음**이라는 비판은 모두 부적절하다. 본 버전의 해당 절은 §III-B2이며, 이전 분석에 적힌 §III-D와 구분한다. 추가 non-keyframe 관측의 admission과 pool 내부 학습 배분을 구별하는 근거로 사용한다.

### VIGS-SLAM — arXiv:2512.02293v2

[원문](https://arxiv.org/html/2512.02293v2), §3.3 Map Management.

새 keyframe depth를 역투영하여 Gaussian을 생성하고, keyframe당 10 mapping iteration을 수행한다. 각 iteration은 tracking frame graph의 keyframe과 두 global keyframe을 사용한다. **좋은 dense initialization과 학습 관측의 범위는 별개**라는 연결에 적합하다. 이 규칙 자체로 GPU 낭비나 불충분한 학습을 실증했다고 쓰지 않는다. 종료 후 color refinement는 online mapping과 분리한다.

### HI-SLAM2 — arXiv:2411.17982v3, T-RO

[원문](https://arxiv.org/html/2411.17982v3), §III-D Optimization Losses 및 §III-E Post-Keyframe Insertion, Figure 5, PDF p.7.

Online loss는 local-window keyframe을 사용하며 새 keyframe마다 10 iteration을 수행한다. 종료 후에는 coverage가 부족한 위치에 keyframe을 추가하고 전체 BA 및 map refinement를 수행한다. 원문은 online optical-flow 기반 선택만으로는 미래 궤적 없이 coverage를 완전히 평가할 수 없다는 점을 설명한다. 이는 **선택된 keyframe 외의 관측이 재구성에 도움이 될 수 있다**는 직접적인 근거다. 다만 이 offline 보완을 우리의 causal online admission과 같은 방법으로 설명하지 않는다.

### Splat-SLAM — CVPR Workshops 2025 게재판

[원문](https://openaccess.thecvf.com/content/CVPR2025W/VOCVALC/papers/Sandstrom_Splat-SLAM_Globally_Optimized_RGB-only_SLAM_with_3D_Gaussians_CVPRW_2025_paper.pdf), §3.2 Keyframe Selection and Optimization, Eq. (11).

Optical-flow threshold에 더해 MonoGS의 keyframe 선택 규칙으로 중복 mapping frame을 줄인다. Gaussian parameter update는 local keyframe window에 배치한다. 따라서 **keyframe 중심**의 사례이지만, **관측 선택은 오직 tracking을 위한 것**이라는 설명의 근거는 아니다. Tracking keyframe buffer 크기와 mapping 학습 후보 집합도 혼동하지 않는다.

### RP-SLAM — arXiv:2412.09868v1

[원문](https://arxiv.org/html/2412.09868v1), §III-C Dynamic Keyframe Window, Eq. (8).

기존 keyframe을 공가시·비공가시 집합으로 나누고, 두 집합의 표본과 새 keyframe으로 매 iteration window를 재구성한다. 새 영역만 학습해 과거를 잊는 문제를 이미 다룬다. **Window membership의 동적 변경**과 **전체 후보 pool의 non-keyframe 확장**은 별개다. 작은 window를 사용해도 전체 pool이 고정됐다고 볼 수 없다.

### AERGS-SLAM — CVPR 2026

[원문](https://openaccess.thecvf.com/content/CVPR2026/papers/Zhou_AERGS-SLAM_Auto-Exposure-Robust_Stereo_3D_Gaussian_Splatting_SLAM_CVPR_2026_paper.pdf), §3.3.2, §4.1, PDF p.5.

Localization이 제공한 keyframe을 training set으로, 나머지 frame을 testing set으로 사용한다고 명시한다. Window 안의 체류 시간을 이용해 각 영상의 supervision 해상도를 바꾸므로, 기존 연구가 관측의 시간적 차이를 전혀 고려하지 않았다는 주장에는 반례다. 이를 우리 평가와 비교할 때는 system-dependent non-keyframe test split과 공통 held-out split의 차이도 확인해야 한다.

### Gaussian-SLAM — arXiv:2312.10070v1

[원문](https://arxiv.org/html/2312.10070v1), §4.1, §5 Implementation Details.

일정 keyframe 수 뒤 새 submap을 만들고 활성 submap의 keyframe들을 학습한다. 새 keyframe에 전체 iteration의 최소 절반을 배정한다. 실험에서 매 5번째 frame을 keyframe으로 삼는다. 특히 v1의 rendering/reconstruction 결과는 DROID-SLAM trajectory를 사용한다고 명시하므로, 결과 전체를 자체 tracking의 완전 실시간 실증으로 소개하지 않는다. 이 버전은 **제한된 iteration에서 새 관측에 충분한 학습을 배분해야 한다**는 선행 문제의식도 이미 제시한다.

### SplaTAM — CVPR 2024: keyframe-only로 묶으면 안 되는 사례

[원문](https://openaccess.thecvf.com/content/CVPR2024/papers/Keetha_SplaTAM_Splat_Track__Map_3D_Gaussians_for_Dense_RGB-D_CVPR_2024_paper.pdf), §4 Gaussian Map Updating.

매 n번째 frame을 keyframe으로 저장하지만, mapping에는 현재 frame, 최근 keyframe, overlap이 큰 k−2개 과거 keyframe을 사용한다. **장기 저장 keyframe pool이 있다**는 사실이 **현재 non-keyframe을 전혀 학습하지 않는다**는 뜻은 아니다. 제한된 active subset의 근거로만 사용할 수 있다.

### RTG-SLAM — arXiv:2404.19706v1: 두 학습 경로를 구분할 사례

[원문](https://arxiv.org/html/2404.19706v1), §3.2 Gaussian optimization 및 Keyframes and global optimization.

최근 time window의 RGB-D frame 중 하나를 뽑아 local optimization하고, 별도로 새 keyframe과 과거 keyframe 세 개를 이용해 global optimization한다. 종료 후 전체 keyframe을 사용하는 정제도 있다. Local 일반 frame 학습을 빠뜨린 채 global keyframe 경로만 설명하면 keyframe-only로 잘못 분류하게 된다.

## 3. Method와 맞춰 좁힌 gap

현재 기준: `paper/latex/sec/4_method.tex`, §3.1–3.3.

1. **학습 후보 범위:** 선택된 keyframe에서 학습 영상을 뽑는 규칙은 그 밖의 관측을 지속적인 supervision 후보로 축적하는 규칙과 다르다. Tracking keyframe과 mapping training view를 분리한다는 것이 §3.1의 핵심이다.
2. **성장의 비용:** 후보가 많아져도 동일한 총 update에서 각 관측을 재학습할 기회가 자동으로 늘지는 않는다. 따라서 gap은 무제한 확장이 불가능하다는 사실이 아니라, **추가 관측을 편입하는 속도와 실제 학습 여력의 조정 문제**다.
3. **기존 관측 유지:** Window에서 빠진 영상이 모든 시스템에서 영구 폐기되는 것은 아니다. MonoGS/RP-SLAM의 global replay와 Photo-SLAM/CaRtGS의 pool을 인정해야 한다. 우리의 과거 training view 유지를 최초의 replay로 주장하지 않는다.
4. **누적 학습 기회:** §3.2의 균등 추출은 비교용 단순 규칙이다. 모든 baseline이 이 규칙을 쓴다고 단정하지 않는다. CaRtGS·Gaussian-SLAM 등의 별도 배분을 인정한 뒤, 성장하는 확장 pool에서의 count 기반 설계를 설명한다.
5. **기하:** §3.3은 문단 5의 역할이다. 문단 4에 ray/opacity 논의를 섞지 않는다.

### Method에서 수정 검토가 필요한 표현 — TeX는 이번에 수정하지 않음

- `Several real-time GS-SLAM systems optimize the map using a bounded set of keyframes [15,16,17].`는 **활성 keyframe subset/window**를 뜻하도록 좁히고 실제 인용을 연결해야 한다. 고정 전체 pool로 읽히지 않게 한다. MonoGS·Splat-SLAM은 이를 뒷받침하지만 Photo-SLAM·CaRtGS는 동일 분류가 아니다.
- Keyframe selection이 dense photometric supervision만을 위해 설계되지 않았다는 말은 가능하지만, **mapping을 고려하지 않는다**는 말은 MonoGS/Splat-SLAM에 맞지 않는다.
- `removing earlier views`의 영향을 특정 시스템의 영구 삭제로 귀속하려면 실제 culling/retention 규칙을 확인해야 한다. 모든 window 방법의 공통 실패로 쓰지 않는다.
- 우리의 후보 pool도 κ와 도착한 영상 수에 의해 제한된다. 그러므로 “기존은 bounded, 우리는 unbounded”는 방법 수식과도 맞지 않는다. 차이는 **고정 크기 또는 keyframing만으로 정하는 후보 규칙과, 완료 update에 연결한 admission**이다.

## 4. 현재 결과가 지지하는 범위

`paper/latex/sec/5_results.tex`, `tab:abl`과 `tab:order`의 현재 값을 확인했다. 실행을 새로 검증하거나 추가 실험한 것은 아니다.

- 중간 영상 추가: 전체 PSNR 23.31 → 23.65 dB, UTMM 20.25 → 21.12, Aria 28.50 → 29.25. 그러나 RPNG는 23.41 → 23.06으로 하락한다. **추가 관측의 잠재적 이득과 정책 설계 필요성**은 설명할 수 있지만 모든 데이터셋에서 개선됐다고 쓰면 안 된다.
- View sampling: 15/30/60 update budget에서 random reshuffling과 entropy-regularized sampling을 비교한다. 이는 성장 속도의 효과를 독립적으로 검증한 실험과 다르다.
- 현재 채워진 표만으로 **즉시 추가 vs 고정 간격 추가 vs 완료 update 기반 추가**의 독립 비교를 확인할 수 없다. 관련 slot·주석의 계획을 완료된 결과로 간주하지 않는다.
- 같은 update 수가 같은 시간·메모리 비용을 보장하지는 않는다. Training view retention과 큰 pool을 장점으로 내세우면 pool 저장 비용과 sampling 비용도 보고해야 한다.
- Count는 학습 기회의 지표다. 적게 선택된 영상이 반드시 가장 정보량이 많거나 PSNR 개선량이 가장 크다는 뜻은 아니다.

## 5. 문단 4 구성 결정

**Keyframe 중심의 관측 후보 → 그 후보 내의 제한된 활성 선택 → 중간 appearance 관측의 활용 여지 → 단순 확장의 학습 비용 → 완료된 최적화에 연결한 admission·배분.**

Introduction에는 11편을 모두 나열하지 않는다. 기존 draft에 이미 정리된 Photo-SLAM·VIGS-SLAM, MonoGS·HI-SLAM2로 관측 후보와 window를 설명하고, CaRtGS는 학습 배분을 이미 다룬 선행연구로 인용한다. HI-SLAM2의 offline 추가 관측 근거와 다른 사례·반례는 이 메모 및 Related Work용으로 보관한다.

최종적으로 주장할 gap은 **“학습 pool의 크기가 고정되어 더 늘릴 수 없다”가 아니라 “선택된 keyframe 중심의 학습을 더 넓은 관측 집합으로 확장하되, 이를 충분히 학습할 수 있는 진행량에 맞추는 규칙이 필요하다”**이다. 이는 문헌 전체에 대한 불가능성/최초성 주장이 아니라, 우리 시스템에서 해결하고 검증할 구체적인 설계 문제다.

## 6. 로컬 원문

이번에 추가한 PDF 8편은 `paper/ref/view_selection/`에 보관했다. Photo-SLAM·CaRtGS는 기존 `paper/ref/convergence/`의 원문을 사용했고, VIGS-SLAM은 arXiv v2 HTML의 §3.3을 확인했다. Photo-SLAM 공식 코드의 조회일은 위에 명시했다. 수식·본문 배치는 MonoGS p.5, HI-SLAM2 p.7, AERGS-SLAM p.5를 렌더링하여 확인했다.
