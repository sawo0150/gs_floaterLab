# exp48 — Incremental 3DGS: SLAM 청크를 warm-start로 받아 매핑

- 상태: **종결 (2026-07-16). vanilla 3dgs-custom 위 자체 incremental 구현은 근본 한계 확인 → 검증된 online baseline([exp49](exp49_photoslam_plan.md) Photo-SLAM)으로 이관.** 최종 도달 18.23dB(배치 상한 30.2dB 미달). 하단 "eval 스크립트 버그 발견" 섹션이 마지막 진단(진짜 벽은 저텍스처 영역 + windowed 구조 자체).
- 배경: [exp47](exp47_speed_track_plan.md)에서 배치(full-scene) 학습 속도를 66분→26.8분(cheapcarve, S2)까지 줄였으나, 남은 고정비의 상당수(~13분, carve field 통짜 빌드 + 전체 프레임 로드)가 **incremental에서는 애초에 존재하지 않는 비용**임을 인지 — warm-start면 매 청크 재학습이 아니라 이어서 학습이므로. 배치 트랙에서 더 쥐어짜는 것은 "실제로 안 겪을 비용"을 상대로 최적화하는 셈이라 판단, incremental(exp48)로 직행하기로 결정.

## 재프레임: SLAM의 "실시간성"과 GS의 "incremental성"을 분리한다

최종 목표는 "Aria 라이브 IMU+이미지 스트림 → OpenMAVIS 라이브 SLAM → GS가 결과를 받아 매핑"이지만, 이걸 한 번에 다 만들 필요는 없다. OpenMAVIS는 이미 매핑 결과를 파일로 export하고 있으므로(`data/02_openmavis_output/orb_export/*.jsonl`), **완주된 SLAM 결과를 keyframe 구간별로 잘라 "마치 실시간으로 들어온 것처럼" 순차 공급**하면, OpenMAVIS를 라이브로 만드는 작업을 통째로 미루고도 GS 쪽 incremental loop(warm-start + 청크별 init + 학습)만 먼저 검증할 수 있다.

| Phase | 내용 | OpenMAVIS 변경 | 이번 계획 범위 |
|---|---|---|---|
| **0 (이번 대상)** | 기존 1253 SLAM export를 청크로 잘라 재생 → GS 쪽 warm-start loop 검증 | 없음 | ✅ 상세 설계 |
| 1 | Phase 0에서 검증한 청크 인터페이스를 OpenMAVIS가 실시간으로 직접 emit하도록 C++ export 확장 | 있음 (C++) | 방향만 기록 |
| 2 | Aria 라이브 IMU+이미지 스트림을 OpenMAVIS에 직접 연결 | 있음 (하드웨어 연동) | 미착수 |

## Phase 0 스코프 (오늘 확정)

**목표**: 품질/먼지는 안 본다 — warm-start 루프가 청크를 여러 번 거치며 안 죽고 끝까지 도는지, gaussian 수가 청크마다 늘어나는지, 즉 **배관이 뚫려 있는지**만 확인한다.

| 항목 | 결정 | 근거 |
|---|---|---|
| 대상 장면 | **301_1253** | region GT·self-diagnosis 규칙 등 기존 검증 도구가 가장 많이 맞춰져 있어 배관 검증에 집중할 때 잡음이 적음 |
| 청크 재생 소스 레벨 | **raw SLAM export(jsonl) 단위** | `orb_export/{keyframes,map_points,observations}.jsonl`을 kf_id로 슬라이스. Phase 1에서 OpenMAVIS가 실시간으로 emit할 형식과 동일해서 그대로 재사용 가능 (완성된 `03_rgb_3dgs_full` 데이터셋을 자르는 것보다 미래 호환성이 높음) |
| carve loss | **제외** | 순수 photometric + densify만으로 먼저 배관 검증. floater 억제는 배관이 확인된 다음 단계에서 추가 |
| anti-drift(옛 영역 보호) | **제외** | 이번엔 "새 청크 학습이 옛 영역을 망가뜨리는지"조차 측정 안 함 — 진짜 새 리스크지만 다음 단계 |
| 평가 하네스 | **제외** | region GT 등 정량 평가는 다음 단계. 이번엔 렌더가 안 무너지는지 육안 확인 정도 |
| 청크 크기(keyframe 수) | **1 keyframe = 1 청크로 확정** (2026-07-15 밤) | "keyframe 들어올 때마다 update"라는 실제 incremental 모델과 가장 직결. 1253은 keyframe 57개라 **총 57회 갱신 사이클**. 배칭(N개 keyframe씩 묶기)은 나중에 속도 최적화가 필요해지면 검토 |
| 이미지 소스 | **keyframe만 사용, RGB 보간(1,303장)은 후속 단계로 연기** | 아래 "청크 재생 설계" 참조 — DB 밀도(장면당 이미지 수) 부족 우려는 있으나 Phase 0은 배관 검증이 목적이라 우선 최소로 시작, 밀도 확장은 별도 후속 작업으로 분리 |
| 실행 순서 | **Phase 0a(2청크 예비검증) → Phase 0b(57청크 전체 루프)** | "체크포인트 재개+추가 init pcd"라는 신규 코드 경로가 검증 안 된 상태라, 2청크짜리 최소 테스트로 그 경로만 먼저 확인 후 전체로 확장 (사용자 결정) |

## 아키텍처: 어디에 무엇을 만드는가

| 위치 | 역할 | 변경 필요 여부 |
|---|---|---|
| **OpenMAVIS** (`SLAM_custom/OpenMAVIS`) | SLAM 본체 | Phase 0에서는 **불필요** — 이미 끝난 export를 재생만 함 |
| **gs_floaterLab** (이 repo) | 청크 재생 + 오케스트레이션 루프 소유 | ✅ 신규 — `scripts/incremental/` 폴더 (기존 `scripts/{pipeline,experiments,diagnostic,analysis,anchors}/` 분류 체계에 추가) |
| **3dgs-custom** (`26-1_RPM/gsProjects/3dgs-custom`) | 트레이너 | ✅ 최소 확장 필요 (아래 참조) — SLAM/청크/스케줄링 개념은 전혀 모른 채로 유지 |

**새 repo는 만들지 않는다.** gs_floaterLab이 이미 `scripts/pipeline/full_traj_to_rgb_3dgs.py`로 "SLAM 출력→GS 입력" 브릿지 역할을 하고 있고 `repos/main/`으로 OpenMAVIS·3dgs-custom을 심링크해 두고 있어, 그 역할을 확장하는 편이 4번째 코드베이스를 새로 두는 것보다 관리 비용이 낮다. (`orb_gs_bridge`가 원래 이 역할을 노렸던 이름이지만 지금은 잡다한 결과물 창고가 되어버렸음 — 오늘 세션에 12G 정리함)

## 청크 재생 설계 (2026-07-15 밤 갱신 — 사용자 결정 반영)

### 원본 스키마 확인 (`data/02_openmavis_output/orb_export/`, 1253 기준)

| 파일 | 줄 수 | 핵심 필드 |
|---|---:|---|
| `keyframes.jsonl` | 57 | `image_id, kf_id, frame_id, timestamp_s, timestamp_ns, image_name, slam_camera_id, Tcw, Twc` |
| `map_points.jsonl` | 7,205 | `map_point_id, xyz, observations, found_ratio, descriptor` |
| `observations.jsonl` | 44,230 | `image_id, kf_id, timestamp_ns, map_point_id, keypoint_idx, camera_id, u, v, octave` |

- pose convention: `Tcw_world_to_slam_cam0`, raw Atlas world (MPS world 아님 — `pitfalls.md` 좌표계 주의사항과 동일 계열).
- **1 keyframe = 1 청크** — 1253 기준 총 **57회 갱신 사이클**.

