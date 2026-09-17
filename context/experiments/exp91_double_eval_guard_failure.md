# exp91 — double-evaluation guard does not repair RPNG metric collapse

> **2026-09-17 원인 정정 (exp92/93):** 아래 현상은 평가가 시간에 따라
> 무작위로 변한 것이 아니다. exp91의 혼합-inventory 경로에서 Aria wrapper가
> RPNG 평가 명령의 `--undistort`를 제거했고, 세 번째 수동 direct 평가만
> 원래 RPNG 명령을 사용했다. 같은 PLY의 render·pose는 동일하고 GT tensor만
> 바뀌었다. 아래 중단 당시의 판단과 로그는 provenance로 유지하되,
> `cooldown`·이중 평가는 원인 수정이 아니다. [확정 진단](exp93_evaluator_preprocess_root_cause.md).

- 날짜: 2026-09-17
- 상태: **STOP / 실패; 공식 normalized-vs-vanilla pair 0/17**
- runner: `benchmarks/online_gs/run_exp91_normalized_metric_v2_reliable.py`
- 결과: `results/experiments/exp91_normalized_metric_v2_reliable/rpng/table_01/`

exp90의 첫 평가 오류를 막으려고 양 arm 동일 15초 post-map cooldown과
동일 PLY 독립 2회 평가를 사전 고정했다. 모든 17 scene preflight는 PASS였고,
기존 exp88의 `20.787371/25.584315 dB` pair를 consistency 함수가 예상대로
FAIL 처리했다. 첫 scene RPNG `table_01` normalized mapping을 새로 수행한
결과 archive/config/event/dense admission/3,030 Adam/38,302 render/
zero-tail/502-view held-out 등 구조 gate 12/12는 PASS였다.

그러나 같은 PLY SHA-256 `9c4c70db...d7b32`의 독립 첫/두 번째 평가는
**20.783158/20.783158 dB로 bitwise 동일하게 낮았다.** 따라서 두 평가
일치 gate만으로 올바른 품질 판정이 되지 않는다. 사전 `R4 대비 >0.5 dB`
중단선(기존 R4 25.624315; 관측 차이 −4.841157)을 따라 official vanilla와
후속 16 scene을 시작하지 않았다. 평가 약 1분 뒤 같은 PLY를 세 번째로
평가하자 **25.574971 dB**였다. PLY의 현재 SHA는 앞선 두 평가 전/후
SHA와 동일하며 source·fixed manifest·trajectory도 변경하지 않았다.

결론은 `first eval` 한 번만 문제라거나 `15초 기다리면 해결된다`가 아니다.
일정 시간 여러 subprocess에 걸쳐 낮은 평가 군집이 지속될 수 있다.
두 평가의 일치나 일정 지연만으로 높은 점수를 선택하는 방식은 정당화할 수
없다. 저장 PLY evaluator의 render/pose/입력 상태 중 분기 지점을 실제
tensor 수준에서 잡거나 독립 reference renderer와 교차 검증하기 전에는
v2.1을 공식 benchmark에 사용하지 않는다. `summary.md`의 0/17은 정상적인
fail-stop 결과다.

증거: `evaluation_consistency.json`(두 낮은 평가 exact·동일 입력 SHA),
`quality_gate.json`(12/12 구조 PASS·중단),
`psnr/strict_fixed_manifest_diagnostic_third/final_result.json`(세 번째 높은 평가),
[진행 중 표](benchmark_custom/metric_benchmark_v2_reliable_20260917/summary.md).
