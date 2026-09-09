# exp74 — Offline fixed-pose full-frame scheduler ablation

## 30k 추가 검증 — 아래 11.88k screening 판정을 정정함 (2026-09-06)

사용자 지적대로 최초 1253 실험의 11,880 update는 기본 densification 종료점 15k에도
도달하지 않아 saturation 판정에 부족했다. 두 장면의 핵심 arm을 표준 30k까지 다시
학습하고, held-out frame을 시간순 전반/중반/후반 3등분했다.

| scene / scheduler | 전체 | 전반 | 중반 | 후반 | count CV | min–max count |
|---|---:|---:|---:|---:|---:|---:|
| 1253 causal RR | **35.202** | **36.077** | **36.136** | 33.377 | 0.317 | 18–73 |
| 1253 count-balanced | 34.883 | 35.414 | 35.771 | **33.455** | **0.018** | 26–27 |
| 1253 static all-at-once RR | **35.301** | 35.930 | 36.015 | **33.946** | ≤0.019 | 26–27 |
| 305 causal RR | **34.541** | **37.256** | **32.804** | 33.563 | 0.580 | 5–44 |
| 305 count-balanced | 33.526 | 34.472 | 31.546 | **34.561** | **0.034** | 12–13 |

30k에서 1253 count-balanced의 causal RR 대비 차이는 전체 −0.319dB지만 후반은
**+0.078dB**다. 305는 전체 −1.015dB지만 후반은 **+0.998dB**다. 11.88/21.78k에서
30k로 늘렸을 때 count-balanced의 전체 개선량은 각각 +4.482/+3.084dB로 causal RR의
+2.982/+1.163dB보다 크다.

따라서 아래의 “raw-count fairness 자체가 NO-GO” 판정은 너무 강했으며 다음처럼 정정한다.

- count-balanced RR는 초기 수렴은 느리지만 충분한 tail에서 후반 frame 품질을 실제로 회복한다.
- 그러나 30k에서도 전·중반 손실 때문에 전체 평균은 causal RR보다 낮아, 아직 일반 RR을
  이겼다고 말할 수 없다.
- 모든 frame을 처음 공개한 static RR가 1253 전체와 후반 모두 가장 높다. Static pool에서는
  count-balanced RR와 ordinary RR가 동일한 uniform-permutation law이므로, scheduler만으로
  static RR를 이긴다는 가설은 여전히 성립하지 않는다.
- 올바른 평가는 `final 30k quality`, `temporal worst-bin`, `quality-vs-update anytime curve`를
  함께 봐야 한다. 단기 screening만으로 final scheduler를 기각해서는 안 된다.

30k machine-readable 결과: [exp74_30k_summary.json](evidence/exp74_30k_summary.json)

## 질문

VIGS-SLAM의 작은 admitted pool 때문에 count-aware scheduler의 이점이 가려졌는가? 모든
training frame을 admission한 큰 pool을 3dgs-custom에서 학습하면 일반 random
reshuffling(RR)을 이길 수 있는가?

## 평가 계약

- SLAM·admission·optimizer를 동시에 바꾸지 않고 **view draw만** 바꾼다.
- RGB, final online VIGS pose, 누적 depth-anchor 초기 PCD, optimizer 설정, 총 update와
  seed는 arm 사이에 고정한다. 이는 scheduler 격리용 offline 실험이며 strict-online 결과가 아니다.
- llffhold-8을 적용해 1253은 1,140 train/163 test, 305는 2,352 train/336 test로 완전 분리한다.
- causal arm은 OpenMAVIS keyframe event에 따라 그 구간까지 도착한 모든 dense frame을 즉시
  공개한다. gate와 admission cap은 없고 마지막에는 모든 train frame이 pool에 포함된다.
- event당 60 update 뒤 동일한 3,000-update tail을 준다. 1253은 11,880, 305는 실제
  21,780 update다(305의 중복 KF boundary 제거 뒤 명목 21,720보다 60회 더 실행).
- 1024 원본을 `-r 4`로 학습한 screening ablation, seed 0이다.

## 방법

1. **Static RR:** 모든 train frame을 처음부터 공개하고 epoch마다 uniform permutation.
2. **Causal RR:** growing pool의 unfinished permutation에 새 frame을 random insertion.
3. **Count-balanced RR:** 현재 최소 lifetime count인 frame들 중 uniform draw. 고정 pool에서는
   exact RR이지만 growing pool에서는 늦게 온 frame이 기존 count를 따라잡는다.
