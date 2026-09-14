# benchmark_custom — dense-supervision VIGS tuning

날짜: 2026-09-14
상태: **대표 장면 튜닝 진행 중; final 16-scene 미생성**

## 목표

Original vanilla의 [`5070ti_1.5x_streaming`](../benchmark_vanila/5070ti_1.5x_streaming/README.md)
held-out PSNR보다 여러 장면에서 안정적으로 높은 하나의 custom recipe를 만든다.
최종 recipe는 causal dense RGB supervision을 실제 optimizer source로 사용하고,
scene 이름·절대 frame·고정 topology-freeze 시점에 의존하지 않아야 한다.

## 실행 계약

- 입력: timestamp 순 RGB+IMU, source timestamp 간격의 1.5x pacing
- 실행: tracking과 Gaussian mapping을 병렬 수행
- 종료: 마지막 RGB 뒤 이미 제출된 frontier packet만 drain
- 금지: terminal replay epoch, final BA, color refinement, background polish,
  topology freeze, MPS/post-hoc pose·depth 입력
- 평가: `idx % 5 == 0` fixed evaluator를 mapping supervision에서 제외한
  online-final PSNR/SSIM/LPIPS
- 실시간 진단: tracking lateness와 map drain은 별도 기록하되, paced-drain
  품질 결과를 strict zero-tail 성과라고 부르지 않는다.

## 과적합 방지 계약

- Aria1253에서 미리 fit한 `adaptive_density_curve`는 사용하지 않는다.
- density는 도착한 content의 정규화 rank만 쓰는 `online_rank`이며 scene 파일,
  stream length, 절대 frame boundary가 없다.
- topology event/freeze 시점과 late-mapping 시작 frame을 튜닝하지 않는다.
- 센서별로 달라지는 항목은 calibration, IMU noise/frequency, undistortion뿐이다.
- 먼저 고정한 3–4개 대표 scene에서 한 축씩 비교하고, 최종 후보가 정해진 뒤에만
  UTMM/RPNG 전체 16 scene을 실행한다.

## 대표 panel과 vanilla target

| family | scene | 선택 이유 | vanilla streaming PSNR |
|---|---|---|---:|
| UTMM | `ego-drive` | 기존 dense 연구 개발 장면, 중간 길이 | 20.2615 |
| UTMM | `fast-straight` | 짧고 저운동, 초기 map service guard | 17.4259 |
| RPNG | `table_01` | RPNG 표준 장면, full-sequence 전이 | 24.1699 |
| RPNG | `table_04` | 긴 장면과 후반 drift guard | 20.7658 |

한 arm이 위 네 장면 전부 또는 최소 3/4에서 vanilla를 이기고 평균도 양수일 때만
final 후보로 승격한다. 결과가 나쁜 arm은 전체 16 scene으로 확장하지 않는다.

## exp85 arms

| arm | 공통 | optimizer source 차이 | 상태 |
|---|---|---|---|
| exp85-A | final-v7, RGB-only, online-rank, paced-drain | idle KF100, native dense 0 | `ego-drive` 22.1981 / RPNG `table_01` 20.2364 dB |
| exp85-B | A와 동일 | idle KF100 + native historical dense RGB 3/6 | **gate 실패:** 1승 2패, `table_04` 중단 |
| exp85-C | B와 동일 | idle KF75/dense25 + native dense 3/6 | 공통 RPNG recipe 회복 전 보류 |
| exp85-D | A와 동일하되 KF RGBD(alpha=.95)+normal(.5) 복구 | idle KF100, native dense 0 | RPNG `table_01` fixed 19.9879 dB, A보다 -0.2485; 기각 |
| exp85-E | D와 동일하되 init map 600→1050 | idle KF100, native dense 0 | RPNG `table_01` fixed 19.8691 dB, D보다 -0.1187; 기각 |
| exp85-F | E와 동일하되 point birth를 vanilla uniform 64/32로 복구 | idle KF100, native dense 0 | RPNG `table_01` fixed 19.8453 dB, E보다 -0.0238; 기각 |
| exp85-G | F와 동일하되 motion filter 3.6→2.4 | idle KF100, native dense 0 | RPNG `table_01` fixed 19.9195 dB, +0.0741지만 느리고 기각 |
| exp85-H | D에서 mapping queue drop 제거(no-drop backpressure) | idle KF100, native dense 0 | RPNG `table_01` fixed 20.1342 dB, D보다 +0.1463; 구조 유지 후보 |
| exp85-I | H와 동일 | native historical dense RGB 3/6 추가 | RPNG `table_01` fixed 20.1043 dB, I−H -0.0299; dense 기각 |
| exp85-J | H에서 model controller의 frontier 축소/1-view replay 치환 해제, packet당 constant frontier 10 | full multi-view frontier, dense 0, idle replay 0 | RPNG `table_01` fixed 19.1974 dB, J−H -0.9368; 기각 |
| exp85-K | H에서 upstream frontend contract(window25/radius2/BA4+2/motion2.4) 복구 | final-v7 KF-only, no-drop | RPNG `table_01` fixed 19.6051 dB, K−H -0.5291; 기각 |
| exp85-L | custom 코드에서 scheduler/idle/dense를 끄고 upstream map recipe 묶음 복구, isotropic만 제외 | KF-only, drop-oldest, frontend·init·birth·loss·service upstream parity | vanilla와 같은 non-KF 463장 **24.2752dB**(+0.1054); 품질 GO, 실행 중 wrapper 수정으로 telemetry log 불완전 |
| exp85-M | L에서 upstream isotropic scale loss까지 복구 | 완전 upstream map recipe parity | non-KF463 **24.2463dB**(+0.0764 vs vanilla), parity GO; 358.004초라 realtime acceptance 아님 |
| exp85-N | M의 global2 중 historical KF 1개를 causal midpoint dense RGB로 교체 | 동일 10 step/총 view 수, dense full Gaussian gradient·topology stats | non-KF463 **23.8979dB**, N−M -0.3484; 기각 |
| exp85-O | M의 KF backward·global2·topology를 보존하고 dense gradient를 별도 투영 | 마지막 1 step, dense batch1, geometry norm0, appearance/opacity PCGrad cap0.25 | non-KF463 **24.2333dB**, O−M -0.0130; 무손실이나 gain 없음 |
| exp85-P | O의 projected dense batch만 1→4 | 215 projected step/860 dense view, cap0.25 | non-KF463 **24.2625dB**, P−M +0.0162; 양수지만 +1 실패 |
| exp85-Q | P의 projected dense norm cap만 0.25→1.0 | batch4/geometry0/regular service 유지 | non-KF463 **24.2413dB**, Q−M -0.0050; cap 부족 가설 기각 |
| exp85-R | P의 projected dense iteration 1→10(all frontier step) | batch4/cap0.25/geometry0 | non-KF463 **24.2234dB**, R−M -0.0230; 빈도 증가 기각 |
| exp85-S | R의 queue만 drop-oldest→unbounded no-drop | 243/243 causal packet+각 step dense | non-KF463 **24.1253dB**, vanilla -0.0445; 절대 gate 실패 |
| exp85-T | P의 cyclic dense 선택→residual2+least-served2 | 동일 216 step/864 view | non-KF463 **24.2979dB**, T−P +0.0354; 양수·집중 개선 필요 |
| exp85-U | T residual score에 `1/sqrt(1+n)` 한계이득 감쇠 | projected-last1/batch4/cap0.25/geometry0 고정 | table_01 **+0.1847**, table_04 **+0.4615**, ego-drive **+0.3148**, fast-straight **+0.0316dB**; 4/4 양수·+1 실패 |
| exp85-V | U dense 고정, historical KF global2도 residual1+coverage1 marginal 선택 | 추가 render 없음, map-call당 loss sync 1회 | table_01 non-KF463 **23.8075dB**, U -0.5471/vanilla -0.3624; 기각 |
| exp85-W | M의 historical KF global2 중 1회를 U dense appearance로 고정-budget 교체 | current-window geometry/topology 보존, 총 historical render 동일 | non-KF463 **23.9327dB**, M -0.3137/vanilla -0.2372; 기각 |
| exp85-X | upstream parity의 Gaussian SH0→SH1, KF-only와 U dense 짝비교 | 실제 SH1 보존 버그 수정 후 common463 비교 | KF **24.5224**, dense **24.5270dB**(dense +0.0046); SH1 자체는 vanilla +0.35이나 dense 상호작용은 기각 |
| exp85-Y | X dense와 동일 동작에 gradient/progress telemetry만 추가 | 추가 render·per-step host sync 없음 | common463 **24.4137dB**; appearance 충돌 2–4%, projection 잔존 99%+, cap100%; residual cache의 PGBA pose-revision staleness 발견 |

