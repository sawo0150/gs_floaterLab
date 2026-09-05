# 3. Method

본 연구는 VIGS-SLAM의 visual--inertial tracking 및 Gaussian mapping backend를 기반으로 한다. 시각 프론트엔드는 입력 시각 \(t\)까지 도착한 RGB와 IMU만을 사용하여 keyframe 집합 \(\mathcal{K}_t\), camera pose \(T_k\), 그리고 keyframe depth \(D_k\)를 추정한다. Mapping backend는 장면을

$$
\mathcal{G}_{\theta}
=\{(\boldsymbol{\mu}_i,\mathbf{q}_i,\mathbf{s}_i,o_i,\mathbf{c}_i)\}_{i=1}^{M}
$$

로 표현한다. 여기서 \(\boldsymbol{\mu}_i\), \(\mathbf{q}_i\), \(\mathbf{s}_i\), \(o_i\), \(\mathbf{c}_i\)는 각각 Gaussian의 위치, 회전, 크기, opacity, 색상이다. 기존 VIGS-SLAM의 keyframe mapping은 새 Gaussian의 생성과 densification 및 pruning을 담당한다. 본 연구는 이 구조를 대체하지 않고, 두 keyframe 사이에 이미 도착했지만 mapping에 사용되지 않은 RGB frame을 추가 photometric supervision으로 사용한다.

핵심은 dense frame의 이용 여부를 하나의 선택 문제로 다루지 않는 데 있다. 시각 \(t\)에서 관측 가능한 후보 집합을 \(\mathcal{C}_t\), mapping에 편입된 집합을 \(\mathcal{A}_t\subseteq\mathcal{C}_t\)라 하면, online mapper가 내려야 하는 결정은 다음 세 단계로 분해된다.

$$
\underbrace{B_t\longmapsto Q_t}_{\text{cardinality}}
\;\;\longrightarrow\;\;
\underbrace{(Q_t,\mathcal{C}_t)\longmapsto\mathcal{A}_t}_{\text{membership}}
\;\;\longrightarrow\;\;
\underbrace{\mathcal{A}_t\longmapsto\pi_t}_{\text{optimization order}},
$$

여기서 \(B_t\)는 입력 시각 \(t\)까지 실제로 제공된 mapping service, \(Q_t\)는 새로 편입할 수 있는 view 수, \(\pi_t\)는 현재 training pool을 방문하는 순서다. 아래 세 소절은 각각 이 세 결정을 정의한다. 모든 결정은 현재와 과거의 상태만 사용하며, 미래 frame, 최종 trajectory 길이, validation loss 또는 평가 영상을 참조하지 않는다.

## 3.1 Compute-Adaptive Causal View Admission

고정 stride 또는 고정 dense FPS는 입력률만 규정할 뿐, mapper가 그 supervision을 실제로 학습할 수 있는지는 반영하지 않는다. 반대로 모든 frame을 즉시 추가하면 계속 커지는 training set에 update가 분산된다. 우리는 새 view의 유입 속도를 **완료된 Gaussian optimization work**에 연결하여, mapper가 기존 pool에 반복 학습 기회를 제공한 만큼만 pool을 확장한다.

현재 admitted dense pool에서 view \(v\)가 성공적으로 사용된 누적 횟수를 \(n_v(s)\)라 하고, 한 view가 초기 노출을 넘어 반복 학습을 받았다고 판단하기 위한 최소 opportunity를 \(r\)이라 하자. 본문에서 기술하는 기본 configuration은 \(r=2\)를 사용한다. Replay update \(s\) 직전의 pool maturity를

$$
m_s^{-}=
\mathbb{1}\!\left[
|\mathcal{A}_{s^-}|>0
\;\land\;
\min_{v\in\mathcal{A}_{s^-}}n_v(s^-)\ge r
\right]
$$

로 정의한다. Backend는 성공한 single-view update 중 이미 mature한 pool 위에서 수행된 work만 별도의 service counter에 더한다.

$$
S_t^{\mathrm{mat}}
=\sum_{s\le t}m_s^{-}.
$$

