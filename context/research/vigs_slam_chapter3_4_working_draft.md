# VIGS-SLAM Paper Working Draft — Chapters 3–4

> 상태: 초기 논문 구성안. 현재는 §3.2–§3.4의 논리 골격을 정리했다. 나머지 절은 논지와 최종 시스템 정의가 확정된 뒤 채운다.
>
> 작성 원칙: 실험 보고서가 아니라 논문 Method/System의 논리 구조를 관리한다. 세부 수치와 전체 ablation은
> Experiments chapter에서 다룬다.

## 3. Method

### 3.1 Background: 3DGS and the Causal Online Contract

<!-- TODO -->

### 3.2 Compute-Adaptive Causal View Admission

#### 이 절의 역할

- **핵심 질문:** keyframe 사이에 도착하는 RGB 중 현재 계산예산으로 감당할 수 있는 만큼을 어떻게 admission할 것인가?
- **이 절의 핵심 주장:** 적절한 inter-keyframe view 수는 고정 FPS가 아니라 실제 mapping service capacity에 따라 달라진다.
- **Contribution으로 주장하지 않을 것:** dense frame을 사용한다는 사실 자체.
- **Contribution으로 제시할 것:**
  - 고정 dense FPS 대신 완료된 GPU mapping work에 비례해 view-set 증가량을 결정.
  - 미래 trajectory, held-out loss, scene 이름, 절대 frame 경계를 사용하지 않는 causal admission.
  - Cardinality, membership, optimization order를 각각 §3.2, §3.3, §3.4로 분리.

#### Motivation에 넣을 내용

- 기존 GS-SLAM:
  - Tracking을 위해 선택된 keyframe을 주된 mapping supervision으로 사용.
  - Tracking에 적합한 표본과 전체 trajectory의 photometric optimization에 적합한 표본은 반드시 같지 않음.
- 프로젝트에서 확인한 출발 관측:
  - 동일 RGB objective에서도 inter-keyframe RGB를 포함한 view-set이 keyframe-only보다 낮은 held-out loss를 달성.
  - 따라서 keyframe 사이 RGB는 버려지는 입력이 아니라 활용 가능한 mapping supervision.
- 모든 RGB를 그대로 사용하는 방식의 한계:
  - 제한된 mapping budget이 계속 커지는 training set에 분산.
  - 각 view가 충분한 optimization opportunity를 받지 못할 수 있음.
  - Stream이 GPU service보다 빠르면 새로운 supervision을 추가하는 속도가 실제 학습 속도를 앞지름.
- **따라서 다룰 문제:** dense 사용 여부가 아니라, 현재 budget으로 학습 가능한 dense-view cardinality를 결정하는 것.

#### Budget-dependent cardinality를 설명할 내용

- Held-out loss를 mapping GPU budget에 따라 관측한 convergence curve를 분석 도구로 사용.
- 서로 다른 view-set density의 curve를 비교하면:
  - 짧은 budget에서는 작은 set이 반복 학습 측면에서 유리할 수 있음.
  - budget이 늘어나면 더 조밀한 set의 trajectory supervision 이득이 나타남.
  - 일정 density 이후에는 추가 view의 이득이 포화될 수 있음.
- 이 관측이 의미하는 것:
  - 하나의 고정 FPS를 모든 runtime condition에 적용할 근거가 없음.
  - 최적 cardinality의 닫힌 형태나 이론적 optimum은 주장하지 않음.
  - Controlled K-sweep은 online controller가 아니라, budget-dependent operating point의 존재를 보여주는 근거.

#### 제안 방법에 넣을 내용

- Online system이 직접 알 수 없는 정보:
  - 미래 frame과 최종 trajectory.
  - 앞으로 남을 총 mapping budget.
  - Held-out loss와 loss-optimal view-set 크기.
- Online에서 관측 가능한 정보:
  - 실제로 완료된 mapping/replay work.
  - Mapping update의 measured GPU time.
  - Tracking·PGBA와 경쟁한 뒤 실제로 남은 service capacity.