Native frontier의 현재-window tracked keyframe은 모든 arm에서 그대로 RGB supervision을
받는다. exp85-B/C의 dense view는 닫힌 keyframe interval 안에서 인과적으로 생성한
IMU rotation-bridge pose와 RGB-only loss를 사용한다.

## 구현·재현

- code worktree:
  `/home/wosas/Desktop/26-1_RPM/gsProjects/VIGS-SLAM-main-integration-20260828`
- runner: `exp85_axes/run_benchmark_custom.sh`
- configs: `config/exp85_{utmm,rpng}_online_rank_rgb_only.yaml`
- raw tuning: `results/benchmarks/benchmark_custom/tuning/`
- 최종 후보 확정 전에는 `custom_0913_5070ti_1.5x_streaming/`을 만들지 않는다.

## 진행 로그

- **2026-09-14 — protocol 사전등록:** 사용자의 결정에 따라 custom 품질 개발은
  exact 1.5x map cutoff 대신 1.5x-paced concurrent execution과 EOF queue drain으로
  측정한다. 기존 strict runner의 기본 동작은 보존하고 opt-in `paced_drain`에서만
  sensor-EOS cutoff와 replay deadline guard를 해제했다. 종료 후 새 replay epoch는 없다.
- **2026-09-14 — scene-specific density 제거:** 기존 UTMM/RPNG custom config에 남아 있던
  `config/exp55/aria1253_content_curve.json` 의존성을 제거하고, causal normalized
  `online_rank` policy로 교체했다.
- **2026-09-14 — exp85-A 최초 pilot 무효:** `v7` compatibility alias가 runner의
  `terminal_prune=off` 표기와 달리 stream 종료 뒤 dust-GC로 9,176 Gaussian을 hard
  prune했다. fixed PSNR 22.2194는 후보 판정에서 제외하고 raw 폴더를 보존한다.
  `EXP69_TERMINAL_DUST_GC=0` opt-in을 추가해 이후 A/B는 terminal mutation 없이
  다시 실행한다.
- **2026-09-14 — exp85-A 유효 control:** UTMM `ego-drive`에서 terminal mutation 없이
  fixed held-out PSNR 22.1981, SSIM 0.7355, LPIPS 0.2687을 기록했다. vanilla
  paced-streaming 20.2615 대비 **+1.9366 dB**다. EOF map drain은 약 0.28초였고,
  terminal prune/commit과 dense-view update는 모두 0이었다. 전체-view mean 22.5055는
  판정에 사용하지 않는다.
- **2026-09-14 — exp85-B `ego-drive`:** fixed held-out PSNR 22.2251, SSIM 0.7363,
  LPIPS 0.2677로 A 대비 +0.0270 dB, vanilla 대비 **+1.9636 dB**다. Native
  frontier dense-view update 438회가 실제 발생했고 terminal mutation은 0이었다.
  paced-drain에서는 worker service량이 A 6,426회, B 6,552회로 완전히 같지 않으므로
  작은 A→B 차이를 dense의 순수 인과 효과로 판정하지 않고 panel 전이성부터 본다.
