# 3DGS Floater 공유 자료 요약 설명서

이 폴더는 3DGS 학습 시 불필요하게 생기는 공중 먼지(floater) 제거 실험의 핵심 데이터를 포함하고 있습니다.

## 1. 폴더 핵심 요약

*   **`floater_share/`**: 기존 학습 베이스라인 데이터 및 사용자 수동 청소 라벨
    *   `01_labels/`: 사용자가 수동으로 먼지를 지운 원본(`original.ply`) 및 청소본(`user_cleaned.ply`) 파일. 두 파일의 차이(diff)를 비교해 삭제할 먼지 점(floater)을 검출할 수 있습니다.
    *   `02_region_gt/`: 삭제된 먼지 영역을 3D Delaunay 사면체 채움으로 입체화한 기하 마스크 파일(`.npz`).
    *   `03_results/`: 기존 Carve Loss 알고리즘(exp40b 등)을 적용해 먼지를 지운 결과 PLY 파일들.
*   **`improved_results/`**: 최신 연구(exp46)를 통해 복원 화질을 극대화하고 먼지를 거의 제거한 **최종 개선 결과**
    *   `12F__improved_highest_quality_exp46_ax7b.ply`: 12F 씬의 최고 화질 모델 (PSNR 35.18 dB, 먼지 236개)
    *   `12F__improved_min_dust_exp46_ax3.ply`: 12F 씬의 최소 먼지 모델 (PSNR 34.93 dB, 먼지 192개)
    *   `305__improved_exp46_ax1.ply`: 305호 씬의 최고 성능 모델 (PSNR 35.84 dB, 먼지 단 4개 남음)

## 2. 뷰어 추천 비교 방법

1.  **3DGS 뷰어(예: SuperSplat 등)**에 다음 쌍을 함께 올려놓고 비교해 보시면 효과를 뚜렷하게 보실 수 있습니다.
2.  **12F (뿌연 로비 씬) 비교**:
    *   `share/floater_share/01_labels/12F__original.ply` (지저분한 상태)
    *   `share/improved_results/12F__improved_highest_quality_exp46_ax7b.ply` (화질 유지 + 먼지 제거)
3.  **305호 (깨끗한 방 씬) 비교**:
    *   `share/floater_share/03_results/305__baseline.ply` (지저분한 상태)
    *   `share/improved_results/305__improved_exp46_ax1.ply` (완벽하게 청소된 상태, 먼지 단 4개)
