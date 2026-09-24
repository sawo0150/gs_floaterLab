# Experiment hub

실험 번호를 순서대로 읽지 않는다. 이 파일에서 **연구 질문별 campaign**으로
들어가는 것이 기본 탐색 경로다. `INDEX.md`는 삭제하지 않는 chronological
ledger이고, `results/experiments/`는 재현성을 위해 경로를 고정한 raw artifact
store다.

## 지금 먼저 볼 것

| 목적 | 문서 | 현재 결론 |
|---|---|---|
| 논문용 공식 B-track 결과 | [BENCH](campaigns/03_benchmark_contract/README.md) | Exp94/109: official vanilla 대비 17/17, 평균 약 +1.29 dB |
| 그 이득이 어디서 왔는지 | [ATTR](campaigns/06_gain_attribution/README.md) | service grouping과 birth/capacity를 아직 완전히 분리하지 못함 |
| dense view와 ERCB의 실제 효과 | [DENSE](campaigns/05_dense_ercb_integration/README.md) | supplementary dense는 안전하지만 ERCB 독립 PSNR 이득은 미입증 |
| local topology 및 pruning | [TOPO](campaigns/04_local_topology/README.md) | bounded ticket은 품질 보존; aggressive KF→dense replacement는 기각 |
| strict realtime 계보 | [LIVE](campaigns/01_strict_streaming/README.md) | strict/live와 mapping-only B-track은 분리해서 해석해야 함 |

## Campaign 구조

| Code | 범위 | 연구 질문 |
|---|---:|---|
| `LEGACY` | exp01–51 | batch 품질, floater, 초기 incremental 기반 |
| `LIVE` | exp52–65, 일부 77–79 | strict streaming과 mapper runtime |
| `SCHED` | exp66–76 | dense supervision·view scheduling·ERCB 기초 |
| `BENCH` | exp77–94, 109 | frozen-tracker 공정 비교와 공식 main result |
| `TOPO` | exp95–110, 121 | birth/prune/local topology와 source-backed operator |
| `DENSE` | exp111–123 | dense/ERCB 활성화 및 공격적 통합의 원인 분석 |
| `ATTR` | 다음 작업 | vanilla 대비 bulk gain의 causal attribution |

- [전체 campaign catalog](campaigns/README.md)
- [기존 시간순 ledger](INDEX.md)
- [현재 시스템 상태](../STATUS.md)
- [benchmark 실행 코드 분류](../../benchmarks/online_gs/EXPERIMENT_GROUPS.md)

## 앞으로의 이름 규칙

`expNNN`은 provenance용 내부 ID로만 유지한다. 새 문서·runner·결과의 사람이
읽는 경로는 아래처럼 campaign과 질문을 앞세운다.

```text
context/experiments/campaigns/<campaign>/<question>/
benchmarks/online_gs/campaigns/<campaign>/<runner>.py
results/campaigns/<campaign>/<question>/<run>/
```

예: 다음 factorial은 `ATTR/service_birth_factorial`로 부르고, 필요할 때만
metadata에 legacy ID `exp124`를 기록한다. 기존 `expNN` 경로는 source lock과
문서 링크를 깨지 않기 위해 이동·삭제하지 않는다.