Controller가 시각 \(t\)에서 관측한 새 mature service를 \(\Delta S_t^{\mathrm{mat}}=S_t^{\mathrm{mat}}-S_{t-1}^{\mathrm{mat}}\), 사용하지 않은 admission credit을 \(c_t\)라 하면

$$
c_t=c_{t-1}+\Delta S_t^{\mathrm{mat}},
\qquad
Q_t=\left\lfloor\frac{c_t}{r}\right\rfloor .
$$

실제로 \(a_t\le Q_t\)개의 view가 편입되면 \(c_t\leftarrow c_t-r a_t\)로 credit을 차감한다. 새 view가 들어온 직후에는 그 view의 \(n_v(t)\)가 작으므로 pool은 다시 immature 상태가 되고, 새 구성원이 \(r\)회의 opportunity를 받을 때까지 \(S_t^{\mathrm{mat}}\)가 증가하지 않는다. 각 update **직전**의 maturity를 검사하므로 기존 구성원의 opportunity debt를 갚는 update가 새 supervision을 위한 credit으로 다시 계산되지 않는다. 또한 controller는 이미 완료된 credit을 먼저 소비한 다음 새 interval을 발견하며, 현재 pending 후보가 없을 때 남은 credit을 폐기한다. 따라서 과거 계산이 미래에 도착할 frame을 미리 구매할 수 없다.

새로 닫힌 keyframe interval마다 첫 dense view 한 장은 bootstrap으로 즉시 편입한다. 이는 admitted view가 전혀 없어서 replay가 시작되지 않고, replay가 없어서 admission credit도 생기지 않는 초기 교착을 방지한다. 나머지 후보는 위의 service credit으로만 열린다. 이 설계에서 pool 크기 \(|\mathcal{A}_t|\)는 scene별로 지정한 FPS나 최종 frame 수가 아니라, 현재까지 실제로 완료된 optimization work에 의해 점진적으로 결정된다.

Replay 실행 자체도 다음 RGB 도착 시각을 넘지 않도록 제한한다. 최근 ordinary replay step의 실행시간을 \(\{\delta_i\}\)라 하고 보수적인 다음-step 비용을

$$
\widehat{\delta}_t=\max_{i\in\mathcal{H}_t}\delta_i
$$

로 둔다. \(\mathcal{H}_t\)는 최근 step으로 이루어진 짧은 history다. Sensor period의 online exponential moving average로 예측한 다음 도착 deadline을 \(\widehat{d}_{t+1}\)라 할 때,

$$
t_{\mathrm{wall}}+\widehat{\delta}_t\le\widehat{d}_{t+1}
$$

인 경우에만 replay 한 step을 시작한다. 이 검사는 admission score가 아니라 실행 가능성에 대한 deadline guard다. 각 update가 끝난 뒤 tracking queue와 deadline을 다시 확인하므로, dense replay는 foreground tracking과 경쟁하여 긴 비선점 작업을 만들지 않는다.

## 3.2 Trajectory-Balanced View Membership

Admission controller가 view 수를 정하면, membership module은 그 quota를 trajectory 상의 어느 frame에 배치할지를 결정한다. \(k_{j-1}\)과 \(k_j\)를 연속한 두 tracked keyframe의 frame index라 하자. 오른쪽 endpoint \(k_j\)가 도착한 뒤에만 interval

$$
\mathcal{I}_j=(k_{j-1},k_j),
\qquad
\mathcal{C}_j=\{v\mid k_{j-1}<v<k_j,\;v\notin\mathcal{K}_t\}
$$

을 닫힌 causal interval로 등록한다. 즉, 미래 keyframe을 예측하거나 아직 도착하지 않은 frame을 후보로 만들지 않는다. Training과 분리된 평가 frame은 \(\mathcal{C}_j\)를 구성할 때 제외한다.

**Interval 내부 선택.** 각 interval에서는 양 끝 keyframe과 이미 admitted된 dense view로부터 가장 멀리 떨어진 후보를 순서대로 선택한다. \(\mathcal{A}_j\)를 interval \(j\)에서 현재까지 편입된 dense view라 하면 다음 후보는

