# exp83 — strict VIGS KF+dense supervision

> 상태: 진행 중. 목표는 strict-streaming 1.5×에서 KF의 native
> RGB+depth+normal loss를 유지하고 causal dense RGB를 추가하여 동일 KF-only
> control보다 fixed held-out PSNR을 +1.0dB 높이는 것이다. 현재 최고 dense arm은
> **+0.2399dB**이며 acceptance는 아직 미달이다.

## 계약

- dataset/개발 scene: UTMM `ego-drive`, 1,399 RGB
- 입력: timestamp 순 RGB+IMU만 사용, MPS/GT pose/depth 입력 없음
- fixed sensor deadline: 69.9454초, optimizer zero-tail
- fixed evaluator: `is_fixed_eval_view=true` 281장. evaluator union 평균은 판정에 쓰지 않음
- 공통: B1(one view → one Adam), native KF RGB+depth+normal, dense RGB-only,
  realtime5070 frontend, dense-RR pool, seed 0

## 결과

### final-v7 복원 및 공통-policy 경계 감사

| arm | dataset / 실행 계약 | fixed PSNR | 비교 Δ | replay KF/dense | 판정 |
|---|---|---:|---:|---:|---|
| exp83-A | UTMM, 5070 execution + final-v7, KF-only | 21.2468 | — | 3,489 / 0 | strict control |
| exp83-B | UTMM, 위와 동일, dense-only replay | **21.4867** | **+0.2399** | 0 / 2,999 | 작은 양수, +1 미달 |
| exp83-C | Aria1253, exp67 final-v7 policy 회귀 | **27.0560** | — | 0 / 4,545 | 27dB 통과, 과거 27.812 평균 미재현 |
| exp83-D | UTMM, exp67 실행 숫자까지 그대로 이식 | 17.6878 | 비교 불가 | 0 / 329 | **1.5× deadline 실패** |
| exp83-E | UTMM, B + native dense-global3, interval은 map 뒤 등록 | 21.3293 | +0.0825 vs A | 0 / 2,957 | B보다 −0.1574, 기각 |
| exp83-F | UTMM, E + interval을 같은 frontier map 전 등록 | 21.1035 | −0.1433 vs A | 0 / 2,559 | E보다 −0.2258, 기각 |
| exp83-G pilot | UTMM, B + IMU rotation, adaptive residual 누락 | 19.6242 | invalid | 0 / 2,482 | PGBA 뒤 bridge 0장, 버그 노출 |
| exp83-G | UTMM, B + IMU rotation, adaptive residual 보존 | 21.1924 | −0.0544 vs A | 0 / 2,366 | B보다 −0.2942, 기각 |
| exp83-H | UTMM, B selection + progress 관측-only | 21.0909 | −0.1559 vs A | 0 / 2,206 | B보다 −0.3958, admission 재현성 문제 노출 |
| exp83-I unwired pilot | UTMM, token env가 exp81에서 off로 덮임 | 21.2030 | invalid I | 0 / 3,272 | 실제 work-credit 반복, I 판정 제외 |
| exp83-I | UTMM, global-seed token-only \(\kappa=22\) | 20.0185 | −1.2283 vs A | 0 / 1,245 | pool starvation, 기각 |
| exp83-J | UTMM, interval bootstrap + paid token \(\kappa=22\) | 20.9872 | −0.2595 vs A | 0 / 3,192 | pure gate-removal도 기각 |
| exp83-K | UTMM, native global3 + progress 관측-only | 21.4482 | +0.1508 vs repeat KF | 2,701 / 0 | dense native update 1,197 유지 |
| exp83-L pilot | residual1+coverage1+random1, per-iter CPU sync | 20.0983 | invalid | 1 / 0 | Adam 782로 service 붕괴 |
| exp83-L | residual1+coverage1+random1, batched EMA | 21.3731 | +0.0757 vs repeat KF | 2,807 / 0 | K보다 −0.0751, 기각 |
| exp83-M | random native global3 + idle dense100 | 21.2360 | −0.0614 vs repeat KF | 0 / 3,192 | SSIM/LPIPS 개선, PSNR 기각 |
| exp83-N | random native global3 + idle KF75/dense25 | **21.5855** | **+0.2880 vs repeat KF** | 2,244 / 748 | native 계열 최고, +1 미달 |
| exp83-O | N + dense RGB RMSE | 21.4978 | +0.2004 vs repeat KF | 2,070 / 691 | N보다 −0.0877, 기각 |
| exp83-P r1/r2 | Aria1253, final-v7 + topology-freeze API 완전 제거 | 26.9449 / **27.1171** (평균 **27.0310**) | — | dense 3,749 / 3,799 | unknown-horizon 27dB 평균 유지 |
| exp83-Q-U | UTMM full, 현재 HEAD final-v7 dense, freeze API 없음 | **21.2556** | −0.2311 vs 과거 B (비동시) | 0 / 2,934 | zero-tail, producer +0.012s 경계 |
| exp83-Q-R | RPNG table_01 첫 1,000, 동일 policy/sensor adapter | **18.9723** | current paired control 없음 | 0 / 182 | **producer deadline +1.020s, strict 실패** |
| exp83-R | RPNG 첫 1,000, Q vs original vanilla pure-online/no-polish | 18.9377 / **23.8599** shared | **−4.9222** | shared held-out 185 | custom가 vanilla에 크게 미달 |

exp83-A/B는 deadline/EOS 뒤 Adam 0/0이다. A/B의 frontier KF view-update는
3,002/3,023으로 native KF RGB+depth+normal 경로가 유지됐고, 차이는 replay source다.
다만 B는 total Adam이 3,508회로 A의 3,998회보다 적어졌음에도 +0.2399dB였으므로
dense 신호의 작은 이득은 확인되지만 +1 acceptance와는 거리가 있다.

exp83-C는 제거된 `background_polish_step()` 없이 `map()` 내부 final-v7만으로
Aria1253 fixed 27.0560dB를 냈다. 따라서 backpolish 함수 삭제가 Aria의 27dB 경로를
없애지는 않았다. 그러나 같은 exp67 runner의 과거 평균 27.8123dB보다 0.7563dB
낮고, 현재 active candidate/replay는 308/4,545로 과거 450–553/5,974–6,505보다
작다. 현재 HEAD의 admission/worker 진화까지 포함한 회귀로 보고 원인을 분리해야 한다.

exp83-P는 exp57의 고정 `freeze800` reference와 exp67 final-v7을 혼동한 기록을
바로잡고, runtime에서 `mapping_auto_topology_freeze`,
`mapping_topology_freeze_after_frame`, dense-count topology trigger API와 모든 runner
wiring을 삭제한 뒤 수행한 Aria1253 회귀다. 두 run의 fixed 252-view PSNR은
**26.9449/27.1171dB(평균 27.0310)**, SSIM은 0.86155/0.86174, LPIPS는
0.25857/0.25682였다. 둘 다 정상 frontier topology event가 2회 발생한 뒤
final-v7 controller가 관측된 topology/capacity와 replay epoch만으로
`balanced → replay`로 전환했다. Freeze option/log는 0개이고 online-final evaluation의
map update도 0이다. 따라서 장면별 freeze knob 없이 현재 Aria 27dB 수준을 평균으로
유지한다. 단, 개별 2회 중 1회가 27dB를 0.055dB 밑돌아 per-run 27dB 보장은 아직 아니다.

