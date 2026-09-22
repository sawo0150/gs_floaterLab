#!/usr/bin/env python3
"""Build the selected Fig.2: compressed-axis curve (a), actual render/GT triptych (b).

CPU-only SVG composition, Inkscape PDF export, PDF-derived PNG preview.
Default: review output only. --install: also synchronize current and manuscript.
"""
import argparse
import base64
import hashlib
import html
import json
import re
import shutil
import subprocess
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'output'
STEM = 'fig3_ab_page_trim'
SOURCE = ROOT.parents[3] / 'results/figure03_scene_search_20260921/rpng/table_06/evaluation/curves.json'
MANUSCRIPT = ROOT.parents[2] / 'HumanTeck_Song_s_intern'
W, H = 2100, 1275
# Crop only the page, retaining every existing child element and coordinate.
# Inkscape visual bounds: y=19.1000..1208.9807; allow ~2 SVG units of edge padding.
PAGE_TOP, PAGE_BOTTOM = 17, 1211
PAGE_HEIGHT = PAGE_BOTTOM - PAGE_TOP
COLUMN_WIDTH_MM = 86.48540196485402
WIDTH_MM = COLUMN_WIDTH_MM * W / 1500
COLORS = {'baseline': '#000000', 'ours': '#0057FF', 'gt': '#E66100'}
ROI = (440, 40, 564, 164)
# Same physical text sizes and canvas width as the preceding selected figure.
FONT = {'tick_y': 44.4, 'tick_x': 45.6, 'axis_x': 50.4,
        'axis_y': 43.875, 'legend': 48, 'annotation': 48, 'image': 42}