- **2026-09-14 — exp85-B `fast-straight`:** 기존 IMU-bridge 경로는 metric IMU
  초기화 전 dense interval을 막았고 이 짧은 stream은 초기화에 도달하지 않아 dense
  update가 0이었다(held-out 15.9058 dB). 장면 길이 임계값을 추가하는 대신 pre-init
  provisional map에서는 도착한 두 keyframe pose 보간을 허용하고, 실제 IMU gauge
  reset 시 dense pool/pending/seen interval을 폐기·재등록하는 일반 경로를 추가했다.
  깨끗한 재실행은 dense frontier update 84회를 확인했지만 held-out 15.8650 dB로
  vanilla 17.4259 대비 **-1.5609 dB**였다. 따라서 이 scene의 손실은 단순 dense
  비활성 문제로 설명되지 않는다. `preinit`/`preinit_v2` 폴더는 각각 코드 예외와
  잔존 실패 프로세스의 GPU 중첩 때문에 무효이고, `preinit_v3`만 유효하다.
- **2026-09-14 — exp85-A/B RPNG paired 및 B gate 중단:** `table_01` fixed held-out은
  KF control A **20.2364**, dense B **20.1401dB**로 B가 -0.0963dB였다. B의 native
  dense frontier update는 1,059회였지만 vanilla 24.1699에는 A/B 모두 약 -4dB다.
  B는 현재 3개 panel 중 `ego-drive`만 이기고 `fast-straight`, `table_01`에서 졌으므로
  남은 `table_04`를 이겨도 사전등록한 3/4 gate를 통과할 수 없어 실행을 중단했다.
  이 결과는 dense 비율 이전에 공통 final-v7 recipe가 RPNG에서 약하다는 기존 exp83-R
  결론을 full-sequence paced-drain pair로 재확인한다. 따라서 C 비율 sweep보다 vanilla와
  공통 map initialization/loss/density 차이를 한 축씩 복구하는 것이 먼저다.
- **2026-09-14 — exp85-D keyframe RGBD+normal 복구:** exp85-A의 scheduler, tracking,
  초기화, paced-drain 및 KF-only source를 모두 고정하고 keyframe objective만 vanilla와
  같은 `alpha=.95`, `lambda_dnormal=.5`로 복구했다. Dense view는 depth/normal이 없으므로
  여전히 RGB-only 분기를 탄다. RPNG `table_01` fixed는 **19.9879dB**, SSIM 0.5816,
  LPIPS 0.3806으로 A보다 **-0.2485dB**였다. 따라서 잘못된
  RGB-only KF 설정은 바로잡았지만 RPNG 공통 격차의 원인은 아니며, 다음 단일 축은
  map 초기화 service `init_itr_num 600→1050` 복구다.
- **2026-09-14 — exp85-E init map service 복구:** D에서 `init_itr_num`만 600→1050으로
  늘렸다. 이는 첫 map 생성 중 수행되어 terminal 후처리가 아니며 나머지 paced-drain
  계약은 동일하다. RPNG `table_01` fixed는 **19.8691dB**, SSIM 0.5748,
  LPIPS 0.3901로 D보다 **-0.1187dB**였다. Initial optimizer 횟수 부족은 단독 원인이
  아니다. 다음은 point birth policy 전체를 vanilla의 uniform 64/32로 복구한다.
- **2026-09-14 — exp85-F vanilla point-birth 복구:** E의 tracking/scheduler/service를
  고정하고 PPM+online-rank 256/64 대신 upstream uniform-random 64/32 birth만 적용했다.
  RPNG `table_01` fixed는 **19.8453dB**, SSIM 0.5742, LPIPS 0.3819로 E보다
  **-0.0238dB**였다. Map loss, init 반복, birth policy 세 축이 모두 20dB 부근이라
  다음은 custom 221개 vs vanilla 250개의 keyframe stream 차이를 만드는 motion-filter
  threshold 3.6→2.4 단일축이다.
- **2026-09-14 — exp85-G motion threshold 2.4:** F에서 motion threshold만 upstream
  2.4로 낮췄다. Active map 후보는 507→662, frontier optimizer step은 520→644로
  늘었지만 idle KF replay는 2,394→874로 줄고 online loop는 약 129→150초로 느려졌다.
  Fixed는 **19.9195dB**, SSIM 0.5778, LPIPS 0.3619로 F보다 +0.0741dB뿐이다.
  KF 증가 자체도 원인이 아니다. 다음 구조 감사는 queue-full에서
  이미 도착한 frontier packet을 버리는 custom worker 정책을 no-drop backpressure로 바꾸는
  단일축이며, 실패한 F/G birth/frontend 조합이 아니라 올바른 KF geometry의 D에서 분기한다.
- **2026-09-14 — exp85-H no-drop mapping queue:** D에서 queue-full 시 오래된 frontier
  packet을 버리는 정책만 causal backpressure로 바꿨다. PGBA 직전에도 pending packet을
  버리지 않고 먼저 모두 적용한 뒤 correction한다. 처리량은 **176/213→213/213**,
  packet drop **37→0**, idle replay 1,902→2,871회가 됐다. Fixed는 **20.1342dB**,
  SSIM 0.5888, LPIPS 0.3677로 D보다 **+0.1463dB**다.
  방향은 맞아 유지 후보이나 단독 해결은 아니며 다음 exp85-I는 H에서 dense global3만 켠다.
- **2026-09-14 — exp85-I no-drop dense pair:** H에서 native historical dense slot만
  0→3/6으로 바꿨다. Packet은 모두 보존됐고 dense frontier view update도 1,389회
  발생했지만 fixed는 **20.1043dB**, SSIM 0.5878, LPIPS 0.3762로 H보다
  **-0.0299dB**였다. 따라서 기존 dense 부호가 queue drop 탓이라는 가설은 기각한다.
  Vanilla table_01가 약 372초 mapping service를 받은 반면 H/I online loop는 약 130초이고,
  final-v7은 요청 7회도 상태에 따라 3회로 축소하므로 다음은 map service 계약 차이다.