### ⚠ 확인 필요 — keyframe 이미지는 SLAM 추적용이지 RGB 학습용이 아님

`keyframes.jsonl`의 `image_name`(예: `3814770023750.png`)이 가리키는 실제 파일은 `data/01_euroc_openmavis_input/mav0/cam0/data/`에 있는데, 이건 **SLAM 추적용 흑백 fisheye624 스테레오 카메라(cam0/cam1) 이미지**다. 3DGS 학습엔 이게 아니라 **별도 Aria RGB 카메라 스트림**이 필요하다 (`full_traj_to_rgb_3dgs.py`가 `f_aria_301_1253_rebuild.txt` 전체-프레임 pose를 인접 keyframe 사이로 보간해서 `data/03_rgb_3dgs_full`의 1,303장 RGB 프레임 pose를 만드는 이유가 이것 — RGB 카메라는 SLAM 카메라와 다른 센서라 별도 pose 계산이 필요함).

**제안하는 Phase 0 방식** (사용자 확인 요청): 매 keyframe마다 **전체 궤적 보간 대신, 그 keyframe timestamp에 가장 가까운 RGB 프레임 1장만 골라서** keyframe의 Tcw를 (기존 파이프라인이 쓰는 RGB 카메라 extrinsic으로) 그 순간의 RGB 카메라 pose로 변환해 사용한다. 즉:

```
1 keyframe = 1 청크 = { 그 keyframe 시점에 가장 가까운 RGB 프레임 1장 + 그 시점 pose + 그 keyframe이 새로 얻은 map point들 }
```

이러면 57개 keyframe → 57장의 RGB 이미지만 있는 극단적으로 희소한 데이터셋이 되지만(Phase 0 목표가 배관 검증이라 이걸로 시작), `full_traj_to_rgb_3dgs.py`의 "전체 궤적 보간" 로직을 이번 단계에선 **전혀 안 씀** — 훨씬 단순.

**후속 작업으로 분리 (사용자 지시)**: "원하는 만큼 이미지 수(DB 밀도)가 안 나올 것"이라는 우려는 맞음 — 나중에 각 청크의 keyframe 구간 안에 있는 RGB 보간 프레임들(현재 `03_rgb_3dgs_full`가 만드는 방식)을 추가로 채워 넣는 **"프레임 밀도 확장" 후속 작업**을 별도로 계획한다 (Phase 0 성공 이후, 아래 실행 순서 참조).

### 제안하는 chunk manifest 스키마 (신규)

```json
{
  "chunk_id": 3,
  "kf_id": 30,
  "keyframe": {/* keyframes.jsonl의 해당 한 줄 */},
  "new_map_points": [/* map_points.jsonl 서브셋: 이 keyframe에서 새로 triangulate된 점만 */],
  "rgb_frame": {"image_name": "...", "pose": "..."},
  "prev_checkpoint": "results/experiments/exp48_.../chunk_002/ckpt.pth",
  "cumulative_map_point_count": 4120
}
```

### 데이터 레이아웃 (제안)

```
data/scenes/301_1253/04_incremental/
  chunk_000/  (images/ 1장, sparse/0/points3D.txt, cameras.json — 그 keyframe만의 미니 COLMAP 데이터셋)
  chunk_001/
  ...
  manifest.json  (또는 chunk별 manifest 파일)
```

기존 `03_rgb_3dgs*` 명명 관례를 따라 `04_incremental`로 번호를 이어감.

## 3dgs-custom에 필요한 최소 확장 (코드 확인 완료, 미구현)

`gaussian_model.py`/`train.py`를 읽어 확인한 결과, **현재 구조로는 "체크포인트 재개 + 새 청크의 init 점 추가"가 안 된다**:

- `Scene.__init__`이 데이터셋의 `points3D.txt`로 `create_from_pcd()`를 부르는 것과, `--start_checkpoint`로 `gaussians.restore()`가 학습 상태를 통째로 덮어쓰는 것은 **서로 다른 경로**다.
- `restore()`가 불리면 체크포인트의 Gaussian 파라미터로 완전히 대체되므로, 새 데이터셋 디렉토리에 새 청크의 init 점을 넣어놔도 **무시된다** (현재는 냉시작 아니면 온전 재개, 둘 중 하나뿐).
- 필요한 새 기능: **"기존 체크포인트를 복원하면서, 동시에 새 pcd의 점들을 추가로 seed"** 하는 경로. 예: `--extra_init_points <points3D.txt path>` 같은 플래그 — `restore()` 이후 `create_from_pcd`의 일부(신규 xyz/color/scale/opacity 초기화)만 호출해 기존 텐서에 concat.
- chunk_000(첫 청크)은 체크포인트가 없으니 기존 냉시작 경로 그대로 사용 — 이 확장은 chunk_001부터만 필요.

이 확장 하나가 Phase 0에서 3dgs-custom에 손대야 하는 **유일한 코드 변경**이 될 것으로 보임 (SLAM/청크 개념은 여전히 모른 채, "체크포인트+추가 pcd"라는 범용 기능만 가짐).

## 오케스트레이션 루프 (의사코드 수준, gs_floaterLab 신규 스크립트)

```
for kf_id in keyframes(1253):  # chunk_size = 1 keyframe
    build chunk_{kf_id} 미니 데이터셋 (해당 keyframe 시점 최근접 RGB 프레임 1장 + 그 keyframe이 새로 얻은 map point만)
    if kf_id == 0:
        train.py --source_path chunk_000_dir  (냉시작)
    else:
        train.py --source_path chunk_{kf_id}_dir --start_checkpoint <chunk_{kf_id-1} ckpt> --extra_init_points chunk_{kf_id}_dir/sparse/0/points3D.txt
    save checkpoint → 다음 청크가 참조
    (Phase 0: 육안 렌더 확인만. 정량 평가는 다음 단계)
```

## 실행 순서 (2026-07-15 밤 확정)

1. **Phase 0a — 2청크(2 keyframe) 최소 검증**: 신규 코드 경로("체크포인트 재개 + 추가 init pcd")가 실제로 동작하는지만 확인. kf_id 0(냉시작) → kf_id 1(재개+추가init) 단 2사이클.
2. **Phase 0b — 57청크 전체 루프**: 0a 통과 시 1253의 keyframe 57개 전체를 순회. 성공 기준은 아래.
3. **carve loss + anti-drift 추가 (가칭 exp48b, Phase 0b 성공 직후 바로 착수)**: Phase 1(OpenMAVIS 실시간화)보다 먼저, GS 쪽 loop가 검증된 상태에서 floater 억제·옛 영역 보호를 붙임.
4. **프레임 밀도 확장 (후속, 시점 미정)**: keyframe 1장뿐이던 각 청크에 그 구간의 RGB 보간 프레임들(`03_rgb_3dgs_full`식)을 추가해 DB 밀도를 원하는 만큼 올림.
5. **Phase 1 — OpenMAVIS 실시간 export화** (C++, 별도 트랙).

## Phase 0 성공 기준 (품질 무관, 기계적)

1. 청크 전체(0a=2개, 0b=57개)가 크래시 없이 순차 완주
2. gaussian count가 청크를 거치며 단조 증가(혹은 최소한 붕괴하지 않음)
3. 마지막 청크 렌더가 육안으로 명백히 깨지지 않음 (완전히 무너진 기하가 아님)
4. checkpoint-resume이 매 청크 정상 작동 (버퍼 크기 불일치 크래시 없음 — `pitfalls.md`의 기존 checkpoint-resume 버그 재발 여부 체크)

## 미결 사항 (2026-07-15 밤 — 1~4 해결, 신규 1건만 남음)

