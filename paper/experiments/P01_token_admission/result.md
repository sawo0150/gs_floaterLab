# P01 — GPU-Token Admission 구현 및 이론식 대조 — 결과

> **append-only.** 기존 항목을 수정하지 말고, 정정이 필요하면 맨 위에 새 항목을 덧붙인다.
> 실패는 실패로 정직하게 기록한다 (프로젝트 원칙).

## 2026-09-05 — exp73 탐색적 부분 결과 (5090)

> 아래의 초기 “결과 없음” 표기를 갱신한다. exp73은 P01의 사전등록된 세 arm 전체가 아니라
> **baseline과 token-only/no-prepurchase**를 비교한 부분 실행이다.

### 구현 및 law audit

- 기존 `interval bootstrap + maturity-gated credit`을 `global seed 1장 + token-only paid admission`으로 교체했다.
- 두 장면의 gate-free 7개 run, admission poll 526개에서
  `A_paid(u)=⌊u/κ⌋`의 정수 오차가 모두 0이었다.
- pending candidate가 없을 때 credit을 폐기하는 no-prepurchase를 구현했다.
- 관련 scheduler 회귀 테스트 64개와 Python/shell syntax 검사를 통과했다.

### `κ=22` 품질 결과

| 장면 | 반복 | held-out PSNR | baseline 대비 | 최종 pool | selection CV |
|---|---:|---:|---:|---:|---:|
| aria1253 | 2 | 27.711 dB 평균 | +0.003 dB | 275.5 평균 | 0.951 |
| aria301_305 | 1 | 28.815 dB | −0.119 dB | 749 | 0.942 |

두 장면 모두 사전 사용하던 `−0.2 dB` non-regression 기준을 통과했으나, 장면 수와 반복 수가
부족하므로 `κ=22`는 universal constant가 아니라 다음 scheduler A/B의 engineering candidate다.

### 반드시 유지할 해석 경계

exp73은 **순수 gate-removal ablation이 아니다.** 1253에서 pool이 422.5→275.5로 줄어든 것은
paid admission이 줄어서가 아니라 무료 interval bootstrap이 약 217장→1장으로 줄었기 때문이다.
실제 분해는 baseline `217+194=411`, `217+217=434`에서 token-only `1+274=275`,
`1+275=276`으로 바뀌었다. 305에서는 `312+362=674 → 1+748=749`로 오히려 증가했다.

또한 selection CV가 1253 `0.373→0.951`, 305 `0.470→0.942`로 악화했다. 따라서 exp73은
admission law를 실증했지만 lifetime count 균등화는 해결하지 못했다. carry arm, 동일 bootstrap을
유지한 순수 gate-removal arm, 5070Ti/slowdown rate-invariance는 미실행이다.

(아직 결과 없음)