- Admission 원리:
  - 완료된 mapping work를 admission credit으로 환산.
  - Credit이 허용하는 수만큼 다음 inter-keyframe 후보를 training set에 편입.
  - GPU service가 빠르면 더 많은 view를 받고, mapping cost가 커지면 admission을 줄임.
  - Validation loss를 online에서 측정하거나 scene별 FPS를 튜닝하지 않음.
- 이 절에서 설명할 수준:
  - 왜 service와 admission을 연결하는지.
  - Controller의 입력, 출력, causal restriction.
  - Credit 계산과 runtime timing의 세부 구현은 §4.1로 이동.

#### 논문에서 보여줄 실험 근거 — 하나의 통합 평가

- Experiments chapter에 `Compute-Adaptive View Admission` 평가 블록 하나를 둔다.
- 모든 arm에서 membership, shuffle order, loss, topology 설정을 동일하게 고정하고 admission만 변경.
- 비교 대상:
  - keyframe-only.
  - 몇 개의 대표 fixed-density 설정.
  - all-frame admission.
  - proposed service-matched admission.
- Budget 또는 GPU 처리량을 바꾸면서 동일한 실험 grid를 실행.
- 하나의 결과 묶음에서 두 가지를 함께 제시:
  - **Convergence plot:** fixed-density loss curves와 budget별 lower envelope.
  - **Summary table:** proposed policy가 scene/hardware별로 strongest fixed baseline에 얼마나 가까운지와 strict deadline 충족 여부.
- 필요한 통제:
  - RGB-only density 분석에서는 depth/normal·carve confound 제거.
  - 실제 end-to-end 비교에서는 모든 arm에 동일한 geometry 설정 사용.
  - 최소 3 scenes × paired seeds.
  - Scene별 별도 parameter tuning 금지.
  - 전체 trajectory를 포괄하고 training과 겹치지 않는 fixed held-out split 사용.
- 기존 exp66 결과:
  - Motivation과 실험설계의 pilot으로 사용.
  - 단일 장면 결과를 그대로 일반 결론으로 제시하지 않고, 동일 설계의 multi-scene 결과로 보강.

#### Claim boundary

- **주장할 수 있는 것:**
  - View-set density의 적정점이 mapping budget에 의존함을 convergence curves로 보임.
  - Measured service 기반 admission이 고정 FPS보다 runtime capacity 변화에 적응함을 실측.
- **주장하지 않을 것:**
  - Service quota가 전역적인 held-out-loss optimum을 보장.
  - Dense density가 모든 budget에서 단조롭게 좋음.
  - Dense supervision의 이득이 Fisher novelty 하나로 설명됨.
- 권장 표현:
  - “The controller tracks a budget-dependent operating region rather than assuming a universal input rate.”
  - “Admission is matched to completed mapping service without using future frames or evaluation feedback.”

#### 다음 절로의 연결

- §3.2: **몇 장을 받을지 결정.**
- §3.3: **주어진 quota에서 어떤 view를 받을지 결정.**
- §3.4: **선택된 view에 학습 기회를 어떤 순서로 줄지 결정.**

### 3.3 Trajectory-Balanced View Membership

#### 이 절의 역할

- **핵심 질문:** §3.2가 허용한 quota 안에서 어떤 inter-keyframe RGB를 training set에 편입할 것인가?
- **이 절의 핵심 주장:** membership은 높은 novelty만 추구하기보다 전체 trajectory의 시간적 측도를 먼저 보존해야 한다.
- **§3.2와의 분리:** §3.2는 view 수를 정하고, §3.3은 그 수 안에서 view의 위치를 정한다.
- **§3.4와의 분리:** 여기서는 training set의 구성만 정하며, 선택된 view의 학습 순서는 바꾸지 않는다.

#### Motivation에 넣을 내용

- 전체 trajectory loss를 평가 목표로 삼으면 training set은 도착한 trajectory를 가능한 한 균형 있게 대표해야 함.
- Keyframe-only supervision의 한계:
  - Keyframe은 tracking과 geometric optimization을 위해 선택되므로 시간축에서 균등한 표본이 아님.
  - 빠른 운동 구간이나 긴 keyframe interval에는 supervision 공백이 남을 수 있음.
