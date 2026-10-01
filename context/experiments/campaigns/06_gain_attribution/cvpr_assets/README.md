# CVPR 실제 figure/table 데이터 수집

2026-10-01 시작. 에이전트 분담 없이 직접 수행한다.

## 목표와 source

- `paper/plan/visual_assets/dataset_registry.md`의 20개 후보를 보존한다. 전체 후보에 대한 실행/실패/미실행 상태를 기록한 뒤 대표 그림을 선택한다.
- VIGS-SLAM-custom main은 geometry commit `8c840d41`의 후속 버전이며 현재 HEAD와 실제 Python/CUDA source hash를 실행별 기록한다.
- official vanilla는 `22ffe24` checkout의 mapper를 사용한다. mapper 학습에는 동일 causal tracker archive와 held-out 제외 규칙을 적용한다.
- 기본 mapper 코드 수정은 피하고 별도 runner, 설정, 측정 observer로 실행한다.

## 비교

1. 학습 렌더 예산: 15/40 renders per KF. D3의 보조 proxy 렌더는 별도 계측하며 동일 총 렌더 비용이라고 표기하지 않는다.
2. 실제 tracker 동시 실행: 센서 구간의 1/1.5배 시간을 허용하는 FIFO, 대기 packet만 제거하고 학습 history는 유지한다. 종료 뒤 optimizer tail은 0회다. tracking 초과 시간도 기록한다.
3. ERVS/RR, KF-only/dense, geometry off/on은 원래 sampler와 최신 online implementation을 구분하여 비교한다.
4. 수렴 곡선에는 중간 지도 checkpoint의 실제 held-out 평가가 필요하다. 끝점 간 가짜 보간으로 수렴 성능을 주장하지 않는다.
5. 기하 수치는 독립적인 GT/region 계약이 검증된 경우에만 쓴다.

## 출력

- 원본/측정: `results/campaigns/gain_attribution/cvpr_assets/`
- runner: `benchmarks/online_gs/campaigns/gain_attribution/collect_cvpr_assets.py` 및 이 campaign의 후속 runner
- 최종 자산: `paper/figures/`와 `paper/tables/` 기존 각 폴더
- teaser/overview만 전체 너비. 나머지 figure/table은 본문과 appendix 모두 한 단 너비.

## 진행 기록

- 2026-10-01: TeX만 사용해 한 단 배치 PDF를 재빌드했다. 입력 asset은 재생성하지 않았다. 측정 수집은 strict fixed held-out cohort를 사용하고 native / D3 / live FIFO를 분리한다.

- 2026-10-01 CVPR aria/aria1253 15renders/KF d3: status=passed, PSNR=23.46339702606201; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/pilot_v1/render15/aria/aria1253/d3

- 2026-10-01 CVPR aria/aria1253 15renders/KF vanilla: status=passed, PSNR=19.023149574075948; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/pilot_v1/render15/aria/aria1253/vanilla

- 2026-10-01 CVPR rpng/table_01 15renders/KF d3: status=passed, PSNR=24.407874449315774; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render15/rpng/table_01/d3

- 2026-10-01 CVPR rpng/table_01 15renders/KF vanilla: status=passed, PSNR=21.345150768994333; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render15/rpng/table_01/vanilla

- 2026-10-01 CVPR rpng/table_01 40renders/KF d3: status=passed, PSNR=25.7536418618434; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render40/rpng/table_01/d3

- 2026-10-01 CVPR rpng/table_01 40renders/KF vanilla: status=passed, PSNR=22.743234839572374; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render40/rpng/table_01/vanilla

- 2026-10-01 CVPR rpng/table_02 15renders/KF d3: status=passed, PSNR=21.446611975970335; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render15/rpng/table_02/d3

- 2026-10-01 CVPR rpng/table_02 15renders/KF vanilla: status=passed, PSNR=19.18900990486145; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render15/rpng/table_02/vanilla

- 2026-10-01 CVPR rpng/table_02 40renders/KF d3: status=passed, PSNR=24.167826538216577; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render40/rpng/table_02/d3

- 2026-10-01 CVPR rpng/table_02 40renders/KF vanilla: status=passed, PSNR=20.073584814594216; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render40/rpng/table_02/vanilla

- 2026-10-01 CVPR rpng/table_03 15renders/KF d3: status=passed, PSNR=23.397692402827417; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render15/rpng/table_03/d3

- 2026-10-01 CVPR rpng/table_03 15renders/KF vanilla: status=passed, PSNR=20.04718496183866; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render15/rpng/table_03/vanilla

- 2026-10-01 CVPR rpng/table_03 40renders/KF d3: status=passed, PSNR=24.990276752967127; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render40/rpng/table_03/d3

- 2026-10-01 CVPR rpng/table_03 40renders/KF vanilla: status=passed, PSNR=20.682447953162963; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render40/rpng/table_03/vanilla

- 2026-10-01 CVPR rpng/table_04 15renders/KF d3: status=passed, PSNR=21.60679450329439; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render15/rpng/table_04/d3

- 2026-10-01: Aria 15-render pilot는 ours 23.4634/vanilla 19.0231 dB, 양쪽 1785 training renders, 동일 trajectory/prefix/cohort와 double held-out 평가 통과. 전체 fixed-work panel에서 RPNG table_01/02/03의 15/40 비교 12회도 통과했다. 현재 table_04 진행 중. 각 실행 결과와 실패는 이 문서 및 INDEX/STATUS에 자동 기록한다.
- 2026-10-01: T1/T2 본문·부록은 실제 측정 CSV로 생성하며 paired coverage를 명시한다. F12는 기존 4 scenes의 16개 live run 실제 측정으로 교체했다. 나머지 mockup은 아직 실제 결과가 아니며 전체 측정·scene 선정 뒤 교체한다.
- 2026-10-01: 새 live adapter는 원래 측정 파일/production source를 바꾸지 않고 scene 경로와 shared official Tracking config만 AST로 교체한다. CPU anchor/compile 확인만 완료, GPU live 검증은 아직 안 했다. snapshot timing과 Tracking config 양쪽 일치 여부를 실행 후 확인할 예정이다.
- 2026-10-01: aria301_12F raw 2193장·IMU·고정 calibration 확인, 독립 held-out 440장을 실행 전 선언했다. official tracker archive capture 명령을 준비했으며 현재 fixed-work GPU batch와 겹치지 않게 뒤에 실행한다.

