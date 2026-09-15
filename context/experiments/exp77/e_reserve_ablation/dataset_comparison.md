# 기존 Aria와 RPNG/UT-MM benchmark 데이터 비교

정리일: 2026-09-11. 목적은 1253/305에서 얻은 품질이 RPNG/UT-MM으로 전이되지 않는
원인을 찾기 위해, 데이터 자체의 차이와 현재 실행 recipe의 차이를 분리하는 것이다.

`dense replay`는 admission된 non-keyframe RGB view를 background optimizer가 다시
선택한 횟수다. `pool`은 최종 admission view 수이며 `Adam`은 mapping/birth 등을 포함한
전체 완료 optimizer step이라 두 수치는 동일하지 않다. 스레드별 wall timer는 서로
겹치므로 합산해 GPU time으로 해석하지 않는다.

## 1. 데이터 자체

해상도는 `W×H`다. RPNG/UT-MM의 범위·합계는 각각 8개 sequence 전체 기준이다.

| 데이터 | Sequence 수 | RGB 형식 | Raw RGB | VIGS 입력 | RGB frame | 녹화 길이 | RGB rate | IMU rate | 평가 view | 로컬 크기 |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Aria 301_1253 | 1 | JPEG | 1024×1024 | 464×464 | 1,303 | 65.10s | 20Hz | 약 1,000Hz | fixed 262 | RGB 275MiB |
| Aria 301_305 | 1 | JPEG | 1024×1024 | 464×464 | 2,688 | 134.35s | 20Hz | 약 1,000Hz | fixed 539 | RGB 503MiB |
| RPNG AR Table | 8 | PNG | 848×480 | 616×344 | 합계 40,693; 2,506–8,484/seq | 합계 1,356.81s; 83.54–282.89s/seq | 약 30Hz | 400Hz | 1/5 fixed split | 전체 해제본 27.35GiB |
| UT-MM | 8 | PNG | 1280×660 | 648×328 | 합계 8,387; 332–1,614/seq | 합계 279.43s; 11.04–53.81s/seq | 약 30Hz | 100Hz | 1/5 fixed split | 전체 해제본 21.27GiB |

VIGS에 들어가는 pixel 수는 Aria 215,296, RPNG 211,904, UT-MM 212,544로
Aria 대비 각각 98.4%, 98.7%다. 따라서 네트워크 입력 pixel 수 자체는 거의 같다.
다만 benchmark는 PNG이고 raw 파일이 크므로 decode/I/O 특성은 다르다.

## 2. 목표 품질 reference와 현재 진단 run

아래 A2 두 행은 같은 채택 tracking recipe의 기존 성공 reference다. exp79와 exp77E2는
현재 fixed-1× zero-tail 비교다. A2의 `BACKGROUND_POLISH_DONE`과 최신
`MAP_RR_DONE.dense_updates`는 같은 background dense optimization 역할이지만 계측 세대가
달라 완전히 동일한 counter로 보지는 않는다.

| Run | Protocol / tracking | Frame 간격 및 budget | IMU init 시작 | 최종 KF | Dense pool | Dense replay | Replay/s | Replay/pool | Adam | 최종 GS | Fixed held-out PSNR |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1253 A2 reference | 약 1.5×; thresh 2.6, radius 2, iters1 2 | 50ms; 101.06s 관측 | frame 195/1303, 15.0% | 123 | 454 | 4,699 | 46.5 | 10.35 | 구계측 미기록 | 95,954 | 27.843dB |
| 305 A2 reference | 약 1.5×; thresh 2.6, radius 2, iters1 2 | 50ms; 205.00s 관측 | frame 312/2688, 11.6% | 170 | 1,020 | 10,000 (cap) | 48.8 | 9.80 | 구계측 미기록 | 74,202 | 29.834dB |
| 1253 exp79 repeat1 | fixed 1× zero-tail; final-v7 | 50ms; 65.10s | frame 185/1303, 14.2% | 124 | 404 | 6,613 | 101.6 | 16.37 | 6,895 | 97,509 | 27.499dB |
| RPNG table_06 E2 reserve0 평균 | fixed 1× zero-tail; thresh 3.6, radius 1, iters1 1; Droid TRT off | 33.3ms; 92.24s | frame 385/2767, 13.9% | 225 | 420 | 2,105 | 22.8 | 5.01 | 2,485 | 약 293,683 | 21.426dB |
| UT-MM fast-straight exp80 | fixed 1× zero-tail; thresh 3.6, radius 1, iters1 1; Droid TRT off | 33.3ms; 11.04s | frame 241/332, 72.6% | 14 | 13 | 0 | 0 | 0 | 65 | 2,524 | 4.896dB |

가장 가까운 1× 비교에서 1253 repeat1과 table_06은 dense pool이 404 대 420으로 거의
같다. 그런데 replay는 6,613 대 2,105, pool당 선택은 16.37 대 5.01이다. table_06은
frame 수가 2.12배인데 각 admitted view를 평균 1/3만 학습했다. 최종 map은 97.5k 대
293.7k Gaussian으로 약 3.0배 커졌고 replay step wall EMA도 3.09ms 대 6.92–7.76ms로
약 2.2–2.5배 비싸졌다.

## 3. fixed-1× benchmark 전체 결과

