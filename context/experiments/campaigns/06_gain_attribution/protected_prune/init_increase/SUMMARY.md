# Init +25% / opacity0.1 / 300-render 주기 — 결과

2026-09-28. **같은 pruning 조건에서 init 생성량을25% 늘리자 RPNG·UTMM은 약0.143dB 개선됐고 Aria는0.056dB 하락했다.** 전장면 공통 이득은 아니므로 기본값은 변경하지 않는다. 사전 지정한 두조건×세장면, 총6회만 실행했다.

## 직접 비교: 같은300주기에서 init만 변경

| 장면 | 기본init PSNR | init1.25배 PSNR | ΔPSNR | 최종GS 기본→증가 | mapper초 기본→증가 |
|---|---:|---:|---:|---:|---:|
| aria | 25.8387 | 25.7828 | -0.0559 | 158,393→195,316 | 33.43→34.65 |
| rpng | 25.0820 | 25.2254 | +0.1434 | 164,895→202,838 | 100.86→105.46 |
| utmm | 22.1295 | 22.2722 | +0.1427 | 98,000→121,363 | 37.45→36.53 |

장면별 PSNR 차이의 단순 평균은 **+0.0767dB**다. 최종GS 합은+23.3%,mapper시간 합은+2.9% 변화했다. 단일실행 시간이므로 작은 차이로 속도 우열을 확정하지 않는다.

## 기존 결과와 연결

| 장면 | pruning OFF·기본init PSNR | 150주기·기본init | 300주기·기본init | 300주기·init1.25배 |
|---|---:|---:|---:|---:|
| aria | 25.9107 | 25.8162 | 25.8387 | 25.7828 |
| rpng | 25.2237 | 25.0709 | 25.0820 | 25.2254 |
| utmm | 22.2231 | 22.1207 | 22.1295 | 22.2722 |

주기만150→300으로 바꾼 차이는 약+0.009~+0.022dB로 작다. Init증가 후RPNG는pruning 없는기본품질을거의회복했고,UTMM은약0.049dB높았다. Aria는pruning없는기본보다약0.128dB낮다. 이 기존조건들은앞선실행을재사용한참고비교다.

## 고정 조건과 실제 생성량

40renders/KF·seed0,opacity0.1·최근10번의비어있지않은KF birth보호,완료render300단위의packet경계prune,zero-tail. PPM Sobel weighting·causal online-rank2.5/span2·ERVS κ16/τ₀4·3:3:6·영상별Adam·denseRGB·scale projection유지. Densify/Carve/크기prune/KF-cap/blur OFF.

전장면 공통 downsample배율만1.0→0.8로변경했다. `pcd_downsample_init`64→51.2,`pcd_downsample`256→204.8이다. 생성량은분모에반비례하므로약1.25배이며,첫초기화와이후매KF에적용한다. PPM선택방식은같지만추가점만동일지도에붙인실험은아니다. 표본수변화로선택점과초기scale도달라질수있다.

| 장면 | 마지막지도세대 생성수 기본→증가 | pruning 횟수(양쪽동일) | training renders / Adam(양쪽동일) |
|---|---:|---:|---:|
| aria | 192,623→240,732 | 13 | 4760 / 4760 |
| rpng | 357,071→446,350 | 27 | 9080 / 9080 |
| utmm | 141,545→176,990 | 12 | 3600 / 3600 |

## 검증과 한계

- 6개실행의held-out독립평가·동일입력/선택/admission/loss/LR/work·birth배율·prune시점·source lock검사가통과했다. 최근보호점삭제0,optimizer state정렬PASS. 마지막지도세대birth−prune=최종GS일치.
- CPU41테스트PASS. 각저장지도2회평가는학습다중seed반복검증과다르다. 세개발장면·단일seed·frozen causal tracker조건이며실시간동시tracking이나floater/geometry개선검증이아니다.
- 증가조건은현재300주기의기본init과직접비교했다. 기존150주기결과와의차이를init증가효과로오해하지않는다.
- 개선이장면별로달라기본preset은미변경이다. 추가배율탐색·장면별튜닝은하지않았다.

## 재현 자료

`results/campaigns/gain_attribution/protected_prune/init_increase300_v1/comparison.json`에통합결과와원본경로가있다. 각`{scene}/{base,increase}/`에명령·설정·source snapshot·평가·독립감사를보존했다.

Runner: `benchmarks/online_gs/campaigns/gain_attribution/run_protected_prune_comparison.py --dataset SCENE --cases opacity01 --prune-every-renders 300 --birth-downsample-multiplier {1.0,0.8}`. 증가조건의baseline-dir은같은scene의`base/opacity01`이다.
