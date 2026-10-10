"""Prepare an ordered COLMAP image sequence (StaticHikes, MipNeRF360, Tanks and Temples) as a C-harness input.

Writes <out>/<dataset>/<scene>/v1/{archive, reference_scene, scene_contract.json} in the external_mapper_packets_v2 layout
used by the 6N contract inputs (RGB-only, no IMU, no depth). Frames are taken in filename order, undistorted with the
COLMAP camera (PINHOLE / OPENCV radtan) and resized once to a fixed output size; the archive serves those images unchanged
(intrinsics are the pinhole intrinsics of the output size). The evaluation reference is the COLMAP camera-to-world pose
(arbitrary scale; the evaluator aligns with Sim(3)); frames COLMAP did not register, or whose centre jumps far from both
neighbours (mis-registration), have no reference and are excluded from training and evaluation, as for other datasets.
Every `holdout`-th frame (On-the-fly NVS convention: 10 StaticHikes, 8 MipNeRF360/T&T) is held out for evaluation.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path

import cv2
import numpy as np

MODELS = {0: ('SIMPLE_PINHOLE', 3), 1: ('PINHOLE', 4), 2: ('SIMPLE_RADIAL', 4), 3: ('RADIAL', 5), 4: ('OPENCV', 8)}


def read_cameras(path):
    cams = {}
    with open(path, 'rb') as f:
        for _ in range(struct.unpack('<Q', f.read(8))[0]):
            cid, model, w, h = struct.unpack('<iiQQ', f.read(24))
            name, n = MODELS[model]
            cams[cid] = (name, w, h, np.array(struct.unpack('<' + 'd' * n, f.read(8 * n))))
    return cams


def read_images(path):
    out = {}
    with open(path, 'rb') as f:
        for _ in range(struct.unpack('<Q', f.read(8))[0]):
            _, qw, qx, qy, qz, tx, ty, tz, cid = struct.unpack('<idddddddi', f.read(64))
            name = b''
            while (c := f.read(1)) != b'\0':
                name += c
            f.read(24 * struct.unpack('<Q', f.read(8))[0])
            w, x, y, z = qw, qx, qy, qz
            R = np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                          [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                          [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])
            w2c = np.eye(4); w2c[:3, :3] = R; w2c[:3, 3] = [tx, ty, tz]
            out[name.decode()] = (cid, np.linalg.inv(w2c))
    return out


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def prepare(dataset, scene, root, images, out, holdout, size_hw, fps=30.0, jump=20.0):
    root = Path(root); images = Path(images)
    dst = Path(out) / dataset / scene / 'v1'
    if dst.exists():
        raise FileExistsError(dst)
    cams = read_cameras(root / 'sparse/0/cameras.bin')
    regs = read_images(root / 'sparse/0/images.bin')
    if len(cams) != 1:
        raise ValueError('expected one shared COLMAP camera')
    model, cw, ch, p = next(iter(cams.values()))
    names = sorted(x.name for x in images.iterdir() if x.suffix.lower() in ('.jpg', '.jpeg', '.png'))
    w0, h0 = cv2.imread(str(images / names[0])).shape[1::-1]
    sx, sy = w0 / cw, h0 / ch                                   # COLMAP camera may be at a larger resolution
    if model == 'PINHOLE':
        fx, fy, cx, cy = p; dist = np.zeros(4)
    elif model == 'SIMPLE_PINHOLE':
        fx = fy = p[0]; cx, cy = p[1:]; dist = np.zeros(4)
    elif model == 'OPENCV':
        fx, fy, cx, cy = p[:4]; dist = p[4:8]
    else:
        raise ValueError('unsupported COLMAP model ' + model)
    K0 = np.array([[fx * sx, 0, cx * sx], [0, fy * sy, cy * sy], [0, 0, 1.]])
    h, w = size_hw
    K = K0.copy(); K[0] *= w / w0; K[1] *= h / h0
    mx, my = cv2.initUndistortRectifyMap(K0, dist, np.eye(3), K, (w, h), cv2.CV_32FC1)
    # reference poses in sequence order; drop mis-registered frames (centre jump vs both neighbours)
    c2w = [regs[n][1] if n in regs else None for n in names]
    centres = [None if t is None else t[:3, 3] for t in c2w]
    steps = [np.linalg.norm(centres[i + 1] - centres[i]) for i in range(len(names) - 1)
             if centres[i] is not None and centres[i + 1] is not None]
    med = float(np.median(steps)); outliers = []
    for i, c in enumerate(centres):
        if c is None:
            continue
        nb = [centres[j] for j in (i - 1, i + 1) if 0 <= j < len(names) and centres[j] is not None]
        if nb and all(np.linalg.norm(c - q) > jump * med for q in nb):
            outliers.append(i); c2w[i] = None
    ref = dst / 'reference_scene'; (ref / 'rgb').mkdir(parents=True); (dst / 'archive').mkdir()
    frames, oracle = [], []
    for uid, name in enumerate(names):
        im = cv2.remap(cv2.imread(str(images / name)), mx, my, cv2.INTER_AREA if w < w0 else cv2.INTER_LINEAR)
        path = ref / 'rgb' / f'{uid:06d}.png'
        cv2.imwrite(str(path), im)
        held = uid % holdout == 0
        frames.append(dict(uid=uid, timestamp=uid / fps, rgb=str(path), heldout=held, evaluation_depth=None, source_name=name))
        oracle.append(dict(uid=uid, timestamp=uid / fps, c2w=None if c2w[uid] is None else c2w[uid].tolist()))
    (ref / 'arrivals.jsonl').write_text(''.join(json.dumps(f) + '\n' for f in frames))
    (ref / 'oracle_poses_evaluator_only.json').write_text(json.dumps(oracle))
    heldout = [f['uid'] for f in frames if f['heldout']]
    (ref / 'heldout_uids.json').write_text(json.dumps(heldout))
    missing = [o['uid'] for o in oracle if o['c2w'] is None]
    scene_meta = dict(schema='external_mapper_scene_v2', dataset=dataset, scene=scene, source_root=str(root),
                      calibration=[K[0, 0], K[1, 1], K[0, 2], K[1, 2]], distortion_model='rectified_pinhole', height=h, width=w,
                      arrivals='arrivals.jsonl', heldout='heldout_uids.json', gt_pose_file='oracle_poses_evaluator_only.json',
                      gt_pose_convention='camera_to_world_opencv_colmap_scale', reference_kind='colmap_sfm_reference',
                      gt_missing_frames=len(missing), mis_registered_frames=outliers, depth_scale=1.0,
                      depth_training_default=False, depth_associated_frames=0, imu_available=False, frame_count=len(frames),
                      heldout_count=len(heldout), duration_seconds=len(frames) / fps, synthetic_timestamps_fps=fps,
                      colmap_camera=dict(model=model, width=cw, height=ch, params=p.tolist()),
                      input_hashes={'cameras.bin': sha(root / 'sparse/0/cameras.bin'), 'images.bin': sha(root / 'sparse/0/images.bin')},
                      reference_source='COLMAP sparse/0 shipped with the dataset (not independent GT)')
    (ref / 'scene.json').write_text(json.dumps(scene_meta, indent=1))
    (dst / 'archive' / 'arrivals.jsonl').write_text(''.join(json.dumps(dict(
        frame_uid=f['uid'], sensor_timestamp=f['timestamp'], held_out=f['heldout'], rgb=f['rgb'])) + '\n' for f in frames))
    (dst / 'archive' / 'archive_manifest.json').write_text(json.dumps(dict(
        schema_version='external_mapper_packets_v2', prepared_scene=str(ref), dataset=dataset, scene=scene, arrivals='arrivals.jsonl',
        events=[], preprocessing=dict(output_image_size_hw=[h, w], intrinsics=[K[0, 0], K[1, 1], K[0, 2], K[1, 2]]),
        geometry_source='not present; each baseline must run its own frontend', shared_geometry_replay_allowed=False,
        GT_depth_training_allowed=False, full_sequence=True, source_frame_count=len(frames)), indent=1))
    train = [f['uid'] for f in frames if not f['heldout'] and c2w[f['uid']] is not None]
    held_ok = [u for u in heldout if c2w[u] is not None]
    total = 6 * len(train)
    contract = dict(dataset=dataset, scene=scene, archive=str(dst / 'archive'), reference_kind='colmap_sfm_reference',
                    reference_pose_file=str(ref / 'oracle_poses_evaluator_only.json'), input_frames=len(frames),
                    training_uids=train, heldout_uids=held_ok, reference_missing_uids=missing, render_budget=total,
                    renders_per_training_input=6, segment_training_frames=64,
                    snapshot_renders=list(range(384, total, 384)) + [total], geometry_reference=None, own_frontend_required=True,
                    input_frame_cap=None, prepared_inputs_verified=True, benchmark_completed=False,
                    common_calibration_policy='COLMAP camera, one-time undistort + resize to output size; local prep 2026-10-10')
    (dst / 'scene_contract.json').write_text(json.dumps(contract, indent=1))
    print(dataset, scene, f'{len(frames)} frames, train {len(train)}, heldout {len(held_ok)}, missing {len(missing)} '
          f'(mis-registered {outliers}), {w0}x{h0} {model} -> {w}x{h}, K {K[0,0]:.1f} {K[1,1]:.1f} {K[0,2]:.1f} {K[1,2]:.1f}')


if __name__ == '__main__':
    a = argparse.ArgumentParser()
    a.add_argument('--dataset', required=True); a.add_argument('--scene', required=True)
    a.add_argument('--root', required=True); a.add_argument('--images', required=True)
    a.add_argument('--out', required=True); a.add_argument('--holdout', type=int, required=True)
    a.add_argument('--size', type=int, nargs=2, required=True, metavar=('H', 'W'))
    x = a.parse_args()
    prepare(x.dataset, x.scene, x.root, x.images, x.out, x.holdout, tuple(x.size))
