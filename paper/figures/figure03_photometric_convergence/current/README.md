# 실제 photometric convergence

2026-10-01. 20개 후보 장면과 최종 held-out 1,280뷰를 확인한 뒤 RPNG table_06을 선택했다. 실제 checkpoint의 shared uniform64 held-out PSNR과 frame1975 렌더링을 사용한다.

- 방법별 실제 training-render 수를 표시하며, 중간 이미지는 같은 입력 prefix이나 완전히 같은 렌더 횟수는 아니다.
- 확대 위치는 GT 포스터 글자 영역에서 정하고 두 방법에 동일하게 적용했다.
- D3 proxy 렌더는 training budget 외의 추가 연산이다.
- [Caption](caption.md) · [Provenance](provenance.json) · [Figure](figure.pdf)
