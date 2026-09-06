# 논문 아웃라인 v03 (2026-09-06) — 묶는 논리 확정

> 섹션 **간** 논리 흐름과 페이지 배분. 절 **내부** 상세는 `sections/*/plan/CURRENT.md`.
> CVPR 본문 8쪽 (references 제외) 기준.

## 중심 문장 (v03 확정) — 한 원인의 세 결과

### v02 가 안고 있던 균열

v02 의 중심 문장은 이랬다:

> …"얼마나 받아들일지"와 "어떤 순서로 학습할지"는 서로 다른 문제인데 기존은 keyframe 하나에
> 묶는다. … 그 위에서 순서를 정하며(C2), **남은** free-space 오류를 carve 로 억제한다(C3).

**"남은"이 다 하고 있었다.** C1·C2 는 supervision 배분이라는 한 논리로 묶이는데 C3 는
*"그리고 이것도 있다"* 로 붙어 있었다.

원인은 원래 분해가 `cardinality / membership / ordering` — **셋 다 스케줄링**이라는 데 있다.
carve 는 스케줄링 결정이 아니라 **loss 항**이라 그 삼분법에 애초에 안 들어간다.
membership 이 계속 어색했던 것도 같은 뿌리다. 스케줄링 축은 실은 둘인데 셋으로 세려니 억지가 났다.

### 확정된 묶음

> **온라인 매핑은 아직 도착 중인 데이터셋에 모델을 맞춘다. 이 하나의 사실이 offline 3DGS 가
> 딛고 선 세 가정을 각각 깨뜨린다 — 고정 집합 위의 고정 예산(§3.1), 유한 고정합 위의
> 셔플링(§3.2), 가진 뷰로 결정되는 기하(§3.3). 기존 온라인 시스템은 이 셋을 keyframe 규칙
> 하나로 물려받는다.**

| 깨지는 offline 가정 | 왜 깨지나 | 우리 답 |
|---|---|---|
| 고정 집합 위의 고정 예산 | 집합이 자라면 update 가 희석된다 | **C1** Compute-Paced View Growth |
| 셔플링은 유한 고정합 위에 있다 | pool 이 자라면 그 전제가 무너진다 | **C2** ERCB |
| 기하는 가진 뷰로 결정된다 | free space 는 충분히 관측되기 전엔 미결정. floater 가 그 산물 | **C3** Causal Free-Space Carving |

### 이 틀이 주는 것 셋

1. **C3 가 붙는 게 아니라 파생된다.** floater 는 게으름이 아니라 *데이터셋이 아직 그 영역을
   결정하지 못했다는 증거*다. carve 는 "덤으로 넣은 정규화"가 아니라 "불완전한 데이터셋에서
   기하를 어떻게 제약하는가"의 답이 된다.
2. **§3.2 의 scope guard 가 변명에서 논거로 바뀐다.** *"pool 이 자라서 random reshuffling 의
   수렴 보장을 못 가져온다"* 는 사과가 아니라 **주제의 재확인**이다. pool 이 자라는 것이 이 논문의
   전제이기 때문이다.
3. **기존이 왜 실패하는지가 한 줄로 설명된다.** baseline 은 offline 가정을 그대로 들고 온라인에 온다.

### 소절 순서의 필연성

데이터 → 순서 → 목적함수. 학습 루프의 세 손잡이 순서이자, 위 세 가정이 깨지는 순서다.

### ⚠ 이 묶음이 성립하는 조건

**carve 가 "관측 부족으로 생긴 floater"를 다룰 때만 성립한다.**
관측이 충분해도 최적화가 만든 floater 를 다루는 것이라면 이 틀은 무너지고,
대안인 **"학습 루프의 세 손잡이(데이터 / 순서 / 목적함수)"** 로 되돌아가야 한다.
그쪽은 셋이 대등하지만 *왜 하필 이 논문이 그 셋을 다시 다루는가*를 설명하지 못한다.
→ **팀원 확인 필요.** 확인 전까지 §3.3 초안을 쓰지 않는다.

### 그 밖의 경계

- ⚠ 이 중심 문장은 **C1 이 실증되어야 성립한다.** P01/P02 실패 시
  [`plan/claims/CURRENT.md`](../claims/CURRENT.md) §B 의 fallback 으로 갈아탄다.
