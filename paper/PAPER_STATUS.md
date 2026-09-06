# PAPER_STATUS — 논문 현재 상태 (1페이지 엄수)

> **append-only.** 기존 항목을 수정하지 말고, 정정은 "최근 흐름" 맨 위에 새 항목으로 덧붙인다.
> 넘치면 `notes/` 로 밀어낸다. (`context/STATUS.md`와 같은 규칙)

## 타깃

**CVPR 2027** — 마감 **2026-11-13 추정** (초록 2026-11-07), 공식 CFP 미발표.
오늘(2026-09-05) 기준 **약 10주**.

## 세 contribution과 현재 증거 성숙도

| | contribution | 담당 | 구현 | 실증 | 논문 주장 가능? |
|---|---|---|---|---|---|
| **C1** | Pool-Independent GPU-Token Admission | 나 | ❌ 미구현 | ❌ 없음 | **불가** — 제안 단계 |
| **C2** | Entropy-Regularized Count-Balanced Block Reshuffling | 나 | ✅ opt-in `block128_beta002` | ⚠ 부분 | **부분** — 품질보존·고엔트로피만 |
| **C3** | Carve Loss | 팀원 | ✅ batch (`3dgs-custom/eval/carve_loss.py`) | ⚠ batch만 | **부분** — incremental 미검증 |

상세는 [`plan/claims/CURRENT.md`](plan/claims/CURRENT.md).

## 크리티컬 패스

```
P01 (C1 구현) → P02 (rate-invariance) → P03 (C2 재검증)
                                          ↑ 여기가 막히면 C1·C2 둘 다 주장 불가
P04 (carve 이식, 팀원)  ────────────────────┘  병렬
```

exp72가 자기 실패 원인을 **"기존 minimum-count maturity gate를 유지해 ordering이 admission에
계속 영향"** 이라고 명시했다. 즉 **C1 없이는 C2도 완성되지 않는다.** 순서는 협상 불가.

## 지금 열려 있는 결정

1. **C3를 독립 §3.4로 낼 것인가, scheduler의 geometry lane으로 낼 것인가.**
   2026-09-01 mission brief(`context/research/2026-09-01_carve_kf_viewset_mission.html` §8.2)는
   후자를 권고한다. 팀원·사수 합의 필요.
2. **membership(§3.2)을 헤드라인에서 뺀 뒤의 서사 접착제.** 초안은
   cardinality→membership→ordering 3단 분해가 뼈대였다. 현재 대안은
   "admission과 ordering의 분리"를 중심 문장으로 두는 것.
3. **admission token 정책: carry vs no-prepurchase.** 논문에서 하나로 고정해야 한다.
   현재 후보는 보수적인 no-prepurchase.
4. **Overleaf 동기화 방식** — 선배님 공유 대기.
5. **CVPR 2027 author-kit 교체 시점** — 현재 `latex/`는 2026 kit.

## 최근 흐름 (최신순)

