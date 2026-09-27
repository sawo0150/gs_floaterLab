#!/usr/bin/env python3
"""Causal training-packet pose diagnostic; no evaluator poses or GS optimization."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
from types import SimpleNamespace
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import torch
import torch.nn.functional as F
from lietorch import SE3
from exp78b_frozen_archive import FrozenTrackerArchive
from dense_visual_pose import matrix
from dense_pose_quality_refiner import QualityAuditedRefiner
import run_online_dense_training as trial
from online_runtime_dependencies import fingerprint

MODES = ('rgb_consistent', 'legacy_filler_compatible', 'tracker_consistent')


class ColorRefiner(QualityAuditedRefiner):
    def features(self, view):
        reverse = self.mode == 'tracker_consistent' or (
            self.mode == 'legacy_filler_compatible' and int(view.uid) in self.anchor_uids)
        image = view.original_image[[2, 1, 0]] if reverse else view.original_image
        return super().features(SimpleNamespace(uid=view.uid, original_image=image))


def cases(archive):
    """Choose three diagnostic examples; each example uses only its own prefix."""
    candidates, known_keyframes = [], set()
    for event in archive.events:
        known_keyframes.update(int(u) for u in event.get('frame_uids', []))
        if event['kind'] != 'keyframe_update':
            continue
        keys = sorted(int(u) for u in event['frame_uids'] if int(u) not in archive.heldout_uids)
        for left, right in reversed(list(zip(keys, keys[1:]))):
            available = [u for u in range(left + 1, right) if u in archive.arrival_by_uid
                         and u not in known_keyframes and u not in archive.heldout_uids]
            if available:
                uid = min(available, key=lambda u: (abs(u - (left + right) / 2), u))
                if right > int(event['emitted_at_frame_uid']):
                    raise ValueError('Future anchor in capture packet')
                candidates.append((event, left, right, uid))
                break
    if len(candidates) < 3:
        raise ValueError('Need three causal diagnostic examples')
    # This stratification chooses offline diagnostic cases only. It never
    # controls mapper admission, optimization or topology phases.
    return [candidates[round((len(candidates) - 1) * f)] for f in (.25, .5, .75)]


def camera(uid, image, depth, pose, intrinsic):
    height, width = image.shape[-2:]
    return SimpleNamespace(uid=int(uid), original_image=image.float() / 255., depth=depth,
                           R=pose[:3, :3], T=pose[:3, 3], image_height=height, image_width=width,
                           fx=float(intrinsic[0]), fy=float(intrinsic[1]),
                           cx=float(intrinsic[2]), cy=float(intrinsic[3]))


@torch.no_grad()
def reprojection_error(anchor, target, target_pose):
    """Raw RGB L1 on physically projected depth samples; not a map quality metric."""
    device = target_pose.device
    height, width = anchor.image_height, anchor.image_width
    y, x = torch.meshgrid(torch.arange(3, height, 8, device=device),
                          torch.arange(3, width, 8, device=device), indexing='ij')
    depth = torch.as_tensor(anchor.depth, device=device).reshape(height, width)[3::8, 3::8]
    points = torch.stack(((x - anchor.cx) / anchor.fx * depth,
                          (y - anchor.cy) / anchor.fy * depth, depth), dim=-1)
    transform = target_pose @ torch.linalg.inv(matrix(anchor))
    projected = points @ transform[:3, :3].T + transform[:3, 3]
    z = projected[..., 2]
    u = target.fx * projected[..., 0] / z.clamp(min=1e-8) + target.cx
    v = target.fy * projected[..., 1] / z.clamp(min=1e-8) + target.cy
    valid = (torch.isfinite(depth) & (depth > .01) & torch.isfinite(projected).all(-1)
             & (z > .01) & (u >= 0) & (u <= target.image_width - 1)
             & (v >= 0) & (v <= target.image_height - 1))
    grid = torch.stack((2 * u / (target.image_width - 1) - 1,
                        2 * v / (target.image_height - 1) - 1), dim=-1)
    sampled = F.grid_sample(target.original_image.to(device)[None], grid[None], align_corners=True)[0]
    source = anchor.original_image.to(device)[:, 3::8, 3::8]
    return (sampled - source).abs().mean(0), valid


def projection_check():
    # A frontoparallel plane shifted one pixel has a known exact image warp.
    y, x = torch.meshgrid(torch.arange(64), torch.arange(64), indexing='ij')
    rgb = torch.stack((x, y, x + y)).float() / 128 * 255
    pose = torch.eye(4, device='cuda')
    left = camera(0, rgb, torch.ones(64, 64), pose, [64., 64., 32., 32.])
    right = camera(1, torch.roll(rgb, 1, 2), None, pose, [64., 64., 32., 32.])
    correct = pose.clone(); correct[0, 3] = 1 / 64
    wrong = pose.clone(); wrong[0, 3] = -1 / 64
    error, valid = reprojection_error(left, right, correct)
    wrong_error, wrong_valid = reprojection_error(left, right, wrong)
    common = valid & wrong_valid
    assert error[common].max() < 1e-6 and wrong_error[common].mean() > .005
    return {'known_pixel_translation_max_error': float(error[common].max()),
            'wrong_sign_mean_error': float(wrong_error[common].mean())}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    dependencies = fingerprint()
    (args.output / 'runtime_dependencies.json').write_text(json.dumps(dependencies, indent=2) + '\n')
    (args.output / 'runner_source.py').write_bytes(Path(__file__).read_bytes())
    checks = projection_check()
    model_path = trial.BASE.PAPER_ROOT / 'pretrained_models/droid.pth'
    shared = QualityAuditedRefiner(model_path)
    sources = {str(model_path): hashlib.sha256(model_path.read_bytes()).hexdigest()}
    for path in [Path(__file__).resolve(), Path(trial.__file__).resolve(),
                 trial.BASE.WORKSPACE / 'benchmarks/online_gs/exp78b_frozen_archive.py'] + [
                 trial.BACKEND / 'vigs' / name for name in
                 ('dense_visual_pose.py', 'dense_visual_pose_reuse.py', 'dense_pose_quality.py', 'dense_pose_quality_refiner.py')]:
        sources[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
    rows = []
    for dataset, scene in trial.SCENES:
        archive = FrozenTrackerArchive(trial.BASE.sequence_paths(dataset, scene)['archive'])
        def lock(path):
            sources[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
        lock(archive.root / 'archive_manifest.json')
        lock(archive.root / archive.manifest['arrivals'])
        lock(Path(archive.manifest['input_calibration']))
        for event, left_uid, right_uid, uid in cases(archive):
            if {left_uid, right_uid, uid} & archive.heldout_uids:
                raise ValueError('Held-out image reached pose diagnostic')
            payload = archive.load_event_payload(event)
            lock(archive.root / event['payload'])
            ids = [int(u) for u in payload['frame_uids'].tolist()]
            anchors = []
            for aid in (left_uid, right_uid):
                pos = ids.index(aid)
                reference = payload['geometry_refs'][pos]
                geometry = archive.load_geometry(reference)
                if isinstance(reference, str):
                    lock(archive.root / reference)
                else:
                    for key in ('depth', 'normal'):
                        lock(archive.root / reference[key])
                pose = SE3(payload['poses'][pos:pos + 1].cuda()).matrix()[0]
                anchors.append(camera(aid, archive.load_rgb(aid), geometry['depth'], pose, payload['intrinsics'][pos]))
            alpha = (uid - left_uid) / (right_uid - left_uid)
            poses = [SE3(payload['poses'][ids.index(aid):ids.index(aid) + 1].cuda()) for aid in (left_uid, right_uid)]
            initial = (SE3.exp((poses[1] * poses[0].inv()).log() * alpha) * poses[0]).matrix()[0]
            target = camera(uid, archive.load_rgb(uid), None, initial, payload['intrinsics'][ids.index(left_uid)])
            for image_uid in (left_uid, right_uid, uid):
                lock(archive.image_dir / archive.arrival_by_uid[image_uid]['source_name'])
            outputs, errors, masks = {}, {}, {}
            before = [matrix(a).clone() for a in anchors]
            for mode in MODES:
                engine = ColorRefiner.__new__(ColorRefiner)
                engine.net, engine.cache, engine.measurements = shared.net, {}, {}
                engine.mode, engine.anchor_uids = mode, {left_uid, right_uid}
                pose, stats = engine.refine(*anchors, target)
                outputs[mode] = {'pose_w2c': pose.cpu().tolist(), 'stats': stats}
                pairs = [reprojection_error(anchor, target, pose) for anchor in anchors]
                errors[mode] = torch.cat([p[0].flatten() for p in pairs])
                masks[mode] = torch.cat([p[1].flatten() for p in pairs])
                if any(not torch.equal(matrix(a), original) for a, original in zip(anchors, before)):
                    raise RuntimeError('Pose diagnostic changed a fixed anchor')
                del engine
            common = torch.stack(list(masks.values())).all(0)
            if not common.any():
                raise ValueError('No common reprojection support across preprocessing modes')
            for mode in MODES:
                outputs[mode]['common_support_rgb_l1'] = float(errors[mode][common].mean())
            row = {'dataset': dataset, 'scene': scene, 'event_id': event['event_id'],
                   'available_through_uid': event['emitted_at_frame_uid'],
                   'anchor_uids': [left_uid, right_uid], 'dense_uid': uid,
                   'common_support_fraction': float(common.float().mean()), 'modes': outputs}
            rows.append(row)
            (args.output / 'cases.partial.json').write_text(json.dumps(rows, indent=2) + '\n')
            print(json.dumps({k: v for k, v in row.items() if k != 'modes'}), flush=True)
            print({mode: outputs[mode]['common_support_rgb_l1'] for mode in MODES}, flush=True)
    for path, digest in sources.items():
        if hashlib.sha256(Path(path).read_bytes()).hexdigest() != digest:
            raise RuntimeError(f'Source changed during diagnostic: {path}')
    if fingerprint() != dependencies:
        raise RuntimeError('Runtime dependencies changed during diagnostic')
    result = {'protocol': 'causal_training_pose_color_diagnostic_v1', 'projection_check': checks,
              'cases': rows, 'source_lock': sources, 'heldout_or_eval_poses_used': False,
              'gaussian_updates': 0, 'quality_claim': False,
              'limitations': 'Offline diagnostic on causal prefixes, not streaming performance. RGB warp residual includes occlusion/illumination effects and is not ground-truth pose error. No evaluator or mapper was changed.'}
    (args.output / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    (args.output / 'runner_source.py').write_bytes(Path(__file__).read_bytes())


if __name__ == '__main__':
    main()
