#!/usr/bin/env python3
"""Build a 300-second silent 1080p presentation video from the final deck.

Usage: python build_video.py [--pdf /path/to/preconverted.pdf]
Outputs are versioned; existing output directories are never overwritten.
"""
from pathlib import Path
import argparse
import hashlib
import json
import shutil
import subprocess
import tempfile
from datetime import datetime
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT/'reference/Internship_20260918_final.pptx'
TIMES = [15,30,25,30,25,35,40,30,45,25]


def run(args):
    subprocess.run([str(a) for a in args], check=True)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--pdf',type=Path)
    args=parser.parse_args()
    out=ROOT/'video_versions'/datetime.now().strftime('v_%Y%m%d_%H%M%S')
    out.mkdir(parents=True,exist_ok=False)
    shutil.copy2(SOURCE,out/SOURCE.name)
    shutil.copy2(Path(__file__),out/'build_video.py')
    pdf=out/'Internship_20260918_final.pdf'
    if args.pdf:
        shutil.copy2(args.pdf,pdf)
    else:
        with tempfile.TemporaryDirectory(prefix='intern-video-lo-') as tmp:
            run(['libreoffice','-env:UserInstallation='+Path(tmp).as_uri(),'--headless','--convert-to','pdf','--outdir',out,SOURCE])
    pages=out/'frames'
    pages.mkdir()
    run(['pdftoppm','-scale-to-x','1920','-scale-to-y','1080','-png',pdf,pages/'slide'])
    images=sorted(pages.glob('slide-*.png'))
    assert len(images)==10 and sum(TIMES)==300
    clips=out/'segments'
    clips.mkdir()
    timeline=[]
    current=0
    for i,(path,seconds) in enumerate(zip(images,TIMES),1):
        assert Image.open(path).size==(1920,1080)
        print(f'Encoding slide {i}/10: {current}–{current+seconds}s',flush=True)
        target=clips/f'{i:02d}.mp4'
        run(['ffmpeg','-hide_banner','-loglevel','error','-nostdin','-loop','1','-framerate','30','-i',path,
             '-t',seconds,'-an','-c:v','libx264','-preset','veryfast','-tune','stillimage',
             '-crf','18','-pix_fmt','yuv420p','-threads','4','-r','30',target])
        timeline.append({'slide':i,'start_seconds':current,'end_seconds':current+seconds,'duration_seconds':seconds})
        current+=seconds
    concat=out/'concat.txt'
    concat.write_text(''.join(f"file 'segments/{i:02d}.mp4'\n" for i in range(1,11)))
    video=out/'박상원.mp4'
    run(['ffmpeg','-hide_banner','-loglevel','error','-nostdin','-f','concat','-safe','0','-i',concat,
         '-c','copy','-an','-movflags','+faststart',video])
    info=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(video)]))
    assert len(info['streams'])==1
    stream=info['streams'][0]
    assert stream['codec_type']=='video' and stream['codec_name']=='h264'
    assert stream['width']==1920 and stream['height']==1080
    assert abs(float(info['format']['duration'])-300)<.05
    assert int(stream['nb_frames'])==9000
    sheet=Image.new('RGB',(960,1450),'#e9e9ee')
    check=out/'verification'
    check.mkdir()
    for row in timeline:
        i=row['slide']
        frame=check/f'video-slide-{i:02d}.png'
        # Actual encoded frame just after every scheduled cut.
        run(['ffmpeg','-hide_banner','-loglevel','error','-ss',row['start_seconds']+.1,'-i',video,
             '-frames:v','1','-update','1',frame])
        im=Image.open(frame).convert('RGB')
        im.thumbnail((480,270))
        x=((i-1)%2)*480
        y=((i-1)//2)*290
        sheet.paste(im,(x,y))
        ImageDraw.Draw(sheet).text((x+8,y+273),f"Slide {i} | {row['start_seconds']}–{row['end_seconds']} sec",fill='black')
    sheet.save(out/'video_contact_sheet.jpg')
    report={'source':SOURCE.name,'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
            'duration_seconds':300,'audio_streams':0,'resolution':'1920x1080','fps':30,
            'frames':9000,'timeline':timeline,'ffprobe':info}
    (out/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
    (out/'README.md').write_text('# 최종 발표 영상\n\n박상원.mp4: 1920×1080, H.264, 30fps, 정확히 5분, 음성 트랙 없음.\n'
        '정적인 슬라이드 화면을 지정 시간 동안 표시하며 전환은 즉시 이루어집니다.\n'
        '원본 PPT의 애니메이션·동영상은 재생하지 않습니다.\n'
        '전환 시각: 0:00 / 0:15 / 0:45 / 1:10 / 1:40 / 2:05 / 2:40 / 3:20 / 3:50 / 4:35.\n'
        '최종 PPT·PDF, 프레임, 빌드 코드, 검증 기록을 함께 보존했습니다.\n')
    print('OUTPUT: '+str(video),flush=True)


if __name__=='__main__':
    main()
