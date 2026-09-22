# Fig.3 수평 비교 A/B 선택안

사용자 선택: **B안**. `VIGS-SLAM best` 문구를 제거한 [현행본](../current/README.md)을 사용한다.

2026-09-21. 사용자가 직접 보고 판단할 수 있도록 기존 검토안을 논문용 SVG/PDF/PNG로 출력했다.
두 안의 원시 곡선28점, frame1420 이미지6개, 86.49×46.13 mm 크기는 같다.
Inkscape PDF를 Poppler로 PNG 렌더링하고 단 폭200dpi에서 배치를 확인했다.

| 안 | 비교 | PNG | SVG | PDF |
|---|---|---|---|---|
| A | Ours2000→baseline2400:400 iter. Ours가 기준을 넘고 이후 저장점에서도 유지 | [PNG](fig3_frame1420_peak_A_400iter.png) | [SVG](fig3_frame1420_peak_A_400iter.svg) | [PDF](pdf/fig3_frame1420_peak_A_400iter.pdf) |
| B | Ours1400→baseline2400:1000 iter. Ours의 첫 저장점 도달; 이후 재하락 포함 | [PNG](fig3_frame1420_peak_B_1000iter.png) | [SVG](fig3_frame1420_peak_B_1000iter.svg) | [PDF](pdf/fig3_frame1420_peak_B_1000iter.pdf) |

기준은 baseline 최고 관측 PSNR23.28134465 dB다. 별표는 캡션에서 각 정의를 설명한다.

A 캡션 추가문:

> The bracket compares the baseline checkpoint with the highest observed PSNR
> (2,400 iterations) against the earliest stored checkpoint from which ours
> remains above that PSNR at every subsequent stored checkpoint (2,000 iterations).

B 캡션 추가문:

> The bracket compares the baseline checkpoint with the highest observed PSNR
> (2,400 iterations) against the first stored checkpoint at which ours reaches
> or exceeds that PSNR (1,400 iterations), regardless of subsequent regressions.

두 경우 모두 wall-clock time이나 수렴 완료를 뜻하지 않는다. 원고 TeX는 수정하지 않았다.
[문헌·세부 판단](../analysis/peak_annotation_review/README.md) · [검증](qa/peak_options_validation.json).
재생성: `python humanteck/sections/02_method/figure03/scripts/export_peak_options.py`
