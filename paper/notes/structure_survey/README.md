# structure_survey/ — 기존 논문 구조 해부

> **목적:** "무슨 내용인가"가 아니라 **"어떻게 썼는가"**를 기록한다.
> 절 구성, 문단마다 하는 일, 수식·그림 배치, 증거를 어디에 두는가.
> 내용 요약은 `../related_work/`에 따로 있다. 목적이 다르니 섞지 않는다.

방법론의 출처는 `refs/00_writing/snu_paper_analysis_example.pdf` —
게재 논문 위에 구간을 표시하고 move 이름을 붙이는 방식이며, 이 폴더는 그것을 마크다운으로 옮긴 것이다.

## 현재 범위: §3 Method와 §4 Experiments만

전 섹션을 한 번에 하지 않는다. §1/§2는 과기글 프레임워크(Field→Map→Gap→Aim)가 이미 잘 덮지만,
**§3/§4는 그 프레임워크가 못 덮는 구간**이라 실측 조사가 가장 필요하다.
우리 §3은 Lagrangian 유도 + deterministic controller라 일반적인 실험과학 Methods와 서술 결이 다르다.

## 진행표

| 논문 | PDF | 왜 이걸 보나 | §3 | §4 | 상태 |
|---|---|---|---|---|---|
| **cartgs** | `refs/05_budget_system/cartgs.pdf` (8p) | 계산 예산 정렬 GS-SLAM. **우리 문제의식과 가장 가까움** | ✅ | ✅ | 완료 |
| mallick2024taming3dgs | `refs/05_budget_system/mallick2024taming3dgs.pdf` (13p) | 제한 자원 3DGS. 한글 번역본 대조 가능 | — | — | 예정 |
| chen2026cover | `refs/02_view_selection/chen2026cover.pdf` (9p) | **CVPR 조판 실물** + 최적화 유도가 있는 §3 | — | — | 예정 |
| vigsslam | `refs/01_gs_slam/vigsslam.pdf` (31p) | 우리 baseline이 스스로를 어떻게 서술하는가 | — | — | 예정 |
| lmrs | `refs/05_budget_system/lmrs.pdf` (17p) | 최적화 유도 중심 논문의 §3 | — | — | 보류 |

## 해부 스키마 (모든 파일 공통)

```markdown
# <bibkey> — 구조 해부
## 기본 정보          venue / 쪽수 / §3·§4 분량
## §3 골격            소절 목록 + 각 소절의 역할 한 줄
## §3 문단 단위 해부   | 위치 | 문단 | 하는 일 | 수식·그림 |
## §4 골격            Setup 항목 / Results 조직 / 표 구성
## §4 지표 설계        무엇을 재고 어떻게 보고하나
## ★ 훔칠 것           우리 논문에 그대로 쓸 구조
## ✗ 우리와 다른 점     따라 하면 안 되는 것
## 없는 move           이 논문에 없는 것 (우리에겐 필요한가?)
```

마지막 "없는 move" 칸을 반드시 채운다 — 학생 예시도 빠진 move를 "⇨ 없음"으로 명시한다.
