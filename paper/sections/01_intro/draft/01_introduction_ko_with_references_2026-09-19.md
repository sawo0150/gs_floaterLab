# Introduction 한국어 초안과 문단별 인용 근거

작성일: 2026-09-19

이 문서는 사용자가 제안한 7문단 구성에 따라 작성한 검토용 초안이다. 현재 `paper/latex/sec/1_intro.tex`와 `4_method.tex`, 그리고 아래에 연결한 논문 원문·저자 프로젝트 페이지를 기준으로 한다. 이전 `paper/` Markdown 계획은 현재 원고의 근거로 사용하지 않았다. TeX는 수정하지 않았다.

앞부분은 논문에 들어갈 연결된 한국어 문장이고, 뒷부분은 인용 선택을 검토하기 위한 연구 메모다. 각 문단 제목은 역할을 보여주기 위한 것으로 최종 Introduction의 소제목을 뜻하지 않는다. 문장들은 새로 작성한 초안이며 외부 논문의 직접 인용문이 아니다.

## 1. Introduction 한국어 초안

### 문단 1 — Field: 관측 도중 사용할 수 있는 지도의 필요성

로봇과 웨어러블 증강현실 시스템은 환경을 관측하는 동안에도 지도를 사용해야 한다. 장면의 외관을 재구성한 지도는 새로운 시점에서의 시각화를 지원하고, 기하적으로 정확한 지도는 가림 관계의 판단과 주변 공간과의 상호작용을 가능하게 한다. 따라서 이러한 응용에서는 관측을 모두 마친 뒤 얻는 최종 재구성 품질뿐 아니라, 관측이 진행되는 동안 확보되는 지도 품질이 중요하다. 새로운 관측이 들어올 때마다 지도를 확장하고 개선하여, 데이터 수집이 끝나기 전에도 활용할 수 있는 장면 표현을 제공해야 한다.

### 문단 2 — Map: 3DGS와 온라인 매핑