- membership(slot placement)은 §3.1 의 run-in 볼드 한 문단으로 남고,
  **+0.35% 라는 작은 이득 자체가 "병목은 어느 프레임이냐가 아니라 몇 장이냐"의 근거**로 쓰인다.

## 페이지 배분 (본문 8쪽)

| 절 | 쪽 | 누적 | 폴더 |
|---|---:|---:|---|
| Abstract | — | — | `sections/00_abstract/` |
| 1. Introduction | 1.0 | 1.0 | `sections/01_intro/` |
| 2. Related Work | 1.15 | 2.15 | `sections/02_related/` |
| 3. Method | 3.25 | 5.4 | `sections/03_method/` |
| 4. Experiments | 2.2 | 7.6 | `sections/04_experiments/` |
| 5. Conclusion | 0.2 | 7.8 | `sections/05_conclusion/` |
| 6. Limitations | 0.2 | 8.0 | `sections/06_limitations/` |

### §3 내부 (소절 3개 + 도입)

| | 쪽 | 문단 |
|---|---:|---|
| (도입) Method opening | 0.15 | **roadmap 1문단 (6문장 16줄).** Notation·배경식 없음 |
| 3.1 **Compute-Paced View Growth** (C1) | 1.05 | 5 (`Slot placement.` run-in 포함) + 식3 + **Fig.3** |
| 3.2 **Entropy-Regularized Count Balancing** (C2) | 1.0 | 5 + 식4 |
| 3.3 **Causal Free-Space Carving** (C3) | 1.05 | 팀원 |
| Fig.2 system diagram | (별도) | |

⚠ **2026-09-06 변경.** 도입이 0.5p 5문단이었으나 코퍼스 11편 조사 결과 관행에서 벗어났다.
Method 도입은 5~7문장 8~13줄 한 문단이고, 진단에 소절을 준 논문은 cartgs 하나뿐이다.
→ 진단은 각 소절 P1 으로 분산하고, **"세 결정으로 분해"라는 중심 주장은 §1 이 진다.**
→ Notation·배경식도 두지 않는다. 넣어본 배경식을 §3.1·§3.2 가 한 번도 참조하지 않았고,
  두 소절이 쓰는 기호는 전부 우리 것이다. 3DGS 소개는 §2, mapping loss 는 §3.3 이 진다.
그래서 §1 문단 4·5(우리 방법 + 기여 목록)의 무게가 커졌다.

### §4 내부 (번호 붙은 소절 2개 + 도입)

| | 쪽 | 문단 |
|---|---:|---|
| (도입) Setup | 0.35 | `Datasets.` `Streaming contract.` `Metrics.` `Baselines.` |
| 4.1 Main Results | 1.10 | Results pointer → 같은 예산 → 같은 품질 → 장면 일반화 → `Rate robustness.` → `Compute and latency.` |
| 4.2 Ablations | 0.75 | `View growth.` `Count balancing.` `Carving.` |

Preliminaries는 **독립 절로 빼지 않는다** — vision 25편 중 4편뿐이고 GS-SLAM은 예외 없이 안 뺀다.
§3 안에 배경 수식과 기여 수식이 섞이는 문제는 문장 하나로 막는다:
*"Equations (1)–(2) are standard 3DGS and VIGS-SLAM formulations, restated here for notation.
All remaining equations are ours."*

Fig.1 teaser가 1쪽 상단 2단을 먹으므로 §1은 실질 0.6쪽. 유도 전문은 Supplementary로 밀고
본문에는 결과 식과 직관만 남긴다.

## 절 간 논리 흐름

```
§1  keyframe은 tracking을 위해 골라진 것이지 mapping supervision으로 고른 게 아니다
      ↓ 그러면 keyframe 사이 RGB를 얼마나 쓸 것인가?
§3.0 이 결정은 "얼마나 / 어떤 순서로 / 남은 기하 오류" 셋으로 분해된다
      ↓ 고정 iteration도, 고정 FPS도, maturity gate도 답이 아니다
§3.1 (C1) 완료된 GPU service가 증가 속도를 정한다 → pool 크기·하드웨어와 무관
      · (run-in) slot placement는 +0.35% — 병목이 membership이 아님을 보여준다
      ↓ 받아들인 뷰를 어떤 순서로 학습할 것인가
§3.2 (C2) count-Gibbs × K-view 비복원 → 유일한 해가 exp(−βn_i)
      ↓ 순서가 정해져도 free-space 오류가 남는다
§3.3 (C3) causal carve evidence
      ↓
§4   각 결정이 실제로 분리되어 작동하는지 확인
```