1. ~~청크 크기~~ → **해결**: 1 keyframe = 1 청크, 총 57사이클.
2. ~~예비 테스트 vs 전체 루프~~ → **해결**: Phase 0a(2청크)로 신규 코드 경로 먼저 검증 후 Phase 0b(57청크) 확장.
3. ~~chunk_000 init 방식~~ → **해결**: "keyframe 들어올 때마다 update" 모델이라 자연히 냉시작(kf_id 0) → 재개(kf_id 1~)로 통일됨. 별도 특수 케이스 아님.
4. ~~carve/anti-drift 위치~~ → **해결**: Phase 0b 성공 직후 바로 착수 (exp48b), Phase 1과 묶지 않음.
5. **(신규, 확인 필요) 이미지 소스 해석** — "청크 재생 설계" 절의 "⚠ 확인 필요" 참조: keyframe timestamp에 가장 가까운 RGB 프레임 1장 + keyframe pose를 RGB 카메라 extrinsic으로 변환해서 쓰는 방식으로 이해했는데, 맞는지 확인 부탁.

## 연결

- 전신: [exp47](exp47_speed_track_plan.md) (배치 속도 트랙, cheapcarve/keyframe subset 발견은 "프레임 밀도 확장" 이후 청크당 학습 예산 튜닝에 재사용 예정)
- 품질 방법론(carve·hybrid init)은 exp48b(Phase 0b 직후)에서 그대로 가져다 씀

## Phase 0b 전체 루프 완주 결과 (2026-07-15 완료)

- **설정**: 1253 keyframe 57개 전체 사이클, 청크당 200 iterations씩 누적 warm-start 학습.
- **총 소요 시간**: 약 17분 (청크당 평균 ~18초)
- **버그 발굴 및 수정 3건** (Phase 0a→0b 전환 과정에서 코드 리뷰를 통해 전부 수정):
  1. **🔴 계보 버퍼 리셋 방지**: `capture()`/`restore()`에 `ancestor_idx`, `birth_step`, `accum_visibility` 등 9종 트래킹 버퍼를 포함시켜 체크포인트 재개 시 학습 이력이 보존되도록 수정.
  2. **🟡 PCD 더블 로딩 제거**: chunk≥1에서 `points3D.txt`는 3점짜리 더미로 교체하고 실제 신규 맵 포인트는 `extra_points3D.txt`로 분리 공급.
  3. **🔴 cameras_extent=0 프루닝 버그 (chunk_015 크래시 원인)**: 단일 카메라 청크에서 `getNerfppNorm()`이 `radius=0.0`을 반환 → 3,000 iter를 넘는 순간 모든 Gaussian이 `0.1 * 0 = 0` 기준 미달로 전량 Prune되는 치명적 버그. `radius == 0.0`일 때 `3.0`으로 fallback 처리하여 해결.
- **Gaussian 개수 궤적 (주요 구간)**:

| Chunk | Gaussian 수 | 비고 |
|---|---|---|
| 000 | 405 | 냉시작 |
| 001 | 899 | |
| 007 | 3,423 | |
| 014 | 8,901 | |
| 015 | 9,428→7,232 | opacity_reset 발동(정상), 이후 반등 |
| 027 | 11,845 | |
| 037 | 18,670 | densify 가속 구간 |
| 047 | 35,052 | |
| 056 | **~52,000** | 마지막 청크 (렌더링 검수 완료) |

- **성공 기준 4개 모두 충족**:
  1. ✅ 57개 전 청크 크래시 없이 순차 완주
  2. ✅ Gaussian 수 전반적 단조 증가 (opacity_reset 등에 의한 일시 감소 후 복구 포함)
  3. ✅ 마지막 청크(chunk_056) 렌더링 163개 뷰 정상 완료
  4. ✅ 매 청크 checkpoint-resume 정상 작동 (버퍼 불일치 크래시 없음)

**→ Phase 0b 성공. 다음 단계: exp48b (carve loss + anti-drift 추가)로 진행.**

## Phase 0a 예비 검증 결과 (2026-07-15 완주)

- **설정**: 1253 keyframe 2개 (kf_id 0, 11) 대상, 청크당 200 iterations 학습.
- **결과**:
  - `chunk_000` (kf_id 0): 냉시작(scratch)으로 초기화 및 학습 완료. 200 iter 후 checkpoint (`chkpnt200.pth`) 및 **405** 가우시안 생성.
  - `chunk_001` (kf_id 11): `chkpnt200.pth` 기반 warm-start로 가우시안 파라미터 복원 후, 신규 keyframe 11이 관측한 **494개 신규 PCD 포인트**를 `--extra_init_points` 옵션으로 주입.
  - `add_extra_points` 동작 검증: optimizer 상태 텐서 및 10종의 tracking buffer(opacity, ancestor_idx, birth_step, num_splits, num_clones 등)가 $405 + 494 = 899$ 크기로 크래시 없이 성공적으로 Concatenate되어 확장됨.
  - **최종 검증 성공**: 가우시안 총 **899개**로 단조 증가하며 크래시 없이 학습 완주. 배관 동작성을 완벽히 확인하여 **Phase 0b (57청크 전체 루프)** 런칭 준비가 완료됨.
  - 독립 검증 완료: `gaussian_metrics/iteration_200.json`(405)·`iteration_400.json`(899)을 직접 열어 manifest의 신규 포인트 수(405·494)와 정확히 일치함을 재확인. `build_incremental_chunks.py`의 pose 변환식(`T_rgb_worldRaw = inv(T_worldRaw_cam0 @ T_c0_rgb)`)도 수식 검산 완료, RGB 프레임 매칭 오차 0.08ms.

## 코드 리뷰 발견 사항 (2026-07-15 밤, Phase 0b 전 수정 필요)

Phase 0a 결과 자체는 정확하지만, 코드를 뜯어보니 **exp48b(carve 붙이는 다음 단계)에서 바로 터질 문제 1건**과 경미한 사항 2건을 발견함.

### 🔴 발견 1 (중요, Phase 0b 전 수정 권장) — 계보/계측 버퍼가 매 청크마다 옛 gaussian 것까지 통째로 0 리셋됨

- **위치**: `3dgs-custom/train.py:134-144`
- **증상**: 체크포인트 재개+`add_extra_points()` 이후, `accum_rgb_grad`/`accum_visibility`/`birth_step`/`generation`/`num_splits`/`num_clones`/`ancestor_idx` 중 크기가 `_n`과 안 맞는 게 있으면 **통째로 새 0-텐서로 교체**하는 안전장치가 있음. `add_extra_points()`가 자체적으로 `torch.cat`해서 늘려놓긴 하지만(`gaussian_model.py:282-291`), `Scene()`이 restore() 전에 chunk_i 자신의 pcd로 먼저 `create_from_pcd`를 호출했다가(뒤에서 restore가 덮어씀) 버려지는 과정에서 버퍼 크기가 어긋나 이 안전장치가 거의 매번 발동함.
- **결과**: 최종 개수(899)는 맞지만, kf_id 0에서 태어난 405개 gaussian의 `accum_visibility`·`birth_step`·`generation`·`num_splits`도 kf_id 11 청크 시작하자마자 **0으로 리셋됨** — 옛 gaussian의 학습 이력이 매 청크 경계마다 소실.
- **왜 지금 고쳐야 하나**: Phase 0(품질/carve 제외)엔 무해하지만, exp48b에서 carve loss의 예산 prune이 `accum_visibility`를 "기여도" proxy로 쓰는데(round8 설계), 이대로면 워밍스타트 직후 멀쩡한 옛 표면 gaussian이 "방금 태어난 애=기여 0"으로 오판되어 **carve가 옛 표면을 잘못 지울 위험**이 있음.
- **수정 방향**: 버퍼는 청크 경계에서 보존하고 새로 추가된 점 구간만 0으로 append — `add_extra_points()`의 `torch.cat` 로직이 사실 올바른 방향이므로, train.py의 "크기 불일치 시 통째로 리셋" 안전장치가 **오히려 그 위에 덮어써서 무효화**하는 게 문제. 안전장치를 "크기가 안 맞으면 에러/경고"로 바꾸고, `Scene()`의 create_from_pcd→restore 덮어쓰기 과정에서 애초에 버퍼 크기가 어긋나지 않도록(예: restore 전에는 create_from_pcd를 아예 스킵하거나, 최소 1점짜리 더미 pcd로 초기화) 근본 원인을 손보는 게 필요.