exp83-Q는 P에서 topology-freeze/forced-trigger API를 삭제한 현재 HEAD의 final-v7
causal-dense policy를 재튜닝 없이 UTMM `ego-drive` full 1,399장과 RPNG `table_01`
첫 1,000장에 전이했다. 센서 calibration/undistortion과 measured-cost 5070 실행 adapter만
dataset별로 사용했다. UTMM fixed 281-view는 **21.2556dB**, SSIM 0.70386, LPIPS
0.32001이며 Adam 3,443회 중 dense replay 2,934회, topology event 2회 뒤 replay phase에
도달했다. Deadline/EOS 뒤 update와 online-final update는 모두 0이나 producer EOS가
deadline보다 0.012초 늦어 literal timing은 경계다. 과거 B보다 −0.2311dB지만 제거된
freeze option은 B에서도 활성화되지 않았고 실행 시점의 코드 상태도 같지 않으므로 이를
삭제 효과로 귀속하지 않는다.

RPNG fixed 201-view는 **18.9723dB**, SSIM 0.59619, LPIPS 0.37708이다. Adam 763회,
dense replay 182회뿐이고 정상 topology event 2회 뒤 balanced phase에서 끝났다. Update
tail은 0/0이지만 producer EOS가 49.9828초 deadline보다 **1.0202초 늦어 strict 1.5×
실패**다. 과거 dense_rr KF-only 17.5626dB보다 숫자는 +1.4097dB지만 mapping profile과
코드 시점이 달라 paired dense gain으로 해석하지 않는다. 현재 final-v7 KF-only pair가
없으므로 Q는 cross-dataset 실행 회귀일 뿐 dense +1 acceptance 증거가 아니다.

exp83-D는 mapping/frontend flag를 exp67과 동일하게 고정하고 UTMM에서는 sensor/IMU
calibration 및 648x328 TensorRT engine만 교체했다. 하지만 producer EOS가 deadline보다
5.9389초 늦었고 completed Adam은 699회, dense replay는 329회뿐이었다. 즉 모든 실행
숫자를 공통화하면 UTMM 해상도/부하에서 optimization service가 붕괴한다. 채택할 구조는
**공통 final-v7 policy + sensor calibration adapter + measured-cost execution adapter**이며,
scene별 PSNR 튜닝값을 두는 방식은 아니다.

exp83-E/F는 current-window KF와 native KF RGB+depth+normal loss를 보존한 채 기존
historical-global 세 자리만 dense RGB로 교체했다. E/F의 native dense view-update는
동일하게 420회였지만, B의 replay-only **21.4867dB**에 비해 E는
**21.3293dB(−0.1574)**, F는 **21.1035dB(−0.3832)**였다. 특히 pre-frontier
등록만 바꾼 F는 E보다 −0.2258dB다. F에서는 비동기 drop packet의 dense record를 다음
packet으로 인계했음에도 pool이 E 317→F 552로 커지고 total Adam은 3,466→3,068회로
줄었다. 따라서 일찍 도착한 dense를 native frontier/topology에 즉시 노출하는 방식은
이 execution profile에서 admission feedback과 optimizer service를 함께 악화시킨다.
E/F 모두 deadline/EOS 뒤 Adam 0/0이므로 strict 계약 위반이 원인은 아니다.

exp83-G pilot은 adaptive admission 경로가 IMU-corrected pose를 6-field record로
전달하면서 `causal_pose_residual`을 누락하는 버그를 드러냈다. 첫 PGBA 뒤 dense
289장을 갱신했지만 residual 재적용은 0장이었고 fixed는 19.6242dB였다. 일반 interval
경로와 똑같이 interpolation 대비 right-multiplied residual을 저장하도록 고친 유효 G는
316장 중 312장에 residual을 재적용해 fixed를 **21.1924dB(+1.5682)**로 회복했다.
그러나 A보다 −0.0544, optical B보다 −0.2942dB이고 total Adam도 B 3,508→G 2,887로
줄었다. IMU residual 지속성 수정은 유지하지만, final-v7의 pose source로 IMU bridge를
채택하지 않는다. 두 G 모두 deadline/EOS 뒤 Adam은 0/0이다.

exp83-H는 B의 optical pose, replay-only topology, loss 및 random selection을 그대로
두고 이미 계산하던 epoch loss/progress의 view별 행만 보존한 관측-only 반복이다. JSONL은
stream 종료 뒤 기록하므로 optimizer tail은 추가되지 않았고 deadline/EOS 뒤 Adam도
0/0이다. 그런데 fixed는 **21.0909dB**로 B보다 −0.3958dB, pool은 310→543,
total Adam은 3,508→2,715회로 갈렸다. 두 run의 mapping packet은 enqueue 71/drop 7/
process 64로 같지만, fixed-time 비동기 실행에서 optical interval queue와 idle service의
작은 timing 차이가 maturity 기반 work-credit admission의 pool 성장으로 증폭됐다. 따라서
현재 B 단일값을 재현 가능한 +0.2399dB로 간주할 수 없으며 sampler 변경 전에 admission
clock을 안정화해야 한다.

exp83-I 첫 pilot은 wrapper가 token on을 출력했지만 exp81 baseline runner가 이를 off로
덮어 실제 backend는 work-credit였다. Fixed 21.2030dB, pool 421, total Adam 3,781회인
B/H 추가 반복 자료로만 보존하고 I 판정에서는 제외한다. 전달 경로를 default-off/
explicit-opt-in으로 수정한 유효 I는 frontend·backend 모두 `gate_free=1, cost=22`를
기록했다. 그러나 exp73 token-only는 interval bootstrap도 없애고 global seed 한 장만
무료라, UTMM에서는 bootstrap 1+paid 50=pool 51장에 그쳤다. First/last-quarter selection
mean이 63.92/4.75로 크게 기울고 total Adam도 1,769회, fixed는 **20.0185dB**로
붕괴했다. Strict tail은 0/0이다. 이는 \(\kappa=22\)의 숫자 sweep 근거가 아니라,
exp73 카드가 남긴 “interval bootstrap을 유지한 pure gate-removal arm”이 이번 비교에
필요하다는 증거다.

exp83-J는 기존 work-credit의 interval bootstrap을 그대로 두고 paid admission만
completed-work token으로 바꾼 pure gate-removal 분리 축이다. 실제 admission은
bootstrap 140+paid 127=267장이고 replay 3,192회, total Adam 3,708회로 I의 starvation은
해결했다. 그러나 first/middle/last-quarter selection mean이 16.26/16.27/4.41로 후반
coverage가 여전히 부족했고 fixed는 **20.9872dB**로 A보다 −0.2595, B보다 −0.4994dB였다.
Deadline/EOS tail은 0/0이다. 따라서 final-v7 adaptive admission의 숫자/gate를 더
조정하지 않고, native map의 고정 3 dense-global slot으로 optimizer cardinality를
통제한 재현 pair를 다음 scheduler 기반으로 사용한다.

exp83-K는 +0.2115/+0.1911dB가 재현된 native global3의 random selection을 유지하고
native map-call loss/progress만 stream 종료 뒤 JSONL로 저장했다. Native KF/dense
view-update는 기존과 정확히 같은 6,420/1,197회, deadline/EOS tail은 0/0이다. Fixed는
**21.4482dB**로 repeat KF-only 21.2974보다 +0.1508이고, 같은 random dense repeat
21.4886보다 −0.0403이라 observation-only 경로가 기존 작은 gain을 보존했다. Dense
129장에 1,041 observation/912 paired progress가 생겼다. 동일 view의 연속 관측에서
previous progress→next absolute gain Spearman은 0.080으로 약한 반면, previous loss→
next absolute gain은 **0.315**였다. Dense_rr membership은 adaptive Fisher 계산을
지나지 않아 Fisher novelty가 전부 0이므로 이를 coverage라고 사용할 수 없다.