- 2026-10-01 CVPR rpng/table_04 15renders/KF vanilla: status=passed, PSNR=20.002419714280116; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render15/rpng/table_04/vanilla

- 2026-10-01 CVPR rpng/table_04 40renders/KF d3: status=passed, PSNR=23.145880527260864; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render40/rpng/table_04/d3

- 2026-10-01 CVPR rpng/table_04 40renders/KF vanilla: status=passed, PSNR=20.809272621688528; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render40/rpng/table_04/vanilla

- 2026-10-01 CVPR rpng/table_05 15renders/KF d3: status=passed, PSNR=22.14680972091576; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render15/rpng/table_05/d3

- 2026-10-01 CVPR rpng/table_05 15renders/KF vanilla: status=passed, PSNR=19.83612312180876; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render15/rpng/table_05/vanilla

- 2026-10-01 CVPR rpng/table_05 40renders/KF d3: status=passed, PSNR=23.31833450063894; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render40/rpng/table_05/d3

- 2026-10-01 CVPR rpng/table_05 40renders/KF vanilla: status=passed, PSNR=20.942781929065575; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render40/rpng/table_05/vanilla

- 2026-10-01 CVPR rpng/table_06 15renders/KF d3: status=passed, PSNR=23.865029927846546; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render15/rpng/table_06/d3

- 2026-10-01 CVPR rpng/table_06 15renders/KF vanilla: status=passed, PSNR=20.698803021886327; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render15/rpng/table_06/vanilla

- 2026-10-01 CVPR rpng/table_06 40renders/KF d3: status=passed, PSNR=25.12607385790026; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render40/rpng/table_06/d3

- 2026-10-01 CVPR rpng/table_06 40renders/KF vanilla: status=passed, PSNR=22.56127199396357; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render40/rpng/table_06/vanilla

- 2026-10-01 CVPR rpng/table_07 15renders/KF d3: status=passed, PSNR=25.496817031334736; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render15/rpng/table_07/d3

- 2026-10-01 CVPR rpng/table_07 15renders/KF vanilla: status=passed, PSNR=22.01145080335454; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render15/rpng/table_07/vanilla

- 2026-10-01 CVPR rpng/table_07 40renders/KF d3: status=passed, PSNR=27.549992338351764; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render40/rpng/table_07/d3

- 2026-10-01 CVPR rpng/table_07 40renders/KF vanilla: status=passed, PSNR=24.011500866278727; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render40/rpng/table_07/vanilla

- 2026-10-01 CVPR aria/aria1253 regionrenders/KF d3: status=evaluated, PSNR=25.749060383279815; results/campaigns/gain_attribution/cvpr_assets/collection_v1/aria_manual_region40_v1.json

- 2026-10-01 CVPR aria/aria1253 regionrenders/KF vanilla: status=evaluated, PSNR=20.872029646662355; results/campaigns/gain_attribution/cvpr_assets/collection_v1/aria_manual_region40_v1.json

- 2026-10-01 CVPR aria/aria1253 regionrenders/KF d3: status=evaluated, PSNR=23.46339702606201; results/campaigns/gain_attribution/cvpr_assets/collection_v1/aria_manual_region15_v1.json

- 2026-10-01 CVPR aria/aria1253 regionrenders/KF vanilla: status=evaluated, PSNR=19.023149574075948; results/campaigns/gain_attribution/cvpr_assets/collection_v1/aria_manual_region15_v1.json

- 2026-10-01 CVPR rpng/table_08 15renders/KF d3: status=passed, PSNR=24.521692992660828; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render15/rpng/table_08/d3

- 2026-10-01 CVPR rpng/table_08 15renders/KF vanilla: status=passed, PSNR=21.47925835868916; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render15/rpng/table_08/vanilla

- 2026-10-01: 수작업 Aria1253 free-space mask/ORB pose를 exp70 archive에서 발견하고 원본 SHA와 timestamp를 검증했다. 독립 region 진단 15/40 두 예산·두 시스템 총4개를 실행해 T3/CSV에 반영했다. 학습 입력에는 사용하지 않았으며 dense surface accuracy/completeness/F-score는 NA다. 40-render nominal opacity>0.3 count는 vanilla416/ours153; erosion/dilation sensitivity와 shared registration median/p90=2.42/3.84cm도 함께 기록했다.

- 2026-10-01: TeX flafter와 float-page top alignment를 적용해 appendix 설명 뒤에 표가 나오도록 수정했다. 측정 CSV52개 exact metric/SHA 대조, production source hash unchanged, snapshot 좌표/SH export CPU4 tests 통과. 새 live runner는 scene별 setup과 stream clock origin을 읽기용 AST adapter로 기록한다; 새 GPU live 실행은 아직 대기 중이다.

- 2026-10-01: current merged mapper의 RR/dense-vs-KF RGB 및 native-geometry 대조 runner를 준비했다. 기본 source/preset은 수정하지 않았고 15/40 prefix render·trajectory·held-out cohort를 검증하도록 했다. native-vs-D3는 별도 geometry recipe 비교이며 isolated loss ablation으로 부르지 않는다.

- 2026-10-01 CVPR rpng/table_08 40renders/KF d3: status=passed, PSNR=24.87198794267203; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render40/rpng/table_08/d3

- 2026-10-01 CVPR rpng/table_08 40renders/KF vanilla: status=passed, PSNR=21.88165073709297; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render40/rpng/table_08/vanilla