### 🟡 발견 2 (경미, 정합성엔 무해) — 같은 points3D.txt를 두 번 읽음

- **위치**: `scripts/incremental/run_exp48_incremental.py:91,106`
- **증상**: `--source_path`(Scene 초기화용)와 `--extra_init_points`가 같은 파일(`chunk_dataset_path/sparse/0/points3D.txt`)을 가리킴. `create_from_pcd()`가 그 점들로 한 번 초기화했다가 `restore()`가 통째로 덮어써서 버려지고, `add_extra_points()`가 같은 파일을 또 읽어 진짜로 추가함 — 최종 결과는 중복 없이 맞지만(확인함) KNN(`distCUDA2`)이 같은 점 집합에 두 번 도는 낭비가 있음.
- **수정 방향**: chunk_i≥1의 `--source_path`용 데이터셋엔 빈/더미 `points3D.txt`를 쓰고, 실제 신규 점은 `--extra_init_points` 경로 하나로만 공급 (발견 1의 근본 수정과 자연히 같이 해결될 가능성 높음).

### 🟡 발견 3 (설계 확인 필요) — `densify_until_iter`가 매 청크 갱신되어 densify가 사실상 영원히 안 꺼짐

- **위치**: `scripts/incremental/run_exp48_incremental.py:94` (`--densify_until_iter target_iterations`)
- **증상**: 배치 레시피는 densify를 초반 7k/30k에서 끄는데, 여기선 매 청크마다 `densify_until_iter`가 그 청크의 누적 목표 iteration으로 계속 밀려 올라가 57청크 내내 densify가 켜져 있게 됨.
- **판단 필요**: Phase 0 짧은 burst엔 무해했지만, exp48b에서 옛 영역이 계속 densify로 흔들릴 수 있는 지점 — 의도적 설계인지 재검토 필요.

### 🟢 미확인 — 성공 기준 3번(육안 렌더 확인) 실제로는 미실시

렌더 이미지 파일이 결과 폴더에 안 남아 있어 "마지막 청크 렌더가 안 깨졌는지" 육안 확인은 아직 안 된 상태. loss는 정상 감소(chunk_000 0.158→0.104, chunk_001 0.176→0.083), NaN 없음 — 프로그램적으로는 건강해 보이나 시각 확인은 별도로 필요.

### Phase 0b 실제 재검증 결과 — "완료" 판정 철회 (2026-07-15 밤, 사후 검증)

위 발견 사항들을 기록한 직후, Phase 0b 카드에 적힌 "✅ 마지막 청크(chunk_056) 렌더링 163개 뷰 정상 완료"를 직접 렌더+수치로 재검증함 (`render.py --source_path data/03_rgb_3dgs_full --eval --skip_train`로 163개 held-out 뷰 렌더 후 픽셀 단위 PSNR 계산).

**결과: 평균 PSNR 15.8dB.** 이 프로젝트 챔피언 레시피(32~35dB) 대비 사실상 미학습 수준. 직접 이미지 2장(00000, 00080)을 열어보니 방 형태를 알아볼 수 없는 긴 바늘 모양 아티팩트로 뒤덮여 있었음. 반면 마지막 인덱스(00161·00162)는 GT와 픽셀 차이 평균 3.7/255로 거의 완벽했는데, PSNR이 index 158→162로 19.8→22.4→25.6→30.8로 매끈하게 치솟는 패턴은 "일반화"가 아니라 **마지막 청크가 방금 직접 학습한 시점 근처라 우연히 겹친 유출(leakage)**로 판단.

**원인**: Phase 0(0a·0b)은 "1 keyframe = 1 이미지, 다시는 재방문 안 함" 구조라 각 영역이 딱 1번 200 iter 학습받고 영원히 방치됨 — 장면의 97%가 사실상 미학습. **"Phase 0 성공 기준 4개 중 1·2·4(크래시 없음·개수 증가·체크포인트 정상)는 맞지만, 3(렌더 안 깨짐)은 틀렸다.** "프로세스가 안 죽었다"와 "결과가 정상이다"를 혼동한 게 원인 — 앞으로 품질 관련 성공 기준은 반드시 held-out PSNR 수치로 검증하고 프로그램적 완주만으로 판정하지 않는다.

## v2 재설계 및 품질 조사 (2026-07-16)

### 구조 정리: train.py 원복 + train_incremental.py 신설

exp01~47이 검증한 `train.py`(배치 트레이너) 경로가 incremental 전용 로직으로 오염되지 않도록, `--extra_init_points`/`add_extra_points` 호출부와 CLI 인자를 train.py에서 전부 제거하고 원래 모습으로 복원함 (문법 체크 통과). 버퍼 안전장치(체크포인트 재개용, exp45c에서 이미 쓰인 범용 기능)는 범용 확장이라 그대로 둠.

incremental 전용 오케스트레이션은 신규 파일 `3dgs-custom/train_incremental.py`가 전담. `Scene()`을 통째로 안 쓰고 하위 레벨 함수(`sceneLoadTypeCallbacks`/`cameraList_from_camInfos`)만 직접 호출해 "이미 존재하는 gaussians에 새 카메라·점을 이어붙이는" incremental 루프를 구현. 핵심 메커니즘(VINGS-Mono_custom 분석에서 이식):
- **로컬 윈도우 샘플링**: 매 iteration 카메라를 그 청크 하나가 아니라 `deque(maxlen=window_size)`에 쌓인 최근 keyframe들의 카메라 풀에서 무작위로 뽑음.
- **freeze-when-stable**: 이벤트당 `accum_rgb_grad` 증가분이 임계값 미만이면 stable 승격, 이후 gradient를 0으로 밀어 업데이트에서 제외 (이번 라운드 실험들은 전부 `stable_grad_thresh=-1`로 꺼서 격리 검증).

### 실험 1~4: 구조를 바꿔도 15~17dB 천장에서 안 움직임

| # | 설정 | 총 iteration | 최종 N | 평균 PSNR(163뷰) |
|---|---|---:|---:|---:|
| 1 | keyframe-only(1장/청크), window=15, iters=100 | 5,700 | 7,205 | 16.7dB |
| 2 | keyframe-only, window=15, **iters=300**(3배) | 17,100 | 7,205 | 16.3dB |
| 3 | **dense frame**(청크당 평균 23장, `build_dense_incremental_chunks.py` 신규), window=5, iters=150, densify 없음 | 8,550 | 7,205 | 16.3dB |
| 4 | dense frame, window=5, iters=150, **densify 켬**(cameras_extent 고정값 사용) | 8,550 | **123,621**(17배) | **15.7dB**(오히려 하락) |

**dense frame 통합**: `build_dense_incremental_chunks.py` 신규 작성. keyframe끼리만 보간하면 오차가 커지므로, `data/03_rgb_3dgs_full`이 이미 갖고 있는 정확한 보간 pose(dense per-frame trajectory로 slerp/lerp한 결과, `full_traj_to_rgb_3dgs.py` 산출물)를 keyframe timestamp 구간으로 나눠 재사용 — pose 재계산 없이 심링크+images.txt 서브셋만 생성. 1,303장이 57개 청크에 평균 23장씩 정확히 분배됨(검증 완료).

