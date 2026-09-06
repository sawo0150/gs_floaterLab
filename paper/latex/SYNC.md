# Overleaf 동기화 합의 (2026-09-06)

> 이 파일이 `paper/latex/`의 성격과 Overleaf와의 관계를 규정한다.
> `paper/README.md`의 일반 규칙보다 **이 파일이 우선**한다.

## 합의 사항

1. **Overleaf 프로젝트는 지금 그대로 둔다.** 구조 변경·잔존물 삭제를 우리가 먼저 하지 않는다.
   - 프로젝트: `https://www.overleaf.com/project/6a9c1b93c9b98e33cf8e5770`
   - 공유받은 형태: `CVPR2027_chsong_s_intern.zip` (2026-09-06 다운로드)
2. **로컬 작업 기준은 그 zip이다.** `paper/latex/`는 zip을 푼 것이며, 이후 모든 `.tex` 수정은
   이 트리 위에서 한다. 예전 CVPR author-kit 트리는 아래 "보관"으로 옮겼다.
3. **동기화는 사람이 직접 복사·붙여넣기로 한다.**
   - git remote 연결(Overleaf Git), 자동 push, API 업로드는 **쓰지 않는다.**
   - Claude는 Overleaf에 직접 접근하지 않는다 (403이라 애초에 불가).
4. **로컬 파일은 "Overleaf가 그렇게 되어야 할 모습"으로 유지한다.**
   그래서 파일 하나를 통째로 복사해 붙여넣으면 동기화가 끝나도록 쓴다. 부분 패치를 만들지 않는다.
5. **아직 안 올린 변경은 아래 표로 관리한다.** 붙여넣은 뒤 그 행을 지운다.

## 방향

```
Overleaf  ──(zip 다운로드, 사람)──▶  paper/latex/     ← 초기 1회. 이후 반복하지 않음
paper/latex/  ──(복사·붙여넣기, 사람)──▶  Overleaf     ← 평소 방향
```

선배님들이 Overleaf에서 직접 고치신 게 있으면 **다시 zip을 받아 이 폴더를 덮어쓴다.**
그때 로컬 미반영분이 날아갈 수 있으니, 덮어쓰기 전에 아래 표를 먼저 비운다.

## 아직 안 올린 것

| 파일 | 무엇을 바꿨나 | 올렸나 |
|---|---|---|
| `main.bib` | VIGS-SLAM 참고문헌 30개를 파일 끝에 marker 블록으로 추가 (기존 34개는 그대로 둠) | ☐ |

## 보관

| 위치 | 내용 |
|---|---|
| `paper/notes/archive/latex_authorkit2026_2026-09-05/` | 우리가 먼저 만들었던 CVPR **2026** author-kit 트리. `main.bib`(참고문헌 30개), `sec/*.tex` 스텁, `fig/teaser.tex`, `authorkit_reference/` 포함. 버리지 않는다 |

## 이 프로젝트에 대해 알아둘 것

공유받은 프로젝트는 **논문 초안이 아니라 연구실 템플릿 껍데기**다.
이전 논문(카메라 캘리브레이션, conic moment estimator)을 복사해 제목만 `Real-time GS Mapping`으로
바꾼 상태이며, 본문 내용은 없다 (§1은 `\lipsum` 더미, §2·§4·§5는 `\section{}` 한 줄).

### 선배님 확인이 필요한 것

| # | 항목 | 현재 상태 |
|---|---|---|
| 1 | `cvpr.sty` 교체 | **2024년 판**이다 (`\ProvidesPackage{cvpr}[2024 ...]`, 21,928 B). `\def\confYear{2024}`도 그대로. 우리 보관본은 2026 판(17,969 B). CVPR 2027 키트는 아직 미출시 |
| 2 | review 모드 전환 | 지금 `\usepackage{cvpr}` = **camera-ready**. 줄 번호가 안 나와 서로 코멘트하기 불편하다. `\usepackage[review]{cvpr}`로 바꿀지 |
| 3 | 이전 논문 잔존물 삭제 | `sec/6_conclusion.tex` 본문, `sec/4-1·4-2·4-3_algorithm.tex`(main.tex에서 include 안 되는 고아 파일), `temp.tex`, `note.tex`, `figs/dummy.png`, acknowledgment 과제번호(2020R1C1C1006620 / 2022-0-00480), `main.bib` 앞쪽 34개 엔트리 |
| 4 | 저자 목록 | `main.tex`에 `chaehyeon, leah100, myunghwan.jeon, jongwoo.lim, ayoungk@snu.ac.kr`이 들어 있다. 이전 논문에서 넘어온 것인지 이번 저자인지 |

**확인 전까지 위 4개를 우리가 먼저 손대지 않는다.**

### 우리 구조와의 차이

| | Overleaf | 우리 계획 (`plan/outline/`) |
|---|---|---|
| 절 이름 | `sec/5_results.tex` | §4 Experiments |
| Preliminaries | `% \input{sec/3_preliminary}` — **주석으로 자리만 있음** | §3.0 Overview에 흡수 예정 |
| Limitations | 없음 | §6 독립 절 (미결) |
| teaser | 없음 (§1 안에 `figs/dummy.png`) | `fig/teaser.tex` 분리 |
| supplementary | `sec/7_appendix.tex` (+ 안 쓰이는 `X_suppl.tex`) | `X_suppl.tex` |

`3_preliminary` 슬롯이 비어 있는 것은 우리에게 유리하다 —
`notes/structure_survey/chen2026cover.md`에서 나온 "Preliminaries를 Method에서 떼어 독립 절로 두면
기여 수식의 경계가 절 번호로 보장된다"를 그대로 쓸 수 있다. 주석만 풀면 된다.

### 이 템플릿에서 가져다 쓸 것

- **`rpm_packages/`** — 연구실 매크로. 표기 매크로를 새로 만들지 말고 이걸 쓴다
  (`rpm_math`: `\argmin`/`\argmax` 등, `rpm_acronyms`, `rpm_SIunits`, `rpm_misc`: `\gr{}` = 초록 글씨)
- **`rpm_packages/string-long.bib`** — 저널명 약어. `\bibliography{rpm_packages/string-long,main}`으로 물려 있음
- **theorem 환경** — `definition` / `thm` / `corollary` / `lemma` 가 `preamble.tex`에 이미 선언됨.
  §3.3 Gibbs 유도에 그대로 쓴다
- **`algorithm` + `algpseudocode`** — token admission·ERCB block sampling 의사코드용
- **하이라이트 매크로** — `\hlr{}` 빨강 / `\hlg{}` 초록 / `\hlb{}` 파랑. 서로 코멘트할 때 쓴다

### 주의

- `\TODO`, `\todo`, `\apref`, `\thmref`는 **정의되어 있지 않다.** `preamble.tex`에서 주석 처리됐고
  `rpm_packages/`에도 없다. 쓰려면 먼저 정의해야 한다 (우리 보관본 `main.tex`가 `\TODO`를 쓰고 있었다)
- `\usepackage{kotex}`은 주석 처리 상태 → **한국어는 컴파일되지 않는다.**
  한국어 초안은 `sections/*/draft/`에 md로 쓰고, 이 트리에는 영문만 올린다
