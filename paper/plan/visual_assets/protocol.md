# 공통 Figure / Table 비교·제작 규칙

작성 2026-10-01. 사용자 선택 목록의 공통 계약이며 새 실험의 결과가 아니다.

## 1. 세 종류의 비교

| 유형 | 고정하는 것 | 주로 연결할 항목 |
|---|---|---|
| 동일 work | 같은 인과적 입력 trace/평가 집합, 완료 image-render 수. Adam/추가 geometry 계산은 별도 기록 | T1, F3, T6 |
| 실제 동일 time | 실제 tracking+mapping, 동일 hardware/입력 재생/시간 허용 및 zero-tail | T2, F11, F12 |
| sampler/supervision isolation | 같은 코드·scene·pose/init·loss·topology·admission·budget 중 시험 변수만 변경 | T4/F9, T5 |

각 유형의 Ours−baseline 차이는 의미가 다르다. VIGS 시스템 전체와 다른 mapper의 품질 비교를 ERVS 단독 이득으로 해석하지 않는다.

## 2. Work 단위

- `training_render`: image 하나에 대한 학습용 render. batch 안의 각 image를 센다.
- `optimizer_step`: 성공적으로 완료한 Adam step. image 몇 개의 gradient를 모았는지 함께 기록한다.
- `geometry_extra_render`: D3 등 기하 감독용 추가 forward. training_render와 분리해 total cost에도 반영한다.
- `mapping_call` / packet / KF 하나는 위 세 단위와 같지 않다.
- caption에 정의하지 않은 mapping iteration 용어를 공통 예산의 단위로 사용하지 않는다.
- 40 renders/KF에서 KF 수가 다르면 총 renders가 다르다. 서로 다른 frontend 시스템의 동일-work 표에는 scene별 절대 budget을 맞출 방안이 필요하다.
- 현재 ours와 vanilla의 optimizer grouping을 그대로 두는 시스템 비교는 가능하지만 같은 Adam 횟수라고 쓰지 않는다.

## 3. Ours와 geometry

최종 사용할 code commit, config hash, data/split ID, tracker 설정, renderer, geometry 항을 고정한다.
현재 selected mapping recipe와 최신 D3 포함 live recipe를 구분한다. 원고 Carve/Hit, latest D3, 과거 opacity pruning은 서로 다른 조작이다.

F2의 기존 도식은 재사용하지만 최신 코드와 다른 설명은 검토한다. 최신 D3 PSNR을 Carve의 실증으로 사용하지 않는다.

## 4. 품질과 집계

- held-out PSNR/SSIM/LPIPS는 공통 camera cohort와 해상도, pose 정책, exposure 처리를 공유한다.
- dataset 평균: 각 scene의 held-out image 평균 → scene 간 동일 가중 평균. 길이가 긴 scene에 더 큰 가중치를 자동 부여하지 않는다.
- main 평균과 appendix sequence 값은 같은 경량 데이터에서 만든다. 같은 table 내 각 방법의 유효 scene 수와 공통 paired cohort를 표시한다.
- —=미측정, F=실행/추적 실패, NA=지표 적용 불가, NR=정한 구간 내 목표 미도달. 이들을 0으로 채우지 않는다.
- #Gaussians는 평가 checkpoint의 생존 primitive 수이며 기본 단위는 k. method별로 2D/3D primitive 차이가 있으면 각주로 공개한다. 적을수록 항상 우수하다고 순위화하지 않는다.
- seed 반복과 동일 저장 지도 재평가는 구분한다. 표준편차를 적으려면 독립 training run이 필요하다.
- 3dgs-custom 과거 replay의 test split은 llffhold-8이다. test.txt만 보고 평가 대상을 가정하지 않는다.

## 5. 시간축

1×=센서 구간 길이만큼 입력 시간을 허용. 1.5×=60초 데이터를 90초에 입력. 1.5배 빠른 재생이 아니다.
실행 시간 원점은 sensor release start로 고정한다. warm load, map initialization, GPU synchronization, evaluation, saving의 포함/제외를 기록한다.
중간 eval은 immutable snapshot으로 외부 수행하고, snapshot 저장이 live에 주는 overhead를 기록한다.
Mapper zero-tail과 tracker의 최종 처리 지연은 별개다. deadline 뒤 learning을 하지 않아도 실시간 tracking이 보장되지는 않는다.
현재 FIFO capacity2는 ordinary pending packet에 적용하고 reset/rescale/PGBA는 보호한다. 학습 full-history pool을 truncate한 실험이 아니다.
현재 live RPNG/UTMM의 tracker config 차이는 전체 시스템 비교에 공개한다. mapper-only 비교에는 같은 causal tracking trace가 필요하다.

## 6. Geometry

학습 depth와 독립적인 reference, 공통 관측 영역, 거리/opacity threshold를 정의한다. accuracy뿐 아니라 completeness/coverage도 보고한다.
학습 depth loss 또는 train PSNR 감소를 기하 정답의 증거로 대신하지 않는다. zero-opacity로 지도 전체를 지워서 얻는 free-space 점수 개선을 허용하지 않는다.

## 7. 파일 구조와 재현

- 항목별 `plan/CURRENT.md` → 생성 코드 scripts → 검토본 output → 검수한 current.
- Figure current: PDF/SVG/PNG, caption.md, provenance.json. Table current: TeX, preview, caption/provenance.
- 원본 실험 데이터는 `results/campaigns/...`에 두고 복제하지 않는다. 새로운 실험 문서/runner는 `context/experiments/campaigns/...`, `benchmarks/online_gs/campaigns/...` 규칙을 따른다.
- 생성 데이터에는 run ID, source/config hash, scene/view UID, checkpoint/work/time, source file/hash를 남긴다.
- 동일 crop/표시 범위, actual checkpoint, axis 단위, mean 일치 여부를 확인한 뒤 설치한다.
- 한국어 계획에 적힌 source availability와 실제 완성 상태를 구분한다. 2026-10-01부터 cvpr_assets campaign에서 실제 학습·held-out 평가·중간 지도 저장을 진행한다. 표의 정본 입력은 paper/results/tables/cvpr_endpoint_measurements.csv이며, 현재 T1/T2/F12만 측정값을 부분 반영했고 다른 자산은 아직 제작 단계다.