**densify 재도입**: 카메라 여러 대짜리 dense 청크 덕분에 발견 3의 `cameras_extent=0` 버그가 자연히 해소되는 걸 확인 후 `densify_and_prune`/`reset_opacity`를 `train_incremental.py`에 복원(`densify_from_iter/until_iter/densification_interval/opacity_reset_interval`은 `opt`의 기존 `OptimizationParams` 그대로 재사용, `--cameras_extent_source`로 scene extent를 replay 전체 궤적에서 고정값으로 계산). GaussianModel의 9종 트래킹 버퍼는 `densify_and_split/clone/prune_points`가 이미 정합적으로 처리(exp32 lineage 작업에서 검증된 기존 코드) — 이 스크립트가 로컬로 관리하는 `stable_mask`만 별도로 재정렬.

윈도우 방식, 프레임 밀도, densify 여부 — **큰 구조를 세 번 갈아엎었는데도 결과가 15~17dB 범위에서 거의 안 움직임.** 심지어 densify로 gaussian이 17배 늘어도 하락. 이 일관성 자체가 "뭔가 공통 원인이 있다"는 신호로 판단.

### 결정적 통제 실험: "iteration 부족"이 아니라 "windowed 구조 자체"가 원인

같은 데이터셋·같은 총 iteration(8,550)을 **원본 train.py로, incremental 로직 전혀 없이** 그냥 배치로 돌려서 비교:

| | 평균 PSNR | PSNR>25인 뷰 | 최저 |
|---|---:|---:|---:|
| **통제(원본 train.py, 전체 씬 동시 접근)** | **30.2dB** | 158/163 | 23.3dB |
| incremental (4개 변형 전부) | 15~17dB | 9~17/163 | ~10.5dB |

**결론: 8,550 iteration은 충분하다 — 전체 씬에 동시에/골고루 쓰일 때만.** "총 학습량 부족" 가설은 기각. 문제는 순수하게 windowed/순차적 구조 자체.

### 유력 원인: `reset_opacity`가 윈도우에서 빠진 영역을 영구히 죽인다

3DGS는 3000 iteration마다 `reset_opacity()`로 **전체** gaussian opacity를 강제로 거의 0까지 낮추는 표준 기법을 씀(플로터 억제용). 통제 실험은 다음 iteration부터 전체 씬을 골고루 다시 보니 opacity가 회복되지만, **incremental 구조에서는 window_size=5라 각 keyframe이 이벤트 5개쯤 지나면 윈도우에서 영구히 빠짐** — 그 시점 이후 reset이 발동하면(8,550 iter 동안 iter 3000·6000에 두 번) 이미 빠진 keyframe 영역은 opacity가 0으로 리셋된 뒤 다시는 회복할 기회가 없음. 초반 keyframe들(씬의 상당 부분)이 이 이유로 사실상 영구 소멸했을 가능성.

더 근본적으로: 통제 실험은 전체 씬을 처음부터 끝까지 **동시에** 최적화하는데, incremental은 씬을 순차적 조각으로 쪼개 **한 조각씩** 처리함 — 3DGS의 멀티뷰 일관성(여러 각도 제약이 동시에 서로 도와 좋은 기하를 만드는 것)이 구조적으로 깨짐. opacity_reset은 가장 눈에 띄는 증상일 뿐, SH 차수 상승·LR 감쇠 등 "학습이 무르익는" 모든 전역적 과정이 지역마다 다른 타이밍에 걸리는 것도 같은 계열 문제로 의심됨.

### VINGS-Mono_custom 대조 분석 — 가설 확증

`repos/reference/VINGS-Mono_custom`(실제로 301_1253/301_12F로 이미 한 번 시도된 이력 있는 코드베이스, `configs/aria/`, `output/aria/301_1253/*` 존재)의 `scripts/gaussian/{gaussian_base,gaussian_model}.py`를 코드 레벨로 확인:

- **`reset_opacity`/`opacity_reset`이 코드베이스 전체에 전무.** grep 결과 0건.
- **LR 감쇠 스케줄도 전무.** `get_expon_lr_func`류 없음, `setup_optimizer`가 config의 **고정 LR**을 그대로 씀(`update_learning_rate()` 같은 함수 자체가 없음).

**두 가설 모두 정확히 일치 확증.** "전체 iteration 수를 미리 알고 거기 맞춰 전역적으로 감쇠/리셋"하는 vanilla 3DGS 기법이 "언제 끝날지 모르고 오래된 뷰는 다시 안 오는" 온라인/incremental 세팅과 근본적으로 안 맞아서, VINGS-Mono 설계자들이 애초에 빼버린 것으로 판단됨. 대신 그들은:
- **`add_new_frame`**: keyframe 도착 시 현재 모델을 그 시점에서 먼저 렌더 → GT와 비교해 (a) 크게 틀린 기존 gaussian은 그 자리에서 바로 삭제 (b) 잔차 큰 곳에만 depth-lift로 새 점 추가. "언젠가 전역 리셋으로 청소"가 아니라 "관측 시점마다 국소적으로 즉시 정리".
- **`stablemask_control`**: 최근 로컬 윈도우 동안 gradient가 거의 없던 gaussian을 stable로 얼려서 이후 건드리지 않음 — reset 대신 "수렴했으면 잠근다".
- **`storage_control`**: 4이벤트마다 **현재 윈도우 카메라만으로** gradient-only backward를 한 번 더 돌려 애매한 gaussian만 골라 prune — 전역이 아니라 국소 범위의 저비용 청소.

### 다음 확인 단계 (미착수, 다음 세션)

1. **`opacity_reset_interval`을 매우 크게(사실상 끔) 설정하고 재실행** — 이 가설이 맞다면 PSNR이 크게 회복돼야 함. 안 되면 SH/LR 등 다른 전역 스케줄 요인으로 넘어감.
2. **LR을 고정값으로 바꿔서(감쇠 없이) 비교** — 마찬가지로 VINGS-Mono 방식 이식.
3. 위 둘로도 안 되면 "윈도우 방식 자체"보다 더 근본적인 재설계(예: VINGS-Mono처럼 관측 시점 즉시-정리형 접근으로 전환)를 검토.

## 가설 검증 라운드 2 — opacity_reset·LR 둘 다 기각, ancestor 추적으로 진짜 그림 확인 (2026-07-16)

### 1·2번 개별 검증: 둘 다 기각

- **`--opacity_reset_interval 999999`(사실상 끔)**: 평균 15.4dB, 최저 5.8dB(오히려 하락) — 회복 없음.
- **`--constant_lr`(xyz LR 감쇠 없이 고정)**: 평균 15.5dB — 마찬가지로 변화 없음.

6개 변형(keyframe-only×2, dense, dense+densify, no-reset, constant-lr) 전부 15~17dB, "방금 학습한 keyframe 근방(index 156~158)만 30dB급"이라는 동일 패턴 반복. 개별 하이퍼파라미터 on/off로는 원인을 못 찾는다고 판단, 사용자 제안으로 **특정 keyframe의 gaussian을 끝까지 추적**하는 진단으로 전환.

### 추적 진단: `ancestor_idx`로 event 5의 혈통을 끝까지 따라감

`train_incremental.py`에 `--trace_event N` 옵션 추가. `add_extra_points`가 새 점에 부여하는 `ancestor_idx`는 이후 `densify_and_split/clone`에서 자식에게 그대로 상속되므로(코드 확인됨), event N에서 태어난 gaussian들의 `ancestor_idx` 집합을 기록해두면 이후 몇 번을 쪼개지든 `torch.isin()`으로 그 혈통 전체를 계속 찾을 수 있음.

event 5(221개 seed)를 표식하고 표준 설정(window=5, iters=150, opacity_reset_interval=3000)으로 57개 이벤트 전체를 추적한 결과:

