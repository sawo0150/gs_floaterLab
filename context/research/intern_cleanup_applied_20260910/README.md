# 2026-09-10 승인된 정리 실행 결과

사용자가 조사 목록의 정리·삭제와 데이터 다운로드를 승인한 뒤 실행했다.

| 작업 | 결과 |
|---|---|
| 동일 GT 공유 | 60,007개, SHA256 재검증 후 hardlink로 교체. 모든 기존 경로 유지 |
| 일반 중간 PLY 삭제 | 106개. 크기·PLY 헤더·더 나중 모델 존재 확인, 삭제 파일 SHA256 기록 |
| 전송 archive 삭제 | 5개. 제공 SHA256 검증 및 tar 내부 일반 파일을 해제본과 내용 대조 |
| 보존 검증 | run별 마지막 모델 158/158, anytime/shared 중간 모델 49/49 존재 |
| 실제 회수 allocated bytes | 32,637,149,184 bytes = **30.3957GiB** |

추가 보호: 조사 시 열린 file descriptor 및 /home/intern 내부 symlink의 직접 대상은
삭제 대상에서 제외하도록 검사했다. 시스템 전체의 모든 사용 관계를 증명하는 검사는 아니다.

삭제하지 않은 archive:

- `baseline_mapper_inputs_20260813T1951_JST.tar.zst`: 해제본의 symlink 5,079개가
  재연결돼 archive 문자열과 다름. 일반 파일 비교는 통과했지만 별도 링크 대응 검증 전 보존.
- `baseline_frontend_artifacts_20260813T1951_JST.tar.zst`: 해제본의 symlink 36개가
  없거나 깨짐. 정상 복원 가능성을 위해 보존.
- source/environment archive, checksum 목록, transfer manifest는 원래부터 보존 대상.

[summary.json](summary.json)에 집계, `actions.jsonl.gz`에 파일별 hash·보존 경로·삭제/공유
작업·archive 검증 차이를 기록했다. 숫자는 삭제와 hardlink 공유로 회수한 파일 block의
합계이며, 동시에 진행되는 다운로드 때문에 `df`의 차이와 일치하지 않을 수 있다.

코드 저장소·환경·원본 데이터·최종 PLY·실험 수치·로그는 이번 정리에서 삭제하지 않았다.