CAPTION = r'''\caption{Photometric convergence on RPNG~\cite{chen2023monocular}
  \texttt{table\_06}.
  Insets show intermediate renderings from VIGS-SLAM~\cite{zhu2026vigs}
  (left) and ours (right).
  $^{*}$Our method first reaches the baseline's highest PSNR with
  1,000 fewer mapping iterations.}'''


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build():
    OUT.mkdir(exist_ok=True)
    (OUT / 'pdf').mkdir(exist_ok=True)
    (OUT / 'qa').mkdir(exist_ok=True)
    data = json.loads(SOURCE.read_text())
    curves = {arm: sorted((r for r in data['curves'] if r['arm'] == arm),
                          key=lambda r: r['iteration']) for arm in ('baseline', 'ours')}
    xl, xr = 205, 2070
    upper_top, upper_bottom = 20, 300
    lower_top, lower_bottom = 330, 380
    px = lambda k: xl + (xr - xl) * k / 2800
    high = lambda q: upper_bottom - (q - 19) / 7.5 * (upper_bottom - upper_top)
    low = lambda q: lower_bottom - (q - 14) / 5 * (lower_bottom - lower_top)
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH_MM}mm" '
         f'height="{WIDTH_MM * PAGE_HEIGHT / W}mm" viewBox="0 {PAGE_TOP} {W} {PAGE_HEIGHT}">',
         '<title>Photometric convergence and rendering comparison</title>',
         '<desc>Panel a: 555 fixed held-out views, unchanged checkpoint means, '
         'piecewise linear y-axis compressed below 19 dB, wavy separator at 19 dB. '
         'All 28 measurements retained, no smoothing or omitted PSNR interval. '
         'Panel b: frame1420, 1400 iterations, full views and identical magnified ROIs; '
         'left VIGS-SLAM, center Ours, right Ground truth. Carve disabled.</desc>',
         f'<rect width="{W}" height="{H}" fill="white"/>',
         '<defs>',
         f'<clipPath id="upper-range"><rect x="{xl}" y="{upper_top}" width="{xr-xl}" height="{upper_bottom-upper_top}"/></clipPath>',
         f'<clipPath id="lower-range"><rect x="{xl}" y="{lower_top}" width="{xr-xl}" height="{lower_bottom-lower_top}"/></clipPath>',
         '</defs>']

    def text(x, y, value, size, anchor='start', color='#111111', extra=''):
        s.append(f'<text x="{x}" y="{y}" font-family="Times New Roman" '
                 f'font-size="{size}" text-anchor="{anchor}" fill="{color}" {extra}>'
                 f'{html.escape(value)}</text>')

    def line(x1, y1, x2, y2, color='#333333', width=1.8, dash=''):
        extra = f' stroke-dasharray="{dash}"' if dash else ''
        s.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
                 f'stroke="{color}" stroke-width="{width}"{extra}/>')

    def rect(x, y, w, h, color, width=2.4):
        s.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" '
                 f'fill="none" stroke="{color}" stroke-width="{width}"/>')

    # Panel (a): both ranges have explicitly different linear scales.
    for q in (19, 21, 23, 25):
        yy = high(q)
        line(xl, yy, xr, yy, '#dddddd', 1.2, '4 7')
        line(xl - 8, yy, xl, yy)
        text(xl - 17, yy + 12, str(q), FONT['tick_y'], 'end')
    text(xl - 17, low(15) + 12, '15', FONT['tick_y'], 'end')
    line(xl - 8, low(15), xl, low(15))
    for k in (0, 800, 1600, 2400, 2800):
        xx = px(k)
        for yt, yb in ((upper_top, upper_bottom), (lower_top, lower_bottom)):
            line(xx, yt, xx, yb, '#e7e7e7', 1.1, '4 7')
        line(xx, lower_bottom, xx, lower_bottom + 8)
        text(xx, lower_bottom + 47, f'{k / 1000:g}', FONT['tick_x'], 'middle')
    for xx in (xl, xr):
        line(xx, upper_top, xx, upper_bottom)
        line(xx, lower_top, xx, lower_bottom)
    line(xl, upper_top, xr, upper_top)
    line(xl, lower_bottom, xr, lower_bottom)
    # A pair of waves marks the change in scale across the full plotting width.
    for mid in (310, 320):
        commands = [f'M {xl-10} {mid}']
        x = xl - 10
        while x < xr + 10:
            end = min(x + 100, xr + 10)
            half = (end - x) / 2
            commands.append(f'q {half / 2} -4 {half} 0 t {half} 0')
            x = end
        s.append(f'<path d="{" ".join(commands)}" fill="none" stroke="#888888" stroke-width="1.5"/>')
    text((xl + xr) / 2, 486, 'Mapping iterations (×10³)', FONT['axis_x'], 'middle')
    text(120, 205, 'PSNR (dB) ↑', FONT['axis_y'], 'middle',
         extra='transform="rotate(-90 120 205)"')
    text(35, 215, '(a)', FONT['image'], 'middle')

    # Indicate the shared checkpoint used by the two rendered images in (b).
    # The guide starts at the measured point and is interrupted at the axis break.
    selected_x = px(1400)
    selected_ours = next(r for r in curves['ours'] if r['iteration'] == 1400)
    for y0, y1 in ((high(selected_ours['mean_psnr']), upper_bottom), (lower_top, lower_bottom)):
        line(selected_x, y0, selected_x, y1, '#777777', 1.6, '5 6')
    line(selected_x, lower_bottom, selected_x, lower_bottom + 8, '#555555')
    text(selected_x, lower_bottom + 47, '1.4', FONT['tick_x'], 'middle', '#333333')

    point_records = []
    for arm, rows in curves.items():
        dash = ' stroke-dasharray="14 9"' if arm == 'baseline' else ''
        # Clip the same full polyline into each linear range. This preserves
        # exact line interpolation through 19 dB without false bridging.
        for name, transform in (('upper', high), ('lower', low)):
            pts = ' '.join(f'{px(r["iteration"]):.8f},{transform(r["mean_psnr"]):.8f}' for r in rows)
            s.append(f'<g clip-path="url(#{name}-range)"><polyline id="curve-{arm}-{name}" '
                     f'points="{pts}" fill="none" stroke="{COLORS[arm]}" '
                     f'stroke-width="4.6" stroke-linejoin="round"{dash}/></g>')
        for r in rows:
            yy = (high if r['mean_psnr'] >= 19 else low)(r['mean_psnr'])
            s.append(f'<circle id="measurement-{arm}-{r["iteration"]}" cx="{px(r["iteration"])}" '
                     f'cy="{yy}" r="3.2" fill="{COLORS[arm]}"/>')
            point_records.append({'arm': arm, 'iteration': r['iteration'], 'psnr': r['mean_psnr'],
                                  'x': px(r['iteration']), 'y': yy,
                                  'range': 'upper' if r['mean_psnr'] >= 19 else 'lower'})
    best = max(curves['baseline'], key=lambda r: r['mean_psnr'])
    first = next(r for r in curves['ours'] if r['mean_psnr'] >= best['mean_psnr'])
    assert (first['iteration'], best['iteration']) == (1400, 2400)
    xa, xb, ay = px(1400), px(2400), 85
    line(xa, ay, xb, ay, '#555555', 1.6, '5 5')
    for xx, r, arm in ((xa, first, 'ours'), (xb, best, 'baseline')):
        yy = high(r['mean_psnr'])
        line(xx, ay - 5, xx, yy, '#555555', 1.5, '5 5')
        if arm == 'baseline':
            s.append(f'<path d="M {xx} {yy-6} l 6 6 l -6 6 l -6 -6 Z" '
                     f'fill="white" stroke="{COLORS[arm]}" stroke-width="2.4"/>')
    for arm in ('baseline', 'ours'):
        r = next(r for r in curves[arm] if r['iteration'] == 1400)
        s.append(f'<circle id="selected-checkpoint-{arm}" cx="{selected_x}" '
                 f'cy="{high(r["mean_psnr"])}" r="6" fill="white" '
                 f'stroke="{COLORS[arm]}" stroke-width="2.4"/>')
    text((xa + xb) / 2, 65, '1,000 fewer iter.*', FONT['annotation'], 'middle', '#333333')
    for arm, label, yy in (('baseline', 'VIGS-SLAM', 75), ('ours', 'Ours', 140)):
        line(265, yy, 330, yy, COLORS[arm], 4.6, '14 9' if arm == 'baseline' else '')
        text(350, yy + 14, label, FONT['legend'], color=COLORS[arm])

    # Panel (b): Fig.2-style full image, ROI locator, and overlapping enlargement.
    images = []
    image_y, image_w, inset_y, inset_w = 570, 630, 795, 360
    image_h = image_w * 344 / 616
    for j, (arm, label) in enumerate((('baseline', 'VIGS-SLAM'), ('ours', 'Ours'), ('gt', 'Ground truth'))):
        x = 115 + j * 655
        src = ROOT / 'candidates/scene_search/table_06/frame_1420' / ('gt.png' if arm == 'gt' else f'{arm}_01400.png')
        raw = src.read_bytes()
        assert (int.from_bytes(raw[16:20], 'big'), int.from_bytes(raw[20:24], 'big')) == (616, 344)
        uri = 'data:image/png;base64,' + base64.b64encode(raw).decode()
        color = COLORS[arm]
        display_label = f'{label} (1.4k)' if arm != 'gt' else label
        text(x + image_w / 2, 1200, display_label, FONT['image'], 'middle', color)
        s.append(f'<image id="full-{arm}" x="{x}" y="{image_y}" width="{image_w}" '
                 f'height="{image_h}" href="{uri}"/>')
        scale = image_w / 616
        rx, ry = x + ROI[0] * scale, image_y + ROI[1] * scale
        rw, rh = (ROI[2] - ROI[0]) * scale, (ROI[3] - ROI[1]) * scale
        ix = x + 2
        assert ix + inset_w < rx and ry + rh < inset_y
        d = f'M {rx} {ry+rh} L {ix} {inset_y} M {rx+rw} {ry+rh} L {ix+inset_w} {inset_y}'
        for stroke, width in (('white', 5), (color, 2.5)):
            s.append(f'<path d="{d}" fill="none" stroke="{stroke}" stroke-width="{width}" stroke-dasharray="9 6"/>')
            rect(rx, ry, rw, rh, stroke, width)
        s.append(f'<rect x="{ix-4}" y="{inset_y-4}" width="{inset_w+8}" height="{inset_w+8}" fill="white"/>')
        clip = f'crop-{arm}'
        s.append(f'<defs><clipPath id="{clip}"><rect x="{ix}" y="{inset_y}" width="{inset_w}" height="{inset_w}"/></clipPath></defs>')
        zscale = inset_w / (ROI[2] - ROI[0])
        s.append(f'<g clip-path="url(#{clip})"><image id="detail-{arm}" '
                 f'x="{ix-ROI[0]*zscale}" y="{inset_y-ROI[1]*zscale}" '
                 f'width="{616*zscale}" height="{344*zscale}" href="{uri}"/></g>')
        rect(ix, inset_y, inset_w, inset_w, color, 3)
        images.append({'arm': arm, 'iteration': None if arm == 'gt' else 1400,
                       'source': str(src), 'sha256': sha(src), 'roi': ROI,
                       'full_box': [x, image_y, image_w, image_h],
                       'roi_box': [rx, ry, rw, rh], 'zoom_box': [ix, inset_y, inset_w, inset_w]})
    text(35, 875, '(b)', FONT['image'], 'middle')
    s.append('</svg>')
    svg = OUT / f'{STEM}.svg'
    svg.write_text('\n'.join(s) + '\n')
    tree = ET.parse(svg)
    ns = {'s': 'http://www.w3.org/2000/svg'}
    for p in point_records:
        node = tree.find(f'.//s:circle[@id="measurement-{p["arm"]}-{p["iteration"]}"]', ns)
        xx, yy = float(node.attrib['cx']), float(node.attrib['cy'])
        back_k = (xx - xl) / (xr - xl) * 2800
        back_q = (19 + (upper_bottom - yy) / (upper_bottom - upper_top) * 7.5 if p['range'] == 'upper'
                  else 14 + (lower_bottom - yy) / (lower_bottom - lower_top) * 5)
        assert abs(back_k - p['iteration']) < 1e-7 and abs(back_q - p['psnr']) < 1e-10
    assert len(point_records) == 28
    for im in images:
        for prefix in ('full', 'detail'):
            node = tree.find(f'.//s:image[@id="{prefix}-{im["arm"]}"]', ns)
            assert hashlib.sha256(base64.b64decode(node.attrib['href'].split(',', 1)[1])).hexdigest() == im['sha256']
    pdf = OUT / 'pdf' / f'{STEM}.pdf'
    subprocess.run(['inkscape', str(svg), f'--export-filename={pdf}'], check=True, capture_output=True)
    subprocess.run(['pdftoppm', '-singlefile', '-png', '-scale-to', '2100', str(pdf), str(OUT / STEM)], check=True)
    subprocess.run(['pdftoppm', '-singlefile', '-png', '-r', str(200 * COLUMN_WIDTH_MM / WIDTH_MM),
                    str(pdf), str(OUT / 'qa' / f'{STEM}_column')], check=True)
    provenance = {'layout': '(a) compressed-axis curve above (b) full views with magnified ROIs',
                  'frame': 1420, 'scene': 'table_06', 'heldout_views': 555, 'carve_enabled': False,
                  'width_mm': WIDTH_MM, 'height_mm': WIDTH_MM * PAGE_HEIGHT / W,
                  'column_width_mm': COLUMN_WIDTH_MM, 'column_height_mm': COLUMN_WIDTH_MM * PAGE_HEIGHT / W,
                  'page_crop': {'original_viewbox': [0, 0, W, H],
                                'cropped_viewbox': [0, PAGE_TOP, W, PAGE_HEIGHT],
                                'visual_bounds_y': [19.10002251791914, 1208.9806718767497],
                                'height_reduction_percent': (H - PAGE_HEIGHT) / H * 100,
                                'content_coordinates_and_sizes_unchanged': True},
                  'colors': COLORS, 'font_sizes_svg': FONT, 'font_sizes_preserved': True,
                  'panel_label_position': 'left gutter, vertically centered beside each panel',
                  'method_label_position': 'below images',
                  'checkpoint_link': {'iteration': 1400, 'plot_x_tick': '1.4',
                                      'plot_guide': 'vertical dashed, interrupted at y-axis break',
                                      'plot_markers': 'circles on both methods',
                                      'image_labels': 'VIGS-SLAM (1.4k) / Ours (1.4k) / Ground truth'},
                  'curve_source': str(SOURCE), 'curve_sha256': sha(SOURCE),
                  'curve_points_total': len(point_records), 'curve_points_per_method': 14,
                  'curve_values_unchanged': True, 'measurements': point_records,
                  'y_axis': {'kind': 'piecewise linear with wavy separator', 'boundary_db': 19,
                             'lower_range_db': [14, 19], 'lower_y_svg': [380, 330],
                             'upper_range_db': [19, 26.5], 'upper_y_svg': [300, 20],
                             'omitted_values': False, 'smoothing': False},
                  'images': images, 'ours_iteration': 1400, 'baseline_iteration': 2400,
                  'iteration_difference': 1000, 'baseline_best_psnr': best['mean_psnr'],
                  'definition': 'First stored checkpoint at or above baseline best; not sustained attainment or wall-time speedup.',
                  'caption_latex': CAPTION, 'svg_sha256': sha(svg), 'pdf_sha256': sha(pdf)}
    (OUT / f'{STEM}_provenance.json').write_text(json.dumps(provenance, indent=2) + '\n')
    (OUT / 'qa' / f'{STEM}_validation.json').write_text(json.dumps({
        'all_28_measurements_recovered_from_svg': True, 'embedded_full_and_detail_images_match_source_bytes': True,
        'same_roi_for_three_columns': True, 'original_image_pixels_unchanged': True,
        'font_sizes_preserved': FONT, 'column_height_mm': provenance['column_height_mm']}, indent=2) + '\n')
    print(json.dumps({'pdf': str(pdf), 'column_height_mm': provenance['column_height_mm']}))
    return svg, pdf, provenance


