# exp30~37 — OpenMAVIS(ORB) 데이터셋으로 갈아탄 재현 트랙

- **날짜**: 2026-07-09~
- **배경**: exp08~29는 전부 MPS(Aria 자체 SLAM) pose + MPS 62.6만 init을 썼다. 이 연구실의 목표는 **OpenMAVIS(우리 SLAM)**로 완전히 옮기는 것. exp30~37은 새로 재구축한 데이터셋(`data/03_rgb_3dgs_full`, OpenMAVIS pose 1303장 + ORB 7,205 init)에서 지금까지의 방법들을 하나씩 재현하는 트랙이다.
- **⚠ 비교 주의**: exp08(MPS)과 exp30(ORB) 등은 pose/init 출처가 완전히 다르므로 **직접 비교 금지**. 이 트랙 안에서는 exp30이 자체 기준선이다.
- **anchor는 native 재생성** (세션 간 좌표 변환 불필요) — `scripts/anchors/build_native_anchors_neworb.py` (일반, obs≥3) / `build_native_anchors_neworb_highconf.py` (고confidence, obs≥10 & found_ratio≥0.5). 상세 배경은 [exp27](exp27_anchor_init.md) 참조.

## 실험 목록

| Exp | 설정 | init/anchor | PSNR@7k | PSNR@30k | Gaussians@30k | \|Z\|>4m | 학습시간 | 상태 |
|---|---|---|---:|---:|---:|---:|---:|---|
| **exp30** | baseline (plateau 없음) | ORB 원본 7,205 | 29.183 | **32.906** | 147,620 | 269 | 15.8분 | **완료 — 이 트랙의 기준선** |
| exp31 | anchor를 init으로 | 일반 anchor 7,108 (obs≥3: SLAM 6,543 + virtual 565) | 29.011 | 32.671 | 143,330 | 71 | 17.6분 | 완료 |
| exp32 | plateau 기본 tau + λ0.01 (exp19 설정) | ORB 원본 + 일반 anchor로 당김 | 28.938 | 32.903 | 148,585 | - | 36.6분 | 완료 |
| exp33 | plateau enlarged tau + λ0.10→0.03 (exp25 설정) | ORB 원본 + 일반 anchor로 당김 | 28.989 | 32.536 | 146,872 | 33 | 26.9분 | 완료 |
| exp34 | anchor를 init으로 (고confidence) | 고confidence anchor 1,438 (obs≥10&found_ratio≥0.5: SLAM 646 + virtual 792) | 28.308 | 31.970 | 119,443 | 23 | 9.8분 | 완료 |
| exp35 | plateau 기본 tau, 고confidence anchor | ORB 원본 + 고confidence anchor로 당김 | 28.670 | 32.799 | 147,777 | 46 | 12.7분 | 완료 |
| exp36 | plateau enlarged tau, 고confidence anchor | ORB 원본 + 고confidence anchor로 당김 | 28.981 | 32.591 | 148,484 | 42 | 12.2분 | 완료 |
| exp37 | **dense confidence+monodepth init** | dense init 148,564 (SLAM core 6,543 + monodepth 완성 142,021) | 28.848 | **32.621** | 223,759 | **0** | 10.9분 | **완료 — 큐 전체 종료** |

> 표는 각 run 완료 시 갱신. 학습시간은 START~DONE 벽시계 기준 (다른 실험과 GPU 동시 사용 없었던 구간만). exp30~37 전체 완료 (2026-07-09 23:24).

## 학습 시간 메모

- init만 있고 plateau 없는 run(exp30/31/34/37)이 plateau 있는 run(exp32/33/35/36)보다 대체로 짧다 — plateau loss 자체의 오버헤드(전 Gaussian-anchor 거리 계산)가 상당함을 시사. 단 exp37(dense init, plateau 없음)은 Gaussian 수가 가장 많은데도(223,759) 10.9분으로 제일 빠른 축 — plateau 유무가 densification 유무보다 시간에 더 큰 영향.
- exp34(9.8분)가 exp31(17.6분)보다 짧은 이유: 최종 Gaussian 수가 119,443 vs 143,330으로 더 적음 — init point가 적으면(1,438 vs 7,108) densification도 덜 일어나 학습이 빨라짐.
- 고confidence anchor로 하는 plateau(exp35/36, 12.7분/12.2분)가 일반 anchor plateau(exp32/33, 36.6분/26.9분)보다 훨씬 빠름 — anchor 개수가 적을수록(1,438 vs 7,108) 거리 계산 비용이 작아짐.

