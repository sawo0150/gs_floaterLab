#!/usr/bin/env python3
"""Convert Oxford Spires cam0 + IMU sequences to the official VIGS tracker input contract (CPU only).

Per sequence, into /ssd/intern/paperExperiments/data/oxford_spires/vigs/<sequence>/:
  rgb/<ns>.jpg   cam0 equidistant fisheye rectified to pinhole (R = I, so the camera frame and T_cam_imu are kept),
                 720×540, new K from cv2.fisheye.estimateNewCameraMatrixForUndistortRectify(balance=0)
  imu.txt        ns, gyro xyz, accel xyz (EuRoC/Aria order, comma separated)
  calib.txt      fx fy cx cy 0 0 0 0
  config.yaml    official Aria adapter tracking contract with Oxford IMU noise (imu.yaml), 400 Hz and
                 Tcb = T_cam0_imu from cam-lidar-imu.yaml (C_q_CI xyzw, C_r_CI); calibration files come from the
                 sequence's INPUTS.json calibration root (nearest calibration session, per the dataset README)
  heldout.json   zero_based_frame_index % 5 == 0 OR final frame (same rule as aria301_12F)
  prep.json      sources, hashes, counts
GT trajectories are not read. Nothing is written into the raw dataset folders.

  python prepare_oxford_vigs.py --sequences 2024-07-09-new-college-01 ... [--workers 8]
"""
import argparse
import hashlib
import json
from multiprocessing import Pool
from pathlib import Path

import numpy as np

ROOT = Path('/ssd/intern/paperExperiments/data/oxford_spires')
OUT = ROOT / 'vigs'
ADAPTER = Path(__file__).resolve().parents[2] / 'config/vigs_official_aria_adapter.yaml'
SIZE = (720, 540)


