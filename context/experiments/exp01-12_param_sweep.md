# exp01~12 — Parameter Sweep (통합 카드)

- 날짜: 2026-06-16
- result dir: `results/experiments/exp01_*` ~ `results/experiments/exp12_*`
- 데이터: MPS init 1311장 full (`aria_mps_2dgs/0416_Data__0416_301-1253`), 30k iter

## 목적

densification/pruning/optimizer/LR/sparse prior 파라미터로 floater를 줄일 수 있는 상한 확인.

## 결과 요약

| Exp | 핵심 설정 | PSNR@30k | 판단 |
|---|---|---:|---|
| exp01 | full baseline | - | 기준선 (886k Gaussians) |
| exp02 | sparse densification | 33.377 | 최고 PSNR, large-scale 위험 |
| exp03 | large-scale 개선 계열 | 33.052 | large-scale 개선 |
| exp04 | 구조 개선 계열 | 32.831 | 구조 개선, PSNR 손실 |
| exp05 | beta1=0.95 | 조기중단 | 기각 |
| exp06 | beta1=0.85 | 32.879 | beta1=0.85 채택 |
| exp07 | pruning 완화 | 조기중단 | 기각 |
| exp08 | 종합 best | 33.012 | → [별도 카드](exp08_best_baseline.md) |
| exp09 | densify_until=5000 | 조기중단 | 너무 이름 |
| exp10 | position LR 낮춤 | 32.574 | PSNR 손실 큼 |
| exp11 | position LR 완화 | 32.682 | 부족 |
| exp12 | sparse depth prior 0.01→0.002 | 32.587 | 기각 |

## Verdict

- densification을 덜 자주(interval=200), 더 까다롭게(threshold=0.0004), 더 일찍 끝내는(until=7000) 방향이 유효 → exp08로 수렴.
- sparse depth prior는 이 weight에서 품질/floater proxy 모두 악화. sparse point에 outlier가 섞여 있어 강한 prior는 잘못된 geometry를 고정함 (exp12).
- **한계 확인**: parameter search만으로는 floater 근본 해결 불가 → 진단 루프로 전환 (`rounds/`).

## 주의 (beta1 실험의 의도)

beta1을 낮춘 것은 momentum으로 local minima를 탈출하려는 것이 아니라 **early 잘못된 gradient/momentum 누적을 덜 따라가게** 하려는 것. 재해석 시 position/scaling LR schedule, densification timing과 함께 봐야 함.