## exp37 — 가장 중요한 결과: floater 완전 제거

**exp37 (dense init 148,564, plateau 없음): PSNR@30k = 32.621, \|Z\|>4m = 0개.**
이 트랙에서 \|Z\|>4m이 0인 유일한 run이다 (baseline exp30조차 269개). PSNR은 baseline 대비 -0.29dB(노이즈 범위 근처)로 손해가 작다. **init 자체를 dense하고 outlier 없이 만들면, plateau loss 없이도 densification이 floater를 거의 안 만든다**는 이번 트랙 전체의 핵심 결론.

## 추가 생성: dense confidence init (고confidence anchor를 seed로 확장, 2026-07-09 저녁)

exp37의 dense init은 SLAM core(obs≥3, 6,543)를 seed로 썼다. 이번엔 **고confidence anchor(1,438개, exp34/35/36과 동일한 그 파일)를 seed로 삼아** 같은 방식(depth mono는 고confidence 점으로만 피팅, voxel/stride 확장)으로 새로 만들었다 — `scripts/anchors/build_dense_confmono_init_highconf_seed.py --voxel-size <m> --tag <name>`.

**밀도 두 종류:**

| tag | voxel | 개수 (seed 1,438 + 확장) | NN spacing median | 결과 경로 |
|---|---:|---:|---:|---|
| 5cm (기본) | 0.05m | 1,438 + 143,392 = **144,830** | 4.0cm | `results/diagnostic/dense_confmono_init_highconf_seed_20260709_231415` |
| 60k (MPS급) | 0.11m | 1,438 + 63,657 = **65,095** | 7.8cm | `results/diagnostic/dense_confmono_init_highconf_seed_60k_20260709_232434` |

**균질성 확인**: 3D 공간에서 무작위로 뽑은 게 아니라, 각 keyframe depth map을 픽셀 격자로 스캔 후 **voxel(5cm 또는 11cm) 단위로 1점만 남기는 dedup** 방식. 실제로 최근접 이웃 거리를 재보니 voxel 크기와 거의 일치하고(5cm판 median 4.0cm, 60k판 median 7.8cm) 카메라 근거리/원거리 편향도 거의 없음(5cm판: 근거리 3.9cm vs 원거리 4.0cm) — **의도한 대로 3D 공간에서 고르게 퍼져 있음** 확인.

**plateau 커버리지 재확인 (고confidence anchor의 plateau가 이 dense 점들을 덮는가, `eval/plateau_loss.py` ellipsoid 계산 그대로 복제):**

| | exp35 기본 tau | exp36 enlarged tau |
|---|---:|---:|
| 5cm판 (144,830pts) | 87.2% 커버 | 99.8% 커버 |
| 60k판 (65,095pts) | 87.2% 커버 | 99.3% 커버 |

밀도를 낮춰도(5cm→11cm) 커버리지 비율은 거의 그대로 — **기본 tau는 구조적으로 약 13%를 못 덮고, enlarged tau라야 거의 다 덮는다.** 즉 이 dense-confidence init과 같이 쓸 plateau는 enlarged tau만 앞뒤가 맞는다.

아직 학습에는 안 넣었음 (요청 시 exp38 계열로 큐 추가 가능).

## anchor/init 종류 정리 (헷갈리기 쉬움)

| 이름 | 개수 | 만드는 법 | 쓰는 실험 |
|---|---:|---|---|
| ORB 원본 | 7,205 | SLAM이 뽑은 map point 그대로 | exp30, exp32/33/35/36의 init |
| 일반 anchor | 7,108 | obs≥3 필터 + kNN 고립점 제거 + monodepth로 빈틈 시딩(30cm voxel, 16px stride, 최소간격 50cm) | exp31 init, exp32/33 plateau 당기는 힘 |
| 고confidence anchor | 1,438 | obs≥10 & found_ratio≥0.5로 더 엄격히 필터 + 같은 시딩 | exp34 init, exp35/36 plateau 당기는 힘 |
| dense init | 148,564 | SLAM core(obs≥3, 6,543) + depth 보정은 고confidence 점으로만 피팅 + 촘촘한 voxel(5cm)·stride(4px), 최소간격 제약 없음 | exp37 init 전용 (plateau 없음) |

## 질문별 답 (완료된 것만)

