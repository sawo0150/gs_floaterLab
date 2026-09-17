# exp93 — 혼합 inventory에서 Aria 평가 어댑터가 RPNG undistort를 제거

- 날짜: 2026-09-17
- 상태: 원인 확정, 수정 후 공식 재실행은 exp94에서 별도 검증
- runner: `benchmarks/online_gs/run_exp93_capture_preprocess_branch.py`
- 결과: `results/experiments/exp93_preprocess_branch_capture/rpng/table_01/normalized_s0/`

RPNG `table_01` normalized PLY를 기존 혼합-inventory 실행 경로로 평가한
세 번의 fixed held-out 점수는 전부 **20.789347 dB**였다. 세 번 모두 캡처된
`evaluator_argv`에 `--undistort`가 없고
`preprocess.undistort_argument=false`였다. exp92의 같은 PLY 저/고 평가에서
prediction·pose는 같고 GT만 달랐다는 증거와 합치한다.

정확한 코드 원인은 `run_exp88_normalized_metric_v2.install_inventory()`가
`run_exp78b_r4_aria.install_extension()`을 호출하면서
`base.evaluation_command`를 Aria 전용 명령 생성기로 **모든 dataset에 대해**
덮어쓴 것이다. 그 Aria 명령은 RPNG/UTMM에 필요한 `--undistort`를 넣지 않았다.
즉 exp87/88/91의 약 20.8 dB와 direct-file 약 25.6 dB의 차이는 시간 경과나
평가 무작위성이 아니라 **서로 다른 GT 전처리 계약**이다. 해당 실험의 낮은
점수를 normalized map 급락으로 해석한 판단은 무효다.

`run_exp78b_r4_aria.py`를 Aria scene에만 전용 평가 명령을 쓰고 그 밖에는
원래 RPNG/UTMM 명령으로 위임하도록 수정했다. `test_exp94_aria_evaluator_delegation.py`
2개 테스트가 RPNG/UTMM `--undistort` 유지와 Aria의 원래 명령을 확인했다.
기존 낮은 값은 provenance로 보존하고, 새 source lock·새 output root의
exp94 결과만 공식 비교에 쓴다.
