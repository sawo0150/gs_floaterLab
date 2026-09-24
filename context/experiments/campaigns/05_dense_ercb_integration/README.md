# DENSE — making dense views and ERCB materially active

## 현재 결론

Dense view는 **보조 supervision**으로는 품질을 보존하거나 작은 이득을 줄 수
있다. 그러나 RGB-D+normal historical keyframe을 RGB-only dense view로 직접
교체하면 RPNG에서 손실이 난다. ERCB는 선택 trace를 바꾸도록 활성화했지만
RR 대비 독립 PSNR gain은 아직 입증되지 않았다.

| Subtrack | 실험 | 관찰 | 상태 |
|---|---|---|---|
| dense repeat | [111](../../exp111_dense_repeat_ercb.md) | dense share 약 2배, 3-family 평균 +0.015 dB vs R4 | SAFE |
| normalized ERCB strength | [112](../../exp112_normalized_temperature.md) | gamma16은 trace 활성, RR 대비 −0.009 dB | ACTIVE, gain 미입증 |
| LPM signal/prior | [113](../../exp113_lpm_error_zone_probe.md)–[117](../../exp117_lpm_mass_transfer.md) | official error-zone signal과 mass prior 활성, 3-family 품질 보존 | SAFE evidence |
| unified dense slot | [118](../../exp118_unified_dense_global.md)–[120](../../exp120_unified_dense_transfer.md) | dense share 5.6–6.7%, 평균 −0.048 dB; RPNG −0.186 dB | NOT ADOPTED |
| loss diagnosis | [122](../../exp122_dense_global_topology_stats_isolation.md)–[123](../../exp123_dense_geometry_mass_isolation.md) | topology stats나 scalar geometry mass가 아니라 view-specific RGB-D coverage가 주원인 | CLOSED |

## 다음 설계 제약

- native RGB-D carrier를 제거하지 않는다.
- dense는 별도 auxiliary service 또는 이미 지불한 appearance slot에서 사용한다.
- dense/ERCB contribution은 “활성 trace”와 “품질 보존”을 넘어 RR 대비 causal
  gain을 보여야 한다.
- 장면별 ratio, temperature, phase cutoff 튜닝은 하지 않는다.
