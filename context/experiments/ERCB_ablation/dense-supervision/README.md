# dense-supervision — KF-only vs KF+dense supervision (online incremental)

> 날짜: 2026-09-17
> 목적: 논문 문장 *"When the frames between keyframes are used as supervision as well,
> the map converges faster under the same number of iterations (Table X)"* 를 뒷받침하는 표.
> 배치에서만 관측되던 효과(exp66)를 causal/incremental 조건에서 재현한다.

## 계약

benchmark-B에서 그대로 상속: stride20 dataset/init point cloud, causal arrival schedule,
`causal_rr` selector, seed 0, `-r 4`, RGB-only loss, llffhold-8 held-out(두 arm 모두 미학습),
zero-tail, 그리고 **scene·budget별 총 optimizer update 수**.

benchmark-B와 다른 것은 **densification을 켠 것 하나**뿐이며, 그 스케줄은 각 run 자기 예산의
고정 비율(시작 1/60, 종료 1/2, opacity reset 1/10)로 장면 무관하게 통일했다.

축은 **keyframe interval당 할당 iteration**이다(online incremental이 실제로 겪는 조건).
총 iteration은 궤적 길이의 결과이지 조절 대상이 아니다.

| arm | 후보 pool |
|---|---|
| `kf_only` | VIGS keyframe만 |
| `kf_dense` | 도착한 모든 train frame (keyframe 포함) |
| `k{K}` | interval당 keyframe + 중간 frame `K-1`장 (keyframe 시드 farthest-point-in-time) |

## 최종 결과 — keyframe당 120 iteration, 19 scene (논문 Table A, `TABLES.tex`)

| Metric | Policy | RPNG (8) | UTMM (7) | Aria (4) | All (19) |
|---|---|---:|---:|---:|---:|
| PSNR ↑ | Keyframes only | 23.71 | 21.18 | 29.43 | 23.98 |
| | **+ in-between frames** | **24.16** | **22.85** | **30.89** | **25.09** |
| SSIM ↑ | Keyframes only | 0.7928 | 0.7352 | 0.8867 | 0.7913 |
| | **+ in-between frames** | **0.8085** | **0.7786** | **0.9019** | **0.8171** |
| LPIPS ↓ | Keyframes only | 0.1656 | 0.2676 | 0.2064 | 0.2118 |
| | **+ in-between frames** | **0.1567** | **0.2476** | **0.2014** | **0.1996** |
| final #G | Keyframes only | 685,209 | 316,407 | 333,327 | 475,254 |
| | + in-between frames | 710,420 | 304,566 | 354,106 | 485,881 |

Scene별 Δ는 **18/19 양수, 평균 +1.11dB**다(Aria +1.46 4/4, UTMM +1.67 7/7,
RPNG +0.45 7/8). 유일한 음수는 `table_07` **−0.11**로, 프로젝트 run-to-run 분산
±0.33dB 안쪽이라 단일 seed로는 부호를 확정할 수 없다. UTMM은 Gaussian을 더 적게
쓰고도(316,407 → 304,566) 이긴다.

Table B(view ordering, benchmark-B의 RR vs ERCB)는 예산을 열로 놓아 승자가 예산에
따라 달라지는 것을 보인다: PSNR은 15/30/60 updates/interval에서 RR `20.77/22.22/22.88`
대 ERCB `21.39/22.33/23.11`이다. SSIM/LPIPS는 미계산이다.

## 수렴 곡선 — keyframe당 60 iteration

동일한 38개 run을 24개 checkpoint로 다시 측정했다. KF+dense는 19/19 scene에서
KF-only의 최종 PSNR에 더 적은 optimizer iteration으로 한 번 이상 도달했고, 선형 보간한
iteration 절감률의 중앙값은 **21.4%**다. 이는 실제 wall-clock 가속이 아니라 동일
optimizer-iteration 축의 crossing이며, 일부 곡선은 이후 다시 하락한다. 실제로 event60
최종값은 위 `TABLE_X.md`와 같이 15/19만 양수이므로, early crossing을 endpoint 우위나
단조 수렴으로 해석하지 않는다.

- [대표 6 scene 수렴 곡선](figure_convergence.pdf): family별 final Δ 중앙 장면과 최저 장면
- [전체 실행 manifest](evidence/manifest_curve.json): 38/38 완료, 동일 seed·arrival·총 update
- 재생성: `python plot_convergence.py`

