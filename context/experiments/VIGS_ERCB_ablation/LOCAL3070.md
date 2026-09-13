# Local3070 end-to-end ERCB development

2026-09-13. 목표: 동일 custom VIGS 시스템/입력/시간 예산에서 RR·기존 ERCB·경량 변형을
비교하고 반복 가능한 held-out 품질 우위를 검증한다. 준비/실행 성공을 품질 성공으로
판정하지 않는다. exp77 fixed-map 결과는 후보 개발 근거이지 VIGS 통합 결과가 아니다.

## 출발점

### 2026-09-13 사용자 요청:3070 중단 /5070 Ti 인계

사용자가 GitHub에 정리하여5070 Ti 에이전트가 재개하도록 요청. GPU 학습 프로세스
없음을 확인했고 새 실험을 시작하지 않는다. CPU correlation staging은 미구현.
코드/문서는 전용 handoff/ercb-rpng-20260913 브랜치로 전달하며 기존 main은 유지.
상세 재개 지침: [HANDOFF_5070TI.md](HANDOFF_5070TI.md).

### 2026-09-13 RPNG retry4 allocator 대안 실패

cudaMallocAsync에서도 frame731 correlation indexing 1003.67MiB 할당 OOM.
최종 PSNR 없음. 해당 실패 프로세스 종료, 로그 보존. allocator 변경만으로
해결되지 않았으므로 다음은 correlation 선택 시 원본/결과의 GPU 동시 상주
피크를 줄이는 정확값 CPU staging 구현을 검토한다. 아직 구현/검증 전이며
추가 전송 시간은 실제 budget에 포함해야 한다. 세 arm 공통 적용 필요.

### 2026-09-13 RPNG retry3 OOM / allocator 대안 검사

parallel replay 설정을 수정한 retry3은 frame1538에서 correlation indexing
880MiB 할당 OOM. 실제 allocated6.10GiB/free841MiB/reserved-unused444MiB.
최종 PSNR 없음; 출력 보존 및 해당 실패 프로세스만 종료. allocator128만으로
병렬 replay의 peak를 해결하지 못했다. 다음은 CUDA11.8의 cudaMallocAsync
allocator를 공통 하드웨어 조건으로 검사한다. 데이터/해상도/pool/학습 recipe는
유지하며, 완주 전 메모리 문제 해결을 주장하지 않는다.

### 2026-09-13 RPNG replay 미실행 원인 확정 및 설정 수정

native RPNG Training에는 parallel이 없어 _gs_parallel=False였고 idle replay
worker가 생성되지 않았다. retry2의15.397522dB는 RR ablation 기준값에서 제외.
RPNG overlay에 UTMM 공통 실행값 parallel=true/queue2/init600/global6/
kernel_batch_render=true/background_polish=false를 반영했다. 실제 load_config로
8개 mapping/loss 항목 일치 및 RPNG IMU400Hz 유지 검사 통과.
이는 ERCB 전용 튜닝이 아니라 실험 설정 누락 수정이며 세 arm 모두 적용한다.
retry3은 같은 scale6/allocator128/KF256으로 RR부터 재측정한다.

### 2026-09-13 RPNG RR retry2 완주, replay 활성 여부 점검 필요

session80940 exit0. fixed502뷰 PSNR15.3975218549dB, Adam2324,
deadline/EOS 이후 업데이트0/0, 평가 map_updates0. 예산501.221578초지만
tracking loop 약540초이므로 전체 시스템6× 완주 주장은 불가.
allocator max_split_size_mb:128에서 OOM 없이 종료; peak allocated7,325,572,608B.
audit_local_pair 필수 평가 검사 pass이나 MAP_RR_DONE이 없어 final pool 및
selection 통계가 null이다. 단순히 낮은 RR 품질로 결론내리지 말고 실제 replay
실행 여부를 확인한 후 ERCB 비교를 진행해야 한다. 이 결과만으로 ablation 유효성
혹은 ERCB 이득을 판정하지 않는다. 원본 출력 retry2 보존.

### 2026-09-13 RPNG retry1 CUDA OOM

retry1은 frame839/2506, KF74에서 factor_graph.rm_factors의 correlation
indexing 중 1004MiB 할당 실패. allocated3.43GiB/reserved-unallocated3.25GiB,
device free755MiB. 최종 PSNR 없음. 실패 프로세스만 종료하고 출력 보존.
단편화 가능성을 먼저 검사하기 위해 retry2는 PYTORCH_CUDA_ALLOC_CONF=
max_split_size_mb:128을 공통 하드웨어 설정으로 사용한다. 데이터/해상도/
학습 budget/pool/scheduler는 불변. 효과는 아직 미검증이며 모든 비교군에
동일 allocator 설정을 적용해야 한다.

### 2026-09-13 RPNG 첫 RR 실패 및 공통 초기화 수정

첫 RR seed0은 frame276/2506에서 Rwg=None 상태의 IMU pose 초기화로 실패했다.
최종 held-out PSNR 없음. 원본 출력은 보존하고 품질 비교에서 제외한다.
공통 runner의 pose-init threshold15가 native RPNG inertial init20보다 빨랐다.
DepthVideo에서 threshold뿐 아니라 실제 Rwg 준비 여부도 확인하도록 수정;
준비 전에는 기존 visual initialization을 유지하고 preintegration은 계속한다.
RR/relative-floor/coverage1 모두 같은 수정 적용. CPU 분기/용량 테스트6개 통과;
CUDA 완주나 품질 동등성 증명은 아니다. 새 출력 suffix retry1로 재실행한다.

retry1 session29396/PID79374 실행 중 frame459까지 확인: 기존 실패 지점276과
inertial 초기화 시점을 통과했다. 아직 최종 평가 없음; 완주·품질 판정은 보류.

### 2026-09-13 사용자 재개 요청: RPNG VIGS 측정 시작

사용자가 RPNG 실제 VIGS 효과 측정을 요청하여 재개. table_01 원본 RGB2506장,
imu.txt 및 repo calib/rpngar.txt 사용. GT pose/point cloud/depth 입력 없음.
runner에 EXP81_DATASET_FAMILY=rpng opt-in 경로를 추가하고 native rpng.yaml의
IMU 단위/외부 calibration/noise를 상속한 exp81_rpng_rgb_only.yaml 사용.
공통 local density256/init64/PPM/adaptive 유지, RGB-only, scale6, zero-tail,
interval gamma log3/block8 유지. KF storage capacity256을 세 arm에 공통 적용
(UTMM128과 다르며 pool eviction 제한은 아님). 장면별 PSNR 맞춤 튜닝 없음.
첫 RR seed0 `outputs/vigs3070_rpng_rr_scale6_seed0`, session44555 시작.
전체 입력 decode/실행 유효성/PSNR은 아직 미검증. 우선 RR/기존/coverage1
seed0을 동일 조건으로 비교하고, 정상 조건에서 seed1/2도 반복한다.