- **2026-09-14 — exp85-J full-frontier service 진단:** 사용자가 custom 개발 단계에서는
  exact 1.5x cutoff를 품질 최적화의 강제 종료선으로 쓰지 않아도 된다고 정리함에 따라,
  H의 no-drop/RGBD+normal/online-rank를 고정하고 절대 frame gate 없이 모든 일반 packet에
  constant frontier 10회를 적용했다. 213/213 packet, drop 0, terminal map update 0을
  지켰고 online loop는 **203.751초**였다. Controller의 1-view replay는 3,207→0회,
  multi-view frontier는 532→2,078 step, frontier view update는 8,398→34,686회로
  늘었지만 fixed는 **19.1974dB**, SSIM 0.5429, LPIPS 0.3256으로 H보다
  **-0.9368dB**였다. 정상 state-based topology event도
  4→14회로 늘었다. 따라서 RPNG gap은 단순 map service 부족이 아니며, 현재-window를
  과도하게 반복하는 fixed full-frontier 정책도 해법이 아니다. 다음은 dense를 추가하는
  K가 아니라 vanilla/custom의 평가 pose·trajectory 및 실제 global-view sampling 경로를
  코드/로그로 일치 검증한다. 최초 J 폴더는 금지된 `late_mapping_start_frame=0`을 넣어
  validation 전에 종료된 무효 pilot이며, 유효 결과는 `_v2` 폴더다.
- **2026-09-14 — metric audit 및 exp85-K upstream frontend:** custom evaluator JSON의
  `mean_psnr`는 fixed 502장과 non-fixed tracking KF를 합친 union이고, 판정값은
  `fixed_eval_mean_psnr`여야 한다. D–J 진행 로그가 union을 fixed로 잘못 부른 것을
  정정했으며 결론의 부호는 바뀌지 않는다. Vanilla `24.1699dB`는 vanilla KF를 뺀
  463장이므로 동일 UID 재집계도 병행한다. H는 fixed/shared463
  **20.1342/20.1160**, J는 **19.1974/19.2192dB**다. K는 H의 mapping·density·loss를
  고정하고 upstream frontend 전체(window25/radius2/BA4+2/motion2.4)를 복구했다.
  Tracking KF는 221→243, loop는 **181.717초**가 됐지만 fixed/shared463은
  **19.6051/19.6103dB**, H보다 -0.5291/-0.5057이었다. SE(3)-aligned KF ATE도
  H 0.04161m, vanilla 0.04950m보다 나쁜 **0.06548m**였다. 따라서 저비용 frontend
  단독이 4dB gap의 원인은 아니다. 다음은 custom 코드에서 scheduler/idle replay를
  완전히 끄고 upstream map contract를 묶음 복구하는 parity control이다.
- **2026-09-14 — exp85-L upstream map parity minus isotropic:** custom 코드 자체는
  유지하되 final-v7 scheduler/idle replay/dense/online-rank/no-drop 경로를 쓰지 않고,
  upstream frontend(25/2/4+2), init1050, uniform 64/32 birth, frontier10/global2,
  RGBD+normal 및 drop-oldest queue를 묶음 복구했다. Custom 기본값 때문에 upstream의
  isotropic scale loss만 빠진 조건이다. Vanilla와 동일하게 `idx%5` 평가 중 이 run의
  keyframe을 제외한 463장은 **24.2752dB / SSIM 0.80115 / LPIPS 0.18762**로,
  vanilla streaming **24.1699dB보다 +0.1054dB**다. Fixed502/union713/KF250은 각각
  24.2602/24.2984/24.3421dB, KF ATE(SE(3))는 0.04940m로 vanilla 0.04950m와 같다.
  따라서 약 4dB gap은 tracking pose나 custom core 자체가 아니라 final-v7 map-path
  변경 묶음에서 생긴다. 단, 실행 중 wrapper를 수정해 최종 `run.log`가 셸 오류 한 줄로
  덮였으므로 지도·metric은 유효한 품질 진단으로만 쓰고 packet/runtime telemetry 계약
  증거로는 쓰지 않는다. M에서 isotropic까지 복구하고 고정 wrapper로 재측정한다.
- **2026-09-14 — exp85-M complete upstream map parity:** L에서 upstream의 unconditional
  isotropic scale loss(weight 10)만 복구했다. Vanilla와 동일한 non-KF 463장은
  **24.2463dB / SSIM 0.80442 / LPIPS 0.19015**로 vanilla streaming 24.1699dB보다
  **+0.0764dB**다. Fixed502/union713/KF250은 24.2286/24.2670/24.3212dB이며,
  KF ATE(SE(3)) 0.04933m도 vanilla 0.04950m와 일치한다. L 대비 isotropic의 PSNR
  차이는 -0.0289dB뿐이다. Online loop는 **358.004초**, 최종 209,220GS,
  topology counter 20, online-final optimizer update 0이었다. 따라서 complete upstream
  recipe를 custom 코드에서 재현했지만 이는 fixed 1.5x deadline을 만족한 realtime
  성과가 아니라 quality-first paced-drain parity다. 다음 N은 M의 총 frontier
  iteration/view 수를 고정하고 historical KF global 2개 중 1개만 causal dense RGB로
  교체한다.
- **2026-09-14 — exp85-N parity-base dense global1:** M의 upstream map contract와
  packet당 10 optimizer step, current KF window, 총 global slot 2개를 고정하고 historical
  KF global 하나만 causal dense RGB로 교체했다. Dense는 evaluator residue와 겹치지 않는
  stride5/offset2, keyframe interval당 temporal-maximin 1장, IMU rotation bridge pose다.
  최종 pool 307장과 PGBA residual refresh를 확인했다. M과 동일 non-KF 463장에서
  **23.8979dB / SSIM 0.78896 / LPIPS 0.20347**, 즉 M보다 **-0.3484dB**이고 vanilla보다
  -0.2720dB다. Loop 357.899초와 KF ATE 0.04941m는 M 358.004초/0.04933m와 같지만
  최종 map은 209,220→217,377GS로 변했다. 현재 native dense-global은 RGB-only여도
  xyz/scale/rotation/opacity/SH full gradient와 densification statistics를 함께 바꾸므로,
  pose가 정확히 같지 않은 dense RGB가 topology까지 흔드는 경로가 문제다. Dense 양을
  늘리는 sweep은 중단하고, 다음 O는 M의 regular RGBD backward와 topology statistics를
  그대로 보존한 채 dense appearance/opacity gradient만 parameter-group PCGrad+norm cap으로
  한 번 더하는 단일축이다.
