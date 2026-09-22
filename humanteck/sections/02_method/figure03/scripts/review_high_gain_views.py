#!/usr/bin/env python3
"""Render selected held-out views of existing final maps; no optimization."""
import json
import sys
from pathlib import Path

import numpy as np
import torch
import lietorch
from PIL import Image

WORK = Path('/home/intern/gs_floaterLab')
ROOT = Path(__file__).resolve().parent.parent
runtime = json.loads((WORK / 'results/experiments/exp94_normalized_metric_v2_fixed_eval/aria/aria301_305/normalized_variance_s0/mapping_replay_runtime.json').read_text())
sys.path.insert(0, str(Path(runtime['custom_root']) / 'vigs'))
sys.path.insert(0, str(WORK / 'benchmarks/online_gs'))
from exp78_evaluate_vigs_ply import load_gaussians, preprocess_image
from gaussian.renderer import render
from gaussian.utils.camera_utils import Camera
from gaussian.utils.graphics_utils import getProjectionMatrix2
from gaussian.utils.loss_utils import psnr


def main():
    records = json.loads((ROOT.parent / 'figure02/analysis/view_ranking.json').read_text())
    rows = [r for r in records if r['scene'] == 'aria301_305' and r['frame_index'] in (640, 980, 1180, 1410)]
    rows.sort(key=lambda r: r['frame_index'])
    runs = {name: Path(rows[0][name + '_run']) for name in ('baseline', 'ours')}
    command = json.loads((runs['ours'] / 'mapping_command.json').read_text())
    archive = Path(command[command.index('--archive') + 1])
    manifest = json.loads((archive / 'archive_manifest.json').read_text())
    calibration = np.loadtxt(manifest['input_calibration'])
    trajectories = {name: np.loadtxt(run / 'traj_full_beforeBA.txt') for name, run in runs.items()}
    models = {name: load_gaussians(run / '3dgs_before_final.ply') for name, run in runs.items()}
    results = []
    for row in rows:
        idx = row['frame_index']
        np.testing.assert_allclose(trajectories['baseline'][idx], trajectories['ours'][idx], atol=1e-6, rtol=0)
        rgb, params = preprocess_image(Path(manifest['input_image_directory']) / row['uid'], calibration, manifest['preprocessing']['undistort'])
        fx, fy, cx, cy, width, height = params
        projection = getProjectionMatrix2(znear=.01, zfar=100., fx=fx, fy=fy, cx=cx, cy=cy, W=width, H=height).T.cuda()
        pose = lietorch.SE3(torch.tensor(trajectories['ours'][idx, 1:], dtype=torch.float32, device='cuda')).inv().matrix().data
        camera = Camera.init_from_tracking(rgb.float()/255, None, None, pose, idx, projection, params)
        gt = camera.original_image.cuda()
        mask = gt > 0
        arrays = {'gt': gt.permute(1, 2, 0).cpu().numpy()}
        checks = {}
        for name, model in models.items():
            with torch.no_grad():
                pred = render(camera, model, torch.ones(3, device='cuda'))['render'].clamp(0, 1)
                checks[name] = float(psnr(pred[mask][None], gt[mask][None]).item())
            assert abs(checks[name] - row[name + '_psnr']) < .005, (idx, name, checks[name])
            arrays[name] = pred.permute(1, 2, 0).cpu().numpy()
        folder = ROOT / 'candidates/high_gain_review' / f'frame_{idx:04d}'
        folder.mkdir(parents=True, exist_ok=True)
        for name, array in arrays.items():
            # Same display rotation as the existing Aria Fig. 2 candidates.
            array = np.rot90(array, k=-1).copy()
            Image.fromarray((array*255).round().clip(0,255).astype('uint8')).save(folder / f'{name}.png')
        record = {**row, 'recomputed_psnr': checks, 'display_rotation_clockwise_degrees': 90,
                  'source_maps': {k: str(v / '3dgs_before_final.ply') for k,v in runs.items()},
                  'map_stage': 'final only', 'processing': 'display rotation only; no enhancement; no optimization'}
        (folder / 'provenance.json').write_text(json.dumps(record, indent=2) + '\n')
        results.append(record)
        camera.clean()
        print(idx, checks, 'PSNR verified', flush=True)
    (ROOT / 'candidates/high_gain_review/manifest.json').write_text(json.dumps(results, indent=2) + '\n')


if __name__ == '__main__':
    main()
