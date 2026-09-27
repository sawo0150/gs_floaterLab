# exp124 — Role-aware dense photometric service

- 날짜: 2026-09-24
- 상태: **대표 3-family gate PASS / 품질 gain 미입증**
- 코드: lab `23e0410`, VIGS `d8c2eb76`
- artifact: `results/campaigns/gain_attribution/role_aware_dense_service_v3/`

## 문제와 판정 기준

Exp94/109의 최종 품질은 official vanilla보다 높았지만 physical render의 거의
전부가 keyframe window에 쓰였다. Dense RGB/ERCB가 약 1%대 부가 경로에만
있다면 이를 최종 방법의 중심 contribution으로 설명할 수 없다. 반대로 과거
Exp119--123처럼 historical RGB--D keyframe 한 장을 RGB-only dense view로 바로
교체하면 RPNG 품질이 하락했다. 따라서 이번 실험은 다음을 동시에 요구했다.

1. Dense RGB가 전체 render의 최소 5% 이상을 실제로 사용한다.
2. Normalized ERCB가 동일-work RR과 다른 view trace를 만든다.
3. RGB--D keyframe의 geometry backbone과 topology 통계는 보존한다.
4. Backbone/normalized/RR의 physical render, Adam step, causal input,
   held-out, zero-tail 계약을 일치시킨다.
5. 장면별 hyperparameter나 phase cutoff를 쓰지 않고 UTMM/RPNG/Aria 대표
   장면에 같은 설정을 적용한다.

## 구현

관측을 하나의 replay pool로 섞지 않고 역할을 분리한다.

- **Geometric keyframe service:** native RGB--D/normal loss, pose constraint,
  densification statistics와 topology mutation을 담당한다.
- **Photometric dense service:** causal하게 bracket된 intermediate RGB를
  사용하며 SH appearance만 갱신한다. `xyz`, scale, rotation은 freeze하고
  densification statistics에도 넣지 않는다.
- 각 native mapping call에서 마지막 반복 1개만 flexible quantum으로 열고,
  최소 한 번의 complete geometry iteration을 보호한다. Dense pool이 native
  batch cardinality만큼의 서로 다른 view를 공급할 수 없으면 native geometry
  iteration을 그대로 실행하고 service debt를 보존한다.
- Dense batch는 normalized-variance Gibbs
  `p_i ∝ exp[-16 n_i/(T+1)]`로 중복 없이 뽑고, Adam 성공 뒤에만 selection
  count를 commit한다. RR arm은 Gibbs energy만 0으로 둔 work-matched control이다.
- 기존 R4의 auxiliary one-view keyframe appearance slot도 dense repeat로
  재배치한다. Repeat는 primary admission credit을 만들지 않는다.

## 구현 오류 발견과 정정

v1은 multi-view batch를 transactional하게 예약했지만 한 batch 안에서 같은
dense UID를 중복 선택할 수 있었다. 중복 batch는 UTMM 53/55, RPNG 148/217,
Aria 77/81개였으므로 v1은 view-diversity 근거로 무효다. VIGS commit
`d8c2eb76`에서 sequential without-replacement proposal로 고치고 128개
CUDA-free test를 전부 통과했다. v2는 이 오류를 고쳤고, v3는 여기에 기존
aux-KF appearance slot의 dense repeat 전환까지 적용한 최종 paper-aligned
candidate다. v3 duplicate batch는 3장면 모두 0이다.

## v3 결과

| Scene | Backbone | Normalized | RR | N−B | N−RR | Role photo share | Total dense share | Render / Adam | ERCB↔RR trace diff | Gate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| UTMM square-1 | 21.227975 | 21.009381 | 21.017637 | −0.218595 | −0.008256 | 10.16% | 11.50% | 9,345 / 757 | 41 | PASS |
| RPNG table_01 | 25.580296 | 25.466880 | 25.462897 | −0.113417 | +0.003983 | 9.77% | 11.03% | 38,302 / 3,030 | 115 | PASS |
| Aria aria1253 | 25.751478 | 25.644918 | 25.618089 | −0.106560 | +0.026829 | 10.26% | 11.58% | 13,620 / 1,055 | 57 | PASS |

- Mean normalized − backbone: **−0.146190 dB**
- Mean normalized − RR: **+0.007519 dB**
- Normalized final Gaussian / backbone:
  120,056/120,143, 417,261/417,932, 177,223/177,144
- Normalized/backbone mapping wall time:
  39.71/39.44 s, 165.24/166.69 s, 34.16/38.47 s
- 모든 arm에서 same physical render, same Adam step, causal event,
  held-out disjointness, double evaluation, zero-tail, equal-cardinality,
  geometry-scope, transactional without-replacement 검증이 PASS했다.

Selection-count 최소값이 0인 것은 late-arriving view가 zero-tail 이전에 모두
service되지 못했기 때문이다. 장면 끝에서 추가 최적화를 하지 않았으며, 남은
service debt는 210/217/233으로 그대로 기록했다.

## 결론

이번 변경으로 “99% keyframe-window mapper에 이름만 붙은 dense/ERCB” 문제는
해소됐다. Dense RGB가 전체 physical render의 약 11%를 쓰고, ERCB도 실제
selection trace를 바꾸며, keyframe RGB--D geometry carrier는 유지된다.

그러나 **ERCB의 품질 우월성은 입증되지 않았다**. Normalized−RR 평균은
+0.0075 dB로 noise 수준이고, role-aware candidate도 backbone보다 평균
0.146 dB 낮다. 따라서 이 결과로 주장할 수 있는 것은 역할 분리된 dense
service가 active하고 대표 3장면에서 품질을 크게 훼손하지 않는다는 것까지다.
기존 official vanilla 대비 +1.29 dB는 Exp109 결과이며 이를 exp124의 dense/ERCB
causal gain으로 재해석하지 않는다. 17-scene main table과 strict-live latency
claim은 아직 없다.

## 재현

```bash
/home/colin/miniconda3/envs/vigs-slam-5090/bin/python \
  benchmarks/online_gs/campaigns/gain_attribution/run_role_aware_dense_service.py \
  preflight

/home/colin/miniconda3/envs/vigs-slam-5090/bin/python \
  benchmarks/online_gs/campaigns/gain_attribution/run_role_aware_dense_service.py \
  run-all
```

요약은 `results/campaigns/gain_attribution/role_aware_dense_service_v3/summary.md`,
장면별 검증은 각 `verification.json`, 고정 source/commit은 `source_lock.json`에
있다.