- **2026-09-14 — exp85-O projected dense appearance/opacity:** M의 upstream current-window
  RGBD+normal backward, historical KF global2, 10 optimizer step과 KF-only densification
  statistics를 그대로 둔 뒤 마지막 regular step에 dense batch1의 RGB gradient를 더했다.
  Parameter group별로 KF gradient와 음의 내적 성분을 제거하고 KF gradient norm의 25%로
  제한했으며 dense의 xyz/scale/rotation 비율은 0이라 geometry에는 더하지 않았다.
  동일 non-KF463은 **24.2333dB / SSIM 0.80391 / LPIPS 0.18934**로 M 대비
  PSNR -0.0130, SSIM -0.00051, LPIPS **-0.00081 개선**인 사실상 동률이다. Vanilla보다
  PSNR +0.0634다. Loop 359.074초, KF ATE 0.04939m, pool307, 최종 203,907GS다.
  Full-gradient N의 -0.3484dB 붕괴를 막았지만 batch1은 pool 전체에 충분한 기회를 주지
  못해 PSNR gain도 없다. 다음 P는 projection cap/regular step을 고정하고 dense batch만
  1→4로 늘려 한 projected direction이 더 넓은 view coverage를 대표하게 한다.
- **2026-09-14 — exp85-P projected dense batch4:** O의 regular KF loss, projected
  iteration 1회, geometry ratio0, group PCGrad 및 norm cap0.25를 고정하고 dense batch만
  1→4로 바꿨다. 종료 계측은 regular frontier **2,965 step/37,635 KF-view update**,
  projected dense **215 step/860 view update**, topology20이다. Non-KF463은
  **24.2625dB / SSIM 0.80455 / LPIPS 0.18966**로 O보다 +0.0292dB, M보다
  **+0.0162dB**, vanilla보다 +0.0926dB다. Loop364.672초, KF ATE0.04956m,
  최종202,735GS다. 더 넓은 coverage의 부호는 양수지만 noise 수준이며 +1 목표에는
  부족하다. 다음 Q는 batch4/regular service/geometry0을 고정하고 dense projected norm
  cap만 0.25→1.0으로 풀어 dense 신호 세기 부족 여부를 한 번 확인한다.
- **2026-09-14 — exp85-Q projected dense full cap:** P의 regular KF recipe,
  projected iteration1, dense batch4, geometry ratio0을 고정하고 group PCGrad norm
  cap만 0.25→1.0으로 높였다. Regular frontier **2,975 step/37,765 KF-view**,
  projected dense **216 step/864 view**, pool307, topology20으로 P와 거의 같은
  service를 받았다. 동일 non-KF463은 **24.2413dB / SSIM 0.80414 /
  LPIPS 0.19155**로 P보다 -0.0212dB, M보다 -0.0050dB이며 vanilla보다
  +0.0714dB이다. Fixed502/union713/KF250은 24.2233/24.2632/24.3211dB,
  loop370.611초, KF ATE0.04943m, 최종207,451GS다. Packet은 243개 enqueued,
  18개 drop-oldest, 225개 processed되고 EOF queue0/final optimizer update0이었다.
  따라서 projected dense의 신호 크기가 +1dB 미달의 주원인이라는 가설은 기각하고,
  cap 숫자 sweep을 종료한다.
- **2026-09-14 — exp85-R projected dense all frontier steps:** Q에서 cap을 다시
  안전한 0.25로 복구하고 batch4/geometry0을 고정한 채 projected iteration을
  packet당 1→10으로 늘려 모든 frontier step에 dense appearance gradient를 주었다.
  Projected dense service는 **1,920 step/7,680 view**로 Q의 216/864보다 약 9배
  늘었지만, 계산 경쟁으로 packet drop이 18→25, regular frontier가
  2,975→**2,735 step**으로 줄었다. 동일 non-KF463은 **24.2234dB /
  SSIM 0.80099 / LPIPS 0.19956**로 M보다 -0.0230dB, P보다 -0.0391dB,
  vanilla보다 +0.0535dB이다. Fixed502/union713/KF250은
  24.2047/24.2511/24.3057dB, loop374.338초, ATE0.04940m, 196,327GS,
  topology18, EOF queue0/final update0이다. Dense 빈도를 무조건 늘리는 경로는
  직접 품질 이득이 없고 regular service까지 잠식하므로 기각한다.
- **2026-09-14 — exp85-S unbounded no-drop dense all-step absolute gate:** R의
  map/dense recipe는 고정하고 mapping queue만 size2 drop-oldest에서 unbounded no-drop으로
  바꿔, timestamp-paced tracking이 생성한 causal packet 243개를 모두 처리했다.
  EOF에서 새 replay/polish/BA는 만들지 않고 이미 제출된 packet만 drain했다.
  Regular frontier는 **3,115 step/39,585 KF-view**, projected dense는
  **2,300 step/9,200 view**로 R보다 모두 늘었지만 non-KF463은
  **24.1253dB / SSIM 0.79723 / LPIPS 0.20184**로 M보다 -0.1210dB,
  vanilla보다도 -0.0445dB였다. Fixed502/union713/KF250은
  24.1061/24.1565/24.2261dB, loop398.127초, ATE0.04943m, 181,105GS,
  topology21, packet243/243·drop0·EOF queue0·final update0이다. 사전 absolute gate인
  vanilla+1=25.1699dB를 1.0445dB 미달했으므로 no-drop control pair와 추가
  all-step 최적화는 진행하지 않고 고비용 빈도 경로를 종료한다.