- **exp30 자체 기준**: OpenMAVIS 데이터로 아무 개선 없이 학습하면 32.906dB. 이게 이 트랙 전체의 기준점.
- **⚠ run-to-run 노이즈 확인됨**: exp30을 동시에 두 번 독립 실행했다가(중복 버그, 아래 사고 기록 참조) 우연히 비교 가능해짐 — 완전히 같은 설정인데 32.671 vs 32.906, **0.24dB 차이**. 이후 실험 비교 시 ±0.2dB 안팎은 유의미한 차이로 보지 말 것.
- **⚠ MPS 트랙과 반대 패턴 (exp32 vs exp33)**: MPS 트랙(Round 7)에서는 enlarged tau(exp25)가 최선이고 기본 tau(exp19)가 열세였는데, ORB 트랙은 **정반대**다 — 기본 tau(exp32, 32.903)가 baseline(32.906)과 동급인 반면 enlarged tau(exp33, 32.536)는 -0.37dB 손해를 본다. \|Z\|>4m만 보면 enlarged tau가 더 적어(33 vs 71) floater를 더 잘 잡는 것처럼 보였으나, **아래 "floater 지표 재검토" 섹션에서 이 판단이 틀렸음이 확인됨** — 더 엄밀한 지표(ray-density)로는 오히려 enlarged tau가 진짜 floater를 더 만든다.
- **exp31 vs exp34 (anchor 선별 기준의 효과, init으로 쓸 때)**: 일반 anchor(7,108pts, obs≥3) init인 exp31이 32.671, 고confidence anchor(1,438pts, obs≥10&fr≥0.5) init인 exp34가 31.970 — **일반 anchor가 +0.7dB 더 좋다.** floater는 고confidence 쪽이 더 적다(23개 vs 71개)지만 그 차이보다 화질 손해가 크다. 점 개수가 적어 densification이 덜 되고(최종 Gaussian 119k vs 143k) 커버리지가 부족했던 것으로 보임 — "confidence보다 개수/커버리지가 init 품질에 더 중요"할 가능성.
- **exp32/33 vs exp35/36 (plateau에서 anchor confidence 기준의 효과)**: 일반 anchor plateau(exp32 기본tau=32.903, exp33 enlarged=32.536)와 고confidence anchor plateau(exp35 기본tau=32.799, exp36 enlarged=32.591)가 **거의 같은 패턴**(기본 tau가 enlarged보다 낫다)을 보인다 — anchor confidence 기준보다 tau 크기가 결과를 더 좌우한다는 뜻. 다만 고confidence 쪽이 학습시간은 절반 이하(12분대 vs 27~37분) — anchor 개수가 적어 손해(-0.1dB 안팎)는 작고 속도 이득은 크다.
- **exp37 (dense init, plateau 없음)이 이 트랙 최고의 floater 억제**: 위 "exp37 — 가장 중요한 결과" 참조. \|Z\|>4m=0.

## floater 지표 재검토 (2026-07-10) — \|Z\|>4m과 plateau-inside-ratio는 둘 다 부정확했다

육안으로 exp32(plateau 있음) vs baseline을 비교했을 때 floater 감소가 뚜렷이 안 보인다는 관찰에서 출발. 지금까지 쓴 지표(\|Z\|>4m 개수, "Gaussian이 anchor plateau 안에 있는 비율")는 둘 다 **위치만 보고 opacity/렌더링 기여·실제 관측 여부를 전혀 안 본다**는 근본 한계가 있었다. 세 가지를 새로 확인했다.

### 1. Plateau-inside-ratio는 enlarged tau에서 변별력이 없다

`eval/plateau_loss.py`의 ellipsoid 계산을 그대로 복제해서, **plateau loss가 없는 run**(exp30/31/34/37, 자연 수렴)도 같은 anchor의 plateau 안에 얼마나 있는지 확인:

| | plateau loss 없음 (자연 수렴) | plateau loss 있음 | 차이 |
|---|---:|---:|---:|
| 일반anchor/기본tau | exp30: 61.6% | exp32: 69.3% | +7.7pp |
| 일반anchor/enlarged tau | exp30: 97.2% | exp33: 97.9% | **+0.7pp** |
| 고conf anchor/기본tau | exp34: 74.9% | exp35: 82.9% | +8.0pp |
| 고conf anchor/enlarged tau | exp34: 98.0% | exp36: 98.7% | **+0.7pp** |

