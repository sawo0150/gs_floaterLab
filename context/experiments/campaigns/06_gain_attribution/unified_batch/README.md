# Unified mapping batch — window / KF / dense

2026-09-25 사용자 요청: window 학습과 추가 KF/dense 학습을 하나로 통합. 예시12 render/iter에서4 recent-window +4 full-KF ERVS +4 full-dense ERVS; 비율은 실험으로 비교한다.

## 구현/실험 계약

- 동일 integration worker에 `schedule=unified`를 추가한다. 하나의 arrival packet에 tracker/control event를 순서대로 담아 pose/depth·Gaussian birth를 반영하고 같은 dispatch에서 학습까지 처리한다. 별도 `_render_target` packet, native optimizer, idle 추가 학습은 사용하지 않는다.
- 한 batch에서 uniform recent KF / full-history KF cumulative ERVS / full-history dense cumulative ERVS를 혼합한다. batch 전체 UID 중복은 금지하고 window에서 뽑힌 KF도 동일 누적 count에 반영한다.
- 부족한 role의 자리는 사용 가능한 pool에 재배분한다. 전체 unique 영상 수가 작으면 batch를 줄인다. 40 renders/KF 마지막 잔여 예산은 작은 batch로 처리하고 동률 remainder 배분을 순환시킨다.
- KF RGBD+normal, dense RGB loss를 유지한다. 모든 pose 준비를 먼저 끝낸 뒤 각 영상의 loss gradient를 합산하고 Adam을 batch당1회 수행한다. LR clock은 완료 render 수이며 LR 배수 튜닝은 하지 않는다.
- densify/prune·topology gate·model scheduler OFF, 관측 birth/reset 유지. full pool·누적 count·기존 pose correction 유지.
- 비교: 이전 paired+densify/prune OFF 결과(`no_densify_prune/gpu40_v2`), 동일40 renders/KF, same causal tracker events/poses/held-out cohort, seed0. Adam 횟수는 grouping으로 달라지므로 반드시 보고한다.
- 사전 정의한12장 비율: 4:4:4, 6:3:3, 3:6:3, 3:3:6. 각 비율을 Aria1253/RPNG table_06/UTMM square-1 전부 평가한다. 장면별 다른 비율은 채택하지 않는다. 세 장면 평균 held-out PSNR과 mapper 시간을 함께 보고한다.
- 12장 grouping에서 품질 손실이 크면 동일 구조의6장(2:2:2),3장(1:1:1)을 후속 확인한다. 이는 iteration 수 감소의 영향을 점검하기 위한 사전 fallback이다.
- ratio 개발에 이 held-out cohort를 사용하므로 독립적인 최종 benchmark는 아니다. 실제 동시 tracking/live 성능·geometry/floater 개선도 별도 검증 전에는 주장하지 않는다.
- CPU: distinct·window membership·full-history 선택·window count 누적·취소·승격·부족 pool·잔여 budget·독립 audit corruption 검증. GPU: 한 arrival당 packet1개, native optimizer0, 모든 render backward, causal ledger와 cumulative count, topology OFF, zero-tail, saved map 평가2회 일치.

Runner: `benchmarks/online_gs/campaigns/gain_attribution/run_unified_batch_panel.py`

Results: `results/campaigns/gain_attribution/unified_batch/`

**2026-09-25 unified batch 444 / aria:** execution=True, audit=True, held-out PSNR=22.753850383612946; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/unified_batch/gpu40_v1/444/aria.

**2026-09-25 unified batch 444 / rpng:** execution=True, audit=True, held-out PSNR=23.73948145342303; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/unified_batch/gpu40_v1/444/rpng.

**2026-09-25 unified batch 444 / utmm:** execution=True, audit=True, held-out PSNR=19.89654070948377; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/unified_batch/gpu40_v1/444/utmm.