| 이벤트 | 상태 | 생존 수 | opacity(mean) | 비고 |
|---|---|---:|---:|---|
| 5→18 | 윈도우 안(~9)→밖 | 221→3,572 | 0.07→0.23 | 정상 densify 증식 |
| **19** | 윈도우 밖 | 3,614 | **0.010/0.010/0.010(전부 동일)** | `reset_opacity()` 발동 흔적(global_iter=3000) |
| **20** | 윈도우 밖 | **144**(96%↓) | 0.085 | reset 직후 opacity-threshold prune에 대량 희생 — 윈도우 밖이라 회복 불가 |
| 21→38 | 윈도우 밖 | 235→1,388 | 0.12→0.22 | 부분 재증식(같은 densify 사이클 내 잔존 인접 gaussian들 영향 추정) |
| **39** | 윈도우 밖 | 1,388 | **0.010 (전부 동일)** | 2차 reset(global_iter=6000) |
| 40 | 윈도우 밖 | 930(33%↓) | 0.11 | 2차 희생 |
| 45→56 | 윈도우 밖 | **1,210 (완전 고정)** | 0.14→0.16 | densify_until_iter=7000 이후 정지 — 더는 회복 기회 없음 |

**메커니즘은 실재 확인됨**: reset이 윈도우 밖 영역을 정확히 저격해서 죽이는 게 맞음. 다만 아래에서 보듯 이걸 꺼도 전체 품질은 안 바뀜.

### 재검증: `size_threshold`와 `opacity_reset_interval`이 코드에서 같은 조건을 공유하던 버그 발견 + 수정 후 재확인

1차 "no-reset" 테스트(`--opacity_reset_interval 999999`)가 무효과였던 이유: `size_threshold = 20 if global_iter > opt.opacity_reset_interval else None` 코드가 **reset 끄기와 size 기반 pruning 끄기를 같은 조건에 묶어놔서**, reset을 끄면 크기 기반 정리까지 같이 꺼져버림 (두 변수가 섞인 통제 실패). `--size_threshold_from_iter`로 분리하는 신규 CLI 인자 추가 후 재검증.

**결과: 여전히 15.6dB, 최저치는 오히려 더 나쁨(6.3dB).** reset을 꺼서 죽지는 않지만(N 123k→374k, 3배), 살아남은 gaussian들도 opacity 0.14~0.16 수준에서 정체된 채 "제대로 여물지 못한" 상태로 남음 — event 5 추적 로그의 마지막 값(mean opacity 0.163, scale 이상치 최대 1.087)이 이를 보여줌.

### 결론: opacity_reset은 증상이지 근본 원인이 아니었다

reset을 켜두면 윈도우 밖 영역이 대량 사멸하고, 꺼두면 죽지는 않지만 대신 미성숙 상태로 방치되어 똑같이 나쁨 — **"윈도우를 벗어나는 순간 그 영역은 그 어떤 메커니즘 설정으로도 더 이상 여물 기회가 없다"는 것 자체가 진짜 원인**으로 보임. LR 감쇠·opacity_reset은 둘 다 이 근본 문제의 증상이었을 뿐, VINGS-Mono와의 차이점을 하나씩 끄고 켜는 접근으로는 못 고침.

### 다음 결정 지점

두 갈래로 좁혀짐:
1. **VINGS-Mono 방식으로 아키텍처 자체를 다시 설계** — 주기적 전역 리셋/정리 대신, `add_new_frame`처럼 keyframe 도착 시점에 현재 모델을 그 자리에서 렌더 → 잔차 기반으로 즉시 국소 정리(삭제/추가)하는 방식으로 전환. 지금보다 구현 난이도는 높지만 VINGS-Mono가 실제로 이 문제를 풀었던 방식.
2. **윈도우를 훨씬 크게 키워서(예: 20~30 keyframe, 사실상 "거의 전체 접근"에 근접) 어느 크기부터 회복되는지 스캔** — 근본 재설계 전에 "얼마나 커야 이 문제가 사라지는지" 경계값을 먼저 확인하는 저비용 진단.

## depth-mono init 연결 — 첫 실제 개선 (2026-07-16 밤)

사용자 지적: 배치 챔피언(exp44d2) init은 **RoMA + PPM(Sobel 적응 샘플링) + depth-mono lift** 3가지 조합인데, 지금까지 incremental은 raw SLAM sparse point만 썼음. "depth-mono부터 연결, RoMA는 나중"으로 단계화.

### 구현: `scripts/incremental/build_depthmono_ppm_chunks.py` (신규)

`build_hybrid_init_scene.py`(exp44d2 레시피)의 2단계(Sobel-PPM + depth-mono lift)를 이식하되, **인과 순서를 지킴** — 배치판은 씬 전체 SLAM point로 depth를 보정하지만, 여기서는 **그 keyframe 시점까지 이미 triangulate된 SLAM point만** 누적해서 Huber 보정에 씀(미래 정보 사용 금지, Phase 1에서 OpenMAVIS가 실시간으로 이 형식을 낼 때도 그대로 맞도록).

- keyframe별 대표 프레임(`04_incremental/chunk_NNN/images/frame_00001.jpg`)에 depth-pro raw inference
- 그 시점까지의 누적 SLAM point로 Huber 회귀 스케일 보정 (`calib_depth()`, 원본과 동일 로직)
- Sobel gradient 가중 픽셀 샘플링(청크당 최대 4000점) → 보정 depth로 3D 역투영
- 출력: `05_incremental_dense/chunk_NNN/sparse/0/ppm_points3D.txt` (기존 `extra_points3D.txt`와 별개 파일, 병행 가능)
- 실행 결과: 57개 keyframe 중 56개 성공(chunk_000만 스킵 — 보정에 필요한 최소 10점이 아직 없음), 청크당 최대 4000점.

`train_incremental.py`에 `--init_source {slam,ppm,both}` 옵션 추가 — `both`면 SLAM sparse point와 PPM depth-lift point를 합쳐서 `add_extra_points`.

### 결과: 첫 실제 개선

| | 평균 PSNR | 중앙값 | PSNR<15 개수 | N |
|---|---:|---:|---:|---:|
| 기존(SLAM만, densify+표준 reset) | 15.7dB | 13.95dB | 107/163 | 123,621 |
| **SLAM+PPM(depth-mono) 결합, 나머지 동일 설정** | **18.0dB** | **16.8dB** | **41/163** | 278,368 |

가설 검증 라운드 2(opacity_reset·LR)는 6개 변형 전부 무효과였는데, **init 소스를 바꾼 건 처음으로 실제 개선.** 배치 트랙의 "init이 floater의 단일 지배 레버" 결론이 incremental에서도 방향은 맞다는 신호. 다만 통제 실험(30.2dB)과는 여전히 격차가 큼 — "윈도우를 벗어난 영역은 안 여문다"는 근본 문제 자체는 안 풀렸고, 더 나은 재료로 그 위에서 조금 나아진 정도로 해석.

### 다음 단계 (미착수)

1. **RoMA 연결** — `build_hybrid_init_scene.py` 1단계(인접 keyframe 쌍 dense correspondence + 삼각측량, 기하 검증)를 같은 인과 순서 원칙으로 이식. 배치 트랙에서 RoMA는 "청정 축"(먼지 최소) 담당이었음.
2. 위 "다음 결정 지점" 1·2번(아키텍처 재설계 vs 윈도우 크기 스캔)은 여전히 유효한 병행 축.

## PSNR 30 못 넘는 이유 분석 — "대표 프레임 1장" init의 커버리지 구멍 확인 (2026-07-16)

### 진단 경로

