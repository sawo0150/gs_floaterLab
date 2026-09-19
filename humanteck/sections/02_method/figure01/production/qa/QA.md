# Vector layout proof QA

## 화살표 확대 검수 — 2026-09-20

- `qa/arrows/`에 5개 영역의 before/after PDF 3배 확대 crop을 저장하고 직접 확인했다. 제목 침범, 가려진 화살촉, 좁은 평행선 간격, normal 입력/base 출력 교차를 정리했다.
- 화살촉을 동일 크기의 직접 그린 벡터 삼각형으로 바꿔 PDF marker export의 작은 shaft 돌출을 제거했다. 지도 양쪽 진입점은 실제 이미지 표시 범위에 맞춰 같은 높이와 4단위 간격으로 정렬했다.
- 초기화/관측/완료 update 및 RGB/prior 교차는 비연결 틈으로 구별한다. Update 선의 실제 feedback 분기만 점으로 표시한다.
- 이전 SVG 대비 text 92개, image 25개, rect 163개, ellipse 8개의 속성·내용·좌표 동일성 확인. 사진·글자·배치 변경 없음.
- 최종 PDF 재렌더, SVG parse/export, Times New Roman embedding 확인. 원본 자산·GPU·실험·본문 TeX는 건드리지 않았다.
- 직전 PDF/PNG/SVG와 builder는 archive/before_arrow_cleanup/에 보존했다.

## 벽 정렬·점 표시 추가 검수 — 2026-09-20

- 현재는 벽 정렬 S5(yaw 0°, elevation 24°), 표시 Gaussian 30,587개다. 아래 초기 S3·43,706개 기록은 이전 이력이다.
- 벽 band 중심에 RANSAC/SVD 평면 추정: 1,510/6,000 지지점, RMS 0.02235m. 법선은 표시 방향 추정이지 GT가 아니다. 같은 벽 좌표로 공간 절단하고 앞쪽·하단 범위를 다듬었다.
- 궤적 scatter alpha 0.34, size 0.85 적용. 실제 trajectory/frustum과 색상은 유지.
- 원본 PLY hash 불변, 모든 active asset hash 통과. K/I 및 C10 render/prior hash가 직전 archive와 모두 동일함을 확인.
- Python AST·SVG XML·Inkscape export 통과. PDF 재렌더를 직접 확인했고 Times New Roman 전체 embedded 확인. 변경 없는 레이아웃에서 지도 설명·화살표·폰트 겹침 없음. 본문 TeX compile은 미실행.
- 직전 산출물은 archive/before_wall_alignment/에 보존했다. 추가 학습·원본 지도 편집 없음.

## 현재 선택·cutaway 검수 — 2026-09-20

현재 산출물은 `current/overview.{svg,pdf,png}`다. 아래의 이전 미선택·Arial·UID284·내부 시점 기록은 과거 작업 이력이며 현재 상태가 아니다.

- 사용자 선택 C07(UID786) 영역 / C10(UID1091) modality / trajectory A 반영. K3 입력·rendered RGB/depth/normal·frontend prior의 UID1091 일치 확인.
- K/I UID1073/1079/1091/1104/1123의 실제 역할, mapping 포함, held-out 제외 assert 통과. 모든 active 자산의 SHA256 일치 확인.
- 궤적 A의 Gaussian 중심 점 표시 alpha 0.26, size 0.65 적용. 실제 pose·방향·지도 파라미터 변경 없음.
- Cutaway 6개 방향을 직접 열어 비교하고 S3 선택. C07 기준 공간 상자로 표시만 절단하며 원본 PLY는 그대로다. 43,706/177,099개를 표시하고 나머지는 이 도해에서만 숨긴다. Floater 선별이나 optimizer update가 아니다.
- 원본 PLY SHA256 `3c6b132bd64d3e0047b83c5c7673b0d320c9dfbf091ac66a66e88b43b2ac6766` 재확인. C10 modality는 모두 map_clip_applied=False.
- Python 2개 AST parse, SVG XML parse, Inkscape export 통과. PDF 1쪽, 510.236×244.576pt (180×86.28mm). Times New Roman Regular/Bold/Italic/BoldItalic embedding 확인.
- PDF를 Poppler로 다시 렌더해 직접 열었고 cutaway 설명과 Render 화살표 간격을 수정한 뒤 다시 확인했다. 기존 3열 구조·색상·폰트 유지, footer 잘림 없음.
- 기존 그림과 provenance는 archive/before_cutaway/에 보존했다. 선택된 자산을 구버전 default extractor가 덮어쓰지 않도록 무옵션 실행 보호 추가.
- 본문 TeX compile·실물 인쇄는 미실행. Run의 ray-space loss가 꺼져 있다는 해석 제한과 표시용 절단을 caption에 명시했다.