색 정보를 가진 명시적인 Gaussian primitive로 표현된 지도는 효율적으로 렌더링하고 영상 기반 최적화를 통해 개선할 수 있다. 이러한 표현인 3D Gaussian Splatting(3DGS)은 고품질의 새로운 시점 영상 합성과 빠른 렌더링을 결합한다.[[1]](https://repo-sam.inria.fr/fungraph/3d-gaussian-splatting/) 최근 SLAM 연구는 이를 카메라 tracking과 함께 수행하는 지도 구축으로 확장하였다.[[2]](https://openaccess.thecvf.com/content/CVPR2024/html/Matsuki_Gaussian_Splatting_SLAM_CVPR_2024_paper.html)[[3]](https://openaccess.thecvf.com/content/CVPR2024/papers/Keetha_SplaTAM_Splat_Track__Map_3D_Gaussians_for_Dense_RGB-D_CVPR_2024_paper.pdf) 그러나 빠른 렌더링이 빠른 지도 개선을 의미하지는 않는다. 현재 지도를 높은 프레임률로 표시하더라도 최근에 관측한 영역은 여전히 충분히 재구성되지 않은 상태일 수 있다. 온라인 매핑은 tracking과 연산 자원을 공유하므로, 관측이 도착하는 동안 완료할 수 있는 지도 최적화 단계, 즉 mapping update의 수가 제한된다. 따라서 핵심 과제는 이러한 제한된 update를 효율적으로 활용하여 쓸 수 있는 품질의 지도를 확보하는 것이다.

### 문단 3 — Map: convergence 가속과 신뢰할 수 있는 지도 구축

신뢰할 수 있는 온라인 Gaussian 지도를 구축하려면, 관측에 부합하는 초기 표현에서 출발하여 제한된 연산 안에 재구성 품질을 높이고 학습 과정에서도 기하적 일관성을 확보해야 한다. EDGS는 영상 간 dense correspondence를 이용해 관측 기하를 반영하는 조밀한 Gaussian 초기화를 구성함으로써, 재구성을 위한 기하적 출발점을 제공하고 빠른 수렴과 높은 재구성 품질을 달성한다.[[4]](https://arxiv.org/abs/2504.13204v2) 초기 표현의 개선과 더불어, 3DGS-LM은 second-order optimization으로 목표 품질에 도달하는 데 필요한 최적화 시간을 줄여 주어진 시간 안에 재구성 품질을 더 빠르게 높인다.[[14]](https://arxiv.org/abs/2409.12892) 온라인 환경의 수렴 부족을 다루는 CaRtGS는 효율적인 역전파와 keyframe별 학습 배분을 결합하여, 제한된 계산 자원이 관측의 충분한 학습으로 이어지도록 한다.[[7]](https://arxiv.org/html/2410.00486v2) 한편 PGSR은 기하적 일관성을 고려한 최적화를 통해 높은 렌더링 품질과 함께 정확한 표면 재구성을 추구하며, 빠른 학습뿐 아니라 학습된 지도 기하의 신뢰성도 중요함을 보여준다.[[10]](https://arxiv.org/html/2406.06521v2) 관측이 계속 도착하는 streaming 환경에서는 이러한 학습 효율과 기하적 신뢰성을 함께 확보해야 하므로, 증가하는 관측의 학습 편입과 update 배분을 결정하는 동시에 지도 기하를 지속적으로 제약하는 방식이 요구된다.

### 문단 4 — Gap ①: 성장하는 학습 영상 집합

그러나 온라인 지도의 빠른 수렴은 최적화 방식뿐 아니라 어떤 관측에 update를 사용하는지에도 달려 있다. Photo-SLAM과 VIGS-SLAM은 frontend가 선택한 keyframe을 지도 학습에 사용하며[[6]](https://openaccess.thecvf.com/content/CVPR2024/papers/Huang_Photo-SLAM_Real-time_Simultaneous_Localization_and_Photorealistic_Mapping_for_Monocular_Stereo_CVPR_2024_paper.pdf)[[13]](https://arxiv.org/html/2512.02293v2), MonoGS와 HI-SLAM2는 keyframe의 local window로 계산량을 제한한다.[[2]](https://openaccess.thecvf.com/content/CVPR2024/papers/Matsuki_Gaussian_Splatting_SLAM_CVPR_2024_paper.pdf)[[5]](https://arxiv.org/html/2411.17982v3) 이러한 방식은 관측을 효율적으로 재사용하지만, 중간 영상의 보완적인 시점과 appearance 정보를 활용하지 못하면 제한된 update에서 재구성 품질을 높일 기회를 놓칠 수 있다. 반대로 영상을 단순히 늘리면 update가 분산되어 관측별 학습이 부족해질 수 있으므로, 추가 관측이 빠른 품질 향상으로 이어지도록 편입 속도를 조절해야 한다. 또한 균등 선택은 편입 시점에 따른 누적 학습 기회의 차이를 보정하지 못해, 늦게 포함된 관측의 학습 지연이 남을 수 있다. CaRtGS는 loss 기반 배분으로 keyframe 재학습 불균형을 완화하지만, keyframe 밖의 관측을 언제 편입할지는 별도로 남는다.[[7]](https://arxiv.org/html/2410.00486v2) 따라서 제한된 update로 높은 지도 품질에 빠르게 도달하려면, 학습 집합의 성장을 실제 완료된 최적화량에 맞추고 집합 내부의 재학습 기회도 함께 조정해야 한다.

### 문단 5 — Map + Gap ②: 초기화 이후에도 남는 기하적 모호성

한편, 영상 관측을 더 효과적으로 학습하여 색 오차를 줄이는 것만으로는 올바른 기하에 도달했는지 판단할 수 없다. 관측 기하에 가깝게 초기화하더라도, 이후 색 기반 최적화에서 잘못된 깊이의 Gaussian이 색을 설명하며 남을 수 있기 때문이다.[[8]](https://arxiv.org/html/2503.18458v1) 2DGS의 depth distortion이나 DS-NeRF의 ray termination 분포 감독처럼, 색 외에 ray상의 기여 위치를 제약하는 접근도 제안되어 왔다.[[9]](https://arxiv.org/abs/2403.17888)[[11]](https://www.cs.cmu.edu/~dsnerf/) 여기서 평균 rendered depth의 일치와 올바른 표면의 형성은 구분되어야 한다. 표면 앞뒤의 기여가 평균에서 상쇄되면 관측 depth와의 오차가 작아도 표면 앞의 빈 공간에 잘못된 opacity가 남을 수 있으며, 평균값만 맞추는 목적함수는 이를 구별하지 못한다. 따라서 appearance와 geometry를 함께 학습하는 온라인 지도에서는, 제한된 update를 색과 평균 깊이의 오차 감소에만 사용하는 것으로 충분하지 않다. 남는 과제는 현재까지 확보한 불확실한 depth evidence를 이용해 관측된 빈 공간의 잘못된 opacity와 표면을 설명하는 기여를 구분하고, 이를 초기화 이후의 최적화에도 반영하는 것이다.

### 문단 6 — Aim: 시스템 기반과 세 가지 접근법

본 연구는 제한된 온라인 mapping update 안에서 Gaussian 지도의 appearance와 geometry를 개선하는 것을 목표로 한다. 이를 위해 VIGS-SLAM의 DROID 기반 visual–inertial frontend가 추정하는 pose와 dense depth를 Gaussian 초기화에 활용하여, 관측 기하에 기반한 출발점을 마련한다.[[12]](https://arxiv.org/abs/2108.10869)[[13]](https://vigs-slam.github.io/) 이 기반 위에서 세 가지 mapping 정책을 적용한다. 첫째, Optimization-Guided View Growth는 실제로 완료된 mapping update에 따라 keyframe 밖의 영상을 학습 집합에 추가한다. 둘째, Entropy-Regularized View Sampling은 누적 선택 횟수가 적은 영상에 높은 선택 확률을 부여하면서 무작위성을 유지하고, 비복원 추출로 짧은 구간의 반복 선택을 줄인다. 셋째, 현재까지 확보한 depth evidence에 기반한 기하 제약으로 ray상의 관측된 빈 공간과 표면을 구분하여 지도 최적화에 반영한다. Gaussian 초기화는 이 정책들이 작동하는 공통 시스템 기반이며, 별도의 새로운 초기화 방법을 기여로 주장하지 않는다.

### 문단 7 — 검증 범위

우리는 RPNG, UTMM, Aria에서 VIGS-SLAM과 held-out 렌더링 품질을 비교하고, 별도의 ablation을 통해 중간 영상의 활용과 영상 선택 정책이 제한된 mapping update에서 얻는 품질에 미치는 영향을 분석한다. 정책 비교에서는 초기화와 pose 등 공통 조건을 통제하여 관측 활용 정책의 효과를 분리하고, 여러 update 예산에서 그 효과가 어떻게 달라지는지 살펴본다. 이를 통해 초기 표현의 차이와 학습 관측의 추가·선택에 따른 차이를 구분하여 평가한다.

> 문단 7의 두 번째 문장은 실험 서술을 확정할 때 각 표의 통제 조건과 대조해야 한다. 전체 VIGS-SLAM 비교까지 동일 초기화·동일 pose라는 의미로 확장하지 않는다. 현재 TeX에 있는 렌더링 비교와 정책 ablation을 넘어, 기하 성능이나 native-rate 처리량을 이미 검증했다고 쓰지는 않았다.

### Contributions

본 연구의 기여는 다음과 같다.

1. **Optimization-Guided View Growth:** 완료된 mapping update에 따라 tracking keyframe 밖의 관측을 추가하여, 온라인 학습 영상 집합의 확장 속도를 결정한다.
2. **Entropy-Regularized View Sampling:** 누적 선택 횟수가 적은 영상에 더 많은 학습 기회를 부여하면서 무작위성을 유지하고, 비복원 추출을 통해 연속적인 update 사이의 반복 선택을 줄인다.
3. **Depth 기반 기하 제약:** 현재까지 관측한 depth evidence를 이용하여 ray상의 관측된 빈 공간과 표면을 구분하고, Gaussian opacity의 배치를 제약한다.

> 세 번째 항목은 현재 TeX에 남아 있는 Carve / Hit / Carve+Hit 중 최종 목적함수를 선택한 뒤 그 실제 작용에 맞춰 구체화한다. 위 문구는 후보들이 공유하는 연구 방향을 표현하며, 목적함수별 성능을 확정한 표현이 아니다.

## 2. 문단별 인용 설계

| 문단 | 인용 | 인용이 맡는 역할 | 우리 논리와의 연결 |
|---|---|---|---|
| 1 | 특정 논문 인용 없음 | 연구의 응용 맥락과 목표 설정 | 관측 도중의 지도 품질을 문제로 정의 |
| 2 | [1], [2], [3] | 효율적인 표현 → 온라인 SLAM → 제한된 학습량 | 렌더링 속도에서 지도 개선 효율로 논의 이동 |
| 3 | [4], [14], [7], [10] | 초기화·optimizer·온라인 학습 배분을 통한 수렴 가속과 기하적 일관성 제약을 통한 신뢰성 확보 | 문단 4의 관측 편입·배분과 문단 5의 지도 기하 제약이라는 두 과제로 연결 |
| 4 | [6], [13], [2], [5], [7] | Frontend keyframe 중심의 학습 후보, local-window 최적화, 기존 재학습 배분을 구분 | Non-keyframe 관측으로 후보 범위를 넓히되 완료된 학습량에 맞춰 편입·재학습을 조정 |
| 5 | [8], [9], [11] | photometric ambiguity와 ray 분포 제약의 선행연구 인정; 평균 depth 일치의 한계 | causal depth로 빈 공간과 표면을 구분하는 접근으로 연결 |
| 6 | [12], [13] | pose/depth 추정 기술과 실제 visual–inertial Gaussian 시스템 기반 | 기존 backbone과 제안 mapping 정책을 구분 |
| 7 | 새로운 외부 인용 없음 | 우리 실험의 범위와 통제 비교를 설명 | Contributions로 연결 |

문단 3은 photometric/geometric convergence로 구분하지 않고, 수렴 가속과 신뢰할 수 있는 지도 구축을 하나의 연구 흐름으로 묶는다. EDGS·3DGS-LM·CaRtGS는 초기 상태와 학습 효율의 개선을, PGSR은 영상 재구성과 함께 표면의 기하적 일관성을 확보하는 접근을 대표한다. 여기서 신뢰성은 uncertainty calibration이나 모든 floater의 제거 보장이 아니라, 재구성된 기하가 실제 표면에 부합한다는 의미다. 문단 4는 keyframe 중심 관측의 범위와 후보 집합 확장·학습 배분의 결합 문제, 문단 5는 색·평균 depth의 일치로 식별되지 않는 opacity 배치 문제에 집중한다. 두 gap은 모든 선행연구가 해당 문제를 무시했다는 주장이 아니다. 특히 [7]의 학습 배분과 [10]의 기하적 일관성 제약, [9], [11]의 분포 제약을 인정한 뒤, 우리 온라인 조건에서 다룰 설계 문제를 좁혀 제시한다. 기존 검토 번호를 유지하기 위해 현재 본문에서 제외한 [15]의 메모도 아래에 남겼다.

## 3. 인용 논문별 문제의식·기여·사용 범위

### [1] 3D Gaussian Splatting for Real-Time Radiance Field Rendering

- **논문:** Kerbl et al., 2023. [저자 프로젝트·논문](https://repo-sam.inria.fr/fungraph/3d-gaussian-splatting/)
- **집중한 문제:** 고품질 novel-view synthesis와 빠른 렌더링을 함께 달성하는 장면 표현 및 최적화.
- **주요 기여:** 명시적인 anisotropic 3D Gaussian 표현, 최적화와 교차 수행하는 density control, visibility-aware splatting 기반의 효율적인 렌더링을 결합한다.
- **초안에서의 역할:** 문단 2에서 표현의 출발점을 제시한다.
- **우리 연구와의 연결:** 동일한 표현이 온라인에서도 유용하지만, 스트림이 도착하는 동안 학습을 완료하는 문제는 별도로 다뤄야 한다.
- **주장 범위:** 원 논문의 실시간 렌더링을 실시간 SLAM 또는 zero-tail mapping의 증거로 사용하지 않는다.
- **확인 위치 / BibTeX key:** 프로젝트 Abstract와 논문 Method / `kerbl20233dgs`.

### [2] Gaussian Splatting SLAM — MonoGS

- **논문:** Matsuki et al., CVPR 2024. [공식 게재 페이지](https://openaccess.thecvf.com/content/CVPR2024/html/Matsuki_Gaussian_Splatting_SLAM_CVPR_2024_paper.html)
- **집중한 문제:** 이동 카메라로부터 Gaussian map을 점진적으로 만들면서 카메라 pose를 추정하는 온라인 dense SLAM.
- **주요 기여:** Gaussian 표현을 tracking과 mapping에 사용하고, 미분 가능한 pose 최적화 및 incremental reconstruction의 모호성에 대응하는 geometric verification·regularization을 도입한다.
- **초안에서의 역할:** 문단 2에서 3DGS의 온라인 SLAM 확장을 대표한다.
- **우리 연구와의 연결:** 학습 가능한 Gaussian map을 온라인으로 유지하는 시스템적 선례다.
- **주장 범위:** 온라인 실행과 센서 입력 속도를 완전히 따라가는 실행은 같은 뜻이 아니다. 이 논문을 모든 GS-SLAM이 native-rate로 동작한다는 근거로 묶지 않는다.
- **확인 위치 / BibTeX key:** Abstract와 tracking/mapping 방법 / `matsuki2024monogs`.

### [3] SplaTAM: Splat, Track & Map 3D Gaussians for Dense RGB-D SLAM

- **논문:** Keetha et al., CVPR 2024. [원문](https://openaccess.thecvf.com/content/CVPR2024/papers/Keetha_SplaTAM_Splat_Track__Map_3D_Gaussians_for_Dense_RGB-D_CVPR_2024_paper.pdf)
- **집중한 문제:** Unposed RGB-D 관측으로 tracking, map 확장, 고품질 dense reconstruction을 수행하는 것.
- **주요 기여:** Gaussian 표현과 silhouette mask로 이미 설명된 영역을 구분하고, 관측 depth와 map coverage를 이용해 Gaussian을 추가한다. Mapping은 현재 frame·최근 keyframe·overlap이 높은 과거 keyframe을 사용한다.
- **초안에서의 역할:** 문단 2의 온라인 Gaussian mapping 사례.
- **우리 연구와의 연결:** 어떤 관측을 mapping에 사용하는지와 새 geometry를 어디에 생성하는지가 시스템 설계의 일부임을 보여준다.
- **주장 범위:** RGB-D 시스템이다. 또한 현재 frame도 사용하므로, “기존 시스템은 모두 keyframe만 학습한다”는 주장의 근거가 될 수 없다.
- **확인 위치 / BibTeX key:** Gaussian Densification, Gaussian Map Updating / `splatam2024`.

### [4] EDGS: Eliminating Densification for Efficient Convergence of 3DGS

- **논문:** Kotovenko et al., CVPR 2026. [arXiv:2504.13204v2](https://arxiv.org/abs/2504.13204v2), [확인한 게재판 PDF](https://openaccess.thecvf.com/content/CVPR2026/papers/Kotovenko_EDGS_Eliminating_Densification_for_Efficient_Convergence_of_3DGS_CVPR_2026_paper.pdf)
- **집중한 문제:** Sparse initialization에서 시작해 split·densification을 반복하면 필요한 구조가 갖춰지고 학습되기까지 긴 최적화 경로가 발생한다는 문제.
- **주요 기여:** Dense image correspondence를 삼각측량하여 Gaussian의 위치·색·크기를 초기화한다. 모든 primitive가 처음부터 관측 신호를 받도록 하여 반복적인 densification의 필요성을 줄이고 빠른 수렴을 보인다.
- **초안에서의 역할:** 문단 3에서 densification의 세부 과정보다, 영상 간 correspondence에 근거한 dense initialization이 기하적 출발점을 제공하고 수렴 속도와 재구성 품질을 개선한다는 점에 집중한다. 이를 독립적인 기하 정확도 보장으로 확대하지 않는다.
- **우리 연구와의 연결:** 충분한 관측 기하로 출발하는 것이 제한된 update의 활용에 중요하다는 동기. 여기서 우리 온라인 시스템으로의 연결은 저자의 실험 결과 자체가 아니라 본 초안의 문제 설정이다.
- **주장 범위:** 전체 입력 영상의 correspondence를 이용한 재구성이다. 미래 관측을 사용할 수 없는 strict online 초기화의 성능 근거로 사용하지 않는다. Dense initialization과 dense RGB supervision도 구분한다.
- **확인 위치 / BibTeX key:** 게재판 Figure 1의 시간–LPIPS 비교, Figure 4의 Gaussian 위치·색 변화 분석 / `edgs`. 위치 이동량 감소를 GT 표면 오차의 감소와 동일시하지 않는다. 현재 `.bib`의 서지정보는 불완전하므로 게재판 기준으로 보완할 것.

### [5] HI-SLAM2: Geometry-Aware Gaussian SLAM for Fast Monocular Scene Reconstruction

- **논문:** Zhang et al. [원문](https://arxiv.org/html/2411.17982v3), [저자 페이지: T-RO 2025](https://hi-slam2.github.io/)
- **집중한 문제:** Monocular RGB에서 appearance와 geometry의 품질, 그리고 전역 일관성을 함께 확보하는 dense SLAM.
- **주요 기여:** Learning-based dense SLAM과 monocular geometric priors를 결합하고, prior depth의 공간별 scale alignment와 loop closure 후 Gaussian map 갱신을 사용한다. 새 keyframe의 추정 depth를 역투영하여 Gaussian을 추가하고 색·깊이·normal·scale 관련 손실로 개선한다.
- **초안에서의 역할:** 문단 4에서 online local-window keyframe 학습의 사례로 사용한다. 초기화 가속의 직접 증거가 아니라 관측 선택 규칙을 뒷받침한다. §III-E의 offline post-keyframe insertion은 선택된 관측 외의 추가 coverage 필요성을 보여주는 보완 근거다.
- **우리 연구와의 연결:** 새 영역의 초기화는 최초 시점에만 일어나는 작업이 아니라 keyframe이 추가될 때 반복되는 과정이다.
- **주장 범위:** 이 논문의 모든 품질 향상을 초기화 하나의 효과로 귀속하지 않는다. Offline refinement도 포함하므로 수치 인용 시 online/offline 조건을 구분해야 한다.
- **확인 위치 / BibTeX key:** §III-D, Map Management 및 Optimization Losses / 현재 `main.bib`에 대응 key 없음. 제안 key: `zhang2025hislam2`.

### [6] Photo-SLAM: Real-time Simultaneous Localization and Photorealistic Mapping for Monocular, Stereo, and RGB-D Cameras

- **논문:** Huang et al., CVPR 2024. [원문](https://openaccess.thecvf.com/content/CVPR2024/papers/Huang_Photo-SLAM_Real-time_Simultaneous_Localization_and_Photorealistic_Mapping_for_Monocular_Stereo_CVPR_2024_paper.pdf)
- **집중한 문제:** 제한된 연산 자원에서 정확한 localization과 온라인 photorealistic mapping을 함께 수행하는 것.
- **주요 기여:** Geometry와 appearance 정보를 가진 hyper-primitives map, geometry-based densification, Gaussian-pyramid 기반 학습을 결합한다. Dense depth에 의존하지 않고 appearance를 점진적으로 학습하는 방향을 제시한다.
- **초안에서의 역할:** 문단 4에서 frontend keyframe을 photorealistic mapping의 관측으로 사용하는 사례다. 현재 공식 코드의 후보 집합은 scene에 저장된 keyframe들이므로 전체 pool이 고정 크기라고 쓰지 않는다. Table 4의 품질 ablation을 동일 품질까지 필요한 iteration 감소의 직접 증거로 해석하지 않는다.
- **우리 연구와의 연결:** 온라인 최적화의 방식뿐 아니라 사용 가능한 RGB 관측을 학습 집합에 포함하는 방식도 검토한다.
- **주장 범위:** DROID 기반 dense-depth initialization 논문으로 소개하지 않는다. 초기화 논문 다음에 배치하는 것은 논리적 연결이며 연구의 시간적 계보를 뜻하지 않는다.
- **확인 위치 / BibTeX key:** Introduction, geometry-based densification 및 Gaussian-pyramid 학습 설명 / `huang2024photoslam`.

### [7] CaRtGS: Computational Alignment for Real-Time Gaussian Splatting SLAM

- **논문:** Feng et al. [확인한 원문: arXiv:2410.00486v2](https://arxiv.org/html/2410.00486v2)
- **집중한 문제:** Online GS-SLAM의 부족한 전체 학습량, keyframe별 long-tail optimization, 약하게 제약된 densification.
- **주요 기여:** Splat-wise 역전파로 계산 효율을 높이고, keyframe별 rendering loss를 이용해 최적화 기회를 배분하며, opacity regularization을 추가한다. 오래된 keyframe이 최근 keyframe보다 더 많이 재학습되는 현상을 명시적으로 다룬다.
- **초안에서의 역할:** 문단 3의 온라인 연산·학습 배분 선행연구이자 문단 4에서 가장 직접적으로 비교해야 하는 연구. 역전파 가속으로 같은 시간에 더 많은 update를 수행하는 효과와, 같은 update 수에서 더 효율적으로 학습하는 효과는 구분한다.
- **우리 연구와의 연결:** Keyframe pool 안의 loss 기반 배분에서 더 나아가, keyframe 사이 관측까지 포함하는 집합의 성장과 count 기반 선택을 함께 다루는 질문으로 연결한다.
- **주장 범위:** “학습 불균형을 처음 발견했다”, “기존 연구는 update 배분을 다루지 않는다”라고 쓰지 않는다. 우리 방법이 loss 기반 배분보다 우수하다는 주장은 직접 비교가 있을 때만 가능하다.
- **확인 위치 / BibTeX key:** §III-A1–A3, §III-B1–B3 / `cartgs`.

### [8] StableGS: A Floater-Free Framework for 3D Gaussian Splatting

- **논문:** [확인한 원문: arXiv:2503.18458v1, 2025](https://arxiv.org/html/2503.18458v1)
- **집중한 문제:** Color와 opacity의 결합으로 인해 잘못된 Gaussian이 남고, 특히 약한 texture나 반투명 영역에서 geometry 제약과 appearance가 충돌하는 문제.
- **주요 기여:** Floater와 parameter coupling을 분석하고, depth consistency와 geometry/material을 분리하는 dual-opacity 모델을 제시한다. DUSt3R 기반 기하 prior도 활용한다.
- **초안에서의 역할:** 문단 5에서 photometric agreement만으로 올바른 geometry가 확보되지 않는다는 구체적인 근거.
- **우리 연구와의 연결:** 초기화 이후에도 opacity 배치에 대한 별도 제약이 필요하다는 동기.
- **주장 범위:** 논문 제목의 “floater-free”를 모든 장면에 대한 보편적 보장으로 옮기지 않는다. 이 연구의 coupling 분석과 우리의 새 ray loss가 동일한 방법이라는 뜻도 아니다.
- **확인 위치 / BibTeX key:** Introduction 및 floater 분석·depth consistency·dual-opacity 설명 / `stablegs`. 저자명 등 최종 서지정보는 제출 시 사용 버전에서 확인할 것.

### [9] 2D Gaussian Splatting for Geometrically Accurate Radiance Fields

- **논문:** Huang et al., 2024. [논문 페이지](https://arxiv.org/abs/2403.17888), [원문](https://www.cvlibs.net/publications/Huang2024SIGGRAPH.pdf)
- **집중한 문제:** 고품질 view synthesis를 제공하는 Gaussian 표현에서 정확하고 일관된 표면 기하를 재구성하는 것.
- **주요 기여:** Surface-oriented 2D Gaussian primitive와 perspective-correct rendering을 사용하며, depth distortion과 normal consistency로 기하를 정규화한다.
- **초안에서의 역할:** 문단 5의 geometry-aware reconstruction 선행연구.
- **우리 연구와의 연결:** 색 외에 ray상의 기여 위치와 표면 방향을 다루는 제약의 필요성.
- **주장 범위:** 2DGS는 depth distortion을 사용하므로 “기존 연구는 모두 평균 depth만 맞춘다”는 비판의 대상으로 묶지 않는다. Online SLAM에서의 제한된 update 실증과도 구분한다.
- **확인 위치 / BibTeX key:** Method의 depth distortion 및 normal consistency / `huang20242dgs`.

### [10] PGSR: Planar-based Gaussian Splatting for Efficient and High-Fidelity Surface Reconstruction

- **논문:** Chen et al., 2024. [논문 페이지](https://arxiv.org/abs/2406.06521)
- **집중한 문제:** Gaussian splatting의 효율성을 활용하면서 정밀한 표면 재구성을 확보하는 것.
- **주요 기여:** Gaussian을 평면 형태로 만들고, 렌더링한 camera-to-plane distance와 normal로부터 깊이를 계산하는 unbiased depth rendering을 제안한다. 단일 시점의 depth–normal 일관성과 다중 시점의 기하·photometric 제약을 결합하여 표면 재구성을 개선한다.
- **초안에서의 역할:** 문단 3에서 빠른 수렴뿐 아니라 올바른 표면에 부합하는 재구성이 중요하다는 reliable map 관점을 담당한다. 별도의 geometric convergence 범주나 긴 방법 소개로 나누지 않는다.
- **우리 연구와의 연결:** 색을 설명하는 것만으로는 정확한 표면이 결정되지 않으므로 최적화에 기하 정보를 반영해야 한다는 문제의식을 공유한다. PGSR은 평면 기반 깊이 렌더링과 시점 간 일관성을, 우리는 현재까지 확보한 depth evidence에 따른 ray상의 빈 공간·표면 제약을 다룬다. 동일한 목적함수나 직접적인 방법 계승 관계로 서술하지 않는다.
- **주장 범위:** 주어진 pose의 다중 영상에서 표면을 복원하는 연구로, strict online mapping의 실증 근거는 아니다. PGSR이 평균 depth만 맞춘다거나 모든 floater를 제거한다고 쓰지 않는다. 우리와 연결하는 근거는 기하적 제약의 필요성이며, PGSR의 ray별 opacity 분포 식별 한계를 이 문단에서 입증한 것은 아니다.
- **확인 위치 / BibTeX key:** [원문 v2](https://arxiv.org/html/2406.06521v2)의 Introduction, Figure 2, §IV-A 및 §IV-B / `chen2024pgsr`.

### [11] Depth-Supervised NeRF: Fewer Views and Faster Training for Free — DS-NeRF

- **논문:** Deng et al., CVPR 2022. [저자 프로젝트·논문](https://www.cs.cmu.edu/~dsnerf/)
- **집중한 문제:** 적은 입력 시점에서 radiance field를 학습할 때 나타나는 기하적 모호성과 느린 학습.
- **주요 기여:** SfM이 제공하는 sparse 3D point를 depth supervision으로 이용하고, depth uncertainty를 고려하여 ray termination depth의 분포를 제약한다.
- **초안에서의 역할:** 문단 5에서 평균값을 넘어 ray상의 분포를 감독하는 접근의 선행연구.
- **우리 연구와의 연결:** 현재 방법의 ray termination·Hit 관점을 논의할 때 반드시 인정해야 하는 가까운 개념적 기반이다.
- **주장 범위:** Depth supervision을 Gaussian 초기화와 혼동하지 않는다. “Ray termination distribution supervision을 처음 제안한다”는 주장은 피하고, causal online GS 조건과 실제 목적함수의 차이를 설명한다.
- **확인 위치 / BibTeX key:** 프로젝트의 depth supervision 설명과 Ray Termination Distribution Visualization / `deng2022dsnerf`.

### [12] DROID-SLAM: Deep Visual SLAM for Monocular, Stereo, and RGB-D Cameras

- **논문:** Teed and Deng, NeurIPS 2021. [논문 페이지](https://arxiv.org/abs/2108.10869)
- **집중한 문제:** Monocular·stereo·RGB-D 입력에서 강건한 camera motion 및 dense geometry 추정.
- **주요 기여:** Recurrent update와 differentiable dense bundle adjustment로 camera pose와 pixelwise depth를 반복적으로 추정한다.
- **초안에서의 역할:** 문단 6의 pose/depth 추정 기술 기반.
- **우리 연구와의 연결:** Gaussian을 생성하고 감독하는 데 사용할 기하 추정의 계보를 설명한다.
- **주장 범위:** 원 DROID-SLAM 자체를 IMU를 사용하는 Gaussian mapping 시스템으로 소개하지 않는다. Visual–inertial 통합과 Gaussian backend의 직접 출처는 [13]이다.
- **확인 위치 / BibTeX key:** Abstract 및 dense bundle adjustment 설명 / `teed2021droid`.

### [13] VIGS-SLAM: Visual Inertial Gaussian Splatting SLAM

- **논문:** Zhu et al., 2025. [논문](https://arxiv.org/abs/2512.02293), [저자 프로젝트](https://vigs-slam.github.io/)
- **집중한 문제:** Motion blur·낮은 texture·노출 변화 등에서 visual-only 추정이 약해지는 문제와, 강건한 추정에 기반한 photorealistic mapping.
- **주요 기여:** Visual–inertial 추정에서 pose·depth·IMU state를 결합하고, IMU 초기화·bias modeling·loop closure와 일관된 Gaussian 갱신을 다룬다. 추정한 keyframe depth와 pose로 Gaussian을 생성한다.
- **초안에서의 역할:** 문단 4에서 keyframe 중심의 학습 관측 선택을, 문단 6에서 우리의 실제 시스템 기반을 명시한다. §3.3의 local/global keyframe 선택과 새 keyframe당 10 iteration은 전체 학습 pool의 고정 크기를 뜻하지 않는다.
- **우리 연구와의 연결:** Frontend의 추정 기하를 사용하는 기존 기반 위에 view growth, sampling, 기하 제약을 적용한다.
- **주장 범위:** 기존 시스템이 제공한 초기화나 IMU 추정을 우리의 새 기여처럼 쓰지 않는다. 기존 논문의 성능 수치와 우리의 평가 결과는 각 평가 계약에 맞춰 별도로 설명한다.
- **확인 위치 / BibTeX key:** 논문 시스템 구성·IMU 초기화, 프로젝트 Gaussian mapping 설명 / `vigsslam`.

### [14] 3DGS-LM: Faster Gaussian-Splatting Optimization with Levenberg-Marquardt

- **논문:** Höllein et al., ICCV 2025. [논문 페이지](https://arxiv.org/abs/2409.12892), [확인한 게재판 PDF](https://openaccess.thecvf.com/content/ICCV2025/papers/Hollein_3DGS-LM_Faster_Gaussian-Splatting_Optimization_with_Levenberg-Marquardt_ICCV_2025_paper.pdf)
- **집중한 문제:** Adam 기반 3DGS 학습에서 영상 재구성 품질을 확보하기까지 걸리는 긴 최적화 시간.
- **주요 기여:** 초기 Adam 학습·densification 이후 Levenberg–Marquardt와 GPU 기반 선형계 풀이로 second-order update를 수행한다.
- **초안에서의 역할:** 문단 3에서 optimizer 개선으로 목표 품질까지의 최적화 시간을 줄이는 접근을 대표한다. 개별 update의 실행 시간이 더 짧아진다거나 같은 시간에 더 많은 update를 수행한다는 설명으로 바꾸지 않는다.
- **우리 연구와의 연결:** Parameter update 자체를 개선하는 흐름을 인정하면서, 우리는 성장하는 관측 집합의 활용을 다룬다는 점을 구분한다.
- **주장 범위:** 주 실험은 20K Adam iteration 이후 5 LM iteration을 수행한다. 처음부터 5회 만에 수렴한다고 쓰거나, 여러 영상을 사용하는 LM iteration과 우리의 단일-view mapping update를 같은 비용으로 비교하지 않는다. 기하 수렴의 증거로도 사용하지 않는다.
- **확인 위치 / BibTeX key:** §4 Implementation Details, Table 1, Figure 4 / 현재 대응 key 없음. 제안 key: `hollein2025gs_lm`.

### [15] GeoGS-SLAM: Geometry-Only Gaussian Splatting for Dense Monocular SLAM

- **논문:** Zhou et al., 2026년 7월 preprint. [확인한 원문: arXiv:2607.07452v1](https://arxiv.org/html/2607.07452v1)
- **집중한 문제:** 제한된 온라인 최적화에서 정확한 표면 기하를 빠르게 확보하는 것.
- **주요 기여:** Appearance 파라미터를 제외한 기하 중심 Gaussian 표현, single-/multi-view 감독, local-plane 기반 초기화와 전역 pose 보정 후의 일관된 map 갱신을 제안한다.
- **초안에서의 역할:** 현재 본문에서는 제외하고, geometric convergence를 직접 다루는 보완 문헌으로 보관한다. 문단 3의 신뢰할 수 있는 표면 재구성 사례로는 appearance 표현도 유지하는 [10]을 사용한다.
- **우리 연구와의 연결:** 제한된 update에서 기하 수렴이 별도의 설계 대상임을 보여준다. 우리는 appearance 표현을 유지하면서 이용 가능한 depth evidence로 기하를 제약하는 조건을 다룬다.
- **주장 범위:** Geometry-only는 RGB 정보를 사용하지 않는다는 뜻이 아니다. View 간 photometric consistency를 기하 감독에 사용하되, Gaussian의 색 표현을 학습하지 않는다. 이 논문의 시간–기하 오차 실험을 우리의 joint appearance/geometry 시스템과 동일한 조건으로 취급하지 않는다.
- **확인 위치 / BibTeX key:** §IV-D, Figure 12의 시간–Chamfer Distance 곡선, Figure 15의 mapping iteration별 초기화 ablation / 현재 대응 key 없음. 제안 key: `zhou2026geogsslam`.

## 4. 본문에 모두 넣지 않아도 되는 보완 문헌

### QuickSplat: Fast 3D Surface Reconstruction via Learned Gaussian Initialization

[논문](https://arxiv.org/abs/2505.05591), ICCV 2025.

학습된 2DGS 초기화·densification·parameter update로 실내 표면 복원을 가속한다. Figure 1의 시간–depth error 곡선은 geometric convergence의 직접적인 근거지만, 오프라인 재구성이며 학습된 prior를 사용한다. 문단 3을 짧게 유지하기 위해 이 논문과 [15]는 보완 문헌으로 남긴다. 전체 가속 효과를 초기화만의 효과로 귀속하지 않는다.

### Matrix-free Second-order Optimization of Gaussian Splats with Residual Sampling — LM-RS

[논문](https://arxiv.org/abs/2504.12905v3), [저자 프로젝트](https://vcai.mpi-inf.mpg.de/projects/LM-RS/), 3DV 2026.

Matrix-free second-order optimization에 view·residual sampling을 결합한다. §4.3과 Table 2는 camera 위치·방향 clustering을 이용한 다양한 batch 구성을 다룬다. 주어진 camera set에서의 batch 구성은 우리의 causal view growth·누적 선택 횟수 기반 배분과 구별한다. 문단 3에서는 optimizer 사례를 [14] 하나로 제한하고, sampling 관련 상세 비교는 Related Work에 남긴다. 기존 BibTeX key `lmrs`의 제목은 실제 제목인 “Residual Sampling”으로 확인·보완해야 한다.

### RTG-SLAM: Real-time 3D Reconstruction at Scale Using Gaussian Splatting

[저자 프로젝트](https://gapszju.github.io/RTG-SLAM/), [논문](https://arxiv.org/abs/2404.19706)

RGB-D 기반의 대규모 온라인 재구성을 위해 compact Gaussian 표현을 사용하고, stable/unstable Gaussian을 구분해 unstable Gaussian과 관련 pixel에 계산을 집중한다. 현재 문단 3의 계산 효율 사례는 EDGS·3DGS-LM·CaRtGS로 충분하므로 RTG-SLAM은 추가하지 않는다. 지도 기하의 신뢰성은 PGSR로 연결한다. BibTeX key: `rtgslam2024`.

### Geometry-Aware Online Mapping for 3D Gaussian Splatting SLAM

[확인한 원문: arXiv:2608.14902v1, 2026 preprint](https://arxiv.org/html/2608.14902v1)

제한된 online 최적화에서 초기 scale과 density-control heuristic의 영향을 다룬다. Photo-SLAM 기반 RGB-D 설정에서 camera-aware scale initialization, error-guided densification, transmittance-preserving densification을 제안한다. 초기화·primitive 생성과 observation allocation의 관계를 설명할 때 가까운 문헌이다. 다만 sensor depth를 사용하는 설정을 우리의 추정 depth 기반 조건과 구분해야 한다. Introduction의 중심 인용을 늘리기보다 Related Work에서 비교하는 용도로 남긴다. BibTeX key: `geometryOnline2026`.

## 5. 영어 TeX로 옮길 때 유지할 구분

1. **초기화의 단위:** 최초 map뿐 아니라 새 영역·새 Gaussian의 초기화도 포함한다. Online 시스템을 “좋은 초기 지도를 한 번 만든 뒤 학습하는 구조”로만 설명하지 않는다.
2. **두 종류의 dense:** Dense initialization은 primitive의 초기 배치, dense RGB supervision은 학습에 사용하는 관측의 범위다.
3. **기존 기여 인정:** CaRtGS는 keyframe 학습 불균형, DS-NeRF는 termination distribution supervision을 이미 다룬다. 우리의 정확한 설정과 설계를 차별점으로 쓴다.
4. **추정치와 정답 구분:** Frontend depth는 관측으로 추정한 evidence다. “정확한 geometry 확보”나 “초기화로 기하 문제가 해결됨”이라고 단정하지 않는다.
5. **관측 선택의 범위:** SplaTAM은 현재 frame도, RTG-SLAM은 최근 일반 RGB-D frame도 사용한다. “모든 기존 방법은 keyframe-only”라고 쓰지 않는다. 또한 local window의 제한과 전체 후보 pool의 고정 크기를 구분한다. 조사 근거는 [문단 4 관측 선택 검토](02_paragraph4_view_pool_evidence_2026-09-19.md)에 정리했다.
6. **연구 결과와 동기 구분:** EDGS가 보여준 초기화 효과, 기존 시스템에서의 depth 역투영, 우리의 view policy 효과는 각각 다른 근거다. 하나의 실험처럼 연결하지 않는다.
7. **실험 문장 확인:** 문단 7의 동일 초기화·pose는 실제로 통제한 ablation에 한정한다. 같은 update 수를 같은 실행 시간으로 바꾸어 표현하지 않는다.
8. **기하 목적함수 확정:** 현재는 후보가 공유하는 목적을 기술했다. 최종 Carve/Hit 선택과 평가가 정해지면 문단 5–6과 contribution 3을 함께 맞춘다.
9. **기하 gap의 범위:** 평균 depth loss의 식별 한계를 모든 geometry-aware 방법의 한계로 확대하지 않는다. 2DGS와 DS-NeRF는 이미 분포를 제약한다. 우리의 차이는 causal online 조건과 실제 목적함수·계산 비용·검증 결과로 구체화해야 하며, “최초의 ray 분포 제약”이나 “더 빠른 기하 수렴”은 현재 초안의 기여 주장이 아니다.

## 6. 다음 편집에서 결정할 항목

- 문단 3은 수렴 가속과 신뢰할 수 있는 지도 구축으로 framing을 확장했다. EDGS → 3DGS-LM → CaRtGS의 효율화 접근에 PGSR의 기하적 일관성 제약을 연결한다. Photometric/geometric convergence로 범주를 나누지 않으며, 문단 끝은 관측의 학습 편입·배분과 지도 기하 제약이라는 두 과제로 이어진다.
- 문단 4는 keyframe 중심의 학습 후보를 중간 영상으로 넓히는 문제에서 출발하여, 추가 관측과 재학습 기회의 상충 및 편입 시점별 누적 학습 불균형으로 이어진다. “전체 pool이 고정되어 확장 불가”라는 주장은 사용하지 않는다. 문단 5의 핵심은 색·평균 depth가 맞아도 남을 수 있는 잘못된 opacity 배치다. 방법명과 구체적인 해법은 문단 6에 둔다.
- 문단 6 마지막의 “초기화는 공통 기반” 문장은 설명용으로 남겼다. 영어 본문에서는 앞 문장의 attribution만으로 충분하면 생략한다.
- 실험 결과가 확정되면 문단 7에 핵심 정량 결과 한 문장을 넣되, 평가 조건이 다른 수치를 섞지 않는다.
- TeX에 반영할 때 3DGS-LM BibTeX를 추가하고 EDGS 등 불완전한 서지정보를 최종 인용 버전에 맞춰 보완한다. GeoGS-SLAM은 다른 절에 실제로 인용할 경우에만 추가한다. 이 문서 작성에서는 `.bib`를 수정하지 않았다.