1. held-out 163뷰가 **연속 블록**(`frame_00580`~`frame_00742`, `sparse/0/test.txt` 확인)이라는 걸 재확인.
2. "무작위 샘플링 운" 가설 테스트: `train_incremental.py`에 `draw_counts` 계측 추가(`--init_source both`, N=275,786 재실행) → **draw_count와 PSNR 상관계수 0.025**(사실상 0). 학습 중 한 번도 안 뽑힌 프레임 9개조차 평균 17.29dB로 정상 분포 — 샘플링 횟수는 원인이 아님, 기각.
3. 163뷰 PSNR을 프레임 단위로 정렬 → 최저 10개(10.0~12.1dB)가 `frame_00633`~`00641`에, 최고 10개(29.9~34.0dB)가 `frame_00726`~`00738`에 **각각 촘촘히 뭉쳐있음**. 무작위가 아니라 공간/시간적으로 국소화된 원인.
4. 이 두 구간이 속한 keyframe 청크를 **실제 `05_incremental_dense/chunk_NNN/images/` 폴더의 프레임 범위**로 역추적(주의: timestamp 구간 이분 탐색으로 짠 첫 버전 스크립트는 인덱싱이 한 칸 밀려 틀린 청크를 가리켰음 — 반드시 실제 파일 목록으로 검증할 것):
   - 최저 구간(633~641) → **`chunk_019`**(kf_id=77, `num_new_map_points=63`, `num_dense_frames=50`)
   - 최고 구간(726~738) → **`chunk_021`**(kf_id=88, `num_new_map_points=159`, `num_dense_frames=50`)
5. 각 청크의 depth-mono+PPM 대표 프레임(`04_incremental/chunk_NNN/images/frame_00001.jpg`)을 실제 GT/렌더 이미지와 육안 비교:
   - **`chunk_019` 대표 프레임**: 책상 위 노트북·선반·수납함을 찍은 장면. 반면 `frame_00636`의 실제 GT는 문 옆 화이트보드를 거의 화면 전체를 채울 만큼 근접 촬영한 장면 — **완전히 다른 내용/방향**. 렌더 결과는 흰색/초록 안개뿐(구조 없음).
   - **`chunk_021` 대표 프레임**: 천장 조명·책상 줄·노란 수납함이 보이는 복도 샷 — `frame_00736`의 실제 GT와 **거의 동일한 뷰포인트**. 렌더 결과도 천장 파이프·조명·의자·모니터가 뚜렷이 복원됨.

### 근본 원인

`build_depthmono_ppm_chunks.py`는 청크당 **대표 프레임 1장(그 keyframe의 `frame_00001.jpg`)만** depth-pro 추론 + Sobel-PPM 샘플링에 사용한다. 그런데 photometric loss는 그 청크에 속한 **dense 프레임 전체(~50장)**에 걸쳐 학습한다. 카메라가 그 50프레임 구간 동안 크게 회전/이동하면(`chunk_019`가 실제로 그랬듯 책상→화이트보드로 시선이 이동), 대표 프레임이 담은 시야 밖 영역은 depth+PPM점도, SLAM extra point도(63개뿐, `chunk_021`의 159개 대비 희박) 거의 못 받고 photometric loss만 받는다 — init 없이 맨땅에서 4000점짜리 예산은 엉뚱한 곳(대표 프레임 시야)에 다 쓰이고, 정작 필요한 화이트보드 근접 영역은 사실상 무(無)-init 상태로 남는다.

여기에 "가설 검증 라운드 2"에서 이미 확인한 "윈도우를 벗어나면 그 어떤 설정으로도 다시 여물 기회가 없다"는 문제가 겹친다 — 대표 프레임이 놓친 영역은 그 청크가 윈도우 안에 머무는 짧은 동안(`iters_per_event`=150) 조차 init 자체가 없어 사실상 학습이 안 되고, 윈도우 밖으로 밀려나면 그걸로 끝. 두 문제가 곱해져서 "대표 프레임과 실제로 잘 맞은 청크(예: 021)는 30dB대, 대표 프레임이 놓친 청크(예: 019)는 10dB대"인 **양봉분포**가 나오고, 평균이 통제 실험(30.2dB)에 크게 못 미치는 15~18dB에 눌려앉는다.

### 다음 단계 제안 (미착수)

**대표 프레임 1장 → 청크 내 다중 프레임(예: dense 구간의 처음/중간/끝, 또는 N프레임마다 균등 샘플)으로 depth-mono+PPM 소스를 확장** — 카메라가 청크 안에서 실제로 훑은 궤적을 init 커버리지가 따라가게 만드는 것. 지금까지 시도한 opacity_reset/LR/window-size 튜닝보다 훨씬 직접적으로 이 근본 원인을 겨냥함. RoMA 연결(위 "다음 단계" 1번)과 별개로, 이 쪽이 더 저비용·고효과일 가능성이 높아 우선순위로 제안.

## 🚀 2026-07-16 결과 및 검증 완료 (v2~v4 실험 결과)

### 1. PPM Multi-frame (K=3) 확장 및 1차 검증 (exp48_v2)
- **설정**: `build_depthmono_ppm_chunks.py`를 개편하여 청크 내 균등 간격 K장($K=3$, 처음/중간/끝)을 샘플링하여 depth-pro + Huber calibration 및 Sobel-PPM 역투영을 병합하여 공급.
- **학습 결과** (`train_incremental.py --init_source both`, N=781,276):
  - **평균 PSNR**: **18.04 dB** (기존 18.00 dB 대비 0.04 dB 상승)
  - **중앙값 PSNR**: **17.17 dB** (기존 16.80 dB 대비 0.37 dB 상승)
  - **PSNR < 15 뷰 개수**: **40 / 163 개** (기존 41 개 대비 1개 감소)
- **분석**: 다각도 init을 공급했으나 평균 성능은 거의 그대로임. 윈도우 밖으로 밀려난 영역이 `reset_opacity` 시점에 투명화되어 소멸하는 근본적 병목(온라인 학습 루프 홀)이 해결되지 않았기 때문.

### 2. RoMA dense correspondence 추가 (exp48_v3_hybrid)
- **설정**: `build_roma_chunks.py`를 신설하여 인접 keyframe(chunk_idx-1과 chunk_idx) 쌍 매칭 및 triangulation(Huber scale, reprojection < 2px) 공급. `--init_source all`을 통해 PPM K=3 + RoMA + SLAM 결합.
- **학습 결과** (N=839,729):
  - **평균 PSNR**: **18.12 dB** (PPM 단독 대비 0.08 dB 상승)
  - **중앙값 PSNR**: **17.20 dB** (PPM 단독 대비 0.03 dB 상승)
  - **PSNR < 15 뷰 개수**: **37 / 163 개**
- **분석**: 기하학적으로 검증된 RoMA 포인트들이 추가(가우시안 수 ~6만 개 증가)되어 정량 메트릭이 추가 개선되었으나 여전히 18dB대에 정체.

### 3. 온라인 3DGS 핵심 루프 홀 수정: Selective Opacity Reset 도입 (exp48_v4_selective_reset)
- **진단 및 해결**:
  - 온라인/점진적 학습 도중 3000 iterations 마다 `reset_opacity`가 모든 가우시안의 opacity를 `0.01`로 리셋함.
  - 배치 학습은 전역 카메라가 다시 학습하여 복원하나, 점진적 학습은 활성 윈도우(`window_size=5`) 바깥의 오래된 가우시안들이 다시 여물 기회를 박탈당해 영구 미성숙/반투명화 및 Pruning(min_opacity_threshold 미달로 소멸) 궤멸을 겪음.
  - 이를 해결하기 위해 **현재 활성 윈도우에 관여하는 가우시안만 opacity를 리셋하고, 윈도우를 벗어난 안정된(stable/historical) 가우시안들은 opacity 리셋을 원천 차단**하도록 `train_incremental.py` 내 reset 로직을 수정.
- **학습 결과** (N=1,164,933 - 리셋 차단에 의해 가우시안 수 32만 개 추가 보존):
  - **평균 PSNR**: **18.23 dB** (전체 실험 중 최고점 달성)
  - **중앙값 PSNR**: **18.27 dB** (기존 하이브리드 17.20 dB 대비 **1.07 dB 대폭 상승**)
  - **PSNR < 15 뷰 개수**: **35 / 163 개** (기존 37개 대비 2개 감소)
