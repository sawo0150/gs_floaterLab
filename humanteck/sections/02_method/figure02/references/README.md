# Fig. 2 참고 도판

## 2026-09-20 추가 검토: 통합 확대창과 주장에 맞는 ROI

이전의 전체/확대 2행 구성은 보존하되, 사용자 피드백 이후 현재 제안은 **한 행의 세 패널 + 각 패널 내 확대 inset**이다. 상세 판단은 [motivation·기여·레이아웃 연결 노트](../analysis/motivation_and_layout_revision_2026-09-20.md)에 있다.

| 추가 논문 | 확인 도판 | 확인한 표현과 적용 범위 |
| --- | --- | --- |
| SEGS-SLAM, ICCV 2025 | [Fig. 8–9, 8쪽](segs_slam_fig8_9_page8.png) | 작은 ROI와 확대창을 실선으로 연결한다. Fig. 9 하단은 커튼 무늬 확대를 영상 내에 배치한다. 이번에는 이를 가는 점선의 두 연결선으로 변형하며, 원문에 같은 사다리꼴이 있다고 주장하지 않는다. |
| 3D Gaussian Rendering Can Be Sparser: Efficient Rendering via Learned Fragment Pruning, NeurIPS 2024 | [Fig. 3, 9쪽](fragment_pruning_fig3_page9.png) | 숫자·점선·잎사귀를 확대해 구체적인 appearance 차이를 논의한다. PSNR 차이만이 아니라 논문의 주장에 맞는 관찰 대상을 고르는 방식이 참고점이다. |

공식 원문: [SEGS-SLAM](https://www.openaccess.thecvf.com/content/ICCV2025/papers/Wen_SEGS-SLAM_Structure-enhanced_3D_Gaussian_Splatting_SLAM_with_Appearance_Embedding_ICCV_2025_paper.pdf), [Fragment Pruning](https://proceedings.neurips.cc/paper_files/paper/2024/file/0b2de71212384ffcaf80ad9fd1a21fe3-Paper-Conference.pdf). 두 PDF도 이 폴더에 저장했다.

## 최초 검토 기록

이번 그림은 시스템 overview인 Fig. 1과 달리 **정성 비교 그림**이다. 따라서 이번에는 각 논문의 정성 비교 도판을 참고했다. 아래 PNG는 출처 확인용 논문 페이지이며, 우리 논문에 그대로 삽입하는 자산이 아니다.

| 논문 / 도판 | 저장한 페이지 | 구성에서 참고할 점 | 이번 그림에 적용하지 않을 점 |
| --- | --- | --- | --- |
| Gaussian Splatting SLAM (MonoGS), CVPR 2024, Fig. 4 | [7쪽](monogs_fig4_page7.png) | 방법별 열을 유지하고 전체 영상 아래 같은 위치의 확대 영상을 배열한다. 전체 장면과 세부 차이가 동시에 읽힌다. | 여러 장면을 작은 크기로 쌓는 구성은 단일 단 Fig. 2에서 생략한다. |
| Photo-SLAM, CVPR 2024, Fig. 6 | [6쪽](photoslam_fig6_page6.png) | 같은 ROI를 일관된 색으로 표시해 비교할 위치를 알려준다. | 여러 방법 열과 영상 내부 inset을 모두 넣으면 단일 단에서 복잡해지므로 사용하지 않는다. |
| CaRtGS, Fig. 6 | [7쪽](cartgs_fig6_page7.png) | 동일 장면과 표시된 관심 영역으로 방법 간 차이를 비교한다. | 많은 방법을 배치하고 GT를 크게 따로 두는 비대칭 구성은 사용하지 않는다. |

원문 출처: [MonoGS 공식 논문](https://openaccess.thecvf.com/content/CVPR2024/papers/Matsuki_Gaussian_Splatting_SLAM_CVPR_2024_paper.pdf), [Photo-SLAM 공식 프로젝트](https://huajianup.github.io/research/Photo-SLAM/), [CaRtGS 원문](https://arxiv.org/abs/2410.00486).

## 채택한 구조

- 열: VIGS-SLAM / Ours / Ground truth, 동일 크기.
- 첫 행: 대표 장면의 전체 RGB 영상과 동일 좌표의 ROI 사각형.
- 둘째 행: 같은 ROI를 크게 확대. 세 열의 확대율과 보간 방식은 동일하게 유지한다.
- Times New Roman, 흰 배경, 얇은 황색 ROI 표시. 장식용 화살표나 그림자 없이 영상 자체에 공간을 준다.
- PSNR은 후보 검토 카드에서만 먼저 표시한다. 본문 그림의 수치 포함 여부는 최종 크기에서 결정한다.

수상자 조언의 취지에 맞춰 한 장면을 크게 보여주고, 숫자를 읽기 전 어떤 차이가 있는지 알아볼 수 있게 한다. 구조 검토용 생성 이미지는 실험 결과가 아니며, 실제 최종 도판에는 저장된 지도에서 렌더링한 영상만 사용한다.
