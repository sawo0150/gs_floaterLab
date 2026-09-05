# exp73 — Gate-free token-only admission 실제 장면 검증

## 질문

exp69 final-v7의 admission은 admitted view 전체의 최소 lifetime count가 2 이상일 때만
다음 view를 받는다. Growing pool에서 revisit 주기가 길어지면 한 straggler가 전체
admission을 막는다. 이 global barrier를 없애고 다음처럼 GPU work만으로 pool 증가를
결정할 수 있는가?

\[
A_{\mathrm{paid}}(u)=\left\lfloor\frac{u}{\kappa}\right\rfloor,
\]

여기서 \(u\)는 완료된 dense Adam update 수, \(\kappa\)는 새 view 한 장의 가격이다.

## 구현

- 최초 전역 seed view 한 장만 무료 admission한다.
- 이후에는 완료된 dense update \(\kappa\)회마다 현재까지 도착한 pending view 한 장을
  admission한다.
- view별 최소 선택 횟수, epoch 완료, active/archive 크기는 admission 조건에 쓰지 않는다.
- 미래 view에 token을 선지급하지 않고, 현재 도착한 causal candidate만 admission한다.
- 비교를 분리하기 위해 replay scheduler는 final-v7 active/archive 그대로 유지했다.
- 새 mode는 opt-in이며 production default는 바꾸지 않았다.

## 해석 범위: 순수 gate-removal ablation은 아님

- exp73은 기존 admission에서 maturity gate 조건만 뺀 실험이 아니다.
- 기존 final-v7은 각 keyframe interval에서 한 장을 무료 bootstrap하고, 추가 view만
  maturity-gated credit으로 admission한다.
- exp73은 interval별 bootstrap을 없애고, 최초 전역 seed 한 장을 제외한 모든 신규 view를
  \(\kappa\)-token으로 지불하는 **token-only 정책 교체**다.

$$
A_{\mathrm{old}}
=A_{\mathrm{interval\text{-}bootstrap}}+A_{\mathrm{gate\text{-}credit}},
\qquad
A_{\mathrm{exp73}}=1+\left\lfloor\frac{u}{\kappa}\right\rfloor.
$$

- 1253 baseline 두 run은 각각 \(217+194=411\), \(217+217=434\)장이었다.
  exp73 \(\kappa=22\)는 \(1+274=275\), \(1+275=276\)장이었다.
  유상 admission은 늘었지만 무료 bootstrap 217장이 1장으로 줄어든 효과가 더 커서
  전체 pool이 감소했다.
- 305에서는 \(312+362=674\rightarrow1+748=749\)로 오히려 pool이 증가했다.
- 따라서 pool 증감은 “gate 제거 효과”가 아니라 **interval bootstrap 제거와 token pacing이
  결합된 정책 교체 효과**다. Gate 자체의 효과를 분리하려면 interval bootstrap을 유지한
  gate-free arm이 별도로 필요하다.

실제 구현 경로:

- `/home/intern/VIGS-SLAM-main-integration-20260828/vigs/map_scheduler.py`
- `/home/intern/VIGS-SLAM-main-integration-20260828/vigs/vigs.py`
- `/home/intern/VIGS-SLAM-main-integration-20260828/vigs/gs_backend.py`
- `/home/intern/VIGS-SLAM-main-integration-20260828/demo.py`
- runner: `/home/intern/VIGS-SLAM-main-integration-20260828/exp73_axes/run_gate_free_token_admission.sh`

## 계약 검증

두 장면 7개 gate-free run의 admission poll 526개를 전부 검사했다. 모든 poll에서

\[
A_{\mathrm{paid}}(u)-\left\lfloor u/\kappa\right\rfloor=0
\]

으로 maximum integer error가 0이었다. 따라서 pool이 작거나 커지는 것과 무관하게
**실제로 완료된 GPU work에 대한 admission slope는 정확히 \(1/\kappa\)**다.

단, admission은 mapping packet에서 polling하므로 마지막 packet 뒤에 생긴 token은
새 view를 EOS에서 뒤늦게 넣지 않는다. 이는 학습 기회가 없는 view를 final pool에만
추가하지 않기 위한 causal 실행 정책이다.

## 실행 조건

- RTX 5090, original timestamp 1×, seed 0
- final-v7 clean control, legacy carve off
- terminal dust-GC와 EOS pose rematuration 유지
- strict zero-tail 실험이 아니라 final-map scheduler/admission A/B
- 기존 exp72 fresh baseline을 재사용; 새 mode가 opt-in이라 baseline 경로는 불변

## aria1253 sweep

Baseline은 두 fresh run 평균 PSNR 27.708 dB, pool 422.5장이다.

| mode | PSNR | baseline 대비 | pool | streaming update | selection CV | middle/first |
|---|---:|---:|---:|---:|---:|---:|
| maturity-gate baseline | 27.708 | — | 422.5 | 5,821 평균 | 0.373 | 1.098* |
| gate-free, \(\kappa=8\) | 25.668 | −2.040 | 604 | 5,092 | 0.999 | 0.737 |
| **gate-free, \(\kappa=12\)** | **27.644** | **−0.064** | **469** | **5,716** | **0.895** | **0.710** |
| gate-free, \(\kappa=16\) | 22.163 | −5.545 | 359 | 6,034 | 1.032 | 0.542 |
| gate-free, \(\kappa=22\), repeat 0 | 27.750 | +0.042 | 275 | 6,319 | 0.940 | 0.645 |
| gate-free, \(\kappa=22\), repeat 1 | 27.672 | −0.036 | 276 | 6,338 | 0.962 | 0.665 |
| **gate-free, \(\kappa=22\), 평균** | **27.711** | **+0.003** | **275.5** | **6,328.5** | **0.951** | **0.655** |

