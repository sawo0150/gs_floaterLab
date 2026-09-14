# exp76 — Mean-normalized interval Softmax RR

> 날짜: 2026-09-09  
> 질문: 임의의 `0.5 * mean` threshold 없이, 원래의 entropy-regularized
> count-softmax를 평균 service로 정규화하는 것만으로 exp75 최고 설정과 호각을 이룰 수 있는가?  
> 판정: **causal RR에는 작지만 일관되게 우세했으나, exp75 최고 설정과는 호각 실패.**

## 1. 단일 수식

interval `j`의 frame 수, 누적 선택 수, member당 service를 각각

\[
m_j=|G_j|,\qquad c_j,\qquad r_j=\frac{c_j}{m_j}
\]

라 하고 현재 전체 frame의 평균 service를

\[
\bar r_t=\frac{\sum_jc_j}{\sum_jm_j}
\]

로 둔다. Frame-uniform base distribution은
\(q_j=m_j/\sum_km_k\)이다. 다음 entropy-regularized 상대-service 문제

\[
p^*=\arg\min_{p\in\Delta}
\left[
  \sum_jp_j\frac{r_j}{\bar r_t}
  +\frac{1}{\gamma}D_{KL}(p\|q)
\right]
\]

의 해는

\[
p_j^*\propto m_j\exp\!\left(-\gamma\frac{r_j}{\bar r_t}\right)
\]

이다. 실제 구현은 이 weight의 Gumbel top-`K`로 interval `K=8`개를
Plackett–Luce 비복원 추출하고, 각 interval 내부 frame도 persistent random
reshuffling으로 비복원 추출한다.

- threshold, clipping, phase switch, loss term이 없다.
- 모든 count를 같은 배수로 늘려도 확률이 변하지 않는다.
- \(a=e^\gamma\)는 service가 평균 1단위 더 많은 interval에 적용되는 상대 penalty다.
  exp75의 bounded maximum odds와 달리 전역 hard cap은 아니다.
- \(\gamma=0\)은 size-aware interval RR control이다.

## 2. 실험 계약

| 항목 | 305 | 12F |
|---|---:|---:|
| training frame pool | 2,352 | 1,925 |
| interval 수 | 312 | 408 |
| optimizer update / last arrival | 18,661 | 24,421 |
| llffhold-8 held-out frame | 336 | 276 |

공통 조건은 fixed VIGS pose/init, resolution `r=4`, 모든 training frame의 causal
즉시 admission, 마지막 arrival 뒤 update 0회(zero-tail)다. Development는 seed 0만
사용했고 \(a=e^\gamma\in\{1,1.1,1.2,1.25,1.3,1.35,1.4,1.5,2\}\)를
sweep했다. 한 공통값이 두 장면 모두에서 causal RR 대비 overall과 worst-Q1을 올려야
통과시키고, 그 뒤에만 seed 1로 재검증했다. Scene별 파라미터는 허용하지 않았다.

## 3. Seed-0 sweep

모든 수치는 후보−causal RR held-out PSNR(dB)이다.

| \(e^\gamma\) | \(\gamma\) | 305 mean | 305 worst-Q1 | 305 late | 12F mean | 12F worst-Q1 | 12F late | 판정 |
|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 1.00 | 0.000000 | +0.044 | -0.246 | -0.629 | +0.029 | +0.190 | +0.022 | fail |
| 1.10 | 0.095310 | -0.346 | -1.535 | -1.224 | -0.058 | -0.103 | -0.147 | fail |
| 1.20 | 0.182322 | +0.085 | +0.247 | -0.566 | -0.197 | -0.614 | -0.516 | fail |
| **1.25** | **0.223144** | **+0.204** | **+0.181** | -0.339 | **+0.027** | **+0.106** | **+0.107** | **PASS** |
| 1.30 | 0.262364 | -0.231 | -0.071 | -0.891 | -0.068 | -0.305 | -0.371 | fail |
| 1.35 | 0.300105 | +0.245 | +1.023 | -0.394 | -0.098 | +0.030 | -0.182 | fail |
| 1.40 | 0.336472 | +0.062 | +0.468 | -0.381 | -0.095 | -0.077 | +0.024 | fail |
| 1.50 | 0.405465 | +0.462 | +0.751 | -0.295 | -0.193 | -0.378 | -0.219 | fail |
| 2.00 | 0.693147 | +0.424 | +1.498 | +0.314 | -0.578 | -0.673 | -0.416 | fail |

