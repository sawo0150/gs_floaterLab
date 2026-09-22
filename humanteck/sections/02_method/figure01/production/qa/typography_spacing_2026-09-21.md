# 제목 위계·설명 크기·오른쪽 공간 정리 — 2026-09-21

## 사용자 요청 반영

- (a)/(b)/(c) 제목을 SVG 32-unit = 180mm 지면 기준 **9.00pt**로 통일. (c)는 `Free-Space Carve Loss`로 간결하게 표시한다.
- 일반 설명 글자를 최소 25-unit = **7.03pt**로 확대. 렌더 modality 라벨은 세 문구 사이 간격을 확보하도록 Regular 24-unit = **6.75pt**, K/I identity 배지는 기존 Bold 23-unit = **6.47pt**를 사용한다. 이전 5pt대 설명은 남기지 않는다.
- `Depth-derived normal` → 사용자 요청 문구 **`Rendered normal`**. 실제 normal asset이나 계산 방식은 바꾸지 않았다.
- Shared Gaussian map의 제목·이미지, Render, modality 행을 **38-unit / 약 3.77mm 위로 이동**. 지도 이미지 크기와 종횡비는 유지했다.
- Base supervision을 위로 옮기고 행간을 넓혔으며 Carve 박스는 170→192-unit 높이로 확장해 제목·free-space 설명의 간격을 확보했다.
- 큰 글자에 맞춰 Growth subtitle, update 간격 라벨, count 숫자, probability 숫자 및 축/배지 간격을 조정했다. Count/probability 값과 막대 상대 높이는 유지했다.
- 전체 180×75.37mm, 세 열, 괄호 중심 연결, 실제 이미지·궤적·ray 표현 유지. 원고용 overview.pdf도 갱신.

## 검수

- 처음 확대 렌더에서 커진 렌더 라벨이 붙어 읽히는 문제를 확인했다. Regular 스타일·간격·24-unit 크기로 조정했다.
- 제목과 Growth subtitle, Sampling 제목과 count 숫자의 글자 경계가 겹치는 부분을 발견해 행간을 조정했다.
- PDF 전체와 영역 확대본을 직접 확인했다. 최종 word bbox의 가로·세로 중첩이 모두 0.25pt를 넘는 쌍 0개, 페이지 밖 단어 0개. 사용 폰트 전부 embedded, 원고 PDF 일치, 원본 자산 SHA256 및 SVG 내장 이미지 25개의 바이트·반복 횟수 동일성 확인. Python AST/SVG parse 및 diff whitespace 검사 통과.
- 모든 업데이트는 기존 `build_overview_v02.py`의 diff다. GPU·추가 학습·원본 이미지 편집 없음.
- 직전 source 및 결과는 `archive/before_type_spacing_2026-09-21/`에 보존했다. 전체 원고 컴파일·실물 인쇄는 수행하지 않았다.