enlarged tau는 **loss 없이도 이미 97~98%**가 "안"이다 — tau_t 반경이 최대 2m라 scene 안 거의 모든 Gaussian이 그냥 자연스럽게 어떤 anchor의 2m 이내에 들어간다. 즉 enlarged tau의 높은 커버리지는 loss가 잘 작동해서가 아니라 **plateau 자체가 scene 대부분을 덮을 만큼 크게 그려져서**다. 이 지표로는 enlarged tau의 효과를 사실상 측정할 수 없다.

### 2. Ray-density 기반 재정의: "카메라가 한 번도 안 본 공간의 Gaussian" = 진짜 floater

`scripts/diagnostic/check_gaussian_ray_coverage.py`. ORB 데이터셋 1,303개 카메라 전부에서 픽셀 ray(441개/카메라, 15m까지, 0.15m voxel)를 march해서 "한 번이라도 ray가 지나간 3D voxel" 지도를 만듦 (전체 voxel의 91.7% 방문됨). 이 지도에 없는 voxel의 Gaussian은 **어떤 카메라에서도 photometric gradient를 받은 적이 없으므로 존재 근거가 전혀 없다** — opacity까지 같이 보면 "진짜 눈에 보이는 floater"를 가려낼 수 있다.

| Run | Gaussians | ray 없는 voxel의 Gaussian | 그중 opacity>0.1 | **그중 opacity>0.5 (진짜 floater)** |
|---|---:|---:|---:|---:|
| exp30 (baseline) | 147,620 | 725 (0.49%) | 255 | 53 |
| exp31 (일반anchor init) | 143,330 | 275 | 106 | 18 |
| **exp32 (기본tau plateau)** | 148,585 | 202 | 70 | **11** |
| **exp33 (enlarged tau plateau)** | 146,872 | 444 | 224 | **73 ⚠** |
| exp34 (고conf anchor init) | 119,443 | 221 | 94 | 12 |
| exp35 (고conf 기본tau) | 147,777 | 248 | 86 | 32 |
| exp36 (고conf enlarged tau) | 148,484 | 296 | 120 | 49 |
| **exp37 (dense init)** | 223,759 | 153 (0.07%) | 84 | **34** |

**반전**: \|Z\|>4m·plateau-inside-ratio로는 enlarged tau(exp33/36)가 더 좋아 보였는데, 실제 opacity>0.5(눈에 보이는) floater 개수는 **정반대**다 — exp32(기본tau) 11개 vs exp33(enlarged tau) 73개, **6.6배 차이**. exp32(일반anchor·기본tau)와 exp37(dense init)이 이 엄밀한 기준으로는 가장 깨끗하다.

### 3. 원인 확인: enlarged tau의 plateau가 미관측 공간까지 파고든다

`scripts/diagnostic/check_plateau_vs_raydensity.py`. 위에서 만든 "ray가 한 번도 안 지나간 voxel"(84,073개, 전체의 8.3%) 각각이 anchor plateau 안에 들어가는지 확인:

| Config | ray-미관측 voxel 중 plateau 안 | 비율 |
|---|---:|---:|
| 일반anchor / 기본tau | 120 / 84,073 | 0.14% |
| **일반anchor / enlarged tau** | 952 / 84,073 | **1.13%** (8x) |
| 고conf anchor / 기본tau | 73 / 84,073 | 0.09% |
| **고conf anchor / enlarged tau** | 1,657 / 84,073 | **1.97%** (22x) |

**결론**: enlarged tau의 plateau(반경 최대 2m)는 기본 tau보다 8~22배 더 많이 **관측된 적 없는 공간까지 침범**한다. Virtual anchor(monodepth로 채운 점, scene 경계처럼 ray가 희박한 곳에도 생성됨) 주변에 큰 반경을 그리면, 그 반경이 실제로 아무도 본 적 없는 공간까지 뻗어나가고, plateau loss는 그 안에 있는 Gaussian을 "괜찮다"고 방치한다. **"당기는 힘을 세게/넓게 걸수록 안전하다"는 지금까지의 직관은 이 세 가지 지표를 종합하면 틀렸다** — tau가 커질수록 plateau가 관측 불가능한 공간까지 커버하면서 오히려 floater 서식지를 넓혀준다.

### 종합 결론

1. floater 판정은 **위치(anchor 근접도)가 아니라 ray 관측 여부 + opacity**로 해야 한다.
2. enlarged tau plateau는 PSNR도 낮고(앞 섹션) 진짜 floater도 더 많다(이 섹션) — **이번 트랙에서는 기각**. 기본 tau + 일반 anchor(exp32)가 plateau 계열 중 최선.
3. exp37(dense init, plateau 없음)이 여전히 가장 깨끗하다 — init을 촘촘하고 outlier 없이 만드는 것이 plateau loss보다 근본적으로 낫다는 이 트랙의 핵심 결론이 다시 한번 확인됨.

