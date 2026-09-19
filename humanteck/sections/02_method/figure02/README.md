# Fig. 2 — RGB 정성 비교 준비

구조 시안과 실제 실험 결과를 분리한다. 생성 이미지는 배치 검토용이며 성능 근거로 사용하지 않는다.

## 최신 결과 — F04 선택 및 Fig. 2 제작

사용자가 F04를 선택했다. [제작본 PNG](output/rgb_comparison.png), [PDF](output/pdf/rgb_comparison.pdf), [SVG](output/rgb_comparison.svg)를 출력했고 원고의 Fig. 2 파일 경로에도 반영했다. [제작·검수 기록](output/README.md).

아래는 후보 선정 전 논의 기록이다.

## 이전 검토 — 후보 미선정 단계

사용자 피드백에 따라 **PSNR 차이가 큰 장면 선택보다 Introduction의 motivation과 contribution을 보여주는 관찰 대상을 먼저 정한다.**

- [주장·기여·증거·ROI 선정 기준](analysis/motivation_and_layout_revision_2026-09-20.md): Fig. 2는 제한된 training-render 예산에서 확보한 appearance 품질, 별도 geometry 그림은 Carve의 기하 효과를 담당한다.
- [가로형 mockup v02](mockup/layout_v02.png): 약 2.8:1, 세 패널 내 확대 inset과 점선 연결. Full view / Detail 행을 없앴다. Built-in imagegen으로 기존 시안을 수정했다. [실제 사용 프롬프트](mockup/prompt_v02.md).
- v02는 구도 검토용이다. 생성 과정에서 작은 ROI는 서랍 세 칸, 확대창은 두 칸을 담아 정확한 crop 대응이 어긋났고 연결선 끝점도 최종 정렬이 필요하다. 실험 결과로 사용하지 않으며, 실제 제작은 동일 crop 좌표와 벡터 연결선으로 맞춘다. 후보 미선정 상태에서 실제 데이터의 최종 figure를 만들지 않았다.
- 이전 후보 추천은 provisional이다. F04 등을 확정하지 않고 본문의 주장과 GT 일치, 인쇄 크기에서의 판독성을 기준으로 다시 검토한다.

## 먼저 볼 파일

1. [GPT 생성 구조 시안](mockup/layout_v01.png): 세 열(VIGS-SLAM / Ours / GT), 위 전체 영상 / 아래 동일 영역 확대. built-in imagegen으로 생성한 배치 검토용이며, 세 열에 같은 가상 장면을 넣어 성능 차이를 꾸며내지 않았다. [생성 프롬프트](mockup/prompt_v01.md).
2. [실제 후보 24개 목록](candidates/README.md): 개별 확대 카드와 PSNR 표.
3. 실제 영상 모음판: [F01–F04](candidates/contact_sheet_01.png) · [F05–F08](candidates/contact_sheet_02.png) · [F09–F12](candidates/contact_sheet_03.png) · [F13–F16](candidates/contact_sheet_04.png) · [F17–F20](candidates/contact_sheet_05.png) · [F21–F24](candidates/contact_sheet_06.png).
4. [논문 참고 도판과 구성 분석](references/README.md), [선정 기준·검수·비교 조건](analysis/selection_notes_2026-09-20.md).

## 우선 추천

| 후보 | 장면 / frame | 영상별 PSNR 개선 | 볼 부분 |
| --- | --- | ---: | --- |
| [F04](candidates/F04_comparison.png) | RPNG table_06 / 1420 | +5.13 dB | 포스터 글자·로고. Fig. 2 첫 후보로 추천. |
| [F07](candidates/F07_comparison.png) | RPNG table_08 / 425 | +4.43 dB | 반복 격자와 경계. |
| [F09](candidates/F09_comparison.png) | RPNG table_03 / 4070 | +4.13 dB | 테이블·천 무늬·바닥. 현재 확대 영역은 바닥. |
| [F14](candidates/F14_comparison.png) | UTMM square-1 / 1265 | +3.64 dB | 금속 구조와 창틀. 다른 데이터셋 후보. |
| [F01](candidates/F01_comparison.png) | Aria301_305 / 1220 | +11.71 dB | 가장 큰 개선. 다만 벽·천장 비중이 큼. |

**후보는 모두 Carve off**이므로 RGB 재구성 비교로 한정한다. 개선이 큰 시점을 의도적으로 선택했으며 위 수치는 장면 평균이 아니다. 현재 자동 ROI는 최종 결정이 아니므로, 사용자가 F 번호를 고른 뒤 확대 위치를 함께 확정한다.

## 폴더 구성

- `mockup/`: imagegen 배치 시안과 프롬프트
- `references/`: 참고 논문 정성 비교 도판·출처·구성 분석
- `candidates/`: 실제 Vanilla/Ours/GT 비교판과 개별 영상
- `analysis/`: 전체 비교 쌍·held-out 시점의 PSNR 차이 순위와 선택 기록
- `scripts/`: 후보 선별·실제 지도 렌더·비교판 생성 코드

첫 검토는 현재 논문 주 비교와 대응하는 exp94의 Aria·RPNG·UTMM 전체 17장면을 대상으로 한다. 과거 실행도 살펴보되 evaluator 오류를 정정하기 전 결과나 다른 예산의 run을 현재 baseline과 섞지 않는다. 같은 장면 내에서는 PSNR 차이가 큰 held-out 영상을 우선하되 가까운 시점의 중복을 줄인다. 선정 영상은 의도적으로 개선이 큰 사례이며 평균적인 성능을 대표한다는 주장은 하지 않는다.
