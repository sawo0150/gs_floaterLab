# /home/intern 용량·정리 후보 조사

2026-09-10 조사. 삭제·이동·symlink 변경·환경 제거는 하지 않았다. 현재 위치에서 벤치마크를 준비할 수 있다. `/home/intern/gs_floaterLab`는 여유 528GiB인 루트 파일시스템에 있고, 별도 SSD 사용은 필수가 아니다.

## 실측 범위

`du -x`, symlink를 따라가지 않는 전체 파일 stat 조사, 일부 실험 카드와 transfer manifest 확인. 일반 파일 entry 633,796개, symlink 21,151개, 조사 오류 0개. 파일 종류 합계는 inode 중복을 제외한 allocated bytes를 사용했다. 표의 정수 디렉터리 크기는 `du -h` 반올림이다.

| 위치 (/home/intern 기준) | 크기 | 판단 |
|---|---:|---|
| 전체 | 174GiB | 루트 전체 2.9TiB 사용량 중 일부 |
| gs_floaterLab | 53GiB | 대부분 실험 evidence |
| gs_floaterLab/context/experiments | 51GiB | exp75 42GiB, exp76 6.1GiB, exp74 3.3GiB |
| p28_5090_20260813 | 24GiB | 기존 환경·weight·data 의존성 있어 전체 삭제 금지 |
| aria_data | 24GiB | 원본 데이터와 ZIP, 보존 우선 |
| repro_assets | 17GiB | 현재 사용 중인 데이터·모델·재현 자료 원본 |
| transfers | 16GiB | 이미 해제된 전송 archive가 주요 후보 |
| workspace | 13GiB | 환경 및 현재 symlink 대상 포함 |
| realtime_pipeline_20260817 | 11GiB | 코드·빌드·실험 결과 혼재 |
| VIGS-SLAM-visible-lazy-carve | 8.4GiB | 현재 VIGS data 연결의 경유지 |
| VIGS-SLAM-main-integration-20260828 | 5.5GiB | 현재 실제 개발 worktree |
| VIGS-SLAM-custom | 4.4GiB | 현재 worktree들의 Git 공통 저장소 포함 |

전체 /home/intern의 PLY는 48.91GiB, PNG는 18.44GiB. PNG에는 원본/입력도 포함되므로 확장자 전체 삭제는 불가하다. 워크스페이스의 `results/` 자체는 12MiB에 불과하고 실제 대용량은 `context/experiments/*/evidence/`에 있다.

## 우선 정리 후보: 합계 최대 31.92GiB

아래 세 집합은 경로가 겹치지 않는다. 모두 사용자 검토 전의 후보이며, 숫자는 계획상 회수량이다. 특히 archive는 무결성 확인이 추가로 필요하다.

| 후보 | 회수 가능량 | 검증 상태 / 보존 조건 |
|---|---:|---|
| exp74~76 반복 평가 GT 이미지 공유 | 5.09GiB | SHA256으로 중복 60,007개 확인. canonical 한 벌과 기존 경로를 유지하는 hardlink 또는 symlink 전환 후보 |
| exp75·76 일반 중간 PLY 106개 | 11.50GiB | run별 최대 iteration PLY 보존. anytime_runs와 shared_branch는 중간 PLY도 전부 제외. 삭제 전 논문에 필요한 중간 결과 검토 |
| transfers의 data/weight/reference archive 7개 | 15.33GiB | 해당 해제 파일 목록 존재 확인. source/env archive·contents·SHA256SUMS·manifest는 보존. archive와 해제본 내용 일치 및 백업 필요성 추가 확인 |

모두 정리하면 루트 여유는 약 **528→560GiB**가 된다. 현재 실험 root의 중간 PLY와 중복 GT만 정리하는 안은 **16.59GiB**다. 수백 GiB를 회수할 수 있는 상태로 해석하면 안 된다.

### A. 동일 GT 이미지

`context/experiments/{exp74,exp75,exp76}/.../test/ours_*/gt/`에 총 61,392개, 5.203GiB가 있다. 파일 크기가 같은 후보를 SHA256으로 비교했다. 중복 group 1,384개, 여분 파일 60,007개, 여분 allocated size 5.085GiB다. 조사한 GT 파일은 기존 hardlink가 아니었다.

비교는 내용 기준이므로 서로 다른 장면에서 파일명 `00000.png`가 같다는 이유로 묶지 않았다. candidate manifest의 retained_path는 임시 대표 경로다. 실제 정리 시 장면별 공통 cache로 canonical 파일을 옮기거나 유지하고, 기존 `gt/` 경로를 읽을 수 있도록 보존해야 한다. hardlink 방식이면 이후 in-place 수정이 모든 링크에 반영되므로 canonical GT는 불변으로 관리한다. 이 정리는 파일 경로를 제거하는 단순 삭제보다 공유 전환에 가깝다.

### B. 중간 PLY

`point_cloud/iteration_N/point_cloud.ply` 형식의 158개 run을 조사했다.

- run별 최대 iteration PLY: 158개, **22.414GiB**, 전부 보존 제안.
- 일반 중간 PLY: 106개, **11.503GiB**, 정리 후보. exp75 8.668GiB, exp76 2.835GiB.
- anytime/shared_branch 중간 PLY: 49개, **6.028GiB**, 이번 정리에서 보존 제안.
- PTH checkpoint, input.ply, split event, metrics, config, seed, 로그는 이번 PLY 후보에 포함하지 않았다.

