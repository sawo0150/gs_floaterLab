# Fig. 2 — F04 확정 제작본

- [고해상도 PNG](rgb_comparison.png)
- [논문용 PDF](pdf/rgb_comparison.pdf)
- [편집 가능한 SVG](rgb_comparison.svg)
- [단일 단 150 dpi 크기 검토](rgb_comparison_column_150dpi.png)
- [출처·좌표·해시 기록](provenance.json)

사용자가 선택한 F04, RPNG table_06 / frame index 1420을 사용했다. 실제 검증된 Baseline/Ours/GT PNG만 삽입했으며, 생성형 이미지 편집·색 보정·선명화는 하지 않았다. 원본 데이터는 `../candidates/frames/F04/`에 있다.

## 디자인

승인된 mockup v2의 가로형 세 패널 및 통합 확대창 구조를 유지했다. 원본 ROI가 오른쪽 위에 있으므로 확대창은 왼쪽 아래에 배치하여 ROI를 가리지 않도록 했다. 동일한 ROI `(440, 40, 564, 164)`를 모든 방법에 적용했으며 기존 F04 crop과 pixel 단위로 동일함을 검증했다. 대응하는 두 모서리를 점선으로 연결하고, 확대창은 왜곡 없는 사각형으로 유지했다.

단일 단 실제 폭 약 86.49 mm, 높이 약 30.75 mm, 가로세로비 2.8125:1이다. 라벨은 약 7.08 pt Times New Roman이며 PDF에 subset embedding되어 있다. 이미지 자체는 raster이고 라벨·ROI 테두리·연결선은 vector다.

## 원고 반영

`humanteck/HumanTeck_Song_s_intern/figure/rgb_comparison.pdf`에 동일 PDF를 설치했다. 기존 Fig. 2의 `includegraphics[width=\linewidth]`가 이 파일을 사용한다. Fig. 2 캡션만 실제 비교 조건으로 갱신했으며, 다른 본문과 Fig. 1/3은 바꾸지 않았다.

현재 출력은 **Carve off**이며, 34,437 physical mapping renders씩 사용한 matched-work 비교다. 동일 wall time·Adam update 수·완전히 동일한 초기화라고 확장해서 주장하지 않는다. 한 시점의 high-gain 예시이지 평균 효과 또는 convergence 곡선이 아니다.

## 재생성

기존 후보 제작 스크립트에 `--figure`만 추가했다. 이 옵션은 CPU에서 기존 PNG를 조합하며 GPU·지도 재학습·재렌더를 수행하지 않는다.

```bash
/home/colin/miniconda3/envs/vigs-slam-5090/bin/python humanteck/sections/02_method/figure02/scripts/build_candidates.py --figure
```

SVG에서 Inkscape로 PDF를 만들고, **그 PDF를** Poppler로 렌더해 PNG를 검수한다. 2400 px 미리보기와 실제 PDF 치수의 150 dpi 출력에서 라벨 잘림·연결선 교차·ROI 가림이 없는지 확인했다. 원본 PNG 해시 보존, 세 crop의 원본 일치, PDF 폰트 embedding도 확인했다. 전체 manuscript 컴파일은 이번 검수 범위에 포함하지 않았다.
