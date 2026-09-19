# 2026-09-18 인턴 발표

10장 / 16:9 / 슬라이드별 시간 합계 300초. 영어 슬라이드, 한국어 구두 설명을 전제로 구성.
원본 reference는 수정하지 않음. 흰 배경, 남색 제목 띠, 회색 본문, 하단 출처를 재현.

## 빌드 및 PDF·렌더링

```bash
cd /home/wosasa/Desktop/Incremental_mapping/gs_floaterLab/context/ppt/ppt0918_internPresentation
python build_ppt.py --render
```

필요 도구: Python python-pptx, Pillow, LibreOffice, Poppler(pdftoppm/pdftotext). 현재 환경에서 사용 가능.
출력: `Internship_20260918.pptx`, 동명의 PDF,
`rendered/slide-01.png`~`slide-10.png`, `rendered/contact_sheet.png`.
PDF는 LibreOffice로 변환하며, 렌더링은 PDF의 모든 페이지를 2배 해상도로 수행.
텍스트와 방법 도식은 편집 가능한 PowerPoint 요소이며, 사진만 비트맵.
Arial은 현재 Linux에서 Liberation Sans로 대체 렌더링된다.
표지 이름은 박상원, 김동휘, 송채현 순서로 같은 크기로 표기하며 Noto Sans CJK KR을 사용한다.
이전 `Chaehyeon_Song_Internship_20260918.*` 파일은 구버전이며 현재 출력 파일을 사용한다.

## 이미지 교체

PPT에서 연한 회색 이미지 자리 도형과 안내 글자를 지우고 사진을 삽입해도 된다.
재빌드하려면 `assets/` 폴더에 아래 파일명을 사용한다. PNG/JPG/JPEG 지원, 종횡비 유지.

| 슬라이드 | 파일명(확장자 제외) | 내용 |
|---|---|---|
| 3 | online_map | 본인 프로젝트의 온라인 지도 또는 데모 프레임 |
| 5 | underoptimized_crop | 최근 관측 영역의 학습 부족 사례 |
| 5 | floater_crop | 실제 floater 확대 이미지 |
| 9 | result_baseline | 같은 시점·같은 시점각의 baseline 결과 |
| 9 | result_proposed | 대응하는 제안 설정 결과 |
| 9 | result_metric | 검증된 핵심 지표. 긴 그래프를 넣으려면 코드에서 영역 높이 조절 |

모든 빈칸의 위치는 `image_slots.json`에도 저장.
9장 수치는 확정 자료가 없어 의도적으로 비웠다. 조건이 다른 과거 숫자를 혼합하지 않는다.
출처: paper/latex/sec/0_abstract.tex, 1_intro.tex, 4_method.tex,
5_results.tex 및 context/STATUS.md. ERCB 시간 그룹/개별 뷰 서술과 Carve/Hit 후보가
초안에 공존하므로 슬라이드는 공통 직관만 표현하며 최종 알고리즘 확정을 주장하지 않는다.
사진 출처는 reference의 기존 크레딧을 유지했고 새 인터넷 이미지를 수집하지 않았다.

## 발표 전 채울 것

- 실제 이미지 6개 자리. 없는 사진은 회색 경계의 빈칸으로 남아 있다.
- 결과 비교에는 dataset, GPU, budget, held-out split, 반복 횟수, 종료 후 추가 학습 여부를 기재.
- 공동 연구에서 본인이 맡은 구현·분석 항목은 역할 확인 후 9장에 추가.
- 9장은 현재 구현 진행 상황과 후속 검증을 표현하며 실시간·수렴·기하 성능 달성을 선언하지 않음.

슬라이드 노트는 제작 메모와 시간 배분만 포함하며 발화용 대본은 작성하지 않았다.
각 장에 자동 전환 시간(10/30/25/30/25/35/35/35/50/25초)을 저장했다.
PowerPoint에서 타이밍 사용을 켜면 합계 5분으로 재생된다. PDF에는 시간 설정이 적용되지 않는다.
동영상은 이번 산출물에 포함하지 않으며, 최종 이미지 삽입 후 PowerPoint에서 무음 영상으로 내보내면 된다.
