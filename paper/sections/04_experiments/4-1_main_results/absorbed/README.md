# absorbed/ — 이 소절에 흡수된 것

| 폴더 | 원래 | 본문에서 |
|---|---|---|
| `rate_robustness/` | `4-3_ablation_admission/` → `4-2_rate_robustness/` | §4.1의 run-in `\textbf{Rate robustness.}` + **Fig.4** |
| `compute_latency/` | `4-6_system_analysis/` → `4-5_compute_latency/` | §4.1의 run-in `\textbf{Compute and latency.}` |

## 왜 Ablations가 아니라 Main Results에 넣나

rate robustness는 **구성요소를 빼보는 것이 아니라** "주장한 성질이 실제로 성립한다"는 **결과**다.
ablation 소절에 넣으면 범주가 어긋난다.

## 왜 소절을 안 주나

- **P02가 아직 미착수다.** 결과가 나오기 전에 지면을 예약할 근거가 없다.
- 번호 붙은 소절 2개는 해부한 5편 중 lmrs·cartgs와 같고, 나머지 3편(3개)보다 하나 적을 뿐이다.
- 실험 자체는 그대로 크리티컬 패스에 남는다. **소절을 빼는 것과 실험을 빼는 것은 다르다.**
  P02는 C1의 정의적 성질(완료가 박자를 만든다 = credit-based)을 검증하는 유일한 실험이고,
  `plan/claims/`의 B2가 여기에 달려 있다. Fig.4도 그대로 간다.
- 결과가 강하게 나오면 그때 소절로 승격하면 된다. 지면이 있으면.
