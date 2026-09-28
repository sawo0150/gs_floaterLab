# Research provenance and scope

## 작업 범위

- 요청: dense non-keyframe 활용과 과거 전체 training pool 유지가 기존 robotics/Gaussian mapping 연구의 어떤 문제와 연결되는지 조사하고 Introduction 방향을 제안.
- 수행일: 2026-09-28 KST. UTC metadata가 2026-09-27일 수 있다.
- `context/STATUS.md`의 최신 append 항목과 campaign 문서를 우선 확인했다. 오래된 best 표를 현재 전체 시스템의 성능으로 사용하지 않았다.
- 기존 Overleaf intro/comment export를 읽고 `inputs/`에 사본을 남겼다. 외부 프로젝트 수정·comment resolve·메시지 전송은 하지 않았다.
- 새 성능 실험을 하지 않았으므로 experiment card/INDEX/STATUS의 실험 완료 항목은 추가하지 않았다.

## 검색 경로

웹 검색은 논문 발견에 사용했고, 분석의 근거는 arXiv에서 직접 받은 원문 PDF다. 주요 검색어는 다음과 같다.

1. `Gaussian splatting SLAM keyframe selection forgetting global replay CaRtGS`
2. `Gaussian SLAM non keyframes dense supervision incremental mapping all frames`
3. `Gaussian SLAM non-keyframes`, `Gaussian SLAM replay keyframe`
4. `Online 3D Gaussian Splatting Modeling with Novel View Selection`
5. `Gaussian splatting frame selection online mapping`, `Gaussian SLAM forgetting 2025 2026`
6. `EliGSiR arxiv`, `IMGS-SLAM arxiv`, `GS3LAM arxiv`
7. `Splat-Nav SplatSim robot gaussian splatting`
8. `gaussian splatting VLA novel view augmentation policy 2025 2026`

대표 기반 연구에서 관련 참고문헌·인접 주제로 확장했고, 우리 접근을 지지하는 자료뿐 아니라 반례 설계도 확인했다. 검색 결과의 블로그·자동 요약·Reddit은 논문 주장의 근거로 쓰지 않았다.

## 읽기 깊이

- **직접 비교를 위한 방법/평가 절 확인:** iMAP, Co-SLAM, MonoGS, HI-SLAM2, CaRtGS, Online NVS, EliGSiR, VIGS-SLAM.
- **관련 설계 절 확인:** SplaTAM, RP-SLAM, RTG-SLAM, GLC-SLAM, GS3LAM, Splat-SLAM, Photo-SLAM, MVS-GS.
- **표현/응용 배경 확인:** 3DGS, Splat-Nav, SplatSim, GS for Autonomy, GS-VLA.
- 총 21 PDFs/309 pages를 저장했다. 모든 페이지를 동일 깊이로 정독했다는 뜻은 아니다.

## 검색 중 보았지만 핵심 근거로 채택하지 않은 후보

| 후보 | 처리 |
|---|---|
| IMGS-SLAM author GitHub | coverage-aware mapping-frame selection을 표방하는 가까운 후보. 이번 검색에서 arXiv 원문 ID를 확정하지 못해 핵심 비교표에서 제외. 추후 novelty 점검 대상 |
| DUDG-SLAM, Sensors 2026 | publisher 검색 결과에 historical replay 전략이 나타남. 이번 arXiv 원문 중심 조사에서는 깊이 검증하지 않아 기술적 결론의 근거로 쓰지 않음 |
| GQGS-SLAM, Neurocomputing 2026 | mapping/localization과 quality-aware keyframe의 인접 후보. full text 검증 전으로 watchlist에만 둠 |
| Feed-forward dynamic reconstruction/Instant Gaussian Stream | 시간축 입력이 있어도 본 과제의 static online SLAM replay와 문제 설정이 다름 |
| GS-VLA | 원문까지 읽고 보관했으나 누적 scene memory의 근거가 아니라 optional VLA motivation으로만 사용 |
| 동명 VIGS SLAM 2501.13402 | RGB-D+IMU 기반의 별도 연구. 현재 프로젝트 기반인 2512.02293과 혼동하지 않음 |

따라서 이 문서는 선택한 직접 관련 논문에 대한 집중 조사다. 2026-09-28까지의 모든 논문을 망라하거나 최초성을 인증하지 않는다.

## 중요하게 교정한 주장

1. MonoGS에는 이미 global random KF replay가 있다.
2. SplaTAM은 현재 incoming frame도 mapping에 쓰므로 모든 기존 방법을 KF-only로 일반화할 수 없다.
3. Online NVS는 non-KF 추가 supervision을 이미 다룬다.
4. EliGSiR는 admission과 장기 replay priority를 이미 분리한다.
5. HI-SLAM2의 post-keyframe insertion은 coverage mismatch의 직접 사례다.
6. VIGS-SLAM v2 main evaluation은 final BA/refinement 이전이다. 과거 로컬 polishing 관찰과 논문 protocol을 구분한다.
7. 최근 pool/전체 pool과 recent-count/lifetime-count는 다른 ablation이다.
8. 현재 dense 이득은 fixed-work 근거이며 동일 시간·live·geometry 이득이 아니다.

## 파일과 재현

- `paper_list.json`: 검색으로 확정한 arXiv ID.
- `download_papers.py`: requests/beautifulsoup4/pymupdf 사용. PDF와 추출문이 모두 있으면 재다운로드하지 않는다. Git clone 뒤에는 manifest의 버전과 SHA-256을 확인하며 로컬 PDF·추출문을 복원한다. 원문 업데이트는 기존 reviewed PDF를 덮어쓰기보다 새 폴더에 받아 비교한다.
- `metadata/*.html`: 다운로드 당시 arXiv abstract page.
- `metadata/*.json`: citation metadata, submission history, 페이지 수, SHA-256, 수집 시각.
- `manifest.json`: 이번 분석에서 사용한 PDF bytes와 버전 목록.
- `text/*.txt`: PDF 페이지 marker가 있는 검색용 텍스트. column order·수식·hyphenation은 추출 오차가 있으므로 정밀 인용은 PDF를 우선한다.
- `references.bib`: arXiv citation metadata로 작성한 UTF-8 preprint 항목. 최종 투고 시 출판 버전·venue·author 표기를 재확인한다.
- `inputs/local_source_hashes.json`: 이번에 참고한 주요 로컬 결과 문서의 hash. 큰 STATUS 전체를 복제하지 않았다.

PDF 일부에 MuPDF color-space warning이 있었으나 다운로드/텍스트 추출은 완료됐다. 최종 검사는 PDF 열기, 페이지 수, SHA-256, 문서 링크, citation key를 확인한다. LaTeX는 삽입용 section 초안이며 전체 논문 compile은 하지 않았다.
