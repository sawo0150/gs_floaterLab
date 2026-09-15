# exp77 E — dense replay가 적은 이유

분석: 2026-09-11. E1의 table_06 4회 비교 로그와 현재 코드를 확인했다. 새 번호로 전환하지 않는다.

## 실제 변화

| 지표 (각 2회 평균) | reserve 40ms | reserve 20ms |
|---|---:|---:|
| Dense replay updates (MAP_RR_DONE) | 1,889 | 2,073 |
| 모든 mapper Adam 완료 호출 | 2,260 | 2,434 |
| Tracking 중 idle replay gate 허용 | 0 | 391.5 |
| Idle replay 함수 wall time | 7.55s | 9.49s |
| Mapper packet dispatch wall time | 29.89s | 28.94s |
| Tracking 호출 wall time | 73.66s | 74.72s |
| Held-out PSNR | 21.117 | 21.391 |

Dense replay는 +9.74%, 전체 Adam은 +7.70%, PSNR은 +0.274dB다. gate 허용은 함수 진입 기회이며 update 수가 아니다. Dense replay 합계에는 idle 경로와 packet 처리 중 pressure allocation 경로가 함께 포함된다. 여러 thread의 wall time은 겹치므로 표의 시간을 더하거나 GPU 이용률로 해석하면 안 된다.

## 병목 1: 평균 FPS보다 심한 순간 backlog와 과거 deadline

`vigs.py:2206,2245`에서 replay deadline은 producer가 아닌 **track()에 들어온 프레임**의 timestamp로 갱신된다. 최초 소비 프레임 wall time + 센서 timestamp 경과 + 추정 한 프레임 간격이다. tracking이 밀리면 deadline은 과거로 남는다. `_polish_gate()`는 이 slack으로 다음 replay를 허용한다.

20ms run1은 tracking 평균 26.98ms이지만 p90=99.92ms, p95=120.51ms, 최대 2.145s다. 평균만 보고 매 33ms마다 일정한 여유가 있다고 가정할 수 없다. gate가 관측한 slack 평균 -1.875s, 최소 -8.274s였고 run2도 -1.831s/-8.288s다. reserve를 0으로 만들어도 음수 slack에는 양수 비용의 replay가 들어가지 못한다.

이 통계는 polling 횟수 가중값이며 시간 가중 지연이나 모든 프레임의 지연 분포가 아니다. backlog의 존재는 확인되지만 전체 몇 초를 이 조건으로 잃었는지는 현재 계측으로 계산할 수 없다. 절대 sensor-EOS cutoff와 이 per-frame gate는 별개다. per-frame gate의 정책을 바꾸는 실험도 EOS cutoff를 유지해야 한다.

## 병목 2: idle replay는 worker의 최우선 작업이 아니다

`vigs.py:620` 이후 worker는 mapping queue가 비었을 때만 idle replay에 진입한다. packet을 처리하는 동안에는 같은 worker가 idle replay를 실행할 수 없다. E1에서는 dispatch에 약29초를 썼고, run1은 208개 packet 중 193개 처리·15개 drop을 기록했다. map 생성, depth/pose 처리 및 PGBA 대응 등의 비용이 이 경로에 포함된다.

단, dispatch가 전부 replay 손실은 아니다. `map_scheduler.py:2140`의 foreground allocation은 worker가 계속 포화되면 기존 frontier 반복 예산을 dense replay로 바꾼다. run1/run2는 각각119회 pressure allocation을 기록한다. 따라서 idle replay 횟수만 보고 총 dense 학습량을 판정하면 안 된다. 현재 로그는 두 경로의 완료 update 수를 따로 집계하지 않아 정확한 경로별 분해는 미확인이다.

## 병목 3: 지도 상태 gate와 초기 학습 지연

`map_scheduler.py:2136`은 BALANCED/REPLAY 상태에서만 idle replay를 허용한다. FRONTIER나 초기 빈 map이면 차단된다. 최초 Adam 시작이 producer 시작 후 약15.2초라 92.24초 예산의 약16.5%가 그 전에 지난다. 여기에는 초기화와 초기 처리 지연이 섞여 있으며 IMU만의 비용이라고 단정하지 않는다.

E1에서 최초 BALANCED 전환도 frame1088~1108까지 늦어졌다(약39~40% 지점). 초기 map이 생긴 즉시 idle replay를 허용하는 구조가 아니라 topology 관측·capacity 회복 증거를 기다린다. 그 이전에도 pressure allocation을 통한 dense update는 가능하다.

20ms run1의 reject_model은43,578회다. 다만 `vigs.py:791` telemetry는 tracking active 상태의 모든 실패를 reject_tracking으로 먼저 분류한다. 그러므로 reject_tracking118,747회를 tracking reserve만의 실패로 해석하면 잘못이다. 여러 gate가 동시에 실패할 수 있고, 빠른 polling이라 횟수의 비율은 손실 시간의 비율도 아니다.

## 병목 4: 작은 센서 슬롯에 보수적 비용 예측과 동기화가 들어간다

`gs_backend.py:3188` 비용 예측은 EMA가 아니라 **최근16개 관측의 최대값**이다. 33ms 슬롯에서 20ms를 예약하면 이상적인 경우에도 약13ms만 남고, 호출이 늦으면 그보다 작다. 긴 replay 관측이 들어오면 이후 admission이 더 보수적이 된다. E1 최종 replay EMA는 run1/2에서7.78/8.23ms다. 이것을 전체 실행 평균 비용으로 사용하면 안 된다.

`idle_map_rr_step()`은 video/gaussian lock을 잡고 완료 event를 동기화한다. `sensor_eos_guard.py`도 Adam마다 현재 CUDA stream을 동기화한다. 따라서 별도 CUDA stream과 overlap gate 허용이 곧 완전한 GPU 동시 실행을 뜻하지 않는다. 동기화 비용과 lock 대기 비용은 아직 분리 측정하지 않았다. guard 제거는 zero-tail 검증을 약화하므로 품질 개선안으로 취급하지 않는다.

## 결론과 다음 실험

reserve40은 실제 결함이었지만 고친 뒤에도 dense replay는 **tracking backlog, 과거 per-frame deadline, packet 우선 처리, 지도 상태 gate**에 종속되어 있다. 420뷰 replay pool의 평균 선택 횟수도 약4.5→4.9회에 그친다. 단순히 replay_iters를 높이면 실행 가능 시간이 늘지 않으므로 개선을 보장하지 않는다.

E2에서는 같은 table_06에서 reserve20↔0을 각각2회 비교해 여전히 남은 예약량의 영향을 먼저 분리한다. 그다음 필요하면 과거 deadline일 때의 정책을 별도로 바꾸되, 센서 인과성·fixed1×·EOS optimizer cutoff는 유지한다. 추적 지연과 ATE가 나빠지면 PSNR만으로 채택하지 않는다. 추가 정책·장면 검증은 모두 exp77 E의 하위 단계로 기록한다.

[원본에서 추출한 계측](evidence/replay_diagnostics.json) · [E1 결과](README.md)
