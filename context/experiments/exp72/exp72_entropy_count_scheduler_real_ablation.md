# exp72 — ERCB statistical-block scheduler 실제 final-v7 A/B

- 날짜: 2026-09-04
- 유형: final-v7 scheduler-only implementation + real 3DGS ablation
- 상태: **품질 보존 후보 (K=128,\beta=0.02) 확인 / 공동 방법론으로는 NO-GO**

## 질문

exp71의 entropy-regularized count balancing(ERCB)

\[
p(i\mid\mathcal R)\propto \exp(-\beta n_i)
\]

을 실제 final-v7에 이식했을 때 다음을 동시에 얻을 수 있는가?

1. 기존 held-out 품질과 1× online wall time을 훼손하지 않는다.
2. 초기 cohort와 stream 중간 cohort의 최종 lifetime count를 비슷하게 만든다.
3. uniform shuffle에 가까운 높은 conditional entropy를 유지한다.
4. 기존 maturity gate가 있는 상태에서도 admission이 pool 크기와 무관하게 진행된다.

## 구현

실제 변경은 replay view draw에만 opt-in으로 적용했다. Admission, mapping loss,
optimizer, PGBA, Gaussian budget, terminal dust-GC/rematuration, RTX 5090 1× profile은
final-v7 control과 동일하다. 기본값 `beta=-1`에서는 기존 active/archive queue가 그대로
실행된다.

ERCB의 logical statistical block 크기를 (K)라 하고, block 시작 시 현재 pool에서
순차적으로

\[
p_{\beta}(i\mid\mathcal R)
=\frac{\exp(-\beta n_i)}
{\sum_{j\in\mathcal R}\exp(-\beta n_j)}
\]

로 (K)개를 비복원 추출한 뒤 물리적 B1 optimizer update로 하나씩 소비한다.
(K=1)은 매 update의 categorical sampling, (K\ge N)은 full-pool weighted
permutation이다. Active-aware 대조군은 기존 bounded demand를 보존해

\[
w_i=(1+D)^{\mathbf1[i\in A]}\exp(-\beta n_i)
\]

를 사용했다.

구현 경로(저장소 기준):

- `vigs/map_scheduler.py`: ERCB queue와 entropy/count telemetry
- `vigs/gs_backend.py`: opt-in queue 생성과 cohort 통계 연결
- `demo.py`: CLI 인자, 조합 검증, 실행 manifest
- `exp69_axes/run_decoupled_geometry.sh`: 환경변수에서 CLI로 전달
- `exp70_axes/run_v7_1x_no_legacy_carve.sh`: 동일 final-v7 1× control wrapper
- `exp72_axes/run_scheduler_ablation.sh`: arm 정의
- `exp72_axes/test_entropy_count_scheduler.py`: 분포·비복원·arrival·회귀 test

5090 검증 원본의 저장소 root는
`/home/intern/VIGS-SLAM-main-integration-20260828`이며, GitHub에는
`exp72-entropy-count-scheduler` 브랜치로 보존한다.

## 중요한 구현 감사

첫 구현은 `remaining`을 full-pool epoch 전체에 유지했다. 이 경우 모든 view가 결국 한 번씩
선택되므로 \(\beta\)는 lifetime exposure가 아니라 epoch 내부 순서만 바꾼다. aria1253rot
교차검증에서 이 문제가 드러나 해당 결과를 무효화했다. 최종 구현은 exp71 simulator와
동일하게 `remaining`을 statistical block마다 초기화한다. 최종 CSV/JSON은 이 수정 뒤의
run만 포함한다.

분포식, B1 반복 가능성, block 내 비복원성, arrival 경계, active multiplier, work-credit
interface와 기존 scheduler 회귀를 포함한 **60 tests**가 통과했다.

## 실행 조건

- final-v7 RTX 5090 original timestamp 1× profile
- legacy carve flag off, detached opacity off
- terminal dust-GC와 EOS pose rematuration 유지
- seed 0
- scene: `aria1253`, `aria1253rot`
- baseline aria1253 2회, rot 1회
- sweep: B1 \(\beta=0,0.006,0.02,0.05\),
  \(K=32/128,\beta=0.02\), rot에서 \(K=128,\beta=0.05\)와 active-aware 변형

이 평가는 EOS rematuration을 포함하는 final-map 비교이며 strict zero-tail 주장이 아니다.

## 결과

### aria1253 sweep

Baseline PSNR은 2회 평균 27.708 dB였다.

