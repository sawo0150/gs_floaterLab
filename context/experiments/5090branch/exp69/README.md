# exp69 — Decoupled geometry maintenance

exp68 사후 감사에서 확인한 low-opacity dust garbage collection 부재와 12F photometric
service 붕괴를 분리해 검증한 후속 실험이다.

- `exp69_decoupled_geometry_maintenance_plan.html`: exp67 기준선 고정, 독립 mature dust GC,
  단계별 실험과 사전 PASS 규칙
- `exp69_result.html`: exact compositing telemetry 구현, reversible/hard action,
  bounded archive, 고정-size FIFO epoch sampler, pose-balanced active + unbounded
  archive 재검증, 세 장면 strict 1.5× 결과와 최종 기각/보존 판정

## 최종 상태

- exact per-Gaussian contribution 계측과 stable-ID mature-dust detector는 구현·검증 완료
- 추가 FIFO epoch scheduler 테스트 45개와 geometry 테스트 24개 통과
- hard prune은 12F PSNR을 손상해 기각
- bounded archive는 1253/305 PSNR은 높였지만 giant-splat geometry를 악화시켜 기각
- very-conservative reversible suppression은 일부 geometry 지표가 개선됐지만 305 strict
  run이 27 dB floor를 통과하지 못해 **범용 champion으로 승격하지 않음**
- `epoch_size=50`, `new_fraction=0.08`, dense FIFO 500 실험은 설정한 4/50 신규
  membership을 정확히 만들었지만 305/12F가 각각 24.88/23.80 dB로 하락해 기본값으로 기각
- pose-balanced active + unbounded archive는 1253/305에서 27.87/28.27 dB였지만,
  paired 12F가 기존 full-pool 26.68 dB 대비 25.76 dB(−0.92)로 하락했다.
  1253 geometry는 혼합 개선, 305 high-opacity/footprint는 소폭 악화해 범용 기본값으로 기각
- production-safe 기본값은 exp67 scheduler이며 exp69 action은 experimental flag로 보존