**2026-09-25 unified batch 633 / aria:** execution=True, audit=True, held-out PSNR=22.703423805819213; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/unified_batch/gpu40_v1/633/aria.

**2026-09-25 unified batch 633 / rpng:** execution=True, audit=True, held-out PSNR=23.506363653921866; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/unified_batch/gpu40_v1/633/rpng.

**2026-09-25 unified batch 633 / utmm:** execution=True, audit=True, held-out PSNR=19.758660684397192; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/unified_batch/gpu40_v1/633/utmm.

**2026-09-25 unified batch 363 / aria:** execution=True, audit=True, held-out PSNR=23.133291899702932; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/unified_batch/gpu40_v1/363/aria.

**2026-09-25 unified batch 363 / rpng:** execution=True, audit=True, held-out PSNR=23.79480908368085; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/unified_batch/gpu40_v1/363/rpng.

## 후속 원인 분리 계획 — packet 통합과 Adam grouping

사용자가 packet 통합 후 품질 저하 이유를 질문했다. 현재12장 batch는40 renders/KF는 유지하지만 Adam 횟수를 크게 줄인다(Aria3901→454). 따라서 동일12장 선택 구성·동일 role 비율·동일 누적 count·동일 render 예산을 유지하고, batch 안에서 Adam을 영상별로 실행하는 대조군을 추가한다. 입력 envelope는 계속 arrival당1개다.

이 비교에서는 선택 묶음 시작 시점의 LR을 묶음 내에서 유지해, 학습률 진행 방식을 추가로 바꾸지 않는다. 전체 UID/role 선택 순서도 대조군과 대조한다. window/KF/dense 비율은4:4:4와12장 panel에서 평균이 가장 좋은 다른 비율을 우선 확인한다. 서로 다른 optimizer grouping 결과를 혼합해 비율 우위를 주장하지 않는다. 작은6장/3장 묶음은 이 대조군에서도 품질이 회복되지 않거나 속도·품질 절충이 더 필요할 때 후속으로 확인한다.

**2026-09-25 unified batch 363 / utmm:** execution=True, audit=True, held-out PSNR=19.94246701252313; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/unified_batch/gpu40_v1/363/utmm.

**2026-09-25 unified batch 336 / aria:** execution=True, audit=True, held-out PSNR=23.067362428621482; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/unified_batch/gpu40_v1/336/aria.

**2026-09-25 unified batch 336 / rpng:** execution=True, audit=True, held-out PSNR=23.92392785012185; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/unified_batch/gpu40_v1/336/rpng.

**2026-09-25 unified batch 336 / utmm:** execution=True, audit=True, held-out PSNR=19.986103846703045; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/unified_batch/gpu40_v1/336/utmm.

**2026-09-25 unified batch 444m1 / aria:** execution=True, audit=True, held-out PSNR=24.47153246857738; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/unified_batch/optimizer1_v1/444m1/aria.

**2026-09-25 unified batch 444m1 / rpng:** execution=True, audit=True, held-out PSNR=25.27027747351844; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/unified_batch/optimizer1_v1/444m1/rpng.

**2026-09-25 unified batch 444m1 / utmm:** execution=True, audit=True, held-out PSNR=22.194252832436266; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/unified_batch/optimizer1_v1/444m1/utmm.

## Native 경로 후처리 점검

통합 경로의 `map()` early return은 native optimizer뿐 아니라 기존 함수 끝의 scale projection(`get_scaling.clamp(max=0.1)`)도 우회했다. 세 setup 모두 `mapping_preserve_dense_geometry_scale=False`, `mapping_replay_scale_projection=False`이므로 paired native 경로에서는 이 상한이 활성화되어 있었다. opacity reset 주기는2000000001이어서 이번 예산에서는 비활성이었다.

