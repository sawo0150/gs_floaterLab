# Fig.3 v2 — 하단 범례·수평선 재검토·crop 후보

2026-09-21. [PNG](../../output/fig3_table06_compact_v2_frame355.png) · [SVG](../../output/fig3_table06_compact_v2_frame355.svg) · [PDF](../../output/pdf/fig3_table06_compact_v2_frame355.pdf)

상단 `RPNG table_06`와 `Frame 355 insets: upper baseline / lower ours`를 삭제했다.
장면·frame·상하 arm 정보는 캡션으로 옮긴다. 범례는 x축 제목 아래에 두었고
Inkscape의 실제 텍스트 경계를 기준으로 그림 전체 폭의 가운데에 정렬했다.
물리 크기는 86.49×46.13 mm로 유지한다. Frame355는 후보 선택 전 임시 inset이다.

## 수평선에 대한 판단

이번 추천본에서는 baseline-final 수평선과 보간 iteration 화살표를 제거했다.
교점 계산 자체는 맞지만 첫 도달이 수렴을 뜻하지는 않는다. Baseline 최종값은
22.68788 dB, 중간 최고값은 약 23.28 dB이며 두 arm 모두 비단조적이다.
이 endpoint 하나를 기준으로 속도 차이를 강조하면 최종값의 하락에 해석이 의존한다.

아래는 **보간하지 않은 저장 checkpoint**의 첫 도달과 마지막 checkpoint까지
모든 후속 표본이 기준 이상인 첫 지점이다. 후자는 이번 데이터의 민감도 진단이며
미래에도 영원히 유지되거나 optimizer가 수렴했다는 뜻이 아니다.

| 기준 PSNR | Ours 첫 도달 | Baseline 첫 도달 | Ours 후속 유지 | Baseline 후속 유지 |
|---|---:|---:|---:|---:|
| 22.0 dB | 1200 | 1200 | 1200 | 1200 |
| 22.5 dB | 1200 | 1400 | 1200 | 2000 |
| Baseline final (22.68788 dB) | 1200 | 2000 | 1200 | 2000 |
| 23.0 dB | 1400 | 2200 | 2000 | 미달 |

**추천:** Fig.3에는 원시 곡선과 동일 iteration의 실제 이미지를 보여주고
`online mapping quality vs. iterations`로 설명한다. 빠른 수렴의 별도 정량 근거가
필요하면 비교 전에 공통 목표 PSNR·최소 유지 기간을 정하고, 여러 목표·장면의
time-to-quality를 함께 보고한다. 같은 입력 prefix/pose와 작업량 조건도 명시한다.
현재 그림에 유리한 threshold를 새로 골라 단일 가속률로 바꾸지 않는다.
Moving average나 누적 최고값으로 비단조성을 숨기면 원래 평가 의미가 바뀐다.

## 확대 후보 다시 보기

기존 48장의 검증된 렌더를 재사용했다. 새 학습·GPU 평가 없음.
이번에는 전체 GT에서 crop 위치를 표시하고 동일 영역을 Baseline/Ours/GT로 나란히
배치했다. 각 frame별 파일에는 800/1400/2600 세 시점이 모두 들어 있다.
확대 이외 화질 보정은 없고 표시 PSNR은 **crop이 아닌 전체 frame** 값이다.

[후보판 1: 1110·685·950·2370](../../candidates/table06_review_v2/candidate_board_1.png) ·
[후보판 2: 905·1630·355·205](../../candidates/table06_review_v2/candidate_board_2.png)

| 후보 | 눈으로 비교할 부분 | 800/1400/2600 전체 frame gap (dB) | 판단 |
|---|---|---|---|
| [1110](../../candidates/table06_review_v2/frame_1110_three_stages.png) | 포스터의 상자 연결선·원형 도형 | +1.03 / +1.29 / +1.99 | 세 시점 비교 우선 후보. 다만 초기 crop 차이는 작음 |
| [685](../../candidates/table06_review_v2/frame_0685_three_stages.png) | 포스터의 선·글자 번짐 | +1.88 / +1.09 / +2.41 | 포스터 대안, 작은 인쇄 크기에서 글자 차이는 제한적 |
| [950](../../candidates/table06_review_v2/frame_0950_three_stages.png) | 의자 등받이 구멍·책상 경계 | +1.44 / +0.46 / +2.79 | 포스터와 다른 소재, 후기 시각 차이가 명확하지만 중기 gap은 작음 |
| [2370](../../candidates/table06_review_v2/frame_2370_three_stages.png) | 의자·체커보드 | +0.15 / −0.22 / +2.86 | 후기 품질에는 적합, 조기 수렴 근거로는 부적합 |

최종 gap만 보면 905/1630도 크지만 Fig.2와 같은 면의 포스터이며 일부 확대 부위는
여전히 차이가 작다. 새 후보를 사용자가 선택하기 전 v2 그림에 임의로 확정하지 않았다.

## 캡션 초안

> Online mapping quality on RPNG table_06. Curves show mean PSNR over 555 fixed
> held-out views as a function of mapping iterations. Insets compare the same
> crop of frame 355 at 800, 1,400, and 2,600 iterations (upper: VIGS-SLAM;
> lower: ours). Curves include mapping and pose-correction effects under a
> matched total rendering budget.

Frame 번호는 후보 확정 뒤 바꾼다. 원고 TeX에는 삽입하지 않았다.
재현 코드는 `scripts/build_table06_layout_v2.py`와 `scripts/review_table06_candidates_v2.py`.
[검증 결과](../../output/qa/table06_v2_validation.json).

## 추가: Fig.2 frame1420 재사용 검토

[1420 세 시점 실제 렌더](../../candidates/table06_review_v2/frame_1420_three_stages.png).
Fig.2와 동일 crop (440,40,564,164)으로 800/1400/2600 checkpoint의 Baseline/Ours/GT를 비교한다.
기존 렌더 PNG를 재사용하고 원본 hash를 확인했다. 신규 학습·평가 없음.
전체 frame PSNR gap은 +0.33/+0.75/+2.69 dB이며 crop PSNR이 아니다.
