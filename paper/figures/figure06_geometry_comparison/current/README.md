# 실제 covariance 타원체 검토본

20개 후보의 15/40 렌더 실험 80회가 모두 완료된 뒤 설치했다. Aria1253은 독립적인 수작업 empty-space reference가 있는 장면이므로 선택했다. PSNR 차이로 장면을 선택하지 않았다.

PLY 위치·크기·회전을 그대로 읽고 공통 시점·절단면·opacity cutoff로 CPU에서 solid ellipsoid를 렌더링한다. 색은 수작업 빈 공간 내/외를 표시하며 RGB render 색이 아니다. 현재 whole-system 비교이고 native geometry control은 아직 추가해야 한다.