exp83-L pilot은 고정 3슬롯을 residual1+least-served1+random1로 배분했지만 residual
EMA 갱신이 매 native mapping iteration마다 tensor를 CPU로 materialize했다. Native
KF/dense view-update 6,420/1,197회 자체는 유지됐으나 이 sync가 fixed-time idle service를
막아 KF replay가 K 2,701→**1회**, total Adam이 3,482→**782회**로 붕괴했고 fixed는
20.0983dB였다. 따라서 sampler 결과가 아니라 구현 오버헤드 invalid pilot이다. EMA를
K에서 이미 수행하는 map-call당 한 번의 progress sync에 합쳐 추가 sync 0회로 고친 뒤
같은 exp83-L을 재실행한다.

Batched EMA로 고친 유효 L은 native KF/dense 6,420/1,197, idle KF 2,807,
total Adam 3,588회와 strict tail 0/0을 회복했다. Fixed는 **21.3731dB**로 repeat
KF-only보다 +0.0757이지만 K보다 −0.0751, random global3 repeat보다 −0.1154다.
Last-quarter 선택 평균은 random repeat 2.39→4.15로 좋아졌지만 held-out 품질은
악화했다. 따라서 직전 training residual의 단기 예측력을 final-quality scheduler로
곧바로 쓰는 방식과 specialized slot 비율 sweep은 기각한다.

Auto-freeze가 같은 주 비교:

| arm | source/pose/gradient | fixed PSNR | Δ vs KF | Adam total | replay KF/dense |
|---|---|---:|---:|---:|---:|
| KF-only control | KF100 | **21.3314** | — | 3,156 | 2,375 / 0 |
| KF+dense B4 | KF75, interp., full | 20.9657 | −0.3657 | 1,378 | 2,481 / 827 |
| KF+dense B1 | KF75, interp., full | 20.8272 | −0.5042 | 2,837 | 1,542 / 514 |
| KF+dense B1 | KF75, IMU rot., full | 21.1153 | −0.2160 | 2,668 | 1,415 / 472 |
| KF+dense B1 | KF75, IMU rot., appearance+opacity | 20.6375 | −0.6939 | 2,101 | 990 / 330 |
| KF+dense B1 | KF75, IMU rot., residue2 | 21.1685 | −0.1629 | 3,617 | 2,121 / 708 |
| KF+dense B1 | KF90, IMU rot., residue2 | **21.3283** | **−0.0030** | 3,240 | 2,213 / 246 |
| KF+dense B1 | KF90, IMU pose, residue2 | 20.6809 | −0.6505 | 1,567 | 707 / 79 |
| KF+dense B1 | KF90, IMU rot., interval midpoint | 21.3243 | −0.0070 | 3,288 | 2,256 / 251 |
| KF+dense B1 | KF90, IMU rot., post-init midpoint | 21.2640 | −0.0673 | 3,437 | **2,390 / 266** |
| KF+dense B1 | KF75, IMU rot., post-init midpoint | 21.2604 | −0.0710 | 3,703 | **2,191 / 731** |
| KF+dense B1 | KF75, optical, post-init midpoint | 20.9848 | −0.3466 | 2,107 | 984 / 328 |
| KF+dense B2 | KF50+IMU midpoint joint batch | 21.0245 | −0.3069 | 2,284 | 1,503 / 1,503 |
| KF+dense B1 | KF75, IMU midpoint residual survives PGBA | **21.5042** | **+0.1728** | 3,781 | 2,250 / 750 |
| KF+dense B1 | 위 조건 + same-backward pose Adam (4×, LR×10) | 21.3792 | +0.0479 | 3,415 | 1,970 / 657 |
| KF+dense B1 | KF75, IMU stride40 compact repeat (28 views) | 21.4322 | +0.1008 | 3,704 | 2,187 / 729 |

Non-strict GT 상대운동 oracle 진단(아래 값은 strict 성과가 아님):

| arm | GT orientation 처리 | fixed PSNR | Δ vs KF | Adam total | replay KF/dense |
|---|---|---:|---:|---:|---:|
| invalid pilot | robot orientation을 camera로 오독 | 21.0783 | −0.2531 | 3,573 | 2,088 / 697 |
| corrected oracle | UTMM robot c2w × `UTMM_C2R` | **21.3001** | **−0.0313** | 3,818 | 2,277 / 760 |

Non-strict full-GT pose paired 진단(아래 값은 strict 성과가 아님):

| arm | mapping/eval pose | fixed PSNR | Δ vs GT-pose KF | Adam total | replay KF/dense |
|---|---|---:|---:|---:|---:|
| KF-only B1 | GT absolute | **18.9002** | — | 3,261 | 2,664 / 0 |
| KF75+dense25 B1 | GT absolute | **19.0608** | **+0.1607** | 3,239 | 1,981 / 661 |

Dense-owned early-topology strict 진단:

| arm | dense trigger | fixed PSNR | Δ vs KF | Adam total | replay KF/dense |
|---|---:|---:|---:|---:|---:|
| KF75+dense25 B1 | 64 dense backward | 21.2703 | −0.0610 | 3,148 | 1,791 / 597 |
| KF75+dense25 B1 | 16 dense backward | 21.2525 | −0.0788 | 3,228 | 1,851 / 617 |

Unified native-`map()` strict 진단:

| arm | native global slots | fixed PSNR | Δ vs KF | Adam total | native KF/dense views | idle KF/dense |
|---|---|---:|---:|---:|---:|---:|
| KF100+dense-global1 | KF 5 + dense 1 | **21.4864** | **+0.1551** | 3,575 | 7,316 / 406 | 2,787 / 0 |
| KF100+dense-global3 | KF 3 + dense 3 | **21.5429** | **+0.2115** | 3,643 | 6,420 / 1,197 | 2,862 / 0 |
| KF100+dense-global3, open topology | KF 3 + dense 3 | 21.1846 | +0.1685 vs open KF | 3,664 | 6,126 / 1,134 | 2,904 / 0 |
| KF100+dense-global3, all balanced | KF 3 + dense 3 | 21.3506 | +0.0193 | 3,734 | 6,420 / 1,197 | 2,953 / 0 |
| KF100+dense-global3, mix1 | KF 3 + dense 3 | 21.5099 | +0.1785 | 3,827 | 6,420 / 1,197 | 3,046 / 0 |
| KF100+dense-global3, dense RGB weight 2 | KF 3 + dense 3 | 21.5252 | +0.1938 | 3,572 | 6,420 / 1,197 | 2,791 / 0 |

Random global3 재현성 pair:

| repeat | KF-only fixed | dense-global3 fixed | paired Δ | KF/dense Adam total |
|---|---:|---:|---:|---:|
| 0 | 21.3314 | 21.5429 | **+0.2115** | 3,156 / 3,643 |
| 1 | 21.2974 | 21.4886 | **+0.1911** | 3,156 / 3,186 |
| 평균 | 21.3144 | 21.5157 | **+0.2013** | — |

2× causal zero-tail budget 진단(공식 strict 1.5× 성과가 아님):

| arm | scale / deadline | fixed PSNR | paired Δ | total Adam | native KF/dense | idle KF |
|---|---:|---:|---:|---:|---:|---:|
| KF-only | 2.0× / 93.2605s | 21.6809 | — | 7,085 | 7,589 / 0 | 6,304 |
| KF100+dense-global3 | 2.0× / 93.2605s | **21.8221** | **+0.1412** | 7,991 | 6,420 / 1,197 | 7,210 |

