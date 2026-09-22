# Fig.3 수평선 문헌 시각 검토

원고 통합: 사용자 요청으로 현행 B안을 HumanTeck `paper.tex`의 기존 Fig.2 자리에
설치했다. label `fig:photometric_convergence`, asset `figure/photometric_convergence.pdf`.
캡션은555 held-out 평균·matched total rendering budget·Carve off·상하 이미지·
1400↔2400 최초 도달 정의를 포함한다. 본문 reserved 문장을 실제 photometric 평가
소개로 수정했다. current 캡션·원고 PDF asset 동기화 완료. 정적 참조·순서·PDF hash
검증 통과. TeX compiler 부재와 기존 Carve asset 누락으로 전체 컴파일은 미확인.

최신 사용자 선택: B안(최초 sampled 도달1400↔2400). `VIGS-SLAM best` 문구를
그림에서 삭제하고 캡션에 기준23.28 dB를 명시했다. 끝 PSNR 수치는 넣지 않음.
사용자 요청으로 `figure03/current/`에 고정 이름 SVG/PDF/PNG·캡션·provenance를
모으고 제작 코드의 자동 갱신 및 로컬 AGENTS 규칙을 추가했다.
[현행본](../../../humanteck/sections/02_method/figure03/current/README.md).

추가 제작: 사용자 요청으로 A400/B1000 두 안을 논문용 SVG/PDF/PNG로 출력하고
PDF→PNG 단 폭 검수를 완료했다. 원시28점·내장6이미지 보존. 신규 측정 없음.
[선택안](../../../humanteck/sections/02_method/figure03/output/PEAK_OPTIONS.md).

2026-09-21. 신규 학습·GPU 평가 없음. 사용자가 수렴/가속 논문 figure의 상세 조사와
수평선 선택 판단을 요청했다. HAMMER Fig.5,3DGS-LM Fig.1,Turbo-GS v1 Fig.1/2,
3DGS² Fig.4,Taming3DGS Fig.1의 원문 figure를 실제 이미지로 확인했다.

3DGS-LM의 짧은 가로 시간 괄호가 직접적인 디자인 참고다. HAMMER는
optimization-step 대비 map quality curve를 보여주며 threshold 화살표는 없다.
우리 데이터의 baseline 최고23.281345@2400에 대해 Ours는1400에서23.318603으로
처음 넘지만1600/1800에 재하락한다.2000(23.980361) 이후 저장점에서 기준 이상을
유지한다. 따라서 주 annotation은1400↔2400의1000차이보다2000↔2400의400차이를
권고한다. 후자는 문헌 표준이 아닌 유한 관측열의 사후 비교 규칙이며 캡션에 명시한다.

선택된 frame1420 그림으로 annotation-only SVG/PNG 두 안을 제작했다. 원래 선택본
SVG/PDF는 수정하지 않았다. 원시28점·image6개·source hash 보존 검증.
실제 run의 input prefix가 다르므로 순수 optimizer 인과적 가속 또는 wall time 속도
개선으로 확장하지 않는다.

[상세 문헌 분석·원문 figure·추천 시안·캡션](../../../humanteck/sections/02_method/figure03/analysis/peak_annotation_review/README.md).
