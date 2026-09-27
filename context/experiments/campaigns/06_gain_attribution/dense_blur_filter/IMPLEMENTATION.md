# Dense quality admission implementation

## 데이터와 학습 경로

`OnlineMapperRuntime._offer_arrived_intervals()`는 현재 도착한 양쪽 training KF 사이의 dense 후보를 `DeferredDenseObservations.ingest()`에 전달한다. `dense_blur_filter`가 켜져 있으면 archive의 CPU RGB만 읽어 선명도를 검사하고, 통과한 UID만 deferred inventory에 기록한다. 이 inventory가 기존 trainer의 full dense pool로 전달된다.

- Tracking keyframe 선택·pose·depth·Gaussian birth는 변경하지 않는다.
- Dense 이미지의 선명도와 첫 admission 판정을 UID별로 캐시한다. Gaussian map reset으로 과거 블러 판정을 뒤집지 않는다.
- KF 승격은 별도 의미: 과거에 dense로 탈락한 UID도 frontend가 KF로 선택하면 KF loss에 사용될 수 있다. dense rejection은 tracking을 바꾸는 규칙이 아니다.
- 이미 관측한 오른쪽 KF까지의 RGB만 참조한다. 미래 RGB/pose나 held-out RGB는 점수·기준 계산에 쓰지 않는다.
- 점수 기준은 같은 구간 영상들의75분위다. 원본 중앙80% 영역을 최대384px로 축소해 Laplacian energy 및 Laplacian/gradient energy 비를 계산한다. 두 상대조건이 모두 낮을 때만 제외한다.
- CPU scalar cache만 추가하며, 탈락한 dense에는 pose 준비·GPU 이미지 캐시·학습 render가 발생하지 않는다. 원본 CPU sensor archive는 보존한다.
- accepted dense pool에서는 기존 full-pool cumulative ERVS가 그대로 작동한다. 선택 이후 optimizer는 여전히 영상별 Adam이다.

## 비교 계약

OFF/ON은 window:KF:dense=3:3:6이며, no-dense 대조군은3:9:0이다. dense에 쓰던 작업을 full-KF ERVS에 재배분하므로 총40 renders/KF와 최근 window 예산을 유지한다. 초기 pool 부족에 따른 실제 서비스 비율은 audit에 기록한다. 이 비교는 dense 관측을 KF 재학습으로 대체한 효과이며, 단순히 optimizer를 덜 돌린 경우와 다르다.

품질은 고정 held-out PSNR로 판단한다. 각 결과를2회 평가하지만, 이는 학습seed 반복 실험이 아니다. 실제 tracker 동시 실행과 strict live deadline은 이번 비교에 포함되지 않는다.

## 제한

모션 블러의 정답 classifier는 아니다. 질감 변화·노이즈·이미 흐린 구간 전체는 상대 선명도로 완전히 판별할 수 없다. 특히 제외0장이라면 그 실험의 PSNR 차이는 블러 필터링 효과로 해석하지 않는다. 장면별 threshold는 사용하지 않는다. 실제 사용 여부는 모든 비교 결과를 보고 결정한다.

## 실행 옵션

필터를 사용하지 않는 기존 기본 recipe는 그대로 유지한다. `online_mapping` 옵션에 아래 항목을 추가하면 선별이 활성화된다.

```json
"dense_blur_filter": {"energy_ratio": 0.8, "frequency_ratio": 0.9}
```

`true`도 동일한0.8/0.9 기본값으로 활성화하며, `false` 또는 생략은 OFF다. `0.5/0.75` 초기 보수적 기준도 명시적으로 재현할 수 있다. 두 수치는 장면마다 맞추는 값이 아니라 모든 장면 공통 실험 설정이다.

고정예산 재현 runner는 `--dense-blur-filter --blur-energy-ratio 0.8 --blur-frequency-ratio 0.9`를 지원한다. 필터는 선택 후보에만 적용되며, KF당40회 학습 예산과 dense/KF의 loss 정의는 변경하지 않는다.