두 run 모두 sensor deadline/EOS 뒤 Adam update 0/0이다. 1.5× repeat 평균 대비
0.5× budget의 증분은 KF-only +0.3665dB, dense +0.3064dB이며 paired dense gap은
+0.2013→+0.1412dB로 0.0601dB 줄었다. Common estimated trajectory 교차 렌더에서도
dense map 우위의 부호는 두 방향 모두 유지됐지만, control trajectory에서는 +0.0179dB,
dense trajectory에서는 +0.2772dB로 map/trajectory coupling에 따라 크기가 달랐다.

Open-topology paired 진단:

| arm | dense topology stats | fixed PSNR | Δ vs open KF | Adam total | replay KF/dense |
|---|---:|---:|---:|---:|---:|
| KF-only B1 | 0 | **21.0161** | — | 3,195 | 2,442 / 0 |
| KF90+dense10 B1, IMU midpoint | 0 | 20.9397 | −0.0764 | 3,607 | 2,568 / 286 |
| KF90+dense10 B1, IMU midpoint | 263 views | 20.9245 | −0.0916 | 3,376 | 2,360 / 263 |

모든 표의 strict run은 deadline/EOS 뒤 Adam update 0/0이다. B4는 4-view 평균
gradient당 Adam 1회이므로 B1 네 update와 같지 않아 원인 근거에서는 제외한다.

## 확정된 해석

1. **optimizer 서비스 감소가 일반 원인은 아니다.** Post-init midpoint arm은 KF replay가
   2,390회로 control 2,375회를 보존한 채 dense 266회를 추가했지만 −0.0673dB였다.
2. GT를 학습에 쓰지 않은 oracle 진단에서 975 dense frame 회전오차는 endpoint
   interpolation 2.3856°에서 endpoint-corrected gyro bridge 0.0658°로 줄었다.
   실제 run도 interpolation 대비 +0.2882dB 회복해 dense rotation은 실재 병목이지만,
   이것만으로 양의 gain은 만들지 못했다.
3. VIGS velocity를 이용한 Hermite translation bridge는 최대 보정 6.67cm 범위에서도
   −0.6505dB라 기각했다. Appearance+opacity-only gradient도 느리고 더 낮아 기각했다.
4. 기존 replay는 dense backward를 native `add_densification_stats()`에서 제외한다.
   이를 opt-in으로 연결해 263 dense 관측이 실제 topology에 반영되고 세 번째 event 직전
   Gaussian 수가 약 81.5K→101.0K로 달라졌지만 PSNR은 −0.0152dB 더 낮았다. 단순히
   topology를 열거나 dense 통계를 평균에 추가하는 축은 기각한다.
5. `evo_ape tum -vas` full-trajectory Sim3 ATE는 auto-freeze control 4.070cm,
   post-init midpoint 4.300cm다. 서로의 trajectory를 각 map gauge에 Sim3 정렬해
   교차 렌더하면 dense-map/control-trajectory 21.0566dB, control-map/dense-trajectory
   21.0864dB로 control이 여전히 +0.0298dB다. 숨은 dense-map gain은 보이지 않는다.
6. exp84의 compact-pool 반복 가설에 따라 같은 139-view midpoint pool의 dense quota를
   10%→25%로 높여 평균 약 1.9→5.3회/view 서비스했지만 fixed는 21.2604dB
   (−0.0710)로 개선되지 않았다. 따라서 현재 병목을 **dense 재방문 횟수 하나로만**
   설명할 수 없다. 참고로 로그의 21.4079는 전체 non-KF 평균이며 fixed 판정값이 아니다.
7. PoseTrajectoryFiller arm은 `dense_interval_queue`가 0.553→11.304초로 늘어 replay가
   2,922→1,312 step으로 붕괴했다. fixed 20.9848dB 결과는 현재 synchronous optical
   filler의 실시간 부적합을 뜻하며, optical pose 자체의 품질 비교로 해석하지 않는다.
8. 같은 compact pool을 B2로 묶으면 dense service는 1,503회까지 늘지만 KF도 1,503회로
   줄고 fixed는 21.0245dB(−0.3069)다. 따라서 현재 joint batch의 단순 평균은 KF geometry
   supervision을 보존하는 방법이 아니다. B1 quota/B2 batch-size 추가 sweep은 중단한다.
9. 코드 감사에서 IMU bridge가 등록 시점에만 적용되고 첫 PGBA가 기존 dense 119장의
   pose를 단순 interpolation으로 덮어쓰는 버그를 발견했다. Bridge를 interpolation 대비
   right-multiplied residual로 저장하자 PGBA refresh에서 118/119개에 재적용됐고, 동일
   KF75/B1 arm의 fixed가 21.2604→**21.5042dB**(+0.2438), KF-only 대비
   **+0.1728dB**로 처음 명확한 양수까지 회복했다. rotation pose의 지속성은 채택하지만
   +1 acceptance에는 0.8272dB가 남는다.
10. 기존 dense RGB backward의 camera gradient를 재사용해 view당 최대 4회,
    LR×10, 1mm/0.057° per-component trust bound로 pose Adam을 Gaussian Adam과 같은
    EOS-atomic action에 넣었다. 별도 render/backward와 tail 없이 502회 실행되고 PGBA
    뒤 residual도 119/119 유지됐지만 fixed는 **21.3792dB**였다. KF-only보다
    +0.0479dB이나 pose-align 없는 persistent arm보다 **−0.1250dB**다. 작은 camera
    optimizer/SE(3) 연산도 공짜가 아니어서 total Adam이 3,781→3,415(−9.7%), replay가
    2,250/750→1,970/657로 감소했다. 이 arm은 기각하며 pose 방향과 service loss가
    섞였으므로 camera-step 크기 sweep으로 해석하지 않는다.
11. 같은 KF75/B1/loss/topology/69.9454초 조건에서 dense intra-interval pose만 GT
    상대운동으로 바꾼 non-strict oracle도 corrected fixed **21.3001dB**로 KF-only보다
    **−0.0313dB**였다. 최초 21.0783dB pilot은 UTMM `groundtruth.txt`의 robot-frame
    orientation에 exp84와 동일한 `UTMM_C2R` camera-axis 변환을 빠뜨린 invalid run으로
    보존했다. 수정본은 138/139 dense pose에 GT bridge를 적용하고 PGBA 뒤 118개
    residual을 유지했으며, 3,818 Adam 중 replay가 KF/dense 2,277/760회였다. 따라서
    dense의 현재 +1 미달을 **intra-interval pose 오차 하나로는 설명할 수 없다.** 다만
    이 oracle은 online KF endpoint 자체를 GT로 교체하지 않으므로 full-GT exp84와
    같은 절대-pose 실험은 아니다.
12. Persistent IMU arm에서 dense pool만 139→28장(`frame mod 40 = 2`)으로 줄여
    dense service를 약 5.5→**26.0회/view**로 4.7배 집중했다. fixed는
    **21.4322dB**로 KF-only보다 +0.1008dB지만, 139-view best 21.5042보다
    **−0.0720dB**였다. 따라서 후보당 반복 횟수만 늘리는 것으로도 +1은 나오지 않는다.
    exp84에서는 dense view가 초기부터 densification/topology 형성에 참여한 반면 이 arm은
    keyframe frontier가 만든 topology를 auto-freeze한 뒤 replay한다는 구조 차이가 남는다.