각 화살표가 **다음 절이 존재해야 하는 이유**다. 초고를 쓸 때 이 화살표 문장을
절 마지막 문단에 실제로 넣는다.

## Introduction 문단 계획 (5문단)

1. **문제:** GS-SLAM은 Gaussian 초기화는 상당 부분 풀었다. 남은 건 제한된 mapping
   update를 어떤 supervision에 배분할지다.
2. **간극:** tracker keyframe은 tracking 기준으로 골라진 표본이다. photometric map
   optimization에 좋은 집합과 같아야 할 이유가 없다. keyframe 사이 RGB는 이미
   도착해 있다.
3. **왜 단순한 답이 안 되나:** 전부 버리면 coverage 손실, 전부 넣으면 growing pool에
   update 희석, 고정 FPS는 GPU가 실제로 감당한 service를 반영 못 함.
   기존 maturity gate는 view growth와 ordering을 묶어 버린다.
4. **우리 방법:** 세 결정으로 분해 + C1/C2/C3 한 문장씩. **§3.0에서 붙인 문제 이름과 같은 이름**을 쓴다.
5. **기여 목록 (bullet 3개) + 결과 한 줄.**

⚠ 4번에서 C1을 "we show"가 아니라 "we propose"로 쓸지는 P01/P02 결과에 달렸다.

## Related Work 배치

| 소절 | 우리와의 차별점 한 줄 |
|---|---|
| 2.1 GS-SLAM | KF heuristic이 아니라 **완료된 GPU service**가 학습 뷰 증가를 정한다 |
| 2.2 View selection / Active vision | active capture가 아니라 **arrived-only** streaming replay |
| 2.3 Shuffling / without-replacement SGD | 이론을 배경으로 인용하되 **성장하는 비볼록 pool에 보장을 가져오지 않음.** β=0 ≡ random reshuffling은 K ≥ N_t일 때만 |
| 2.4 Floater / geometry reg | offline batch clean-up이 아니라 strict causal + rate-limited online 적용 |

Related Work는 **분류가 아니라 대비**로 쓴다. 각 소절 마지막 문장은 반드시
"따라서 X는 우리 설정에 그대로 적용되지 않는다"로 끝난다.

## v01에서 종결된 것

- ~~§6 Limitations를 독립 절로 둘지 §5에 흡수할지~~ → **미결이나 위험 없음.**
  chen2026cover는 독립 §6, lmrs는 Conclusion 흡수. 둘 다 CVPR 조판 선례. 분량 보고 결정
- ~~membership(§3.2)을 본문에 남길지~~ → **종결.** §3.1의 run-in 볼드 한 문단으로 흡수
- ~~exp72의 실패를 §4 negative result로 낼지 §6로 내릴지~~ → **종결.**
  §3.2 문단 5(scope guard) + Table 3의 `lifetime mid/first` 열.
  lmrs가 자기 중간 설계의 4× 저하를 §4 본문에 실은 형식. 실패가 다음 설계의 근거가 되므로
  Method 안이 가장 강하다

## 아직 안 정한 것

- Fig.1 teaser에 정성 렌더를 넣을지 정량 곡선만 넣을지
- §3.1의 Fisher tie-break를 본문에 남길지 Supplementary로 내릴지
- contribution bullet의 동사 (`we propose` vs `we show`) — P01/P02 결과에 달림
- §3.3 제목 (팀원 확정 대기)

## 구조 확정 (2026-09-06)

이 아웃라인의 절·소절 구성은 **확정**이다. 근거 문서:

| 무엇 | 어디 |
|---|---|
| 절 제목 3개와 그 근거 | `notes/naming/CURRENT.md` |
| §3 구성과 문단 계약 | `sections/03_method/README.md`, `3-0_overview/plan/CURRENT.md` |
| §4 구성과 소절 수 근거 | `sections/04_experiments/README.md` |
| 해부 원본 5편 | `notes/structure_survey/` |
| 표·그림 | `plan/figures/CURRENT.md`, `plan/experiment_table/CURRENT.md` |
