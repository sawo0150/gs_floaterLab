# VIGS-SLAM paper rendering reference

출처: [`paper/refs/01_gs_slam/vigsslam.pdf`](../../../paper/refs/01_gs_slam/vigsslam.pdf),
supplementary Table 18(RPNG)과 Table 19(UTMM).

- [`vigs_before_color_refinement.csv`](vigs_before_color_refinement.csv): online
  Gaussian mapping 뒤, final color refinement 전 논문 VIGS-SLAM 수치.
- [`vigs_after_color_refinement.csv`](vigs_after_color_refinement.csv): 논문의 final
  color refinement 뒤 수치. pure-online baseline과의 직접 비교값으로 쓰지 않는다.

논문은 모든 비교 방법이 mapping에 사용하지 않은 frame에서 평가한다. 로컬
standalone 평가는 공개된 고정 split이 없어 `idx % 5 == 0` 중 해당 실행의 vanilla
keyframe을 제외한다. 따라서 장면별 차이는 참고값이며 엄밀한 재현 오차가 아니다.

논문 장비는 Intel i7-14700K + RTX 5090이다. Table 18/19의 rendering metric은
runtime 1.5x streaming 계약을 의미하지 않는다.