- 2026-10-01 CVPR utmm/ego-centric-1 15renders/KF d3: status=passed, PSNR=20.653921477206342; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render15/utmm/ego-centric-1/d3

- 2026-10-01 CVPR utmm/ego-centric-1 15renders/KF vanilla: status=passed, PSNR=14.564862241992703; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render15/utmm/ego-centric-1/vanilla

- 2026-10-01 CVPR utmm/ego-centric-1 40renders/KF d3: status=passed, PSNR=20.153859510050193; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render40/utmm/ego-centric-1/d3

- 2026-10-01: RPNG 8/8 sequence의 15/40 두 예산·두 시스템 총32 run 완료, 모두 실행/audit/double held-out eval 통과. Mean PSNR ours/vanilla=23.3612/20.5762 at15,24.8655/21.7132 at40. 본문40/부록15·40표에 실제8-scene 평균 반영. UTMM/Aria 전체 fresh panel은 계속 진행 중이다.

- 2026-10-01: F11의 dummy를 기존 actual-tracker 16 run(4 scenes×2 allowances×2 systems)의 실제 endpoint 평균으로 교체했다. 각 점은 독립 실행의 최종 품질/committed renders이며 within-run convergence가 아니다. 공통 Tracking config의 신규 pilot과 실제 checkpoint wall-clock 곡선은 아직 미완료.

- 2026-10-01: GPU serial pipeline PID1121893/session6728은 기존 fixed-work PID1070380/session14222의 실제 종료를 기다린 뒤12F capture/fixed-work→Aria snapshot evaluator pilot→shared Tracking Aria1253/table01 live pilot을 실행하도록 대기 중이다. 아직 새 GPU stage를 시작한 것은 아니며 production code hash는 변하지 않았다.

- 2026-10-01 CVPR utmm/ego-centric-1 40renders/KF vanilla: status=passed, PSNR=16.759209010508155; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render40/utmm/ego-centric-1/vanilla

- 2026-10-01 CVPR utmm/ego-centric-2 15renders/KF d3: status=passed, PSNR=19.130685996278494; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render15/utmm/ego-centric-2/d3

- 2026-10-01 CVPR utmm/ego-centric-2 15renders/KF vanilla: status=passed, PSNR=16.139085963311324; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render15/utmm/ego-centric-2/vanilla

- 2026-10-01 CVPR utmm/ego-centric-2 40renders/KF d3: status=passed, PSNR=19.55067374423089; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render40/utmm/ego-centric-2/d3

- 2026-10-01 CVPR utmm/ego-centric-2 40renders/KF vanilla: status=passed, PSNR=18.08685510642684; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render40/utmm/ego-centric-2/vanilla

- 2026-10-01 CVPR utmm/ego-drive 15renders/KF d3: status=passed, PSNR=20.772115279771256; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render15/utmm/ego-drive/d3

- 2026-10-01 CVPR utmm/ego-drive 15renders/KF vanilla: status=passed, PSNR=17.366720756177802; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render15/utmm/ego-drive/vanilla

- 2026-10-01 CVPR utmm/ego-drive 40renders/KF d3: status=passed, PSNR=21.516879920009192; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render40/utmm/ego-drive/d3

- 2026-10-01: 후속 pipeline의 단계 성공판정을 강화해 첫 대기-only coordinator를 GPU stage 시작 전 종료하고 v2(PID1128231, session65350)로 교체했다. fixed_work primary(session14222)는 중단하지 않았다. capture/4 fixed-work run/8 live pilot 및 checkpoint 실제 metric 존재 여부로 stage를 판정한다.

- 2026-10-01: T6은 긴8-column header 대신 dataset group+7개 짧은 metric header로 한 단 가독성을 개선했다. 실제 aligned checkpoint가 양쪽2개 이상 평가되어야 peak crossing을 채우며 현재0/20 measured로 유지한다. T1full-cohort PSNR과 곡선의 fixed64subset PSNR을 혼용하지 않는다.

- 2026-10-01 CVPR utmm/ego-drive 40renders/KF vanilla: status=passed, PSNR=18.83111600434653; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render40/utmm/ego-drive/vanilla

- 2026-10-01 CVPR utmm/fast-straight 15renders/KF d3: status=passed, PSNR=17.02004697743584; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render15/utmm/fast-straight/d3

- 2026-10-01 CVPR utmm/fast-straight 15renders/KF vanilla: status=passed, PSNR=14.058433939428891; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render15/utmm/fast-straight/vanilla

- 2026-10-01 CVPR utmm/fast-straight 40renders/KF d3: status=passed, PSNR=18.735907512552597; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render40/utmm/fast-straight/d3

- 2026-10-01 CVPR utmm/fast-straight 40renders/KF vanilla: status=passed, PSNR=15.550470758886899; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render40/utmm/fast-straight/vanilla

- 2026-10-01 CVPR utmm/slow-straight-1 15renders/KF d3: status=passed, PSNR=15.127045559883118; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render15/utmm/slow-straight-1/d3

- 2026-10-01 CVPR utmm/slow-straight-1 15renders/KF vanilla: status=passed, PSNR=12.621661043167114; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render15/utmm/slow-straight-1/vanilla

- 2026-10-01 CVPR utmm/slow-straight-1 40renders/KF d3: status=passed, PSNR=16.95625534057617; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render40/utmm/slow-straight-1/d3

- 2026-10-01 CVPR utmm/slow-straight-1 40renders/KF vanilla: status=passed, PSNR=13.546598517894745; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render40/utmm/slow-straight-1/vanilla

- 2026-10-01 CVPR utmm/slow-straight-2 15renders/KF d3: status=passed, PSNR=20.954066347484748; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render15/utmm/slow-straight-2/d3

