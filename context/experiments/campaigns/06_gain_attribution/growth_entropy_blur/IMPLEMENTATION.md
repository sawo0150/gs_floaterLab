# κ / τ / blur 구현과 비교 범위

1. **입력 후보:** 기존 blur gate가 이미 도착한 KF interval의 RGB 선명도만 비교한다. energy ratio0.8와 high-frequency ratio0.9를 모두 밑도는 후보를 제외한다. Held-out은 gate/reference/admission/supervision에서 제외한다.
2. **Admission:** `UnifiedTrainingSet`이 `membership=growth`를 지원한다. 기존 `OnlineTrainingSet._admit()`를 재사용하며 `growth_budget_scope=dense_only`로 KF의 필수 등록과 분리한다. Generation마다 완료된 optimizer step κ회당 dense admission credit1개가 생긴다. 후보가 늦게 도착하면 이미 얻은 credit을 사용할 수 있다. Promotion은 credit을 환불하지 않는다. 도착한 후보 중 현재 시간축 coverage의 가장 큰 빈 곳부터 채운다.
3. **학습 몫:** recent KF window / full KF pool / admitted dense pool =3:3:6. 작은 초기 pool에서는 distinct UID 조건을 지키면서 부족한 자리를 다른 활성 pool로 채운다. 따라서 κ를 바꾸면 초기 실제 slot 비율과 batch 경계도 조금 달라질 수 있다. 총/prefix 렌더링 수와 Adam 수는 동일하다.
4. **ERVS:** KF/dense의 각 pool에서 `tau_pool=tau/N`; `p_i ∝ exp(-n_i/[tau_pool*(sum(n)+1)])`. Count는 현재 지도 generation의 모든 완료된 사용을 누적하고 KF window 사용도 포함한다. tau가 작을수록 적게 선택된 이미지에 더 강하게 치우친다. 공유 tau를 KF/dense 양쪽에 적용한다. Scene별 조정/최근 구간 count/잔여 sequence 길이 사용 없음.
5. **Optimizer:** 영상별 Adam1회, 기존 선택 batch 내 LR 유지 방식 그대로. κ는 optimizer step 단위이며 이 실험에서는 render 단위와 같다. Image별 native/dense loss와 scale projection은 그대로; densify/prune/phase gateOFF. Geometry/floater 개선을 검증하는 실험은 아니다.
6. **배선:** worker runner의 `--kappa`, `--tau`, `--growth-budget-scope` → OnlineMapperRuntime → OnlinePhotometricTrainer → UnifiedTrainingSet/OnlineTrainingSet. Sampler support에 더해 runtime의 full-pool guard도 paired schedule에만 적용하도록 수정했다. Actual separate-pool entropy weights는 `policy.sampler_pool_tau`로 기록한다. Legacy `effective_tau`는 combined pool 요약이라 unified sampling 해석에는 사용하지 않는다.
7. **검증:** growth credit은 reserve/cancel로 증가하지 않고 완료된 commit에서만 증가한다. 새 CPU tests와 runtime wiring regression으로 검증했다. 각 GPU run은 admissions의 step threshold, actual loss route, cumulative count, causal prefixes, poses/events/cohort, zero-tail, source lock, blur rejection을 독립 audit하고 저장 지도를 두 번 평가한다.

실험은 frozen causal tracker + 고정 렌더링 수 비교다. Mapping 시간에는 dense pose/input 처리비가 포함되지만 실제 tracking 동시 실행을 검증하지 않았다. 세 개발 장면 seed0의 coarse staged search이며 모든 κ×τ 조합을 탐색한 global optimum이 아니다. 장면별 0.05dB 하락 허용치와 near-tie0.02dB는 사전 선언한 공학적 선택 규칙이며 통계적 유의성 구간이 아니다.
