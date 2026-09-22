#!/usr/bin/env python3
"""Faithful vector reconstruction of approved v12 layout, with real Aria assets."""
from pathlib import Path
import base64
import hashlib
import html
import json
import math
import subprocess
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parent.parent
W,H=1815,700
DESIGN_H=760
VERTICAL_SCALE=H/DESIGN_H
LABEL_SIZE=24  # 6.75pt at the 180mm manuscript width; one small step down.
CONTRIBUTION_SIZE=29  # 8.15pt, identical for (a), (b), and (c).
INK='#12164c'; GREY='#818b93'; BLUE='#0876ee'; RED='#ec492d'; PURPLE='#9c32df'; TEAL='#03a99f'
S=[]; BOXES=[]
def add(s): S.append(s)
def rect(x,y,w,h,fill='white',stroke='none',sw=1.5,r=0,extra=''):
    add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" {extra}/>')
def text(x,y,t,size=23,color=INK,bold=False,anchor='start',extra='',compact=False):
    if not compact:
        size=LABEL_SIZE if size<=25 else size
    # Tighten baseline spacing without vertically shrinking the glyphs.
    extra+=f' transform="translate(0 {y}) scale(1 {1/VERTICAL_SCALE}) translate(0 {-y})"'
    add(f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{700 if bold else 400}" text-anchor="{anchor}" fill="{color}" {extra}>{html.escape(t)}</text>')
def line(points,c=GREY,sw=2.3,arrow=False,dash=False,start=False):
    # Explicit vector heads avoid PDF-export marker scaling and tip protrusion.
    shaft=list(points);heads=[]
    for tip_i,near_i,enabled in [(-1,-2,arrow),(0,1,start)]:
        if not enabled:continue
        x,y=points[tip_i];px,py=points[near_i];length=math.hypot(x-px,y-py)
        ux,uy=(x-px)/length,(y-py)/length
        bx,by=x-9*ux,y-9*uy
        heads.append([(x,y),(bx-4.5*uy,by+4.5*ux),(bx+4.5*uy,by-4.5*ux)])
        trim=min(7,length);shaft[tip_i]=(x-trim*ux,y-trim*uy)
    cap='butt' if arrow or start else 'round'
    add(f'<polyline points="{" ".join(f"{x},{y}" for x,y in shaft)}" fill="none" stroke="{c}" stroke-width="{sw}" stroke-linejoin="round" stroke-linecap="{cap}"{" stroke-dasharray=\"7 5\"" if dash else ""}/>')
    for head in heads:
        add(f'<polygon points="{" ".join(f"{x},{y}" for x,y in head)}" fill="{c}"/>')
def path(d,c=GREY,sw=2.3,fill='none',extra=''):
    add(f'<path d="{d}" fill="{fill}" stroke="{c}" stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round" {extra}/>')
def badge(x,y,t,w=43):
    c=TEAL if t.startswith('I') else '#656e75'
    rect(x-w/2,y-21,w,29,c,'none',r=7)
    text(x,y+1,t,23,'white',True,'middle',compact=True)
def img(key,x,y,w,h,border=True,r=2,fit='slice'):
    rec=PROV['assets'][key]; p=ROOT/rec['path'];data=p.read_bytes()
    assert hashlib.sha256(data).hexdigest()==rec['sha256']
    clip=f'clip{len(BOXES)}'; BOXES.append((key,x+(1-VERTICAL_SCALE)*w/2,y*VERTICAL_SCALE,w*VERTICAL_SCALE,h*VERTICAL_SCALE))
    # Match horizontal image scaling to the canvas vertical scaling, preserving aspect ratio.
    cx=x+w/2
    add(f'<g transform="translate({cx} 0) scale({VERTICAL_SCALE} 1) translate({-cx} 0)">')
    add(f'<clipPath id="{clip}"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}"/></clipPath>')
    add(f'<image x="{x}" y="{y}" width="{w}" height="{h}" preserveAspectRatio="xMidYMid {fit}" clip-path="url(#{clip})" href="data:image/png;base64,{base64.b64encode(data).decode()}"/>')
    if border: rect(x,y,w,h,'none','#8d99a3',1.3,r)
    add('</g>')
def camera(x,y,scale=1,c=INK):
    add(f'<g transform="translate({x} {y}) scale({scale})">')
    path('M 0 5 L 13 0 L 22 6 L 22 29 L 10 33 L 0 26 Z','#4b555d',1.7,'#d0d6da')
    path('M 10 10 L 47 -17 L 59 16 L 22 25 Z','#657078',1.5,'#ffffff',extra='fill-opacity=".45"')
    path('M 13 14 L 47 -17 L 47 21 Z','#7a838b',1.3)
    path('M 13 14 L 59 16 M 10 10 L 10 33 M 0 5 L 10 10 L 22 6','#56616a',1.3)
    add('</g>')
def label_chip(x,y,w,t,c=INK,size=22,bg='white'):
    size=LABEL_SIZE if size<=25 else size
    rect(x,y-size-3,w,size+11,bg,'none',r=5);text(x+w/2,y,t,size,c,False,'middle')
def brace(x1,x2,y,c=INK):
    mid=(x1+x2)/2
    path(f'M {x1} {y} q 0 13 14 13 H {mid-14} q 14 0 14 12 q 0 -12 14 -12 H {x2-14} q 14 0 14 -13',c,1.9)


def build():
    # Arrow anchors track the actual `meet` image footprint, not its larger slot.
    png=(ROOT/PROV['assets']['map_cutaway']['path']).read_bytes()
    pw,ph=int.from_bytes(png[16:20],'big'),int.from_bytes(png[20:24],'big')
    scale=min(488/pw,125/ph);mw=pw*scale*VERTICAL_SCALE
    map_left=1218+(488-mw)/2;map_right=map_left+mw;map_mid=106+125/2
    add(f'<svg xmlns="http://www.w3.org/2000/svg" width="180mm" height="{180*H/W:.4f}mm" viewBox="0 0 {W} {H}">')
    add('<title>Online Gaussian mapping overview - Aria 1253</title><desc>Vector reconstruction of approved v12. Actual input, frontend priors and saved-map renders; view growth, selection counts and ray-space constraint are schematic. The illustrative run does not enable the ray loss.</desc>')
    add('<defs>')
    for name,c1,c2 in [('obs','#f0fbff','#e9f6fb'),('views','#fffaf4','#fcf3eb'),('map','#f5f5ff','#eef1ff')]:
        add(f'<linearGradient id="{name}" x1="0" y1="0" x2="1" y2="1"><stop stop-color="{c1}"/><stop offset="1" stop-color="{c2}"/></linearGradient>')
    for c in [INK,GREY,BLUE,RED,PURPLE,TEAL]:
        add(f'<marker id="a{c[1:]}" viewBox="0 0 10 10" refX="10" refY="5" markerUnits="userSpaceOnUse" markerWidth="9" markerHeight="9" orient="auto-start-reverse"><path d="M0 0L10 5L0 10Z" fill="{c}"/></marker>')
    for name,c in [('count','#92999f'),('prob','#429eff'),('red',RED),('blue','#51bbec'),('purple',PURPLE),('green','#65b769')]:
        if name in ('count','prob'):
            add(f'<linearGradient id="{name}" x1="0" y1="0" x2="0" y2="1"><stop stop-color="{c}" stop-opacity=".55"/><stop offset="1" stop-color="{c}"/></linearGradient>')
        else:
            add(f'<radialGradient id="{name}"><stop stop-color="{c}" stop-opacity=".6"/><stop offset=".6" stop-color="{c}" stop-opacity=".22"/><stop offset="1" stop-color="{c}" stop-opacity=".03"/></radialGradient>')
    add('</defs>')
    add(f'<g font-family="Times New Roman" transform="scale(1 {VERTICAL_SCALE})">')
    rect(0,0,W,DESIGN_H)
    for x,w,name,title in [(10,461,'obs','Online observations'),(487,670,'views','Training-view management'),(1173,632,'map','Gaussian map optimization')]:
        rect(x,8,w,742,f'url(#{name})',r=18)
        text(x+15,51,title,31,INK,True)

    # Initialization and arrived-image admission have distinct endpoints.
    # Route initialization in the header corridor; keep its label beside the map.
    # The small gap at y186 separates arrival admission from initialization.
    line([(330,369),(474,369),(474,192)],GREY,2.1)
    line([(474,180),(474,77),(1196,77),(1196,map_mid),(map_left-4,map_mid)],GREY,2.1,True)
    text(1265,120,'Gaussian',24,INK,False,'middle')
    text(1265,150,'initialization',24,INK,False,'middle')
    line([(460,186),(616,186)],GREY,2.1,True)

    # Left: observations first; a SINGLE actual pose output replaces both fake curves.
    text(30,110,'RGB stream',25)
    rect(22,126,438,107,'#8b969e','none',r=2)
    for x in range(29,451,15):
        rect(x,131,7,6,'#f8fbff','none',r=1);rect(x,221,7,6,'#f8fbff','none',r=1)
    for i,a in enumerate(ALIASES):
        x=29+i*85.3;img(a,x,143,81,72);badge(x+40,257,a)
    # The grouping brace itself points to the frontend; no extra arrowhead.
    badge(108,292,'K',28);text(129,293,'keyframe',21)
    badge(283,292,'I',28);text(304,293,'intermediate',21)
    brace(31,453,307)
    rect(150,342,180,64,'#e4e8ef','#8e98a3',1.8,12)
    text(240,367,'Online',25,INK,True,'middle');text(240,399,'frontend',25,INK,True,'middle')
    line([(240,408),(240,421)],GREY,2.2,True)
    text(240,447,'Estimated poses',25,INK,True,'middle')
    img('trajectory',33,457,405,110,False,2,fit='meet')
    add('<circle cx="178" cy="582" r="4" fill="#f04b36"/>')
    text(189,588,'Start',18)
    add('<circle cx="281" cy="582" r="4" fill="#02a69b"/>')
    text(292,588,'End',18)
    line([(150,386),(26,386),(26,601),(358,601),(358,610)],GREY,2.1,True)
    line([(148,601),(148,610)],GREY,2.1,True)
    label_chip(61,633,174,'Keyframe depth',INK,22,'#edf8fc')
    label_chip(271,633,174,'Keyframe normal',INK,22,'#edf8fc')
    # Uniformly reduce image boxes; preserve each original display aspect ratio.
    prior_w=174*100/112
    img('prior_depth',148-prior_w/2,644,prior_w,100)
    img('prior_normal',358-prior_w/2,644,prior_w,100)
    # The frontend-prior corridor branches into Base and the Carve depth input.
    # The RGB crossing stays separate from the prior input corridor.
    line([(148,745),(148,756),(1166,756),(1166,522)],GREY,2)
    line([(1166,510),(1166,486),(1246,486)],GREY,2,True)
    line([(358,745),(358,756)],GREY,2)

    # Middle (a): three rows retain identities and increase 3 -> 4 -> 5.
    text(502,123,'(a) View Set Growth',CONTRIBUTION_SIZE,RED,True)
    text(549,155,'Retain old views; admit arrived views',25,RED)
    # Local update intervals replace the long perimeter feedback loop.
    for y in [232,324]:
        line([(496,y),(496,y+45)],RED,1.9,True)
        text(508,y+27,'+κ updates',25,RED)
    for row,n in enumerate([3,4,5]):
        y=174+92*row
        text(604,y+42,['S','S + κ','S + 2κ'][row],23,INK,True,'end',extra='font-style="italic"')
        for i in range(n):
            x=616+i*88
            thumb_w=80*55/65;thumb_x=x+(80-thumb_w)/2
            img(ALIASES[i],thumb_x,y,thumb_w,55)
            if row and i==n-1: rect(thumb_x-2,y-2,thumb_w+4,59,'none',RED,2.1,2)
            badge(x+40,y+79,ALIASES[i])
    brace(616,1048,455)

    # Middle (b): compact paired bars, and the sampled view stays IN the panel.
    text(502,499,'(b) View Sampling',CONTRIBUTION_SIZE,BLUE,True)
    xs=[645,709,773,837,901]
    text(607,554,'Selection',25,INK,False,'end');text(607,586,'counts',25,INK,False,'end')
    counts=[12,9,6,3,0];prob=[10,14,18,25,33]
    for x,n in zip(xs,counts):
        bh=n*4
        rect(x-17,594-bh,34,bh,'url(#count)')
        text(x,585-bh,str(n),25,INK,False,'middle')
        line([(x,598),(x,607)],GREY,1.6,True)
    line([(613,594),(931,594)],GREY,1.3)
    text(607,636,'Sampling',25,INK,False,'end');text(607,668,'probability',25,INK,False,'end')
    for x,p,a in zip(xs,prob,ALIASES):
        bh=p*1.1
        rect(x-17,678-bh,34,bh,'url(#prob)')
        text(x,670-bh,f'{p}%',25,BLUE,False,'middle')
        badge(x,708,a)
    line([(613,678),(932,678)],BLUE,1.3)
    text(773,742,'Low count → high probability',25,BLUE,False,'middle')
    # The selected image updates its corresponding count (K3), not empty space.
    rect(969,575,162,126,'#f5fbff',BLUE,1.5,9)
    img('K3',997,584,106,106*89/122);badge(1050,689,'K3')
    line([(931,644),(968,644)],BLUE,2,True)
    line([(1131,629),(1141,629),(1141,517),(773,517),(773,533)],BLUE,1.7,True)
    label_chip(891,520,206,'Selection history',BLUE,25,'#fff6ed')
    # The selected view supplies its camera pose to Render and its RGB to Base.
    line([(1131,656),(1152,656),(1152,262),(1386,262)],BLUE,1.9,True)
    label_chip(1194,271,160,'Camera pose',BLUE,25,'#f2f3ff')
    line([(1152,516),(1246,516)],BLUE,1.9,True)
    text(1188,507,'RGB',25,BLUE,False,'start')

    # Right: real shared map, large enough to carry comparable visual weight to v12.
    text(1450,94,'Shared Gaussian map',26,INK,True,'middle')
    img('map_cutaway',1218,106,488,125,False,3,fit='meet')
    # Render is the heading of a single modality group. Its brace points into
    # base supervision without duplicating that relation with three arrows.
    rect(1390,246,123,32,'#e0e4ee','none',r=7)
    text(1451,270,'Render',25,INK,False,'middle')
    line([(1451,233),(1451,243)],GREY,2,True)
    for key,x,label in [('render_rgb',1203,'Rendered RGB'),('render_depth',1370,'Rendered depth'),('render_normal',1537,'Rendered normal')]:
        img(key,x,292,146,86)
        # A small optical adjustment keeps the three full labels separate.
        text(x+73,410,label,23,INK,False,'middle',compact=True)
    brace(1203,1683,425,GREY)
    rect(1250,464,401,70,'#e1e5ed','#a0a9b1',1.2,12)
    text(1450,492,'Base supervision',26,INK,True,'middle')
    text(1450,522,'RGB (K + I) · Depth / normal (K)',25,INK,False,'middle')
    text(1188,475,'Priors',25,INK,False,'start')
    # Both terms feed the objective, never a serial loss chain.
    add(f'<circle cx="1750" cy="435" r="49" fill="white" stroke="{GREY}" stroke-width="2.6"/>')
    text(1750,414,'Map',25,INK,True,'middle');text(1750,445,'objective',25,INK,True,'middle')
    text(1750,474,'+',25,GREY,True,'middle')
    line([(1651,503),(1692,503),(1721,475)],GREY,2.1,True)
    line([(1750,386),(1750,250),(map_right-18,250),(map_right-18,235)],GREY,2.1,True)
    text(1720,237,'Update',24,INK,False,'middle')

    # Ray-space schematic: only opacity changes; no displacement or hard cutoff.
    # Keep panel width; lift and tighten its height so the bottom border is clearly inset.
    # Paint the Depth backing below the panel border, aligned with the shifted input labels.
    rect(1182,681,72,36,'#fffaff','none',r=5)
    rect(1182,552,512,184,'#fffaff',PURPLE,1.5,9,extra='stroke-dasharray="6 4"')
    text(1191,584,'(c) Free-Space Carve Loss',CONTRIBUTION_SIZE,PURPLE,True)
    # Balance the simplified diagram vertically after removing its input footer.
    add('<g transform="translate(0 -4)">')
    text(1410,623,'Observed free space',25,INK,False,'middle')
    line([(1260,637),(1260,633),(1565,633),(1565,637)],BLUE,1.5)
    camera(1198,635,.79)
    # Keep the observed surface; depth uncertainty is explained in the method text.
    path('M 1620 636 L 1640 647 L 1640 687 L 1620 676 Z','#c4b9a3',1,'#eadfbd')
    for x,rx,ry,g,ang,opacity in [(1310,27,13,'red',-19,.6),(1410,30,16,'red',-14,.6),(1510,25,12,'red',10,.6),(1620,33,22,'purple',-19,1)]:
        add(f'<g opacity="{opacity}">')
        add(f'<ellipse cx="{x}" cy="653" rx="{rx}" ry="{ry}" transform="rotate({ang} {x} 653)" fill="url(#{g})"/>')
        add(f'<ellipse cx="{x}" cy="653" rx="{rx*.55}" ry="{ry*.55}" transform="rotate({ang} {x} 653)" fill="url(#{g})"/>')
        add('</g>')
        if g=='red':
            text(x,684,'α ↓',25,RED,False,'middle')
    line([(1220,653),(1620,653)],INK,1.5)
    add(f'<circle cx="1620" cy="653" r="3.3" fill="{INK}"/>')
    text(1640,623,'Surface',25,INK,False,'middle')
    text(1410,724,'Penalize free-space opacity',25,RED,False,'middle')
    add('</g>')
    # Keep the common left edge x=1188 for all three input labels, with the arrow entering the wide box.
    line([(1166,720),(1246,720)],GREY,2,True)
    text(1188,709,'Depth',25,INK,False,'start')
    line([(1694,663),(1750,663),(1750,488)],PURPLE,2.1,True)

    add('</g></svg>')
    svg='\n'.join(S);ET.fromstring(svg)
    return svg


if __name__=='__main__':
    PROV=json.loads((ROOT/'assets/aria1253/provenance.json').read_text())
    ALIASES=['K1','I2','K3','I4','K5']
    source=build()
    out=ROOT/'current/overview.svg';out.write_text(source)
    for ext,extra in [('pdf',[]),('png',['--export-width=2723'])]:
        subprocess.run(['inkscape',str(out),'--export-area-page',f'--export-filename={out.with_suffix("."+ext)}',*extra],check=True)
    subprocess.run(['pdftoppm','-scale-to','2723','-png','-singlefile',str(out.with_suffix('.pdf')),str(ROOT/'qa/overview_pdf_check')],check=True)
    # Native high-resolution PDF crops for connector inspection; no asset edits.
    zooms=ROOT/'qa/arrows';zooms.mkdir(exist_ok=True)
    regions={'frontend':(10,230,455,380),'initialization':(430,75,825,355),
             'map_update':(1170,75,630,310),'sampling':(490,450,665,300),
             'loss_routes':(1140,305,660,450)}
    previous=ROOT/'archive/before_type_spacing_2026-09-21/current/overview.pdf'
    for version,pdf in [('before',previous),('after',out.with_suffix('.pdf'))]:
        if not pdf.exists():continue
        for name,(x,y,w,h) in regions.items():
            target=zooms/f'{version}_{name}'
            if version=='after':y,h=math.floor(y*VERTICAL_SCALE),math.ceil(h*VERTICAL_SCALE)
            subprocess.run(['pdftoppm','-scale-to',str(W*3),'-x',str(x*3),'-y',str(y*3),
                '-W',str(w*3),'-H',str(h*3),'-png','-singlefile',str(pdf),str(target)],check=True)
    # Matching-size reference comparison, generated by this same maintained builder.
    comparison=['<svg xmlns="http://www.w3.org/2000/svg" width="2400" height="640" viewBox="0 0 2400 640">',
                '<rect width="2400" height="640" fill="#fff"/>']
    for x,p,title in [(15,ROOT.parent/'plan/overall_pipeline_v12.png','Approved v12 · generated design reference'),
                      (1215,ROOT/'qa/overview_pdf_check.png','Current vector · actual Aria 1253 assets')]:
        comparison.append(f'<text x="{x}" y="36" font-family="Arial" font-size="26" font-weight="bold" fill="{INK}">{html.escape(title)}</text>')
        data=base64.b64encode(p.read_bytes()).decode()
        comparison.append(f'<image x="{x}" y="59" width="1170" height="560" preserveAspectRatio="xMidYMid meet" href="data:image/png;base64,{data}"/>')
    comparison.append('</svg>')
    compare=ROOT/'qa/v12_vs_vector_comparison.svg';compare.write_text('\n'.join(comparison))
    subprocess.run(['inkscape',str(compare),f'--export-filename={compare.with_suffix(".png")}'],check=True)
    # Same physical width, native aspect ratios: make height reduction explicit.
    comparison=['<svg xmlns="http://www.w3.org/2000/svg" width="2400" height="665" viewBox="0 0 2400 665">',
                '<rect width="2400" height="665" fill="white"/>']
    for x,p,title in [(15,ROOT/'archive/before_height_compaction/current/overview.png','Before: 180 x 86.28 mm'),
                      (1215,ROOT/'qa/overview_pdf_check.png','Current: 180 x 69.42 mm')]:
        data=p.read_bytes();iw,ih=int.from_bytes(data[16:20],'big'),int.from_bytes(data[20:24],'big')
        comparison.append(f'<text x="{x}" y="33" font-family="Times New Roman" font-size="27" fill="{INK}">{title}</text>')
        comparison.append(f'<image x="{x}" y="60" width="1170" height="{1170*ih/iw}" href="data:image/png;base64,{base64.b64encode(data).decode()}"/>')
    comparison.append('</svg>')
    compare=ROOT/'qa/height_before_after.svg';compare.write_text('\n'.join(comparison))
    subprocess.run(['inkscape',str(compare),f'--export-filename={compare.with_suffix(".png")}'],check=True)
    # Keep a same-size comparison against the exact pre-edit PDF rendering.
    comparison=['<svg xmlns="http://www.w3.org/2000/svg" width="2400" height="580" viewBox="0 0 2400 580">',
                '<rect width="2400" height="580" fill="white"/>']
    for x,p,title in [(15,ROOT/'archive/before_detail_cleanup_2026-09-21/qa/overview_pdf_check.png','Before: overlapping labels and redundant connectors'),
                      (1215,ROOT/'qa/overview_pdf_check.png','After: grouped flow and aligned labels')]:
        comparison.append(f'<text x="{x}" y="35" font-family="Times New Roman" font-size="27" fill="{INK}">{title}</text>')
        comparison.append(f'<image x="{x}" y="60" width="1170" height="490" preserveAspectRatio="xMidYMid meet" href="data:image/png;base64,{base64.b64encode(p.read_bytes()).decode()}"/>')
    comparison.append('</svg>')
    compare=ROOT/'qa/detail_cleanup_before_after.svg';compare.write_text('\n'.join(comparison))
    subprocess.run(['inkscape',str(compare),f'--export-filename={compare.with_suffix(".png")}'],check=True)
    # Refresh the exact asset preferred by the current Overleaf manuscript.
    import shutil
    manuscript=ROOT.parents[3]/'HumanTeck_Song_s_intern/figure/overview.pdf'
    assert manuscript.parent.is_dir(),manuscript
    shutil.copy2(out.with_suffix('.pdf'),manuscript)
    counts=[12,9,6,3,0];mass=[math.exp(-.1*n) for n in counts]
    probabilities=[v/sum(mass) for v in mass]
    assert [round(100*p) for p in probabilities]==[10,14,18,25,33]
    (ROOT/'qa/v02_validation.json').write_text(json.dumps({'assets':BOXES,'font':'Times New Roman','reference':'../plan/overall_pipeline_v12.png','physical_width_mm':180,
        'physical_height_mm':180*H/W,'previous_height_mm':180*870/W,'height_reduction_percent':100*(1-H/870),
        'layout_revision':'view_set_growth_title_2026-09-22','immediate_previous_height_mm':180*DESIGN_H/W,'vertical_scale':VERTICAL_SCALE,'body_glyphs_preserved':True,'image_aspect_ratios_preserved':True,
        'contribution_font_pt':CONTRIBUTION_SIZE*180/W*72/25.4,
        'body_font_pt':LABEL_SIZE*180/W*72/25.4,
        'modality_label_font_pt':23*180/W*72/25.4,
        'compact_badge_font_pt':23*180/W*72/25.4,
        'shared_map_shift_up_mm':38*180/W,
        'group_flow':'braces point to frontend, sampling and base supervision without added arrowheads',
        'image_assets_unchanged':True,'status':'overview_with_real_assets_not_full_method_result',
        'schematic_counts':counts,'schematic_probabilities':probabilities,
        'schematic_effective_beta':.1,'schematic_tau':1/(.1*(sum(counts)+1)),
        'counts_are_measured':False,
        'thumbnail_display_crop':'center crop to each SVG image slot; rendered RGB/depth/normal share the same rectangle and crop; prior depth/normal share the same rectangle and crop',
        'image_rotation':'90 degrees clockwise in prepared assets; no RGB enhancement'},indent=2)+'\n')
    print(out)
