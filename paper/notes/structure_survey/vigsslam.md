# vigsslam — 구조 해부 (§3, §4)

## 기본 정보

| | |
|---|---|
| 논문 | VIGS-SLAM: visual-inertial 3DGS SLAM (Zihan Zhu et al.) |
| venue | ECCV/LNCS 계열 1단 조판, 31쪽 (본문 ~14쪽 + 참고문헌 + supp.) |
| 절 구성 | 1 Intro / 2 Related / **3 Method (3.1 Tracking, 3.2 IMU Initialization, 3.3 Gaussian Splatting Mapping)** / **4 Experiments (4.1 Mapping·Tracking·Rendering, 4.2 Tracking Robustness, 4.3 Ablation Study)** / 5 Conclusion |
| 왜 보나 | **우리 baseline이다.** 우리가 무엇을 바꾸는지가 이 논문의 문장 단위로 정해진다 |

---

## ★ 발견 1 — 우리가 교체하는 대상이 §3.3의 **두 문장**이다

`3.3 Gaussian Splatting Mapping` → run-in 볼드 `Map Management.` 문단:

> *"For each new keyframe, **we run 10 mapping iterations.** In each iteration, we **randomly sample
> keyframes from the frontend tracking frame graph E** along with two global keyframes to render color
> Î and depth D̂ from the Gaussian map."*

| baseline 문장 | 우리 기여 |
|---|---|
| "For each new keyframe, we run 10 mapping iterations" | **C1** — keyframe 개수가 아니라 **완료된 GPU service**가 update 예산을 정한다 |
| "we randomly sample keyframes from the frame graph E" | **C2** — count-Gibbs × K-view 비복원이 순서를 정한다 |
| (frame graph E = tracker가 고른 keyframe만) | **§3.0의 문제 제기** — E는 tracking 기준으로 골라진 표본이다 |

★ **§3.0 도입은 이 문장을 인용하는 것으로 시작하는 게 가장 강하다.**
"기존 방법이 대충 한다"가 아니라 **"state-of-the-art가 실제로 이렇게 쓴다"**를 보이는 것이다.
우리 outline §1 문단 2("tracker keyframe은 tracking 기준으로 골라진 표본이다")의 근거가 바로 여기 있다.

## ★ 발견 2 — §3 골격은 **데이터 흐름 순서**다 (유도형도, 문제↔해법 대칭도 아님)

```
3. Method  (도입: 파이프라인 한 문단 + Fig. 2)
  3.1 Tracking             ← Vision Residual. / Inertial Residual. / (최적화 모듈)
  3.2 IMU Initialization
  3.3 Gaussian Splatting Mapping  ← Preliminary. / Map Management. / Loop Closure Gaussian Update.
```

- 소절 = **시스템 모듈**, 서브헤드 = **run-in 볼드**(별도 번호 없음). 2단 조판에서 지면을 아끼는 방식
- **Preliminaries를 §3.3 안의 run-in 볼드 하나로** 처리했다 (CONVERGE는 독립 절, CaRtGS는 독립 소절)
  → 배경이 적을 때 쓰는 3번째 선택지
- 도입 문단이 입력(`{I_i}`, `{a_k, ω_k}`)부터 출력까지 한 번에 훑는다. 문제 진단이 §3에 **없다** —
  전부 §1로 갔다

→ ✗ **우리는 이 형식을 따르면 안 된다.** 우리 §3은 모듈 나열이 아니라 **세 결정(cardinality/
membership/ordering)의 분해**이고, 각 결정에 진단과 유도가 붙는다. VIGS-SLAM은 시스템 논문,
우리는 그 시스템 안의 한 결정을 파고드는 논문이다.

## ★ 발견 3 — **online 계약이 §4 Baselines 문단 한 문장으로 선언된다** (가장 중요)

