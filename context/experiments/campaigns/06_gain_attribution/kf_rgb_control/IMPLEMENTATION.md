# KF RGB-only 대조군 구현

기본 구조는 변경하지 않는다. `auxiliary_mode=dense_rgb`가 계속 기본값이다.
실험 옵션은 `OnlineMapperRuntime → OnlinePhotometricTrainer → UnifiedTrainingSet`으로 전달된다.

| 모드 | 세 번째 slot pool | 실제 loss |
|---|---|---|
| dense_rgb | 도착한 전체 dense | 기존 dense RGB L1+SSIM |
| kf_native | 전체 KF | 기존 KF RGBD+normal 경로 |
| kf_rgb | 전체 KF | dense와 동일한 RGB L1+SSIM 함수 |

앞 두 slot은 recent KF window uniform / 전체 KF 누적 ERVS 그대로다. 세 번째 slot은 모두 누적 ERVS, 배치 전체에서 UID 중복은 허용하지 않는다. KF RGB-only도 KF의 기존 resident RGB와 online pose를 사용한다. `depth=None`로 KF 객체를 변조하지 않고 선택된 slot 역할로 loss를 분기하므로 같은 KF가 window/KF slot에 뽑히면 기존 geometric loss가 유지된다. RGB-only는 Gaussian parameter 일부를 freeze하는 것이 아니라 depth/normal supervision 없이 RGB loss를 역전파한다.

누적 선택 횟수는 역할별로 쪼개지 않는다. 동일 KF의 window/native/RGB-only 사용 모두 하나의 count에 더해진다. KF 두 대조군은 같은 RNG·후보·배치 경계·LR·counts를 유지한다. Loss가 pose/후보 선택에 피드백되는 경로는 이 frozen-tracker 실험에 없다. 맵 값은 loss에 따라 달라진다.

독립 audit는 실제 loss 함수 진입 로그를 완료된 render UID/slot 순서와 대조하고 KF 두 대조군의 전체 서비스 로그를 역할 이름만 정규화해 비교한다. causal prefix·held-out cohort·pose trajectory hash·Adam 횟수·scale projection·densify/prune OFF·zero-tail도 검사한다. dense 기본 arm은 이전 baseline과 선택 서비스 로그가 완전히 같아야 한다.

**해석 범위:** KF native와 KF RGB-only 비교는 전체 loss recipe 교체 효과다. native RGB에는 RGB mask/weight가 있고 dense RGB는 L1+SSIM이므로 이 차이를 depth/normal 항 제거 하나의 효과로 단정할 수 없다. depth와 normal 중 무엇이 원인인지는 이 실험만으로 분리하지 않는다. dense vs KF RGB-only는 추가 관측 경로(이미지·pose 포함) 비교이며 초기 KF pool 부족에 따른 배치/slot 구성 차이도 실제 count와 함께 보고한다.

CPU tests: 기존24 + 새3 = 27 PASS. 새 테스트는 초기 작은 pool부터 KF 두 조건의 UID/count/LR 일치, 실제 RGB-only loss/gradient dispatch, reset 시 mode 보존을 검증한다.

## Admission / entropy 설정 (실행 중 사용자 질의 확인)

현재 비교는 `membership=immediate`: 양쪽 도착 KF로 bracket되고 held-out이 아닌 적격 dense 후보를 모두 admit한다. `kappa=64`가 snapshot에 남지만 이 모드에서는 admission에 사용되지 않는다. 따라서 이 결과를 optimization-guided κ growth의 검증으로 인용하면 안 된다.

`tau=1.0`, `entropy_weight_policy=per_view`; 실제 unified sampler는 KF와 dense의 **각 pool별** N에 대해 tau_pool=1/N을 쓴다. weights = exp(-(n_i-min(n))/(tau_pool*(sum(n)+1))). 누적 count에는 window 사용도 포함되고 image당 optimizer step1회다. Scene/PSNR별 tau 튜닝은 없다. inherited `policy.effective_tau`는 합쳐진 KF+dense 크기를 사용하는 legacy 요약값이며 unified sampler의 실제 각 pool 가중치가 아니다. 실제 식과 pool_sizes로 해석해야 한다.