13. 모든 mapping/evaluation camera를 UTMM GT absolute pose로 바꾼 non-strict paired
    oracle에서도 KF-only **18.9002dB**, KF75+dense25 **19.0608dB**로 dense gain은
    **+0.1607dB**뿐이었다. 절대 PSNR이 online-pose control보다 낮은 것은 online depth와
    map scale/gauge는 그대로 둔 채 pose만 GT gauge로 치환해 RGBD geometry가 불일치한
    진단 한계이므로 GT 성능 ceiling으로 읽지 않는다. 하지만 동일한 불일치를 공유하는
    pair에서도 +1이 나오지 않았으므로 현재 실패를 pose interpolation 단독 원인으로
    확정할 수 없다.
14. Auto-freeze를 dense-owned trigger까지 유예하고 dense screen-space 통계 64 또는
    16회마다 topology event 1회를 강제한 strict arm은 각각 **21.2703dB(−0.0610)**,
    **21.2525dB(−0.0788)**였다. 둘 다 tail 0/0이다. Trigger를 16으로 낮춰도 dense-owned
    event는 frame654로, frontier의 두 번째 event(frame633)보다 늦었다. 코드상 replay는
    GS queue가 비는 tracking/mapping slack에서만 실행되므로 threshold가 아니라 **dense
    service 자체가 frontier topology 뒤에 시작되는 구조**가 원인이다. 현 replay worker에
    trigger 숫자만 더 줄이는 sweep은 중단한다.
15. 별도 idle dense replay를 완전히 끄고, native `map()`의 6개 historical-global 슬롯 중
    1개를 causal IMU-midpoint dense RGB로 교체했다. 현재-window KF와 그 RGBD+normal loss,
    총 frontier view cardinality, native topology/Adam clock은 그대로다. 실제 계측은 native
    KF/dense **7,316/406 view-update**, idle KF/dense **2,787/0**이며 fixed는
    **21.4864dB**, KF-only보다 **+0.1551dB**였다. Dense가 frontier에 일찍 참여하는 단일
    scheduler 방향은 양수지만 +1에는 0.8449dB가 남고, 현재 전체 view supervision에서
    dense 비율은 약 3.9%뿐이다.
16. 같은 총 6 global 슬롯에서 dense만 1→3으로 늘리자 native dense update는
    **406→1,197회**로 2.95배가 됐지만 fixed는 **21.4864→21.5429dB**, +0.0565dB만
    올랐다. KF-only 대비는 +0.2115dB이며 tail 0/0이다. 슬롯 비율만 높이는 축은 빠르게
    수확체감한다. 두 unified arm 모두 final `topology_events=1`이고, 그 event는 dense가
    등록되기 전 발생했으므로 1,197개 dense screen-space gradient는 Gaussian 생성/분할에
    실제 소비되지 않았다.
17. Global3에서 auto-freeze만 해제해 native topology event를 1→3회로 늘렸지만 fixed는
    **21.1846dB**였다. 동일 open-topology KF-only 21.0161보다 +0.1685dB지만,
    auto-freeze global3 21.5429보다 **−0.3583dB**다. Dense evidence를 topology에
    소비하는 것만으로 gain이 커지지 않으며, 계속 열린 topology는 이 예산에서 해롭다.
18. Global3의 uniform random을 모든 슬롯 최소방문 우선으로 바꾸자 137개 후보의 service가
    min/max 7/9회, first/last quarter 평균 8.82/8.53으로 균등해졌지만 fixed는
    **21.3506dB**, random보다 **−0.1923dB**였다. Frame1200+ bin은 control보다
    +0.873dB로 random의 +0.428보다 좋아졌지만, frame0–599 세 bin은 각각
    −0.370/−0.132/−0.462dB로 나빠졌다. Late catch-up만 최대화하면 안정된 초기/중기
    dense retention을 잃으므로 all-balanced는 기각한다.
19. 3개 슬롯 중 1개만 balanced, 2개를 random으로 둔 mixture는 first/last quarter
    13.82/4.09회로 두 극단 사이가 됐고 frame1200+도 control 대비 +0.598dB였다. 그러나
    fixed **21.5099dB**로 KF-only보다 +0.1785, random global3보다 −0.0330dB라 채택하지
    않는다. 현재 scene에서는 단순 random의 안정-view retention이 가장 낫다.
20. Random global3의 membership/pose/topology/KF loss를 고정하고 dense RGB 항만
    1→2배로 키웠다. Native KF/dense view-update는 동일하게 **6,420/1,197회**였고
    fixed는 **21.5252dB**로 KF-only보다 +0.1938dB지만 weight1보다 **−0.0177dB**다.
    Weight2는 frame0–599 세 bin을 weight1보다 +0.308/+0.211/+0.120dB 높인 대신
    frame600 이후 네 bin을 −0.122/−0.214/−0.257/−0.166dB 낮췄다. Dense 신호의
    존재는 재확인되지만 전 구간에 같은 상수 weight를 주는 것으로 +1까지 확대되지는
    않는다. 상수 weight sweep은 중단한다.
21. 최고 random global3와 KF-only를 그대로 반복하자 paired gain은
    **+0.2115/+0.1911dB**(평균 **+0.2013dB**, range 0.0204)로 양수가 2/2
    재현됐다. 특히 repeat1은 dense arm의 total Adam이 3,186회로 control 3,156회보다
    30회만 많지만 +0.1911dB였고, native KF/dense view-update는 두 dense run 모두
    6,420/1,197회로 같았다. 따라서 +0.2dB를 단순 idle-update 우연으로 설명하기는
    어렵다. 반면 목표 +1dB까지는 평균 기준 0.7987dB가 남아 있으므로, strict VIGS에서
    큰 dense 효과가 검증됐다고 표현해서는 안 된다.
22. 동일 scheduler/loss/topology에서 replay scale만 1.5→2.0으로 늘린 causal zero-tail
    진단은 KF-only **21.6809dB**, dense-global3 **21.8221dB**, paired
    **+0.1412dB**였다. 2×에서 total Adam은 각각 7,085/7,991회로 1.5×보다 크게
    늘었지만 dense gap은 반복 평균 +0.2013보다 커지지 않았다. 오히려 dense arm은
    906회 더 많은 idle KF Adam까지 받았으므로, 현재 +1 미달의 주원인을 단순 map-iter
    부족 하나로 볼 수 없다. Frame 0–1199 여섯 bin은 dense가 +0.117~+0.338dB였고
    1200–1398만 −0.146dB였다. Common estimated trajectory 교차 렌더의 dense-map
    우위도 +0.0179/+0.2772dB로 양수였지만 비대칭이어서, 공식 own-trajectory PSNR은
    map과 tracking trajectory를 함께 평가하는 system metric으로 유지한다. 2×는
    공식 fixed-1.5× strict acceptance가 아니라 budget 병목 진단이다.
23. Final-v7 dense-only replay(B)에 native dense-global3를 더한 E는 fixed
    **21.3293dB**로 B보다 **−0.1574dB**였다. 같은 native dense view-update 420회를
    유지하고 interval 등록만 frontier `map()` 전으로 옮긴 F는
    **21.1035dB**, E보다 **−0.2258dB**였다. F는 pre-frontier 59 packet/536 record를
    실제 등록했고 queue drop record도 다음 packet으로 인계했지만, pool은 317→552로
    급증하고 completed Adam은 3,466→3,068로 감소했다. 즉 이 구조에서는 dense의
    frontier 선행 등록이 topology 정보를 유익하게 앞당기기보다 adaptive admission과
    wall-clock service를 교란한다. E도 B보다 낮으므로 native global slot 교체 자체도
    final-v7 replay-only보다 열세다. 다음 축은 B 구조를 보존하고 optical trajectory
    filler만 이미 causal 검증된 저비용 IMU rotation bridge로 교체해 pose 품질과 service
    비용을 분리한다.