- 2026-10-01 CVPR utmm/slow-straight-2 15renders/KF vanilla: status=passed, PSNR=16.816587519054572; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render15/utmm/slow-straight-2/vanilla

- 2026-10-01 CVPR utmm/slow-straight-2 40renders/KF d3: status=passed, PSNR=22.77454875126358; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render40/utmm/slow-straight-2/d3

- 2026-10-01 CVPR utmm/slow-straight-2 40renders/KF vanilla: status=passed, PSNR=15.12111733964652; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render40/utmm/slow-straight-2/vanilla

- 2026-10-01 CVPR utmm/square-1 15renders/KF d3: status=passed, PSNR=20.965688475856073; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render15/utmm/square-1/d3

- 2026-10-01 CVPR utmm/square-1 15renders/KF vanilla: status=passed, PSNR=15.860937889711357; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render15/utmm/square-1/vanilla

- 2026-10-01 CVPR utmm/square-1 40renders/KF d3: status=passed, PSNR=22.100768560244713; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render40/utmm/square-1/d3

- 2026-10-01 CVPR utmm/square-1 40renders/KF vanilla: status=passed, PSNR=18.79899032027633; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render40/utmm/square-1/vanilla

- 2026-10-01 CVPR utmm/square-2 15renders/KF d3: status=passed, PSNR=21.19905044399962; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render15/utmm/square-2/d3

- 2026-10-01 CVPR utmm/square-2 15renders/KF vanilla: status=passed, PSNR=16.45605817911576; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render15/utmm/square-2/vanilla

- 2026-10-01 CVPR utmm/square-2 40renders/KF d3: status=passed, PSNR=22.23544576216717; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render40/utmm/square-2/d3

- 2026-10-01 CVPR utmm/square-2 40renders/KF vanilla: status=passed, PSNR=18.786255019051687; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render40/utmm/square-2/vanilla

- 2026-10-01 CVPR aria/aria1253 15renders/KF d3: status=passed, PSNR=23.479717014400105; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render15/aria/aria1253/d3

- 2026-10-01 CVPR aria/aria1253 15renders/KF vanilla: status=passed, PSNR=19.01287403907485; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render15/aria/aria1253/vanilla

- 2026-10-01 CVPR aria/aria1253 40renders/KF d3: status=passed, PSNR=25.747064095417052; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render40/aria/aria1253/d3

- 2026-10-01 CVPR snapshot CPU audit: 332 immutable states checked, 324 satisfy shared pose-alignment limits, 8 do not; held-out exclusion passed for all332. This is readiness for post-run evaluation, not map-quality validation. Result: results/campaigns/gain_attribution/cvpr_assets/checkpoint_alignment_v1.json.

- 2026-10-01 CVPR aria/aria1253 40renders/KF vanilla: status=passed, PSNR=20.62817724606463; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render40/aria/aria1253/vanilla

- 2026-10-01 CVPR aria/aria1253rot 15renders/KF d3: status=passed, PSNR=23.803835471731716; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render15/aria/aria1253rot/d3

- 2026-10-01 CVPR aria/aria1253rot 15renders/KF vanilla: status=passed, PSNR=20.373812591052445; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render15/aria/aria1253rot/vanilla

- 2026-10-01 CVPR aria/aria1253rot 40renders/KF d3: status=passed, PSNR=24.998510898527552; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render40/aria/aria1253rot/d3

- 2026-10-01 CVPR aria/aria1253rot 40renders/KF vanilla: status=passed, PSNR=21.83502317960145; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render40/aria/aria1253rot/vanilla

- 2026-10-01 CVPR aria/aria1253 regionrenders/KF d3: status=evaluated, PSNR=23.479717014400105; results/campaigns/gain_attribution/cvpr_assets/collection_v1/aria_manual_region15_v2.json

- 2026-10-01 CVPR aria/aria1253 regionrenders/KF vanilla: status=evaluated, PSNR=19.01287403907485; results/campaigns/gain_attribution/cvpr_assets/collection_v1/aria_manual_region15_v2.json

- 2026-10-01 CVPR aria/aria1253 regionrenders/KF d3: status=evaluated, PSNR=25.747064095417052; results/campaigns/gain_attribution/cvpr_assets/collection_v1/aria_manual_region40_v2.json

- 2026-10-01 CVPR aria/aria1253 regionrenders/KF vanilla: status=evaluated, PSNR=20.62817724606463; results/campaigns/gain_attribution/cvpr_assets/collection_v1/aria_manual_region40_v2.json

- 2026-10-01 CVPR aria/aria301_305 15renders/KF d3: status=passed, PSNR=23.474117611688673; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render15/aria/aria301_305/d3

- 2026-10-01 CVPR aria/aria301_305 15renders/KF vanilla: status=passed, PSNR=19.008593502646253; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render15/aria/aria301_305/vanilla

- 2026-10-01 CVPR aria/aria301_305 40renders/KF d3: status=passed, PSNR=24.840737277368888; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render40/aria/aria301_305/d3

- 2026-10-01 CVPR aria/aria301_305 40renders/KF vanilla: status=passed, PSNR=20.71910099638194; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_v1/render40/aria/aria301_305/vanilla

- 2026-10-01 CVPR cvpr/capture_12f measurement_stagerenders/KF pipeline: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/pipeline_v2/capture_12f.log

- 2026-10-01 CVPR aria/aria301_12F 15renders/KF d3: status=passed, PSNR=25.69641070365906; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_12f_v1/render15/aria/aria301_12F/d3

- 2026-10-01 CVPR aria/aria301_12F 15renders/KF vanilla: status=passed, PSNR=22.064716050841593; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_12f_v1/render15/aria/aria301_12F/vanilla

- 2026-10-01 CVPR aria/aria1253_region_checkpoints 40renders/KF d3_vs_vanilla: status=evaluated, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/collection_v1/aria_manual_region_curve40_v1.json