### 2026-09-13 사용자 요청으로 여기까지 / 3-arm 3-seed 수집 종료

사용자 "여기까지 하고" 요청에 따라 새 실험을 시작하지 않는다. 이미 진행된
relative-floor seed2 평가만 회수했다: exit0, fixed324뷰19.585773dB,
Adam25353, pool1235, deadline/EOS 이후0/0. seed2 필요 계약 검사 통과,
RR pool1236과 불일치 경고 유지.

| 방법 | seed0 | seed1 | seed2 | 평균 dB |
|---|---:|---:|---:|---:|
| RR |19.458044|19.390477|19.398387|19.415636|
| relative-floor |19.564295|19.448941|19.585773|19.533003|
| coverage1 |19.518942|19.619168|19.614576|19.584229|

기존 ERCB-RR 평균+0.117367dB(3/3), coverage1-RR+0.168593dB(3/3),
coverage1-기존 평균+0.051226dB(2/3). 단일 개발 장면 square-1/3070 scale6
end-to-end VIGS의 관측이며 범용적·통계적으로 확실한 개선이나 논문 ablation
완료를 의미하지 않는다. pool/pose 차이, latency/overhead, base 분해,
교차 장면 검증은 미완. 다음 장면 GPU 학습/full decode는 시작하지 않았다.

### 2026-09-13 입력 bracket 검사 해석 정정

depth_video.py __preintegrate는 index<1에서 return하고 측정 시작/끝을
가용 IMU index로 clamp한다. 따라서 첫 RGB보다 앞선 IMU를 무조건 요구하는
사전 assert는 실행 가능성 검사로 과도했다. 검사 도구만 변경하여 경계 gap을
별도 수치로 출력하고 boundary_integration_accuracy=not_verified를 유지한다.
slow-straight-2 metadata pass,597RGB/1992IMU,19.869544506초,
initial gap0.012902021초/terminal gap0초. 모든 RGB decode는 아직 미완.
VIGS 적분 동작 자체와 진행 중 학습 recipe는 변경하지 않았다.

### 2026-09-13 다음 장면 입력 사전 검사

slow-straight-2 RGB597장/IMU1992 numeric rows(파일1993행, 헤더 포함).
새 읽기 전용 `audit_utmm_input.py`에서 첫 RGB1706737562.258097887초,
첫 IMU1706737562.271초로 초기 IMU bracket 검사 실패(~12.902ms 지연).
이를 데이터 손상/실행 불가로 단정하지 않으며 입력 처리 정책 대조가 필요하다.
현재 이미지 전체 디코딩 및 나머지 검사는 미완. 실행 중 GPU benchmark에
부하를 주지 않도록 전체 decode는 이후 수행한다. 현재 relative-floor seed2
실행/설정은 변경하지 않았다.

### 2026-09-13 RR seed2 완료 / coverage1 첫 3-seed 비교

`vigs3070_pair_rr_scale6_seed2` exit0, fixed324뷰19.398387dB,
Adam25812, pool1236, deadline/EOS 이후0/0. coverage1 seed2보다
0.216190dB 낮다. 필요 계약 감사 통과, pool1236/1235 불일치 경고 유지.
RR 구간별 [18.428638,19.331919,20.969799,18.863191]dB.

coverage1-RR seed0/1/2 = [+0.060898,+0.228690,+0.216190]dB,
평균 **+0.168593dB**, 단일 개발 장면 square-1에서3/3 양수.
이는 첫 반복 개선 관측이지 교차 장면·범용적 우위 또는 인과적 sampler-only
효과의 증명은 아니다. 동적 pool/pose 경로 차이·추가 overhead·latency
분포·base 분해는 여전히 필요하다. 기존 ERCB와의3-seed 비교를 마치기 위해
계획대로 relative-floor seed2를 동일 설정으로 시작했다.

### 2026-09-13 coverage1 seed2 완료

`vigs3070_pair_coverage1_scale6_seed2` exit0, fixed324뷰19.614576dB,
Adam25177, pool1235, deadline/EOS 이후0/0, 필요 계약 감사 통과.
구간별 [18.456890,19.766117,21.104299,19.130998]dB.
선택 CV0.872045, 마지막 quarter2.480519회. coverage1의 세 seed 결과는
[19.518942,19.619168,19.614576]dB이나 RR seed2가 없으므로3/3 승리
주장은 아직 불가. 계획대로 RR seed2를 동일 공통 설정으로 시작했다.

### 2026-09-13 RR seed1 완료 / 첫 2-seed 비교

`vigs3070_pair_rr_scale6_seed1` exit0, fixed324뷰19.390477dB, Adam25576,
deadline/EOS 이후0/0, pool1236. 같은 seed1 relative-floor19.448941
(RR+0.058463), coverage1 19.619168(RR+0.228690)dB. 세 arm 필요 계약
감사 통과. RR 구간별 [18.692004,19.420150,20.785713,18.664043]dB,
선택 CV0.794570, 마지막 quarter2.679612회.

seed0/1 paired delta: relative-floor [+0.106251,+0.058463], coverage1
[+0.060898,+0.228690]dB. 두 seed 모두 RR보다 높지만 장면1개/2회에
불과하고 pool/pose 경로 차이가 있어 확실한 일반적 우위 판정은 아직 불가.
후보끼리의 순위도 seed에 따라 다르다. 고정 계획대로 coverage1 seed2를
시작했으며 다음 RR seed2, relative-floor seed2 순으로 진행한다.

### 2026-09-13 seed1 pool 차이 읽기 전용 감사

relative-floor/coverage1 `kf_content.csv` 첫 열 diff에서 유일한 차이는
relative-floor에만 존재하는 frame1316이다. `traj_kf_beforeBA.txt`도 각각
71/70행으로 다르다. gs_backend dense 등록은 이미 self.viewpoints에 있는
frame을 skipped_tracked로 제외한다. 그러므로 keyframe 구성 차이가 dense
pool1235/1236 차이와 일관되지만, dense UID 등록 trace 없이 정확히1316이
추가 dense인지 단정하지 않는다. frontend/비동기 경로 차이의 원인 및 품질
영향은 미확정. 동일 config audit PASS가 동일 realized pool/pose를 의미하지
않음을 재확인했다. RR seed1은 설정 변경 없이 계속 실행 중이다.