`*` baseline cohort telemetry가 있는 repeat 한 회 값이다.

추가 요청으로 실행한 \(\kappa=22\)는 두 번 모두 −0.2 dB 품질 보존 기준을 통과했고,
평균은 baseline과 +0.003 dB로 사실상 같았다. 동시에 pool은 422.5→275.5장(−34.8%)으로
줄었다. 이 감소는 gate 제거 때문이 아니라 위에서 설명한 interval별 무료 bootstrap 제거
때문이다. 반면 중간값인 \(\kappa=16\)은 22.163 dB로 무너졌다. 따라서 실제 online 3DGS의
품질은 admission density에 대해 단조롭지 않으며, topology·PGBA·비동기 replay 분기가
결과에 강하게 결합한다. \(\kappa=22\) 반복 재현은 이 값이 단일 우연은 아님을 보여주지만,
\(\kappa=16\) 이상치를 설명한 것은 아니다.

## 305호 transfer와 진단

305호 baseline은 PSNR 28.934 dB, pool 674장이다.

| mode | PSNR | baseline 대비 | pool | streaming update | selection CV | middle/first |
|---|---:|---:|---:|---:|---:|---:|
| maturity-gate baseline | 28.934 | — | 674 | 14,246 | 0.470 | 0.774 |
| gate-free, \(\kappa=12\) | 27.388 | **−1.546** | 1,215 | 14,677 | 1.002 | 0.552 |
| gate-free, \(\kappa=22\) | 28.815 | **−0.119** | 749 | 16,593 | 0.942 | 0.449 |

1253에서 선택한 \(\kappa=12\)를 재튜닝 없이 옮기면 실패했다. 305호는 같은 wall time 동안
더 많은 dense work를 완료하므로 1,215장을 admission했고, view당 실효 학습량이 부족했다.
baseline pool 규모에서 역산한 진단점 \(\kappa\approx22\)는 pool 749장에서 품질을
−0.119 dB까지 회복했다.

\(\kappa=22\)는 처음에는 305호 baseline pool을 보고 정한 진단값이지만, 이후 같은 값을
1253에 역전이하여 2회 모두 품질 기준을 통과했다. 따라서 현재 두 장면에서는 **재튜닝 없이
공유 가능한 첫 token-cost engineering candidate**다. 다만 선택 과정이 305 baseline을
참조했고 검증 장면이 2개뿐이므로 scene-general optimum이나 이론적 universal constant라고
주장할 수는 없다.

## 결론

1. **Token-only GPU-work-proportional admission에는 maturity gate가 필요하지 않다.** Gate
   없이도 \(A_{\mathrm{paid}}(u)=\lfloor u/\kappa\rfloor\)를 실제 실행에서 정확히 만족했다.
   다만 exp73은 interval bootstrap도 함께 제거했으므로 gate 하나의 효과를 분리한
   ablation은 아니다.
2. **\(\kappa=22\)는 현재 두 장면의 첫 공통 후보다.** 1253 2회 평균은 baseline 대비
   +0.003 dB, 305는 −0.119 dB로 모두 −0.2 dB 기준을 통과했다. 반면 \(\kappa=12\)는
   305에서 −1.546 dB로 실패했으므로 모든 token price가 호환되는 것은 아니다.
3. **Token-only admission만으로 최종 학습 균등성은 좋아지지 않았다.** 선택 scheduler를 그대로 둔
   결과 공통 \(\kappa=22\)의 selection CV는 1253 0.373→0.951, 305
   0.470→0.942로 악화했다.
4. 따라서 admission과 scheduling을 분리한다는 방향은 맞고, \(\kappa=22\)는 다음 공동
   A/B의 기본 admission 후보로 올린다. 그러나 final count 균등성이 악화했고 검증 장면도
   2개뿐이므로 production default 채택은 아니다. 다음 문제는 gate-free arrival에서
   early/middle cohort count와 shuffle entropy를 함께 맞추는 scheduler다.

## 재현

```bash
cd /home/intern/VIGS-SLAM-main-integration-20260828
bash exp73_axes/run_gate_free_token_admission.sh aria1253 \
  exp73_axes/results/k12_aria1253_seed0 k12
bash exp73_axes/run_gate_free_token_admission.sh aria1253 \
  exp73_axes/results/k22_aria1253_seed0 k22
bash exp73_axes/run_gate_free_token_admission.sh aria1253 \
  exp73_axes/results/k22_repeat_aria1253_seed0 k22
bash exp73_axes/run_gate_free_token_admission.sh aria301_305 \
  exp73_axes/results/k12_aria301_305_seed0 k12
bash exp73_axes/run_gate_free_token_admission.sh aria301_305 \
  exp73_axes/results/k22_aria301_305_seed0 k22
python exp73_axes/summarize_gate_free_token_admission.py
```

회귀 검증은 view scheduler 55개와 exp72 entropy scheduler 9개, 총 64 tests를 통과했고
관련 Python compile 및 shell syntax 검사도 통과했다.

Machine-readable evidence:
[`evidence/exp73_gate_free_token_admission_summary.json`](evidence/exp73_gate_free_token_admission_summary.json)
