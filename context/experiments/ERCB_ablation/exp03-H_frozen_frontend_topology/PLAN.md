# exp03-H — frozen frontend packet + topology trace isolation

날짜: 2026-09-15  
상태: v1/v2 interleaving 실패 보존, v3 2-scene seed0 완료; 결과는 `RESULT.md`

## 질문

exp03-G에서 GT pose만 고정하자 ERCB delta가 다시 양수가 됐지만 과거 fixed
pose/init/topology replay보다 작았다. VIGS 내부에서도 RR와 dense-role ERCB가 정확히
같은 frontend supervision packet과 topology 결정을 받을 때 저예산 이득이 복구되는가?

## 사전 고정 계약

- UTMM square-1, q15, seed0 pilot부터 시작한다.
- reference capture 한 번에서 mapper가 실제 소비한 KF RGB/depth/normal/GT pose와
  causal dense records를 packet 단위로 기록한다.
- reference의 각 native topology event에서 stable point ID 생존 집합과 새 Gaussian
  초기값을 기록한다. 비교 arm은 topology를 끄거나 특정 iteration에서 freeze하지 않고,
  같은 native event clock에서 기록된 구조 변화를 적용한다.
- replay RR와 ERCB는 packet frame ID를 매 event exact-match해야 한다. 불일치는 즉시
  실패시킨다.
- unified B1, KF RGBD+normal, dense appearance+opacity, role-stratified KF/dense clock,
  packet physical credit, fixed 1.5x sensor budget, zero-tail은 유지한다.
- GT pose 및 reference topology를 쓰므로 strict 성과가 아니라 scheduler isolation이다.

## 판정

1. replay packet/topology count가 reference와 정확히 일치해야 한다.
2. Adam, KF/dense service, final stable topology를 pair-match한다.
3. primary는 mapping-excluded fixed held-out PSNR의 `ERCB-RR`이다.
4. UTMM pilot이 유효하고 양수이면 RPNG table_07 q3로 무재튜닝 전이한다.

## v1 정정

최초 구현은 packet 저장 run에서 topology도 동시에 기록했다. 저장 I/O 때문에 reference와
replay의 packet↔optimizer interleaving이 달라져 두 번째 topology event 직전 stable ID가
`95,435 vs 115,361`로 불일치했고 즉시 실패시켰다. 해당 output은 실패 증거로 보존한다.
v2는 ① packet-only capture ② frozen-packet RR topology capture ③ frozen packet+topology
RR/ERCB 비교의 3단계로 분리한다.

v2도 세 번째 event에서 `140,149 vs 143,470`으로 갈렸다. Packet 내용만 같아도 wall-time에
따라 packet과 optimizer step의 교차 순서가 달라지기 때문이다. v3는 새로운 phase cutoff
없이 keyframe birth를 해당 causal packet에서 즉시 수행하고, reference topology 결정을
그때 기록된 packet count에 적용한다.
