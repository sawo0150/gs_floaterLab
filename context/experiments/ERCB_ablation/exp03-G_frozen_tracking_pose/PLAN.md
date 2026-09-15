# exp03-G — frozen tracking-pose ERCB isolation

날짜: 2026-09-15  
상태: 3-seed × 2-scene 완료; 결과는 `RESULT.md`

## 질문

Fixed pose/init/topology replay에서는 저예산 ERCB가 이겼지만 strict online pose/native
topology에서는 실패했다. Tracking pose 오차와 PGBA map correction만 제거하고 native
online birth/densify/prune를 남겼을 때 dense-role interval ERCB의 저예산 이득이
복구되는가?

## 사전 고정 계약

- `gt_absolute` diagnostic oracle로 모든 RR/ERCB mapping camera와 evaluator pose를
  동일 GT trajectory에 고정한다. Frontend keyframe/depth 생성은 온라인으로 유지한다.
- PGBA의 map pose correction은 oracle 모드가 억제한다.
- causal RGB arrival, unified B1 KF RGBD+normal / dense appearance+opacity, native
  topology, packet physical-credit, fixed 1.5x sensor budget, zero-tail을 유지한다.
- RR와 ERCB는 role-stratified population clock으로 KF/dense service를 맞추고,
  keyframe은 shared RR, dense 순서만 `relative_floor(K=8,rho=.5,gamma=log3)`로 바꾼다.
- pilot: RPNG table_07 q3 seed0, UTMM square-1 q15 seed0.
- 두 장면 모두 fixed held-out `ERCB-RR > 0`일 때만 seed1/2로 확장한다.
- 이 결과는 GT pose를 쓰므로 strict 성과가 아니라 pose-feedback 원인 분리용이다.

## pilot gate

- RPNG table_07 q3 seed0: fixed held-out `+0.077602 dB`
- UTMM square-1 q15 seed0: fixed held-out `+0.042306 dB`
- 양 장면 모두 양수이므로 사전 계약에 따라 seed1/2 반복으로 확장한다.
