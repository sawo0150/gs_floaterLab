# Fig. 3 실제 데이터 후보

## 실측 중간 map 기반 3개 선택안

[A:1180 / B:1220 / C:980 도판](../output/README.md)을 제작했다.
`convergence_insets/frame_*/`에는 실제 600/1000/1300-step 렌더와 GT가 있다.
세 도판 모두 고정 held-out 539뷰의 동일 곡선을 사용하며, 후반 pose correction의 영향도 포함한다.

## 선정 당시 추천 — 최종 PSNR 차이 우선 재검토

**Aria aria301_305 / frame 1180**: 전체 view PSNR 21.68 → 33.15 dB (+11.47).
기존 endpoint의 장면 전체 held-out 평균 차이는 +3.19 dB다. 이후 중간 곡선을 실측했으며
새 pair의 최종 차이는 +3.24 dB다. 아래 자료는 후보 선정 당시 기록이다.

- [실제 확대 비교판: 1180 / 980 / 1220](high_gain_review/high_gain_comparison.png)
- [편집 가능한 SVG](high_gain_review/high_gain_comparison.svg)
- [선정 근거·run·중간 checkpoint 후보](../analysis/high_gain_selection_2026-09-21.md)
- [추가 4view의 실제 렌더링 출처·PSNR 검증](high_gain_review/manifest.json)

## 이전 추천 — 초반 관측 편의성 중심

기존 실제 endpoint 이미지에서 선정한 잠정 후보다. 중간 곡선·checkpoint 렌더링은 아직 없다.

| 순위 | 장면 / 평가 frame | 실제 비교판 | 확대 대상 |
|---|---|---|---|
| 1 | table_01 / 330 | [F18](../../figure02/candidates/F18_comparison.png) | 테이블 천 무늬 |
| 2 | table_06 / 1420 | [F04](../../figure02/candidates/F04_comparison.png) | 포스터 로고·인쇄 패턴 |
| 3 | table_08 / 425 | [F07](../../figure02/candidates/F07_comparison.png) | 테이블 경계·무늬 |

- [선정 근거·run·checkpoint 계획](../analysis/scene_frame_selection_2026-09-21.md)
- [기계 판독용 출처 목록](shortlist_2026-09-21.json)

기존 원본 이미지는 figure02에 보존하고 링크로 참조한다. imagegen 시안은 `../mockup/`에 보관한다.