def sha_file(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def quat_xyzw_to_R(q):
    x, y, z, w = q
    n = np.sqrt(x * x + y * y + z * z + w * w); x, y, z, w = x / n, y / n, z / n, w / n
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                     [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


_MAP = None


def _init(m1, m2):
    global _MAP
    _MAP = (m1, m2)


def _rectify(job):
    import cv2
    src, dst = job
    img = cv2.imread(str(src), cv2.IMREAD_COLOR)
    if img is None:
        raise RuntimeError(f'unreadable image {src}')
    out = cv2.remap(img, _MAP[0], _MAP[1], interpolation=cv2.INTER_AREA, borderMode=cv2.BORDER_CONSTANT)
    if not cv2.imwrite(str(dst), out, [cv2.IMWRITE_JPEG_QUALITY, 95]):
        raise RuntimeError(f'write failed {dst}')
    return dst.name


def write_imu_calib(s, o, newK):
    # IMU: secs,nsecs,acc xyz,gyro xyz  ->  ns, gyro xyz, accel xyz (plain float repr; numpy 2 scalars are cast)
    raw = np.loadtxt(s / 'raw/imu.csv', delimiter=',', skiprows=1)
    ns = raw[:, 0].astype(np.int64) * 1_000_000_000 + raw[:, 1].astype(np.int64)
    order = np.argsort(ns, kind='stable')
    with (o / 'imu.txt').open('w') as f:
        for i in order:
            a, g = [float(v) for v in raw[i, 2:5]], [float(v) for v in raw[i, 5:8]]
            f.write(f'{int(ns[i])},{g[0]!r},{g[1]!r},{g[2]!r},{a[0]!r},{a[1]!r},{a[2]!r}\n')
    fx, fy, cx, cy = (float(newK[0, 0]), float(newK[1, 1]), float(newK[0, 2]), float(newK[1, 2]))
    (o / 'calib.txt').write_text(f'{fx!r} {fy!r} {cx!r} {cy!r} 0.0 0.0 0.0 0.0\n')
    return raw


def repair_text(seq):
    """Rewrite imu.txt/calib.txt of an existing prepared sequence (images and held-out are unchanged)."""
    o = OUT / seq
    prep = json.loads((o / 'prep.json').read_text())
    for name in ('imu.txt', 'calib.txt'):
        bad = o / name
        if bad.exists():
            (o / 'failed_attempts').mkdir(exist_ok=True)
            bad.rename(o / 'failed_attempts' / f'numpy_repr_{name}')
    write_imu_calib(ROOT / 'sequences' / seq, o, np.array(prep['K_out']))
    print('REPAIRED', seq, (o / 'calib.txt').read_text().strip(), flush=True)


def prepare(seq, workers):
    import cv2
    import yaml
    s = ROOT / 'sequences' / seq
    o = OUT / seq
    if o.exists():
        raise FileExistsError(f'{o} exists; prepared inputs are preserved')
    # Calibration root chosen by the dataset's per-sequence INPUTS.json (README: nearest calibration session).
    croot = ROOT / json.loads((s / 'INPUTS.json').read_text())['calibration_root_relative_to_dataset']
    cam_file, ext_file, imu_file = croot / 'cam0.yaml', croot / 'cam-lidar-imu.yaml', croot / 'imu.yaml'
    cam = yaml.safe_load(cam_file.read_text())
    K = np.array(cam['camera_matrix']['data'], float).reshape(3, 3)
    D = np.array(cam['distortion_coefficients']['data'], float).reshape(4, 1)
    assert cam['distortion_model'] == 'equidistant', cam['distortion_model']
    wh = (int(cam['image_width']), int(cam['image_height']))
    newK = cv2.fisheye.estimateNewCameraMatrixForUndistortRectify(K, D, wh, np.eye(3), balance=0.0, new_size=SIZE)
    m1, m2 = cv2.fisheye.initUndistortRectifyMap(K, D, np.eye(3), newK, SIZE, cv2.CV_16SC2)
    names = sorted((q for q in (s / 'raw/images/cam0').iterdir() if q.suffix == '.jpg'),
                   key=lambda q: tuple(int(x) for x in q.stem.split('.')))
    (o / 'rgb').mkdir(parents=True)
    jobs = []
    for q in names:
        sec, nsec = q.stem.split('.')
        ns = int(sec) * 1_000_000_000 + int(nsec.ljust(9, '0')[:9])
        jobs.append((q, o / 'rgb' / f'{ns}.jpg'))
    with Pool(workers, initializer=_init, initargs=(m1, m2)) as pool:
        written = pool.map(_rectify, jobs, chunksize=32)
    uids = [j[1].name for j in jobs]
    assert written == uids and len(set(uids)) == len(uids)
    raw = write_imu_calib(s, o, newK)
    ext = yaml.safe_load(ext_file.read_text())['cam0']
    T = np.eye(4); T[:3, :3] = quat_xyzw_to_R(ext['C_q_CI']); T[:3, 3] = ext['C_r_CI']
    imu = yaml.safe_load(imu_file.read_text())
    cfg = yaml.safe_load(ADAPTER.read_text())
    cfg['IMU'].update(frequency=float(imu['update_rate']),
                      accelerometer_noise_density=float(imu['accelerometer_noise_density']),
                      accelerometer_random_walk=float(imu['accelerometer_random_walk']),
                      gyroscope_noise_density=float(imu['gyroscope_noise_density']),
                      gyroscope_random_walk=float(imu['gyroscope_random_walk']),
                      rgb_file_in_nanoseconds=True, imu_in_nanoseconds=True, imu_time_offset=0.0,
                      Tcb_np=[[float(v) for v in row] for row in T])
    (o / 'config.yaml').write_text('# Oxford Spires cam0 adapter generated by prepare_oxford_vigs.py from '
                                   'vigs_official_aria_adapter.yaml (tracking contract unchanged; IMU block from '
                                   'Oxford calibration).\n' + yaml.safe_dump(cfg, sort_keys=False))
    views = [dict(frame_index=i, timestamp_token=u[:-4], uid=u) for i, u in enumerate(uids)
             if i % 5 == 0 or i == len(uids) - 1]
    sha_json = lambda x: hashlib.sha256(json.dumps(x, sort_keys=True).encode()).hexdigest()
    (o / 'heldout.json').write_text(json.dumps(dict(
        dataset='oxford', sequence=seq, role='transfer', selection_rule='zero_based_frame_index % 5 == 0 OR final frame',
        mapping_disjoint_required=True, frame_count=len(uids), eval_count=len(views),
        all_input_uids_sha256=sha_json(uids), eval_uids_sha256=sha_json([v['uid'] for v in views]), views=views),
        indent=1))
    (o / 'prep.json').write_text(json.dumps(dict(
        sequence=seq, source=str(s), frames=len(uids), imu_samples=int(len(raw)), out_size=list(SIZE),
        K_in=K.tolist(), D_in=D.ravel().tolist(), K_out=newK.tolist(), T_cam_imu=T.tolist(),
        sources={str(p): sha_file(p) for p in (cam_file, s / 'raw/imu.csv', ext_file, imu_file, s / 'INPUTS.json',
                                               ADAPTER)},
        script_sha256=sha_file(Path(__file__)), gt_read=False), indent=1))
    print('PREPARED', seq, len(uids), 'frames', len(views), 'held-out', 'K_out', np.round(newK, 2).tolist(), flush=True)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--sequences', nargs='+', required=True)
    p.add_argument('--workers', type=int, default=8)
    p.add_argument('--repair-text', action='store_true')
    a = p.parse_args()
    for seq in a.sequences:
        repair_text(seq) if a.repair_text else prepare(seq, a.workers)


if __name__ == '__main__':
    main()