### 2026-09-13 coverage1 seed1 완료

`vigs3070_pair_coverage1_scale6_seed1` exit0, fixed324뷰 **19.619168dB**,
relative-floor seed1 19.448941 대비+0.170227dB. seed1 RR은 아직 없으므로
RR 우위 미판정. Adam25287, deadline/EOS 이후0/0, 필요 계약 감사 통과.
구간별 [18.755211,19.618833,21.082943,19.019684]dB. 마지막 구간은
relative-floor19.208641보다 낮다. 선택 CV0.866831, 마지막 quarter2.436893회.
최종 pool **1236 vs relative-floor1235**로 다름: 동일 sensor input/config/time
조건의 end-to-end 실행이지만 동일 pool 궤적의 sampler-only 비교로 간주 불가.
이 차이는 숨기지 않고 원인/등록 UID 감사 대상으로 남긴다. 단일 seed0의
후보 순위도 seed1에서 뒤집혔으므로 현재 후보 확정 금지. 고정 실행 계획에
따라 RR seed1을 같은 공통 설정으로 시작했다.

### 해석상 추가 분해 필요

RR과 interval ERCB의 차이는 count bonus만이 아니다. outer block에서 서로
다른 interval을 고르는 혼합도 함께 달라진다. 따라서 후보 확정 이후 `base`
(gamma 효과 제거/동일 interval block 및 inner RR)를 추가해야 count 보정
기여를 분리할 수 있다. 특히 interval 수가 block_size 이하이면 각 block은
모든 interval을 정확히 한 번씩 선택하므로 크기 prior나 bonus는 장기 선택
비율이 아니라 순서만 바꾼다. interval 크기가 다를 때 이 상태를 frame-uniform
분포라고 부르면 안 된다. 이는 구현 구조의 성질이며 현재 PSNR 차이의 원인으로
확정한 것은 아니다. 진행 중인 3-arm 반복 recipe는 변경하지 않는다.

CPU 재현 검사: 크기9/1의 두 interval, block_size8, 총200 draw에서
base/coverage1/relative-floor 모두 interval별100/100회 선택됨.
`test_full_interval_blocks_are_not_frame_uniform` 3 mode 추가 후 interval
test8개 통과(0.03s). 학습 코드 변경 없음. 이 검사는 구조적 편향만 증명하며
실제 장면에서 해당 편향의 PSNR 영향은 미검증이다.

### 2026-09-13 relative-floor seed1 완료

`vigs3070_pair_relative_floor_scale6_seed1` exit0, fixed324뷰19.448941dB,
Adam25692, deadline/EOS 이후0/0, 필요 계약 감사 통과. 구간별
[18.377360,19.236791,20.972971,19.208641]dB. 선택 CV0.770639,
초기/중간/마지막 quarter38.636364/14.116883/3.561688회.
seed0의19.564295보다0.115355dB 낮다. 이는 seed0에서 관측한 RR 대비
0.106251dB 이득과 비슷한 변동 규모이므로 단일 결과 주장은 부적절하다.
아직 seed1 RR이 없으므로 이 실행의 RR 대비 우열은 미판정이다.
계획에 따라 같은 공통 설정 coverage1 seed1 실행을 시작했다.

### 2026-09-13 coverage1 seed0 완료

`vigs3070_pair_coverage1_scale6_seed0` exit0, fixed324뷰 **19.518942dB**.
RR19.458044 대비 **+0.060898dB**, relative-floor19.564295 대비
**-0.045353dB**. 세 arm 필요 계약 감사 통과(동일322.856502초/scale6,
deadline/EOS update0/0); coverage1 Adam25221, RR26140, relative-floor26374.
coverage1 구간별 PSNR [18.544900,19.387747,20.952083,19.191040]dB.
선택 CV0.856736, 초기/중간/마지막 quarter40.597403/12.438312/2.714286회.
RR 마지막2.610390, relative-floor3.811688회와 비교해 지속 보정은 약하다.
coverage1은 단일 seed에서 RR보다 소폭 높지만 기존 ERCB를 개선하지 못했다.
분산·시간별 pool·학습 trace·다른 장면 검증 전 성공 판정 금지.
고정 계획에 따라 relative-floor seed1을 동일 설정으로 시작했다.

### 2026-09-13 반복 비교 계획 고정 (coverage1 seed0 결과 확인 전)

square-1은 개발 장면이다. 같은 공통 recipe/scale6에서 seed0,1,2를 모두
비교하며 좋은 결과만 남기거나 첫 승리에서 종료하지 않는다. 실행 순서는
seed0 RR→relative_floor→coverage1, seed1 relative_floor→coverage1→RR,
seed2 coverage1→RR→relative_floor로 교대한다. 인프라 실패는 로그를 남기고
동일 설정 재실행하며 품질이 낮다는 이유로 재실행하지 않는다. 최종 fixed
held-out 평균과 각 seed의 paired delta, 구간별 품질/선택 횟수 및 실제 시간
계약을 모두 보고한다. 3 seeds는 개발 최소 확인이지 확실한 일반화 증명이
아니다. 후보 선택 후 별도 장면으로 검증하며 공통 recipe 변경 시 비교군도
함께 새로 실행한다. 프레임을 독립 seed처럼 취급해 유의성을 부풀리지 않는다.

### 2026-09-13 동일 조건 relative-floor seed0 완료

`vigs3070_pair_relative_floor_scale6_seed0_retry1` 정상 종료. fixed324뷰
PSNR **19.564295dB**, RR `vigs3070_pair_rr_scale6_seed0` **19.458044dB** 대비
**+0.106251dB**. 동일 scale6/322.856502초, Adam26374 vs26140,
deadline/EOS 이후 update 모두0/0. audit_local_pair.py 필요 계약 검사 통과.
전체 평가 union 평균19.672213은 고정 held-out 비교값으로 사용하지 않는다.
relative-floor 선택 횟수 CV0.773085, 초기/중간/마지막 quarter 평균
39.883117/14.363636/3.811688. 단일 seed의 작은 차이이며 반복 우위나
인과적 품질 개선의 증거로 충분하지 않다. 시간별 pool 동일성·supervision
trace·반복성·교차 장면은 미검증. 다음 coverage1을 동일 설정으로 실행한다.