- **최종 분석**: 
  - 선택적 리셋 기법 덕분에 윈도우를 벗어난 가우시안들이 성공적으로 살아남았으며, 그 결과 중앙값 PSNR이 1.07dB 대폭 개선되는 쾌거를 거둠.
  - ~~여전히 18dB대에 머무는 이유는 held-out test split(frame 580~742, 163뷰)이 하나의 연속 블록으로 구성되어 발생한 공간적 학습 공백 때문임.~~
  - ~~학습 궤적 상 chunk 18(frame 579)과 chunk 19(frame 743) 사이에 163뷰의 공백이 있어, 점진적 학습 진행 시 전방을 바라보는 뷰(chunk 18)와 후방을 바라보는 뷰(chunk 19)가 활성 윈도우에 함께 담기지 못해 co-optimization이 일어나지 않음.~~
  - ~~향후 이 공백을 메우기 위해 슬라이딩 윈도우 크기를 확장(예: window_size = 10 또는 15)하여 두 뷰포인트를 강제로 동시에 co-optimize하는 진단을 권장함.~~
  - **⚠ 아래 "eval 스크립트 버그 발견" 섹션에서 이 설명 전체가 틀린 프레임 매핑에 기반했음이 밝혀짐 — 폐기.**

## ⚠ eval 스크립트 버그 발견 + 전체 재분석 (2026-07-16 밤, 세션 재개 후)

### 버그: `render.py --eval`이 `test.txt`를 아예 안 읽는다

`3dgs-custom/scene/dataset_readers.py:238~248`:

```python
if eval:
    if "360" in path:
        llffhold = 8
    if llffhold:          # 기본값 8, 아무도 오버라이드 안 함 → 항상 참
        test_cam_names_list = [name for idx, name in enumerate(cam_names) if idx % llffhold == 0]
    else:
        with open(... "test.txt") as file:   # ← 이 분기는 절대 안 탐
            test_cam_names_list = [...]
```

`llffhold` 기본값이 8이고 아무 호출부도 0으로 오버라이드하지 않으므로, **`--eval`을 켜는 순간 `sparse/0/test.txt`는 완전히 무시되고**, 전체 1,303프레임을 이름순 정렬한 뒤 **8번째마다 하나씩** 뽑아 테스트셋(163장, 우연히 `test.txt` 줄 수와 같음)을 만든다.

**검증**: `test.txt` 57번째 줄(인덱스 56) 기준으로는 `00056.png` = `frame_00636.jpg`(책상 장면)여야 하는데, 실제 render.py가 만든 GT `00056.png`를 열어보면 화이트보드 근접샷 — 이건 llffhold-8 매핑의 인덱스 56(`frame_00449.jpg`)과 픽셀 단위로 일치함. **즉 지금까지(이전 세션 + antigravity v2~v4) "held-out 163뷰는 frame_00580~742 연속 블록"이라는 전제 자체가 틀렸고, 그 위에서 만든 "chunk_019 vs chunk_021", "chunk 18/19 사이 공백" 설명은 전부 잘못된 프레임 매핑에 기반한 이야기였음.**

### 올바른 매핑으로 재분석 (exp48_v4_selective_reset의 `per_view.json` 재사용, 매핑만 수정)

| 청크 구간 | 프레임 범위 | keyframe 범위 | 평균 PSNR |
|---|---|---|---:|
| chunk 0-13 (초반) | ~1-425 | kf 0-51 | 15~21dB (중간) |
| **chunk 14-20 (최악)** | **~430-700** | **kf 54-83** | **9.6~17dB** |
| chunk 21-46 (점진 회복) | ~700-1230 | kf 88-132 | 16~25dB |
| **chunk 47-56 (최고, 후반부)** | **~1230-1300** | **kf 134-143** | **25~34dB** |

- 청크 15(`frame_00430`) 육안 확인: **정확히 그 화이트보드 근접샷** — 최초 직감(대표 프레임이 화이트보드를 놓쳤다)의 "화이트보드가 어렵다"는 부분은 맞았고, 청크 번호만 잘못 짚었던 것.
- 청크 50(`frame_01231`)은 앞서 "좋은 결과" 사례로 반복 등장하던 **그 복도 뷰**와 동일 — 천장 조명·책상·의자, 텍스처가 풍부한 영역.
- **map point 수로는 설명 안 됨**: 나쁜 구간(14-20)이 새 SLAM point가 오히려 더 많음(62~338개) — 좋은 구간(47-56)은 3~97개뿐. "init 점이 적어서 나쁘다"가 아니라, **화이트보드류 저텍스처 근접 표면 자체가 SLAM(특징점 희소)·depth-pro(단조로운 표면이라 상대 깊이 신호 약함) 양쪽 다에게 근본적으로 어려운 영역**이라는 뜻.

### 재해석

antigravity가 순차로 시도한 3개 수정(K=3 다각도 PPM, RoMA, selective opacity reset)이 18.0→18.23dB로 거의 안 움직인 이유가 이걸로 설명됨: "대표 프레임 1장이 카메라 스윕을 놓친다"는 문제가 아니라, **애초에 화이트보드 구간 자체가 어떤 init 방법으로도 잘 안 잡히는 저텍스처 영역**이었기 때문 — 다각도로 봐도, RoMA 대응점을 붙여도 텍스처가 없으면 삼각측량/PPM 샘플링 둘 다 약해짐. K=3/RoMA 확장 자체는 방향은 맞았으나(coverage gap을 메우려는 시도) 이 특정 구간의 핵심 병목(저텍스처)은 다른 층위의 문제.

반면 후반부(chunk 47-56)가 25~34dB로 크게 좋은 것은 새 map point가 적은데도(3~97개) 잘 나온다는 점에서, **그 복도 구간을 궤적 초반에도 이미 지나갔을 가능성**(반복 방문으로 인한 장기 성숙) 쪽이 유력 — 아직 미검증, 다음 확인 과제로 남김.

### 다음 단계 제안 (미착수, 우선순위 재조정)

1. **eval 버그 자체를 고칠지 결정 필요**: `test.txt`(연속 블록, 특정 구간 집중 평가)를 쓰고 싶으면 `llffhold=0`을 명시로 넘기게 수정, 아니면 지금의 llffhold-8(전체 궤적 고른 샘플링)을 표준으로 그대로 채택 — 후자가 "전체 장면 평균 품질" 지표로는 오히려 더 대표성 있음. 지금까지의 모든 exp48 PSNR 숫자(15.7/18.0/18.23dB 등)는 사실 llffhold-8 기준이었으므로 서로 비교는 유효함(같은 버그가 일관되게 적용됐으므로) — 다만 "특정 구간을 콕 집어 분석"할 때만 프레임 매핑을 반드시 llffhold-8 기준으로 다시 계산할 것.
2. **화이트보드류 저텍스처 구간(chunk 14-20) 전용 대책**: RoMA/PPM 다각도 확장으로는 이미 안 풀렸으니, ① 그 구간만 별도로 batch 트랙의 풀 하이브리드(RoMA+PPM+depth-mono 3종 동시, 예산 키움)를 적용해보거나, ② 애초에 텍스처 없는 벽/화이트보드는 3DGS 자체의 근본 한계(어느 트랙에서든 어려움)일 수 있다는 것도 배제하지 말 것.
3. **후반부(47-56) 고PSNR의 원인이 "반복 방문 성숙"인지 확인**: 궤적 초반에 같은 복도 구간을 지났는지 pose 궤적으로 대조.
4. RoMA 연결은 이미 완료(v3_hybrid) — 남은 병목은 "다다익선 init"이 아니라 "저텍스처 영역 자체의 근본 난이도"로 재정의됨.