4. **Soft count:** \(p(i)\propto\exp(-\beta n_i)\), \(\beta=0.005,0.01,0.02\).
5. **Floor RR:** causal RR을 기본으로 하되 \(n_i<\alpha\bar n\)인 frame을 우선 서비스,
   \(\alpha=0.25,0.5\).

## 결과

### aria1253

| scheduler | held-out PSNR | Δ vs causal RR | count CV | min–max count | tail block-128 temporal entropy |
|---|---:|---:|---:|---:|---:|
| **causal RR** | **32.220** | — | 0.799 | 2–57 | **0.9786** |
| count-balanced RR | 30.402 | −1.818 | **0.072** | 10–14 | 0.9085 |
| soft, β=.005 | 31.950 | −0.270 | 0.861 | 0–69 | 0.9770 |
| soft, β=.01 | 31.768 | −0.452 | 0.820 | 0–59 | 0.9769 |
| soft, β=.02 | 31.931 | −0.289 | 0.763 | 0–53 | 0.9759 |
| floor RR, α=.25 | 31.855 | −0.365 | 0.619 | 5–48 | 0.9651 |
| floor RR, α=.5 | 31.709 | −0.511 | 0.420 | 6–36 | 0.9552 |
| **static offline RR** | **32.660** | **+0.440** | ≤0.096 | 10–11 | — |

Temporal held-out PSNR quartile은 causal RR이 33.624/34.481/32.096/**28.589**,
count-balanced RR이 28.647/32.761/31.519/**28.636**이었다. 완전 균등화는 마지막 quartile을
0.048dB만 개선하고 첫 quartile을 4.977dB 희생했다.

### aria305 교차 검증

| scheduler | held-out PSNR | Δ | count CV | min–max count | tail entropy |
|---|---:|---:|---:|---:|---:|
| **causal RR** | **33.378** | — | 0.797 | 1–40 | **0.9782** |
| count-balanced RR | 30.443 | **−2.936** | **0.047** | 9–10 | 0.8630 |

305에서도 count equality는 거의 완벽해졌지만 reconstruction은 더 크게 악화했다. 마지막
quartile은 31.369→32.326dB로 좋아진 반면 첫 두 quartile은 35.987/35.742에서
30.669/31.256dB로 무너졌다.

## 판정

**가설 기각.** 큰 full-frame pool은 count-aware scheduler가 RR을 쉽게 이기는 조건이 아니다.

- static pool에서는 count-balanced RR과 ordinary RR의 sampling law가 동일하므로 원리상
  기대 성능 차이를 주장할 수 없다.
- growing pool에서 raw terminal count equality를 강제하면 early frame에 이미 쌓인 유효
  optimization을 무시하고 tail budget을 late cohort의 catch-up에 집중한다. count CV는 크게
  좋아져도 minibatch temporal entropy와 전체 reconstruction이 함께 나빠졌다.
- 이번 두 장면에서는 ordinary causal RR이 모든 count-aware 변형보다 높았다. 따라서 논문의
  main claim을 “RR보다 높은 PSNR을 주는 count fairness”로 두면 안 된다.
- static offline RR가 causal RR보다 +0.440dB인 것은 미래 frame을 처음부터 본 이점이며,
  새로운 scheduler의 승리가 아니다.

다음 방법론은 raw count equality가 아니라 **frame별 marginal utility 또는 residual 감소량당
GPU cost**를 목표로 정의해야 한다. 그 경우 RR은 uniform-objective baseline이고, late-frame
minimum service는 별도 constraint로 두어야 한다.

## 구현·증거

- scheduler: `/home/intern/gs_floaterLab/repos/main/3dgs-custom/runtime/scheduler.py`
- trainer integration: `/home/intern/gs_floaterLab/repos/main/3dgs-custom/train.py`
- dataset builder: `/home/intern/gs_floaterLab/repos/main/3dgs-custom/scripts/incremental/build_vigs_causal_replay_dataset.py`
- unit contracts: `/home/intern/gs_floaterLab/repos/main/3dgs-custom/tests/test_view_scheduler.py`
- aggregate: [exp74_summary.json](evidence/exp74_summary.json)
- analysis: [analyze_exp74.py](analyze_exp74.py)

검증은 `py_compile`, scheduler 4개 self-test, 10-step GPU smoke test를 통과했다. `pytest`는
3dgs 환경에 설치되어 있지 않아 동일 test 함수를 직접 실행했다.
