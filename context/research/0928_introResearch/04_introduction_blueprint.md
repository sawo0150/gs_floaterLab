# Introduction의 독자·문단·주장 설계

## 1. 가장 추천하는 출발점

**“카메라는 이미 지나갔는데, 지도는 그 관측을 아직 충분히 배우지 못했다.”**

이것은 실측 결과의 진술이 아니라 연구를 설명하는 문제 장면이다. 관측의 도착과 학습의 완료 사이에 간극이 있다는 데서 시작하면, dense input과 역사 보존, 계산 제한이 자연스럽게 연결된다. 최종 논문에는 그 간극을 보여주는 prefix/region plot이 있어야 한다.

반면 “3DGS가 photorealistic NVS에서 성공했다 → offline optimization이 느리다 → 우리는 빠르게 수렴한다”로 시작하면, optimizer/kernel 가속 논문으로 읽히기 쉽다. 또한 real-time을 하드웨어에 따라 달라지는 애매한 개념이라 낮춰 말할 필요가 없다. **처리율과 시간별 지도 품질을 함께 평가해야 한다**고 쓰면 된다.

## 2. 문단별 역할

| 문단 | 독자가 가져갈 내용 | 근거/그림 | 피할 전개 |
|---|---|---|---|
| P1 | 지도는 이미지와 공간을 질의할 수 있는 로봇의 표현; 관측 중 품질 중요 | Splat-Nav/SplatSim, 실제 autonomy 사례 | Gaussian parameter 나열, VLA 유행만 길게 설명 |
| P2 | tracking KF와 map supervision은 목적이 다름 | HI-SLAM2 Fig.5, Online NVS | 기존 방법이 모두 KF-only라는 일반화 |
| P3 | 더 많은 관측을 유지하면 새 영역과 과거 영역이 학습 예산을 경쟁 | iMAP/MonoGS/CaRtGS | global replay가 없었다는 허수아비 대비 |
| P4 | 기존 selection/replay 연구 위에서 우리가 검증할 구체적 질문 | Online NVS/EliGSiR 인정 | “nobody addresses compute” 같은 넓은 gap |
| P5 | 완료 work에 따른 admission과 역할별 replay라는 우리의 설계 | 최신 구현 계약 | DROID-SLAM 이름부터 시작, 미검증 우월성 |
| P6 | controlled evidence와 scope | fixed-work 결과, 향후 시간·geometry 검증 | 현재 없는 live/geometry 성과를 과거형으로 작성 |

Geometry는 P1에서 map usefulness의 조건으로 제시하고, P5/6에서 평가 조건으로 돌아오게 한다. Carve가 검증되기 전에는 “두 목표를 모두 해결했다”는 contribution으로 닫지 않는다. 이후 통합 검증이 나오면 P5에 observation-supported free-space regularization을 넣고 P6에 해당 지표를 제시한다.

## 3. 영문 작업 초안

아래는 현재 증거에 맞춘 **논리 초안**이다. 결과가 모두 나온 완성 논문의 abstract/Introduction으로 그대로 제출하는 문장이 아니다. 특히 P4는 남아 있는 보편적 공백을 선언하는 대신 우리가 검증할 질문을 좁힌다. [편집용 LaTeX](intro_working_draft.tex)의 citation key는 [references.bib](references.bib)와 일치한다.

> A robot's map can support more than pose estimation: it can provide visual observations for learned policies and spatial information for navigation. Gaussian representations make these uses possible within a renderable scene model, motivating their adoption in robotic mapping. For a robot acquiring new observations, however, the relevant object is the map available during acquisition, not only the reconstruction obtained after processing ends. Its usefulness depends on both visual fidelity and reliable geometry, which must be developed while the mapper continues to receive new data.

