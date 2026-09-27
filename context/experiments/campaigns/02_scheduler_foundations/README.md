# SCHED — dense supervision and ERCB foundations

## 질문

동일 또는 제한된 update budget에서 어떤 view를 언제 다시 학습해야 하는가?

| 묶음 | 실험 | 핵심 결론 |
|---|---|---|
| fixed-map view density | [exp66](../../exp66/exp66_viewset_density_result.html) | dense RGB view는 충분한 budget에서 KF-only보다 크게 유리할 수 있음 |
| online scheduler 구조 | [exp67](../../exp67/exp67_scheduler_explainer.html)–[69](../../exp69/README.md) | frontier/balanced/replay 구조의 기원 |
| entropy/count scheduling | [exp70](../../exp70/exp70_max_entropy_view_scheduler_sim.md)–[76](../../exp76/exp76_mean_normalized_softmax_ablation.md) | ERCB 수식과 normalized potential 기초 |

## 해석상 주의

- exp66의 +3 dB는 frozen-map RGB-only refinement 조건이다. 현재 online
  RGB-D keyframe 한 장을 RGB-only dense로 교체해도 된다는 뜻이 아니다.
- raw variance와 mean-normalized variance는 effective temperature dynamics가
  다르며 같은 sampler로 포장하지 않는다.
- 이 campaign은 “dense view가 유용할 수 있다”는 근거이지, 현 R4의 +1.29 dB가
  ERCB 때문에 생겼다는 근거는 아니다.