- **2026-09-14 — exp85-T projected residual50+coverage50:** P의 regular KF recipe,
  projected-last1, batch4, cap0.25, geometry0과 drop-oldest queue를 고정하고 dense 선택만
  cyclic4에서 robust high-residual2 + least-served coverage2로 바꿘다. 이전 dense
  render의 4-view loss를 한 번에 EMA로 갱신하므로 추가 render/loss는 없다.
  Regular frontier **2,975 step/37,765 KF-view**, projected dense **216 step/864 view**,
  packet243/225/drop18, loop363.713초로 P의 2,965/37,635, 215/860, 364.672초와
  거의 같다. Non-KF463은 **24.2979dB / SSIM 0.80559 / LPIPS 0.19087**로
  M보다 +0.0516dB, P보다 +0.0354dB, vanilla보다 +0.1281dB이다.
  Fixed502/union713/KF250은 24.2781/24.3214/24.3686dB, ATE0.04940m,
  207,875GS, topology20, EOF queue0/final update0이다. Dense305장 전부가 최소 1회
  선택됐지만 residual hard view는 최대27회로 집중됐다. 구조 부호는 양수지만
  +1 대비 작으므로, 다음 U는 슬롯/비율/계산량을 고정하고 residual score에
  서비스 횟수의 제곱근 한계이득 감쇠만 추가한다.
- **2026-09-14 — exp85-U residual marginal utility:** T의 residual2+coverage2,
  projected-last1/batch4/cap0.25/geometry0을 모두 고정하고 residual ranking을
  `robust_loss / sqrt(1 + prior_services)`로 바꿘다. 이는 frame/iter 경계가 없고
  같은 view를 반복할수록 한계 이득이 감소한다는 scale-free 선택 항이다.
  Regular frontier **2,975 step/37,765 KF-view**, projected dense **216 step/864 view**,
  packet243/225/drop18, loop364.512초로 T/P와 service와 runtime이 일치한다.
  Table_01 non-KF463은 **24.3546dB / SSIM 0.80724 / LPIPS 0.18817**로
  T보다 +0.0566dB, P보다 +0.0921dB, M보다 +0.1082dB, vanilla보다
  **+0.1847dB**이다. Fixed502/union713/KF250은 24.3319/24.3851/24.4471dB,
  ATE0.04943m, 209,160GS, topology20, EOF queue0/final update0이다. Dense305장은
  전부 최소1회를 유지하면서 최대 선택이 T의 27→**5회**로 줄었다.
  +1은 아직 미달이므로 table_01에서 추가 숫자를 튜닝하지 않고 동일 U를
  RPNG table_04에 그대로 전이했다. 동일 UID 1,134장에서는 **21.2274dB /
  SSIM 0.72129 / LPIPS 0.18661**로 vanilla 20.7658/0.70386/0.21578 대비
  **+0.4615dB / +0.01743 / -0.02917**였다. Fixed1,215/union1,561/KF427은
  21.2392/21.2721/21.4048dB다. Regular frontier **5,525 step/70,195 KF-view**,
  projected dense **399 step/1,596 view**, packet419/409/drop10, selection1--5,
  topology37, loop774.078초, ATE0.06040m, 최종318,738GS, EOF queue0/final
  update0이다. RPNG 두 장면 모두 vanilla보다 좋아 선택 구조의 전이 부호는
  확인했지만 평균 개선은 **+0.3231dB**로 +1 목표에는 부족하다. 이어서 U를
  숫자 변경 없이 UTMM `ego-drive`에 이식했다. 동일 UID264장은 **20.5763dB /
  SSIM0.67542 / LPIPS0.36600**으로 vanilla 20.2615/0.66187/0.38504보다
  **+0.3148dB / +0.01355 / -0.01904**다. Fixed281/union349/KF85는
  20.6318/20.6727/20.9625dB, regular795 step/10,105 KF-view, projected dense
  66 step/264 view, packet79/73/drop6, selection1--4, loop117.268초,
  ATE0.06057m, 149,406GS, topology5, EOF queue0/final update0이다. 현재 대표
  panel 3/3 양수·평균 **+0.3203dB**이나 여전히 +1에는 부족하다. 마지막
  `fast-straight`도 같은 설정으로 확인했다. 동일 UID61장은 **17.4575dB /
  SSIM0.66481 / LPIPS0.46861**로 vanilla 17.4259/0.66441/0.46805 대비
  PSNR **+0.0316dB**, SSIM +0.00040, LPIPS는 0.00056 악화해 사실상 동률이다.
  Fixed68/union78/KF17은 17.5542/18.1112/20.5733dB, regular115 step/1,305
  KF-view, projected dense 2 step/8 view, packet9/7/drop2, selection1--2,
  loop28.721초(센서 loop 종료 뒤 drain 2.935초), ATE0.05736m, 40,711GS,
  topology1, EOF queue0/final update0이다. 최종 representative panel은 PSNR
  **4/4 양수**지만 평균은 **+0.2482dB**뿐이다. 구조의 일반 부호는 확인했으나
  목표 +1과 차이가 크므로 전체 16-scene 확장은 보류한다.
- **2026-09-14 — exp85-V joint historical marginal selector:** U의 dense
  projected service와 current-window RGBD+normal, global2, optimizer step을 고정하고
  무작위 historical KF 2장만 dense와 같은 한계이득 규칙의 residual1+least-served1로
  바꿨다. Loss는 이미 수행한 regular render에서 모아 map-call 끝에 한 번만 CPU로
  옮기며 추가 render는 없다. Non-KF463은 **23.8075dB / SSIM0.79136 /
  LPIPS0.19711**로 U보다 **-0.5471dB**, vanilla보다 **-0.3624dB**이고 세 지표가
  모두 악화했다. Regular2,965 step/37,635 KF-view, projected215 step/860 view,
  packet243/223/drop20, loop360.843초, ATE0.04936m, 206,421GS, topology20,
  EOF queue0/final update0이다. KF249장 모두 residual을 얻었고 selected count도
  최소10회였지만 최대90회로 어려운 KF에 집중했다. Historical KF의 높은 residual은
  곧바로 남은 학습 이득을 뜻하지 않는다는 반례이며, V는 첫 장면에서 기각해 전이하지
  않는다.