exp77 D/이전 exp80의 동일 1× optimizer-zero-tail 실행이다. 실패 run은 품질 평균에서
빠졌지만 시도 수에서는 유지한다.

| Dataset | Sequence | RGB frame | 녹화/budget | Dense replay | Adam | Pool | 최종 GS | Fixed held-out PSNR | 상태 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| RPNG | table_01 | 2,506 | 83.54s | 1,515 | 1,882 | 460 | 393,229 | 20.250 | 완료 |
| RPNG | table_02 | 2,914 | 97.17s | 2,085 | 2,413 | 625 | 621,089 | 16.644 | 완료 |
| RPNG | table_03 | 7,006 | 233.60s | 5,793 | 6,145 | 995 | 975,529 | 17.381 | 완료 |
| RPNG | table_04 | 6,068 | 202.34s | 5,256 | 5,665 | 820 | 758,621 | 17.041 | 완료 |
| RPNG | table_05 | 6,164 | 205.52s | 6,070 | 6,446 | 628 | 469,700 | 21.161 | 완료 |
| RPNG | table_06 | 2,767 | 92.24s | 2,101 | 2,459 | 420 | 293,837 | 21.442 | 완료; E2 이전 40ms run |
| RPNG | table_07 | 4,784 | 159.51s | — | — | — | — | — | PGBA index assert |
| RPNG | table_08 | 8,484 | 282.89s | — | — | — | — | — | frontend OOM |
| UT-MM | ego-centric-1 | 1,535 | 51.15s | 1,442 | 1,772 | 188 | 72,135 | 19.125 | 완료 |
| UT-MM | ego-centric-2 | 1,298 | 43.24s | 1,451 | 1,765 | 456 | 78,304 | 17.980 | 완료 |
| UT-MM | ego-drive | 1,399 | 46.63s | 1,598 | 1,968 | 329 | 111,042 | 20.976 | 완료 |
| UT-MM | fast-straight | 332 | 11.04s | 0 | 65 | 13 | 2,524 | 4.896 | init이 72.6% 지점 |
| UT-MM | slow-straight-1 | 393 | 13.08s | 0 | — | 0 | — | — | 13 KF로 init threshold 미달 |
| UT-MM | slow-straight-2 | 597 | 19.87s | 0 | 163 | 17 | 26,197 | 18.348 | init이 76.4% 지점 |
| UT-MM | square-1 | 1,614 | 53.81s | 3,386 | 3,646 | 608 | 108,187 | 13.589 | 완료 |
| UT-MM | square-2 | 1,219 | 40.62s | 2,017 | 2,293 | 176 | 103,374 | 15.648 | render 완료, tracking 실패 |

평가 성공 sequence만 합치면 RPNG 6개는 replay 22,820회, weighted pool당 5.78회,
평균 18.986dB다. UT-MM 7개는 replay 9,894회, weighted pool당 5.54회, 평균
15.794dB다. 단, 짧은 두 straight sequence는 replay가 0이므로 family 평균이 이 실패를
가린다.

## 4. 이 표에서 바로 보이는 confound와 병목

1. **현재 저장된 최고치 대 benchmark는 dataset-only matched comparison이 아니다.**
   305의 29.834dB는 1.5×와 A2 tracking을 사용했지만 benchmark는 1×와 기본
   thresh 3.6/radius 1/iters1 1이다. benchmark config는 지금도 Aria1253에서 fit한
   `adaptive_density_curve`를 가리킨다.
2. **입력 pixel 수보다 cadence와 frame당 시간 예산 차이가 훨씬 크다.** A2 Aria는
   약 76–78ms/frame을 쓸 수 있지만 30Hz fixed-1× benchmark는 33.3ms/frame뿐이다.
   1253 fixed-1×도 50ms/frame이라 RPNG/UT-MM보다 1.5배 여유가 있다.
3. **table_06의 tracking 자체는 느슨하지 않다.** 약 26ms/frame으로 Aria와 비슷하지만
   33ms slot에서는 남는 시간이 약 7ms뿐이다. 기존 40ms reserve는 overlap을 0회로
   만들었다. E2에서 reserve를 0으로 줄여도 replay는 2,105회, PSNR은 21.426dB이므로
   cadence 문제는 실재하지만 잔여 격차 전부는 아니다.
4. **RPNG map workload가 더 빨리 커진다.** table_06은 Aria repeat1과 pool은 같은데
   Gaussian은 약 3배이고 replay step 하나도 2배 이상 비싸다. 따라서 admission 수,
   map growth, replay 서비스율을 같이 봐야 한다.
5. **UT-MM short sequence는 별도 문제다.** useful mapping window가 init에 의해 거의
   사라져 fast/slow-straight에서 dense replay가 0이다. 긴 sequence용 파라미터를 그대로
   적용한 결과로 보는 것이 맞다.

따라서 다음 TensorRT on/off 비교에서는 PSNR만이 아니라 `tracking wall/frame`,
`dense replay/s`, `replay/pool`, `final GS`, `init frame fraction`을 함께 기록해야 한다.
TensorRT로 replay 수가 늘어도 PSNR이 21dB대에 머물면 다음 우선순위는 compute가 아니라
RPNG의 map growth/admission/초기 depth·pose consistency다.