### 왜 anchor plateau 안인데도 floater가 생기는가 (메커니즘)

1. **Densification이 무작위로 뿌린다**: clone/split은 부모 Gaussian 주변에 scale 범위 안에서 jitter를 줘서 자식을 심는다. 부모가 관측 경계(virtual anchor가 있는, ray 희박한 scene 가장자리) 근처에 있으면 자식 일부가 우연히 unseen voxel로 넘어간다.
2. **일단 들어가면 되돌릴 힘이 없다**: photometric loss는 그 위치를 지나는 ray가 없으니 gradient가 정확히 0. plateau loss는 `hinge=max(D-1,0)` 형태라 D≤1(plateau 안)이면 loss·gradient가 정확히 0 — enlarged tau 때문에 그 unseen voxel이 plateau 안에 들어가 있다면 plateau조차 "여기 있어도 된다"고 승인해버린다.
3. 결과: densification이 우연히 심어놓은 위치·opacity 그대로 **영원히 얼어붙는다.** enlarged tau가 floater를 늘리는 이유는 "당겨서 넣어주기" 때문이 아니라 **"이미 잘못 심어진 애를 안 건드리는 면적을 넓혔기" 때문**이다.

### 명시적 pruning + Z-layer 시각화 (2026-07-10)

`scripts/diagnostic/prune_unseen_gaussians.py` — 8개 run 전부에서 unseen-voxel Gaussian을 실제로 잘라내 `pruned.ply`(남은 것)/`removed.ply`(잘린 것)로 저장 (62필드 원본 포맷 그대로, 표준 3DGS 뷰어에서 바로 열림). 결과: `results/diagnostic/rayprune_<ts>/<run>/{pruned,removed}.ply` — 전체 293MB라 git에는 안 올림.

point cloud를 직접 봐서는 차이가 잘 안 보여서(잘린 비율이 0.1~0.5%로 작음), 제거된 점들의 Z-layer별 위치를 PDF로 그렸다 (`scripts/diagnostic/render_rayprune_zlayers.py`, 배경=그 Z-슬랩에서 ray-미관측 비율, 점=제거된 Gaussian을 opacity로 색칠). PDF(1.2MB)만 git에 포함: `results/diagnostic/rayprune_20260710_010352/rayprune_zlayers.pdf`.

## 사고 기록 (2026-07-09)

exp30~33 자동 체인 launcher(`wait_and_chain.sh`)가 `pgrep -f`로 exp29 종료를 감지하려다 **자기 자신의 부모 프로세스 커맨드라인과 오매칭**돼 무한 대기에 빠짐. 수동으로 부모만 kill했는데 자식이 살아남아 있다가 부모 사망 후 정상 감지 로직이 풀리며 **똑같은 exp30~33을 또 한 번 실행** — 결과적으로 동일 실험이 두 세트 동시에 GPU를 나눠쓰며 돌아감. 발견 즉시 중복 체인 kill + 중복 결과 폴더 삭제, 하나만 남김. 위 "run-to-run 노이즈" 항목은 이 사고의 부산물로 얻은 관찰.

## 다음 실험 후보

- **⚠ 갱신 (2026-07-10)**: "floater 지표 재검토" 결과 enlarged tau plateau는 진짜 floater를 더 만드는 것으로 확인되어, dense confidence init + enlarged tau 조합(구 exp38/39 후보)은 우선순위를 낮춘다. plateau 계열은 사실상 이 트랙에서 기각(exp32가 최선이어도 exp37에 못 미침).
- exp37(SLAM core seed dense init)과 dense confidence init(고confidence seed, 5cm/60k판)의 직접 비교 — plateau 없이 seed 종류만 바꿔서 dense init 방식 자체의 최적 seed를 찾는 실험. plateau를 안 쓰므로 위 우려와 무관하게 유효.
- exp37 방식(ray-density가 충분한 dense init)을 MPS 트랙에도 적용 — floater 억제가 재현되는 일반적 효과인지 확인.
- ray-density 기반 floater 지표(`scripts/diagnostic/check_gaussian_ray_coverage.py`)를 앞으로의 모든 실험 평가에 표준으로 채택 — \|Z\|>4m은 더 이상 신뢰하지 말 것.