고정 held-out을 입력 frame index 기준 4등분(각81뷰)한 PSNR은
RR [18.221905,19.535857,20.974794,19.099622], relative-floor
[18.569538,19.609494,20.932643,19.145507]dB.
차이는 [+0.347633,+0.073638,-0.042151,+0.045885]dB로, 평균 이득은
주로 초기 구간에 있다. 따라서 후반 서비스 보정이 품질 향상의 원인이라는
해석은 현재 결과로 지지되지 않는다. audit_local_pair.py에 고정 frame 구간
집계를 추가했으며, 이는 최종 map의 구간별 품질이지 시간별 수렴 곡선이 아니다.

### 2026-09-13 메모리 진단 추가

**첫 end-to-end 완료: memory_trim_rr, session69205 exit0.** square-1 1614프레임,
fixed324뷰 PSNR19.603031dB/SSIM0.658352/LPIPS0.396012.
fixed UID는 {0,5,...,1610,1613}와 정확히 일치. fixed_eval_mapping_excluded=true,
KF overlap16(추적 KF와 겹친다는 뜻, 이 플래그만으로 supervision leakage 판정 금지).
trajectory_uid_aligned=false이나 trajectory1614행/전체 입력1614이므로 gap 여부는
추가 감사 대상. final evaluation map_updates=0, deadline/EOS 이후 Adam0/0.
budget322.856502s, 전체 Adam25416/replay22751. dense pool1235, eviction0.
RR 선택 초기/중간/마지막 quarter 평균40.2695/13.7175/2.4643회.
trim7회 총629.18ms, census 포함812.28ms(예산 대비 약0.252%). allocated CUDA
peak4,992,875,520B/reserved7,883,194,368B. 이 run은 diagnostic이므로 paper
timing 비교에서 제외하며, ERCB 우위는 여전히 미검증이다. 다음: census 없이
동일 periodic trim을 모든 arm에 적용하고 RR/relative_floor/coverage1 실제 비교.

malloc_trim 실측 반환 확인: dense142에서 RSS4,102,644→2,949,016kB
(1,153,628kB 감소), trim74.34ms. dense209에서는3,703,824→3,138,864kB
(564,960kB 감소),37.61ms. free arena가 실제 resident pressure에 기여함을
확인했다. 주기 반환 시 전체 완주 및 overhead는 아직 미검증이며 session69205
계속 진행 중. 첫 두 지점만으로 scheduler 품질/시스템 안정성을 주장하지 않는다.

census run에서 dense417: arena4.802GB, fordblks3.196GB, uordblks1.605GB,
RSS6,590,816kB. 주요 dense CPU265.89MB/KF148.78MB, cache두종0.
allocator 반환 실험으로 전환하기 위해 main64927/자체 reader64984 종료.
`vigs3070_memory_trim_rr`는 동일 조건+VIGS_DIAGNOSTIC_TRIM=1로 시작했다.
각 census에서 malloc_trim(0) 반환 전후 RSS 및 trim_ms를 기록한다.
두 실행은 계측 진단이며 품질/시간 ablation 결과로 사용하지 않는다.

첫 allocator 계측: dense142→209에서 mallinfo2 arena2.499→3.124GB,
fordblks(allocator 내부 미사용 공간)1.223→1.759GB. dense CPU storage는
90.54→133.27MB, KF CPU storage53.56→83.32MB였다. 전체 RSS4.15→4.84GB.
free block 전체가 resident이거나 OS 반환 가능하다는 뜻은 아니지만, 다음 검증은
malloc_trim 전후 RSS 비교가 타당하다. live tensors 전체 원인은 아직 미확정.
진단 session21128은 현재 진행 중이며 PSNR 결과 없음.

`vigs3070_memory_census_rr` 시작: 직전 compact 조건 + VIGS_MEMORY_DIAGNOSTIC=1.
200 dense 증가마다 주요 backend tensor storage(그룹 내부 dedup), proc RSS 및
glibc mallinfo2 통계를 기록한다. 그룹 간 공유는 있어 합산 금지, 전체 프로세스
tensor census는 아니며 frontend/외부 라이브러리는 별도 원인으로 남는다.
계측 비용 때문에 이 실행을 timing ablation에 사용하지 않는다. shared slice
dedup/clone storage 소형 테스트 통과. 이전 session41487 exit143 확인.

buffer128_compact 조합도 frame979에서 available880,392kB/RSS8,775,816kB로
감소해 main64223 TERM. 최종 PSNR 없음. process_memory.jsonl에 5초 간격
실측 기록 보존. 다음은 추가 설정 조합 탐색보다 실제 tensor storage census와
allocator 잔류 메모리 진단을 우선한다. 메모리 원인 해결/ablation 완료 미달성.

조합 probe `vigs3070_probe_rr_hf_scale6_seed0_buffer128_compact` 시작:
VIGS_CPU_DENSE_UINT8=1, VIGS_OWN_CAMERA_PRIORS=1, EXP81_BUFFER_SIZE=128.
square-1/6×/seed0/HF 유지. 이는 단일 축 효과 추정이 아니라 완주 가능성
확보를 위한 조합 진단이며, 채택 시 모든 scheduler arm에 동일 적용한다.
KF128 초과는 RuntimeError로 실패하며 dense pool eviction은 여전히 없다.
이전 session43015 exit143 및 자체 reader63546 종료 확인 후 시작했다.

ownedpriors 단독 probe는 frame1289에서 available772MiB/RSS8,440,176kB로
감소해 main63489에 TERM. 이전 OOM 지점은 통과했지만 단독 수정으로 안정적
완주를 확보하지 못했다. 최종 PSNR 없음. 다음 진단은 이미 검증한 저장 개선의
조합이며, KF capacity128(초과 시 명시적 실패, eviction 없음)을 검토한다.

`buffer256_ownedpriors` RR probe 시작: VIGS_OWN_CAMERA_PRIORS=1,
VIGS_CPU_DENSE_UINT8=0으로 frame별 depth/normal clone만 격리한다.
나머지는 square-1/6×/seed0/buffer256/HF 동일. 실제 Camera 생성의 CPU
depth/normal 및 CUDA cache 네 텐서가 기존과 exact임을 확인했고 CPU storage가
frame numel×element_size와 일치함을 확인했다. 아직 전체 메모리/완주 미검증.
GPU lookup probe session49359는 exit143 종료 확인, 자체 reader62809 정리 완료.

