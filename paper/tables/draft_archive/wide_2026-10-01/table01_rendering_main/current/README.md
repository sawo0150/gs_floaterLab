# table01_rendering_main — 빈칸 TeX 초안

2026-10-01. **측정값 없는 DRAFT template**이며 결과 검증을 통과한 최종 표가 아니다. 숫자 측정 칸은 모두 `\textemdash`이고 기존 실험 결과를 가져오지 않았다. 시간 배수·예산·sequence 이름에 포함된 숫자는 계획의 구조 라벨이다.

- [표 TeX](table.tex) / [독립 미리보기 소스](preview.tex) / [PDF 미리보기](preview.pdf) / [첫 페이지 PNG](preview-01.png)
- [Caption](caption.md) / [Provenance](provenance.json)
- 원고용 복사본: [latex/tab/t1_main_draft.tex](../../../latex/tab/t1_main_draft.tex)
- 재생성: `python paper/scripts/build_draft_tables.py`
- labels: `tab:rendering_comparison`, `tab:main`

본문은 전체 폭 `table*` float로 입력한다. 사용 패키지는 `booktabs`이며 `\shortstack`/`\textemdash`는 LaTeX 기본 명령이다.