- **2026-09-14 — exp85-W budgeted KF→dense appearance replacement:** M의
  current-window RGBD+normal과 KF-only topology 통계를 보존하면서, projected가 가능한
  모든 frontier step에서 historical KF global2 중 정확히 한 자리를 dense appearance
  batch1로 교체했다. Dense 선택은 U의 residual/coverage 50:50 및
  `robust_loss/sqrt(1+prior_services)`를 그대로 사용했고 geometry gradient는 0이다.
  실제 regular KF-view는 M의 37,765에서 **35,605**로 2,160회 줄고 projected dense가
  정확히 **2,160회** 들어가 총 historical render service 37,765회를 보존했다.
  그러나 동일 non-KF463은 **23.9327dB / SSIM0.79408 / LPIPS0.19380**으로 M보다
  **-0.3137dB**, U보다 -0.4219dB, vanilla보다 **-0.2372dB**이며 세 지표가 모두
  악화했다. Fixed502/union713/KF250은 23.9108/23.9400/23.9756dB,
  packet243/224/drop19, loop357.414초, ATE0.04952m, 222,642GS, topology20,
  EOF queue0/final update0이다. 따라서 현재 pose/gradient 조건의 dense view는
  historical KF를 대체할 만큼 view당 한계이득이 높지 않다. U의 작은 양수는 고정
  budget 내의 더 좋은 배분이 아니라 KF service 위에 소량의 appearance 계산을 더한
  효과로 해석하며, W는 첫 장면에서 기각해 타 장면에 전이하지 않는다.
- **2026-09-14 — exp85-X SH1 × dense interaction pair:** M/U 계열이 모두
  view-independent SH0였으므로, 중간 dense view가 관측 방향에 따른 appearance 정보를
  제공하려면 SH 표현력이 필요한지 검사했다. 최초 KF-only pilot은 `IMU_poseinit` 뒤
  `remove_all_gaussians()`가 `GaussianModel(0)`을 하드코딩해 요청한 SH1을 SH0으로
  되돌리는 버그가 있어 common463 **24.2192dB**였지만 판정에서 제외했다. Backend가
  configured SH degree로 모델을 재생성하도록 수정하고 PLY의 `f_rest_0..8`을 확인한
  유효 pair에서 KF-only/dense의 동일 non-KF463은 각각 **24.5224/24.5270dB**,
  즉 dense 순효과는 **+0.0046dB**다. SSIM은 0.814883/0.814880으로 동률이고
  LPIPS만 0.179485→0.178657(-0.000828) 개선했다. SH1 KF-only 자체는 vanilla보다
  **+0.3525dB**(M SH0보다 +0.2761)라 일반 appearance 표현력 이득은 있으나,
  SH1+dense도 vanilla 대비 +0.3571dB에 그쳐 dense가 추가로 수렴을 가속한다는
  가설은 지지하지 않는다. Fixed502는 24.5063/24.5085, union713은
  24.5525/24.5694, KF250은 24.6137/24.6560dB다. KF-only는 regular
  2,975 step/37,765 view, packet243/224/drop19, loop353.911초, ATE0.04953m,
  215,114GS였고 dense는 regular2,965/37,635에 projected215 step/860 view,
  packet243/223/drop20, loop367.029초, ATE0.04949m, 208,765GS였다. 둘 다
  topology20, EOF queue0/final update0이다. SH1의 일반 효과와 dense 효과를 분리하며,
  X dense recipe는 +0.15dB transfer gate를 못 넘었으므로 타 장면에 전이하지 않는다.
- **2026-09-14 — exp85-Y projected-gradient 원인 진단:** X dense와 같은 recipe에서
  이미 계산하는 gradient/loss만 누적하고 추가 render와 per-step host sync는 넣지 않았다.
  Appearance `f_dc/f_rest`의 dense:KF raw norm은 **0.898/0.879배**로 신호가 작지
  않았고, gradient conflict는 **3.72/2.33%**, projection 뒤 norm 잔존은
  **99.36/99.79%**였다. 따라서 PCGrad 충돌 제거가 dense를 죽이는 병목은 아니다.
  두 appearance group은 215/215 step 모두 0.25 cap에 걸려 실제 추가 norm이
  KF의 0.249배였지만, 앞선 full-cap Q도 M보다 -0.005dB였으므로 cap 확대 역시
  이미 기각된 축이다. Opacity는 148 valid step, conflict16.89%, projection 잔존
  85.07%, 실제 추가 norm0.228배였다. Geometry raw norm은 KF의 1.11–1.40배지만
  X 계약대로 적용 norm은 0이다. Dense 재관측 555건의 raw 상대 progress 평균은
  -22.80%, 양수 비율33.15%였으나, PGBA가 dense pose를 갱신한 뒤에도 이전 pose에서
  측정한 loss cache를 그대로 비교·선택하는 것을 발견해 이 progress를 forgetting이나
  pose-risk 효과로 해석하지 않는다. 같은 이유로 U residual ranking에는 stale score가
  실제 들어갈 수 있다. 품질은 common463 **24.4137dB**, vanilla +0.2439dB이나 X
  dense보다 -0.1133dB로 run-to-run/scheduling 변동 범위이며, X의 +0.0046dB dense
  차이가 noise보다 작다는 결론을 강화한다. Fixed502/union713/KF250은
  24.3973/24.4391/24.4952dB, regular2,965/37,635, dense215/860,
  packet243/224/drop19, loop366.692초, ATE0.04952m, 208,523GS, topology20,
  EOF queue0/final update0이다. 다음 Z는 PGBA pose revision에서 residual/last-loss만
  무효화하고 coverage/service count는 보존하는 단일 구조 축이다.

## 현재 판정

| family/scene | vanilla | exp85-A KF | exp85-B dense | B−A | B−vanilla |
|---|---:|---:|---:|---:|---:|
| UTMM `ego-drive` | 20.2615 | 22.1981 | 22.2251 | +0.0270 | +1.9636 |
| UTMM `fast-straight` | 17.4259 | — | 15.8650 | — | -1.5609 |
| RPNG `table_01` | 24.1699 | 20.2364 | 20.1401 | -0.0963 | -4.0298 |

