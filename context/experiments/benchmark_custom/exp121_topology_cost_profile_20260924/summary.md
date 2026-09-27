# Exp121 — topology cost profile

CUDA-synchronized section timing of the frozen unified LPM-mass normalized
mapper. These are profiling runs, not held-out quality comparisons.

| Scene | Mapping wall | Render | Adam | GS | Topology calls | Densify/prune total | Max | Wall share | Regular churn |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| UTMM square-1 | 40.590 s | 9,345 | 757 | 120,708 | 3 | 69.575 ms | 55.108 ms | 0.171% | 89,296 |
| RPNG table_01 | 170.247 s | 38,302 | 3,030 | 418,927 | 4 | 58.666 ms | 40.334 ms | 0.034% | 114,143 |

Conclusion: current global densify/prune is not the average throughput
bottleneck. It remains a quality/interpretability concern because mutation
churn is large, and its 40--55 ms event spike must be checked under strict-live
tracking contention.

Artifacts:

- corrected profiles: `results/experiments/exp121_topology_cost_profile_v2/`;
- preserved pre-mapping environment failure:
  `results/experiments/exp121_topology_cost_profile/`.
