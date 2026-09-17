# Table X — per-interval view density K vs streaming budget

논문 §3.1의 두 전제를 **incremental 조건에서** 세우기 위한 표다. 현재 claim ledger는
A2/A3의 근거로 배치 실험(exp51/exp66)만 인용하고 있다.

- **A2 (P1)**: keyframe 사이 frame이 쓸 수 있는 supervision이다 → 각 budget에서 최적
  `K>1`이 `K=1`(keyframe-only)을 이겨야 한다.
- **A3 (P2)**: 최적 view-set 밀도가 compute budget에 따라 움직인다 → `K*`가 budget에
  따라 이동해야 한다.

`K` = interval당 pool 크기. VIGS keyframe 1장 + 그 interval의 중간 frame `K-1`장
(keyframe을 시드로 한 farthest-point-in-time 선택). `K=1`은 keyframe-only,
`K=all`은 도착한 모든 frame.

## 계약

benchmark-B에서 그대로 상속: stride20 dataset/init, causal arrival schedule,
event당 update 예산(15/30/60), `causal_rr`, seed 0, `-r 4`, RGB-only loss,
llffhold-8 held-out, zero-tail, scene·budget별 총 update 수.
**benchmark-B와 다른 것은 densification을 켠 것 하나뿐**이며 그 스케줄은 각 run 자기
예산의 고정 비율(1/60에서 시작, 1/2까지, opacity reset 1/10)로 장면 무관하게 통일했다.

## 결과 — held-out PSNR (dB)

| scene | budget (upd/interval) | K=1 | K=2 | K=4 | K=8 | K=all | K* | best−K1 |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| aria/aria1253 | 15 | 24.49 | **24.58** | 24.26 | 23.28 | 24.54 | **2** | +0.09 |
| aria/aria1253 | 30 | 26.10 | 26.39 | 26.35 | **26.40** | 25.63 | **8** | +0.29 |
| aria/aria1253 | 60 | 27.75 | 27.78 | 28.53 | **28.57** | 27.78 | **8** | +0.82 |
| rpng/table_01 | 15 | 22.89 | **22.92** | 22.85 | 21.74 | 21.73 | **2** | +0.02 |
| rpng/table_01 | 30 | 23.25 | 23.21 | 23.35 | 23.11 | **23.54** | **all** | +0.29 |
| rpng/table_01 | 60 | 23.66 | 23.36 | 23.45 | — | **23.94** | **all** | +0.28 |
| utmm/square-1 | 15 | 17.86 | 17.89 | 17.76 | 17.78 | **18.00** | **all** | +0.13 |
| utmm/square-1 | 30 | 18.99 | 19.12 | 19.14 | 19.07 | **19.28** | **all** | +0.29 |
| utmm/square-1 | 60 | 20.44 | 20.62 | 20.79 | 20.92 | **21.48** | **all** | +1.05 |

평균 이득(최적 K − K=1): budget 15: +0.08dB (3/3) · budget 30: +0.29dB (3/3) · budget 60: +0.71dB (3/3)

### K* 이동 (A3)

- aria/aria1253: budget15 K*=2 → budget30 K*=8 → budget60 K*=8
- rpng/table_01: budget15 K*=2 → budget30 K*=all → budget60 K*=all
- utmm/square-1: budget15 K*=all → budget30 K*=all → budget60 K*=all

## 왜 최적점이 생기는가 — view당 update 수

같은 예산을 더 많은 view가 나눠 가지므로 K가 커질수록 view당 서비스가 줄어든다.

| scene | budget | K=1 | K=2 | K=4 | K=8 | K=all |
|---|---|---:|---:|---:|---:|---:|
| aria/aria1253 | 15 | 15.9 | 7.4 | 3.8 | 2.1 | 1.6 |
| aria/aria1253 | 30 | 31.8 | 14.9 | 7.5 | 4.1 | 3.2 |
| aria/aria1253 | 60 | 63.7 | 29.8 | 15.0 | 8.2 | 6.4 |
| rpng/table_01 | 15 | 17.1 | 7.5 | 3.8 | 2.1 | 1.6 |
| rpng/table_01 | 30 | 34.1 | 14.9 | 7.5 | 4.2 | 3.3 |
| rpng/table_01 | 60 | 68.2 | 29.9 | 15.0 | — | 6.6 |
| utmm/square-1 | 15 | 16.5 | 7.4 | 3.7 | 1.9 | 0.8 |
| utmm/square-1 | 30 | 32.9 | 14.8 | 7.4 | 3.8 | 1.7 |
| utmm/square-1 | 60 | 65.8 | 29.6 | 14.9 | 7.6 | 3.4 |

## 해석 제한

- pose/init은 사전 VIGS run의 고정 replay다. strict online localization 근거가 아니다.
- densification이 켜져 있어 arm별 최종 Gaussian 수가 다르다.
- held-out이 llffhold-8이라 held-out frame이 중간 frame과 시간적으로 인접하다. 모든
  arm이 동일 held-out을 쓰지만 이 인접성은 큰 K에 유리할 수 있다.
- 단일 seed다. 이 프로젝트의 run-to-run PSNR 분산은 과거 ±0.33dB로 실측된 바 있다.
