# AGENTS.md — gs_floaterLab

이 파일은 이 워크스페이스에서 작업하는 모든 AI 에이전트를 위한 공통 지침이다.
(Claude Code는 `CLAUDE.md`를, 다른 에이전트는 이 파일을 읽는다 — 두 파일의 목표/규칙은 동일하게 유지할 것.)

## 최종 목표 (North Star)

Aria glass 기반 **실시간 incremental 3DGS 매핑** 시스템:

1. **Localization**: Aria 흑백 SLAM 카메라(Fisheye624 stereo + IMU)로 실시간 위치 추정.
2. **Mapping**: RGB 카메라 정보를 incremental하게(keyframe마다) 받아 3DGS 지도를 online 확장.
3. **동시 충족**: ① 고품질(배치급, PSNR 30dB+) ② floater 없음(좋은 geometry) ③ 실시간.

## 현재 단계 & 우선순위 (2026-07-17)

localization은 나중. 지금은 **매핑 품질 확보**가 목표. 순서:

1. **[지금] incremental mapping을 30dB+로.** 병목 = supervision 밀도(keyframe 57장 only).
   다음 실험 = **dense-frame supervision**(keyframe 사이 RGB 프레임도 supervision에 추가).
   ⚠ **저품질(22dB) 지도에 carve(floater 억제)를 먼저 넣지 말 것** — 품질이 선결 조건.
2. **[그다음] carve loss를 고품질 지도에 이식** → floater 방법론이 incremental에서 통하는지 검증.
3. **[그다음] 라이브 통합**(exp50 DiskChunGS, Fisheye624 트래킹 성공한 것 위에).

## 필수 작업 규칙

- **시작 전 `context/STATUS.md`를 먼저 읽는다** (단일 진실 소스: 현재 best·열린 질문·다음 할 일).
  이미 확정된 결론을 재추론하지 말고 그 위에서 이어간다.
- **실험 완료 시 3종 세트 필수**: ① `context/experiments/`에 exp 카드 결과 추가
  ② `context/experiments/INDEX.md` 한 줄 ③ `context/STATUS.md` "최근 흐름"에 날짜 붙여 새 항목 추가.
  STATUS의 기존 항목은 **수정하지 말고** 정정이 필요하면 새 항목을 위에 덧붙인다.
- **품질 판정은 held-out PSNR / region GT 지표로만.** "크래시 없이 완주 = 성공"으로 오판한 전례
  있음(exp48). train PSNR은 floater 지표로 부적합(프로젝트 확립 원칙).
- **held-out 평가 하네스**: 3dgs-custom `render.py --eval`은 `--eval` 시 llffhold-8(전체 프레임
  8번째)을 쓰고 `test.txt`를 무시함(exp48에서 발견). 특정 구간 분석 시 프레임 매핑은 반드시
  llffhold-8 기준으로.
- **인과 순서(causal order) 유지**: 어떤 청크/프레임도 미래 keyframe 정보를 쓰면 안 됨
  (최종 시스템이 online이므로).
- **실패는 실패로 정직하게 기록.**
- 파괴적 작업(git reset --hard, 대용량 삭제)은 사용자 승인 없이 금지.
- GPU 사용 전 `nvidia-smi`로 타 프로세스 확인 — 있으면 종료하지 말고 대기(사용자 별개 작업일 수 있음).

## 주요 경로

- 메인 배치 3DGS repo: `/home/wosas/Desktop/26-1_RPM/gsProjects/3dgs-custom` (**dirty worktree — revert 금지**)
- incremental 매핑 repo: `/home/wosas/Desktop/26-1_RPM/gsProjects/Photo-SLAM` (exp49),
  `/home/wosas/Desktop/26-1_RPM/gsProjects/DiskChunGS` (exp50, 라이브)
- 데이터: `data/01_euroc_openmavis_input`(Aria stereo+IMU), `data/02_openmavis_output/orb_export`(SLAM),
  `data/03_rgb_3dgs_full`(RGB 1303프레임 + held-out), `data/scenes/301_1253`(청크류)
- conda env: `3dgs`(배치·평가), `vings`(CUDA 12.8, Photo-SLAM/DiskChunGS 빌드·실행)
