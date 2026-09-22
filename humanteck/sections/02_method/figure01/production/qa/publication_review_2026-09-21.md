# Fig. 1 논문 게재 완성도 검토 — 2026-09-21

## 검토 범위와 판단

현재 `current/overview.pdf`를 Poppler로 96dpi·300dpi 전체 렌더링하고, frontend / growth / sampling / map-render / loss의 5개 영역을 별도로 확대해 확인했다. `paper.tex`의 Method·caption, 제작 코드와 provenance도 대조했다. 원본 그림·builder·원고는 수정하지 않았다. 이 기록은 도판 검토이며 새 실험이나 성능 판정이 아니다.

**판단: 전체 구조는 사용할 수 있지만, 현재 상태를 제출용 완성본으로 보기는 어렵다.** 주요 이유는 (1) 실제 지면에서 작은 설명 글자, (2) 기여 간 불균형한 공간 배분, (3) supervision 경로의 모호성, (4) 핵심 알고리즘을 충분히 설명하지 못하는 도식이다. 사수님의 구체적 의도를 전달받은 것은 아니며 아래는 직접 확인한 독립 검토다.

폰트 embedding과 벡터 출력은 정상이다. PDF 텍스트 bbox가 페이지 밖으로 나가는 경우는 없었다. 따라서 문제를 폰트 깨짐이나 파일 출력 실패로 진단하지 않는다. 기존 QA의 export/hash 통과는 도판의 설명력·지면 가독성까지 보증하지 않는다.

## 확인한 수치

- PDF 크기: 180 × 75.37mm. 원고 클래스도 textwidth=180mm이므로 현재 `width=\textwidth`에서는 이 크기에 해당한다.
- SVG text 89개 중 **76개가 7pt 미만**, 26개는 6pt 미만이다. text 객체 단위 집계이며 단어·문자 수 집계는 아니다.
- 최소 글자: 약 **5.06pt**. `Selected camera`·`Selection history` 등 19-unit 라벨은 약 **5.34pt**, 대표 설명 23-unit은 약 **6.47pt**다.
- 큰 열 제목은 약 10.12pt. 기여 제목은 (a) 9.56pt, (b) 9.00pt, (c) 7.31pt로 일관되지 않다.
- `Fewer selections → higher probability`의 글자 bbox 아래 페이지 여백은 약 **0.87mm**다. 잘리지는 않지만 하단이 빽빽해 보인다.
- Growth의 작은 사진은 약 **6.71 × 5.45mm**. 비슷한 실내 사진이 반복돼 지면에서는 영상 차이보다 배지와 테두리만 눈에 들어온다.
- 96dpi 미리보기는 축소 시 판독성 점검용이다. 모니터의 실제 크기·배율을 보정한 실물 인쇄 검수는 아니며, 논문 전체 컴파일도 수행하지 않았다.

## P0 — 다음 수정에서 먼저 해결

- [ ] **글자 크기를 확보하도록 정보량을 줄인다.** 현재는 사진·설명·화살표를 모두 보존한 채 높이를 줄인 결과 보조 정보가 작고 하단이 밀집했다. 반복 사진·중복 문구를 덜어낸 뒤 핵심 라벨 8–9pt, 필요한 보조 라벨 7pt 이상을 작업 목표로 삼는다. 이는 본 검토의 권장 목표이며 제출처 규정이라는 뜻은 아니다. 전체 확대만으로 해결하면 지면을 과도하게 쓴다.
  - 완료 기준: 180mm 폭에서 확대 없이 세 기여 제목·입출력·핵심 라벨을 읽을 수 있고, 의도적으로 남긴 작은 예외를 설명할 수 있다.

- [ ] **세 기여의 시각적 위계를 맞춘다.** 큰 배경 열 제목이 가장 강하고, Growth의 3행 반복 사진이 많은 공간을 쓴다. 반면 본문 핵심 기여 Carve는 오른쪽 맨 아래 작은 박스에 있다. (a)/(b)/(c)의 제목 크기·굵기·여백 규칙을 통일하고 Carve의 설명 공간을 늘린다. 기존 frontend/base loss는 보조 수준으로 낮춘다.
  - 완료 기준: 빠르게 훑어도 세 기여가 동등한 단계로 보이고, (c)가 보조 주석처럼 보이지 않는다.

- [ ] **depth와 normal의 supervision 경로를 구분한다.** 현재 왼쪽 두 prior의 선이 하단에서 합쳐지고, 같은 선이 Base supervision과 Carve로 분기한다. 그림만 보면 normal도 Carve의 직접 입력으로 읽힐 수 있다. `depth → Base + Carve`, `normal → Base`를 명시하거나, 묶인 geometry port를 쓸 경우 Carve 분기에 `depth only`를 표시한다.
  - 완료 기준: 각 loss가 어떤 관측을 받는지 선을 따라 한 가지로 해석된다. normal에 관한 구현을 새로 가정해 화살표를 추가하지 않는다.

