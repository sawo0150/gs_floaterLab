# Research campaigns

각 campaign README는 결과를 다시 복사하지 않고, 채택 결과·실패·열린 질문을
한 화면에 모은다. 숫자 순서가 아니라 아래 의존 관계로 읽는다.

```text
LEGACY ──> LIVE ──> BENCH ──> ATTR
                 \          /
                  SCHED ──> DENSE
                             \
                              TOPO
```

| Campaign | 읽을 때 | 핵심 산출물 |
|---|---|---|
| [LEGACY](00_legacy_foundations/README.md) | batch/floater와 초기 incremental 배경이 필요할 때 | exp44, exp48–51 |
| [LIVE](01_strict_streaming/README.md) | strict online 정의와 runtime 최적화를 볼 때 | exp52–65, 77–79 |
| [SCHED](02_scheduler_foundations/README.md) | dense view/ERCB가 처음 왜 필요했는지 볼 때 | exp66–76 |
| [BENCH](03_benchmark_contract/README.md) | 논문 표와 공정 비교 조건을 볼 때 | exp78, 87–94, 109 |
| [TOPO](04_local_topology/README.md) | birth/prune/local densify 근거를 볼 때 | exp95–110, 121 |
| [DENSE](05_dense_ercb_integration/README.md) | 현 코드에서 dense/ERCB가 실제로 무엇을 하는지 볼 때 | exp111–123 |
| [ATTR](06_gain_attribution/README.md) | vanilla 대비 +dB의 원인을 분리할 때 | 다음 active campaign |

상태 표기:

- **ADOPTED**: 후속 실험의 기준으로 사용 가능
- **EVIDENCE**: 결론에는 쓰지만 final method는 아님
- **REJECTED**: 재시도하지 않을 조건이 확정됨
- **OPEN**: 다음 실험이 필요함
