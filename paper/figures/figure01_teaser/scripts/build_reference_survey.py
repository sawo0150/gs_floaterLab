"""Extract inspected Fig. 1 panels for a local design reference, not results.

Inputs are original papers and read-only first-page renders in /tmp.
No source figure content is retouched. Bounding boxes exclude captions; source
pages, URLs, and crop rectangles are recorded for traceability.
"""
from pathlib import Path
import base64
import html
import json
import subprocess

WORK = Path('/home/intern/gs_floaterLab')
ROOT = WORK / 'paper/figures/figure01_teaser'
OUT = ROOT / 'references/2026-10-01_survey'
TMP = Path('/tmp/rogo_teaser_survey')

# name, rendered page, existing PDF, source URL, fractional crop, group
ROWS = [
    ('MonoGS', 'monogs_cvpr2024', 'view_selection/monogs_cvpr2024.pdf', 'https://arxiv.org/abs/2312.06741', (.08,.295,.91,.462), '01_scene_and_representation'),
    ('SplaTAM', 'splatam_cvpr2024', 'view_selection/splatam_cvpr2024.pdf', 'https://arxiv.org/abs/2312.02126', (.09,.244,.91,.465), '01_scene_and_representation'),
    ('HI-SLAM2', 'hi_slam2_2411.17982v3', 'view_selection/hi_slam2_2411.17982v3.pdf', 'https://arxiv.org/abs/2411.17982', (.075,.183,.925,.35), '01_scene_and_representation'),
    ('VIGS-SLAM', 'vigs_slam_zhu_et_al_arxiv_2512.02293v2', 'vigs_slam/vigs_slam_zhu_et_al_arxiv_2512.02293v2.pdf', 'https://arxiv.org/abs/2512.02293', (.22,.515,.78,.69), '01_scene_and_representation'),
    ('PGSR', 'pgsr', 'teaser_design/pgsr.pdf', 'https://zju3dv.github.io/pgsr/paper/pgsr.pdf', (.075,.245,.93,.62), '01_scene_and_representation'),
    ('2DGS', '2dgs', 'teaser_design/2dgs.pdf', 'https://www.cvlibs.net/publications/Huang2024SIGGRAPH.pdf', (.08,.244,.915,.495), '01_scene_and_representation'),
    ('EDGS', 'edgs_cvpr2026', 'convergence/edgs_cvpr2026.pdf', 'https://compvis.github.io/EDGS/', (.095,.287,.91,.485), '02_convergence_and_budget'),
    ('3DGS-LM', '3dgs_lm_iccv2025', 'convergence/3dgs_lm_iccv2025.pdf', 'https://lukashoel.github.io/3DGS-LM/', (.085,.264,.91,.472), '02_convergence_and_budget'),
    ('LM-RS', 'lm_rs_2504.12905v3', 'convergence/lm_rs_2504.12905v3.pdf', 'https://arxiv.org/abs/2504.12905', (.51,.30,.905,.434), '02_convergence_and_budget'),
    ('QuickSplat', 'quicksplat_iccv2025', 'convergence/quicksplat_iccv2025.pdf', 'https://openaccess.thecvf.com/content/ICCV2025/papers/Liu_QuickSplat_Fast_3D_Surface_Reconstruction_via_Learned_Gaussian_Initialization_ICCV_2025_paper.pdf', (.10,.282,.925,.45), '02_convergence_and_budget'),
    ('Taming 3DGS (published)', 'taming_published', 'teaser_design/taming_published.pdf', 'https://humansensinglab.github.io/taming-3dgs/docs/paper.pdf', (.08,.249,.93,.404), '02_convergence_and_budget'),
    ('Speedy-Splat', 'speedy_splat', 'teaser_design/speedy_splat.pdf', 'https://arxiv.org/pdf/2412.00578', (.09,.31,.91,.46), '02_convergence_and_budget'),
    ('CaRtGS', 'cartgs_2410.00486v2', 'convergence/cartgs_2410.00486v2.pdf', 'https://arxiv.org/abs/2410.00486', (.08,.178,.94,.447), '03_direct_comparisons'),
    ('Gaussian-SLAM', 'gaussian_slam_2312.10070v1', 'view_selection/gaussian_slam_2312.10070v1.pdf', 'https://arxiv.org/abs/2312.10070', (.085,.26,.895,.48), '03_direct_comparisons'),
    ('Splat-SLAM', 'splat_slam_cvprw2025', 'view_selection/splat_slam_cvprw2025.pdf', 'https://arxiv.org/abs/2405.16544', (.105,.28,.91,.495), '03_direct_comparisons'),
    ('RTG-SLAM', 'rtg_slam_2404.19706v1', 'view_selection/rtg_slam_2404.19706v1.pdf', 'https://arxiv.org/abs/2404.19706', (.09,.365,.955,.6), '03_direct_comparisons'),
    ('SplatMAP (page 2)', 'splatmap_p2', 'topology/splatmap_2501.07015.pdf', 'https://arxiv.org/abs/2501.07015', (.14,.154,.87,.433), '03_direct_comparisons'),
    ('Gaussian Opacity Fields', 'gof', 'teaser_design/gof.pdf', 'https://arxiv.org/pdf/2404.10772', (.09,.228,.92,.366), '03_direct_comparisons'),
    ('Photo-SLAM', 'photo_slam_cvpr2024', 'convergence/photo_slam_cvpr2024.pdf', 'https://arxiv.org/abs/2311.16728', (.508,.29,.893,.565), '04_problem_specific'),
    ('AERGS-SLAM', 'aergs_slam_cvpr2026', 'view_selection/aergs_slam_cvpr2026.pdf', 'https://github.com/zzy-2021/AERGS-SLAM', (.515,.267,.90,.437), '04_problem_specific'),
    ('GeoGS-SLAM', 'geogs_slam_2607.07452v1', 'convergence/geogs_slam_2607.07452v1.pdf', 'https://arxiv.org/abs/2607.07452', (.52,.19,.93,.56), '04_problem_specific'),
]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = []
    for name, stem, pdf, url, crop, group in ROWS:
        src = TMP / f'{stem}.png'
        w, h = map(int, subprocess.check_output(['identify', '-format', '%w %h', str(src)], text=True).split())
        x0, y0, x1, y1 = [round(v * d) for v, d in zip(crop, (w, h, w, h))]
        dest = OUT / f'{stem}_fig1.png'
        subprocess.run(['convert', str(src), '-crop', f'{x1-x0}x{y1-y0}+{x0}+{y0}', '+repage', str(dest)], check=True)
        manifest.append(dict(name=name, source_pdf=str(WORK/'paper/ref'/pdf), source_url=url,
                             pdf_page=2 if stem == 'splatmap_p2' else 1,
                             crop_fraction=crop, image=dest.name, group=group,
                             kind='original_paper_figure_excerpt_not_our_results'))
    (OUT/'sources.json').write_text(json.dumps(manifest, indent=2)+'\n')
    for group in dict.fromkeys(row['group'] for row in manifest):
        items = [r for r in manifest if r['group'] == group]
        height = 90 + ((len(items)+1)//2)*430
        svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="2000" height="{height}">',
               f'<rect width="2000" height="{height}" fill="white"/>',
               f'<text x="25" y="40" font-family="serif" font-size="30">{html.escape(group.replace("_"," "))} | Original Fig. 1 references</text>']
        for i, row in enumerate(items):
            x = 25 + (i % 2)*990
            y = 85 + (i // 2)*430
            encoded = base64.b64encode((OUT/row['image']).read_bytes()).decode()
            svg.append(f'<text x="{x}" y="{y}" font-family="serif" font-size="29" font-weight="bold">{html.escape(row["name"])}</text>')
            svg.append(f'<image x="{x}" y="{y+15}" width="950" height="370" preserveAspectRatio="xMidYMid meet" href="data:image/png;base64,{encoded}"/>')
        svg.append('</svg>')
        target = OUT / f'{group}.svg'
        target.write_text('\n'.join(svg))
        # Native raster montage avoids SVG renderer interpolation artifacts on
        # narrow, palette-encoded source figures. Original excerpts stay intact.
        args = ['montage', '-font', 'DejaVu-Sans', '-pointsize', '27', '-background', 'white']
        for row in items:
            args += ['-label', row['name'], str(OUT/row['image'])]
        args += ['-geometry', '950x370+20+20', '-tile', '2x', str(target.with_suffix('.png'))]
        subprocess.run(args, check=True)
    print(f'{len(manifest)} original figure excerpts indexed at {OUT}')


if __name__ == '__main__':
    main()