- [ ] **Carve 도식을 본문의 동작과 대응시킨다.** 본문은 불확실성·표면 주변 margin·opacity에 대한 직접 압력을 설명한다. 현재 작은 색 띠는 의미가 쓰여 있지 않고, free-space 안 여러 Gaussian 중 빨간 하나만 아래 화살표를 받아 왜 그것만 억제하는지 불명확하다. 카메라–깊이 D, penalized free space, 보호/불확실 구간을 구분하고 `α↓`는 투명도 변화로 표현한다. 위치를 아래로 이동시키는 화살표로 오독되지 않게 한다.
  - 완료 기준: 어디를 억제하고 어디를 보호하는지, 무엇이 변하는지(α)가 도식만으로 읽힌다. 정확한 경계식은 실제 채택 구현을 확인한 뒤 사용한다. `Verified`의 검증 조건이 없다면 `Available keyframe depth` 등 확인 가능한 표현으로 바꾼다.

- [ ] **Sampling의 비복원 선택과 연속 update를 실제로 보여준다.** 현재 `Sample without replacement` 아래에는 K3 한 장만 있어 본문의 “서로 다른 K개를 뽑아 다음 K회 update에서 한 번씩 사용”을 시각적으로 설명하지 못한다. 작은 선택 큐 또는 연속 update 예시를 추가하고, 중복이 없는 범위가 한 묶음임을 표시한다.
  - 완료 기준: 동시 multi-view update나 영구 재선택 금지로 오해되지 않는다. 기존 `One view / update` 의미를 유지한다. K를 keyframe 배지와 선택 개수에 중복 사용한다면 표기를 구분한다.

- [ ] **Sampling feedback의 도착점을 count 갱신으로 명확히 한다.** `Selection history` 선은 상단 빈 공간에서 끝나 실제로 어느 상태가 갱신되는지 모호하다. 선택된 view의 누적 횟수 갱신을 count에 연결한다. `Earlier/Later admitted`는 현재 예시에서 count와 일대일처럼 보이므로, 선택 확률의 직접 원인이 admission 시간 자체가 아니라 누적 선택 횟수임을 우선 표현한다.
  - 완료 기준: `count → probability → selection → count` 순환과 Growth의 completed-update feedback이 서로 구별된다. 확률 막대가 실측 결과가 아닌 예시라는 설명을 유지한다.

## P1 — 전체 구도와 시각 자산 정리

- [ ] **Growth를 적은 반복으로 설명한다.** 현재 입력 필름 5장과 Growth 3+4+5장이 반복된다. 첫 pool과 추가되는 카드, 또는 3→4→5의 간결한 상태 전이로 보존·추가를 설명하는 안을 검토한다. `S, S+κ, S+2κ`에서 S가 무엇인지 불명확하므로 completed-update count의 기준 기호를 정의하거나 `+κ updates → +1 arrived view`로 직접 표시한다.
  - 완료 기준: 기존 view 보존, 도착한 후보만 admission, κ update당 추가라는 세 사실이 유지된다. 그림을 간소화하며 causal 조건을 잃지 않는다.

- [ ] **연결선을 포트 중심으로 재배치한다.** prior가 그림 최하단을 길게 돌아가고, 선택 결과의 camera/RGB 분기가 패널 경계의 평행선에 섞여 있다. `Priors` 라벨은 파란 RGB 입력선과 가까워 어느 선의 라벨인지 바로 읽히지 않는다. RGB와 pose 출력을 명명하고, 관련 loss 가까이에 prior 입력 포트를 둔다. 실제 분기는 점으로, 비연결 교차는 동일 규칙의 틈으로 처리한다.
  - 완료 기준: 긴 선을 왕복 추적하지 않고도 각 입력·출력이 보인다. 실선 데이터와 점선 scheduling feedback의 의미를 짧은 범례나 caption에 적는다.

- [ ] **Shared map을 전체 지도와 cutaway의 관계가 보이게 표현한다.** 현재 흐릿한 절단 가장자리와 어두운 바닥이 두드러지고, `C07 region`은 독자에게 의미 없는 내부 후보 ID다. 또한 절단 지도 아래 Render가 있어 그 부분 지도에서 C10 렌더를 만든 것처럼 읽힐 수 있다. 내부 ID는 provenance로 옮기고, shared map의 표시용 inset/cutaway임을 명확히 한다.
  - 완료 기준: map 데이터와 표시용 cutaway를 혼동하지 않는다. 데이터의 geometry·opacity를 미관 때문에 고치지 않는다. 필요하면 같은 지도에서 구조가 읽히는 다른 표시 시점이나 간결한 map 아이콘을 검토한다.

- [ ] **Normal 예시의 역할과 명칭을 수정한다.** 현재 rendered normal은 강한 고주파 색 변화 때문에 작은 크기에서도 시선을 빼앗는다. 코드상 rendered depth에서 계산한 normal이므로 `Depth-derived normal`이 더 정확한 명칭이다. 큰 원본으로 modality/pose/좌표계를 확인한 뒤, 실제 분포를 유지하는 축소 표시 또는 전체 modality에 동일한 crop을 적용하는 안을 검토한다.
  - 완료 기준: normal이 도판의 시각적 중심이 되지 않으며 RGB/depth와 대응한다. smoothing·재색칠로 결과를 좋게 보이게 하지 않는다. 공간이 부족하면 별도 thumbnail을 줄이고 depth→normal 연산 기호로 표현할 수 있다.