- 전역 novelty 또는 residual만으로 view를 고르는 방식의 한계:
  - 드문 pose나 현재 오차가 큰 구간에 quota가 집중되어 trajectory의 시간적 비중을 왜곡할 수 있음.
  - Residual은 현재 optimizer 상태에 따라 변하므로 membership 자체가 불안정해질 수 있음.
- 따라서 membership에는 두 단계의 우선순위가 필요함:
  - **1차:** trajectory 전 구간에 admission 기회를 배분해 시간적 대표성을 유지.
  - **2차:** 각 구간 안에서 이미 선택된 view와 중복이 적은 후보를 선택.

#### 제안 방법에 넣을 내용

- 연속한 두 keyframe 사이를 하나의 causal interval로 정의.
- §3.2에서 새 admission credit이 생기면, 아직 충분히 대표되지 않은 interval부터 quota를 배분.
- Interval 내부 후보는 양 끝 keyframe과 기존 선택 view 사이의 가장 큰 공백을 먼저 줄이는 maximin 순서로 정렬.
  - 첫 dense view는 interval 중앙 부근을 대표.
  - 이후 view는 남아 있는 가장 큰 시간적 공백을 차례로 분할.
  - 결과적으로 특정 순간에 후보가 몰리지 않고 interval 전체를 점진적으로 채움.
- 여러 interval이 동시에 대기할 때는 admitted view가 적은 interval부터 채우는 water-filling을 사용.
- Novelty의 역할은 **trajectory 균형을 대체하는 전역 점수**가 아니라, 동일 interval·동일 quota 안에서 중복을 줄이는 국소 기준으로 제한.
- 미래 keyframe, held-out image, validation loss를 사용하지 않고 현재까지 닫힌 interval만 처리.

#### 왜 이 구성이 필요한지 설명할 내용

- Temporal stratification은 training set의 표본 비중이 특정 운동 구간에 과도하게 쏠리는 것을 막는 1차 장치.
- Interval 내부 maximin은 같은 quota로 더 넓은 temporal support를 덮기 위한 2차 장치.
- 이 순서는 “가장 새로운 view가 항상 가장 좋은 gradient를 준다”는 가정을 요구하지 않음.
- 인접한 dense view의 유용한 중첩은 유지하면서, 거의 동일한 시점의 반복 편입만 줄임.
- 결과적으로 §3.2에서 정한 cardinality를 trajectory 전반에 배치하는 membership rule로 해석.

#### 논문에서 보여줄 실험 근거 — 고정 cardinality membership ablation

- 모든 arm에서 view 수, optimizer order, update budget, loss를 고정하고 membership만 변경.
- 하나의 표 또는 convergence figure에서 다음 기준을 비교:
  - Random membership.
  - Temporal-uniform membership.
  - Global novelty/coverage membership.
  - Proposed trajectory-stratified maximin membership.
  - Residual-based membership.
- 보고할 핵심:
  - 동일 cardinality에서 held-out loss AUC와 최종 품질.
  - 선택 view의 interval별 분포 또는 최대 temporal gap을 보조 통계로 제시.
- 기존 Stage B pilot의 해석:
  - Global coverage는 temporal-uniform보다 AUC가 나빠, novelty 단독 최적화가 trajectory 대표성을 보장하지 않음을 보였음.
  - Interval quota를 보존한 representative selection의 이득은 작았으므로, novelty를 주된 수렴 원인으로 과장하지 않음.
  - 논문의 중심 근거는 “전역 novelty의 우월성”이 아니라 **trajectory balance를 먼저 보존해야 한다는 것**.

#### Related-work positioning

- iMAP과 NICE-SLAM도 제한된 memory에서 informative 또는 overlapping keyframe을 고르지만, 주된 대상은 sparse keyframe management임.
- 본 절은 keyframe 사이에서 연속적으로 도착하는 RGB를 대상으로 하며, cardinality 결정과 optimization order를 membership에서 명시적으로 분리.
- Coreset optimum이나 validation-gradient matching을 푸는 것으로 서술하지 않고, causal trajectory coverage를 유지하는 경량 선택 규칙으로 위치시킴.

