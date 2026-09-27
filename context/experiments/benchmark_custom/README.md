# benchmark_custom

이 폴더는 custom gsSLAM과 official vanilla VIGS-SLAM의 비교 문서만 모은다.
현재 논문 표의 기준은 **exp94 normalized-variance ERCB B-track v2.2**다.

## 현재 공식 결과

| 항목 | 값 |
|---|---|
| 유효 scene | 17 (`RPNG 8 + UTMM 7 + Aria 2`) |
| 승패 | **16승 1패** |
| scene-mean ΔPSNR | **+1.253787 dB** |
| RPNG | **+1.598585 dB**, 8/8 승리 |
| UTMM | **+0.517175 dB**, 6/7 승리 |
| Aria | **+2.452740 dB**, 2/2 승리 |
| 범위 | mapping-only, frozen tracker, zero-tail, 동일 physical render |
| 비실시간 주의 | `time_scale=unbounded`; strict live-time C-track 결과가 아님 |

바로 볼 문서:

1. [최종 표와 판정](metric_benchmark_v2_fixed_eval_20260917/summary.md)
2. [현재 mapper 동작과 실측 scheduling 비율](../../../benchmarks/online_gs/CURRENT_MAPPING_BEHAVIOR.md)
3. [최종 실행 계약](metric_benchmark_v2_fixed_eval_20260917/README.md)
4. [코드 버전·재실행 가이드](/home/intern/VIGS-SLAM-paper-full/docs/EXP94_NORMALIZED_ERCB_B_TRACK.md)

새 실행은 다음 진입점만 사용한다.

```bash
./benchmarks/online_gs/run_exp94_repeat.sh preflight exp94_repeat_YYYYMMDD
nvidia-smi
./benchmarks/online_gs/run_exp94_repeat.sh run-all exp94_repeat_YYYYMMDD
```

## 결과 계보

| 폴더/문서 | 상태 | 용도 |
|---|---|---|
| `metric_benchmark_v2_fixed_eval_20260917/` | **공식** | exp94, normalized ERCB 대 fresh vanilla, 17 scenes |
| `exp101_residual_birth_supplement_20260924/` | 단일 scene PASS | R4를 보존한 official residual supplement는 품질 유지, 비용 과다 |
| `exp100_capacity_matched_local_birth_20260924/` | 실패한 method gate | R4 capacity/density trace를 맞춰도 residual-only replacement가 −2.00 dB |
| `exp99_gaussian_slam_local_birth_corrected_20260924/` | 실패한 method gate | cap 결합 해소 후에도 1,024 ticket의 capacity 부족으로 R4 대비 −2.51 dB |
| `exp98_gaussian_slam_local_birth_20260924/` | 중단된 진단 | 공식 Gaussian-SLAM birth가 legacy Aria density cap에 다시 잘리는 결합 발견; PSNR 없음 |
| `exp97_shadow_filter_prune_isolation_20260924/` | 단일 scene 진단 | pruning source isolation과 비용 측정 |
| `exp96_filter_prune_isolation_20260924/` | 중단된 진단 | naive no-prune가 controller cadence를 바꾸는 결합 발견 |
| `r4_all_scenes_fixed_work_20260915/` | 이전 기준 | raw/shortfall R4, 17/17, 평균 +1.2609 dB |
| `metric_benchmark_v2_normalized_variance_20260917/` | 중단된 실행 | evaluator adapter 오류로 발생한 가짜 20.79 dB 급락 |
| `metric_benchmark_v2_reliable_20260917/` | 진단 | 이중 평가만으로 오류가 해결되지 않음을 확인 |
| `5070ti_vanilla_matched_time/` | 과거 진단 | 5070 Ti matched-time 및 birth/prune 실험 |
| [HISTORY_EXP85.md](HISTORY_EXP85.md) | 역사 | exp85 A--Y tuning 진행 로그 |

`normalized_variance`의 최초 급락 문서는 실패 provenance로만 남긴다. 최종 exp94는
RPNG/UTMM evaluator의 `--undistort` 누락을 수정하고 candidate와 vanilla를 모두 새로
실행한 결과다. 실패 폴더의 수치를 공식 표와 섞지 않는다.

## 어떤 파일을 어디에 둘지

- 공식/후속 비교 한 건당 `benchmark_custom/<run_tag>/` 폴더 하나를 만든다.
- 그 폴더의 `summary.md`를 사람이 읽는 단일 결과표로 둔다.
- raw PLY·render·log는 여기 두지 않고 `results/experiments/<run_tag>/`에 둔다.
- 과거 튜닝 일지는 최상위 README에 이어 쓰지 않고 별도 `HISTORY_*.md`에 둔다.
- 새로운 공식 결과가 생기면 이 README의 “현재 공식 결과”와 결과 계보만 갱신한다.
