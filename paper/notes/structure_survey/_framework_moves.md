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

## §3 Method — 해부 4편에서 추가로 확인한 move

> 위 표는 cartgs 한 편에서 귀납한 것이고, 아래는 chen2026cover / mallick2024taming3dgs /
> lmrs / vigsslam을 해부하며 추가된 것이다. 출처 논문을 함께 적는다.

| move | 하는 일 | 실물 |
|---|---|---|
| **Roadmap (열거형)** | 유도 단계를 "(1)…(2)…(3)…"으로 세어 소절 개수와 일치시킴 | chen §4 도입 |
| **Roadmap (사슬형)** | 소절마다 **존재 이유**를 붙임 — 앞이 만든 문제를 뒤가 푼다 | lmrs §4 도입 |
| **Measurement / 프로파일 우선** | 주장이 아니라 실측으로 병목을 지목하고 표적 해결로 감 | taming §4 도입 |
| **Empirical law** | 관찰 → 곡선 적합 → 닫힌 형태 스케줄 | taming §3.2 |
| **Correction rule** | 스케줄이 현실(소멸·prune)과 어긋날 때의 보정을 한 문장으로 정의 | taming §3.2 4문단 |
| **가정 원장 (assumption ledger)** | 근사마다 **성립 조건**을 한 구절씩 붙임 | chen §4.4 |
| **등식→부등식 감사** | 등식이 깨지는 지점 + 대신 성립하는 것 + 그래도 주장 가능한 것 | chen §4.1 (Cauchy-Schwarz) |
| **Forward pointer** | §3에서 §4의 특정 표/그림을 지목 — "이건 취향이 아니라 측정된 것" | taming §3.2, lmrs §4.2 |
| **In-method 실패 보고** | **자기 중간 설계의 열세를 §3 본문에서** 인정하고, 그것을 다음 소절의 동기로 씀 | lmrs §4.2 ("4× slower, as shown in Tab. 3") |
| **가정 반증 그림** | 흔한 근사를 쓸 수 **없다**는 것을 그림 하나로 못박음 | lmrs Fig.3 (대각/블록대각 아님) |
| **Diagnosis (인용형)** | baseline의 **실제 문장**을 인용해 문제를 세움 | vigsslam §3.3을 우리가 인용하는 형태 |
| **소절 전이 Diagnosis** | Diagnosis가 절 앞에만 오지 않는다 — 소절 사이에도 온다 | chen §4.3 끝 |

## §4 Experiments — 추가 move

| move | 하는 일 | 실물 |
|---|---|---|
| **Contract 선언** | 평가 조건에 이름 + 제외 항목 + **제외 크기(수치)** + 적용 대상 + 제외본은 supp. | vigsslam §4 Baselines ("before the final global BA … over 10 minutes") |
| **Comparability guard** | *"…are not directly comparable to ours"* — 비교 불가를 표 앞에서 명시 | vigsslam §4 Metrics |
| **Provenance 캡션** | 인용 수치 / 재현 수치 / 실패(F)를 캡션에서 구분 | vigsslam Table 1 |
| **지표 이중 묶음** | 품질군과 자원군을 선언해서 나눔. peak vs final 이중 계측 | taming §5.1 (`Peak #G`) |
| **품질+자원 단일 표** | IPF·train time을 품질 옆에 둬서 "같은 계산량에서"를 표 하나로 | cartgs Table I, taming Table 1 |
| **Budgeted scenario 2개** | 같은 예산→품질 / 같은 품질→예산. 표 하나를 상하로 분할 | taming §5.2 |
| **예산 봉인 문장** | ablation 표 앞 *"all configurations yield the same number of Gaussians"* | taming §5.3 |
| **교란변수 동거 표** | 기여 축과 교란 축을 **같은 표**에 넣어 기여의 크기를 스스로 드러냄 | lmrs Table 2 (sampler × batch size) |
| **레짐 서술** | "baseline이 강하다"를 먼저 인정 → 이유 → gap이 열리는 레짐 탐색 | chen §5.1 |
| **Regime 표 + oracle 행** | method×baseline이 아니라 **setting×method** + 상한 행 | chen Table 2 |
| **열화 조건 소절** | 입력을 인위적으로 열화시켜 강건성을 보고, **지표도 바꿈** | vigsslam §4.2 (Strided, ATE→Recall) |
| **명명 ablation** | (a)–(f)로 번호를 주고 **무엇을 껐는지 한 문장씩 정의** | vigsslam §4.3 |
| **Compute time 독립 소절** | 고정 시간 예산 논리로 마무리 | chen §5.3 |
| **Rejected alternatives 부록** | 시도했다 버린 대안을 표로. 본문 지면 0 | lmrs App E |
| **Disabled features 부록** | 무엇을/왜 껐는지 + **선행 연구도 그랬음** | lmrs App F |
| **가정 원장 ↔ Limitations 짝** | §3에서 붙인 가정을 §6에서 순서대로 감사 | chen §4.4 ↔ §6 |