\(e^\gamma=1.25\)만 두 장면의 mean과 worst-Q1을 동시에 통과했다. 305는
강한 correction을 비교적 잘 받지만 12F는 \(\gamma\)가 커질수록 빠르게 손해를 봤다.
PSNR 곡선이 매끄럽지 않은 것은 작은 draw 차이가 Gaussian split/prune 경로를 바꾸기
때문이며, 한 seed의 장면별 최고점을 고르지 않고 공통 통과조건을 사용한 이유다.

## 4. 고정값의 독립 seed 검증

선택값은 `K=8`, \(\gamma=\log1.25\)다.

| Scene | seed | RR | normalized | exp75 best | Δ vs RR | Δ vs best | worst-Q1 Δ vs RR | RR-hard-Q1 Δ | late Δ vs RR |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 305 | 0 | 32.154 | 32.358 | 32.641 | **+.204** | -.283 | **+.181** | **+.670** | -.339 |
| 305 | 1 | 31.999 | 32.034 | 32.764 | **+.035** | -.731 | **+.313** | **+1.010** | +.039 |
| 12F | 0 | 27.021 | 27.048 | 27.244 | **+.027** | -.195 | **+.106** | **+.435** | +.107 |
| 12F | 1 | 26.905 | 26.996 | 27.203 | **+.091** | -.207 | **+.333** | **+.524** | +.218 |

두 장면×두 seed 평균은 다음과 같다.

| 비교 | mean Δ | worst-Q1 Δ | RR-hard-Q1 Δ | late-third Δ |
|---|---:|---:|---:|---:|
| normalized − causal RR | **+.089 (4/4+)** | **+.233 (4/4+)** | **+.660 (4/4+)** | +.006 (3/4+) |
| normalized − exp75 best | **-.354 (0/4+)** | -.603 (1/4+) | -.135 (1/4+) | **-.632 (0/4+)** |

Scene별 두-seed 평균은 305에서 RR 대비 +.119dB이나 exp75 best 대비 -.507dB,
12F에서 각각 +.059dB와 -.201dB다. 따라서 **일반 RR과는 호각 이상이지만, 기존
최고 설정과 호각이라는 가설은 기각**한다.

## 5. 무엇을 배웠는가

| 4-run 평균 | causal RR | normalized | exp75 relative-floor |
|---|---:|---:|---:|
| frame count CV ↓ | .9989 | **.9037** | .9014 |
| dynamic 128-step temporal entropy ↑ | .9737 | **.9727** | .9613 |
| final Gaussian 수 | 436,492 | 439,151 | 452,593 |

Normalized Softmax는 relative-floor와 거의 같은 global count CV를 만들면서 RR 수준의
temporal entropy를 더 잘 보존했다. 그런데 PSNR은 relative-floor보다 평균 .354dB,
late-third는 .632dB 낮았다. 따라서 이 실험에서는 **전체 count variance와 temporal
entropy만으로 최종 3DGS 품질을 설명할 수 없다.** 평균 이상 interval까지 계속 미세하게
재가중하는 normalized law보다, 심각하게 under-served한 interval에만 correction을 집중하는
exp75 law의 시점별 service 형태가 더 유효했다.

이는 `rho=.5`가 이론적으로 확정됐다는 뜻은 아니다. 반대로 threshold를 제거한 더 단순한
대안이 같은 품질을 내지 못했다는 empirical evidence다. 논문에서는 normalized law를
깔끔한 scale-free ablation으로 사용할 수 있지만, exp75 최고식을 대체하거나 “동일 품질”이라고
주장하면 안 된다.

## 6. 구현·재현

- 구현: `repos/main/3dgs-custom/runtime/scheduler.py`
- CLI: `repos/main/3dgs-custom/train.py --view_scheduler normalized_interval_size_softmax_rr`
- 분석: `analyze_exp76.py`
- 개발 sweep: `run_normalized_softmax_development_s0.sh`,
  `run_normalized_softmax_refine_s0.sh`, `run_normalized_softmax_low_gamma_s0.sh`
- 독립 검증: `run_normalized_softmax_selected_s1.sh`
- machine-readable 결과: `evidence/exp76_summary.json`
- 회귀검사: scheduler test 30개 PASS, py_compile PASS

이 결과는 fixed-pose causal-offline 3dgs-custom ablation이며, RGB+IMU-only strict
VIGS-SLAM 또는 wall-clock budget 결과로 확대해석하지 않는다.
