# exp89 — RPNG normalized ERCB selector-family isolation

- 날짜: 2026-09-17
- 상태: **진단 완료; normalized 4.8 dB map 손실 가설 기각, evaluator 재현성 OPEN**
- 코드: `benchmarks/online_gs/run_exp89_selector_family_diagnostic.py`
- 결과: `results/experiments/exp89_selector_family_diagnostic/rpng/table_01/`

RPNG `table_01`의 기존 frozen tracker/held-out 502장/seed0/R4 work를 유지하고,
`Var(count)/mean(count)`의 per-view Gibbs law
`p_i ∝ exp[-log(1.5) n_i/(T+1)]`를 dense, auxiliary keyframe,
native historical keyframe selector에 하나씩만 적용했다. 전체 적용과 R4
shortfall control도 같은 direct-file 방식으로 새로 실행했다. 장면별 knob나
phase cutoff는 바꾸지 않았다.

| selector profile | fixed held-out PSNR | 새 R4 control 대비 |
|---|---:|---:|
| R4 service-shortfall control | 25.626168 | — |
| dense만 normalized | 25.617035 | −0.009133 |
| auxiliary-KF만 normalized | 25.619359 | −0.006808 |
| native-KF만 normalized | 25.577844 | −0.048324 |
| 세 family 전부 normalized | 25.582127 | −0.044041 |
| 세 family 전부 normalized, exp88 sibling output | 25.586699 | −0.039469 |

모든 run은 동일 archive/config/event/3,030 Adam/38,302 physical render/
dense admission/zero-tail/held-out disjoint와 동일 dense opportunity skeleton을
통과했다. 첫 선택 변경은 dense opportunity 1 (`event_id=14`), aux-KF
opportunity 104 (`event_id=118`), native historical audit 235다. 최종 선택
차이는 각각 4/269, 157/269, 1,286/1,610행이다. 단독 normalized arm의
해당 family 선택 UID 시퀀스는 exp88의 세-family 동시 실패 실행과 정확히 같았다.

같은 exp88 폴더 아래 새 sibling에 동시 normalized를 다시 실행해도 25.586699
dB였다. 따라서 exp88의 20.787371 dB를 normalized selector의 고정된
map 품질 저하로 귀속할 근거가 없다. 이어진 exp90에서 **동일 exp88 PLY의
재평가가 25.584315 dB**였으므로 원인은 mapper보다 평가 실행 경로에 있다.
저수준 evaluator 결함은 아직 미확정이다. 원래 낮은 숫자를 삭제하거나 새
숫자로 덮지 않고 두 결과를 모두 보존한다.

증거는 각 run의 `mapping_replay_runtime.json`, `diagnostic_report.json`,
`3dgs_before_final.ply`, `psnr/strict_fixed_manifest/final_result.json`이다.
이 결과는 RPNG 한 장면 진단이지 normalized-vs-vanilla 17-scene 판정이 아니다.
