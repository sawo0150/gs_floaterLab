# related_work/ — 논문별 읽기 노트

파일 하나 = 논문 하나. 파일명은 `latex/main.bib` 의 **bibkey** 와 같게 한다
(예: `matsuki2024monogs.md`).

버전 폴더가 아니다. 읽으면서 **덧붙이기만** 한다.

## 템플릿

```markdown
# <bibkey> — <제목>

- venue / year / 링크 / 로컬 PDF 경로
- **한 줄 요약:**
- **우리가 가져오는 원리:**
- **우리와 다른 점 (§2에 쓸 대비 문장):**
- **인용 위치:** §2.x, §3.x
- **주의:** (숫자를 인용할 때의 조건, 재현 조건 등)
```

## 우선 읽을 것

`latex/main.bib` 에 22개 항목이 있고 **다수가 서지정보 미확인**(연도/venue/페이지)이다.
인용 전에 반드시 확인할 것. 로컬 PDF는 `context/reference/papers/`.

| 우선 | bibkey | 왜 |
|---|---|---|
| 1 | `vigsslam` | 우리 baseline 그 자체 |
| 1 | `matsuki2024monogs` | §2.1 주 대비 대상, P06 baseline 후보 |
| 1 | `mishchenko2020random`, `shamir2016without`, `ahn2020shuffling` | §3.3의 이론 배경. **보장을 가져오지 않는다**는 선을 정확히 긋기 위해 필요 |
| 2 | `jiang2024fisherrf` | §2.2 대비 (active capture vs arrived-only) |
| 2 | `chen2026cover` | 로컬 PDF 있음 |
| 2 | `fan2024trimgs`, `stablegs` | §2.4, C3 대비 |
| 3 | `sucar2021imap` | loss-guided sampling 대비 |
| 3 | `hoffmann2022chinchilla` | compute-budget 프레이밍 인용 |
