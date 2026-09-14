# exp77 — final-v7 재현·종료 조건·벤치마크 전이

2026-09-11 사용자 요청으로 기존 exp77~80을 하나의 exp77로 통합했다. 현재 최적화 부족 원인 검증도 **exp77 E**에 통합한다. **사용자가 명시적으로 전환을 지시하기 전까지 exp78을 만들거나 사용하지 않는다.**

| 단계 | 이전 번호 | 내용 | 결과 | 카드 |
|---|---|---|---|---|
| A | exp77 | RPNG/UTMM 1.5× + queue drain 기준선 | 15/16 평가, 평균 19.018 dB | [기준선](exp77_vigs_final_v7_rpng_utmm_16seq.md) |
| B | exp78 | Aria final-map 재현 | 2회 평균 27.924 dB, zero-tail 아님 | [재현](b_aria_reproduction/exp78_aria_final_v7_reproduction.md) |
| C | exp79 | Aria 1× optimizer zero-tail | 2회 평균 26.838 dB, tail 0은 2/2 | [종료 조건](c_aria_zero_tail/exp79_aria_1x_sensor_eos_zero_tail.md) |
| D | exp80 | RPNG/UTMM 1× optimizer zero-tail | 13/16 평가, 평균 17.268 dB | [벤치마크](d_benchmark_zero_tail/exp80_vigs_1x_zero_tail_16seq.md) · [원인 분석](d_benchmark_zero_tail/exp80_root_cause_analysis.md) |
| E | 번호 정정 전 새 exp78 | table_06 reserve 40ms↔20ms 비교 | 4회 완료, 분석은 하위 카드 참조 | [최적화 원인 검증](e_reserve_ablation/README.md) |

단계별 프로토콜과 평가 수가 달라 평균을 합치지 않는다. B↔C 및 A↔D는 여러 설정이 바뀐 비교다. C/D는 optimizer update의 EOS 종료를 확인했으며 모든 SLAM 상태 갱신의 종료를 인증하지 않았다.

하위 카드의 기존 파일명·본문 내 이전 번호와 results/ 원본 run ID는 당시 기록을 추적하기 위해 유지한다. 과거 STATUS 항목도 원문 보존하며, 위 대응표와 최신 정정 항목을 기준으로 해석한다. evidence 파일은 각 단계 폴더와 함께 이동했고 내용은 변경하지 않았다.

[현재 exp77 E: 소수 시퀀스 최적화 원인 검증](e_reserve_ablation/README.md)
