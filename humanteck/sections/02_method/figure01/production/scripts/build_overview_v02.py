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
W,H=1815,870
INK='#12164c'; GREY='#818b93'; BLUE='#0876ee'; RED='#ec492d'; PURPLE='#9c32df'; TEAL='#03a99f'
S=[]; BOXES=[]
def add(s): S.append(s)
def rect(x,y,w,h,fill='white',stroke='none',sw=1.5,r=0,extra=''):
    add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" {extra}/>')
def text(x,y,t,size=23,color=INK,bold=False,anchor='start',extra=''):
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
    text(x,y+1,t,23,'white',True,'middle')
def img(key,x,y,w,h,border=True,r=2,fit='slice'):
    rec=PROV['assets'][key]; p=ROOT/rec['path'];data=p.read_bytes()
    assert hashlib.sha256(data).hexdigest()==rec['sha256']
    clip=f'clip{len(BOXES)}'; BOXES.append((key,x,y,w,h))
    add(f'<clipPath id="{clip}"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}"/></clipPath>')
    add(f'<image x="{x}" y="{y}" width="{w}" height="{h}" preserveAspectRatio="xMidYMid {fit}" clip-path="url(#{clip})" href="data:image/png;base64,{base64.b64encode(data).decode()}"/>')
    if border: rect(x,y,w,h,'none','#8d99a3',1.3,r)
def camera(x,y,scale=1,c=INK):
    add(f'<g transform="translate({x} {y}) scale({scale})">')
    path('M 0 5 L 13 0 L 22 6 L 22 29 L 10 33 L 0 26 Z','#4b555d',1.7,'#d0d6da')
    path('M 10 10 L 47 -17 L 59 16 L 22 25 Z','#657078',1.5,'#ffffff',extra='fill-opacity=".45"')
    path('M 13 14 L 47 -17 L 47 21 Z','#7a838b',1.3)
    path('M 13 14 L 59 16 M 10 10 L 10 33 M 0 5 L 10 10 L 22 6','#56616a',1.3)
    add('</g>')
def label_chip(x,y,w,t,c=INK,size=22,bg='white'):
    rect(x,y-22,w,30,bg,'none',r=5);text(x+w/2,y,t,size,c,False,'middle')
def brace(x1,x2,y,c=INK):
    mid=(x1+x2)/2
    path(f'M {x1} {y} q 0 13 14 13 H {mid-14} q 14 0 14 12 q 0 -12 14 -12 H {x2-14} q 14 0 14 -13',c,1.9)


