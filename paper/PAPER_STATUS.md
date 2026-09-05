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

- **2026-09-05 — `paper/` 폴더 개설.**
  main 브랜치에서 직접 진행(별도 논문 브랜치 없음). 착수 전에 `exp72-entropy-count-scheduler`를
  main으로 fast-forward 하고, **어느 브랜치에도 커밋되지 않았던 파일 4개**를 백업 커밋했다
  (`eee3e8b`): exp70 카드, `vigs_slam_chapter3_4_working_draft.md`(§3 본문 초안),
  `vigs_slam_method_three_contributions_notion_draft.md`, exp69 evidence json 1개.
  CVPR 공식 author-kit(2026)을 `latex/`에 설치했다.
  → 미해결: `discussion_bullets.md`가 2026-09-04에 두 갈래로 갈렸고 두 버전 모두
  `notes/archive/discussion_bullets/`에 보관했다. 정본 선택 필요.
