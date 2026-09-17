# exp90 — saved PLY evaluator first-pass 재현성 진단

- 날짜: 2026-09-17
- 상태: **첫 평가 오류 재현; 저수준 메커니즘 OPEN; 전체 benchmark STOP 유지**
- 지연 진단 코드: `benchmarks/online_gs/run_exp90_first_eval_delay_probe.py`

RPNG `table_01`의 동일한 저장 PLY/trajectory/fixed held-out manifest를
변경하지 않고 재평가하면, mapping 직후 첫 PSNR이 낮았다가 재평가에서 약
4.8 dB 상승한다. 이는 normalized map이 실제로 나빠졌다는 exp88 초기
해석과 exp87의 `run_logged` mapper가 낮은 map을 만든다는 해석을 정정한다.

| 저장 PLY | 첫 평가 | 같은 PLY 재평가 | 차이 |
|---|---:|---:|---:|
| exp88 normalized | 20.787371 | 25.584315 | +4.796944 |
| exp87 shortfall wrapper repeat2 | 20.810871 | 25.620909 | +4.810038 |
| 새 exp87 shortfall wrapper repeat4 | 20.803644 | 25.632411 | +4.828768 |

새 wrapper repeat4는 여전히 첫 평가 20.803644 dB였다. 그 PLY를 다른
평가 subprocess가 읽었을 때 25.632411 dB였으므로 `PIPE로 실행한 mapper가
나쁜 지도를 만들었다`는 가설은 성립하지 않는다. exp88의 저장 normalized
PLY는 direct-file 재평가 25.584315 dB였고 PIPE 재평가도 동일했다.
따라서 PIPE 자체가 evaluator 실패의 충분조건도 아니다. 지도·포즈·뷰
수(502)·evaluator source SHA는 같고 첫/마지막 view를 포함한 광범위한
프레임에서 PSNR/SSIM이 함께 달라졌다. 포즈 파일은 낮은 map과 새 높은
map 사이에서도 SHA-256이 동일하다.

별도 단일-frame probe는 현재 저장 map의 frame0 백색 배경 렌더를 6개
독립 subprocess와 각 subprocess 내 2회 렌더에서 bitwise 동일하게 재현했다
(PSNR 24.707775 dB). 흑색/회색 배경은 각각 19.625601/22.514982 dB였다.
과거 실패한 첫 evaluator subprocess의 pose/render tensor hash는 저장되지
않아 GPU 커널·프로세스 초기화 중 어느 곳이 원인인지는 아직 특정하지 못했다.

추가 15초 post-mapper cooldown 진단 1회는 동일 PLY SHA-256을 평가
전/중/후 확인했고 첫/두 번째 평가가 **25.619359704/25.619359704 dB**로
정확히 같았다. 이는 예비 완화 신호지만 1회뿐이므로 cooldown을 확정된
근본 수정이라 주장하지 않는다. 다음 benchmark는 양 arm에 같은 cooldown과
독립 2회 평가를 사전 적용하고, PSNR/SSIM/LPIPS 및 per-view 불일치 시
높은 쪽을 고르는 대신 즉시 중단해야 한다. 이 self-consistency gate를
검증하기 전에는 17-scene normalized-vs-vanilla loop를 재개하지 않는다.

증거: `results/experiments/exp88_normalized_metric_v2/rpng/table_01/normalized_variance_s0/psnr/strict_fixed_manifest_repeat/`,
`results/experiments/exp87_normalized_variance_r4/rpng/table_01/service_shortfall_replay_s0_repeat2/psnr/strict_fixed_manifest_repeat/`,
`service_shortfall_replay_s0_repeat4/psnr/`(동일 exp87 경로),
`results/experiments/exp90_first_eval_delay_probe/rpng/table_01/control_pipe_delay15_s0/delay_probe_result.json`.
