#!/usr/bin/env python3
"""Render a real captured map directly and after PLY export/reload.

Uses saved training cameras and synthetic black image buffers; no RGB ground
truth or evaluation trajectory is consumed. Run only after the mapper finishes.
"""
import argparse
import json
from pathlib import Path
import sys
import numpy as np
import torch
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from exp78_evaluate_vigs_ply import load_gaussians
from export_online_snapshot import write_map
from gaussian.scene.gaussian_model import GaussianModel
from gaussian.renderer import render
from gaussian.utils.camera_utils import Camera
from gaussian.utils.graphics_utils import getProjectionMatrix2


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-dir', type=Path, required=True)
    parser.add_argument('--archive-manifest', type=Path, required=True)
    args = parser.parse_args()
    manifest = json.loads(args.archive_manifest.read_text())
    height, width = manifest['preprocessing']['output_image_size_hw']
    intrinsics = np.load(args.run_dir / 'intrinsics.npy').tolist()
    params = intrinsics[:4] + [width, height]
    projection = getProjectionMatrix2(znear=.01, zfar=100., fx=params[0], fy=params[1],
        cx=params[2], cy=params[3], W=width, H=height).transpose(0, 1).cuda()
    background = torch.ones(3, device='cuda')
    root = args.run_dir / 'stream_snapshots'
    out = root / 'roundtrip'
    out.mkdir(exist_ok=False)
    rows = []
    for path in sorted(root.glob('snapshot_*.pt')):
        state = torch.load(path, map_location='cpu', weights_only=True)
        direct = GaussianModel(sh_degree=state['max_sh_degree'])
        direct.active_sh_degree = state['active_sh_degree']
        for name, value in state['parameters'].items():
            setattr(direct, '_' + name, value.cuda())
        ply = out / (path.stem + '.ply')
        write_map(state, ply)
        reloaded = load_gaussians(ply)
        keys = sorted(state['keyframe_w2c'])
        selected = [keys[i] for i in sorted(set(np.linspace(0, len(keys) - 1, min(3, len(keys))).astype(int)))]
        for uid in selected:
            camera = Camera.init_from_tracking(torch.zeros(3, height, width), None, None,
                state['keyframe_w2c'][uid].cuda(), uid, projection, params)
            with torch.no_grad():
                a = render(camera, direct, background)['render']
                b = render(camera, reloaded, background)['render']
            error = float((a - b).abs().max())
            rows.append({'snapshot': path.name, 'uid': uid, 'max_abs_render_error': error})
            assert error <= 1e-6, rows[-1]
        del direct, reloaded
    if not rows:
        raise RuntimeError('No real snapshots to verify')
    report = {'render_roundtrip_passed': True, 'evaluation_images_consumed': False, 'rows': rows}
    (out / 'result.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