## 참고 — keyframe당 60 iteration, 19 scene (`TABLE_X.md`)

전체 **+0.33dB, 15/19 승**. family별로 갈린다.

| family | 평균 Δ | 승률 |
|---|---:|---:|
| Aria | +0.75 | 4/4 |
| UTMM | +0.87 | 7/7 |
| RPNG | −0.34 | 4/8 |

Aria+UTMM 11장면은 **11/11 양수(평균 +0.82dB)**. RPNG의 table_03/04/05/06만 음수다.

## 결과 2 — RPNG 역전의 원인은 예산 부족 (dense frame 품질이 아님)

keyframe당 iteration만 60→120으로 올리자 부호가 뒤집힌다. 장면·pool·seed 모두 동일하다.

| scene | keyframe당 60 | keyframe당 120 |
|---|---:|---:|
| rpng/table_06 | KF 26.01 / dense 25.26 → **−0.74** | KF 26.20 / dense 26.42 → **+0.22** |
| rpng/table_01 | (budget 15) **−1.17** → (30) +0.29 → (60) +0.28 | **+0.53** |
| aria/aria1253 | +0.03 | **+1.70** (240에서 +2.33) |
| utmm/square-1 | +1.05 | **+1.76** (240에서 +2.77) |

진 장면들은 keyframe당 60회 기준 dense arm의 **frame당 update가 3.6~5.6회**뿐이었다
(table_05 3.6, table_03 5.0, table_06 5.6). 프레임 수가 많은 장면일수록 같은 예산을 더 많은
view가 나눠 가져 학습이 임계 아래로 떨어진다.

## 결과 3 — 밀도를 줄이면 저예산에서도 회복된다

전부 넣는 대신 interval당 `K`장만 admit하면 같은 예산에서 부호가 바뀐다.

| rpng/table_03 (keyframe당 60) | K=1 | K=2 | **K=4** | K=8 | K=all |
|---|---:|---:|---:|---:|---:|
| Δ vs K=1 | — | +0.12 | **+0.19** | −0.16 | −0.72 |

단 **최적 K는 데이터셋마다 반대 방향**이다. UTMM/Aria는 K가 클수록 좋아 `K=all`이 최적인
반면(ego-centric-2: K=4 +0.07 vs K=all +1.72), RPNG 대형 장면은 중간 K가 최적이다.
따라서 전 장면 공통 고정 K 하나로는 두 쪽을 동시에 만족시키지 못한다.

## 기각된 가설

- **"dense frame당 update 임계"**: 기각. slow-straight-2는 1.7회인데 +0.48, table_05는
  3.6회인데 −2.08이라 단조 관계가 아니다.
- **"데이터셋으로 갈린다"**: 부분 기각. RPNG 안에서도 table_01/02/07/08은 양수다.
- **"중간 frame이 흐려서"**: 약한 상관만 있다(Pearson r=0.298). 다만 keyframe 대비 선명도
  비가 0.95 이상인 12장면은 **12/12 전부 양수(+0.79dB)**, 0.95 미만 7장면(전부 RPNG)은
  3/7이다. 예산 상향으로 table_06이 뒤집힌 것을 보면 블러는 주원인이 아니다.

## 해석 제한

- pose와 초기 point cloud는 사전 VIGS run의 고정 replay다. strict online localization
  결과가 아니며 도착 순서와 zero-tail만 유지된다.
- 단일 seed다. 이 프로젝트의 run-to-run PSNR 분산은 과거 ±0.33dB로 실측됐다.
- held-out이 llffhold-8이라 held-out frame이 중간 frame과 시간적으로 인접하다. 두 arm이
  동일 held-out을 쓰지만 이 인접성은 KF+dense에 유리할 수 있다.

## 재현

```bash
DS_BUDGETS=60 python prepare_manifest.py --all   # 19 scene x 2 arm
python run_panel.py
python summarize_headline.py                     # -> TABLE_X.md

python prepare_manifest_curve.py                 # event60, 24 checkpoints
python run_panel_curve.py
python plot_convergence.py                       # -> figure_convergence.pdf/png

K_SCENES="rpng/table_03" K_BUDGETS=60 python build_k_pools.py 2 4 8   # 밀도 스윕
B_SCENES="rpng/table_06" B_BUDGETS=120 python prepare_manifest_budget.py  # 예산 스윕
```