## 실제 pose 및 후보판 / 폴더 정리 추가

- 사용자 추가 선호: 구조는 유지하고 최종 overview만 Times New Roman Bold/Regular로 변경. 이전 Arial embedding 기록은 당시 이력이며 현재 글꼴은 Times New Roman이다.

- 새 Python 파일 없이 기존 2개를 scripts/로 이동해 diff 수정했다. 원본 결과는 archive/에 보존, 삭제 0개.
- 12개 후보 모두 같은 PLY·실제 prefinal keyframe pose로 재렌더링했다. RGB/depth/normal 및 prior가 같은 UID인지 assert하고 파일 hash를 candidates/manifest.json에 기록했다. 후보판 2개를 실제 열어 잘림·label 대응을 확인했다.
- C02가 이전 UID284다. 다만 후보판은 더욱 직접적인 prefinal keyframe pose를 사용하며 이전 overview의 dense evaluation trajectory와 수치가 조금 다를 수 있다. 비동일 pose 렌더를 pixel-identical이라고 주장하지 않는다.
- 실제 궤적은 endpoint의 115개 keyframe pose. 11개 frustum에 실제 R,t와 intrinsics 반영. 지도 Gaussian 중심에 같은 투영 적용. 과거 모형 trajectory 2개는 현재 overview에서 제거했다.
- 투영 A/B를 실제 열어 확인한 뒤 큰 상하 여백을 줄였다. PNG와 SVG를 함께 저장했고 overview에는 A를 임시 적용했다. 카메라 위치/방향은 실제, frustum 크기는 표시용이다.
- 현재 오른쪽은 아직 이전 view를 유지한다. candidates/manifest.json의 selected_candidate=null이며 사용자 선택 후 교체한다.
- 새 GPU 학습, optimizer, map pruning, RGB 보정 없음. 기존 GUI 프로세스는 그대로 두고 사용자 승인 범위의 저장 지도 렌더만 수행했다.
- current/overview.pdf를 Poppler로 다시 렌더해 실제 pose 배치 확인. 본문 TeX compile은 여전히 미실행.

## v02 실제 자산 재제작 검수 — 2026-09-19 추가

아래 v01 기록은 이력이다. 현재 산출물은 `overview_v12_vector_v02.*`이며 `build_overview_v02.py`를 diff로 유지한다.

- 사용자 승인 run: exp94 Aria1253 normalized_variance_s0. GPU는 지도 자산 렌더에만 사용했고 optimizer/update를 실행하지 않았다. 실험 성능을 새로 측정한 것이 아니다.
- 원본 v12와 v01, 현재 PDF 재렌더 결과를 직접 열어 비교했다. `v12_vs_vector_comparison.png`에도 원본/현재를 동일 크기로 나란히 저장했다. 기준 원본은 이동된 `../plan/overall_pipeline_v12.png`다.
- v12와 일치시킨 요소: 열 비율 약 26:38:36, cyan/peach/lavender 배경, navy heading, 왼쪽 trajectory/filmstrip/frontend/depth/normal, 중앙 3→4→5 pool/count/probability/selected view, 오른쪽 map/render/base/ray/update.
- 의도적인 차이: Arial로 글꼴 통일, 실제 Aria 입력과 prior/렌더 사용, I2 대신 K3를 selected-view 예시로 선택해 keyframe supervision과 대응. 큰 map 이미지는 가짜 cutaway room 대신 실제 wide-FOV 내부 시점으로 표시. ray는 특정 map 위치의 추출 결과가 아니므로 원본의 오해 가능한 `Ray detail` callout은 제거.
- 실제 K/I role, mapping inclusion, held-out exclusion을 archive/runtime과 assert로 검증. 같은 alias는 동일 SHA256 asset을 반복 사용한다. 입력과 출력 예시는 같은 run/scene이고 prior/render는 K3(UID284)다. Prior는 마지막 causal archive version(event112, emitted UID1274), map은 prefinal endpoint snapshot이며 학습 과정의 동일 순간을 기록한 스크린샷이라는 주장은 하지 않는다.
- 모든 frame modality는 시계방향 90도 표시 회전. RGB 보정 없음. Prior normal은 unit camera-space xyz→RGB, render normal은 VIGS depth_to_normal 결과를 사용한다. 색이 예쁘지 않다는 이유로 geometry/normal을 smoothing하지 않았다.
- 6개 외부 시점 렌더를 검토했으나 방 구조가 읽히지 않아 채택하지 않았다. 최종 내부 inspection view는 Gaussian 전체 유지, opacity/scale 변경 없음. 통상적인 view frustum 처리만 적용된다.
- 직접 확인하며 고친 항목: S+2κ 라벨 가림, render labels 충돌, history와 sampling 안내 겹침, selected-camera 라벨과 map/렌더 연결선 간섭. 마지막에는 sampling과 ray 영역을 PDF에서 확대 crop해 별도 확인했다.
- Probability bars: 설명용 counts 12/9/6/3/0, effective beta=0.1, round 10/14/18/25/33%. 현재 Method의 beta_s=1/[tau(T+1)]라면 이 예시 tau=10/31이며 실제 exp94의 sampling 이력을 그린 것이 아니다.
- Python compile + SVG XML parse + Inkscape export 성공. PDF를 Poppler로 재렌더해 확인했고 Arial Regular/Bold/Italic embedding을 확인했다. PNG 확인만으로 PDF 검수를 대신하지 않았다.
- PDF 크기 180×86.28mm. 일부 보조 label은 약 5–6pt여서 최종 지면에서 축소하지 않는 것이 좋다. 실제 본문 TeX 컴파일/인쇄 가독성은 아직 미확인(로컬 TeX engine 없음).
- **해석 제한:** 이 run의 causal carve=False다. 지도는 overview용 실제 예시이며 제안 ray loss의 개선 효과나 full-method 결과로 주장하지 않는다. TeX caption에 명시했다.
- 원본 생성 시안과 기존 TeX/실험 결과는 수정하지 않았다. 별도 신규 Python 파일을 계속 만드는 대신 현재 두 파일을 diff로 수정하는 사용자 방침을 계획과 README에 기록했다.

