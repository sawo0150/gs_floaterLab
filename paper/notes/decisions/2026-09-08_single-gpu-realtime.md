# 단일 GPU · 1× 실시간으로 정하면서 잃는 것 (2026-09-08)

> 결정: **5090 한 대에서 1× 실시간으로만 돌린다.**
> 논문에 GPU 두 대를 썼다고 쓰지 않고, pace 배수(0.75~2.0×)도 말하지 않는다.
>
> 그 결정 자체는 문제없다. **다만 딸려서 무너지는 주장이 있어 여기 기록한다.**

## 예산 서술은 오히려 간단해진다

1× 실시간이면 **예산이 곧 스트림 길이**다. 배수를 말할 필요가 없다.

> Each method receives the sensor stream in real time and performs
> **zero optimizer updates after the last frame**; the compute budget is therefore
> the duration of the stream itself.

한 문장으로 끝난다. `1.5×`, `97.65 s` 같은 수치가 필요 없어진다.

## ⚠ 그러나 검증할 실험이 사라지는 주장이 있다

pace 도 GPU 도 안 바꾸면 **"유입 속도가 하드웨어나 도착률과 무관하다"** 를
검증할 실험이 **하나도 없다.**

| 대상 | 상태 | 조치 |
|---|---|---|
| §3.1 P3 의 *"independent of the size of the set **and of hardware speed**"* | 뒷절에 근거 없음 | **뒷절 삭제.** tex 에 `\pend` 로 표시함 |
| claims **B2** — *"S(t) 가 2배면 admission 도 2배"* | ▶ 상태로 영구히 남음 | **삭제 또는 future work 로.** claims 다음 버전에서 처리 |
| **Fig.4** rate invariance (pace × GPU) | 그릴 실험이 없음 | **폐기.** 그림 5개 → **4개** |
| **P02** rate invariance 실험 | — | **폐기** |

## 남는 것은 그대로 유효하다

**pool-independence 는 단일 런 안에서 측정된다.** 궤적이 진행되며 pool 이 커지는데
admission 간격이 그대로인지를 **같은 trace 안에서** 보면 된다.
exp73 의 2장면·7 run·526 poll 이 이미 그것이다 (claims **B1**).

→ C1 의 실증은 **Fig.3(view-growth trace) 하나로 충분**하고,
지운 것은 *"다른 기계·다른 속도에서도 된다"* 는 **부가 주장뿐**이다.

## 되돌리려면

나중에 5070Ti 를 다시 쓰기로 하면 B2·Fig.4·P02 를 되살리면 된다.
그때까지 §3.1 P3 는 **집합 크기 독립성만** 말한다.

## 관련 문서

- `plan/claims/CURRENT.md` §B (B1 유지, B2 처리 필요)
- `plan/figures/CURRENT.md` (Fig.4 폐기 반영 필요)
- `plan/experiment_table/CURRENT.md` (P02 폐기 반영 필요)
- `sections/03_method/3-1_compute_paced_view_growth/plan/CURRENT.md` (P3 문구)
