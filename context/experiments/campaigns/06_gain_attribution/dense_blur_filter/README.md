# Dense blur filter — causal interval admission

2026-09-26. 질문: 흐린 dense RGB를 제외하면 unified mapper의 held-out 품질과 dense 사용 이득이 유지되는가?

- 기존 최종 unified: 3:3:6, 영상별 Adam, cumulative ERVS, scale≤0.1 projection, densify/prune OFF.
- 공통 40 renders/KF, seed0, Aria1253/RPNG table_06/UTMM square-1, 동일 frozen causal tracker/input/eval cohort, zero-tail.
- 비교: off(3:3:6), on(3:3:6), no_dense(3:9:0; dense 예산을 full-KF ERVS로 이동).
- no_dense도 membership immediate이며 후보는 보유하지만 dense role quota가 0이므로 사용은 0. KF-only 의미는 학습 서비스에 한정.
- 기준을 결과 전에 고정: 이미 도착한 양쪽 KF와 그 사이 dense 후보의 CPU RGB에서 중심80%를 최대384px로 축소, Laplacian energy와 Laplacian/gradient-energy 비를 계산한다. 두 점수가 interval 75분위의 각각 0.5/0.75 미만인 후보만 제외한다.
- 절대 blur classifier가 아닌 상대 sharpness proxy다. 질감 변화·noise·구간 전체 blur를 완벽하게 구별하지 못한다. score/첫 admission decision을 UID별로 고정·캐시한다. held-out 영상은 기준 계산에도 사용하지 않는다.
- filter OFF가 기본값. 새 설정은 성능 검증 전 자동 채택하지 않는다. accepted full dense pool과 ERVS는 그대로 유지.
- quality를 보기 전에 synthetic CPU tests 6개 PASS. 실제 RGB 진단과 독립 run audit를 추가한다.
- 모든 장면/arm을 보고하며 threshold를 장면별로 튜닝하지 않는다. 실제 concurrent tracking/strict realtime 실험은 아니다. 3scene seed0 개발 실험이다.

**2026-09-26 dense blur off / aria:** execution=True, audit=True, PSNR=25.595737493675173, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/dense_blur_filter/gpu40_v1/off/aria.

**2026-09-26 dense blur on / aria:** execution=True, audit=True, PSNR=25.573838343147102, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/dense_blur_filter/gpu40_v1/on/aria.

**2026-09-26 dense blur no_dense / aria:** execution=True, audit=True, PSNR=24.738654588015024, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/dense_blur_filter/gpu40_v1/no_dense/aria.

## 이미지 진단과 사전 선언한 민감도 점검

Aria v1 on에서는 후보924장 중 제외0장이었다. 상대 energy 최소0.534, frequency 최소0.837이어서 .5/.75 조건이 전혀 발동하지 않았다. no-op 실행의 PSNR 차이(OFF25.5957 vs ON25.5738)는 블러 제거 효과가 아니며 CUDA 학습의 수치 변동이다.

실제 RGB 102/128/1271 및 낮은 relative frequency 후보994/996/997/1127을 인접KF와 시각 확인했다. energy만 낮은128은 foreground 질감이 화면에서 사라진 영향도 있어 energy 단독 threshold는 쓰지 않는다. v1을 그대로 완료해 보존한 뒤 **공통 .8 energy / .9 frequency** 민감도 설정을 추가 검증한다(PSNR 최적화가 아니라 0개 제외인 gate의 작동 범위를 점검). 이 기준은 현재 Aria score로7장을 제외하며, RPNG/UTMM 결과를 보고 장면별 조절하지 않는다. 모든 설정 결과를 보고한다.

**2026-09-26 dense blur off / rpng:** execution=True, audit=True, PSNR=25.11266457841203, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/dense_blur_filter/gpu40_v1/off/rpng.

**2026-09-26 dense blur on / rpng:** execution=True, audit=True, PSNR=25.13288996241114, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/dense_blur_filter/gpu40_v1/on/rpng.

**2026-09-26 dense blur no_dense / rpng:** execution=True, audit=True, PSNR=24.79906783576484, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/dense_blur_filter/gpu40_v1/no_dense/rpng.

**2026-09-26 dense blur off / utmm:** execution=True, audit=True, PSNR=22.110949398558816, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/dense_blur_filter/gpu40_v1/off/utmm.

**2026-09-26 dense blur on / utmm:** execution=True, audit=True, PSNR=22.12322810844139, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/dense_blur_filter/gpu40_v1/on/utmm.

**2026-09-26 dense blur no_dense / utmm:** execution=True, audit=True, PSNR=21.39954235229963, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/dense_blur_filter/gpu40_v1/no_dense/utmm.

**2026-09-26 dense blur on / aria:** execution=True, audit=True, PSNR=25.607050022096125, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/dense_blur_filter/gpu40_v2/on/aria.

## 실제 RGB 시각 점검

`inspect_dense_blur_examples.py`로 held-out이나 최종 rendering을 보지 않고, 저장된 후보 판정의 실제 training RGB와 양쪽 도착 KF를 비교했다. Aria v2는 제외 UID를 시간순으로 균등 추출해651/993/996/1271을 확인했다. 일부(특히651/1271)에서 인접 KF 대비 경계 흐림이 보이지만 모든 제외를 motion blur 정답으로 보증하지는 않는다. RPNG v1 제외1162/2041도 포스터와 테이블 패턴의 선명도 차이를 확인했다. 그림과 UID/선정 규칙 JSON은 각 run 디렉터리에 보존한다.

- v1: `results/campaigns/gain_attribution/dense_blur_filter/gpu40_v1/{aria_low_sharpness,rpng_rejected}.png`
- v2: `results/campaigns/gain_attribution/dense_blur_filter/gpu40_v2/aria_rejected.png`

**2026-09-26 dense blur on / rpng:** execution=True, audit=True, PSNR=25.09907927985664, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/dense_blur_filter/gpu40_v2/on/rpng.

**2026-09-26 dense blur on / utmm:** execution=True, audit=True, PSNR=22.10371916971089, error=None; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/dense_blur_filter/gpu40_v2/on/utmm.

## 완료

[전체 비교와 최종 판단](SUMMARY.md), [구현 및 옵션](IMPLEMENTATION.md). GPU12runs/CPU24tests PASS. 기존 기본OFF, 검증된 필터ON recipe 별도 제공.
