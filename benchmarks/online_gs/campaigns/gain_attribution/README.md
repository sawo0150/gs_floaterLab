# Gain attribution runners

다음 active campaign의 구현 위치다. 계획과 판정 기준은
`context/experiments/campaigns/06_gain_attribution/README.md`에 있다.

Role-aware dense photometric service 대표 3-family runner:

```bash
/home/colin/miniconda3/envs/vigs-slam-5090/bin/python \
  benchmarks/online_gs/campaigns/gain_attribution/run_role_aware_dense_service.py \
  preflight

/home/colin/miniconda3/envs/vigs-slam-5090/bin/python \
  benchmarks/online_gs/campaigns/gain_attribution/run_role_aware_dense_service.py \
  run-all
```

Runner는 기존 Exp94/109 artifact를 덮어쓰지 않고
`results/campaigns/gain_attribution/role_aware_dense_service_v3/`에 source lock,
장면별 3-arm 결과, double-evaluation과 verification을 저장한다. 현재 v3는
UTMM `square-1`, RPNG `table_01`, Aria `aria1253`를 같은 설정으로 실행하며,
기존 aux-KF appearance slot까지 dense repeat로 옮긴 paper-aligned candidate다.
상세 판정과 v1 duplicate-batch 정정은
`context/experiments/exp124_role_aware_dense_service.md`를 따른다.