> *"**To evaluate the online setting**, for DROID-SLAM, Splat-SLAM, HI-SLAM2, and our VIGS-SLAM,
> **we report metrics computed before the final global bundle adjustment and the final color refinement
> (which typically takes over 10 minutes).** Results with these refinements are provided in the
> supplementary material."*

이 한 문장이 하는 일:
1. 평가 조건에 **이름을 붙인다** ("online setting")
2. **무엇을 제외했는지 정확히** 말한다 (final global BA + final color refinement)
3. 제외한 것의 **크기를 수치로** 준다 ("over 10 minutes") — 사소한 게 아님을 보임
4. **누구에게 적용했는지** 나열한다 (경쟁자 3개 + 우리) — 우리만 불리하게/유리하게 한 게 아님
5. 제외한 조건의 결과는 **버리지 않고 supplementary로** 보낸다

★★ **우리 strict streaming 계약 S1–S6이 정확히 이 형식으로 §4.1 Setup에 들어가야 한다.**
지금은 `experiments/protocol/CURRENT.md`에만 있고 논문 서술 형태가 없다. 특히 **zero-tail**은
이 논문의 "before the final global BA and color refinement"와 성격이 같으며,
**우리 baseline 자신이 이 조건을 인정한 선례**라는 점에서 인용 가치가 크다.

우리 버전 초안:
> *To evaluate the strict streaming setting, all methods are given the same sensor trace, the same
> 1.5× wall-clock budget (97.65 s for aria1253), and **zero optimizer updates after the last sensor frame**.
> Held-out views are excluded from all supervision. Results with a post-stream refinement tail are
> reported in the supplementary material.*

## ★ 발견 4 — **비교 불가를 명시적으로 선언한다**

`Metrics.` 문단:

> *"For rendering evaluation, we report PSNR, SSIM, and LPIPS **on frames that are not used as keyframes
> by any method, excluding all views involved in mapping.**
> **Consequently, the rendering results reported by MM3DGS-SLAM are not directly comparable to ours.**"*

- held-out의 정의를 "**어느 방법도** keyframe으로 쓰지 않은 프레임"으로 잡는다 (교집합 기준)
- 그 정의 때문에 특정 논문의 수치를 그대로 못 쓴다는 것을 **표 앞에서 미리 말한다**

★ **우리 claims 금지문장 #2 (live-Gen1 PSNR과 strict-file PSNR을 한 표에서 비교 금지)의 해답이다.**
금지가 아니라 **"…are not directly comparable to ours"라는 한 문장으로 처리**하면 된다.
특히 exp73은 strict zero-tail 실험이 아니라 final-map scheduler/admission A/B이므로,
그 수치가 표에 들어간다면 이 문장이 반드시 함께 가야 한다.

## ★ 발견 5 — **표 캡션이 숫자마다 출처를 밝힌다**

Table 1 캡션:

> *"Best results are highlighted as first, second, and third. 'F' indicates failure.
> **Results for SVO, TartanVO, DSO, MSCKF, OKVIS, VINS-Mono, and ORB-SLAM3 are as reported by the
> ORB-SLAM3 paper; DROID-SLAM numbers are from its paper. All other results are reproduced from their
> official code.**"*

- 인용 수치 / 재현 수치 / 실패를 **캡션에서 분리**
- `F`(실패)를 지우지 않고 표에 남긴다

→ 우리 Table 2(baselines)에도 필요하다. **MonoGS-style covisibility baseline을 직접 구현할지
논문 수치를 인용만 할지**가 experiment_table의 미결 항목인데, **캡션 표기 규칙이 있으면 섞어도 된다.**
결정을 미룰 필요가 없어졌다.

또 다른 성실성 장치:
> *"For DBA-Fusion and its successor VINGS-Mono, **we worked closely with the first author** and made
> targeted modifications to improve their performance. **As confirmed by its authors,** MM3DGS-SLAM
> primarily targets an RGB+LiDAR+IMU setup; the open-sourced code does not fully support a pure
> visual-inertial setting."*
= 경쟁자를 약하게 돌려놓고 이겼다는 의심을 원천 차단한다.

