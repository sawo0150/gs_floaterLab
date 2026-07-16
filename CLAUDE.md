# gs_floaterLab

Aria glass 기반 **실시간 incremental 3DGS 매핑** 시스템을 만드는 실험 워크스페이스.

## 최종 목표 (North Star)

하나의 완결된 온라인 시스템을 만든다:

1. **Localization**: Aria glass의 **흑백 SLAM 카메라**(Fisheye624 stereo + IMU)로 실시간 위치 추정.
2. **Mapping**: **RGB 카메라** 정보를 **incremental**하게(keyframe 도착 시마다) 받아 3DGS 지도를 online으로 확장.
3. **품질 요건 (동시 충족)**:
   - **고품질**: "3D 지도답다"고 할 만한 render 품질 (배치 3DGS급, PSNR 30dB+ 수준).
   - **floater 없음**: 좋은 geometry (자유공간 먼지 최소).
   - **실시간**: 온라인으로 돌아가는 속도.

즉 "흑백으로 정밀하게 위치를 잡고, RGB로 실시간 고품질 지도를 짓되 floater가 없는" 시스템.

## 현재 단계 (2026-07-17)

localization까지 한 번에 붙이는 건 어려우므로 **매핑 품질부터** 확보한다. 우선순위 순서:

1. **[지금] incremental mapping을 배치급 고품질(30dB+)로 끌어올리기.** 현재 Photo-SLAM replay가
   22dB에 정체 — **진짜 병목은 supervision 밀도**(keyframe 57장만 씀 vs 배치는 dense 프레임
   ~1140장). 다음 실험: **dense-frame supervision**(keyframe 사이 RGB 프레임들도 pose와 함께
   supervision 뷰로 추가). ⚠ **22dB 지도에 floater 억제(carve)를 먼저 넣는 건 순서가 틀림** —
   낮은 품질에선 "이미지가 floater를 요구"해 carve가 안 통함(exp43 12F에서 확인). 고품질이 선결.
2. **[그다음] floater 억제(carve loss)를 고품질 지도 위에 이식** — 우리 floater 방법론(exp44d2)이
   incremental에서도 통하는지 region GT 지표로 검증.
3. **[그다음] 라이브 통합** — 검증된 매핑 레시피를 실제 라이브 트래킹(exp50 DiskChunGS,
   Fisheye624 흑백 트래킹 이미 성공)에 얹기. dense-frame pose는 최종 시스템에선 흑백 SLAM
   트래킹이 실시간으로 공급 → dense supervision은 공짜 입력.

배치 트랙(exp01~47)은 이 목표의 **품질 상한/방법론 검증**용이며, floater 감소 자체는 배치에서
이미 해결됨(exp44d2, 33.8dB). incremental 트랙(exp48~50)이 위 최종 그림의 본선.

## 시작하기

1. **`context/STATUS.md`를 먼저 읽는다** — 현재 best, 열린 질문, 다음 할 일이 여기에만 있다.
2. 전체 실험 이력은 `context/experiments/INDEX.md`.
3. 문서 구조와 갱신 규칙은 `context/README.md`. **실험 완료 시 exp 카드 + INDEX 한 줄 + STATUS 갱신, 이 3개는 필수.**
4. 실험 전 `context/knowledge/pitfalls.md` 필독.

## 주요 경로

- 메인 3DGS repo: `/home/wosas/Desktop/26-1_RPM/gsProjects/3dgs-custom` (**dirty worktree — revert 금지**)
- 학습 데이터/결과 지도: `context/reference/workspace_map.md`
- 실행 커맨드: `context/reference/repro_commands.md`, `scripts/experiments/run_exp*.sh`
- 공유 자료: `share/` (각 하위 폴더별 README 설명서 완비)
- 개별 배포용 압축 파일들:
  - `floater_share_01_labels.zip` (사용자 라벨 PLY 압축, 171MB)
  - `floater_share_02_region_gt.zip` (Delaunay 3D 영역 마스크 압축, 452KB)
  - `floater_share_03_results.zip` (기존 비교용 PLY 압축, 321MB)
  - `improved_results.zip` (최신 개선 12F 및 305호 결과 PLY 압축, 303MB)
- conda env: `3dgs`
- W&B: `geekseek/3dgs-keyframe`