- 2026-10-01 CVPR aria/aria1253_region_checkpoints 40renders/KF d3_vs_vanilla: status=evaluated, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/collection_v1/aria_manual_region_curve40_v2.json

- 2026-10-01 CVPR aria/aria301_12F 40renders/KF d3: status=passed, PSNR=27.450468639893966; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_12f_v1/render40/aria/aria301_12F/d3

- 2026-10-01 CVPR aria/aria301_12F 40renders/KF vanilla: status=passed, PSNR=24.271544135700573; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/fixed_work_12f_v1/render40/aria/aria301_12F/vanilla

- 2026-10-01 CVPR cvpr/fixed_work_12f measurement_stagerenders/KF pipeline: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/pipeline_v2/fixed_work_12f.log

- 2026-10-01 CVPR cvpr/pilot_checkpoint_d3 measurement_stagerenders/KF pipeline: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/pipeline_v2/pilot_checkpoint_d3.log

- 2026-10-01 CVPR cvpr/pilot_checkpoint_vanilla measurement_stagerenders/KF pipeline: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/pipeline_v2/pilot_checkpoint_vanilla.log

- 2026-10-01 CVPR rpng/table_01 40renders/KF live_ours_1x: status=passed, PSNR=23.667279053494276; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/live_shared_tracking_v1/scale1/rpng/table_01/ours

- 2026-10-01 CVPR rpng/table_01 40renders/KF live_vanilla_1x: status=passed, PSNR=22.444745099876982; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/live_shared_tracking_v1/scale1/rpng/table_01/vanilla

- 2026-10-01 CVPR rpng/table_01 40renders/KF live_ours_1.5x: status=passed, PSNR=25.358613965995758; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/live_shared_tracking_v1/scale1p5/rpng/table_01/ours

- 2026-10-01: 전체20개 후보의15/40 renders/KF×D3/official vanilla 총80 run이 실행/audit/double held-out 평가를 통과했다. T1본문·전체sequence appendix는 같은96-record CSV(80 fixed+16 이전 live)에서 생성하고 각metric SHA/PSNR/disjoint를 원본과 대조했다. 40예산 dataset평균gain: RPNG+3.1523, UTMM+3.5679, Aria+3.8961dB. Production source106개 파일은 변경되지 않았다.
- 2026-10-01: 최신 Aria1253 map의독립region 진단v2는40예산 opacity>0.3 center count vanilla414/ours150이다. F6은 실제PLY covariance의opaque2σ ellipsoid 공통시점/cut/opacity. 색은수작업empty-space membership이며 photometric RGB가 아니다. F7은14실제중간지도, 첫공통camera frusta고정region(71.8%)에서support mass와전체Gaussian수를함께표시한다. 지표는단조감소하지 않으며 surface completeness/isolated D3 ablation을주장하지 않는다.
- 2026-10-01: checkpoint CPU evaluator의초기결과저장 sha인자가 str이라 AttributeError로중단되었다. Path로수정한후v1/full-mask와v2/fixed-initial-region 각각14상태 모두평가완료, 최종지표는T3의원본metric과일치했다. 실패를성공으로간주하지 않았다.
- 2026-10-01: UTMM원본depth PNG도발견했으나RGB660×1280/depth420×848이고color-depth extrinsic/registration이아직검증되지 않았다. 정합없이dense geometry GT로사용하지 않는다. Aria수작업empty-space metric과표면정확도는분리한다.
- 2026-10-01: GPU후속전체측정coordinator PID1157571/session76672는현재실제진행중인pilot pipeline PID1128231/session65350이끝난뒤실제checkpoint(전체15/40),current RR/KF-source/native-geometry controls,공통Tracking fullcohort를순차실행하도록대기한다. Pilot checkpoint D3/vanilla는실제7상태씩모두평가통과했고,shared tracker pilot은진행중이다.

- 2026-10-01 CVPR rpng/table_01 40renders/KF live_vanilla_1.5x: status=passed, PSNR=22.95078182030484; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/live_shared_tracking_v1/scale1p5/rpng/table_01/vanilla

- 2026-10-01 CVPR aria/aria1253 40renders/KF live_ours_1x: status=passed, PSNR=23.428837302986903; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/live_shared_tracking_v1/scale1/aria/aria1253/ours

- 2026-10-01 CVPR aria/aria1253 40renders/KF live_vanilla_1x: status=passed, PSNR=20.122959835838724; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/live_shared_tracking_v1/scale1/aria/aria1253/vanilla

- 2026-10-01 CVPR aria/aria1253 40renders/KF live_ours_1.5x: status=passed, PSNR=25.751155314554694; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/live_shared_tracking_v1/scale1p5/aria/aria1253/ours

- 2026-10-01 CVPR aria/aria1253 40renders/KF live_vanilla_1.5x: status=passed, PSNR=20.92910993372211; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/live_shared_tracking_v1/scale1p5/aria/aria1253/vanilla

- 2026-10-01 CVPR cvpr/shared_tracking_pilot measurement_stagerenders/KF pipeline: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/pipeline_v2/shared_tracking_pilot.log

- 2026-10-01 CVPR cvpr/curve_rpng_table_01_15_d3 full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_rpng_table_01_15_d3.log

- 2026-10-01 CVPR cvpr/curve_rpng_table_01_15_vanilla full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_rpng_table_01_15_vanilla.log

- 2026-10-01 CVPR cvpr/curve_rpng_table_01_40_d3 full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_rpng_table_01_40_d3.log

- 2026-10-01 CVPR cvpr/curve_rpng_table_01_40_vanilla full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_rpng_table_01_40_vanilla.log

- 2026-10-01 CVPR cvpr/curve_rpng_table_02_15_d3 full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_rpng_table_02_15_d3.log

- 2026-10-01 CVPR cvpr/curve_rpng_table_02_15_vanilla full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_rpng_table_02_15_vanilla.log

- 2026-10-01 CVPR cvpr/curve_rpng_table_02_40_d3 full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_rpng_table_02_40_d3.log