def install(svg, pdf, provenance):
    # Resolve the complete figure block before writing any manuscript/current files.
    paper = MANUSCRIPT / 'paper.tex'
    source = paper.read_text()
    pattern = r'(\\includegraphics[^\n]*\{figure/(?:convergece_comparasion|photometric_convergence)\.pdf\}\s*)\\caption\{.*?(?=\n\s*\\label\{fig:photometric_convergence\})'
    updated, count = re.subn(pattern, lambda m: m.group(1) + CAPTION, source, flags=re.S)
    assert count == 1, 'Expected exactly one current convergence figure block'
    assert sha(svg) == provenance['svg_sha256'] and sha(pdf) == provenance['pdf_sha256']
    cur = ROOT / 'current'
    cur.mkdir(exist_ok=True)
    for src, name in ((svg, 'fig3.svg'), (pdf, 'fig3.pdf'), (OUT / f'{STEM}.png', 'fig3.png'),
                      (OUT / f'{STEM}_provenance.json', 'provenance.json')):
        shutil.copy2(src, cur / name)
    for name in ('convergece_comparasion.pdf', 'photometric_convergence.pdf'):
        shutil.copy2(pdf, MANUSCRIPT / 'figure' / name)
    paper.write_text(updated)
    (cur / 'caption.md').write_text('# 원고 Fig.2 현행 캡션\n\n```latex\n' + CAPTION + '\n```\n\n'
        '곡선: 555 fixed held-out views, Carve OFF, matched total rendering budgets.\n'
        '19 dB 아래는 축척을 압축하며 물결로 구분한다. 28개 원본 측정값은 모두 유지한다.\n'
        '별표: baseline 최고 PSNR의 최초 저장 checkpoint 도달. 지속 도달이나 wall-time 가속이 아니다.\n')
    (cur / 'README.md').write_text('''# 현행 수렴 비교 — 원고 Fig.2

작업 폴더명 figure03 및 fig3.* 파일명은 유지한다.

- [PDF](fig3.pdf) / [미리보기](fig3.png) / [SVG](fig3.svg)
- [캡션](caption.md) / [출처·좌표](provenance.json)

2026-09-22: (a) PSNR 곡선과 (b) 렌더 비교를 상하 패널로 분리했다.
(a)/(b) 표기는 각 패널 왼쪽에, 방법명은 사진 아래에 둔다.
사진 아래에 VIGS-SLAM (1.4k), Ours (1.4k), Ground truth를 각각 한 줄로 적는다.
괄호는 mapping iteration이며 1.4k는 1,400회를 뜻한다.
이번 색상 변경에서는 원고 캡션 문구를 유지하고 current/ 및 생성 스크립트에 동기화했다.
(a)의 1.4k tick·중립 점선·두 측정점 원형 표시로 (b)의 checkpoint를 연결한다.
(a)는 RPNG table_06의 고정 held-out 555뷰 평균, 각 방법 14개 원본 측정점이다.
19 dB 이상은 넓게, 14–19 dB는 얇은 구간에 압축하며 물결 두 줄로 축척 변화를 표시한다.
값을 생략하거나 smoothing하지 않는다. 최초 도달 비교는 Ours 1400 / baseline 2400이다.
(b)는 frame1420의 1400 iteration: VIGS-SLAM / Ours / Ground truth 순서다.
전체 화면에 동일 ROI=(440,40,564,164)를 표시하고 같은 영역을 확대한다.
원본 PNG를 그대로 SVG에 내장하며 색상/선명도 보정은 없다.
Baseline은 검정(#000000), Ours는 선명한 파랑(#0057FF), GT는 주황(#E66100)이다.
2026-09-22 색상 변경: GT 글자·ROI 테두리·확대 테두리·연결선에 주황을 적용했다.
직전 버전과 SVG 폭·물리 폭·글자 크기·모든 내부 도형 좌표를 유지한다.
페이지 위아래 여백만 잘라 viewBox를 0 17 2100 1194로 변경했다.
단 폭 삽입 높이는 약49.17mm로 이전52.51mm보다6.35% 줄었다.

재생성(워크스페이스 루트에서):
`python3 humanteck/sections/02_method/figure03/scripts/build_selected_B.py`
기본 실행은 output/에 검토본만 생성한다. PDF를 PNG로 렌더링하여 검수한 뒤
`--install`로 current/ 및 원고 PDF 두 파일·캡션을 동기화한다.
설치 시 원고 캡션을 스크립트 CAPTION으로 갱신하므로 캡션 수정도 함께 반영해야 한다.
표기 참고: analysis/checkpoint_label_review_2026-09-22.md (3DGS-LM / Turbo-GS 실제 figure).
전체 원고 컴파일·인쇄는 별도다. 이전 버전은 archive/ 및 output/에 보존한다.
''')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--install', action='store_true')
    args = parser.parse_args()
    result = build()
    if args.install:
        install(*result)
