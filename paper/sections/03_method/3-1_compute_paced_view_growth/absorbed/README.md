# absorbed/ — 이 소절에 흡수된 것

사수님 판단으로 **기여라기엔 약하고 절 하나를 주기도 아니라서** 본문에서 독립 소절을 잃은 내용.
지우지 않고 여기 보관한다. 본문에서는 `3-1`의 **run-in 볼드 한 문단**이 된다.

| 폴더 | 원래 위치 | 본문에서 어떻게 되나 |
|---|---|---|
| `trajectory_membership/` | `sections/03_method/3-2_trajectory_membership/` | §3.1 마지막 문단 `\textbf{Slot placement.}` |

## 왜 흡수했나

`notes/structure_survey/`에서 확인한 세 패턴 중 **P1(run-in 볼드)** 을 택했다.

| 패턴 | 실물 | 우리 |
|---|---|---|
| P1 run-in 볼드 문단 | VIGS-SLAM §3.3 `Preliminary.` `Map Management.` `Loop Closure Gaussian Update.` | ✅ 채택 |
| P2 번호는 주되 기여 목록엔 안 넣음 | taming3dgs §3.4 High-Opacity Gaussians | ✗ 사수님이 "절 하나는 아니다" |
| P3 본문 최소 + 부록 | chen2026cover §4.4 끝 + Appendix C | ✗ 아까움 |

## ★ 약하다는 사실 자체를 논증으로 쓴다

실측 이득이 +0.35%인데, 이 숫자를 변명하지 말고 **§3.1이 growth에 집중하는 근거**로 쓴다.

> 슬롯을 trajectory에 고르게 배치해도 +0.35%에 그친다. 즉 병목은 **어느 프레임을 고르느냐**가
> 아니라 **몇 장을 받아들일 수 있느냐**이며, 이것이 §3.1이 view growth에 집중하는 이유다.

chen2026cover가 *"random baseline이 이미 강하다"*를 먼저 인정하고 그것으로 자기 기여의 유효 구간을
짚은 것과 같은 수법이다.

## ablation에는 남긴다

기여로 세지 않는 것과 실험에서 빼는 것은 다르다. taming3dgs도 high-opacity를,
lmrs도 LR 스케줄러를 기여 목록에 안 넣으면서 ablation 표에는 남긴다.
"안 해본 게 아니라 해봤더니 작더라"가 보여야 한다.