- 2026-10-01 CVPR cvpr/curve_rpng_table_02_40_vanilla full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_rpng_table_02_40_vanilla.log

- 2026-10-01 CVPR cvpr/curve_rpng_table_03_15_d3 full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_rpng_table_03_15_d3.log

- 2026-10-01 CVPR cvpr/curve_rpng_table_03_15_vanilla full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_rpng_table_03_15_vanilla.log

- 2026-10-01 CVPR cvpr/curve_rpng_table_03_40_d3 full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_rpng_table_03_40_d3.log

- 2026-10-01 CVPR cvpr/curve_rpng_table_03_40_vanilla full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_rpng_table_03_40_vanilla.log

- 2026-10-01 CVPR cvpr/curve_rpng_table_04_15_d3 full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_rpng_table_04_15_d3.log

- 2026-10-01 CVPR cvpr/curve_rpng_table_04_15_vanilla full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_rpng_table_04_15_vanilla.log

- 2026-10-01 CVPR cvpr/curve_rpng_table_04_40_d3 full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_rpng_table_04_40_d3.log

- 2026-10-01 CVPR cvpr/curve_rpng_table_04_40_vanilla full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_rpng_table_04_40_vanilla.log

- 2026-10-01 CVPR cvpr/curve_rpng_table_05_15_d3 full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_rpng_table_05_15_d3.log

- 2026-10-01 CVPR cvpr/curve_rpng_table_05_15_vanilla full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_rpng_table_05_15_vanilla.log

- 2026-10-01 CVPR cvpr/curve_rpng_table_05_40_d3 full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_rpng_table_05_40_d3.log

- 2026-10-01 CVPR cvpr/curve_rpng_table_05_40_vanilla full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_rpng_table_05_40_vanilla.log

- 2026-10-01 CVPR cvpr/curve_rpng_table_06_15_d3 full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_rpng_table_06_15_d3.log

- 2026-10-01 CVPR cvpr/curve_rpng_table_06_15_vanilla full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_rpng_table_06_15_vanilla.log

- 2026-10-01 CVPR cvpr/curve_rpng_table_06_40_d3 full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_rpng_table_06_40_d3.log

- 2026-10-01 CVPR cvpr/curve_rpng_table_06_40_vanilla full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_rpng_table_06_40_vanilla.log

- 2026-10-01 CVPR cvpr/curve_rpng_table_07_15_d3 full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_rpng_table_07_15_d3.log

- 2026-10-01 CVPR cvpr/curve_rpng_table_07_15_vanilla full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_rpng_table_07_15_vanilla.log

- 2026-10-01 CVPR cvpr/curve_rpng_table_07_40_d3 full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_rpng_table_07_40_d3.log

- 2026-10-01 CVPR cvpr/curve_rpng_table_07_40_vanilla full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_rpng_table_07_40_vanilla.log

- 2026-10-01 CVPR cvpr/curve_rpng_table_08_15_d3 full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_rpng_table_08_15_d3.log

- 2026-10-01 CVPR cvpr/curve_rpng_table_08_15_vanilla full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_rpng_table_08_15_vanilla.log

- 2026-10-01 CVPR cvpr/curve_rpng_table_08_40_d3 full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_rpng_table_08_40_d3.log

- 2026-10-01 CVPR cvpr/curve_rpng_table_08_40_vanilla full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_rpng_table_08_40_vanilla.log

- 2026-10-01 CVPR cvpr/curve_utmm_ego-centric-1_15_d3 full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_utmm_ego-centric-1_15_d3.log

- 2026-10-01 CVPR cvpr/curve_utmm_ego-centric-1_15_vanilla full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_utmm_ego-centric-1_15_vanilla.log

- 2026-10-01 CVPR cvpr/curve_utmm_ego-centric-1_40_d3 full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_utmm_ego-centric-1_40_d3.log

- 2026-10-01 CVPR cvpr/curve_utmm_ego-centric-1_40_vanilla full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_utmm_ego-centric-1_40_vanilla.log

- 2026-10-01 CVPR cvpr/curve_utmm_ego-centric-2_15_d3 full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_utmm_ego-centric-2_15_d3.log

- 2026-10-01 CVPR cvpr/curve_utmm_ego-centric-2_15_vanilla full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_utmm_ego-centric-2_15_vanilla.log

- 2026-10-01 CVPR cvpr/curve_utmm_ego-centric-2_40_d3 full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_utmm_ego-centric-2_40_d3.log

- 2026-10-01 CVPR cvpr/curve_utmm_ego-centric-2_40_vanilla full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_utmm_ego-centric-2_40_vanilla.log

- 2026-10-01 CVPR cvpr/curve_utmm_ego-drive_15_d3 full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_utmm_ego-drive_15_d3.log

- 2026-10-01 CVPR cvpr/curve_utmm_ego-drive_15_vanilla full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_utmm_ego-drive_15_vanilla.log

- 2026-10-01 CVPR cvpr/curve_utmm_ego-drive_40_d3 full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_utmm_ego-drive_40_d3.log

- 2026-10-01 CVPR cvpr/curve_utmm_ego-drive_40_vanilla full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_utmm_ego-drive_40_vanilla.log

- 2026-10-01 CVPR cvpr/curve_utmm_fast-straight_15_d3 full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_utmm_fast-straight_15_d3.log

- 2026-10-01 CVPR cvpr/curve_utmm_fast-straight_15_vanilla full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_utmm_fast-straight_15_vanilla.log

- 2026-10-01 CVPR cvpr/curve_utmm_fast-straight_40_d3 full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_utmm_fast-straight_40_d3.log

- 2026-10-01 CVPR cvpr/curve_utmm_fast-straight_40_vanilla full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_utmm_fast-straight_40_vanilla.log

- 2026-10-01 CVPR cvpr/curve_utmm_slow-straight-1_15_d3 full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_utmm_slow-straight-1_15_d3.log

