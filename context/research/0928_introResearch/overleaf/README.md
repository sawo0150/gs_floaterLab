# Overleaf 원고와 코멘트 아카이브

2026-09-28 다운로드. 원본 프로젝트 내용을 편집하거나 댓글을 resolve하지 않았다. PDF가 캐시에 없을 때 exporter가 compile을 요청했다. 로그인 쿠키·인증 정보는 이 폴더에 저장하지 않았다.

## 휴먼테크 — 2페이지 원고

프로젝트: [HumanTeck-Song's intern](https://www.overleaf.com/project/6aadda772e7b434d4382dc48)

- [원본 PDF — 2페이지](humantech/2026-09-28/original.pdf)
- [코멘트 목록을 덧붙인 PDF — 4페이지](humantech/2026-09-28/commented.pdf)
- [전체 스레드·답글 대화록](humantech/2026-09-28/all_threads.md)
- [본문 연결 코멘트 목록](humantech/2026-09-28/comments-2026-09-28.md)
- [코멘트·변경 제안 JSON](humantech/2026-09-28/comments.json)
- [전체 소스 ZIP — 13개 항목](humantech/2026-09-28/project_source.zip)
- [코멘트 대상 LaTeX](humantech/2026-09-28/source/paper.tex)

전체 **29 threads / 34 messages**, open 18·resolved 11, tracked change 1개다. 본문 anchor가 있는 것은 28개이고 1개는 unanchored thread다. 따라서 전체 보존 확인은 `all_threads.md` 또는 JSON을 기준으로 한다. PDF에는 본문 위치 하이라이트가 자동 생성되지 않았다. exporter의 위치 매칭 실패를 원문이 반드시 바뀌었다는 증거로 해석하지 않는다.

## CVPR — 최신본과 이전 다운로드

프로젝트: [CVPR2027-chsong's intern](https://www.overleaf.com/project/6a9c1b93c9b98e33cf8e5770)

- [최신 원본 PDF — 11페이지](cvpr/2026-09-28/original.pdf)
- [최신 코멘트 포함 PDF — 13페이지](cvpr/2026-09-28/commented.pdf)
- [전체 스레드·답글 대화록](cvpr/2026-09-28/all_threads.md)
- [본문 연결 코멘트 목록](cvpr/2026-09-28/comments-2026-09-28.md)
- [코멘트 JSON](cvpr/2026-09-28/comments.json)
- [전체 소스 ZIP — 26개 항목](cvpr/2026-09-28/project_source.zip)
- [코멘트 대상 Introduction](cvpr/2026-09-28/source/sec/1_intro.tex)
- [9월 27일 다운로드 PDF](cvpr/2026-09-27/commented.pdf) / [당시 코멘트](cvpr/2026-09-27/comments-2026-09-27.md)

전체 **18 threads / 20 messages**, 모두 open이다. 7개는 PDF 본문에 annotation이 있고 18개 모두 끝의 목록에 수록됐다. 이전 리서치의 `inputs/` 사본은 9월 27일 자료로 유지했다.

## 보존·검증

`source/`는 exporter가 받은 **코멘트가 달린 파일만** 담는다. 전체 프로젝트 원본은 각 `project_source.zip`이다. 원본 PDF와 annotation PDF를 분리했으며 ZIP CRC·PDF 페이지 수·download manifest의 SHA-256을 확인했다. `download_manifest.json`은 프로젝트 주소, 수집 시각, ZIP 파일 목록과 다운로드 파일 hash를 기록한다. 이후 생성한 `all_threads.md`는 JSON에서 만든 읽기용 파생 문서다.

우리 원고의 PDF·ZIP·코멘트는 Git에 포함한다. exporter 진단 로그와 자동 생성된 agent 지침 파일은 로컬에만 둔다. 참고논문 PDF의 별도 제외 정책은 상위 README를 따른다.
