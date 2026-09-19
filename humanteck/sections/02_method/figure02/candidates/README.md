# 실제 후보 24개

모든 이미지는 실제 저장 지도 렌더이며, Ours는 Carve off이다. ΔPSNR은 선택된 전체 영상 기준으로, 확대 영역이나 장면 평균 값이 아니다. 후보 ID를 클릭하면 전체 영상과 동일 영역 확대를 함께 볼 수 있다.

- [모음판 1: F01–F04](contact_sheet_01.png)
- [모음판 2: F05–F08](contact_sheet_02.png)
- [모음판 3: F09–F12](contact_sheet_03.png)
- [모음판 4: F13–F16](contact_sheet_04.png)
- [모음판 5: F17–F20](contact_sheet_05.png)
- [모음판 6: F21–F24](contact_sheet_06.png)

| 후보 | 데이터 / 장면 | Frame index | Vanilla PSNR | Ours PSNR | ΔPSNR |
| --- | --- | ---: | ---: | ---: | ---: |
| [F01](F01_comparison.png) | ARIA / aria301_305 | 1220 | 17.49 | 29.20 | +11.71 |
| [F02](F02_comparison.png) | ARIA / aria301_305 | 840 | 18.28 | 25.33 | +7.05 |
| [F03](F03_comparison.png) | ARIA / aria1253 | 270 | 22.67 | 27.82 | +5.15 |
| [F04](F04_comparison.png) | RPNG / table_06 | 1420 | 26.13 | 31.25 | +5.13 |
| [F05](F05_comparison.png) | ARIA / aria1253 | 895 | 22.09 | 26.86 | +4.77 |
| [F06](F06_comparison.png) | RPNG / table_06 | 2235 | 25.53 | 30.25 | +4.72 |
| [F07](F07_comparison.png) | RPNG / table_08 | 425 | 23.34 | 27.77 | +4.43 |
| [F08](F08_comparison.png) | RPNG / table_08 | 7505 | 21.93 | 26.35 | +4.41 |
| [F09](F09_comparison.png) | RPNG / table_03 | 4070 | 20.79 | 24.93 | +4.13 |
| [F10](F10_comparison.png) | RPNG / table_02 | 865 | 19.35 | 23.33 | +3.98 |
| [F11](F11_comparison.png) | RPNG / table_03 | 1965 | 20.26 | 24.03 | +3.77 |
| [F12](F12_comparison.png) | RPNG / table_07 | 3855 | 24.68 | 28.39 | +3.71 |
| [F13](F13_comparison.png) | RPNG / table_02 | 1265 | 20.52 | 24.17 | +3.65 |
| [F14](F14_comparison.png) | UTMM / square-1 | 1265 | 19.81 | 23.44 | +3.64 |
| [F15](F15_comparison.png) | RPNG / table_04 | 3965 | 20.89 | 24.42 | +3.53 |
| [F16](F16_comparison.png) | RPNG / table_05 | 5665 | 26.24 | 29.73 | +3.49 |
| [F17](F17_comparison.png) | RPNG / table_05 | 2945 | 25.21 | 28.67 | +3.47 |
| [F18](F18_comparison.png) | RPNG / table_01 | 330 | 23.78 | 27.22 | +3.43 |
| [F19](F19_comparison.png) | UTMM / square-2 | 150 | 19.44 | 21.76 | +2.31 |
| [F20](F20_comparison.png) | UTMM / ego-drive | 540 | 16.95 | 19.26 | +2.31 |
| [F21](F21_comparison.png) | UTMM / ego-centric-1 | 885 | 18.44 | 20.50 | +2.06 |
| [F22](F22_comparison.png) | UTMM / ego-centric-2 | 665 | 19.00 | 21.05 | +2.05 |
| [F23](F23_comparison.png) | UTMM / fast-straight | 115 | 14.41 | 16.45 | +2.04 |
| [F24](F24_comparison.png) | UTMM / slow-straight-2 | 120 | 15.97 | 17.98 | +2.01 |

단위는 dB. 표의 frame index는 평가 시퀀스 인덱스이며 원본 filename UID와 다를 수 있다. 원본 UID·run 경로·crop 좌표·해시는 `frames/Fxx/provenance.json`에 있다. 각 `frames/Fxx/`에는 가공하지 않은 전체 RGB PNG와 같은 좌표의 crop PNG가 함께 있다.

