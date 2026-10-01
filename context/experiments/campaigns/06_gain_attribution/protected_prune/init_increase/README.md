# Init 생성량 +25%, opacity0.1, 주기300 (2026-09-28)

사용자 요청: init 개수를 조금 늘리고 현재 pruning 수준으로 비교한다. **모든 장면 공통 생성량1.25배 한 조건**만 추가하며, pruning은 opacity0.1·최근10KF birth보호·주기300 completed renders를 유지한다. 전역 기본 preset은 바꾸지 않는다.

주기300은 아직 실측하지 않았으므로, 세 장면에서 기본init/증가init 두 조건을 새로 실행한다(총6회). 주기150의 기존결과는 참고로만 재사용하며, init증가 효과는 반드시 같은300주기의 기본init과 비교한다. 더많은배율·opacity·보호범위 탐색은 하지 않는다.

- 기본init: downsample multiplier1.0 → init64/regular256.
- 증가init: multiplier0.8 → init51.2/regular204.8 → 생성량약1.25배. 첫지도뿐 아니라 이후매KF birth에도 동일 적용.
- PPM Sobel weighting·causal online-rank2.5/span2·ERVS κ16/τ₀4·3:3:6·영상별Adam·denseRGB·40renders/KF·seed0 고정. Densify/Carve/size-prune/KF-cap/blurOFF,scale projectionON.
- Aria1253,RPNG table_06,UTMM square-1에 같은 값을 사용한다. 장면별조정 없음.
- 같은영상선택·admission·loss/LR·render/Adam총수와prefix·tracker입력·held-out평가조건을 검증한다. Birth candidate/Sobel/시점/초기화flag는 같고 생성량만 배율대로 달라지는지 확인한다. Sampling방식은 같지만 점개수가 바뀌므로 동일점의단순추가집합이라고 주장하지 않는다.
- 보호점삭제0,optimizer정렬,densify금지,prune주기와zero-tail을 검사한다. Held-outPSNR/최종GS/mapper시간으로 비교하며 geometry/live입증은 아니다. 단일seed3개개발장면.
- Runner: `run_protected_prune_comparison.py --cases opacity01 --prune-every-renders 300 --birth-downsample-multiplier {1.0,0.8}`.
- 결과: `results/campaigns/gain_attribution/protected_prune/init_increase300_v1/{aria,rpng,utmm}/{base,increase}/`.

## 실행 및 결과

진행 중. 개별실행기록은 상위 [README](../README.md)에 남긴다.

**2026-09-28 완료:** 6회검증PASS. 같은300주기에서init1.25배ΔPSNR Aria−0.0559/RPNG+0.1434/UTMM+0.1427dB,평균+0.0767dB. 보호점삭제0,공통기본값미채택. [결과](SUMMARY.md).

**2026-09-28 사용자채택:** 직전결과확인후사용자가init1.25배/prune0.1/300설정을채택하도록지시했다. selected_mapping_recipe.json에고정했다. 과거미채택판정은당시기록으로보존한다.
