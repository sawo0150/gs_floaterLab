# move 어휘 — §3/§4용

> 과기글 프레임워크(`refs/00_writing/`)는 **IMRaD 실험과학** 기준이라
> §1/§2에는 잘 맞지만 §3/§4에는 부족하다. 아래는 그 어휘를 CS 학회 논문에 맞게 확장한 것으로,
> **관찰에서 귀납한 것**이지 문헌에서 가져온 표준 용어가 아니다. 해부가 쌓이면 갱신한다.

## 과기글 원본 (§1/§2용)

| move | 질문 |
|---|---|
| Field / Topic | 어떤 주제이고 왜 중요한가 → 문제로 좁힘 |
| Map | 그동안 어떤 연구가 있었나 |
| Gap | 그럼에도 왜 계속 주목하는가 |
| Aim | 이 논문이 푸는 문제는 무엇인가 |

**CVPR 매핑:** Map이 §1 압축본 + §2 전체로 **쪼개지고**, Gap이 §2 각 소절 마지막 문장으로 **분산**된다.
Discussion 절이 없어 §5/§6/§4 결과 문단으로 흩어진다.
Introduction은 Field→Aim(넓음→좁음), Conclusion은 Aim→Field(좁음→넓음)의 역순 대칭.

## §3 Method용 (확장)

| move | 하는 일 |
|---|---|
| **Roadmap** | 절 첫 문단. "이 절에서 X를 분석하고 Y를 제안한다" — 길 안내 |
| **Diagnosis** | 문제를 N개로 **이름 붙여** 쪼갬. 각각 [기존방식]→[왜 문제]→[증거] |
| **Bridge** | Diagnosis 각 항목 끝의 한 문장. "In this paper, we …" — 해법 예고 |
| **Preliminaries** | 표기 정의, 배경 수식(우리 기여 아님을 분명히) |
| **Mechanism** | 실제 제안. Diagnosis와 **같은 순서·같은 이름**으로 대응 |
| **In-method evidence** | §4를 기다리지 않고 §3 안에 넣는 정량 근거 (그림·수치) |
| **Scope guard** | 무엇을 주장하지 않는지 |

## §4 Experiments용 (확장)

| move | 하는 일 |
|---|---|
| **Setup: Dataset / Metrics / Baselines / Implementation** | run-in 볼드 소제목으로 나눔 |
| **Results pointer** | 첫 문단에서 모든 표를 한 번에 가리킴 |
| **Per-axis result** | 데이터셋·조건별 문단 |
| **Ablation** | 구성요소 제거 |
| **Diagnostic figure** | 왜 그렇게 되는지 보여주는 그림 |
| **Negative / limitation** | 안 된 것 |