이 문단의 근거는 [Splat-Nav](https://arxiv.org/abs/2403.02751), [SplatSim](https://arxiv.org/abs/2409.10161), [실제 GS autonomy](https://arxiv.org/abs/2505.11794)다. “정책 성공률을 높였다”는 우리 성과는 쓰지 않는다.

> A central decision is which observations supervise this evolving map. Keyframes provide an economical basis for tracking and reconstruction, but the views selected for pose estimation need not exhaust the useful evidence in the image stream. Coverage deficiencies can remain between selected views, even when additional images of those regions have already been captured. Prior systems address this issue through post-acquisition keyframe insertion or by selecting non-keyframes for additional training. These findings motivate treating mapping supervision as a separate decision rather than restricting it to the tracking keyframes.

직접 근거는 [HI-SLAM2](https://arxiv.org/abs/2411.17982)와 [Online NVS](https://arxiv.org/abs/2508.14014)다. 모든 intermediate view가 유용하다는 주장이 아니다.

> Expanding supervision introduces a second problem. Previously observed views can constrain regions that would otherwise receive little attention as the camera moves on, making historical replay valuable. Yet a growing replay pool also distributes finite updates across an increasing number of views. Earlier observations accumulate more opportunities for optimization, while newly admitted views may receive only limited training before acquisition ends. Thus, access to more observations does not by itself ensure that their information is incorporated into the map.

과거 replay는 [iMAP](https://arxiv.org/abs/2103.12352)과 [MonoGS](https://arxiv.org/abs/2312.06741), 도착 시점에 따른 opportunity 문제는 [CaRtGS](https://arxiv.org/abs/2410.00486)가 뒷받침한다. “finite updates라서 모든 뷰를 못 배운다”는 무조건적 결론은 내리지 않는다.

> Existing work has already developed uncertainty-based view selection, adaptive keyframe optimization, and map-guided replay under limited compute. We build on this line of work to study a specific question: how should an RGB–inertial mapper admit additional past observations and distribute repeated supervision when optimization must stop with the stream? We distinguish the set of observations retained for possible use from the small set selected for each update. This distinction allows historical coverage to remain available without requiring every view to be optimized at every step.

[Online NVS](https://arxiv.org/abs/2508.14014), [CaRtGS](https://arxiv.org/abs/2410.00486), [EliGSiR](https://arxiv.org/abs/2609.20348)를 여기서 인정한다. 추가 관측·budget-aware scheduling·history retention의 최초성은 주장하지 않는다.

> Our design admits non-keyframe RGB observations according to completed mapping work and allocates updates among recent keyframes, historical keyframes, and admitted non-keyframes. The tracking keyframes continue to provide geometric supervision, while additional RGB observations broaden the supervision available for appearance fitting. Within the historical pools, a count-based sampling policy adjusts training opportunities using completed view usage. We evaluate these choices with causal inputs, held-out views excluded from training, and no optimizer updates after the final input. Controlled comparisons separate the effects of additional observations from changes in the loss and update schedule; rendering quality, geometry, and elapsed time must be assessed separately.

마지막 문장의 geometry/time은 **평가 원칙**이며 완료한 결과라고 쓰지 않았다. submission용에는 마지막 두 문장을 실제 완료된 evidence만으로 다시 써야 한다. 현재 frozen-tracker fixed-work 실험을 concurrent RGB–inertial SLAM 검증처럼 읽히지 않게 experimental scope를 명시한다.

## 4. 결과를 넣을 때의 안전한 문장

현재 결과를 요약하는 작업용 문장:

> With a fixed rendering budget and frozen causal tracking outputs, additional non-keyframe supervision improves held-out PSNR over a keyframe RGB-only control on three development scenes. This comparison establishes a benefit under matched rendering work, while its additional preparation cost motivates controlling the rate of view admission.

“고정 초기화에서 same compute로 압도적 성능을 보였다” 대신 어떤 compute를 맞췄는지 쓴다. wall-clock 비교가 완료되지 않았으면 same computational budget이라는 넓은 표현보다 fixed rendering budget이라고 명시한다.

최종 contribution 후보는 다음과 같다. 이는 계획 목록이며 세 항목 모두 독립 이득이 검증됐다는 뜻은 아니다.

1. Tracking KF 밖의 causal RGB supervision을 활용하고 admission과 replay를 분리한 mapper 설계. **구체 정책 조합의 기여**, broad first claim 아님.
2. Completed-work admission과 역할별 sampling을 같은 mapper에서 검증한 controlled analysis. **Count balancing 단독 이득이 없다면 분석 결과로 보고**, 독립 성능 기여로 부풀리지 않음.
3. Streaming 중 품질·historical retention·종료 시점 품질·시간/geometry의 trade-off 평가. **해당 실험 완료 후** 기여로 올림.

## 5. 기존 18개 코멘트와의 연결

| 코멘트 | 리서치에 근거한 대응 |
|---|---|
| C001 및 답글 | map의 기능부터 시작. VLA는 GS-VLA를 선택적으로 한 문장만; VLA가 map을 반드시 요구한다고 쓰지 않음 |
| C002 | optimization 부담이라는 문제의식은 유지하되 parameter 목록을 줄임 |
| C003 | Aria 고유명을 유지할 때만 공식 device citation 추가. 이 초안은 일반 RGB–inertial stream으로 범위를 표현 |
| C004 | 주어를 사후 refinement의 한계 또는 현재 map quality로 명확히 함 |
| C005 | generic speed 대신 도착·학습·history의 시간 관계를 중심에 둠 |
| C006–C008 | 문단 예고를 observation admission/replay/geometry 평가와 실제 일치시킴 |
| C009–C010 | 도입은 approaches 중심. 구체 method 비교는 ledger/related work로 이동 |
| C011–C012 | rapid 반복을 줄이고 한 문장당 하나의 causal step만 설명 |
| C013 | geometry를 처음부터 map usefulness의 조건으로 두되 아직 성과로 약속하지 않음 |
| C014 | starting point 대신 Gaussian initialization 또는 initial geometry로 정확히 표현 |
| C015 | surface·floater의 강한 기전 주장은 별도 검증 필요. 이번 초안에서 미검증 positional-gradient 주장을 제거 |
| C016–C017 | proposal 첫 문장에 frontend 이름 대신 admission/replay 결정을 제시 |
| C018 | proposal 문단에서 previous-work 설명을 반복하지 않음 |

## 6. Figure 1 제안

논문을 읽기 전에 문제를 이해시키려면 시스템 블록도보다 **같은 관측 궤적에서 학습에 반영된 정보가 어떻게 달라지는지** 보여주는 그림이 좋다.

- 왼쪽: 시간축에 KF와 non-KF, 특정 표면이 보이는 구간을 표시한다. training/eval 구분도 명확히 한다.
- 가운데: KF-only / immediate full admission / proposed admission의 선택·완료 update heatmap. 같은 전체 budget을 사용한다.
- 오른쪽 위: 이미 본 영역에서의 prefix held-out 품질과 새 영역의 관측 후 지연.
- 오른쪽 아래: 같은 old-region query가 이후 map update에도 유지되는지, geometry failure가 없는지.

마지막 프레임 뒤 구간은 별도 배경색으로 표시하면 zero-tail과 post-refinement 차이가 즉시 보인다. 아직 데이터가 없으므로 이 그림은 **설계 제안이며 결과 그림을 만들지 않았다**.

## 7. 쓸 수 없는 빠른 결론

- “Keyframes are insufficient” → 어떤 KF 선택·어떤 영역에서 부족한지 특정해야 한다.
- “All frames must be retained” → reservoir/coreset 대비 필요성 미입증이다.
- “Uniform replay solves forgetting” → replay support와 update 배분은 다르다.
- “Count balancing accelerates convergence” → 현재 비교에서 독립적인 우월성은 확정되지 않았다.
- “Our method achieves geometrically faithful real-time maps” → geometry와 concurrent-live 검증 이후에만 쓴다.
- “Prior methods need offline refinement” → VIGS-SLAM 최신 main protocol 등 예외가 있다.

**논문에서 가장 강하게 만들 부분은 과장된 universal claim이 아니라, 이미 제기된 관측·기억·계산의 충돌을 정확히 분리하고 같은 조건에서 답했다는 점이다.**
