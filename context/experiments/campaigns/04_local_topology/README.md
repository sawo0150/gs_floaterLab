# TOPO — birth, prune, and local topology

## 한 줄 결론

capacity 증가는 RPNG에서 도움이 되지만 전체 데이터셋의 이득을 설명하지 못한다.
Dense gradient로 bounded local topology를 작동시키는 경로는 만들었지만, R4 대비
독립 품질 gain은 아직 noise 수준이다.

| Subtrack | 실험 | 상태 | 결정 |
|---|---|---|---|
| native churn/prune | [95](../../exp95_topology_churn_probe.md)–[97](../../exp97_shadow_filter_prune_isolation.md) | EVIDENCE | pruning 제거는 capacity·runtime tradeoff가 큼 |
| official local birth | [98](../../exp98_gaussian_slam_local_birth_stopped.md)–[101](../../exp101_residual_birth_supplement.md) | REJECTED/EVIDENCE | replacement는 −2 dB급; supplement는 안전하지만 +52% GS |
| dense topology evidence | [102](../../exp102_dense_topology_evidence_probe.md)–[104](../../exp104_dense_topology_ticket.md) | EVIDENCE | dense gradients가 local ticket을 실제 구동 가능 |
| transfer and persistence | [105](../../exp105_dense_ticket_transfer_pilot.md)–[109](../../exp109_first_persistence_panel.md) | ADOPTED as safe composition | 17-scene 품질 보존, ticket 자체 gain은 미입증 |
| causal attribution | [110](../../exp110_rr_ticket_ablation.md) | EVIDENCE | ERCB/ticket 차이는 noise 수준 |
| runtime cost | [121](../../exp121_topology_cost_profile.md) | EVIDENCE | average densify/prune cost는 0.03–0.17%, spike는 40–55 ms |

관련 저자 코드 감사는
[source-code survey](../../benchmark_custom/LOCAL_TOPOLOGY_SOURCE_CODE_SURVEY_20260924.md)를
사용한다. 새 operator는 논문만 보고 재구현하지 않고 pinned official source에서
이식한다.