$$
v_j^{\star}
=\arg\max_{v\in\mathcal{C}_j\setminus\mathcal{A}_j}
\;\min_{u\in\{k_{j-1},k_j\}\cup\mathcal{A}_j}
|\tau(v)-\tau(u)|
$$

이다. \(\tau(\cdot)\)는 stream의 단조적인 시간 좌표이며, 현재 구현은 고정률 RGB stream의 frame index를 사용한다. 이 1차원 farthest-point rule은 첫 view로 interval 중앙 부근을 선택하고, 이후 가장 큰 미관측 temporal gap을 반복적으로 분할한다. 따라서 같은 quota에서 인접 frame만 연속적으로 편입되는 현상을 줄이면서 interval 전체의 support를 점진적으로 넓힌다.

**Interval 간 배분.** 여러 interval에 pending 후보가 남아 있을 때는 현재 admitted count가 가장 작은 interval에 다음 slot을 배정한다.

$$
j^{\star}
=\arg\min_{j:\,\mathcal{C}_j\setminus\mathcal{A}_j\neq\varnothing}
|\mathcal{A}_j|.
$$

이 water-filling rule은 후보가 많은 특정 interval이 admission을 독점하는 것을 막는다. 여기서 temporal maximin은 interval 안의 frame 순위를, water filling은 interval 사이의 quota 순위를 정할 뿐이다. 두 규칙 모두 optimizer가 다음에 학습할 view의 순서를 결정하지 않는다.

기본 membership은 temporal maximin을 사용한다. Fisher-assisted 설정에서는 temporal coverage를 유지한 채 기하학적으로 중복된 후보 사이만 구분하는 tie-break를 추가한다. World point \(\mathbf{X}_m\)을 view \(v\)의 camera 좌표 \((x_m,y_m,z_m)\)로 변환했을 때 normalized projection의 Jacobian은

$$
\mathbf{J}_{v,m}
=
\begin{bmatrix}
z_m^{-1} & 0 & -x_m z_m^{-2}\\
0 & z_m^{-1} & -y_m z_m^{-2}
\end{bmatrix}
\mathbf{R}_v
$$

이다. 이미 도착한 SLAM anchor들에 대한 Jacobian을 이어 붙여 정규화한 feature를 \(\bar{\mathbf f}_v\)라 하면, 기존 anchor view 집합 \(\mathcal{B}_j\)에 대한 방향 novelty를

$$
\nu(v)=
\min_{u\in\mathcal{B}_j}
\left(1-(\bar{\mathbf f}_v^{\top}\bar{\mathbf f}_u)^2\right)
$$

로 둔다. 제곱 cosine은 \(\mathbf{J}\)와 \(-\mathbf{J}\)가 같은 rank-one Fisher 방향을 나타낸다는 점을 반영한다. 최종 선택은 \((\text{temporal gap},\nu(v))\)의 **사전식 순서**로 이루어진다. 따라서 \(\nu(v)\)는 temporal gap이 같은 후보의 tie-break에만 사용되고, 높은 information score가 trajectory coverage를 희생하면서 전역 admission을 독점할 수 없다. 이 값은 Expected Information Gain의 정확한 계산이 아니라, 이미 도착한 공통 SLAM anchor에 대한 저비용 기하학적 중복 proxy다.

선택된 non-keyframe에는 두 endpoint pose를 이용해 초기 pose를 부여한다. \(\alpha_v=(v-k_{j-1})/(k_j-k_{j-1})\)라 하면 SE(3) 보간 pose는

$$
T_v^{(0)}
=\operatorname{Exp}\!\left(
\alpha_v\operatorname{Log}(T_{k_j}T_{k_{j-1}}^{-1})
\right)T_{k_{j-1}}
$$

이다. 구현에서는 이를 초기값으로 사용하고, DROID 계열 dense correspondence의 trajectory-filling 단계로 선택된 과거 frame의 pose를 두 endpoint에 대해 다시 정제한다. 두 endpoint가 모두 도착한 뒤에만 이 과정을 실행하므로 pose refinement 역시 causal하다. 정제된 frame은 depth가 없는 RGB supervision으로 backend에 등록되며, Gaussian 초기화나 topology 갱신에는 사용하지 않는다.

