# v10: admission history와 count 기반 sampling 분포

Imagegen 스킬 / 내장 imagegen 편집. 입력: `overall_pipeline_v09.png`. 수정 범위는 (b) View Sampling이며 오른쪽 loss와 다른 영역은 유지하도록 요청한다.

## 정량 예시 (실험 결과 아님)

Method §3.2의 `p_i ∝ exp(-β n_i)`에 맞춰 설명용으로 β=0.1, counts=[12,9,6,3,0]을 사용했다. 확률은 약 [0.10049,0.13564,0.18310,0.24715,0.33362]이며 표시는 반올림한 [10%,14%,18%,25%,33%]다. 합계 100%. 이 β는 실제 configuration 값을 주장하지 않는다.

오래전에 들어온 영상이 더 많이 선택된 상황의 **한 예시**다. 일반 정책이 admission age나 K/I 종류만으로 확률을 정한다는 의미가 아니다. 높은 count는 낮은 확률, 낮은 count는 높은 확률이며 모든 view의 확률은 양수다. 출력 I2를 유지해 최고확률 K5를 반드시 고르는 정책이 아니라는 점을 보존한다.

```text
Use case: precise-object-edit.
Image 1 is the EDIT TARGET, an academic overview. Edit ONLY the middle territory's bottom "(b) View Sampling" diagram, below the retained view pool. Preserve the entire left Online observations, the middle View Growth and its 3->4->5 snapshots, the entire right Gaussian map optimization including every loss diagram, all main headers, overall dimensions and footer.

Replace the current alternating tall/short gray bars and alternating blue probability bars. They misleadingly correlate with K/I type. Instead show FIVE ALIGNED DISCRETE VIEW COLUMNS in this order: K1, I2, K3, I4, K5. Gray K badges and teal I badges remain. This is one illustrative snapshot of accumulated selection history, not a keyframe preference or a deterministic age rule.
Upper row "Selection counts": values left-to-right 12, 9, 6, 3, 0. Draw gray vertical bars with monotonically DECREASING heights 12>9>6>3>0. Show each value legibly above its bar; the final zero is a zero-height baseline tick, not a positive bar.
Lower row "Sampling probabilities": blue vertical bars with monotonically INCREASING heights. Values left-to-right exactly "10%", "14%", "18%", "25%", "33%". They sum to 100%; ALL FIVE probabilities are positive. Each percentage is legible just above its corresponding blue bar. These are rounded illustrative softmax(-0.1 * count) probabilities. DO NOT put a large equation in the diagram.
Keep gray downward count-to-probability arrows between the rows aligned to each column. Keep K1,I2,K3,I4,K5 badges aligned beneath the probability bars. Add a subtle horizontal annotation beneath those badges: "Earlier admitted" on left and "Later admitted" on right with a fine rightward arrow. Make enough space without touching other territories.
Use the concise annotation "Fewer selections → higher probability" in blue near the sampling plot, replacing redundant clutter rather than overlapping existing text. Keep the selected-view output card on the right and its outgoing connection. Keep selected I2, even though K5 has greater probability: selection is STOCHASTIC, not guaranteed argmax. Keep "Sample without replacement" and "One view per update" above that card.
Reroute "Selection history" as a thin blue return from the selected-view card to the UPPER GRAY COUNT ROW, with exactly one arrowhead at counts. This loop must not point at probabilities or at the view badges. It can use the clear space along the bottom and left of the small sampling plot without crossing text.
Do not alter any geometry/initialization lines outside this sampling subsection. Do not add a continuous Gaussian curve: this is a categorical probability mass distribution over views. Preserve the footer "Schematic examples — not experimental results". No extra performance claims, new modules, new title or copied reference paper content. Preserve the wide full figure.
```