- **2026-09-06 — 세 기여를 묶는 논리 확정. 중심 문장 재작성.**
  v02 중심 문장은 C1·C2 를 supervision 배분으로 묶고 **C3 를 "남은 free-space 오류"로 붙여** 놓았다.
  원래 분해가 `cardinality / membership / ordering` 으로 **셋 다 스케줄링**인데 carve 는 loss 항이라
  그 삼분법에 안 들어가는 것이 원인이었다. membership 이 계속 어색했던 것도 같은 뿌리다.

  → 확정: **"온라인 매핑은 아직 도착 중인 데이터셋에 모델을 맞춘다"는 한 사실이
  offline 3DGS 의 세 가정을 각각 깨뜨린다.**

  | 깨지는 가정 | 우리 답 |
  |---|---|
  | 고정 집합 위의 고정 예산 | §3.1 Compute-Paced View Growth |
  | 셔플링은 유한 고정합 위에 정의된다 | §3.2 ERCB |
  | 기하는 가진 뷰로 결정된다 | §3.3 Causal Free-Space Carving |

  이 틀에서 C3 는 붙는 게 아니라 **같은 원인의 세 번째 결과**가 되고,
  §3.2 의 scope guard("pool 이 자라서 RR 보장을 못 가져온다")가 변명이 아니라 **주제의 재확인**이 된다.
  소절 순서(데이터→순서→목적함수)도 필연이 된다.

  → ⚠ **성립 조건:** carve 가 *관측 부족으로 생긴* floater 를 다룰 때만 성립한다.
  관측이 충분해도 최적화가 만든 floater 라면 이 틀은 무너지고 대안("학습 루프의 세 손잡이 —
  데이터/순서/목적함수")으로 되돌아가야 한다. **팀원 확인 전까지 §3.3 초안을 쓰지 않는다.**

  → 부수: §3 도입에서 Notation·배경식을 뺐다. 넣어본 배경식 2개를 §3.1·§3.2 가 한 번도
  참조하지 않았고, 두 소절이 쓰는 기호는 전부 우리 것이라 각자 쓰이는 자리에서 정의된다.
  3DGS 소개는 §2, mapping loss 는 §3.3 carve 가 필요할 때 진다.

  → 반영: `plan/outline/` v03, `sections/03_method/3-0_overview/plan/` v03, `latex/sec/4_method.tex`.

- **2026-09-06 — §3/§4 구조 확정. (위 열린 결정 중 3건 종결.)**
  절 제목 3개를 확정하고 §3·§4 소절 구성을 닫았다.

  | | 확정 |
  |---|---|
  | C1 | **Compute-Paced View Growth** |
  | C2 | **Entropy-Regularized Count Balancing (ERCB)** |
  | C3 | **Causal Free-Space Carving** (팀원 확정 대기) |
  | §3 | 3.0 + 소절 3개 |
  | §4 | 번호 없는 Setup + **4.1 Main Results / 4.2 Ablations** |
  | 산출물 | **4표 5그림** (v01은 5표 6그림) |

  이름 원칙: **제목은 이 분야 말로, 계보는 본문 첫 문단에서.**
  `admission`·`token`·`credit`·`reshuffling`·`Plackett–Luce`·`token bucket`은 전부 본문으로 내렸다.
  코퍼스 25편 실측에서 `admission`/`token`/`quota`/`reshuffling`은 0회였고, `pool`도 28회 중
  5회가 저자명 `Poole`·나머지가 `pooling`이라 사실상 안 쓰는 말이었다. 그리고 `shuffling`은
  cartgs·taming3dgs 둘 다에서 **CUDA warp shuffle**을 뜻했다.

  → 종결된 결정: ① carve를 독립 contribution으로 (§3.3), ② membership은 기여로 세지 않고
  §3.1의 run-in 볼드 문단으로 흡수, ③ MonoGS baseline을 구현할지 인용할지 — 캡션에 출처를
  구분 표기하면(vigsslam Table 1 방식) 섞어도 된다.

  → 부수 결정: Preliminaries를 독립 절로 빼지 않는다. vision 25편 중 4편뿐이고
  **GS-SLAM(MonoGS·SplaTAM·Photo-SLAM·Co-SLAM·iMAP·CaRtGS·VIGS-SLAM)은 예외 없이 안 뺀다.**
  절 번호는 계획 문서대로 유지된다.

  → 반영: `notes/naming/` v02, `plan/outline/` v02, `plan/figures/` v02,
  `plan/experiment_table/` v03, `sections/03_method/`·`04_experiments/` 폴더 재편.

  → ⚠ 남은 것: **exp72에 `K=128, β=0` arm이 없다.** β=0은 K=1에서만 쟀으므로 block 길이와
  β 효과가 섞여 있고, **β 자체의 기여는 아직 한 번도 측정되지 않았다.** P03 sweep에 이 칸이
  있으나 미착수. 계측 항목 `peak pool`·`총 admission 수`도 protocol에 추가해야 한다.

- **2026-09-06 — Overleaf 동기화 방식 결정. (위 열린 결정 4번 종결.)**
  선배님이 공유하신 프로젝트(`overleaf.com/project/6a9c1b93c9b98e33cf8e5770`)를
  `CVPR2027_chsong_s_intern.zip`으로 받았다. 확인 결과 **논문 초안이 아니라 연구실 템플릿 껍데기**로,
  이전 논문(카메라 캘리브레이션, conic moment estimator)을 복사해 제목만 `Real-time GS Mapping`으로
  바꾼 상태다. §1은 `\lipsum` 더미이고 §2·§4·§5는 `\section{}` 한 줄뿐이라 **우리 서사와 충돌할
  기존 내용이 없다.** → contribution 개수·이름·순서 결정을 Overleaf 확인 뒤로 미룰 이유가 사라졌다.

  합의: **Overleaf는 그대로 두고, 로컬 작업 기준을 그 zip으로 삼으며, 동기화는 사람이 직접
  복사·붙여넣기로 한다.** 자동 스크립트·git remote 연결은 쓰지 않는다.
  `paper/latex/`를 zip으로 교체하고, 기존 CVPR 2026 author-kit 트리는
  `notes/archive/latex_authorkit2026_2026-09-05/`로 보관했다(참고문헌 30개 포함).
  규칙 전문과 미반영 목록은 `latex/SYNC.md`.

  → 선배님 확인 대기 4건 (확인 전까지 우리가 손대지 않는다):
  ① `cvpr.sty`가 **2024년 판**(`\confYear{2024}`)이고 폴더 이름만 CVPR2027 — 2026 판 교체 여부,
  ② 지금 camera-ready 모드(`\usepackage{cvpr}`)라 줄 번호가 없음 — review 모드 전환 여부,
  ③ 이전 논문 잔존물(`6_conclusion.tex` 본문, 고아 `4-x_algorithm.tex` 3개, `temp.tex`,
  `note.tex`, acknowledgment 과제번호, `main.bib` 앞쪽 34개 엔트리) 삭제 여부,
  ④ `main.tex`의 저자 목록이 이번 저자인지.

- **2026-09-05 — exp73로 C1 token law 구현·부분 실증 (위 최초 상태표 정정).**
  5090에서 기존 `interval bootstrap + maturity gate`를 `global seed 1 + token-only/no-prepurchase`로
  교체했다. 두 장면 7개 gate-free run·526 admission poll에서
  `A_paid(u)=⌊u/κ⌋` 정수 오차는 0이었다. `κ=22`는 1253 두 번 평균
  27.711dB(baseline 대비 +0.003), 305 28.815dB(−0.119)로 품질 기준을 통과했다.
  따라서 위 표의 C1 “미구현/실증 없음”은 현재 **구현 ✅ / 실증 ⚠ 부분**으로 정정한다.
  단, exp73은 순수 gate-removal이 아니라 무료 interval bootstrap까지 제거한 정책 교체이며,
  hardware-rate·carry 비교는 미검증이다. selection CV도 1253 0.951, 305 0.942로 악화해
  lifetime 균등화는 P03에 남는다.

- **2026-09-05 — `paper/` 폴더 개설.**
  main 브랜치에서 직접 진행(별도 논문 브랜치 없음). 착수 전에 `exp72-entropy-count-scheduler`를
  main으로 fast-forward 하고, **어느 브랜치에도 커밋되지 않았던 파일 4개**를 백업 커밋했다
  (`eee3e8b`): exp70 카드, `vigs_slam_chapter3_4_working_draft.md`(§3 본문 초안),
  `vigs_slam_method_three_contributions_notion_draft.md`, exp69 evidence json 1개.
  CVPR 공식 author-kit(2026)을 `latex/`에 설치했다.
  → 미해결: `discussion_bullets.md`가 2026-09-04에 두 갈래로 갈렸고 두 버전 모두
  `notes/archive/discussion_bullets/`에 보관했다. 정본 선택 필요.