- [ ] **Frontend의 역할을 간결하고 정확하게 표시한다.** 본문 입력은 RGB+IMU인데 그림에는 RGB만 있다. IMU 입력을 짧게 추가하고, pose가 rendering camera 및 초기화에 쓰인다는 관계를 명료하게 한다. 실제 trajectory 그림의 배경 점·frustum·start/end는 핵심 기여에 비해 많은 공간을 쓰므로 필요한 수준으로 축약한다.
  - 완료 기준: 시스템 입력과 frontend 출력이 본문과 맞는다. 실제 pose를 유지하되 전체 시퀀스 trajectory가 현재 streaming 시점의 스냅샷이라는 인상을 주지 않는다.

- [ ] **제목과 용어를 본문·caption과 통일한다.** 그림의 `(c) Ray-space geometry supervision`, 본문의 `Causal Free-Space Carve Loss`, caption의 `Carve`를 연결해야 한다. (a)/(b)도 약칭과 정식 명칭의 대응을 한 번에 확인할 수 있어야 한다. 본문 contributions의 `ERCB`와 abstract/Method의 `ERVS` 불일치도 최종 원고 점검 항목으로 넘긴다.
  - 완료 기준: 독자가 Fig. 1(a–c)와 해당 Method 단락을 바로 대응시킨다.

## P2 — 출판용 마감

- [ ] **장식·색·선 규칙을 줄인다.** 필름 천공, 다수의 rounded badge, 배경·막대 gradient, 굵은 설명 문장, 여러 색의 camera/화살표가 한 화면에 경쟁한다. 세 기여의 accent와 기본 정보의 중립색을 정하고 제목·배지·화살촉·테두리의 크기를 통일한다. 색은 기능을 구분하는 데 사용하고 강조 수단을 중복하지 않는다.
- [ ] **하단 안전 여백과 블록 정렬을 회복한다.** Sampling 결론문과 `Verified keyframe depth`가 바닥에 붙어 있다. 글자·선에 최소 1.5–2mm 정도의 여백을 작업 목표로 두고, 사진/배지 baseline·render modality 간격·loss 입력 포트를 공통 grid에 맞춘다. 필요하면 높이 75.37mm 고정을 완화하되 먼저 반복 정보를 줄인다.
- [ ] **Caption과 실제 사용 자산의 의미를 함께 검수한다.** map은 Carve-off 예시이고, pool/count/ray는 schematic이라는 사실을 유지한다. 방법 개념도에서 이 출처를 사용할 수 있지만 complete-method 결과처럼 보이게 만들지 않는다. 효과 증거는 별도 실험 figure가 담당한다. `overview_insert.tex`와 원고의 짧은 caption 중 실제 삽입되는 원고를 기준으로 확인한다.
- [ ] **최종 지면 검수를 통과시킨다.** 그림 PDF만 확인하지 말고 본문·caption이 포함된 180mm 폭 조판을 확인한다. PDF→PNG 전체 및 확대 재검수, font embedding, 문자 잘림, grayscale 구분, RGB/depth/normal 대응, 선의 source–destination을 재확인한다. 벡터·실제 이미지 혼합은 유지하되 중복 내장 이미지와 11.6MB PDF 크기는 품질 손실 없는 최적화 가능성을 확인한다.

## 권장 수정 순서

1. 세 기여와 필수 연결만 남긴 간단한 레이아웃을 먼저 만든다. Growth 반복을 줄이고 Carve 공간을 확보한다.
2. depth/normal 분기, sampling 묶음/feedback, Carve 불확실 구간을 정확하게 설계한다.
3. 정해진 슬롯에 현재의 실제 자산을 배치하고 map/normal/trajectory의 표현 밀도를 조절한다.
4. 180mm 폭에서 글자 크기와 여백을 맞추고 논문 caption을 포함해 확인한다.

**권고:** 현재 3열 구도와 실제 자산은 재사용하되, 화살촉 몇 개와 폰트만 손보는 수준보다 정보 배분을 한 번 다시 잡는 편이 적절하다. 사수님의 코멘트를 특정 요소 하나의 취향 문제로 단정하지 않는다.

## 재현 가능한 검토 근거

- 원본: `production/current/overview.pdf` 및 `overview.svg`.
- 본문: `humanteck/HumanTeck_Song_s_intern/paper.tex`, `humantech.cls`.
- 임시 검수 렌더: `tmp/pdfs/fig1_review_20260921/`의 전체 2개, 영역 5개, text bbox XML.
- 폰트 크기: SVG font-size × (PDF width 510.236pt / SVG viewBox width 1815).
- source PDF와 기존 실험 데이터는 변경하지 않음. 기존 worktree 수정도 유지함.