- 2026-10-01 CVPR cvpr/curve_utmm_slow-straight-1_15_vanilla full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_utmm_slow-straight-1_15_vanilla.log

- 2026-10-01 CVPR cvpr/curve_utmm_slow-straight-1_40_d3 full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_utmm_slow-straight-1_40_d3.log

- 2026-10-01 CVPR cvpr/curve_utmm_slow-straight-1_40_vanilla full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_utmm_slow-straight-1_40_vanilla.log

- 2026-10-01 CVPR cvpr/curve_utmm_slow-straight-2_15_d3 full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_utmm_slow-straight-2_15_d3.log

- 2026-10-01 CVPR cvpr/curve_utmm_slow-straight-2_15_vanilla full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_utmm_slow-straight-2_15_vanilla.log

- 2026-10-01 CVPR cvpr/curve_utmm_slow-straight-2_40_d3 full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_utmm_slow-straight-2_40_d3.log

- 2026-10-01 CVPR cvpr/curve_utmm_slow-straight-2_40_vanilla full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_utmm_slow-straight-2_40_vanilla.log

- 2026-10-01 CVPR cvpr/curve_utmm_square-1_15_d3 full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_utmm_square-1_15_d3.log

- 2026-10-01 CVPR cvpr/curve_utmm_square-1_15_vanilla full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_utmm_square-1_15_vanilla.log

- 2026-10-01 CVPR cvpr/curve_utmm_square-1_40_d3 full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_utmm_square-1_40_d3.log

- 2026-10-01 CVPR cvpr/curve_utmm_square-1_40_vanilla full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_utmm_square-1_40_vanilla.log

- 2026-10-01 CVPR cvpr/curve_utmm_square-2_15_d3 full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_utmm_square-2_15_d3.log

- 2026-10-01 CVPR cvpr/curve_utmm_square-2_15_vanilla full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_utmm_square-2_15_vanilla.log

- 2026-10-01 CVPR cvpr/curve_utmm_square-2_40_d3 full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_utmm_square-2_40_d3.log

- 2026-10-01 CVPR cvpr/curve_utmm_square-2_40_vanilla full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_utmm_square-2_40_vanilla.log

- 2026-10-01 CVPR cvpr/curve_aria_aria1253_15_d3 full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_aria_aria1253_15_d3.log

- 2026-10-01 CVPR cvpr/curve_aria_aria1253_15_vanilla full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_aria_aria1253_15_vanilla.log

- 2026-10-01 CVPR cvpr/curve_aria_aria1253_40_d3 full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_aria_aria1253_40_d3.log

- 2026-10-01 CVPR cvpr/curve_aria_aria1253_40_vanilla full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_aria_aria1253_40_vanilla.log

- 2026-10-01 CVPR cvpr/curve_aria_aria1253rot_15_d3 full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_aria_aria1253rot_15_d3.log

- 2026-10-01 CVPR cvpr/curve_aria_aria1253rot_15_vanilla full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_aria_aria1253rot_15_vanilla.log

- 2026-10-01 CVPR cvpr/first_supported_region_observations CPU_annotationrenders/KF shared_RGB_reference: status=measured, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/region_observations_v1/summary.json

- 2026-10-01 CVPR cvpr/curve_aria_aria1253rot_40_d3 full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_aria_aria1253rot_40_d3.log

- 2026-10-01 CVPR cvpr/curve_aria_aria1253rot_40_vanilla full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_aria_aria1253rot_40_vanilla.log

- 2026-10-01 CVPR cvpr/curve_aria_aria301_12F_15_d3 full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_aria_aria301_12F_15_d3.log

- 2026-10-01 CVPR cvpr/curve_aria_aria301_12F_15_vanilla full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_aria_aria301_12F_15_vanilla.log

- 2026-10-01 CVPR cvpr/curve_aria_aria301_12F_40_d3 full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_aria_aria301_12F_40_d3.log

- 2026-10-01 CVPR cvpr/curve_aria_aria301_12F_40_vanilla full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_aria_aria301_12F_40_vanilla.log

- 2026-10-01 CVPR cvpr/curve_aria_aria301_305_15_d3 full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_aria_aria301_305_15_d3.log

- 2026-10-01 CVPR cvpr/curve_aria_aria301_305_15_vanilla full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_aria_aria301_305_15_vanilla.log

- 2026-10-01 CVPR cvpr/curve_aria_aria301_305_40_d3 full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_aria_aria301_305_40_d3.log

- 2026-10-01 CVPR cvpr/curve_aria_aria301_305_40_vanilla full_asset_panelrenders/KF actual_measurement: status=passed, PSNR=None; results/campaigns/gain_attribution/cvpr_assets/full_asset_panel_v1/curve_aria_aria301_305_40_vanilla.log

- 2026-10-01 CVPR rpng/table_01 15renders/KF rr_dense: status=passed, PSNR=24.458256155371192; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/current_controls_v1/render15/rpng/table_01/rr_dense

- 2026-10-01 CVPR rpng/table_01 15renders/KF ervs_kf_rgb: status=passed, PSNR=24.597321282344986; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/current_controls_v1/render15/rpng/table_01/ervs_kf_rgb

- 2026-10-01 CVPR rpng/table_01 15renders/KF rr_kf_rgb: status=passed, PSNR=24.503652960180762; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/current_controls_v1/render15/rpng/table_01/rr_kf_rgb

- 2026-10-01 CVPR rpng/table_01 40renders/KF rr_dense: status=passed, PSNR=25.660401146725356; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/current_controls_v1/render40/rpng/table_01/rr_dense

- 2026-10-01 CVPR rpng/table_01 40renders/KF ervs_kf_rgb: status=passed, PSNR=25.85854049697815; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/current_controls_v1/render40/rpng/table_01/ervs_kf_rgb

