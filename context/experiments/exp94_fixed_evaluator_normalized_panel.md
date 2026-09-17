# exp94 — evaluator 계약 수정 후 normalized-vs-vanilla B-track

- 날짜: 2026-09-17
- 상태: 17/17 pair 완료·16승 1패; 사전 최소 성공 기준 PASS, R4 추가 목표 FAIL
- runner: `benchmarks/online_gs/run_exp94_normalized_metric_v2_fixed_eval.py`
- 결과 표: [metric benchmark v2.2 summary](benchmark_custom/metric_benchmark_v2_fixed_eval_20260917/summary.md)
- raw output: `results/experiments/exp94_normalized_metric_v2_fixed_eval/`

Exp93에서 찾은 혼합-inventory 평가 명령 오류를 수정하고, 17개 scene의
RPNG/UTMM `--undistort`와 Aria 전용 명령을 사전 검사한 뒤 **새 output root와
source lock**으로 시작했다. 이전의 잘못된 PSNR이나 vanilla run은 pair에
재사용하지 않는다. Selector 법칙은 `Phi=Var(count)/mean(count)`가 유도하는
per-view Gibbs `p_i∝exp[-log(1.5)n_i/(T+1)]`이며 scene별 knob/cutoff 없음.

| Scene | Normalized | Official vanilla fresh | ΔPSNR | Renders N/V | Adam N/V | GS N/V | 검증 |
|---|---:|---:|---:|---:|---:|---:|---|
| RPNG `table_01` | 25.581416 | 23.928826 | **+1.652589** | 38,302/38,302 | 3,030/3,027 | 417,561/181,900 | 구조 12/12, 이중 평가, pair fairness PASS |
| RPNG `table_02` | 23.387709 | 21.188828 | **+2.198881** | 53,669/53,669 | 4,229/4,231 | 592,567/257,882 | 구조 12/12, 이중 평가, pair fairness 10/10 PASS |
| RPNG `table_03` | 23.555496 | 21.804534 | **+1.750962** | 85,029/85,029 | 6,724/6,706 | 882,185/347,314 | 구조 12/12, 이중 평가, pair fairness 10/10 PASS |
| RPNG `table_04` | 22.401817 | 21.276622 | **+1.125194** | 67,793/67,793 | 5,359/5,343 | 752,043/300,165 | 구조 12/12, 이중 평가, pair fairness 10/10 PASS |
| RPNG `table_05` | 22.789282 | 21.700924 | **+1.088358** | 52,480/52,480 | 4,135/4,138 | 463,613/212,284 | 구조 12/12, 이중 평가, pair fairness 10/10 PASS |
| RPNG `table_06` | 24.473087 | 22.682196 | **+1.790892** | 34,437/34,437 | 2,714/2,719 | 329,301/147,478 | 구조 12/12, 이중 평가, pair fairness 10/10 PASS |
| RPNG `table_07` | 26.759564 | 25.270524 | **+1.489040** | 33,422/33,422 | 2,691/2,680 | 344,214/173,121 | 구조 12/12, 이중 평가, pair fairness 10/10 PASS |
| RPNG `table_08` | 23.793198 | 22.100431 | **+1.692767** | 94,283/94,283 | 7,465/7,436 | 923,389/388,806 | 구조 12/12, 이중 평가, pair fairness 10/10 PASS |
| UTMM `ego-centric-1` | 17.758819 | 17.212576 | **+0.546243** | 5,676/5,676 | 466/465 | 78,512/81,552 | 구조 12/12, 이중 평가, pair fairness 10/10 PASS |
| UTMM `ego-centric-2` | 19.492180 | 19.255612 | **+0.236568** | 6,655/6,655 | 559/556 | 84,368/108,200 | 구조 12/12, 이중 평가, pair fairness 10/10 PASS |
| UTMM `ego-drive` | 21.264177 | 20.560581 | **+0.703596** | 11,226/11,226 | 898/900 | 112,222/124,234 | 구조 12/12, 이중 평가, pair fairness 10/10 PASS |
| UTMM `fast-straight` | 16.379936 | 15.948413 | **+0.431523** | 1,348/1,348 | 172/165 | 21,611/33,674 | 구조 12/12, 이중 평가, pair fairness 10/10 PASS |
| UTMM `slow-straight-2` | 17.223444 | 17.349673 | **−0.126230** | 1,888/1,888 | 177/171 | 24,366/36,708 | 구조 12/12, 이중 평가, pair fairness 10/10 PASS; PSNR 패배 |
| UTMM `square-1` | 21.224773 | 20.181777 | **+1.042996** | 9,345/9,345 | 757/763 | 119,976/149,638 | 구조 12/12, 이중 평가, pair fairness 10/10 PASS |
| UTMM `square-2` | 21.416180 | 20.630652 | **+0.785529** | 8,277/8,277 | 676/679 | 104,883/131,291 | 구조 12/12, 이중 평가, pair fairness 10/10 PASS |
| Aria `aria1253` | 25.775702 | 24.055908 | **+1.719794** | 13,620/13,620 | 1,055/1,071 | 177,099/175,447 | 구조 12/12, 이중 평가, pair fairness 10/10 PASS |
| Aria `aria301_305` | 25.112411 | 21.926725 | **+3.185685** | 17,620/17,620 | 1,344/1,376 | 214,288/197,515 | 구조 12/12, 이중 평가, pair fairness 10/10 PASS |