## ★ 발견 6 — §4.2가 **열화 조건 실험을 독립 소절**로 둔다

`4.2 Tracking Robustness` → `Strided Evaluation.`:

> *"To evaluate robustness under degraded visual input, we create strided variants of EuRoC and
> RPNG AR Table by **temporally subsampling RGB frames with different strides while keeping the original
> IMU readings**, simulating frame drops, limited bandwidth and high-speed motion.
> We report average **Recall@5cm and Recall@10cm instead of ATE** [열화 조건에선 지표도 바꾼다]"*

원 데이터셋을 변형해 **스트레스 축을 인공적으로 만든다.** 그리고 그 조건에 맞는 지표로 갈아탄다.

★ **우리 P02(rate invariance)가 정확히 이 자리다.** pace {0.75, 1.0, 1.5, 2.0}× × {5090, 5070Ti}는
"입력 속도를 인위적으로 바꿔 강건성을 본다"는 같은 발상이다.
→ **§4에 `4.x Rate Robustness` 같은 독립 소절 이름을 줄 근거가 생겼다.** 지금은 Fig.4로만 잡혀 있다.

## ★ 발견 7 — Ablation을 **(a)–(f) 명명 리스트**로 쓴다

> *"We report ablation results for 6 design choices in Table 6. In **(a) w/o IMU Bias Estimation**, the IMU
> bias is fixed to zero and not optimized. In **(b) w/o IMU Fusion**, the optimization is constrained solely
> by visual residuals. In **(c)**, we remove the inertial-only optimization stage during IMU initialization.
> ... Table 6 demonstrates that removing any component will degrade tracking accuracy as well as
> robustness, while our full system achieves the best results."*

각 항목이 **"무엇을 껐는지"를 한 문장으로 정확히 정의**한다. "w/o X" 라벨만으로는 재현이 안 되기 때문.
→ 우리 ablation(admission·ordering·carve)도 이 형식. 특히 ERCB는 β=0과 K 축소가 다른 조작이라
라벨만으로는 절대 안 통한다.

---

## ★ 훔칠 것

1. **§3.0에서 baseline의 실제 문장을 인용** ("we run 10 mapping iterations" / "randomly sample keyframes")
2. **§4.1 Setup의 계약 선언 문장** — 이름 + 제외 항목 + 제외 크기 + 적용 대상 + 제외본은 supp.
3. **"not directly comparable to ours" 문장** — 금지 대신 명시
4. **표 캡션의 출처 표기** (인용/재현/실패) → Table 2 baseline 혼합 문제 해결
5. **경쟁자를 제대로 돌렸다는 증거** (원저자 협조·확인)
6. **열화 조건 독립 소절 + 조건에 맞는 지표 교체** → P02를 `Rate Robustness` 소절로
7. **(a)–(f) ablation 명명 + 조작 정의 한 문장씩**
8. **실패(F)를 표에 남기기**

## ✗ 우리와 다른 점

- **1단 31쪽 시스템 논문.** 모듈 나열형 §3. 우리 §3(결정 분해 + 유도)와 목적이 다르다.
- **§3에 진단이 없다.** 전부 §1로 갔다. 우리는 §3.0에 진단을 둔다.
- **계산 예산 계약이 없다.** online 선언은 있으나 wall-time 예산 고정은 없다 → taming3dgs 참조.
- **mapping 쪽 ablation이 1줄**(loop closure Gaussian update 하나뿐). 우리가 파고드는 지점이 여기다.

## 없는 move

| 이 논문에 없는 것 | 우리에게 필요한가 |
|---|---|
| mapping supervision 배분에 대한 분석 | **필요 — 이게 우리 논문 전체다** |
| 계산 예산 고정 비교 | **필요** |
| 유도 | **필요** |
| 버린 대안 기록 | **필요** |
| Limitations | 있으면 좋음 (이 논문은 Conclusion 흡수) |
