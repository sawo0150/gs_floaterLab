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