## 3.3 Shuffled Replay Optimization

Membership이 정한 admitted pool을 \(\mathcal{A}_t\)라 하자. 현재 map parameter \(\theta\)에 대한 empirical replay objective는

$$
\mathcal{L}_{\mathcal{A}_t}(\theta)
=\frac{1}{|\mathcal{A}_t|}
\sum_{v\in\mathcal{A}_t}\mathcal{L}_{\mathrm{rgb}}(v;\theta)
$$

로 정의한다. Priority score에 따라 view를 반복 선택하면 실제 update 분포는 \(\sum_v p_v\mathcal{L}_{\mathrm{rgb}}(v;\theta)\)로 바뀌며, membership 단계에서 만든 trajectory 비중이 optimizer 단계에서 다시 왜곡될 수 있다. 우리는 별도의 utility 가정을 추가하지 않고 현재 pool의 empirical objective를 따르기 위해 모든 eligible view를 균등하게 취급한다.

각 epoch \(e\)가 시작될 때 현재 pool에 대한 무작위 순열

$$
\pi_e\sim\operatorname{Uniform}(\mathfrak{S}_{|\mathcal{A}_t|})
$$

을 생성하고, 순열의 각 view를 복원 없이 한 번씩 사용한다. 따라서 한 epoch 안에서 같은 view가 중복 선택되거나 다른 view가 한 번도 선택되지 않는 현상이 없다. Epoch 도중 새 view \(v_{\mathrm{new}}\)가 admission되면 이를 남은 queue의 \(|Q_e|+1\)개 위치 중 하나에 균등하게 삽입한다.

$$
p\sim\operatorname{Uniform}\{0,\ldots,|Q_e|\},
\qquad
Q_e\leftarrow\operatorname{Insert}(Q_e,v_{\mathrm{new}},p).
$$

이 동적 삽입은 새 view를 항상 queue 앞에 두는 novelty-first 동작을 피하면서도, 길어진 epoch가 끝날 때까지 새 supervision을 지연시키지 않는다. 이미 현재 epoch에서 사용된 view는 refill 전까지 다시 들어오지 않는다. Pool이 성장하는 비볼록 3DGS에서는 고정 finite-sum random reshuffling의 수렴 보장을 그대로 적용할 수 없으므로, 본 설계의 역할은 이론적 최적성 보장이 아니라 제한된 online budget에서 **view별 opportunity를 균등화하는 것**이다.

선택된 dense view \(v\)에 대해 differentiable renderer가 생성한 영상을 \(\widehat{I}_v=\mathcal{R}(\mathcal{G}_{\theta},T_v)\)라 하면 replay loss는

$$
\mathcal{L}_{\mathrm{rgb}}(v;\theta)
=(1-\lambda_{\mathrm{ssim}})
\|\widehat{I}_v-I_v\|_1
+\lambda_{\mathrm{ssim}}
\bigl(1-\operatorname{SSIM}(\widehat{I}_v,I_v)\bigr).
$$

한 replay action은 한 view의 render, loss, backward, Adam update로 구성된다. Dense RGB gradient는 위치, 회전, 크기, opacity 및 색상을 포함한 Gaussian parameter를 갱신하지만, replay step은 densification/pruning 통계나 topology clock을 진행시키지 않는다. 새 Gaussian 생성과 topology 관리는 기존 keyframe mapping 경로에 남겨 두어, 추가 RGB supervision의 학습 빈도와 Gaussian 표현의 성장 주기가 서로 뒤섞이지 않도록 한다.

Replay는 별도의 offline refinement가 아니라 online mapping worker가 허용하는 service slot을 사용한다. 각 single-view update 후에는 tracking packet의 도착 여부와 §3.1의 deadline guard를 다시 확인하고, foreground work가 있으면 즉시 replay를 중단한다. Stream의 마지막 frame이 도착한 뒤에는 추가 optimizer step을 수행하지 않는다. 결과적으로 본 방법은 동일한 causal contract 안에서 (i) service가 허용하는 supervision cardinality, (ii) trajectory를 대표하는 membership, (iii) 그 membership을 보존하는 optimization order를 독립적으로 제어한다.
