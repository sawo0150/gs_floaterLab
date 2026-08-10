# 3DGS Floater 연구 공유 폴더 (share/)

이 폴더는 3DGS floater 제거 연구와 관련한 사용자 라벨 데이터, Delaunay 3D 삭제 영역(Region GT), 그리고 개선 및 비교용 PLY 결과들을 모아둔 공유 폴더입니다.

## 폴더 구조

- **[floater_share/](file:///home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/share/floater_share)**: 기존에 배포된 floater 관련 연구 자료들입니다.
  - `01_labels/`: 사용자 라벨 데이터 (원본 `original`과 청소본 `user_cleaned` PLY 쌍).
  - `02_region_gt/`: Delaunay 사면체 채움으로 가공한 3D 삭제 영역 마스크 (`.npz`).
  - `03_results/`: baseline 및 1253 챔피언 등 주요 비교용 PLY 파일들.
  - `README.md`: 기존 floater_share의 가이드 및 설명서.
- **[improved_results/](file:///home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/share/improved_results)**: 최신 실험(exp46 완주 기준)으로 도출된 **12F 및 305호 개선 PLY 파일들**입니다.
  - `12F__improved_highest_quality_exp46_ax7b.ply`: 12F 최고 화질 모델 (PSNR 35.18 dB, 먼지 236개)
  - `12F__improved_min_dust_exp46_ax3.ply`: 12F 최소 먼지 모델 (PSNR 34.93 dB, 먼지 192개)
  - `305__improved_exp46_ax1.ply`: 305호 최고 성능 모델 (PSNR 35.84 dB, 가시 먼지 단 4개)

## 📌 주요 비교 포인트

1. **12F (로비 fog) 씬의 품질 개선**
   - 12F__original ↔ 12F__improved_highest_quality_exp46_ax7b ↔ 12F__improved_min_dust_exp46_ax3
   - 기존 baseline(32dB) 대비 **화질이 35dB를 돌파**하며, 공중 먼지를 **80% 이상 청소**하는 압도적 품질 차이를 확인할 수 있습니다.
2. **305호 (다른 방) 씬의 먼지 99% 제거**
   - 305__baseline ↔ 305__improved_exp46_ax1
   - 베이스라인 대비 화질은 35.84 dB로 초고화질을 유지하며, 가시 먼지는 461개에서 **단 4개만 남기는 극적인 먼지 제거**를 확인할 수 있습니다.

---
각 파일의 세부 통계는 [floater_share/README.md](file:///home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/share/floater_share/README.md)를 참조하십시오.
