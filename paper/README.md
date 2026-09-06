# paper/ — VIGS-SLAM 논문 작업 공간

> 목표 학회: **CVPR 2027** (개최 2027-06-20~24, 시애틀).
> 마감은 이전 사이클 기준 **2026-11-13** / 초록 등록 2026-11-07 로 **추정**이며 공식 CFP 미발표.
> → `plan/timeline/CURRENT.md` 에 확인 체크포인트가 있다.

이 폴더는 `context/`(실험 지식베이스)와 **경로가 겹치지 않는다.** `context/`는 실험이,
`paper/`는 논문이 단일 진실 소스다. 숫자의 출처는 언제나 `context/`와 `results/`이고,
`paper/`는 그것을 **어떻게 주장할지**를 관리한다.

## 어디부터 읽나

| 무엇 | 어디 |
|---|---|
| 지금 상태와 다음 할 일 | [`PAPER_STATUS.md`](PAPER_STATUS.md) |
| 섹션별 무슨 내용을 쓸지 | [`sections/README.md`](sections/README.md) → 각 절 폴더 |
| 실험 테이블 | [`plan/experiment_table/CURRENT.md`](plan/experiment_table/CURRENT.md) |
| 무엇을 주장해도 되는가 | [`plan/claims/CURRENT.md`](plan/claims/CURRENT.md) ← **가장 중요** |
| 전체 서사·페이지 배분 | [`plan/outline/CURRENT.md`](plan/outline/CURRENT.md) |
| 마감 역산 | [`plan/timeline/CURRENT.md`](plan/timeline/CURRENT.md) |

## 폴더

| 폴더 | 무엇 | 버전 관리 |
|---|---|---|
| `plan/` | 논문 전체를 가로지르는 계획 (outline·실험테이블·claim·figure·timeline) | ▣ 버전 폴더 |
| `sections/` | CVPR 목차 1:1. 각 절에 "무엇을 쓸지"를 키워나가는 곳 | ▣ 버전 폴더 |
| `experiments/` | 논문용 실험 P01..Pnn. `protocol/`은 공통 평가 계약 | ▣ 일부 |
| `results/` | 실험 숫자. 경량만 git (raw 로그·PLY는 원격 머신) | run_id |
| `notes/` | 유도 노트·읽기 노트·미팅·원본 보관 | ▣ 일부 |
| `latex/` | **Overleaf 프로젝트 미러.** 규칙은 `latex/SYNC.md` | git |
| `scripts/` | 도구 모음. 사용법은 [`scripts/README.md`](scripts/README.md) | git |

## 버전 관리 규약

반복 수정되는 문서는 **파일이 아니라 폴더**다.

```
plan/claims/
├── README.md                         # 고정 메타 + 버전 이력 표
├── v01_2026-09-05_initial.md
├── v02_2026-09-25_after-P03.md
└── CURRENT.md → v02_2026-09-25_after-P03.md
```

- **`CURRENT.md` 심링크가 항상 정본.** 사람도 스크립트도 경로를 바꾸지 않고 읽는다.
- **README의 버전 이력 표가 핵심**이다. 옛 버전을 남기는 값어치는 파일이 아니라
  `트리거 / 무엇이 바뀌었나 / 폐기된 주장` 세 칸에 있다.
- 새 버전은 반드시 스크립트로:
  ```
  ./paper/scripts/newver.sh paper/plan/claims after-P03 "P03 재검증 결과 반영"
  ```

### bump 기준 (안 정하면 v47까지 간다)

| bump **한다** | bump **안 한다** |
|---|---|
| 실험 결과가 들어와 claim이 바뀔 때 | 오탈자 |
| 리뷰를 받았을 때 (사수·선배·팀원) | 문장 다듬기 |
| 섹션 구조·서사가 바뀔 때 | 표 숫자 갱신 |
| 주장 범위를 넓히거나 좁힐 때 | 링크 수정 |

오른쪽 칸은 **현재 버전 파일을 직접 고친다.** git이 이미 이력을 잡고 있다.

### 버전 폴더가 아닌 것

`PAPER_STATUS.md`, `experiments/REGISTRY.md`, `experiments/*/result.md` 는 **append-only**다.
기존 항목을 수정하지 않고, 정정이 필요하면 **위에 새 항목을 덧붙인다.**
(`context/STATUS.md`와 같은 규칙 — `AGENTS.md` 참조)

## 숫자가 흐르는 방향

```
원격 실험(5090/5070Ti) → results/runs/<run_id>/ → results/tables/*.csv
                                                       ↓ scripts/make_tables.py
                                                  latex/tab/*.tex → \input
```

**latex 에 숫자를 손으로 적지 않는다.** exp72 재실험이 확정되어 있어 숫자가 여러 곳에
박히면 반드시 어긋난다. 모든 표 숫자는 `results/tables/*.csv` 가 출처다.

## 실험 머신

| 별칭 | SSH | GPU |
|---|---|---|
| colin | `chaehyun` (colin@147.46.130.19:363) | RTX 5090 |
| fastMRI desktop | `fastmri-desktop` / `fastmri-5070ti` | RTX 5070 Ti |

두 대의 속도 차이는 부담이 아니라 **C1의 rate-invariance 실험 셋업**이다 (P02 참조).

## Overleaf

**결정됨 (2026-09-06) — 사람이 직접 복사·붙여넣기.** 자동 동기화 스크립트는 만들지 않는다.
`latex/` 는 공유받은 Overleaf 프로젝트 zip을 푼 것이며, "Overleaf가 그렇게 되어야 할 모습"으로
유지한다. 아직 안 올린 변경은 목록으로 관리한다.

로컬에서 쓰고 렌더링해 보다가 됐다 싶으면 Overleaf 에 붙여넣는다.

```bash
./paper/scripts/tex.sh watch    # 저장할 때마다 자동 빌드 → paper/build/main.pdf
./paper/scripts/sync.sh status  # 이제 뭘 Overleaf 에 올려야 하나
```

빌드는 TinyTeX(`~/.TinyTeX`, sudo 불필요). `build/` 와 `.sync-snapshot/` 은 git 제외.

→ 규칙 전문과 미반영 목록은 **[`latex/SYNC.md`](latex/SYNC.md)**. `latex/` 관련해서는
이 README보다 그 파일이 우선한다.
