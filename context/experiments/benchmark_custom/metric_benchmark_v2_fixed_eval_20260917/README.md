# Metric benchmark v2.2 — fixed evaluator contract

- 날짜: 2026-09-17
- 상태: RPNG `table_01`부터 새 source lock으로 진행 중; 완성된 공식 비교는 [summary.md](summary.md)에만 기록
- runner: `benchmarks/online_gs/run_exp94_normalized_metric_v2_fixed_eval.py`
- output: `results/experiments/exp94_normalized_metric_v2_fixed_eval/`

## 평가 계약 수정

Exp92/93에서 exp87/88/91의 RPNG 약 20.8 dB 급락은 mapper가 아니라
Aria 평가 어댑터가 RPNG/UTMM 명령의 `--undistort`를 제거한 결과임을
확인했다. v2.2는 Aria scene에만 Aria 명령을 쓰고 RPNG/UTMM은 기존
distortion-aware 명령으로 위임한다. 실행 전 17개 scene 전부의 평가 명령에서
RPNG/UTMM `--undistort` 존재, Aria 부재를 확인한다. 위임 테스트 2개 PASS.
구버전 output/PSNR은 v2.2에 재사용하지 않고 새 source lock에 wrapper와
평가 코드를 포함한다.

## 나머지 사전 계약

Selector는 `Phi(n)=Var(n)/mean(n)`의 per-view Gibbs
`p_i ∝ exp[-log(1.5)n_i/(T+1)]`을 dense/aux-KF/native-KF에 적용한다.
Pool의 기존 block/no-repeat residue 제약은 유지한다. Dataset·scene별
온도나 phase cutoff는 없다. 각 pair는 같은 frozen causal tracker,
mapping-disjoint fixed held-out, zero-tail, 동일 physical training render
budget을 사용한다. Official vanilla는 normalized arm의 실제 완료 service에
맞춰 **새로 실행**한다. B는 `time_scale=unbounded` mapping-only isolation이지
C의 strict live-time 증거가 아니다.

각 저장 map은 두 번 평가해 per-view PSNR 차이 0.01 dB 이하 등 일치성을
확인한다. 이는 추가 audit일 뿐 exp93 원인의 수정 수단이 아니다. 어느
scene에서든 기존 R4보다 normalized PSNR이 0.5 dB 초과 하락하거나
fairness가 실패하면 즉시 중단한다. 17개 완료 시 최소 성공 기준은
scene 산술평균 ΔPSNR ≥+0.5 dB, 승리 9/17 이상, 모든 pair fairness PASS다.
기존 R4의 17/17·+1.2609 dB 회복은 추가 목표로 별도 판정한다.