GPU lookup probe도 frame776 시점 available812MiB로 감소해 main62780에 TERM.
전체 메모리 개선 미입증, 품질 결과 없음. 새로운 원인 후보: keyframe Camera가
depth_packet[i], packet['normals'][i]를 그대로 보유하여 전체 batch storage를
붙잡는다. CPU 재현에서 32장 normal batch의 한 장(논리2,550,528B)이
81,616,896B storage를 보유하고 clone은 값 동일/2,550,528B였다. 실제 유지되는
패킷 수의 계측과 frame별 독립 storage 수정 검증이 다음 작업이다.

GPU復元 probe `vigs3070_probe_rr_hf_scale6_seed0_buffer256_u8gpu` 시작.
조건은 직전과 동일하고 dense replay loss에서 Camera.rgb_on()으로 CPU float
복원을 피한다. GPU 나눗셈은 기존 CPU /255와 최대5.96046e-8 달라 직접 사용하지
않고 CPU float32 값 256개 lookup을 GPU에 캐시한다. CPU/실제 CUDA exact,
copy/clear/거절 테스트 5 PASS. 아직 전체 실행 효과는 미검증이다.
이전 u8 probe session78861은 exit143 종료 확인, GPU compute0/RAM available9.3GiB.

**uint8 CPU 복원 probe도 실패:** frame827에서 available RAM509MiB,
main PID61893 RSS8,595,188kB. 시스템 OOM 재발 방지를 위해 해당 main에 TERM.
픽셀 동일성은 등록 검사에서 통과했지만 전체 RSS는 개선되지 않았다. 단순 내부
uint8 보관 + 매 접근 CPU float 복원은 채택하지 않는다. 다음 진단은 CPU 임시
복원 텐서를 피하는 sampled-view GPU 변환 경로이며, 원인을 확정한 것은 아니다.

uint8 저장 probe 시작: `vigs3070_probe_rr_hf_scale6_seed0_buffer256_u8`.
VIGS_CPU_DENSE_UINT8=1만 추가한 RR/6×/seed0/buffer256/HF 진단이다.
Camera public original_image는 float32/255 값을 유지하고 내부 CPU RGB만 원본
uint8로 보관한다. 등록 시 기존 float와 torch.equal 불일치면 명시적으로 실패한다.
전체 256 픽셀 수준, 원본 변경 독립성, deepcopy, setter 해제, 손실 입력 거절 및
capacity 테스트 합계 6 PASS. 호출 시 float 복원 비용과 전체 메모리는 실측 전이다.
replay seed 하드코딩0을 EXP81_SEED로 수정했다(현재 seed0 probe에는 변화 없음).
용량/uint8 설정을 input_provenance에 추가했다. 이전 실패 probe 보조 프로세스를
정리한 뒤 session98003은 exit137로 종료 확인, GPU compute0/RAM available9.3GiB.

**buffer256 probe 종료: 실패.** frame1253/1614 부근에서 PID58718이 사라졌고,
kernel journal의 `Out of memory: Killed process 58718 (python)`으로 RAM OOM
확인(anon-rss 7,363,124kB, shmem-rss 1,232,128kB). 최종 평가 결과는 없다.
직전 available RAM은 frame1146 623MiB → frame1240 483MiB였으며 swap0.
부모 실행 session98003은 자식 종료 뒤에도 아직 terminal 응답이 없어 별도
잔존 프로세스 확인이 필요하다. 재실행은 아직 시작하지 않았다.
다음: dense RGB float32 CPU 보유와 중복 이미지 저장 경로 감사 및 원본 uint8
보존 가능성 검증. pool eviction으로 숨기지 않는다.

후속 probe 시작: `vigs3070_probe_rr_hf_scale6_seed0_buffer256`, RR/6×/seed0/HF
가중치는 실패 probe와 같고 EXP81_BUFFER_SIZE=256만 추가했다. runner 기본값은
기존 -1을 유지한다. DepthVideo setter에 capacity 초과 시 counter/IMU 수정 전
명시적 RuntimeError를 추가했다. dense replay pool 제한/eviction은 추가하지 않았다.
shell syntax 및 Python compile 통과; 실행 중이며 완주/품질 결과는 아직 없다.
capacity 초과 int/tensor 입력에서 counter와 timestamp 수정 전에 실패하는 CPU
테스트 3개 통과(실제 setter AST에서 CUDA decorator만 제거; 전체 SLAM 동등성
검사가 아님). frame331에서 available RAM 4.2GiB이나 GPU 7,244MiB이므로
GPU peak 문제는 여전히 감시가 필요하다. 기본 runner의 final evaluation 및
mapping fixed-eval exclusion 옵션도 확인했다.

실패 probe 종료 후 GPU compute process 없음, 시스템 available RAM 8.9GiB 확인.
`run_utmm_strict15x_baseline.sh`는 EXP69_BUFFER_SIZE=-1을 지정하고,
`demo.py`는 이를 1,200으로 변환한다(CLI 설명의 자동 1/10과 다름).
DepthVideo는 모든 슬롯의 CPU RGB uint8, full-resolution disparity 두 벌,
float32 normal 및 CUDA feature 세 벌을 선할당한다. 이는 실제 활성 KF 수와
무관한 큰 고정 비용이다. 다음 조치는 capacity/성장 정책 및 소비 경로 감사이며,
임의 frame eviction이나 품질 조건 변경으로 처리하지 않는다.
이 진단은 메모리 압박의 기여 요인을 확인한 것이지 단일 원인 확정은 아니다.

- Lab main: `3b8cc82` pull 완료.
- VIGS: `.codex-work/VIGS-SLAM-exp81`, branch `exp81-vigs-benchmark-strict15x`,
  `23adbfaf9f191a174426d2ad73e58c4ddfc22adb`.
- GPU: RTX3070 Laptop 8 GiB. 기존 `3dgs` env는 보존하고 `vigs3070` clone 준비 중.
- 원본 UTMM 네 폴더가 보이나 새로 전송한 세 sequence는 완료 확인/입력 감사 전이다.
- verified server baseline은 KF100 replay이며 ERCB off다. dense active set paired
  비교는 별도로 구성해야 한다. provisional pre-IMU gate는 모든 비교 arm에 동일 적용.

## 준비 병목