24. Final-v7 adaptive admission 경로에서 IMU bridge residual이 record에 저장되지 않아
    첫 PGBA가 corrected dense pose를 interpolation으로 덮어쓰는 별도 버그를 발견했다.
    Pilot은 refresh 289/재적용 0장, fixed **19.6242dB**였다. 일반 경로와 같은 residual
    보존을 구현한 뒤 refresh 316/재적용 312장, fixed **21.1924dB**로 +1.5682dB
    회복했다. 수정 자체는 채택하지만, 유효 G는 KF-only A보다 −0.0544dB, optical B보다
    −0.2942dB다. IMU interval 계산은 1.256초로 optical B의 7.785초보다 싸지만 total
    Adam은 오히려 3,508→2,887로 줄었다. Adaptive phase 전환·map growth가 pose source
    변화에 함께 반응하므로 계산비 절감이 곧 optimizer service 회복을 보장하지 않는다.
    따라서 IMU pose-source 교체도 +1 경로로 기각한다.
25. B와 selection law가 같은 관측-only H에서도 fixed가 **21.4867→21.0909dB**,
    pool이 **310→543**, total Adam이 **3,508→2,715**로 갈렸다. H의 1,826개
    view-epoch 행 중 이전 loss가 있는 1,112개 pair의 progress 중앙값은 0.0501,
    양수 비율은 75.6%였다. Spearman은 progress↔현재 loss −0.197,
    progress↔Fisher novelty −0.095로, raw loss·coverage·learning progress가 같은
    신호가 아님을 확인했다. Loss quartile별 progress 중앙값도
    0.0728/0.0692/0.0341/0.0325로 높은 residual이 오히려 덜 학습되는 경향이었다.
    반면 첫 PGBA 뒤에는 대부분 view가 단 한 번의 paired observation만 가져 per-view
    progress 자체가 아직 희소하다. 따라서 high-loss 우선이나 progress-only sampler를
    바로 넣지 않고, 먼저 completed-work에 대한 deterministic token admission으로 pool
    성장과 service 분모를 고정한다.
26. Exp73 token-only \(\kappa=22\)를 그대로 전이한 I는 global bootstrap 1장과 paid
    50장만 admission해 pool이 51장으로 굶었고 fixed **20.0185dB**였다. Replay
    selection first/last-quarter mean은 63.92/4.75, CV 1.337로 early cohort를 반복하면서
    새 coverage를 잃었다. 같은 \(\kappa\)가 Aria1253/305에서는 품질을 보존했더라도,
    5070 strict UTMM의 짧은 completed-work horizon에는 동일한 absolute token-only
    pacing이 전이되지 않는다. 반대로 intended flag가 꺼진 pilot도 pool 421/
    fixed 21.2030으로 B의 pool 310/fixed 21.4867을 재현하지 못했다. 따라서 숫자 \(\kappa\)
    sweep을 하지 않고, 기존 per-interval bootstrap을 보존해 arrival coverage를 고정한 채
    **paid admission의 maturity 조건만 completed-work token으로 교체**한다.
27. Interval bootstrap을 보존한 J는 의도대로 bootstrap 140+paid 127=267장을 만들고
    replay 3,192회·total Adam 3,708회를 확보했지만 fixed는 **20.9872dB**였다.
    A보다 −0.2595, B보다 −0.4994이고 last/first-quarter selection ratio도 0.271이다.
    즉 I의 실패가 bootstrap 제거 때문인 것은 맞지만, 이를 복원해도 maturity gate 제거가
    +1 경로가 되지는 않았다. Final-v7 adaptive family는 admission·PGBA·wall-time 분기가
    pool과 trajectory를 함께 바꾸어 scheduler 효과를 분리하기 어렵다. 반면 native
    dense-global3는 view-update 1,197회가 두 repeat에서 동일하고 paired gain
    +0.2115/+0.1911을 재현했으므로 다음 selection 실험의 안정 기반으로 채택한다.
28. Native global3 관측-only K는 dense 129장에 912개의 same-view progress pair를
    확보했고 fixed **21.4482dB**(repeat KF 대비 +0.1508), native dense update 1,197회를
    유지했다. Dense progress 중앙값은 0.0258, positive fraction 65.35%였다. 그러나
    previous progress의 next absolute gain 예측 Spearman은 0.080뿐이고 previous loss는
    0.315였다. 관측 시점의 current loss↔current progress는 −0.201이라 두 값은 같은
    의미가 아니지만, 실제 scheduling 시점에 이용 가능한 **직전 loss**가 다음 gain을 더
    잘 예측한다. 따라서 progress-only를 기각하고 robust-capped residual을 remaining-gain
    proxy로 쓴다. Fisher는 이 dense_rr 경로에서 0이므로 거짓 coverage 신호로 쓰지 않고,
    이미 검증한 least-served count 한 슬롯으로 causal arrival coverage를 표현한다.
29. L pilot의 residual scheduler는 view cardinality를 바꾸지 않았지만 loss EMA를 매
    mapping iteration CPU로 가져오면서 KF idle replay가 2,701→1회, total Adam이
    3,482→782회로 줄었다. Fixed 20.0983dB는 selection law가 아니라 optimizer service
    붕괴의 결과라 invalid 처리한다. Residual은 새 render/backward가 없어도 CPU
    materialization 위치가 strict wall-clock budget을 소비하므로, K의 map-call batched
    progress transfer에서 같은 float를 재사용해야 한다.
30. Batched transfer로 고친 L은 idle KF replay 2,807·Adam 3,588로 service를 회복했지만
    fixed **21.3731dB**였다. Repeat KF보다 +0.0757이나 K보다 −0.0751, random dense
    repeat보다 −0.1154다. Residual+coverage가 late service는 늘렸어도 final held-out
    quality를 높이지 못했으므로, local one-step gain과 global reconstruction objective의
    차이가 실재한다. Score/slot sweep은 중단하고, 이미 양수인 random native-global3를
    유지한 채 KF native RGBD+normal은 모두 보존하면서 **idle replay source만 compact
    dense RGB로 교체**해 부족한 dense update 총량을 검증한다.
31. Exp83-M은 random native-global3와 native KF RGBD+normal view-update
    **6,420/1,197회**를 그대로 두고, idle replay만 KF 100%에서 dense 100%로 바꿨다.
    Dense replay 3,192회와 total Adam 3,973회를 확보했지만 fixed PSNR은
    **21.2360dB**로 repeat KF-only 21.2974보다 **−0.0614dB**, 같은 random-global3
    repeat 21.4886보다 **−0.2525dB**였다. 반면 fixed SSIM은
    0.70093→**0.71682**, LPIPS는 0.33419→**0.31502**로 좋아졌다. 즉 dense RGB가
    쓸모없는 것은 아니지만, idle KF geometry/appearance 재학습을 전부 치환하면 MSE
    기준 색 정확도가 손해다. Dense update 총량 부족 단독가설은 기각하고, 다음 N에서는
    과거 strict arm에서 가장 근거가 좋았던 **idle KF75/dense25**만 random-global3와
    결합해 geometry retention과 dense perceptual 신호의 중간점을 한 번 검증한다.
