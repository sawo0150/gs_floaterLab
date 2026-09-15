# exp03-F — reliable-role ERCB under low packet budget

날짜: 2026-09-15
상태: 완료 — seed 확장 gate 실패

## 질문

exp03-E에서 pose-noisy dense view에 ERCB coverage를 강제한 것이 end-to-end PSNR
이득을 막았는가? Source 역할과 physical Adam service를 맞춘 채, 신뢰도가 높은 tracked
keyframe 안에서만 같은 interval relative-floor ERCB를 적용하면 RR보다 저예산
held-out PSNR이 높아지는가?

## 사전 고정 계약

- RR와 ERCB의 causal KF/dense 역할 sequence는 동일하다.
- ERCB arm은 keyframe ordering만 바꾸고 dense ordering은 shared causal RR이다.
- `K=8`, `rho=.5`, `gamma=log(3)`는 exp03에서 고정한 값을 그대로 쓴다.
- packet당 physical B1 Adam credit, fixed-arrival dense membership, online pose/native
  topology, fixed 1.5x sensor budget, zero-tail은 exp03-E와 동일하다.
- 먼저 RPNG table_07 q3 exact-service pair와 UTMM square-1 q15 seed0을 본다.
- 두 scene 모두 양수일 때만 seed1/2로 확장한다. 장면별 파라미터 sweep은 하지 않는다.
- primary metric은 fixed held-out PSNR의 paired `ERCB - RR`이다.

## 구현

VIGS `a3c04e43`에서 `--mapping_interval_ercb_target_role keyframe`을 추가했다.
CPU selector test는 12/12 통과했다.