def build():
    # Arrow anchors track the actual `meet` image footprint, not its larger slot.
    png=(ROOT/PROV['assets']['map_cutaway']['path']).read_bytes()
    pw,ph=int.from_bytes(png[16:20],'big'),int.from_bytes(png[20:24],'big')
    scale=min(488/pw,199/ph);mw=pw*scale
    map_left=1218+(488-mw)/2;map_right=map_left+mw;map_mid=158+199/2
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
    add('<g font-family="Times New Roman">')
    rect(0,0,W,H)
    for x,w,name,title in [(10,461,'obs','Online observations'),(487,670,'views','Training-view management'),(1173,632,'map','Gaussian map optimization')]:
        rect(x,8,w,819,f'url(#{name})',r=18)
        text(x+15,54,title,36,INK,True)

    # Dedicated edge corridors. Feedback is not an observation edge.
    line([(1750,290),(1790,290),(1790,79),(550,79),(550,125)],RED,2.1,True,True)
    label_chip(1395,104,190,'Completed updates',RED,21,'#f2f3ff')
    # Enter the map from its left margin, never through its title.
    # Gap at y186 denotes a crossing with the independent observation edge.
    line([(330,393),(474,393),(474,192)],GREY,2.1)
    line([(474,180),(474,121),(543,121)],GREY,2.1)
    line([(557,121),(1196,121),(1196,map_mid),(map_left-4,map_mid)],GREY,2.1,True)
    label_chip(813,124,300,'Geometry-based initialization',INK,22,'#fff8f1')
    # Observation line enters growth from the already arrived filmstrip.
    line([(460,186),(606,186)],GREY,2.1,True)

    # Left: observations first; a SINGLE actual pose output replaces both fake curves.
    text(30,110,'RGB stream',25)
    rect(22,126,438,107,'#8b969e','none',r=2)
    for x in range(29,451,15):
        rect(x,131,7,6,'#f8fbff','none',r=1);rect(x,221,7,6,'#f8fbff','none',r=1)
    for i,a in enumerate(ALIASES):
        x=29+i*85.3;img(a,x,143,81,72);badge(x+40,257,a)
    brace(31,453,271)
    text(243,312,'Arrived views',25,INK,False,'middle')
    badge(108,340,'K',28);text(129,341,'keyframe',21)
    badge(283,340,'I',28);text(304,341,'intermediate',21)
    line([(74,285),(74,391),(147,391)],GREY,2.2,True)
    rect(150,366,180,62,'#e4e8ef','#8e98a3',1.8,12)
    text(240,392,'Online',25,INK,True,'middle');text(240,420,'frontend',25,INK,True,'middle')
    line([(240,430),(240,445)],GREY,2.2,True)
    text(240,472,'Estimated poses',25,INK,True,'middle')
    img('trajectory',33,481,405,145,False,2,fit='meet')
    add('<circle cx="178" cy="630" r="4" fill="#f04b36"/>')
    text(189,636,'Start',18)
    add('<circle cx="281" cy="630" r="4" fill="#02a69b"/>')
    text(292,636,'End',18)
    line([(150,410),(26,410),(26,642),(358,642),(358,651)],GREY,2.1,True)
    line([(148,642),(148,651)],GREY,2.1,True)
    label_chip(61,674,174,'Keyframe depth',INK,22,'#edf8fc')
    label_chip(271,674,174,'Keyframe normal',INK,22,'#edf8fc')
    img('prior_depth',61,692,174,112);img('prior_normal',271,692,174,112)
    # Route priors below all view management content into base + ray branches.
    # Separate input corridors, with a non-junction gap at the RGB crossing.
    line([(148,805),(148,819),(1166,819),(1166,614)],GREY,2)
    line([(1166,602),(1166,556),(1266,556),(1266,564)],GREY,2,True)
    line([(358,805),(358,819)],GREY,2)

    # Middle (a): three rows retain identities and increase 3 -> 4 -> 5.
    text(502,151,'(a) View Growth',34,RED,True)
    text(549,179,'Retain old views; admit arrived views',23,RED)
    line([(536,238),(536,443)],RED,1.9,True)
    label_chip(493,281,87,'Updates',RED,20,'#fff8f1')
    for row,n in enumerate([3,4,5]):
        y=196+100*row
        text(604,y+47,['S','S + κ','S + 2κ'][row],23,INK,True,'end',extra='font-style="italic"')
        for i in range(n):
            x=616+i*88
            img(ALIASES[i],x,y,80,65)
            if row and i==n-1: rect(x-2,y-2,84,69,'none',RED,2.1,2)
            badge(x+40,y+89,ALIASES[i])
    brace(616,1048,495)
    line([(832,520),(832,534)],BLUE,2,True)

    # Middle (b): compact paired bars, and the sampled view stays IN the panel.
    text(502,539,'(b) View Sampling',32,BLUE,True)
    xs=[645,709,773,837,901]
    text(525,600,'Selection',22);text(525,626,'counts',22)
    counts=[12,9,6,3,0];prob=[10,14,18,25,33]
    for x,n in zip(xs,counts):
        bh=n*4
        rect(x-17,632-bh,34,bh,'url(#count)')
        text(x,625-bh,str(n),23,INK,False,'middle')
        line([(x,638),(x,653)],GREY,1.6,True)
    line([(613,632),(931,632)],GREY,1.3)
    text(607,690,'Sampling',20,INK,False,'end');text(607,716,'probabilities',20,INK,False,'end')
    for x,p,a in zip(xs,prob,ALIASES):
        bh=p*1.38
        rect(x-17,724-bh,34,bh,'url(#prob)')
        text(x,716-bh,f'{p}%',22,BLUE,False,'middle')
        badge(x,754,a)
    line([(613,724),(932,724)],BLUE,1.3)
    text(616,788,'Earlier admitted',19)
    line([(758,782),(807,782)],GREY,1.5,True)
    text(944,788,'Later admitted',19,BLUE,False,'end')
    text(814,815,'Fewer selections → higher probability',24,BLUE,True,'middle')
    # Right-aligned output and a thin, unambiguous history loop.
    text(1050,579,'Sample without',19,BLUE,False,'middle')
    text(1050,602,'replacement',19,BLUE,False,'middle')
    rect(969,609,162,139,'#f5fbff',BLUE,1.5,9)
    img('K3',989,620,122,89);badge(1050,736,'K3')
    text(1050,776,'One view / update',20,INK,False,'middle')
    line([(931,704),(952,704),(952,678),(968,678)],BLUE,2,True)
    line([(1131,669),(1141,669),(1141,549),(880,549)],BLUE,1.7,True)
    label_chip(906,552,164,'Selection history',BLUE,19,'#fff6ed')
    # Selected camera goes to rendering; selected RGB goes to the objective.
    line([(1131,696),(1152,696),(1152,395),(1386,395)],BLUE,1.9,True)
    label_chip(1178,404,177,'Selected camera',BLUE,19,'#f2f3ff')
    line([(1152,608),(1246,608)],BLUE,1.9,True)

    # Right: real shared map, large enough to carry comparable visual weight to v12.
    text(1450,147,'Shared Gaussian map',25,INK,True,'middle')
    img('map_cutaway',1218,158,488,199,False,3,fit='meet')
    text(1453,368,'C07 region · cutaway visualization',19,INK,False,'middle')
    rect(1390,382,123,32,'#e0e4ee','none',r=7)
    text(1451,406,'Render',24,INK,False,'middle')
    line([(1451,374),(1451,382)],GREY,2,True)
    line([(1451,414),(1451,424),(1280,424),(1280,435)],GREY,1.9,True)
    line([(1443,424),(1443,435)],GREY,1.9,True)
    for key,x,label in [('render_rgb',1207,'Rendered RGB'),('render_depth',1370,'Rendered depth'),('render_normal',1542,'Depth-derived normal')]:
        img(key,x,439,146,86)
        if key=='render_normal':
            text(x+73,543,'Depth-derived',18,INK,True,'middle')
            text(x+73,564,'normal',18,INK,True,'middle')
        else:
            text(x+73,547,label,19,INK,True,'middle')
    line([(1516,482),(1538,482)],GREY,1.7,True)
    rect(1250,566,401,54,'#e1e5ed','#a0a9b1',1.2,12)
    text(1450,589,'Base supervision',25,INK,True,'middle')
    text(1450,612,'RGB (K + I) · Depth / normal (K)',21,INK,False,'middle')
    for x in [1280,1443]: line([(x,552),(x,564)],GREY,1.6,True)
    line([(1688,482),(1699,482),(1699,581),(1655,581)],GREY,1.6,True)
    label_chip(1180,595,63,'Priors',INK,18,'#f3f4ff')
    # Both terms feed the objective, never a serial loss chain.
    add(f'<circle cx="1750" cy="534" r="43" fill="white" stroke="{GREY}" stroke-width="2.6"/>')
    text(1750,522,'Map',23,INK,True,'middle');text(1750,548,'objective',21,INK,True,'middle')
    text(1750,570,'+',23,GREY,True,'middle')
    line([(1651,606),(1693,606),(1720,568)],GREY,2.1,True)
    line([(1750,491),(1750,map_mid),(map_right+4,map_mid)],GREY,2.1,True)
    add(f'<circle cx="1750" cy="290" r="2.5" fill="{RED}"/>')
    label_chip(1693,343,100,'Update',INK,23,'#f0f2ff')

    # Ray loss: preserve the illustrative icon density, not the fake room rendering.
    rect(1182,637,512,170,'#fffaff',PURPLE,1.5,9,extra='stroke-dasharray="6 4"')
    text(1191,665,'(c) Ray-space geometry supervision',26,PURPLE,True)
    text(1397,691,'Observed free space',21,INK,False,'middle')
    line([(1269,703),(1586,703)],'#0876ee',1.5,True,start=True)
    camera(1198,712,.79)
    # Uncertainty slab, not a Gaussian position displacement.
    rect(1598,696,23,77,'#ece2f6','none')
    path('M 1621 696 L 1640 707 L 1640 782 L 1621 773 Z','#c4b9a3',1,'#eadfbd')
    for x,rx,ry,g,ang in [(1363,30,15,'blue',-19),(1419,35,19,'red',-14),(1511,24,16,'green',10),(1598,41,27,'purple',-19)]:
        add(f'<ellipse cx="{x}" cy="730" rx="{rx}" ry="{ry}" transform="rotate({ang} {x} 730)" fill="url(#{g})"/>')
        add(f'<ellipse cx="{x}" cy="730" rx="{rx*.55}" ry="{ry*.55}" transform="rotate({ang} {x} 730)" fill="url(#{g})"/>')
    line([(1220,730),(1610,730)],INK,1.5)
    line([(1610,696),(1610,781)],'#0876ee',1.5,dash=True)
    add(f'<circle cx="1610" cy="730" r="3.3" fill="{INK}"/>')
    text(1645,690,'Surface',18,INK,False,'middle')
    text(1418,771,'Suppress premature opacity ↓ α',21,RED,False,'middle')
    line([(1419,741),(1419,752)],RED,1.8,True)
    text(1337,800,'Verified keyframe depth',21,INK,False,'middle')
    line([(1166,778),(1180,778)],GREY,1.8,True)
    line([(1469,793),(1610,793),(1610,785)],GREY,1.8,True)
    text(1627,799,'D',22,INK,False,extra='font-style="italic"')
    line([(1694,736),(1750,736),(1750,581)],PURPLE,2.1,True)

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
    regions={'frontend':(10,350,455,468),'initialization':(430,75,825,355),
             'map_update':(1170,75,630,350),'sampling':(855,535,335,278),
             'loss_routes':(1140,405,660,415)}
    previous=ROOT/'archive/before_arrow_cleanup/current/overview.pdf'
    for version,pdf in [('before',previous),('after',out.with_suffix('.pdf'))]:
        if not pdf.exists():continue
        for name,(x,y,w,h) in regions.items():
            target=zooms/f'{version}_{name}'
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
    counts=[12,9,6,3,0];mass=[math.exp(-.1*n) for n in counts]
    probabilities=[v/sum(mass) for v in mass]
    assert [round(100*p) for p in probabilities]==[10,14,18,25,33]
    (ROOT/'qa/v02_validation.json').write_text(json.dumps({'assets':BOXES,'font':'Times New Roman','reference':'../plan/overall_pipeline_v12.png','physical_width_mm':180,'status':'overview_with_real_assets_not_full_method_result',
        'schematic_counts':counts,'schematic_probabilities':probabilities,
        'schematic_effective_beta':.1,'schematic_tau':1/(.1*(sum(counts)+1)),
        'counts_are_measured':False,
        'thumbnail_display_crop':'center crop to each SVG image slot; rendered RGB/depth/normal share the same rectangle and crop; prior depth/normal share the same rectangle and crop',
        'image_rotation':'90 degrees clockwise in prepared assets; no RGB enhancement'},indent=2)+'\n')
    print(out)
