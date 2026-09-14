# exp68 PLY comparison bundle

이 디렉터리의 Google Drive 복제본은 `gs_floaterLab/exp68_geometry_scheduler/`에 있다.

> **2026-08-26 사후 감사 정정:** 기존 floater PASS는 manual region의
> `opacity > 0.3` Gaussian 중심 count에만 해당한다. 저-opacity dust, covariance
> footprint, 큰-scale splat까지 포함한 broad geometry baseline 동등성은 성립하지
> 않는다. 전체 감사, 실제 `map()` 구현, 1253/305 partial pass와 12F blind 실패는
> `exp68_geometry_postmortem_audit.html`을 우선 참조한다.

## 비교 순서

각 장면에 대해 네 PLY를 비교한다.

1. `baseline_exp67`: native tracked-keyframe `map()` baseline
2. `universal_scheduler_exp67`: dense adaptive replay, geometry scheduler 추가 전
3. `dense_only_carve_fisher_exp68`: carve/Fisher + dense-only replay
4. `mixed_carve_fisher_exp68`: 최종 설정, keyframe+dense mixed replay

파일명의 dB는 기존 Drive convention에 맞춘 **all-view PSNR**이다. Geometry 비교의 주 지표는
manual floater region 안에서 `opacity > 0.3`인 Gaussian의 nominal count다.

| scene | condition | all-view PSNR | visible floater | vertices |
|---|---|---:|---:|---:|
| aria1253 | exp67 baseline | 24.87 | 118 | 87,984 |
| aria1253 | exp67 universal scheduler | 27.94 | 193 | 96,657 |
| aria1253 | exp68 dense-only carve/Fisher | 28.22 | 139 | 93,881 |
| aria1253 | exp68 final mixed | 28.03 | 126 | 93,933 |
| aria301_305 | exp67 baseline | 25.95 | 491 | 82,248 |
| aria301_305 | exp67 universal scheduler | 29.79 | 660 | 82,237 |
| aria301_305 | exp68 dense-only carve/Fisher | 30.23 | 576 | 79,163 |
| aria301_305 | exp68 final mixed | 30.70 | 529 | 83,176 |

## 해석 주의

- exp68 final fixed held-out PSNR은 aria1253 27.9331 dB, aria301_305 30.6697 dB다.
- Floater mask는 trajectory Sim3로 정합한 상대 진단이다. 정합 median 오차는 2.48 cm / 6.34 cm이고
  mask voxel은 7.5 cm이므로 작은 절대 count 차이를 과도하게 해석하지 않는다.
- exp68 final은 exp67 scheduler보다 visible floater가 34.7% / 19.8% 적다.
- native baseline과 비교하면 6.8% / 7.7% 많다. 이는 좁은 visible 지표에서만 baseline에
  접근했다는 뜻이며, 전체 geometry가 baseline 수준이라는 뜻은 아니다.
- 저-opacity dust를 포함한 region 전체 Gaussian 수는 아직 native baseline보다 많다.

## 문서

- `exp68_geometry_postmortem_audit.html`: PLY 재감사, 기존 PASS 정정, 증분 carve 구현, dust pruning 실패와 12F PSNR 하락 원인, 기존 exp68 대비 최종 판정
- `exp68_scheduler_method_explainer.html`: scheduler 구조·수식·파라미터·근거
- `exp68_geometry_scheduler_result.html`: 최종 정량 결과와 label 감사

## MD5

| file source | MD5 |
|---|---|
| aria1253 exp67 baseline | `f0b324fa001c6fcbf39f9d3d05882009` |
| aria1253 exp67 scheduler | `d79989c5c3d0d8a701876509f073a639` |
| aria301_305 exp67 baseline | `18dd1757620b45ee07acb40cc6716c32` |
| aria301_305 exp67 scheduler | `7c98c401b0f0a1d131690d088654833a` |
| aria1253 exp68 dense-only | `f37cdee02d9b02474a32356ac4804353` |
| aria301_305 exp68 dense-only | `642a83c82a5a2e9c4b2cb738afd54b8d` |
| aria1253 exp68 final mixed | `86c61be350ba0eb02a4c93ba4b705293` |
| aria301_305 exp68 final mixed | `4999d3a88093e4b9f2563c422ecf66f4` |