- 2026-10-01 CVPR rpng/table_01 40renders/KF rr_kf_rgb: status=passed, PSNR=25.85563205627806; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/current_controls_v1/render40/rpng/table_01/rr_kf_rgb

- 2026-10-01 CVPR rpng/table_01 40renders/KF native_geometry: status=passed, PSNR=25.70282517391372; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/current_controls_v1/render40/rpng/table_01/native_geometry

- 2026-10-01 CVPR rpng/table_02 15renders/KF rr_dense: status=passed, PSNR=21.27773225144164; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/current_controls_v1/render15/rpng/table_02/rr_dense

- 2026-10-01 CVPR rpng/table_02 15renders/KF ervs_kf_rgb: status=passed, PSNR=21.47495967721286; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/current_controls_v1/render15/rpng/table_02/ervs_kf_rgb

- 2026-10-01 CVPR rpng/table_02 15renders/KF rr_kf_rgb: status=passed, PSNR=21.479047011022697; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/current_controls_v1/render15/rpng/table_02/rr_kf_rgb

- 2026-10-01 CVPR rpng/table_02 40renders/KF rr_dense: status=passed, PSNR=23.858373576647615; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/current_controls_v1/render40/rpng/table_02/rr_dense

- 2026-10-01 CVPR rpng/table_02 40renders/KF ervs_kf_rgb: status=passed, PSNR=24.178258804425802; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/current_controls_v1/render40/rpng/table_02/ervs_kf_rgb

- 2026-10-01 CVPR rpng/table_02 40renders/KF rr_kf_rgb: status=passed, PSNR=24.2738583022601; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/current_controls_v1/render40/rpng/table_02/rr_kf_rgb

- 2026-10-01 CVPR rpng/table_02 40renders/KF native_geometry: status=passed, PSNR=24.242548713945364; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/current_controls_v1/render40/rpng/table_02/native_geometry

- 2026-10-01 CVPR rpng/table_03 15renders/KF rr_dense: status=passed, PSNR=23.31877180445041; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/current_controls_v1/render15/rpng/table_03/rr_dense

- 2026-10-01 CVPR 자산 반영 현황: 20-scene fixed-work 80 runs와 checkpoint80 curves 완료, F3/F4/F5 실제 관측·렌더 및 T6 20/20 반영. current controls14/140, shared Tracking live8/80; 두 장면의 partial T4/T5 재생성. teaser/overview만 두 단, 나머지 active figure/table 한 단. 최신19쪽 PDF 재빌드·렌더 확인; F1/F9 mockup과 전체 time/geometry/original replay 측정은 미완료. [audit](../../../../../results/campaigns/gain_attribution/cvpr_assets/collection_v1/asset_installation_status_20261001_v2.json)

- 2026-10-01 CVPR rpng/table_03 15renders/KF ervs_kf_rgb: status=passed, PSNR=23.316275889115055; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/current_controls_v1/render15/rpng/table_03/ervs_kf_rgb

- 2026-10-01 CVPR rpng/table_03 15renders/KF rr_kf_rgb: status=passed, PSNR=23.366801742140133; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/current_controls_v1/render15/rpng/table_03/rr_kf_rgb

- 2026-10-01 CVPR rpng/table_03 40renders/KF rr_dense: status=passed, PSNR=23.97124403655614; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/current_controls_v1/render40/rpng/table_03/rr_dense

- 2026-10-01 CVPR rpng/table_03 40renders/KF ervs_kf_rgb: status=passed, PSNR=24.934068734227505; /home/intern/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/current_controls_v1/render40/rpng/table_03/ervs_kf_rgb

- 2026-10-01 RTX5070Ti 인계: 사용자 요청으로 local GPU queue/worker 중단, fixed80/80 및 controls19/140 보존. 코드·입력 inventory·실행 가이드 정리; 5070 설치/CUDA/실제 실행은 새 컴퓨터에서 검증. 시간 실험 보류.

- 2026-10-01 CVPR aria/aria1253 15renders/KF d3: status=passed, PSNR=23.46318665715574; /home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/rtx5070ti_fixed_pilot_v1/render15/aria/aria1253/d3

- 2026-10-01 CVPR aria/aria1253 15renders/KF vanilla: status=passed, PSNR=18.954430743938183; /home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/rtx5070ti_fixed_pilot_v1/render15/aria/aria1253/vanilla

- 2026-10-01 CVPR aria/aria1253 40renders/KF d3: status=passed, PSNR=25.760522092571694; /home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/rtx5070ti_fixed_pilot_v1/render40/aria/aria1253/d3

- 2026-10-01 CVPR aria/aria1253 40renders/KF vanilla: status=passed, PSNR=20.856434509044384; /home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/results/campaigns/gain_attribution/cvpr_assets/rtx5070ti_fixed_pilot_v1/render40/aria/aria1253/vanilla

- 2026-10-01 CVPR aria/aria1253 regionrenders/KF D3_15: status=evaluated, PSNR=23.46318665715574; results/campaigns/gain_attribution/cvpr_assets/rtx5070ti_fixed_pilot_v1/aria_manual_regions.json

- 2026-10-01 CVPR aria/aria1253 regionrenders/KF Vanilla_15: status=evaluated, PSNR=18.954430743938183; results/campaigns/gain_attribution/cvpr_assets/rtx5070ti_fixed_pilot_v1/aria_manual_regions.json

- 2026-10-01 CVPR aria/aria1253 regionrenders/KF D3_40: status=evaluated, PSNR=25.760522092571694; results/campaigns/gain_attribution/cvpr_assets/rtx5070ti_fixed_pilot_v1/aria_manual_regions.json

- 2026-10-01 CVPR aria/aria1253 regionrenders/KF Vanilla_40: status=evaluated, PSNR=20.856434509044384; results/campaigns/gain_attribution/cvpr_assets/rtx5070ti_fixed_pilot_v1/aria_manual_regions.json
