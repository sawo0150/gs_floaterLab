# refs/ — 참고 논문 목록

> **PDF 파일 자체는 git에 없습니다.** 저작권 자료이고 파일당 최대 50MB, 합계 288MB라
> GitHub에 올릴 수 없습니다. 이 `INDEX.md`만 추적하며, 바이트는 로컬에만 둡니다.
> 다른 컴퓨터에서 작업하려면 아래 목록을 보고 각자 내려받으세요.

## 규칙

- **파일명 = bibkey.** `latex/main.bib`의 키와 1:1로 맞춥니다. 그러면 네 곳이 한 줄로 꿰입니다:
  ```
  main.bib 의 \cite{cartgs}
    ↔ refs/05_budget_system/cartgs.pdf
    ↔ notes/related_work/cartgs.md        (무슨 내용인가)
    ↔ notes/structure_survey/cartgs.md    (어떻게 썼는가 — 구조 해부)
  ```
- **하위 폴더 = `sections/02_related/`의 소절 구조.** 논문이 어느 폴더에 있는지가
  곧 Related Work의 어느 소절에서 인용될지를 뜻합니다.
- 새 논문을 넣으면 **이 표에 한 줄 추가**합니다. 그게 이 폴더의 유일한 관리 비용입니다.

## 00_writing — 논문 작성법 (SNU 과학기술글쓰기)

현재 작업 방법론의 근거 자료. `plan/checklist/`가 여기서 파생됩니다.

| 파일 | 쪽 | 무엇 |
|---|---:|---|
| `snu_writing_guide_1.pdf` | 19 | 서론 4-move 구조(Field→Map→Gap→Aim), Discussion이 그 역순 대칭이라는 원칙, 학부생 보고서 예시 |
| `snu_writing_guide_2.pdf` | 6 | Methods(Materials/Equipments/Procedures)와 Results(General statement→Figure/Table) 구성, 그림·표 캡션 규칙 |
| `snu_paper_analysis_example.pdf` | 9 | ★ **구조 해부의 완성 예시.** 게재 논문 위에 구간을 표시하고 move 이름을 붙인 자료. `notes/structure_survey/`가 이 방식을 마크다운으로 옮긴 것 |

⚠ 이 자료는 **IMRaD 실험과학 논문** 기준입니다. CVPR과의 매핑은 `plan/checklist/CURRENT.md` 참조.

## 01_gs_slam — §2.1 같은 문제영역

| 파일 | 쪽 | 우리 쓰임 |
|---|---:|---|
| `vigsslam.pdf` | 31 | **우리 baseline 그 자체.** arXiv 2512.02293 |

**받아야 할 것:** MonoGS(`matsuki2024monogs`), SplaTAM, Photo-SLAM(`huang2024photoslam`)

## 02_view_selection — §2.2 view 선택 / active vision

| 파일 | 쪽 | 우리 쓰임 |
|---|---:|---|
| `chen2026cover.pdf` | 9 | CVF Open Access **게재판 = 정본**. view 선택을 coverage 최적화로 |
| `chen2026cover_extended13p.pdf` | 13 | 같은 논문 확장판. 유도 세부가 더 있을 때 참조 |
| `comapgs.pdf` | 15 | covisibility map 기반. §3.2 membership과 대비 |

**받아야 할 것:** FisherRF(`jiang2024fisherrf`)

## 03_shuffling_theory — §2.3 without-replacement SGD

(비어 있음) **전부 받아야 함:** `mishchenko2020random`, `shamir2016without`, `ahn2020shuffling`

§3.3 ERCB의 이론 배경이고, **"보장을 가져오지 않는다"는 선을 정확히 긋기 위해** 필요합니다.

## 04_geometry_floater — §2.4 floater / geometry 정규화

C3(carve)의 관련연구. 여기가 가장 두껍습니다.

| 파일 | 쪽 | 우리 쓰임 |
|---|---:|---|
| `sparsegs.pdf` | 14 | sparse view에서의 floater 억제 |
| `tidigs.pdf` | 15 | geometry 개선 계열 |
| `chen2024pgsr.pdf` | 20 | **PGSR** (planar-based). ⚠ 원본 파일명이 `PDGR.pdf`였는데 내용은 PGSR이라 정정함 |
| `splatface.pdf` | 10 | 보조 |
| `ko_report_floater_local_minima.pdf` | 7 | 한글 리포트. ⚠ 원본 파일명이 `3dgs_survey_paper.pdf`였으나 survey 논문이 아니라 국소최적점 리포트라 정정함 |

**받아야 할 것:** TrimGS(`fan2024trimgs`), StableGS(`stablegs`), 2DGS, GOF

## 05_budget_system — §3 서술법을 배울 대상

★ **가장 중요한 카테고리.** 우리 §3은 Lagrangian 유도 + deterministic controller라
보통의 3DGS 논문과 서술 결이 다릅니다. "제한된 자원 / 스케줄링 / 시스템" 논문이
§3을 어떻게 쓰는지를 여기서 배웁니다.

| 파일 | 쪽 | 우리 쓰임 |
|---|---:|---|
| `cartgs.pdf` | 8 | ★ **1순위 해부 대상.** IEEE RA-L. GS-SLAM의 계산 정렬(computational alignment) — 우리 문제의식과 가장 가까움 |
| `mallick2024taming3dgs.pdf` | 13 | ★ 제한된 자원에서의 3DGS. 예산 제약 서술의 표준 |
| `mallick2024taming3dgs_ko.pdf` | 18 | 위 논문의 한글 번역본. 구조 해부 시 원문과 대조하면 빠름 |
| `lmrs.pdf` | 17 | matrix-free 2차 최적화. 최적화 논문의 유도 서술 방식 참조 |
| `edgs.pdf` | 20 | densification 제거로 수렴 효율화. 예산 관점 보조 |

## 06_ours — 우리 시스템 구성요소

| 파일 | 쪽 | 우리 쓰임 |
|---|---:|---|
| `teed2021droid.pdf` | 15 | DROID-SLAM. §3.2 dense correspondence trajectory filling의 근거 |

## 별도 위치에 둔 것 (옮기지 않음)

용량이 크고 당장 안 쓰므로 원래 자리에 둡니다. 필요해지면 그때 정리합니다.

| 파일 | 위치 | 무엇 |
|---|---|---|
| `merged_original.pdf` | `context/reference/papers/` | **241MB / 255쪽.** floater·local minima 논문 10편 안팎의 합본(StableGS로 시작). 논문 한 편이 아니라 묶음집 |
| `merged_translation.pdf` | 〃 | **431쪽 한글 전문 번역집.** 위 묶음집 전체 번역. C3 관련연구 조사 시 큰 자산 |
| `merged_translation (1).pdf` | 〃 | ⚠ 이름과 달리 번역집이 아니라 **11쪽 연구흐름 리포트** |

## 옮겨온 곳 (2026-09-05)

`~/Documents/논문/`, `~/Documents/논문 작성법/`, `Incremental_mapping/reference/paper/`,
`gs_floaterLab/repos/reference/`, `gs_floaterLab/context/reference/papers/` 에 흩어져 있던 것을
여기로 통합했습니다. 중복 2쌍(vigs-slam 31MB, Taming3DGS 40MB)은 제거했습니다.

이 중 154MB는 **git에 추적되고 있었고**, 이번에 추적을 해제했습니다.
⚠ 다만 **git 히스토리에는 그대로 남아 있어 repo 크기(350MB)는 줄지 않습니다.**
줄이려면 `git filter-repo`로 히스토리를 다시 써야 하는데, 원격과 다른 worktree가 있어
별도 결정 사항으로 둡니다.