추가 KF-loss 진단 exp85-D의 RPNG `table_01` fixed는 19.9879dB다. 이는 A보다
-0.2485dB이므로 RGBD+normal 복구만으로 vanilla gap은 닫히지 않았다.

Map-service ceiling exp85-J도 fixed 19.1974dB로 H보다 -0.9368dB였다. 더 많은
multi-view 계산을 무조건 투입하는 방식은 격차를 닫지 못했으므로, K dense pair와
전체 panel 실행은 중단했다. Upstream frontend K도 fixed 19.6051dB로 실패했으므로
vanilla/custom map-path parity control로 공통성 감사를 계속했다. Isotropic을 제외한
upstream map 묶음 L은 vanilla 동일 463장에 24.2752dB로 격차를 닫았다. M에서
isotropic까지 복구해도 24.2463dB로 격차가 닫혔고 L 대비 -0.0289dB뿐이다. 이제
parity base에 causal dense global slot 하나만 올려 동일 service에서 dense의 순효과를
검증했다. N은 -0.3484dB로 실패했으므로 dense global slot 수 sweep은 하지 않는다.
다음은 regular RGBD gradient/topology를 보존하고 dense appearance/opacity gradient만
직교 투영·norm 제한으로 추가하는 O였고, -0.0130dB로 무손실이나 gain은 없었다.
다음 P는 동일 projected step의 dense batch를 1→4만 바꾼다.
P는 M보다 +0.0162dB로 양수지만 실질 gain이 아니었고, Q에서 norm cap을
0.25→1.0으로 높여도 M보다 -0.0050dB였다. R에서 dense 빈도를 약 9배
높여도 M보다 -0.0230dB였고 regular service까지 줄었다. 따라서 projected dense의
batch/cap/frequency 숫자 sweep을 종료하고, dense가 KF와 경쟁하지 않는 service
계약을 S에서 확인했지만 243/243 packet과 dense9200 view에서도 vanilla를
넘지 못했다. 따라서 무조건적 dense 추가 계산을 종료하고, 다음 구조는
같은 자료를 더 많이 보는 것이 아니라 어느 view의 supervision이 현재 map에 유용한지
온라인 증거로 gate하는 방향이어야 한다. T에서 동일 service의
residual50+coverage50이 P보다 +0.0354dB로 양수였지만 hard view에 최대27회
집중했다. U에서 residual 항에만 서비스 횟수 기반 한계이득 감쇠를 적용한다.
실제 U는 table_01에서 M/P/T보다 +0.1082/+0.0921/+0.0566dB이고 vanilla보다
+0.1847dB며, 최대 반복을 27→5회로 낮춰 예상한 작동을 했다. 같은 설정을
table_04에 무재튜닝 전이하자 동일 UID 1,134장에서 vanilla보다 **+0.4615dB**,
SSIM +0.01743, LPIPS -0.02917로 RPNG 2/2 양수였다. 다만 두 장면 평균은
+0.3231dB라 목표 +1에는 크게 부족하다. 동일 U는 UTMM ego-drive에서도
vanilla보다 **+0.3148dB**로 세 지표가 함께 좋아져 현재 panel 3/3 양수다.
세 장면 평균은 +0.3203dB이며 다음은 숫자 변경 없이 fast-straight까지
검사했다. Fast-straight는 +0.0316dB로 사실상 동률이며 projected dense update가
8회뿐이었다. 따라서 panel은 PSNR 4/4 양수·평균 **+0.2482dB**지만 +1 목표에는
부족하다. 전체 16-scene 실행과 final 폴더 생성을 보류하고, 다음 구조 축은
같은 view를 더 세게/자주 보는 숫자 sweep이 아니라 KF와 dense를 함께 고려하는
historical-view marginal-utility scheduler V로 정했다. 하지만 V는 table_01에서
U보다 -0.5471dB, vanilla보다 -0.3624dB로 실패했고 historical KF가 최대90회
과선택됐다. 따라서 KF residual을 dense와 같은 의미로 취급하는 통합 score는
기각한다. 다음 구조는 current-window geometry를 보존하면서 global2라는 고정
render 예산 중 한 자리만 dense appearance에 배정해 KF/dense가 실제 같은 예산에서
경쟁하도록 해야 한다. W에서 이를 정확히 구현해 총 historical render 수를 M과
37,765회로 맞췄지만 vanilla보다 -0.2372dB, M보다 -0.3137dB였다. 따라서 현재 dense
pose/appearance gradient는 KF global supervision을 대체할 수 없고, U의 +0.2482dB
panel 평균은 소량의 추가 계산 효과에 가깝다. W 계열 숫자 sweep과 타 장면 전이를
종료한다. SH0 표현력 한계 가능성은 X에서 실제 SH1 PLY를 보장한 KF/dense pair로
확인했지만 dense 순효과가 +0.0046dB에 그쳤다. 따라서 SH degree 증가는 일반 map
품질 레버(+0.35dB)일 수는 있어도 dense supervision의 한계이득을 복구하는 구조적
해법은 아니다. X도 타 장면 dense 전이 없이 종료하고, 다음은 새로운 비율 sweep보다
projected dense gradient가 KF gradient와의 투영·norm cap 뒤 실제로 얼마나 살아남는지와
pose confidence별 실현 이득을 계측해 병목을 분리한다. Y에서 appearance gradient는
raw norm이 KF의 약 0.9배이고 충돌 2–4%, projection 잔존 99%+라 gradient 생성/PCGrad가
병목이 아님을 확인했다. 반면 PGBA pose revision 뒤 residual cache가 이전 pose의 loss를
계속 점수로 쓰는 오류가 드러났다. Y의 raw progress는 이 pose 변경에 오염되어 학습
망각 증거로 쓰지 않는다. 다음 Z는 새로운 점수나 비율 없이 pose가 바뀐 view의
residual/last-loss만 무효화하고 기존 coverage count는 유지한다.

판정은 vanilla와 동일 UID의 held-out 교집합만 사용한다. 전체 16-scene은
아직 실행하지 않았다.