서버 runner는 1.5x/profile을 하드코딩하고 setup.py는 CUDA compute120까지 지정한다.
3070 호환 빌드와 메모리 상한을 먼저 확인한다. 기존 환경의 CUDA11.8/Torch2.1 clone은
후보일 뿐 최신 코드 호환성은 아직 미검증이다. 필요 의존성·extension submodule을 준비한다.
서버 TensorRT engine은 다른 GPU에서 그대로 사용하지 않는다.

## 실행 순서

### 첫 실제 scheduler 개발 비교 고정 (2026-09-13)

relative_floor 최초 실행은 frame204에서 service_state 누락으로 GS_WORKER_FATAL.
품질 실패가 아니라 통합 인터페이스 실패이며 main67258/reader67285 정리,
session76902 exit143. service_state 및 비-admission 큐 규약의
admission_epochs_completed=0을 추가했다. 선택 알고리즘은 변경하지 않았고
interval/identity tests11 PASS. 동일 조건 retry1(session88027) 시작.
실행 provenance RR 대비 차이는 mapping_interval_ercb 하나임을 확인했다.

RR seed0 완료(session42335 exit0): fixed324뷰19.458044dB, Adam26140,
deadline/EOS 이후0/0. audit_local_pair 필요조건 통과. 진단 run19.603031보다
0.144987dB 낮음(계측 유무도 달라 이를 순수 seed 분산으로 해석하지 않는다).
`vigs3070_pair_relative_floor_scale6_seed0`를 동일 설정으로 시작(session76902).
아직 시간별 pool equality/실제 supervision trace/반복성/다장면 검증은 남았다.

`exp81_axes/audit_local_pair.py` 추가: 완료 로그/final eval update0/EOS·deadline0,
fixed UID·PSNR 재집계, 공통 실행 설정을 검사한다. 기존 memory_trim 진단 결과는
공통 periodic_heap_trim 필드가 없어 명시적으로 거부함을 확인했다. 이 도구는
필요조건 검사이며 pool 동등성/실제 supervision trace/반복성 증명은 별도다.

RR → relative_floor → coverage1, square-1/seed0/6×/buffer128/HF official.
모든 arm에 CPU dense uint8+GPU exact lookup, owned camera priors,
VIGS_PERIODIC_HEAP_TRIM=1, MEMORY_DIAGNOSTIC=0 동일 적용.
200 dense bucket마다 allocator 반환만 수행하고 누적 calls/ms를 기록한다.
첫 run `vigs3070_pair_rr_scale6_seed0` 실행 시작. 예산은 기존 throughput probe의
6×를 그대로 유지하며 상대 PSNR을 보고 고른 예산이 아니다. 아직 6×가 실시간
strict1.5×라는 주장은 하지 않는다. 이 장면은 개발 장면이며 seed 반복과
untouched scene 전이 없이 paper 일반화 성공으로 판정하지 않는다.
판정: 동일 fixed324 UID, fixed PSNR, deadline/EOS0, pool/admission 차이 감사,
전체 시간·반환 비용 및 cohort 서비스 통계. 불리한 결과도 모두 보존한다.

### 평가 계약 감사 (2026-09-13)

현재 VIGS eval_utils.py의 기본 fixed set은 `idx % 5 == 0` 및 마지막 입력
프레임이다. 3dgs-custom render.py의 llffhold-8과 다르다. 비교 대상은
`psnr/<iteration>/final_result.json`의 fixed_eval_mean_psnr 및 fixed per_view이며,
keyframe union의 mean_psnr을 held-out 값으로 사용하지 않는다.
기존 PSNR/MSE는 `gtimage > 0` 색상 성분 mask를 사용한다(전 픽셀 MSE와 다름).
keyframe mapping exclusion은 %5와 expected_last_frame을 포함함을 확인했다.
최종 fixed UID 일치·mapping 제외·zero-tail은 각 완주 결과에서 추가 감사해야 한다.

1. 별도 환경과 extension import를 확보하고 데이터 복사 완료/파일 유효성을 확인.
2. baseline end-to-end 실행과 메모리/처리량 계측. 품질을 보고 유리한 시간 배수 선택 금지.
3. 측정한 3070 제한 예산을 고정하고 same-pool RR/ERCB 통합 경로 감사.
4. 기존 저예산 관측에 근거한 경량 변형 개발 후 동일 조건 반복 비교.
5. 품질·비용·서비스·zero-tail 감사를 함께 기록. 불리한 결과도 유지.

아직 실제 VIGS GPU run과 품질 결과는 없다. 시간 배수를 늘린 결과는 strict1.5x와 구분한다.

## 준비 진행

- RR6x retry2: mapping 실제 성립(GS약2.7만/dense194 확인)했으나 frame340 부근부터
  급격한 지연. GPU7,780MiB, 프로세스RSS9.14GB, 시스템 available288MiB/swap0,
  D-state 확인. 시스템 보호를 위해 내 PID57781에 TERM 요청했다. 완주/PSNR 성공이
  아니며 메모리 압박 진단 실패로 유지한다. 전체 RAM/VRAM 버퍼 정책을 먼저 점검해야 한다.

- `--scaled_streaming_online`를 추가해 인과 입력/Phase2 금지/zero-tail 검사는 공유하되
  provenance policy를 hardware_scaled_rgb_imu_only로 분리했다. 기존 strict 플래그는
  여전히1.5만 허용한다. square-1 RR 임시6x/HF seed0 retry2가 실제 스트림 처리 시작,
  PID57781 약5,030MiB GPU 사용 확인. 출력 `outputs/vigs3070_probe_rr_hf_scale6_seed0_retry2`.
  아직 실행 중이며 mapping/PSNR 성공 판정 전이다.6x는 throughput probe이지 고정 논문 예산 아님.

- HF 공식 depth/normal 실제 CUDA forward PASS(384² zero input, 출력 finite).
  square-1 RR 6x throughput probe를 시도했으나 모두 학습 전 실패:
  conda activation nounset 충돌 → activation 동안만 완화;
  in-tree rasterizer가 설치 wheel을 shadow → 3070만 wheel 경로 사용;
  마지막에는 `VIGS_SENSOR_EOS_ZERO_TAIL=1 requires --strict_aria_online` 계약 검사 실패.
  기존 strict 플래그는 1.5만 허용하므로 단순 scale override로6x 실행할 수 없었다.
  zero-tail을 끄지 않고 scaled streaming 계약을 명시적으로 분리하는 수정이 필요하다.
  실패 output 경로는 보존했고 PSNR은 없다.

