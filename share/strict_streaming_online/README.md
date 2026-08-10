# strict streaming online 결과 PLY (1253/305/12F)

pure-online strict streaming(timestamp 순 Aria RGB+IMU만 사용, MPS 후처리 입력 없음,
fixed 1.5× live budget, 마지막 프레임 뒤 optimizer update 0회) 조건에서 나온
`3dgs_before_final.ply`(polishing 이전 원본, 평가에 쓰인 것과 동일)다.

**세 장면이 모두 27dB에 도달한 것은 아니다** — 현재 27dB 재현이 확정된 장면은
1253호뿐이고, 305호/12F는 exp59 cross-scene transfer에서 발견된 미해결 generalization
gap(경계 flag가 프레임 길이에 안 맞음, 305는 IMU excitation 한계로 추가 잔여 오차)이
남아있는 상태의 **현재 best strict-online 결과**다. 자세한 내용은
`context/experiments/exp59_strict27_cross_scene_transfer.md`,
`context/experiments/exp60_viewpoint_novelty_sampler.md` 참고.

| 파일 | 장면 | held-out PSNR | 출처 |
|---|---|---:|---|
| `1253__strict_online_freeze800_27.86dB_exp57.ply` | aria1253 | **27.86dB** | exp57 채택 recipe (freeze800, 2-run 평균 27.8464dB 중 run1) |
| `305__strict_online_vanillatrack_18.74dB_exp62.ply` | aria301_305 | 18.74dB | exp62 (freeze800 + tracking block만 vanilla로 복원, exp59 as-is 16.99dB보다 개선) |
| `12F__strict_online_freeze800_asis_25.90dB_exp59.ply` | aria301_12F | 25.90dB | exp59 freeze800 recipe as-is 적용 (재튜닝 없음) |

305/12F는 27dB recipe를 재튜닝 없이 그대로 옮긴 결과이며, 아직 채택된 최종본이 아니다.