32. Exp83-N은 M과 같은 native KF/dense 6,518/1,218회 및 compact pool 139장을
    유지하면서 idle replay를 실측 **KF 2,244/dense 748회(75/25)**로 배분했다.
    Fixed는 **21.5855dB**로 repeat KF-only보다 **+0.2880dB**, 같은 random-global3
    repeat보다 **+0.0969dB**여서 native 계열 새 최고다. Total Adam 3,780회,
    deadline/EOS tail 0/0이다. Fixed SSIM 0.71670은 KF 0.70093보다 좋아졌지만 LPIPS
    0.32634는 KF 0.33419 대비 소폭만 개선됐고, M의 dense100보다 나빴다. KF replay를
    보존하며 dense를 섞는 방향은 맞지만 +1까지 0.7120dB가 남는다. M/N의 metric 분화를
    근거로 다음 축은 비율 sweep이 아니라 **dense RGB loss와 판정 metric(PSNR=MSE)의
    정렬 여부**를 코드에서 감사한다.
33. 코드 감사에서 native/idle dense가 모두 `_frontier_mapping_view_loss()`의 동일한
    `0.8·L1 + 0.2·(1−SSIM)` 분기를 거침을 확인했다. Exp83-O는 N의 pose/pool/global3/
    KF75:dense25를 유지하고 dense 분기만 MSE에 단조인 RMSE로 바꿨다. Raw MSE처럼
    gradient를 잔차 크기만큼 축소하지 않도록 per-view RMS로 정규화했다. Fixed는
    **21.4978dB**로 repeat KF보다 +0.2004지만 N보다 **−0.0877dB**이고, SSIM/LPIPS도
    0.70019/0.34265로 N의 0.71670/0.32634보다 악화했다. O는 mapping packet 63,
    native KF/dense 6,420/1,197, idle KF/dense 2,070/691, Adam 3,542회로 N의
    64 packet·6,518/1,218·2,244/748·3,780보다 service가 적어 loss 효과가 완전히
    분리되지는 않는다. 그래도 random-global3 repeat보다 fixed +0.0092에 불과해
    **loss metric mismatch가 주병목이라는 증거는 없다.** RMSE mode는 opt-in/default-off로
    남기되 추가 loss sweep은 하지 않는다.

## 구현

- repo: `/home/wosas/Desktop/26-1_RPM/gsProjects/VIGS-SLAM-main-integration-20260828`
- runner: `exp83_axes/run_utmm_kf_dense_joint.sh`,
  `exp83_axes/run_final_v7_kf_dense.sh`
- `imu_rotation_bridge`: right KF가 도착한 뒤 left-KF gyro bias로 구간을 적분하고
  right endpoint SO(3) 잔차를 시간 비례 분배한다. IMU 초기화 전 interval은 등록하지 않는다.
  Adaptive admission도 interpolation 대비 residual을 record에 저장해 PGBA refresh 뒤
  correction을 유지한다(exp83-G에서 누락 버그 수정).
- `--mapping_dense_pose_align_steps`: RR dense draw에서는 이미 계산된 RGB backward의
  camera gradient를 Gaussian optimizer와 하나의 sensor-EOS action으로 처리한다.
  PGBA-controlled interpolation에 대한 residual로 저장해 다음 PGBA에도 유지한다.
- `exp83_axes/evaluate_shared_trajectory.py`: 두 online trajectory 사이 Sim3로 reference
  pose를 map gauge에 옮겨 fixed 281장을 다시 렌더하는 진단 도구다.
- `--background_dense_gt_camera_frame`: diagnostic trajectory orientation을
  `camera` 또는 `utmm_robot`으로 명시하며 provenance와 strict-invalid 로그에 기록한다.
- `--background_dense_pose_source gt_absolute`: mapping camera와 online-final evaluator를
  동일 GT absolute trajectory로 바꾸는 non-strict paired diagnostic이다.
- `--mapping_dense_global_views 1`: native `map()`에서 current-window KF는 보존한 채 6개
  historical-global 슬롯 중 1개를 causal dense RGB로 교체한다. 새 frontier KF/dense
  계측은 `MAP_RR_DONE`에 기록한다.
- `--mapping_dense_prefrontier`: opt-in으로 닫힌 KF interval의 causal dense record를
  같은 packet의 frontier `map()` 직전에 등록한다. 비동기 queue가 packet을 drop하면 해당
  record는 다음 surviving packet으로 넘긴다. E/F 결과로 기본값 off를 유지한다.
- `EXP81_REPLAY_TIME_SCALE`: exp81의 기본 1.5를 보존하면서 명시적 scale ablation만
  허용한다. 비-1.5× pure-online paced replay의 zero-tail audit은
  `scaled_replay_sensor_eos_zero_tail`로 strict 1.5×와 구분한다.
- `mapping_replay_progress.jsonl`: 기존 epoch loss tracker의 view별 current/previous
  loss와 relative progress를 segment(PGBA revision), Fisher novelty, endpoint distance,
  최종 selection count와 함께 **stream 종료 뒤** 기록한다. Selection에는 사용하지 않으며
  H는 이 관측 경로만 활성화한 반복이다.
- `mapping_frontier_progress.jsonl`: native `map()`에서 실제 선택된 KF/dense view의
  call별 loss/progress와 source, endpoint, final selection count를 종료 뒤 기록한다.
  K에서 dense 1,041행/912 pair를 확보했고 selection에는 사용하지 않았다.
- exp81 benchmark runner의 gate-free token flag는 production/default control에서는 계속
  off이고 `EXP81_GATE_FREE_TOKEN_ADMISSION`으로 명시한 경우에만 exp69로 전달된다.
  I의 unwired pilot에서 발견한 강제-off wiring을 이 opt-in 경로로 수정했다.
- `--mapping_token_interval_bootstrap`: gate-free token mode에서 기존 keyframe interval당
  한 장의 causal bootstrap을 유지한다. J에서만 사용하며 기본값은 off다.
- 검사: topology-freeze 제거 뒤 Python compile, shell syntax, `git diff --check`와
  scheduler/replay 집중 회귀검사 **65 passed**. Exp83-P full-sequence 두 번으로 final-v7
  state transition과 online-final map update 0을 확인했다.
- `exp83_axes/run_rpng_final_v7.sh`: RPNG sensor adapter만 설정하고 동일
  `run_final_v7_kf_dense.sh`의 exp83-B policy를 호출한다. 기본 범위는 기존 대표 계약과
  같은 `table_01` 첫 1,000장이다.

## 다음 단일 축

고정 frame/iteration/count에 의한 topology freeze와 topology-event trigger 계열은
종료하고 runtime API에서도 제거했다. 이후 기준은 **final-v7 unknown-horizon controller +
정상 frontier densify/prune**로 고정한다. Q는 current-code paired control이 없으므로 다음
단일 축은 topology/scheduler를 바꾸지 않고 동일 HEAD·seed·stream에서 final-v7 KF-only를
UTMM/RPNG 각각 한 번 실행하는 것이다. 그 pair 전에는 Q의 dataset 차이나 dense gain을
원인으로 확정하지 않는다.

exp83-R은 Q와 original `origin/main@22ffe24c`를 정확히 같은 RPNG `table_01`
첫 1,000장에 놓고 vanilla가 학습한 keyframe을 양쪽 evaluator에서 함께 제외했다.
185-view shared held-out은 custom **18.9377dB**, vanilla **23.8599dB**로 custom가
**−4.9222dB**였다. Vanilla는 `--pure_online`이라 final BA와 26k color refinement를
실행하지 않았지만 synchronous/unbounded online mapping이라 222.74초(종료 뒤 평가 포함)를
사용했다. 따라서 이 결과는 같은 wall-budget pair가 아니라, 더 많은 online 계산을 허용한
원본 vanilla에 대한 no-offline-polish 품질 기준선이다. 이를 포함한 전체 UTMM/RPNG/Aria
vanilla 기준선은 별도 `benchmark_vanila` 카드에서 확장한다.