최대 iteration이라는 사실만으로 성공 run/완전한 checkpoint를 증명하지는 않는다. 후보는 파일명과 보수적인 경로 필터로 선정했으며, 해당 iteration의 논문 그림·anytime 분석 의존성 검토가 삭제 전에 필요하다. `shared_branch`의 공통 checkpoint는 branch 재현에 필요하므로 통째로 보존한다.

동일 크기 PLY도 파라미터가 다를 수 있으므로 중복으로 판정하지 않았다. 이는 정확한 중간 상태를 버리고 최종 모델을 남기는 보관 정책 선택이다.

### C. transfer 압축본

`/home/intern/transfers/baseline_repro_20260813T1951_JST/`의 8개 archive에 대응하는 contents 목록을 `/home/intern/repro_assets/baseline_repro_20260813T1951_JST/`와 대조했다. 모든 목록 entry의 파일 또는 symlink가 존재했다. symlink의 정상 해석과 모든 파일의 archive 대비 바이트 일치까지 검증한 결과는 아니다.

이 중 source/env archive는 offline Git bundle·patch·환경 명세를 포함하므로 보존한다. 나머지 7개의 15.328GiB를 조건부 후보로 뒀다. 기록상 원격 Drive 전송 위치도 있지만 원격 백업의 현재 존재·무결성은 확인하지 않았다.

`repro_assets` 해제본은 현재 데이터 경로가 사용하므로 삭제 대상이 아니다. 다른 p28 download archive 1.24GiB 및 aria_data ZIP 11.3GiB는 추가 중복 검증 전까지 31.92GiB 합계에 넣지 않았다.

## 후순위: 논문 그림 보관 정책을 정한 뒤

- 실험 test render PNG는 61,392개, **3.252GiB**. 최종 PLY·평가 pose·렌더 설정이 있으면 재생성 가능한 경우가 있으나, 논문 qualitative 비교와 재현의 근거이므로 이번 우선 정리에서 제외한다.
- 폐기한 exp75 분기 전체 삭제는 권하지 않는다. shared_branch만 14.05GiB지만 실패 원인·ablation과 공통 초기화 근거를 포함한다. 최종 PLY 하나씩과 수치·설정·로그는 유지한다.
- realtime pipeline build 및 debug 결과는 후순위. 빌드 디렉터리에는 실행 binary가 있을 수 있고 오래된 source도 dirty일 수 있어 코드/환경을 통째로 지우지 않는다.
- 중복 Omnidata 파일·VRS는 hash 확인과 incoming symlink/설정 수정이 필요하다. 이번에는 후보 회수량에 포함하지 않았다.

## 삭제하면 위험한 연결

실제 symlink target 경로를 조사했을 때 `/home/intern/repro_assets` 아래로 7,306개, `workspace`로 6,638개, `p28_5090_20260813`으로 5,640개, `VIGS-SLAM-visible-lazy-carve`로 1,510개가 연결돼 있었다. 경로 중복 개수이며 디렉터리 간 독립 dependency 수를 뜻하지 않는다.

`git worktree list`에서 현재 integration worktree가 `/home/intern/VIGS-SLAM-custom`의 공통 Git 저장소를 사용하는 것을 확인했다. 따라서 `VIGS-SLAM-custom`을 구버전이라는 이유로 통째로 삭제하면 안 된다. `.git/objects` 약 1.8GiB 역시 일반 캐시가 아니다.

실행 중 프로세스의 전체 open-file 조사는 하지 않았다. 실제 삭제 단계에서는 정확한 후보가 사용 중인지 재확인하고, stale inventory가 아닌 현재 파일 stat/hash를 다시 검사해야 한다.

## 현재 폴더에서 벤치마크를 운영하는 안

별도 SSD 없이도 현재 528GiB에서 RPNG+UTMM pilot의 계획 범위 250~350GiB를 수용할 수 있다. 주요 3종과 모든 baseline·반복 결과를 한꺼번에 최대 보관하는 400~600GiB 안은 그대로 적용하기 어렵다. 단계별로 진행하고 이 파일시스템을 사용하는 다른 작업의 증가분도 고려해 100~150GiB 정도는 비워 두는 운영을 제안한다.

```text
/home/intern/gs_floaterLab/
  benchmarks/online_gs/   # protocol, manifests, env specs, adapters
  repos/benchmarks/       # 각 baseline의 별도 checkout
  data/benchmarks/        # 데이터 한 벌 + 원본/전처리 구분
  results/benchmarks/     # run별 대용량 산출물
  .benchmark_envs/        # 독립 env, Git 제외
  .benchmark_cache/       # package/cache/build, Git 제외
  context/experiments/   # 카드·수치·작은 그림 중심
```

위 경로는 제안이며 아직 생성하지 않았다. 앞으로 새 대용량 PLY·render는 `results/benchmarks`에 저장하고 context에서는 링크로 참조하면 문서와 산출물이 섞이는 문제를 줄일 수 있다. 기존 evidence 이동은 참조 경로를 바꾸므로 이번 조사에서 수행하지 않았다. 같은 파일시스템 안의 이동만으로 여유 용량이 늘지는 않는다.

## 검토용 파일

- [수치 요약](intern_cleanup_20260910_summary.json)
- [106개 중간 PLY 후보](intern_cleanup_20260910_intermediate_ply.csv)
- [7개 archive 후보](intern_cleanup_20260910_archives.csv)
- [SHA256 확인된 GT 중복 경로 목록, gzip CSV](intern_cleanup_20260910_gt_duplicates.csv.gz)

이 목록은 삭제 승인이나 자동 삭제 스크립트가 아니다. 대용량 삭제는 사용자 승인 없이 금지한다는 워크스페이스 AGENTS.md 규칙에 따라 실제 정리는 별도 단계로 둔다. 이번 요청은 조사로 처리했다.
