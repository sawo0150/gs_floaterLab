# 원고 Fig.2 — 전체 렌더 + 확대 영역

## 사용자 요청

포스터 crop만 확대하는 대신 rgb_comparison.pdf처럼 전체 이미지와 확대 영역을 함께 보여준다.
1,400 / 2,600 iteration 두 시점을 사용하며 수렴 곡선은 유지한다. 작업 범위는 Fig.2다.

## 결과

- 곡선 위, 비교 이미지 아래. 두 열은 iteration, 두 행은 VIGS-SLAM / Ours다.
- 각 비교는 해당 checkpoint의 실제 전체 렌더와 같은 이미지의 ROI를 나란히 배치한다.
- 동일 frame1420 및 ROI (440,40,564,164). 원본 렌더 바이트를 SVG에 내장하며 보정·선명화 없음.
- 확대창 한 변 9.80 → 14.99mm (약 1.53배), 도판 86.49×66.31mm (이전 높이46.13mm).
- Graph 원시 값 총28개(각 방법14개), 범위 및 baseline 최고 PSNR의 최초 저장 checkpoint 도달 비교 유지.
- 별표의 의미는 지속 도달 또는 wall-time 가속이 아니다. 비교는 Carve OFF다.
- 800 iteration 이미지만 생략했으며 해당 곡선 측정점은 유지했다.
- 원고 Fig.2 캡션을 실제 전체 렌더/확대창·시점·행 배치에 맞췄다.
- Fig.3와 abstract는 수정하지 않았다. 전체 원고 컴파일은 수행하지 않았다.

## 검수

- PDF 고해상도 및 200dpi 단 폭 렌더에서 전체 이미지, ROI, 색상 대응, 연결선 및 글자 간격 확인.
- 첫 렌더에서 x축 글자 간격·y축 제목 잘림·상단 주석과 곡선 간섭을 발견해 수정했다.
- 최종 word bbox 중첩/페이지 밖 텍스트 0개, PDF Times New Roman embedding 확인.
- 이전 SVG의 곡선을 축 좌표에서 역변환해 새로운 SVG와 측정값 동일성 확인.
- current/fig3.pdf 및 원고 convergece_comparasion.pdf / photometric_convergence.pdf 바이트 일치.
- 원고 변경은 Fig.2 캡션에 한정되는지 직전 snapshot과 비교 확인.
- 직전 파일과 제작 코드는 archive/before_full_view_insets_2026-09-21/에 보존했다.
