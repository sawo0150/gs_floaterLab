# exp92 — RPNG 평가 분기는 GT 전처리만 달랐다

- 날짜: 2026-09-17
- 상태: 원인 위치 확인; normalized-vs-vanilla 공식 pair 0/17
- runner: `benchmarks/online_gs/run_exp92_capture_evaluator_branch.py`
- 결과: `results/experiments/exp92_evaluator_branch_capture/rpng/table_01/normalized_s0/`

동일한 normalized PLY를 다섯 번 평가했다. 첫 세 번은 fixed held-out
**20.785455 dB**, 네 번째와 다섯 번째는 **25.574595 dB**였다. 첫 held-out
view의 rendered prediction SHA-256은 저/고 평가에서 모두 `719d278b...23644`,
camera R·projection·background SHA도 같았다. 반면 GT tensor SHA는 저평가
`a2a8f364...353cf`, 고평가 `9d9b5eb...36c2c`로 달랐다. 따라서 이 분기는
mapper 산출물이나 rasterizer 수치 흔들림이 아니라 **입력 GT 전처리**다.

후속 계측이 포함된 다섯 번째 고평가 명령은 `--undistort`를 포함했고
`preprocess.undistort_argument=true`였다. 첫 세 번의 명령 인자는 당시
계측되지 않았으므로 exp93에서 실행 argv를 직접 캡처했다. 이 카드는
첫/두 번째 평가의 시간적 안정성이 옳은 전처리를 보장하지 않음을 보여준다.
