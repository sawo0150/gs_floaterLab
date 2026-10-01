#!/usr/bin/env python3
"""Render the current fixed40 saved maps for the scene-centered teaser.

No training. Use the unmodified primary PLY evaluator's model, camera and
renderer; verify selected-view PSNR against the saved full-cohort evaluation.
Only the novel scene-context image uses a declared spatial cutaway.
"""
import argparse
import copy
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
from collect_cvpr_assets import ROOT, OUT, RESULTS, read, write, sha
from evaluate_cvpr_checkpoints import load_evaluator


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--scene', default='table_06')
    p.add_argument('--frame', type=int, default=1930)
    p.add_argument('--roi', type=int, nargs=4, default=[105, 22, 340, 145])
    a = p.parse_args()
    catalog = ROOT / 'paper/figures/figure05_rendering_comparison/analysis/rendering_catalog.json'
    assert read(catalog)['complete_candidate_render_review']
    from selected_mapping_check import gpu_idle
    gpu_idle()
    import cv2
    import numpy as np
    import torch
    import lietorch
    from PIL import Image
    module = load_evaluator()
    item = next(r for r in read(OUT / 'scene_inventory.json') if r['dataset'] == 'rpng' and r['scene'] == a.scene)
    base = RESULTS / 'cvpr_assets/fixed_work_v1/render40/rpng' / a.scene
    runs = {arm: base / arm for arm in ['d3', 'vanilla']}
    trajectory = np.loadtxt(runs['d3'] / 'traj_full_beforeBA.txt')
    np.testing.assert_array_equal(trajectory, np.loadtxt(runs['vanilla'] / 'traj_full_beforeBA.txt'))
    pose = lietorch.SE3(torch.tensor(trajectory[a.frame, 1:], dtype=torch.float32, device='cuda')).matrix().cpu().numpy()
    names = module.numeric_names(Path(item['image_dir']))
    rgb, params = module.preprocess_image(Path(item['image_dir']) / names[a.frame], np.loadtxt(item['calibration']), True)
    a.output.mkdir(parents=True, exist_ok=False)
    def save(path, tensor):
        array = tensor.detach().cpu().numpy()
        if array.ndim == 3 and array.shape[0] == 3: array = array.transpose(1, 2, 0)
        Image.fromarray(np.rint(np.clip(array, 0, 1) * 255).astype(np.uint8)).save(path)
    def camera(world_to_camera, intrinsics=params, image=None):
        fx, fy, cx, cy, width, height = intrinsics
        projection = module.getProjectionMatrix2(znear=.01, zfar=100., fx=fx, fy=fy,
            cx=cx, cy=cy, W=width, H=height).T.cuda()
        return module.Camera.init_from_tracking(image, None, None,
            torch.tensor(world_to_camera, dtype=torch.float32, device='cuda'), a.frame, projection, intrinsics)
    render_ext = lietorch.SE3(torch.tensor(trajectory[a.frame, 1:], dtype=torch.float32, device='cuda')).inv().matrix().cpu().numpy()
    view = camera(render_ext, image=rgb.float() / 255)
    save(a.output / 'gt.png', rgb.float() / 255)
    models, sources = {}, {}
    for arm, run in runs.items():
        source = run / '3dgs_before_final.ply'
        expected = read(run / 'psnr/strict_fixed_manifest/final_result.json')
        q = expected['predeclared_fixed_manifest_posthoc']
        assert q['mapping_disjoint'] and q['mapping_view_overlap_count'] == 0
        row = next(r for r in expected['per_view'] if r['frame_index'] == a.frame)
        assert row['predeclared_fixed_manifest_split'] and not row['is_mapping_view']
        model = module.load_gaussians(source); models[arm] = model
        with torch.no_grad(): rendered = module.render(view, model, torch.ones(3, device='cuda'))
        prediction = rendered['render'].clamp(0, 1)
        gt = view.original_image.cuda(); mask = gt > 0
        score = float(module.psnr(prediction[mask][None], gt[mask][None]).item())
        assert abs(score - row['psnr']) < .005, (arm, score, row['psnr'])
        save(a.output / f'{arm}_rgb.png', prediction)
        depth = rendered['depth'].squeeze().cpu().numpy()
        np.save(a.output / f'{arm}_depth.npy', depth)
        normalized = np.clip((depth - .5) / 3.5, 0, 1)
        normalized = np.nan_to_num(normalized)
        color = cv2.applyColorMap(np.rint(normalized * 255).astype(np.uint8), cv2.COLORMAP_VIRIDIS)[:, :, ::-1]
        color[(~np.isfinite(depth)) | (depth <= 0)] = 255
        Image.fromarray(color).save(a.output / f'{arm}_depth.png')
        checkpoint_rgb = run / 'curve_evaluation/final/images' / f'{a.frame:06d}_render.png'
        if checkpoint_rgb.exists(): assert sha(checkpoint_rgb) == sha(a.output / f'{arm}_rgb.png')
        end = read(run / 'render_result.json')
        sources[arm] = dict(run=str(run), map=str(source), map_sha256=sha(source),
            metric=str(run / 'psnr/strict_fixed_manifest/final_result.json'),
            metric_sha256=sha(run / 'psnr/strict_fixed_manifest/final_result.json'),
            training_renders=end['render_counts']['training'], optimizer_steps=end['main_optimizer_steps'],
            frame_psnr=score, recorded_frame_psnr=row['psnr'], full_cohort_psnr=q['mean_psnr'],
            full_cohort_views=q['view_count'], mapping_disjoint=True)
    assert len({r['training_renders'] for r in sources.values()}) == 1
    model = models['d3']; xyz = model.get_xyz.detach().cpu().numpy()
    local = (xyz - pose[:3, 3]) @ pose[:3, :3]
    low, high = np.array([-2.7, -.65, .05]), np.array([2.7, 2., 2.4])
    keep = ((local >= low) & (local <= high)).all(1)
    assert keep.any()
    section = copy.copy(model); mask = torch.tensor(keep, device='cuda')
    for attr in ['_xyz', '_opacity', '_scaling', '_rotation', '_features_dc', '_features_rest']:
        setattr(section, attr, getattr(model, attr)[mask].detach())
    variants = []
    intrinsics = [980., 980., 700., 490., 1400, 980]
    up = -pose[:3, 1]
    for name, eye_local in [('V1', [-2., -1.5, -3.2]), ('V2', [-1., -1.2, -3.4]),
                            ('V3', [1.2, -1.4, -3.4]), ('V4', [-2., -2.4, -2.])]:
        eye = pose[:3, 3] + pose[:3, :3] @ np.array(eye_local)
        target = pose[:3, 3] + pose[:3, :3] @ np.array([0, .4, 1.8])
        forward = target - eye; forward /= np.linalg.norm(forward)
        right = np.cross(forward, up); right /= np.linalg.norm(right)
        down = np.cross(forward, right)
        ext = np.eye(4); ext[:3, :3] = np.stack([right, down, forward]); ext[:3, 3] = -ext[:3, :3] @ eye
        with torch.no_grad(): rendered = module.render(camera(ext, intrinsics), section, torch.ones(3, device='cuda'))
        save(a.output / f'map_{name}.png', rendered['render'])
        variants.append(dict(id=name, image=f'map_{name}.png', world_to_camera=ext.tolist(), intrinsics=intrinsics))
    keyframes = np.loadtxt(runs['d3'] / 'traj_kf_beforeBA.txt')
    middle = int(np.argmin(abs(keyframes[:, 0] - trajectory[a.frame, 0])))
    start, stop = max(0, middle - 7), min(len(keyframes), middle + 8)
    fx, fy, cx, cy, width, height = params
    frusta = []
    for index in np.linspace(start, stop - 1, 4).round().astype(int):
        c2w = lietorch.SE3(torch.tensor(keyframes[index, 1:], dtype=torch.float32, device='cuda')).matrix().cpu().numpy()
        z = .14
        corners = np.array([[0, 0, 0], [-cx/fx*z, -cy/fy*z, z], [(width-cx)/fx*z, -cy/fy*z, z],
                            [(width-cx)/fx*z, (height-cy)/fy*z, z], [-cx/fx*z, (height-cy)/fy*z, z]])
        frusta.append(dict(keyframe_index=int(index), corners_world=(corners @ c2w[:3, :3].T + c2w[:3, 3]).tolist()))
    depth = np.load(a.output / 'd3_depth.npy')
    u, v = (a.roi[0]+a.roi[2])//2, (a.roi[1]+a.roi[3])//2
    patch = depth[max(0, v-2):v+3, max(0, u-2):u+3]
    valid = patch[np.isfinite(patch) & (patch > 0)]; assert len(valid)
    z = float(np.median(valid))
    roi_world = pose[:3, :3] @ np.array([(u-cx)/fx*z, (v-cy)/fy*z, z]) + pose[:3, 3]
    assert all(sha(Path(r['map'])) == r['map_sha256'] for r in sources.values())
    write(a.output / 'provenance.json', dict(kind='actual_current_teaser_source_capture',
        scene=a.scene, dataset='rpng', frame=a.frame, roi=a.roi, source_runs=sources,
        all_candidate_scenes_evaluated_before_selection=True, camera_to_world=pose.tolist(),
        intrinsics=params, depth_range_m=[.5, 4.], depth_interpretation='expected rendered depth, no independent geometry accuracy claim',
        scene_display_cutaway=dict(low=low.tolist(), high=high.tolist(), input_gaussians=len(xyz), displayed=int(keep.sum())),
        map_variants=variants, trajectory_source=str(runs['d3'] / 'traj_kf_beforeBA.txt'),
        trajectory_world=keyframes[start:stop, 1:4].tolist(), trajectory_segment=[start, stop],
        camera_frusta=frusta, roi_center_world=roi_world.tolist(),
        source_maps_unchanged=True, optimizer_updates=0,
        source_evaluator=str(module.__file__), source_evaluator_sha256=sha(Path(module.__file__)),
        script_sha256=sha(Path(__file__)), files={p.name: sha(p) for p in a.output.glob('*') if p.is_file()}))
    print('ACTUAL_TEASER_CAPTURE', a.scene, a.frame, sources, flush=True)


if __name__ == '__main__':
    sys.path.insert(0, '/home/intern/VIGS-SLAM-custom/scripts/selected_mapping')
    main()
