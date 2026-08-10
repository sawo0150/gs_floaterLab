# improved_results - 최신 개선된 12F 및 305호 결과 PLY

이 폴더는 최신 가설 검증 사이클(`exp46`)을 통해 기존 베이스라인 대비 화질을 대폭 상승시키고, 공중 먼지를 극대화하여 청소한 최신 연구 성과 결과 PLY들을 포함하고 있습니다.

## 📂 파일 상세 정보

### 1. `12F__improved_highest_quality_exp46_ax7b.ply`
*   설명: 12F 씬의 최고 화질 모델 (`exp46_ax7b`, zmax=12 차단 인코딩 적용)
*   화질 (PSNR): **35.18 dB** (베이스라인 32.0dB 대비 **+3.18dB 극적 상승**)
*   먼지 개수 ($s>0.5$): 236개 (기존 먼지량 대비 **84% 청소 완료**)

### 2. `12F__improved_min_dust_exp46_ax3.ply`
*   설명: 12F 씬의 최소 먼지 모델 (`exp46_ax3`, surfconf 표면 확신도 prior 적용)
*   화질 (PSNR): **34.93 dB**
*   먼지 개수 ($s>0.5$): **192개** (기존 먼지량 대비 **87% 최다 청소 완료**)

### 3. `305__improved_exp46_ax1.ply`
*   설명: 305호 씬의 최고 성능 모델 (`exp46_ax1`, hybrid depth-lift init 적용)
*   화질 (PSNR): **35.84 dB** (베이스라인 34.5dB 대비 **+1.33dB 상승**)
*   먼지 개수 ($s>0.5$): **단 4개** (기존 가시 먼지 461개 대비 **99.1% 완벽 제거**)

---
## 💡 뷰어 추천 비교 방법
SuperSplat 등의 뷰어에서 아래 파일들을 함께 드래그하여 나란히 띄우면 개선 효과를 즉시 체감하실 수 있습니다.
*   **12F 씬 비교**: `share/floater_share/01_labels/12F__original.ply` (지저분한 원본) $\leftrightarrow$ `share/improved_results/12F__improved_highest_quality_exp46_ax7b.ply`
*   **305호 씬 비교**: `share/floater_share/03_results/305__baseline.ply` $\leftrightarrow$ `share/improved_results/305__improved_exp46_ax1.ply`
