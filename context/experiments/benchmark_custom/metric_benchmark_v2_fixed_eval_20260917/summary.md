# Metric benchmark v2.2 — normalized ERCB vs official vanilla

Predeclared valid inventory: 17 scenes; UTMM slow-straight-1 tracker-ineligible N/A.
Both arms: same frozen tracker, zero-tail, render-matched B-track, 15 s
post-map cooldown and two independent saved-map evaluations. Any >0.01 dB
per-view PSNR disagreement stops the panel; no score is selected by rank.

Exp93에서 확인한 Aria adapter의 RPNG/UTMM `--undistort` 누락을 수정한 뒤
**새 output root·새 source lock**으로 normalized와 official vanilla를 모두
다시 실행했다. 과거 vanilla 평가값은 아래 공식 pair에 사용하지 않았다.
RPNG/UTMM은 distortion-aware evaluator, Aria는 고유 calibration 명령을 쓴다.
15초 cooldown·이중 평가는 추가 일치성 감사이고 GT 전처리 오류의 해결책이
아니다. B-track은 frozen causal tracker를 쓰는 mapping-only fixed-work
비교이며 동시 tracker+mapper의 strict real-time 증거가 아니다.

정규화 potential은 `Phi(n)=Var(n)/mean(n)`이고, per-view Gibbs law는
`p_i ∝ exp[-log(1.5)n_i/(T+1)]`이다. Dense/aux-KF/native-KF에 같은
법칙을 적용하되 기존 block/global no-repeat residue 안에서 조건부로
선택한다. Scene별 온도·phase cutoff는 없으며 `1/(T+1)`을 상쇄하는
재매개변수화도 없으므로 고정-beta raw-variance sampler와 동일하지 않다.

| Dataset | Scene | Normalized PSNR | Vanilla PSNR | ΔPSNR | Renders N/V | Adam N/V | GS N/V | Eval/Fairness |
|---|---|---:|---:|---:|---:|---:|---:|---|
| rpng | table_01 | 25.5814 | 23.9288 | +1.6526 | 38302/38302 | 3030/3027 | 417561/181900 | PASS |
| rpng | table_02 | 23.3877 | 21.1888 | +2.1989 | 53669/53669 | 4229/4231 | 592567/257882 | PASS |
| rpng | table_03 | 23.5555 | 21.8045 | +1.7510 | 85029/85029 | 6724/6706 | 882185/347314 | PASS |
| rpng | table_04 | 22.4018 | 21.2766 | +1.1252 | 67793/67793 | 5359/5343 | 752043/300165 | PASS |
| rpng | table_05 | 22.7893 | 21.7009 | +1.0884 | 52480/52480 | 4135/4138 | 463613/212284 | PASS |
| rpng | table_06 | 24.4731 | 22.6822 | +1.7909 | 34437/34437 | 2714/2719 | 329301/147478 | PASS |
| rpng | table_07 | 26.7596 | 25.2705 | +1.4890 | 33422/33422 | 2691/2680 | 344214/173121 | PASS |
| rpng | table_08 | 23.7932 | 22.1004 | +1.6928 | 94283/94283 | 7465/7436 | 923389/388806 | PASS |
| utmm | ego-centric-1 | 17.7588 | 17.2126 | +0.5462 | 5676/5676 | 466/465 | 78512/81552 | PASS |
| utmm | ego-centric-2 | 19.4922 | 19.2556 | +0.2366 | 6655/6655 | 559/556 | 84368/108200 | PASS |
| utmm | ego-drive | 21.2642 | 20.5606 | +0.7036 | 11226/11226 | 898/900 | 112222/124234 | PASS |
| utmm | fast-straight | 16.3799 | 15.9484 | +0.4315 | 1348/1348 | 172/165 | 21611/33674 | PASS |
| utmm | slow-straight-2 | 17.2234 | 17.3497 | -0.1262 | 1888/1888 | 177/171 | 24366/36708 | PASS |
| utmm | square-1 | 21.2248 | 20.1818 | +1.0430 | 9345/9345 | 757/763 | 119976/149638 | PASS |
| utmm | square-2 | 21.4162 | 20.6307 | +0.7855 | 8277/8277 | 676/679 | 104883/131291 | PASS |
| aria | aria1253 | 25.7757 | 24.0559 | +1.7198 | 13620/13620 | 1055/1071 | 177099/175447 | PASS |
| aria | aria301_305 | 25.1124 | 21.9267 | +3.1857 | 17620/17620 | 1344/1376 | 214288/197515 | PASS |

Completed formal pairs: **17/17**.
Scene-arithmetic mean ΔPSNR: **+1.2538 dB**; wins **16/17**.
Predeclared minimum acceptance: **PASS** (mean ≥+0.5 dB, strict majority positive, all fairness PASS).
Historical R4 stretch target 17/17 and +1.2609 dB: **FAIL**.

| Dataset | Valid scenes | Wins | Mean normalized | Mean fresh vanilla | Mean ΔPSNR |
|---|---:|---:|---:|---:|---:|
| RPNG | 8 | 8 | 24.092696 | 22.494111 | +1.598585 |
| UTMM | 7 | 6 | 19.251358 | 18.734183 | +0.517175 |
| Aria | 2 | 2 | 25.444056 | 22.991317 | +2.452740 |
| **All valid scenes** | **17** | **16** | **22.258188** | **21.004400** | **+1.253787** |

유일한 PSNR 패배는 UTMM `slow-straight-2` **−0.126230 dB**다. 최대
기존 R4 대비 normalized 손실은 RPNG `table_07` **0.080468 dB**여서
사전 `>0.5 dB` 중단선이 한 번도 발동하지 않았다. 추가 목표는 16/17로
17/17에 미달했고, 평균도 +1.2609보다 **0.0071 dB 낮다**. 이 미달을
PASS로 재해석하지 않는다.

검증: 17개 구조 gate 각 12/12, 저장-map 이중 평가 34/34 arm,
render-match fairness 각 10/10, zero-tail, held-out 불교집합, 후보/vanilla
각 scene 동일 physical render를 독립 read-only 감사로 재확인했다.
`audit_exp94_normalized_panel.py --require-complete`는 **17/17·pending 0·
minimum PASS·stretch FAIL**로 exit 0이다. Aria 평가 위임 테스트 2개와
normalized Gibbs log-odds 테스트 3개도 통과했다. Source lock은 runner·
evaluator·mapping harness·Aria adapter 등 17개 파일 해시를 고정한다.

별도 역사적 참고: 과거 R4/vanilla artifact의 평균 이득은 +1.260888 dB,
이번 새 pair는 +1.253787 dB다. 평균 normalized PSNR은 과거 R4보다
0.001030 dB 낮고 새 vanilla는 과거 vanilla보다 0.006070 dB 높다.
이 과거 수치는 새 공식 pair 표에 섞지 않았다.