## 주요 산출물

- `results/benchmarks/exp83_kf_dense_supervision/utmm/ego-drive/kf_only_b1_native_seed0/`
- `results/benchmarks/exp83_kf_dense_supervision/utmm/ego-drive/kf90_dense10_b1_imu_midpoint_postinit_seed0/`
- `results/benchmarks/exp83_kf_dense_supervision/utmm/ego-drive/kf75_dense25_b1_imu_midpoint_postinit_seed0/`
- `results/benchmarks/exp83_kf_dense_supervision/utmm/ego-drive/kf75_dense25_b1_optical_midpoint_postinit_seed0/`
- `results/benchmarks/exp83_kf_dense_supervision/utmm/ego-drive/kf50_dense50_b2_imu_midpoint_postinit_seed0/`
- `results/benchmarks/exp83_kf_dense_supervision/utmm/ego-drive/kf75_dense25_b1_imu_midpoint_pgba_residual_seed0/`
- `results/benchmarks/exp83_kf_dense_supervision/utmm/ego-drive/kf75_dense25_b1_imu_midpoint_posealign_seed0/`
- `results/benchmarks/exp83_kf_dense_supervision/utmm/ego-drive/kf75_dense25_b1_gt_relative_midpoint_oracle_seed0/` (invalid camera-frame pilot)
- `results/benchmarks/exp83_kf_dense_supervision/utmm/ego-drive/kf75_dense25_b1_gt_relative_midpoint_utmmcam_oracle_seed0/`
- `results/benchmarks/exp83_kf_dense_supervision/utmm/ego-drive/kf75_dense25_b1_imu_stride40_repeat_seed0/`
- `results/benchmarks/exp83_kf_dense_supervision/utmm/ego-drive/kf_only_b1_open_topology_seed0/`
- `results/benchmarks/exp83_kf_dense_supervision/utmm/ego-drive/kf90_dense10_b1_imu_midpoint_dense_topology_seed0/`
- `results/benchmarks/exp83_kf_dense_supervision/utmm/ego-drive/kf_only_b1_gt_absolute_oracle_fixed_seed0/`
- `results/benchmarks/exp83_kf_dense_supervision/utmm/ego-drive/kf75_dense25_b1_gt_absolute_midpoint_oracle_seed0/`
- `results/benchmarks/exp83_kf_dense_supervision/utmm/ego-drive/kf75_dense25_b1_imu_midpoint_early_topology_deferred_seed0/`
- `results/benchmarks/exp83_kf_dense_supervision/utmm/ego-drive/kf75_dense25_b1_imu_midpoint_early_topology16_seed0/`
- `results/benchmarks/exp83_kf_dense_supervision/utmm/ego-drive/kf100_denseglobal1_b1_imu_midpoint_seed0/`
- `results/benchmarks/exp83_kf_dense_supervision/utmm/ego-drive/kf100_denseglobal3_b1_imu_midpoint_seed0/`
- `results/benchmarks/exp83_kf_dense_supervision/utmm/ego-drive/kf100_denseglobal3_b1_imu_midpoint_open_topology_seed0/`
- `results/benchmarks/exp83_kf_dense_supervision/utmm/ego-drive/kf100_denseglobal3_balanced_b1_imu_midpoint_seed0/`
- `results/benchmarks/exp83_kf_dense_supervision/utmm/ego-drive/kf100_denseglobal3_mix1_b1_imu_midpoint_seed0/`
- `results/benchmarks/exp83_kf_dense_supervision/utmm/ego-drive/kf100_denseglobal3_w2_b1_imu_midpoint_seed0/`
- `results/benchmarks/exp83_kf_dense_supervision/utmm/ego-drive/kf_only_b1_native_repeat1_seed0/`
- `results/benchmarks/exp83_kf_dense_supervision/utmm/ego-drive/kf100_denseglobal3_b1_imu_midpoint_repeat1_seed0/`
- `results/benchmarks/exp83_kf_dense_supervision/utmm/ego-drive/kf_only_b1_budget2x_seed0_r1/`
- `results/benchmarks/exp83_kf_dense_supervision/utmm/ego-drive/kf100_denseglobal3_b1_imu_midpoint_budget2x_seed0/`
- `results/benchmarks/exp83_kf_dense_supervision/utmm/ego-drive/exp83-A-v7_kf_only-seed0/`
- `results/benchmarks/exp83_kf_dense_supervision/utmm/ego-drive/exp83-B-v7_causal_dense-seed0/`
- `results/benchmarks/exp83_kf_dense_supervision/utmm/ego-drive/exp83-E-v7-dense-global3-postfrontier-seed0/`
- `results/benchmarks/exp83_kf_dense_supervision/utmm/ego-drive/exp83-F-v7-dense-global3-prefrontier-seed0/`
- `results/benchmarks/exp83_kf_dense_supervision/utmm/ego-drive/exp83-G-v7_dense_imu_rotation-seed0/` (adaptive residual 누락 invalid pilot)
- `results/benchmarks/exp83_kf_dense_supervision/utmm/ego-drive/exp83-G-v7_dense_imu_rotation_pgba_residual-seed0/`
- `results/benchmarks/exp83_kf_dense_supervision/utmm/ego-drive/exp83-H-v7_dense_progress_observe-seed0/`
- `results/benchmarks/exp83_kf_dense_supervision/utmm/ego-drive/exp83-I-v7_dense_gatefree_k22-seed0/` (flag가 exp81에서 꺼진 invalid I pilot)
- `results/benchmarks/exp83_kf_dense_supervision/utmm/ego-drive/exp83-I-v7_dense_gatefree_k22-wired-seed0/`
- `results/benchmarks/exp83_kf_dense_supervision/utmm/ego-drive/exp83-J-v7_dense_intervalbootstrap_token_k22-seed0/`
- `results/benchmarks/exp83_kf_dense_supervision/utmm/ego-drive/exp83-K-native_global3_progress_observe-seed0/`
- `results/benchmarks/exp83_kf_dense_supervision/utmm/ego-drive/exp83-L-native_global3_residual1_coverage1_random1-seed0/` (per-iteration sync invalid pilot)
- `results/benchmarks/exp83_kf_dense_supervision/utmm/ego-drive/exp83-L-native_global3_residual1_coverage1_random1-batched-seed0/`
- `results/benchmarks/exp83_kf_dense_supervision/utmm/ego-drive/exp83-M-native_global3_idle_dense-seed0/`
- `results/benchmarks/exp83_kf_dense_supervision/utmm/ego-drive/exp83-N-native_global3_idle_kf75_dense25-seed0/`
- `results/benchmarks/exp83_kf_dense_supervision/utmm/ego-drive/exp83-O-native_global3_idle_kf75_dense25_rmse-seed0/`
- `results/benchmarks/exp83_kf_dense_supervision/aria1253/exp83-P_final_v7_no_topology_freeze/`
- `results/benchmarks/exp83_kf_dense_supervision/aria1253/exp83-P_final_v7_no_topology_freeze_r2/`
- `results/benchmarks/exp83_kf_dense_supervision/utmm/ego-drive/exp83-Q-final_v7_dense_no_topology_freeze-seed0/`
- `results/benchmarks/exp83_kf_dense_supervision/rpng/table_01/exp83-Q-final_v7_dense_no_topology_freeze-seed0/`
- `results/benchmarks/exp83_vigs_vanilla5070/rpng/table_01/origin22ffe24_pure_online_first1000_seed0/`
- `evidence/exp83-R-rpng-first1000-shared.json`
- `run_rpng_vanilla_pure_online.sh`