| Scheduler | PSNR | baseline 대비 | entropy ratio | middle/first | pool |
|---|---:|---:|---:|---:|---:|
| final-v7 active/archive baseline | 27.708 | — | — | 1.098* | 422.5 |
| B1, \(\beta=0\) | 24.845 | −2.863 | 1.0000 | 0.948 | 281 |
| B1, \(\beta=0.006\) | 27.218 | −0.490 | 0.9998 | 0.977 | 269 |
| B1, \(\beta=0.02\) | 27.457 | −0.251 | 0.9983 | 0.993 | 340 |
| B1, \(\beta=0.05\) | 26.598 | −1.110 | 0.9887 | 0.840 | 291 |
| \(K=32,\beta=0.02\) | 25.626 | −2.082 | 0.9975 | 0.977 | 265 |
| **\(K=128,\beta=0.02\)** | **27.624** | **−0.084** | **0.9987** | **0.971** | **333** |

`*` baseline의 cohort telemetry는 계측 추가 뒤 repeat 한 회 값이다.

### 교차 trajectory

| Scheduler | Scene | PSNR | baseline 대비 | entropy ratio | middle/first |
|---|---|---:|---:|---:|---:|
| active/archive baseline | aria1253rot | 24.814 | — | — | 0.758 |
| **\(K=128,\beta=0.02\)** | aria1253rot | **25.177** | **+0.362** | **0.9984** | **0.520** |
| \(K=128,\beta=0.05\) | aria1253rot | 24.906 | +0.092 | 0.9920 | 0.579 |
| \(K=128,\beta=0.05\)+active | aria1253rot | 24.941 | +0.126 | 0.9825 | 0.605 |

선정 후보 (K=128,\beta=0.02)의 online wall은 aria1253
65.133초(baseline 평균 65.112초), rot 74.871초(baseline 74.860초)로 차이가 없었다.
마지막 block에서 가장 많이/적게 학습된 view의 상대 weight 범위도
aria1253 0.517–1.000, rot 0.571–1.000이어서 \(\beta\)가 사실상 0인 분포는 아니다.

## 해석

### 확인된 것

- **품질 보존 engineering candidate:** (K=128,\beta=0.02)는 두 trajectory 모두
  −0.2 dB 기준을 통과했고, conditional entropy도 uniform maximum의 99.84% 이상이었다.
- B1 IID uniform의 −2.86 dB와 (K=32)의 −2.08 dB는 실제 3DGS에서 장기간의
  without-replacement coverage가 중요하다는 직접 증거다.
- aria1253에서는 middle/first가 0.971로 매우 균등했다.

### 해결되지 않은 것

- rot에서는 선정 후보의 middle/first가 0.520으로 baseline 0.758보다 나빴다.
  더 큰 \(\beta\)와 active bonus는 0.605까지만 회복했고 entropy가 0.9825로 내려갔다.
  따라서 이 family가 **일반적으로 lifetime-count equality를 개선한다는 주장은 기각**한다.
- 최종 pool은 aria1253 baseline 평균 422.5 대 후보 333, rot 353 대 334였다.
  기존 `minimum count >= 2` maturity gate를 유지했기 때문에 scheduler가 gate 개방 시점과
  admission 수를 바꾸었다. **pool-size-independent admission은 달성하지 못했다.**
- raw lifetime equality, high entropy, full-pool coverage, growing admission을 모두 동시에
  요구하는 exp71의 incompatibility는 실제 A/B에서도 해소되지 않았다.

## 판정

- **opt-in 구현 유지:** (K=128,\beta=0.02)는 품질 무손실 scheduler ablation으로 재사용.
- **production default 교체 보류:** 두 조건(일반 lifetime equality, pool-independent
  admission)을 만족하지 못했으므로 final-v7 기본 queue를 바꾸지 않는다.
- **논문 방법론 채택 NO-GO:** “적절한 \(\beta\) 하나로 세 조건을 해결했다”는 주장을 하지 않는다.
- 다음 방법론 단계에서는 scheduler를 더 sweep하기 전에 admission gate를 GPU-token
  controller로 분리하고, fairness target을 raw lifetime equality와 age-adjusted equality 중
  하나로 명시적으로 선택해야 한다.

## 재현

```bash
cd /home/intern/VIGS-SLAM-main-integration-20260828
bash exp72_axes/run_scheduler_ablation.sh \
  aria1253 exp72_axes/results/repro_block128_beta002 \
  block128_beta002

/home/colin/miniconda3/envs/vigs-slam-5090/bin/python \
  exp72_axes/summarize_scheduler_ablation.py
```

Machine-readable 결과:

- `exp72_axes/results/exp72_scheduler_ablation_runs.csv`
- `exp72_axes/results/exp72_scheduler_ablation_summary.json`

원본 full-run 디렉터리와 launch log는 용량 때문에 5090의
`/home/intern/VIGS-SLAM-main-integration-20260828/exp72_axes/results/`에 유지하며,
GitHub에는 위 집계 CSV/JSON만 올린다.
