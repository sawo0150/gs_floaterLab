# sections/ — CVPR 목차 지도

> 각 절 폴더에 **무엇을 쓸지**(`plan/`)와 **실제 문장**(`draft/`)이 버전별로 쌓인다.
> 절의 고정 메타(claim·근거실험·그림·claim boundary)는 각 폴더의 `README.md`.
> 이 표는 각 폴더 README에서 생성한 것이다.

전체 서사와 페이지 배분은 [`../plan/outline/CURRENT.md`](../plan/outline/CURRENT.md).

| 절 | 폴더 | latex | 담당 | 분량 | 상태 |
|---|---|---|---|---|---|
| Abstract | [`00_abstract/`](00_abstract/) | `sec/0_abstract.tex` | 나 | 150-200 words | plan v01 / draft 없음 |
| Teaser Figure | [`00_teaser/`](00_teaser/) | `fig/teaser.tex` | 나 | 1 col | plan v01 / draft 없음 |
| 1. Introduction | [`01_intro/`](01_intro/) | `sec/1_intro.tex` | 나 | 1.0 p | plan v01 / draft 없음 |
| 2.1 GS-SLAM | [`02_related/2-1_gs_slam/`](02_related/2-1_gs_slam/) | `sec/2_related.tex` | 나 | 0.3 p | plan v01 / draft 없음 |
| 2.2 View Selection / Active Vision | [`02_related/2-2_view_selection/`](02_related/2-2_view_selection/) | `sec/2_related.tex` | 나 | 0.3 p | plan v01 / draft 없음 |
| 2.3 Shuffling / Without-replacement SGD | [`02_related/2-3_shuffling_theory/`](02_related/2-3_shuffling_theory/) | `sec/2_related.tex` | 나 | 0.25 p | plan v01 / draft 없음 |
| 2.4 Floater / Geometry Regularization | [`02_related/2-4_geometry_reg/`](02_related/2-4_geometry_reg/) | `sec/2_related.tex` | 팀원 | 0.3 p | plan v01 / draft 없음 |
| (도입) Method opening | [`03_method/3-0_overview/`](03_method/3-0_overview/) | `sec/3_method.tex` | 나 | 0.17 p | plan v03 / draft 없음 |
| 3.1 Compute-Paced View Growth (★C1) | [`03_method/3-1_compute_paced_view_growth/`](03_method/3-1_compute_paced_view_growth/) | `sec/3_method.tex` | 나 | 0.69 p | plan v01 / draft 없음 |
| 3.2 Entropy-Regularized Count Balancing — ERCB (★C2) | [`03_method/3-2_ercb/`](03_method/3-2_ercb/) | `sec/3_method.tex` | 나 | 0.68 p | plan v01 / draft 없음 |
| 3.3 Causal Free-Space Carving (★C3) | [`03_method/3-3_carve/`](03_method/3-3_carve/) | `sec/3_method.tex` | 팀원 | 0.7 p | plan v01 / draft 없음 |
| (도입) Experimental Setup | [`04_experiments/4-0_setup/`](04_experiments/4-0_setup/) | `sec/4_experiments.tex` | 나 | 0.35 p | plan v01 / draft 없음 |
| 4.1 Main Results | [`04_experiments/4-1_main_results/`](04_experiments/4-1_main_results/) | `sec/4_experiments.tex` | 나 | 1.1 p | plan v01 / draft 없음 |
| 4.2 Ablations | [`04_experiments/4-2_ablations/`](04_experiments/4-2_ablations/) | `sec/4_experiments.tex` | 나·팀원 | 0.75 p | plan v01 / draft 없음 |
| 5. Conclusion | [`05_conclusion/`](05_conclusion/) | `sec/5_conclusion.tex` | 나 | 0.2 p | plan v01 / draft 없음 |
| 6. Limitations | [`06_limitations/`](06_limitations/) | `sec/5_conclusion.tex` | 나 | 0.2 p | plan v01 / draft 없음 |
| Rebuttal (2027-02 대비) | [`R_rebuttal/`](R_rebuttal/) | `rebuttal.tex` | 나 | 1 p | plan v01 / draft 없음 |
| Supplementary | [`X_supplementary/`](X_supplementary/) | `sec/X_suppl.tex` | 나 | 제한 없음 | plan v01 / draft 없음 |

## latex 대응

`latex/main.tex` 가 `\input` 하는 파일은 CVPR author-kit 규약을 따른다.
author-kit의 `2_formatting.tex` / `3_finalcopy.tex` 는 설명용 더미라
`2_related` / `3_method` / `4_experiments` / `5_conclusion` 으로 교체했고,
원본은 `latex/authorkit_reference/` 에 보관했다.

## 작업 순서

1. `plan/CURRENT.md` 에 무엇을 쓸지 먼저 정리한다 (bullet).
2. 근거가 확보되면 `draft/` 를 만들고 영어 문장을 쓴다.
3. 확정된 문장만 `latex/sec/*.tex` 로 옮긴다.
4. 실험 결과가 들어와 주장이 바뀌면 `newver.sh` 로 버전을 올린다.
