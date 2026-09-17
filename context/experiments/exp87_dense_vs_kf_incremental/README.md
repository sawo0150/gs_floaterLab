# exp87 — incremental KF-only vs KF+dense supervision (논문 표)

> 날짜: 2026-09-17
> 상태: 실행 중
> 목적: 배치에서 이미 관측된 "dense supervision이 keyframe-only보다 빠르게 수렴한다"를
> **causal/incremental 조건에서 재현**하고, 논문에 실을 수렴-속도 표를 만든다.

## 배경 — 왜 기존 incremental 실험에서는 이 효과가 안 보였나

배치 근거는 exp66(aria1253, offline `color_refinement`, 26,000 iteration):
`dense_geom 31.68 > W1 31.00 > W2 30.66 > W3 30.18 > mixed 30.03 > keyframe 28.38dB`,
그리고 "격차가 학습 초반부터 곡선 전체에서" 벌어진다. 조건은 **dense frame에 keyframe과
동일한 geometry 편집 권한**을 준 경우였다.

ERCB ablation 하네스(benchmark-A/B)에서 같은 비교를 했을 때는 효과가 안 보이거나
역전됐는데, 2026-09-17 감사에서 원인이 규명됐다. 전부 실측 확인:

| 축 | benchmark-A/B | exp66 (효과 관측) |
|---|---|---|
| densification | **완전 OFF** (`--fixed_topology_step_before_report`가 `densify_until_iter=0`을 강제, train.py:82-83) | Phase 1 densify 완료 맵 |
| Gaussian 수 | init 개수에 **영구 고정** (31,185 / 100,157 / 54,373 — init과 정확히 일치) | 149K–290K |
| init 외형 | 균일 회색 `[128,128,128]`, 색 정보 0 | 학습된 맵(21.6–22.5dB에서 시작) |
| view당 update | **0.84–6.6회** | ~23회 |
| 종료 시점 곡선 | 마지막 구간에서 아직 +4~5dB 상승 중 | 수렴 후반 |
| 최종 PSNR | 17.6–27.0 | 28.4–31.7 |

추가로 저예산 dense arm은 view의 **28–40%를 한 번도 뽑지 않았다**(square-1 e15: RR 28.2%,
ERCB 40.2%) — "dense supervision"이 아니라 "랜덤 부분집합 1회씩"이었다. 결정적으로
**aria1253은 exp66과 동일 장면인데** 우리 7,321 iter에서는 kf 27.49 > dense 27.00,
exp66 26,000 iter에서는 dense 31.68 > keyframe 28.38으로 **예산/용량만 다른데 부호가
반대**였다. Pose 보간 오차는 0.000000s로 pose는 원인이 아니다.

즉 기존 하네스는 *scheduler만 격리*하려고 densify를 끈 설계였고, 그 조건은
dense supervision의 가치를 측정하기에 구조적으로 부적합했다.

## 계약

- 두 arm이 공유: dataset, init point cloud, causal arrival schedule, `causal_rr` selector,
  seed 0, `-r 4`, RGB-only loss, 표준 3DGS densification(500–15,000, interval 100,
  opacity reset 3,000), 총 optimizer update 수, llffhold-8 held-out(두 arm 모두 미학습)
- 다른 것: **후보 pool 하나뿐** — `kf_only`(VIGS keyframe만) vs `dense_all`(도착한 모든 train frame)
- causality 유지: frame은 자기 keyframe interval의 event 시각에만 열리고, 마지막 frame
  도착 뒤 추가 update 없음(zero-tail)
- 예산: per-event budget을 장면별로 스케일해 총 update ≈ 30,000 (표준 3DGS 길이)

| scene | events | budget/event | total | train frames | keyframes | upd/frame | upd/kf |
|---|---:|---:|---:|---:|---:|---:|---:|
| aria/aria1253 | 123 | 246 | 30,013 | 1,140 | 115 | 26.3 | 261.0 |
| utmm/square-1 | 80 | 380 | 30,021 | 1,412 | 72 | 21.3 | 417.0 |
| rpng/table_01 | 242 | 124 | 29,885 | 2,192 | 212 | 13.6 | 141.0 |

## 측정

수렴 **속도**가 주장이므로 endpoint가 아니라 곡선 전체를 측정한다 —
held-out PSNR을 1k/2k/3k/5k/7k/10k/15k/20k/25k/최종에서 기록하고, 최종 Gaussian 수를
모든 수치 옆에 함께 싣는다.

## 알려진 confound / 주장하지 않는 것

- densify가 켜져 있으므로 arm 간 최종 Gaussian 수가 다르다. "dense가 Gaussian을 더 많이
  만들어서 이긴 것"이라는 반론을 닫으려면 capacity-matched 통제가 추가로 필요하다
  (exp66도 같은 confound를 기록했다).
- pose/init은 사전 VIGS run의 고정 replay다. strict online localization 결과가 아니다.
- held-out이 llffhold-8이라 held-out frame이 dense train frame과 시간적으로 인접한다.
  두 arm이 같은 held-out을 쓰지만 이 인접성은 dense 쪽에 유리할 수 있다.

## 재현

```bash
python build_schedules.py     # causal schedule(≈30k) + keyframe pool 생성
python prepare_manifest.py    # 6 job manifest
python run_panel.py           # 순차·재개 가능 실행
python summarize.py           # 논문 표(summary.md)
```
