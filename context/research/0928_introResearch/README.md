# Online Gaussian mapping Introduction research

조사일: 2026-09-28 (KST). 문헌 검색·원문 확인·기존 실험 해석 작업이며, 새 GPU 실험은 수행하지 않았다. Overleaf 본문도 변경하지 않았다.

**권장 중심 질문: 이미 관측한 장면을, 관측이 계속 들어오는 동안 어디까지 지도에 학습시킬 수 있는가?**

핵심은 프레임 수 자체보다 **tracking에 필요한 관측 집합과 mapping에 유용한 관측 집합의 차이**, 그리고 **새 관측의 학습과 과거 관측의 재사용이 같은 계산 예산을 경쟁한다는 점**이다. “모든 프레임을 쓰면 좋다” 또는 “global replay를 처음 도입했다”는 주장은 문헌과 현재 실험 모두로 방어하기 어렵다.

## 읽는 순서

**원고·댓글 모음:** [Overleaf 원고 아카이브](overleaf/README.md). 휴먼테크 2페이지 원고와 CVPR 원고의 원본 PDF, 코멘트 포함 PDF, 소스 ZIP, 댓글 목록을 날짜별로 보관한다.

1. [연구 흐름과 권장 문제 정의](01_research_synthesis.md): 두 질문의 근거·반례·robotics/graphics 독자의 관심사.
2. [논문별 근거와 직접 경쟁 연구](02_evidence_ledger.md): PDF 페이지, 확인한 내용, 인용하면 안 되는 확대 해석.
3. [우리 실험의 주장 범위와 필요한 비교](03_claims_and_validation.md): 현재 근거와 아직 검증할 가설 분리.
4. [Introduction 구성 및 영문 초안](04_introduction_blueprint.md): 코멘트 대응, 문단 역할, 증거 수준에 맞춘 초안.
5. [논문 목록](PAPERS.md), [BibTeX](references.bib), [검색·검증 기록](RESEARCH_LOG.md).

## 가장 먼저 읽을 원문

- **HI-SLAM2**, PDF p.7, Fig.5: tracking keyframe의 coverage 부족을 사후 프레임 추가로 보완. 우리 동기를 설명하는 구체적 사례.
- **Online 3D Gaussian Splatting Modeling with Novel View Selection**, PDF pp.4–5: 이미 non-keyframe 추가 학습을 제안. 반드시 구분할 직접 선행연구.
- **CaRtGS**, PDF p.3, Fig.2 및 pp.4–5: 과거 replay가 필요한 동시에, 오래된/새 keyframe의 학습량이 불균형해지는 문제.
- **EliGSiR**, PDF pp.2–5: 2026-09-17 preprint. admission/replay/계산 배분이라는 넓은 주제까지 겹친다. 문제의 중요성을 뒷받침하지만 신규성 범위를 좁혀야 하는 근거이기도 하다.

21편의 arXiv PDF를 `papers/`에 다운로드했다. `metadata/`에는 arXiv 메타데이터·버전 이력·SHA-256, `text/`에는 페이지 구분을 보존한 검색용 추출문을 저장했다. 핵심 비교 연구는 방법·평가 절을 읽었고, 배경 연구는 관련 절 위주로 확인했다. 전체 문헌을 빠짐없이 다룬 systematic review나 코드 재현 검증은 아니다.

원본 초안과 리뷰 코멘트는 `inputs/`에 읽기용 사본으로 보관했다. 오래된 방법 초안과 9월 26일 구현이 다른 부분은 최신 실험 문서를 우선했다.

Git에는 리서치 문서·서지/버전 정보·다운로드 스크립트와 우리 Overleaf 원고를 저장한다. 대용량 참고논문 PDF, 추출 전문, arXiv HTML은 로컬에 유지한다. 다른 컴퓨터에서는 `requests beautifulsoup4 pymupdf`를 설치한 Python으로 `download_papers.py`를 실행하면 manifest에 고정된 PDF와 검색용 텍스트를 복원한다.