- 공식 HF depth/normal 모두 VIGS DPTDepthModel에 strict=True 로딩 **All keys matched**.
  Omnidata loader가 기존 wrapper 또는 공식 bare state_dict를 strict-load하도록 확장,
  motion_filter에 명시적 VIGS_OMNIDATA_DEPTH_PATH/NORMAL_PATH override를 추가했다.
  기본 Zenodo 경로는 유지한다. 실제 forward, mapper 초기화, PSNR 비교는 아직 남았다.

- HF 공식 배포 depth/normal 다운로드 **완료**, API LFS SHA256와 로컬 hash 둘 다 일치:
  depth `2f6a22581fb42510053b242dd07b0fa0917368f5e23f434be2a6a10caf1b7e6e`,
  normal `1af4506385ef4c828af559309ec89428833c005d7ecbcf921c4b12f84c2f62df`.
  각 파일약493MB. 기존 Zenodo checkpoint와 포맷/가중치 동등성은 별도이며,
  이 파일로 서버 수치 재현을 주장하지 않는다. 다음은 VIGS model strict-load 검사다.

- Zenodo 연결 timeout이 반복돼 공식 Omnidata README가 안내하는 alexsax/omnidata_models
  hubconf.py를 확인했다. 해당 공식 entrypoint는 sashasax Hugging Face의 depth/normal
  dpt_hybrid_384 state_dict를 배포한다. 별도 `.official.pth`로 다운로드 시작했고 실제
  파일 증가를 확인했다. 원래 부분 ckpt는 보존했다. VIGS 호환/원본 tensor 동등성은
  아직 미검증이며 서버 정본과 동일하다는 주장 없이 별도 검증해야 한다.

- 다운로드 운영 실패 정정: depth curl의 `--retry-all-errors`가 1800초 timeout 뒤
  해당 invocation의 초기 resume offset으로 파일을 되돌렸다(약1.2GB→0.47GB).
  진행 일부를 잃었으며 무결성 성공으로 간주하지 않는다. 내 PID52247만 TERM하고
  자동 retry 없이 `-C -`, max-time7200으로 다시 이어받았다. 다음 오류는 terminal을
  확인한 뒤 새 invocation에서 현재 파일 끝을 기준으로 재개해야 한다.

- 확장 회귀 검사: exp81_axes 전체 + exp72 count scheduler + exp66 map scheduler
  **88 PASS / 3.43초**. 첫 실행은 ROS launch_testing 자동 plugin 및 module path 충돌로
  collection 실패했다. `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`,
  `PYTHONPATH=thirdparty/lietorch`, `pytest --import-mode=importlib`로 격리해 통과.
  테스트 소스를 완화하지 않았으며 native CUDA smoke/실학습과 별개 검사다.

- Zenodo record10447888 API에서 v2 depth/normal 정본 크기와 MD5를 확보하고 read-only
  verifier를 추가했다. local runner는 checksum 검사를 통과하기 전 GPU 실행을 거부한다.
  현재 depth447,142,536/1,947,430,832B, normal550,248,448/1,947,430,960B로
  미완성 판정(exit1). 부분 파일을 잘못 로드해 학습하는 경로를 차단했다.

- Epoch/controller 감사: dense_rr runner는 mapping_model_scheduler/adaptive_viewset을
  끄며 auto-topology-freeze는 epoch가 아니라 GS 수와 직전 topology event로 결정된다.
  interval port는 model/adaptive controller 혼용도 명시적으로 거부하도록 보강했다.
  동일 controller 규칙이라도 선택 gradient로 topology 결과가 달라질 수 있으므로
  실행 후 GS 수/freeze 시점은 기록해야 한다(동일 geometry를 보장한다는 뜻 아님).

- 重要 정정: pose repair가 causal_left/right_keyframe을 갱신하는 경로가 있어 그 필드는
  영구 interval identity가 아니었다. 등록 시 causal_birth_interval을 별도 보존하고
  scaled camera에도 전달, scheduler는 최초 bracket을 사용하도록 수정했다.
  pose-repair 회귀 테스트 포함 interval tests10 PASS. 기존 pose 보정 동작은 유지한다.

- `exp81_axes/run3070_interval_arm.sh` 비교 scaffold 추가. 명시적 sequence/arm/scale/seed/
  새 output을 받아 동일 dense-only RGB full-gradient recipe로 실행하며 다른 GPU compute
  process가 있으면 거부한다. 기존 output 덮어쓰기 거부. seed를 실제 demo.py에 전달.
  syntax와 잘못된 arm 거부 검사 통과. throughput 미측정으로 예산 확정 전이며 아직
  이 runner로 실학습을 시작하지 않았다. 서버 KF100 recipe와 별도 실험임을 유지한다.

- CLI validation에 interval gamma 유한/비음수, block 양수, dense-only B1 replay 제약을
  추가하고 run metadata에 mode/gamma/block을 기록하도록 연결했다. 관련 scheduler /
  gradient role / source quota 테스트 합계 **24 PASS** (1.25초), py_compile PASS.
  현재 checkpoints는 depth327MiB/normal412MiB로 아직 미완성이다(05:08 확인).
  여유 공간21GiB이며 기존 데이터/환경 삭제는 하지 않았다.

- exp77 원본 scheduler.py를 직접 import해 포트와 대조: 10 seeds × relative-floor /
  coverage1, 신규 interval이 미완료 block 중 도착하는 additive stream에서 **1,360개
  draw 정확히 일치**. `exp81_axes/check_exp77_interval_port.py`로 재현 가능.
  ID 정렬 순서가 일치하는 소형 입력에 한정하며 eviction/기존 interval 추가 도착 및
  VIGS end-to-end 결과의 동등성까지 입증한 것은 아니다.

- `EXP81_INTERVAL_ERCB=off|base|relative_floor|coverage1`를 실제 geometry_args에
  전달하도록 runner 연결. mixed-source 및 frame-softmax와의 혼용 거부, bash -n 통과.
  1,000회 B1 CPU microbenchmark: 고정1,000뷰 draw 평균0.499→0.0278ms,
  5,000뷰2.652→0.1336ms(pool 동일 시 sync 재구성 생략). 단일 측정이며 assignment
  생성/카메라 조회/실제 mapping 비용은 미포함. 1–3% overhead 달성 증거는 아니다.

- Interval replay opt-in CLI (`--mapping_interval_ercb`) 및 gs_backend draw 연결 추가.
  기본off 유지. dense-only/idle replay만 허용하며 기존 count-softmax, archive/FIFO,
  work-credit/token admission과의 혼용을 거부한다. camera bracket으로 assignment를
  만들고 pool/gradient/optimizer 선택 외 경로는 변경하지 않았다. py_compile 통과,
  interval/identity tests 9 PASS. 실제 runtime 통합은 모델 다운로드 후 검증해야 한다.