따라서 최초 ratio/optimizer 실험은 이 scale projection이 빠진 상태다. 동일 ratio의 묶음별/영상별 Adam은 둘 다 같은 상태이므로 grouping 비교는 유효하지만, paired 대비 차이는 이 후처리 누락도 포함한다. Aria 저장 지도 scale 진단은 `results/campaigns/gain_attribution/unified_batch/scale_projection_diagnostic.json`에 보존했다. paired 최대 scale0.153에 비해 unified12/1은10.946/10.050이었다. 이 수치는 opacity/가시성 영향을 보정한 geometry 지표가 아니다.

최종 채택 전 원래 상한을 관측 packet 반영 뒤, 통합 학습 앞에 복원하고 선택한 구성으로 세 장면을 재검증한다. densify/prune나 phase gate를 되살리는 변경은 아니다. 매 optimizer step마다 상한을 새로 강제하지 않고 tracker 이벤트 반영 경계에서 적용한다.

**2026-09-25 unified batch 336m1 / aria:** execution=True, audit=True, held-out PSNR=26.264144904740895; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/unified_batch/optimizer1_v1/336m1/aria.

**2026-09-25 unified batch 336m1 / rpng:** execution=True, audit=True, held-out PSNR=25.278631107227223; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/unified_batch/optimizer1_v1/336m1/rpng.

**2026-09-25 unified batch 336m1 / utmm:** execution=True, audit=True, held-out PSNR=22.398476506456916; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/unified_batch/optimizer1_v1/336m1/utmm.

**2026-09-25 unified batch 336m1p / aria:** execution=True, audit=True, held-out PSNR=25.59231961956461; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/unified_batch/projected_v1/336m1p/aria.

**2026-09-25 unified batch 336m1p / rpng:** execution=True, audit=True, held-out PSNR=25.117675599106796; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/unified_batch/projected_v1/336m1p/rpng.

**2026-09-25 unified batch 336m1p / utmm:** execution=True, audit=True, held-out PSNR=22.126344736711477; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/unified_batch/projected_v1/336m1p/utmm.

## 최종 결과 — 2026-09-26

**2026-09-26 unified mapping 최종 검증/기본값 반영:** arrival당 packet1개로 tracker/control 반영과 학습을 통합. native optimizer0·별도 추가학습 packet0, recent-window uniform + full-KF/full-dense 누적 ERVS로 구성. 12장 비율4종×3scene, 영상별 Adam2종×3scene, 기존 scale≤0.1 후처리 복원1종×3scene 총21run 검증. 같은 선택 순서·각 영상 LR에서 묶음별→영상별 Adam으로 품질 회복 확인. 최종3:3:6·영상별 Adam·densify/prune/phase gate OFF·기존 scale 상한 유지,40 renders/KF·seed0에서 Aria/RPNG/UTMM25.5923/25.1177/22.1263 dB. paired OFF25.0216/24.7836/21.7006 대비 +0.5707/+0.3341/+0.4257(평균+0.4435)dB; mapper50.68→52.64 /130.16→138.62 /51.53→55.47초(+4~8%). 모든 arm causal/prefix/cohort/count/one-packet/topology guard 및 저장지도 평가2회 PASS, 최종CPU16tests PASS. 최초 통합 경로가 빠뜨린 native scale projection은 복원해 최종검증했으며 상한 없는26.26dB는 진단 결과로만 유지. integration unified 기본값과 configs/online_mapping_unified.json 반영; paired 재현 경로 및 생산 트리 유지. ratio 탐색용3scene 단일seed이며 실제 동시tracking/live 및 geometry 개선 검증 아님.

[전체 수치](SUMMARY.md) · [실행 구조](IMPLEMENTATION.md). 최종 결과는 `results/campaigns/gain_attribution/unified_batch/projected_v1/`, 전체 비교는 `final_summary/`. `optimizer1_v1` 및 `gpu40_v1`은 원인 분리용 source/결과로 보존했다. 최종 projection은 native `map()` 호출 경계에 적용해 기존 후처리를 보존한다.