#### Claim boundary

- **주장할 수 있는 것:** 같은 view 수에서 trajectory-stratified membership이 전역 novelty 우선보다 안정적으로 시간적 대표성을 유지함.
- **주장하지 않을 것:** maximin view가 Fisher information 또는 held-out improvement를 직접 최대화함.
- **주장하지 않을 것:** 제안 membership이 전역 최적 coreset임을 보장함.

#### 다음 절로의 연결

- §3.3이 trajectory를 대표하는 empirical training distribution을 구성했다면, §3.4는 optimizer가 그 분포를 다시 왜곡하지 않도록 학습 순서를 정함.

### 3.4 Shuffled Epoch Sampling

#### 이 절의 역할

- **핵심 질문:** §3.3에서 구성한 view set에 제한된 update를 어떤 순서로 배분할 것인가?
- **이 절의 핵심 주장:** 현재 pool에서는 각 view를 균등하게 취급하고, 이를 비복원 random shuffle로 실현해야 membership이 만든 trajectory balance를 보존할 수 있다.
- **이 절에서 다루지 않을 것:** pool을 얼마나 빨리 키울지와 late-arriving view의 총 학습량. 이는 §4.1의 admission 문제로 분리.

#### Motivation에 넣을 내용

- §3.3의 목적은 현재까지 관측된 trajectory를 근사하는 training set을 만드는 것.
- 이 pool에서 novelty-first나 residual-first 순서를 반복 사용하면 일부 view의 gradient가 과대표집되어, membership 단계에서 맞춘 표본 비중을 optimizer가 다시 바꿈.
- 반면 현재 pool 위의 균등 sampling은 별도의 utility 가정을 추가하지 않고 empirical training objective를 그대로 따르는 선택.
- 단순한 균등 i.i.d. sampling도 평균적인 선택 확률은 같지만, 짧은 online budget에서는 같은 view의 중복과 다른 view의 미선택이 발생함.
- 따라서 필요한 것은:
  - **분포 수준:** 모든 eligible view에 같은 확률을 부여.
  - **실현 수준:** 한 epoch 안에서는 중복 없이 한 번씩 기회를 부여.

#### 제안 방법에 넣을 내용

- 현재 eligible pool을 무작위 순열로 만들고 앞에서부터 한 view씩 학습하는 shuffled epoch을 사용.
- 한 epoch이 끝나기 전에는 이미 사용한 view를 다시 뽑지 않음.
- 새 view가 epoch 도중 admission되면 남은 queue의 무작위 위치에 삽입:
  - Frontier에 즉시 반복 배치하지 않음.
  - 다음 epoch까지 일괄 지연하지도 않음.
  - 기존 순열의 무작위성을 유지하면서 현재 epoch 안에서 한 번의 기회를 제공.
- Novelty와 residual은 membership 진단이나 ablation에는 사용할 수 있지만, 기본 optimizer order의 우선순위로 사용하지 않음.

#### 이론적 직관을 설명할 수준

- **첫 번째 층 — 분포 보존:**
  - 평가 대상이 시간적으로 균등한 trajectory이고 §3.3의 pool이 이를 근사한다면, 현재 pool의 균등 sampling이 가장 직접적인 대응.
  - View-dependent priority는 다른 objective를 명시적으로 선택하는 것과 같으므로 별도 정당화가 필요함.
- **두 번째 층 — opportunity balance:**
  - 비복원 shuffle은 같은 주변 선택분포를 유지하면서 한 epoch 내 중복 draw와 starvation을 제거.
  - 이는 gradient를 특별한 방향으로 유도하기보다, 제한된 update를 pool 전체에 고르게 분산하는 장치.
- Random reshuffling의 finite-sum 최적화 결과는 이 선택의 선례로 인용하되, 동적으로 성장하는 비볼록 3DGS에 해당 보장을 그대로 주장하지 않음.
- Parameter가 매 step 변하므로 epoch gradient가 full-pool gradient와 정확히 같다고 쓰지 않고, **국소적으로 표본 편향과 count imbalance를 줄이는 설계**라고 표현.

#### 논문에서 보여줄 실험 근거 — 고정 membership order ablation