Normalized 저장 map의 두 평가는 exact **25.581416/25.581416 dB**이고
기존 R4 25.624315와의 차이는 **−0.042900 dB**로 사전 급락 중단선
`−0.5 dB`를 넘지 않았다. 두 arm 모두 동일 frozen causal tracker와 fixed
held-out, zero-tail, 38,302 physical training render를 사용했다. Adam step은
역할별 render 구성 때문에 3,030/3,027로 다르며 동일 step 수라고 주장하지
않는다. 공식 비교값은 이 새 vanilla와의 pair 검증을 통과한 수치다.

`table_02` 역시 normalized 이중 평가 exact **23.387709/23.387709 dB**,
기존 R4 23.295651 대비 **+0.092057 dB**이고, 584-view fixed held-out,
mapping overlap 0, zero-tail 0, pair fairness 10/10 PASS다. 기존 R4의
vanilla 값을 섞지 않았으며 새 vanilla **21.188828 dB**로 비교했다.

`table_03`의 normalized는 기존 R4 23.504535 대비 **+0.050961 dB**이고,
새 vanilla와 85,029 physical render가 일치한다. 두 arm의 Adam은
6,724/6,706이며 동일 step 수라는 주장은 하지 않는다. 구조 gate 12/12,
이중 평가, pair fairness 10/10 모두 PASS했다.

`table_04`도 기존 R4 22.365113 대비 normalized **+0.036704 dB**,
fresh vanilla 대비 **+1.125194 dB**였다. 67,793/67,793 render,
Adam 5,359/5,343, 구조 12/12·이중 평가·fairness 10/10 PASS다.

`table_05`의 normalized는 기존 R4 22.778009 대비 **+0.011273 dB**였고,
fresh vanilla보다 **+1.088358 dB** 높았다. 52,480/52,480 render,
Adam 4,135/4,138, 구조 12/12·이중 평가·fairness 10/10 PASS다.

`table_06`은 normalized가 기존 R4 24.487588보다 **0.014501 dB 낮지만**
사전 급락 중단선 0.5 dB에는 못 미쳤다. Fresh vanilla 대비
**+1.790892 dB**, 34,437/34,437 render, Adam 2,714/2,719,
구조 12/12·이중 평가·fairness 10/10 PASS다.

`table_07`은 normalized가 기존 R4 26.840032보다 **0.080468 dB 낮지만**
중단선 이내이고, fresh vanilla보다 **+1.489040 dB** 높았다.
33,422/33,422 render, Adam 2,691/2,680, 구조 12/12·이중 평가·
fairness 10/10 PASS다.

`table_08`도 기존 R4 23.860418보다 normalized가 **0.067220 dB 낮지만**
중단선 이내이고, fresh vanilla보다 **+1.692767 dB** 높았다.
94,283/94,283 render, Adam 7,465/7,436, 구조 12/12·이중 평가·
fairness 10/10 PASS다. 따라서 **RPNG 8/8 승리, scene 평균 +1.598585 dB**다.

UTMM 첫 장면 `ego-centric-1`은 normalized **17.758819**, 기존 R4
**17.755807** 대비 **+0.003012 dB**다. Fresh vanilla **17.212576**보다
**+0.546243 dB** 높고, 5,676/5,676 render, Adam 466/465,
구조 12/12·이중 평가·fairness 10/10 PASS다.

UTMM `ego-centric-2`는 normalized **19.492180**, 기존 R4 19.494420
대비 **−0.002240 dB**로 사실상 동률이다. Fresh vanilla **19.255612**보다
**+0.236568 dB** 높고, 6,655/6,655 render, Adam 559/556,
구조 12/12·이중 평가·fairness 10/10 PASS다.

UTMM `ego-drive` normalized **21.264177**은 기존 R4 21.248894보다
**+0.015283 dB** 높았다. Fresh vanilla **20.560581** 대비
**+0.703596 dB**, 11,226/11,226 render, Adam 898/900,
구조 12/12·이중 평가·fairness 10/10 PASS다.

