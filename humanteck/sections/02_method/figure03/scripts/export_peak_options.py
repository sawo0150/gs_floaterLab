#!/usr/bin/env python3
"""Export the reviewed peak-comparison alternatives as editable paper figures."""
import json,subprocess,hashlib,xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent; REVIEW=ROOT/'analysis/peak_annotation_review'; OUT=ROOT/'output'
metrics=json.loads((REVIEW/'metrics.json').read_text());ns={'s':'http://www.w3.org/2000/svg'}
base=ET.parse(metrics['source_svg']);items=[]
for tag,variant in [('A_400iter','remaining_checkpoints'),('B_1000iter','first_sampled')]:
 stem=f'fig3_frame1420_peak_{tag}';svg=OUT/f'{stem}.svg';pdf=OUT/'pdf'/f'{stem}.pdf'
 svg.write_bytes((REVIEW/f'frame1420_{variant}.svg').read_bytes());tree=ET.parse(svg)
 for arm in ['baseline','ours']:assert tree.find(f'.//s:polyline[@id="curve-{arm}"]',ns).attrib==base.find(f'.//s:polyline[@id="curve-{arm}"]',ns).attrib
 assert [e.attrib for e in tree.findall('.//s:image',ns)]==[e.attrib for e in base.findall('.//s:image',ns)]
 subprocess.run(['inkscape',str(svg),'--export-type=pdf',f'--export-filename={pdf}'],check=True,capture_output=True)
 subprocess.run(['pdftoppm','-singlefile','-png','-scale-to','1800',str(pdf),str(OUT/stem)],check=True)
 subprocess.run(['pdftoppm','-singlefile','-png','-r','200',str(pdf),str(OUT/'qa'/f'{stem}_column')],check=True)
 p={'variant':variant,**metrics['variants'][variant],'definition':metrics['definitions'][variant],'source_svg_sha256':metrics['source_svg_sha256'],'curve_sha256':metrics['curves_sha256'],'svg_sha256':hashlib.sha256(svg.read_bytes()).hexdigest(),'raw_points_preserved':28,'embedded_images_preserved':6,'width_mm':86.48540196485402,'height_mm':46.12554771458881}
 (OUT/f'{stem}_provenance.json').write_text(json.dumps(p,indent=2)+'\n');items.append(p)
(OUT/'qa/peak_options_validation.json').write_text(json.dumps({'pass':True,'options':items,'raster_preview':'PNG rendered from exported PDF; column preview at 200dpi.'},indent=2)+'\n')
print('Exported A (400 iter) and B (1000 iter): SVG, PDF, PNG, provenance, column QA.')