2026-09-19. 실제 그림 결과가 아니라 생성 파이프라인·글꼴·배치 검수다.

## 완료

- 수상작 전체 overview PDF 렌더 확인 및 pdffonts 확인.
- Times New Roman Regular/Bold 로컬 가용성 확인.
- Python compile 검사 및 SVG XML parse 성공.
- Inkscape SVG → PDF/PNG export 성공. 비치명적인 Pango/GTK wrapper warning이 있었으나 반환값은 0. PDF 렌더링과 embedded font를 별도로 검증했다.
- 출력 PDF page size 510.236 × 238.11pt ≈ 180 × 84mm.
- PDF에서 TimesNewRomanPS Regular/Bold/Italic subset embedding 확인.
- PDF를 pdftoppm 220dpi로 다시 렌더링해 PNG preview와 함께 확인. Keyframe depth/normal label과 queue 설명의 첫 버전 겹침을 수정했다.
- Probability p∝exp(-0.1 n), n=[12,9,6,3,0], 양수·합 1·역관계·반올림 [10,14,18,25,33] 확인.
- `--release`가 missing assets 상태에서 실패하는 것을 확인.
- 실제 RGB 5장 후보는 no crop/no rotation 상태로 출처·sha256과 별도 비교판 저장. 아직 overview의 K/I asset으로 배정하지 않았다.

## 대기 / 한계

- 사용자에게 대표 run을 질문한 상태. 후보 Aria baseline의 자료를 ours라고 사용하지 않는다.
- RGB, prior depth/normal, map, rendered RGB/depth/normal 슬롯 11개 미확정. Final release 불가.
- Frontend prior와 rendered normal을 구분해 배치했으나 실제 데이터의 좌표계·mask·source 일치 여부는 해당 asset 확보 후 검증.
- 현재 ray schematic은 Carve의 premature opacity 억제 개념이다. Carve/Hit/hybrid 채택 결과를 확정한 것이 아니다.
- Pose는 schematic, pool/admission/count는 illustrative. 실제 online event trace를 시각화한 것이 아님.
- Base와 ray geometry의 병렬 합류, update return, history→count 등 기본 endpoint는 코드로 통제한다. 최종 scene 넣기 전 selected camera→renderer 경로, depth-only gate, map ray contributor 입력을 더 명료하게 정리할 수 있다.
- 현재 84mm 높이는 font/layout proof용이다. 2쪽 휴먼테크 실제 조판에서 높이를 확정해야 한다.
- Print 100% 물리 출력 및 TeX compile은 아직 미실행. 현재 환경에서 pdflatex/xelatex/latexmk/tectonic을 찾지 못했다.
- 기존 생성 시안·사용자 수정·원본 수상작·TeX는 보존했다. GPU나 새로운 실험을 실행하지 않았다.
