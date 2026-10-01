# RR 대조군 구현

변경 파일: `/home/intern/VIGS-SLAM-online-worker-integration/vigs/unified_view_training.py`.
기존 selector=ervs 경로의 RNG 호출과 선택 수식은 유지하고 selector=rr을 opt-in으로 허용한다. Default preset은 변경하지 않는다.

## 공통 구조

Window / full KF / admitted dense quota는3:3:6. 전체 배치에서 UID 중복은 없으며 부족한 pool의 quota는 기존 로직으로 재분배한다. 영상별 Adam, LR 위치, growth credit과 native/RGB-only loss 분기는 변경하지 않는다. 도착한 KF와 이미 admission된 dense만 사용한다.

## RR 정의

KF와 dense에 각각 `remaining` queue와 현재 epoch의 `seen` 집합을 둔다. 아직 해당 epoch에서 사용하지 않은 새 영상은 shuffle 후 남은 queue 뒤에 append한다. Queue가 비면 현재 pool 전체를 shuffle하고 다음 epoch를 시작한다. 같은 selection batch에서 이미 사용한 UID는 queue에 남겨 다음 batch에서 선택할 수 있게 한다.

최근 window의 KF 학습도 KF epoch의 사용으로 센다. 따라서 window에서 사용한 UID가 현재 KF queue에 있으면 제거한다. 이는 ERVS가 window 학습을 cumulative count에 포함하는 것과 대응한다. 이 실험의 RR은 이처럼 고정 window 역할과 결합한 online RR이며, 전체 training set을 하나의 고정 offline epoch로 순회하는 구조는 아니다.

Reserve는 RR 상태 복사본으로 전체 batch를 계획한다. 각 영상까지의 RR 상태를 보관하고, commit_prefix 시 실제 완료한 prefix까지만 반영한다. 남은 batch를 cancel해도 이미 완료한 학습은 유지되고, 취소된 영상은 epoch에서 소모되지 않는다. 지도 generation이 바뀌면 새 sampler가 생성된다.

## 테스트 및 검증

CPU 테스트: 고정 pool의 매 epoch 완전 순회, newcomer의 현재 epoch 편입, reserve/cancel 무소모, 부분 commit 보존, window 사용 반영, 작은 pool의 epoch 전환과 배치 중복 방지, dense→KF promotion. 기존 growth/runtime/loss/blur/cumulative count 회귀테스트를 포함해 총35개.

GPU: 각 run에 기존 growth 실험의 causal-prefix/held-out/optimizer/loss-route/source-lock audit 적용. 양 arm 간 admission ledger와 pool membership, 역할 순서, batch size/token, LR render position까지 비교한다. 저장 지도는 동일 held-out evaluator로 두 번 평가한다(독립 학습 반복은 아님).