- Interval 큐 초안 `vigs/interval_replay.py` 추가: relative-floor / coverage1 / base를
  같은 outer PL K-block + inner persistent RR 구조로 구현. causal bracket assignments를
  입력받고 사라진 후보는 제거하며 identity 변경은 거부한다. 신규 후보의 inner epoch
  admission은 다음 pass로 두었다. 이는 exp77의 단발 add와 다른 온라인 변경 처리라
  추가 equivalence/overhead 검증이 필요하다. 아직 gs_backend에 연결하지 않았다.

- 2026-09-13: `exp81_axes/smoke3070_rasterizer.py`를 추가하고 native CUDA forward /
  backward PASS. 화면 안 Gaussian의 양수 radius와 색상 gradient 비영(非零)을 확인하고,
  xyz/screen-space/color/opacity/scale/rotation gradient가 모두 finite임을 검사했다.
  32x32 단일 Gaussian 호환성 검사로 end-to-end SLAM 또는 품질 증거는 아니다.

- 2026-09-13 05:00: rasterizer 빌드/설치 완료. RTX3070에서 KNN 및 SE3.exp CUDA
  smoke test 통과. 전체 VIGS CUDA 경로/렌더 backward 검증을 대신하지 않는다.
  opt-in rtx3070 hardware profile 및 원본 lietorch PYTHONPATH를 runner에 연결했다.
  명시적 EXP81_REPLAY_TIME_SCALE(기본1.5), EXP81_ERCB_BETA(기본off)를 추가하고
  quota가 달라지는 mixed-source ERCB 조합은 거부한다. shell syntax/profile checks 통과.
  이 profile은 호환성 준비이며 3070의 실제 시간 배수는 아직 측정하지 않았다.

### Same-pool 코드 감사 (2026-09-13)

- Interval 이식에 필요한 metadata 확인: `register_causal_dense_views`가 Camera에
  causal_left_keyframe/right_keyframe을 저장한다. 등록 batch가 아니라 이 bracket을
  interval identity로 쓸 수 있다. `causal_dense_interval_key`와 누락/역전 bracket
  거부 tests를 추가했다. legacy 3-field record는 endpoint가 없어 조용히 임의 grouping하면
  안 된다. 실제 scheduler wiring 및 품질 비교는 아직 미완료다.

- **알고리즘 정체성 주의:** 현재 VIGS EntropyRegularizedCountReplayQueue는 frame별
  exp(-beta*count) minibatch sampling이다. exp77 FINAL_REPORT의 interval-size prior,
  K8 interval 비복원 + 내부 persistent RR 기반 ERCB/coverage1과 동일하지 않다.
  beta를 켜는 것만으로 exp77의 기존 ERCB를 이식했다고 보고하면 안 된다.
  다음 개발은 exp77 구현을 확인하고 causal interval 정의를 맞추는 작업이 필요하다.
- square-1 입력 감사: RGB 1,614장 전부 decode 성공(1280x660), timestamp 중복0.
  파일명 nanosecond 기준 구간 약53.8094초. IMU 5,384x7 전부 finite,
  시간 범위1706737736.846–1706737790.676초. RGB 시작이 IMU 시작보다 약30ms 빠르므로
  loader의 초기 정렬 처리 확인이 남아 있다. 데이터 자체는 변경하지 않았다.

- `gs_backend.py:1636`의 queue 선택은 count-softmax beta>=0이면 ERCB가 최우선이다.
  RR 경로에만 SourceQuotaReplayQueue가 적용되므로 KF100 recipe의 beta만 바꾸는
  비교는 scheduler-only가 아니다. source quota=-1 및 archive/FIFO/admission 설정을
  동일하게 고정하고 CausalShuffleQueue 대 ERCB를 비교하는 구성이 필요하다.
- `gs_backend.py:6933` replay_by_key는 평가 제외 keyframe과 dense_viewpoint_stack을
  합쳐 공통 후보를 만든다. 실제 dense 등록/평가 제외 경로와 시간별 pool fingerprint는
  추가 감사해야 한다. 같은 설정이 같은 실행별 pool을 보장한다고 아직 판정하지 않는다.
- `exp72_axes/test_entropy_count_scheduler.py`: 기존 ERCB 9 tests PASS.
- `demo.py --help`: exit0. 이는 CLI/import 검사이지 CUDA runtime/품질 검증은 아니다.

- 2026-09-13 04:56 로컬 확인: 순차 빌드로 vigs_backends/lietorch_backends 컴파일 성공,
  `PYTHONPATH=thirdparty/lietorch`에서 Torch2.1.2와 두 backend 및 lietorch import 통과.
  rasterizer 단독 빌드를 재개했다. Omnidata depth 파일은 14MiB로 미완성이고 normal은
  다운로드 프로세스가 살아 있다. 가중치 완전성 확인 및 실제 실행 검증은 아직 남았다.

빌드 실패 정정: kernel journal에서 `cicc` OOM kill을 확인했다(04:51:15).
RAM14GiB/swap0에서 backend/rasterizer 동시 빌드가 메모리 부족을 유발했다.
내 rasterizer 빌드 프로세스만 TERM으로 중단하고 기존 object를 보존했다.
이후 MAX_JOBS=1 및 모듈 간 순차 빌드로 진행한다. 소스 호환성 오류로 확정하지 않는다.

- `vigs3070` conda clone 완료, Torch2.1.2+cu118 import 확인. 원래3dgs env 변경 없음.
- 모든 extension submodule이 지정 commit으로 checkout 완료.
- `exp81_axes/setup3070.py` 추가: upstream setup.py는 유지하고 sm86/original lietorch로
  별도 build_ext 경로 제공. 현재 컴파일 진행 중이며 성공 판정 전이다.
- munch/evo/sophuspy 등 clone에 없는 의존성을 별도 환경에 설치 중.
- munch4/evo1.31.1/sophuspy1.2.0 및 Torch2.1-CUDA11.8용 torch-scatter wheel 설치 완료.
- VIGS 전용 rasterizer(기존3dgs와 별개 API)는 vigs3070에만 빌드/설치 진행 중.
- 원본 README의 Zenodo Omnidata depth/normal ckpt 다운로드 진행 중. 완료 전 로드 금지.
