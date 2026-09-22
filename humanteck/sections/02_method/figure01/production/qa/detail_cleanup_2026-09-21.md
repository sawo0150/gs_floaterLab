# Fig. 1 상세 배치 정리 — 2026-09-21

사용자 요청: 실제 겹침과 어색한 연결을 정리하되 디테일은 유지한다. 묶음 괄호의 중앙 끝이 다음 단계를 가리키는 경우 화살표를 덧붙이지 않는다. 기존 builder를 diff로 수정하고 직전 current/scripts/qa/README를 `archive/before_detail_cleanup_2026-09-21/`에 보존했다.

## 반영

- `Arrived views` 문구 제거, K/I 범례를 분리 정렬. 입력 묶음 괄호의 끝이 frontend를 가리키도록 배치하고 기존 ㄴ자 화살표 제거.
- RGB stream에서 View Growth의 첫 pool 사진으로 짧은 수평 연결. 초기화 경로와의 교차에는 비연결 틈을 둠.
- 외곽 `Completed updates` 점선 제거. Growth 두 전이에 `+κ updates`를 배치해 completed-update 간격 의미를 유지.
- Growth 아래 괄호의 추가 화살촉 제거.
- `Sample without replacement`, `One view / update`, `Earlier admitted → Later admitted` 제거. 이들 중 알고리즘 관련 설명은 기존 본문·caption에 유지.
- `Lower count → higher probability`를 막대그래프 폭에 맞춰 중앙 정렬. history feedback은 선택된 K3의 count 6을 가리킴.
- `C07 region · cutaway visualization` 문구 제거. cutaway 출처와 해석 제한은 caption/provenance에 유지.
- Render 아래 개별 분기 및 depth→normal 화살표 제거. 세 modality를 정렬하고 아래 괄호로 Base supervision에 연결. normal 이름은 실제 생성 방식에 맞춰 `Depth-derived normal`로 변경.
- Priors/RGB의 라벨과 평행선 간격, Base supervision의 두 줄 간격, Map objective 원 안의 세 줄 간격을 추가 조정.

## 유지

- 180×75.37mm 크기, Times New Roman, 3열 구성, Growth 3→4→5 상태, K/I identity.
- 기존 25개 삽입 이미지의 바이트와 반복 사용 횟수, 크롭 비율·색상, 실제 trajectory·지도·RGB/depth/normal 자산.
- Count 12/9/6/3/0와 probability 10/14/18/25/33, ray 도식과 opacity 억제 표현.
- 데이터·학습·GPU 렌더·원본 지도 변경 없음. 그림 재조립과 CPU PDF 렌더만 실행.

## 검수

- PDF를 다시 PNG로 렌더링해 전체 및 frontend/sampling/loss/initialization/map의 확대본 확인.
- 첫 렌더의 Priors 라벨과 괄호 간섭, 다음 렌더의 Priors/RGB 및 Base supervision 행간을 확인해 재조정.
- SVG XML/Python AST, 이미지 SHA256, 삭제 문구 부재, PDF 문자 bbox와 font embedding 검사.
- 최종 PDF의 word bbox 간 가로·세로 중첩이 모두 0.25pt를 넘는 쌍 0개, 페이지 밖 단어 0개. 이는 글자 경계 검사이며 선·괄호 접촉은 확대 렌더로 별도 확인했다. Times New Roman 사용 폰트 전부 embedded. 수정 전후 SVG의 내장 이미지 바이트 및 반복 횟수(25개) 동일.
- 현재 SVG/PDF/PNG와 원고 `humanteck/HumanTeck_Song_s_intern/figure/overview.pdf` 동기화. 전체 원고 컴파일·실물 인쇄 검수는 수행하지 않음.
- `qa/detail_cleanup_before_after.png`와 `qa/arrows/`에 같은 크기 비교 및 영역 확대본 저장.

이번 변경은 사용자가 특정한 도판 상세 수정이다. 이전 publication review의 모든 방법론·가독성 제안이 완료됐다는 판정은 아니다.