UTMM `fast-straight` normalized **16.379936**은 기존 R4 16.379202와
**+0.000733 dB** 차이로 사실상 동일하고, fresh vanilla **15.948413**보다
**+0.431523 dB** 높다. 1,348/1,348 render, Adam 172/165,
구조 12/12·이중 평가·fairness 10/10 PASS다.

UTMM `slow-straight-2`는 normalized **17.223444**, 기존 R4 17.247573
대비 **−0.024129 dB**로 사전 급락 중단선 이내지만, fresh vanilla
**17.349673**보다 **−0.126230 dB 낮다**. 1,888/1,888 render,
Adam 177/171, 구조 12/12·이중 평가·fairness 10/10 PASS다. 실패를
숨기지 않는다. 이 시점에 historical R4의 **17/17 승리 stretch target은
실패 확정**이고, 17-scene 평균 ≥+0.5 dB·과반 승리·전체 fairness라는
최소 기준은 나머지 scene 완료 전까지 미판정이다.

UTMM `square-1` normalized **21.224773**은 기존 R4 21.239715보다
**−0.014942 dB** 낮지만 중단선 이내다. Fresh vanilla **20.181777** 대비
**+1.042996 dB**, 9,345/9,345 render, Adam 757/763,
구조 12/12·이중 평가·fairness 10/10 PASS다.

UTMM `square-2` normalized **21.416180**은 기존 R4 21.416009 대비
**+0.000171 dB**로 동률이고, fresh vanilla **20.630652**보다
**+0.785529 dB** 높다. 8,277/8,277 render, Adam 676/679,
구조 12/12·이중 평가·fairness 10/10 PASS다. UTMM 7개 scene 집계는
**6승 1패·산술평균 +0.517175 dB**다.

수학 구현 회귀 테스트 `test_exp94_normalized_variance_gibbs.py` 3개 PASS:
dense/aux와 native-KF queue의 log-odds가 모두
`-log(1.5)(n_i-n_j)/(T+1)`과 같고, 같은 count 격차라도 T가 늘면
balancing이 약해진다. 따라서 이는 고정 beta의 raw-variance sampler를
이름만 바꾼 구현이 아니다. 기존 block/global-residue 제약 안에서 이
Gibbs log weight를 조건부로 사용한다.

Aria `aria1253`/`aria301_305`도 각각 새 official vanilla 대비
**+1.719794/+3.185685 dB**였고, Aria 평균은 **+2.452740 dB**다.
두 pair 모두 동일 physical render·zero-tail·이중 평가·fairness 10/10을
통과했다.

독립 read-only 완료 감사 `audit_exp94_normalized_panel.py`는 17-scene
inventory/source lock, 각 pair의 구조 gate·이중 평가·held-out PSNR·physical
render·Adam step·Gaussian 수·zero-tail·held-out 불교집합·fairness checks를
다시 대조한다. `--require-complete`에서 **17/17 완료·pending 0·감사 오류 0**이다.
모든 scene의 구조 gate 12/12, 두 arm 이중 평가, pair fairness 10/10이
PASS했다. Source lock은 runner·evaluator·mapping harness·Aria adapter 등
17개 파일의 해시를 고정한다.

**최종 판정:** 17개 유효 scene의 산술평균 normalized−fresh vanilla는
**+1.253787 dB**, **16승 1패**이며 모든 pair fairness가 PASS여서 사전
최소 기준(평균 ≥+0.5 dB·과반 승리·전 pair 공정성)은 **PASS**다.
RPNG 8/8 **+1.598585 dB**, UTMM 6/7 **+0.517175 dB**, Aria 2/2
**+2.452740 dB**다. 유일한 패배는 UTMM `slow-straight-2` **−0.126230 dB**.
기존 R4 대비 최악의 normalized 손실은 RPNG `table_07` **0.080468 dB**로
사전 `>0.5 dB` 중단선이 발동하지 않았다. 다만 기존 R4의 17/17 승리와
평균 **+1.260888 dB** 회복이라는 추가 목표는 **FAIL**이다. 새 평균 이득이
약 **0.007100 dB** 낮으며, 이를 성공으로 바꾸어 해석하지 않는다.

과거 R4/vanilla artifact 평균과 이번 새 pair의 평균은 별도 사후 비교일
뿐, 과거 vanilla를 공식 표에 섞지 않았다. 새 normalized 평균 PSNR은
과거 R4보다 **0.001030 dB 낮고**, 새 vanilla 평균은 과거 vanilla보다
**0.006070 dB 높다**. B-track은 frozen tracker 기반 mapping-only fixed-work
비교이며 동시 tracker+mapper의 strict real-time 성능을 증명하지 않는다.
