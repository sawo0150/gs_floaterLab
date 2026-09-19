#!/usr/bin/env python3
"""Immutable deck releases with source, inputs, renders, and SHA-256 manifests."""
from pathlib import Path
import argparse
from datetime import datetime, timezone
import hashlib
import json
import shutil
import os

ROOT = Path(__file__).resolve().parent
VERSIONS = ROOT / 'versions'


def snapshot(version, message, legacy=False):
    dest = VERSIONS / version
    if dest.exists():
        raise SystemExit(f'Refusing to overwrite existing release: {dest}')
    dest.mkdir(parents=True)
    if legacy:
        for ext in ('pptx', 'pdf'):
            shutil.copy2(ROOT/f'Chaehyeon_Song_Internship_20260918.{ext}', dest/f'Internship_20260918.{ext}')
    else:
        for name in ('build_ppt.py','version_deck.py','README.md','MATH_NOTES.md','CHANGELOG.md',
                     'Internship_20260918.pptx','Internship_20260918.pdf','image_slots.json'):
            if (ROOT/name).exists():
                shutil.copy2(ROOT/name,dest/name)
        for name in ('assets','reference','rendered'):
            if (ROOT/name).exists():
                shutil.copytree(ROOT/name,dest/name)
    checksums = {str(p.relative_to(dest)):hashlib.sha256(p.read_bytes()).hexdigest()
                 for p in sorted(dest.rglob('*')) if p.is_file()}
    metadata={'version':version,'created_utc':datetime.now(timezone.utc).isoformat(),
              'message':message,'source_available':not legacy,'sha256':checksums}
    (dest/'manifest.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+'\n')
    print(dest)
    return dest


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--archive-legacy',action='store_true')
    p.add_argument('--version')
    p.add_argument('--message',default='')
    args=p.parse_args()
    if args.archive_legacy:
        snapshot('v001_initial','Initial deck. Incorrect presenter emphasis. Historical binary files only; exact source was not preserved.',True)
        snapshot('v002_korean_cover','Names corrected to 박상원, 김동휘, 송채현. Source and render snapshot before equation revision.')
    elif args.version and args.message:
        if not args.version.startswith('v') or not args.version.replace('_','').isalnum():
            p.error('Use a version name such as v003_english_equations')
        d=snapshot(args.version,args.message)
        tmp=ROOT/'latest.pending'
        if tmp.exists() or tmp.is_symlink():
            raise SystemExit('Resolve existing latest.pending before publishing.')
        tmp.symlink_to(d.relative_to(ROOT),target_is_directory=True)
        os.replace(tmp,ROOT/'latest')
    else:
        p.error('Use --archive-legacy or --version NAME --message TEXT')