- §3.3에서 고정한 동일 view set과 동일 update budget을 사용하고 training order만 변경.
- 하나의 표 또는 convergence figure에서 비교:
  - Proposed shuffled epoch.
  - Uniform sampling with replacement.
  - Novelty-first.
  - Residual-first.
  - 필요하면 novelty/residual과 shuffle을 섞은 alternating policy를 보조 baseline으로 포함.
- 보고할 핵심:
  - Held-out loss AUC와 최종 품질.
  - View별 selection-count spread를 opportunity balance의 보조 통계로 제시.
- 기존 Stage C pilot의 해석:
  - Novelty-first와 residual-first는 shuffle보다 AUC MSE가 약 10–11% 높아(나빠), informative-looking view의 반복 우선순위가 빠른 일반화를 보장하지 않음을 보였음.
  - With-replacement sampling은 shuffle보다 AUC MSE가 약 1.7% 높았으며 selection count도 불균등했음.
  - 따라서 큰 효과는 비균등 priority가 만든 분포 왜곡에서, 작은 추가 효과는 비복원 opportunity control에서 온다는 해석을 사용.

#### Related-work positioning

- Random reshuffling은 finite-sum optimization에서 널리 사용되는 순서 정책이며, without-replacement SGD 분석을 이론적 배경으로 인용.
- iMAP의 loss-guided sampling처럼 informative sample을 우선하는 방식과 문제 설정을 구분:
  - 해당 방식이 일반적으로 틀렸다고 주장하지 않음.
  - 본 시스템의 dense trajectory pool과 제한 budget에서는 균등 shuffle이 더 안정적이었다는 실측에 근거.
- 본 절의 contribution은 새로운 SGD 이론이 아니라, causal 3DGS mapping에서 **membership selection과 optimizer ordering을 분리하고 random reshuffling을 채택한 시스템적 설계**.

#### Claim boundary

- **주장할 수 있는 것:** 고정 membership과 budget에서 shuffled epoch이 실험한 priority policies보다 빠르고 안정적인 held-out convergence를 보임.
- **주장하지 않을 것:** Random reshuffling이 모든 nonconvex·nonstationary online optimization에서 항상 우월함.
- **주장하지 않을 것:** 현재 pool의 균등 gradient가 아직 도착하지 않은 미래 trajectory의 정확한 gradient임.

#### 다음 절로의 연결

- §3.2–§3.4는 각각 cardinality, membership, order를 결정.
- Pool 성장으로 epoch이 길어지거나 새 view의 최적화 기회가 희석되는 문제는 sampling weight를 왜곡해 해결하지 않고, §4.1의 service-matched quota enforcement에서 다룸.

### 3.5 Carve Loss

<!-- TODO -->

## 4. System Realization

### 4.1 Runtime Quota Estimation and Enforcement

<!-- TODO -->

### 4.2 Active/Archive Pool Separation (Optional)

<!-- TODO -->

### 4.3 Deadline-Guarded Execution and PGBA Transport (Optional)

<!-- TODO -->

## Working References

- Hoffmann et al., *Training Compute-Optimal Large Language Models*, NeurIPS 2022.
- Sucar et al., *iMAP: Implicit Mapping and Positioning in Real-Time*, ICCV 2021.
- Zhu et al., *NICE-SLAM: Neural Implicit Scalable Encoding for SLAM*, CVPR 2022.
- Chen et al., *AdaptSLAM: Edge-Assisted Adaptive SLAM with Resource Constraints via Uncertainty Minimization*, 2023.
- Zhu et al., *VIGS-SLAM: Visual Inertial Gaussian Splatting SLAM*.
- Mallick et al., *Taming 3DGS: High-Quality Radiance Fields with Limited Resources*.
- Shamir, *Without-Replacement Sampling for Stochastic Gradient Methods*, NeurIPS 2016.
- Ahn et al., *SGD with Shuffling: Optimal Rates without Component Convexity and Large Epoch Requirements*, NeurIPS 2020.
- Mishchenko et al., *Random Reshuffling: Simple Analysis with Vast Improvements*, NeurIPS 2020.
