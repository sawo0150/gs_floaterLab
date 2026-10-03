#!/usr/bin/env python3
"""M2DGR ROS bag → VIGS inputs → frozen tracker archive → setup (dataset key 'm2dgr').

--extract (CPU; run with the aria-tools venv that has rosbags): /camera/color/image_raw/compressed written byte-for-byte
  as rgb/<header ns>.jpg; /handsfree/imu as ns, gyro xyz, accel xyz; calib.txt = D435i colour pinhole + radtan
  (calibration_results.txt / my_params_camera.yaml); config.yaml = official Aria adapter tracking contract with the
  handsfree IMU noise (my_params_camera.yaml acc_n/gyr_n/acc_w/gyr_w), measured rate and Tcb = inv(imu^T_cam);
  heldout every 5th frame + final; mapping_v7.yaml = vigs_final_v7_aria.yaml with that IMU block.
--execute (GPU, vigs env): capture (--undistort), validation, setup (same as the other extra datasets).
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import m2dgr_paths as MP  # noqa: E402

FX, FY, CX, CY = 617.971050917033, 616.445131524790, 327.710279392468, 253.976983707814
DIST = (0.148000794688248, -0.217835187249065, 0.0, 0.0)
R_IMU_CAM = [[0.0, 0.0, 1.0], [-1.0, 0.0, 0.0], [0.0, -1.0, 0.0]]
T_IMU_CAM = [0.57711, -0.00012, 0.83333]
NOISE = dict(accelerometer_noise_density=1.2820343288774358e-01, gyroscope_noise_density=2.1309311394972831e-02,
             accelerometer_random_walk=1.3677912958097768e-02, gyroscope_random_walk=3.6603917782528627e-04)


def extract(seq):
    import numpy as np
    import yaml
    from rosbags.highlevel import AnyReader
    d = MP.PREP / seq
    if (d / 'rgb').exists():
        raise FileExistsError(f'{d}/rgb exists; extracted inputs are preserved')
    (d / 'rgb').mkdir(parents=True)
    imu = []; names = []
    with AnyReader([MP.BAGS / seq / 'rgb_imu.bag']) as r:
        for con, t, raw in r.messages(connections=[c for c in r.connections
                                                   if c.topic in ('/camera/color/image_raw/compressed', '/handsfree/imu')]):
            msg = r.deserialize(raw, con.msgtype)
            ns = int(msg.header.stamp.sec) * 1_000_000_000 + int(msg.header.stamp.nanosec)
            if con.topic == '/handsfree/imu':
                g, a = msg.angular_velocity, msg.linear_acceleration
                imu.append((ns, g.x, g.y, g.z, a.x, a.y, a.z))
            else:
                assert 'jpeg' in msg.format.lower() or 'jpg' in msg.format.lower(), msg.format
                name = f'{ns}.jpg'
                assert not (d / 'rgb' / name).exists(), name
                (d / 'rgb' / name).write_bytes(bytes(msg.data)); names.append(name)
    imu.sort()
    with (d / 'imu.txt').open('w') as f:
        for row in imu:
            f.write(f'{row[0]},' + ','.join(repr(float(v)) for v in row[1:]) + '\n')
    rate = (len(imu) - 1) / ((imu[-1][0] - imu[0][0]) / 1e9)
    acc = np.linalg.norm(np.array([r[4:7] for r in imu[:200]]), axis=1).mean()
    (d / 'calib.txt').write_text(' '.join(repr(float(v)) for v in (FX, FY, CX, CY, *DIST)) + '\n')
    T = np.eye(4); T[:3, :3] = R_IMU_CAM; T[:3, 3] = T_IMU_CAM
    Tcb = np.linalg.inv(T)
    adapter = yaml.safe_load((HERE.parents[1] / 'config/vigs_official_aria_adapter.yaml').read_text())
    adapter['IMU'].update(frequency=float(round(rate, 2)), rgb_file_in_nanoseconds=True, imu_in_nanoseconds=True,
                          imu_time_offset=0.0, Tcb_np=[[float(v) for v in row] for row in Tcb], **NOISE)
    (d / 'config.yaml').write_text('# official Aria adapter tracking contract with the M2DGR handsfree IMU block '
                                   '(prepare_m2dgr.py)\n' + yaml.safe_dump(adapter, sort_keys=False))
    names.sort(key=lambda n: int(n[:-4]))
    views = [dict(frame_index=i, timestamp_token=n[:-4], uid=n) for i, n in enumerate(names)
             if i % 5 == 0 or i == len(names) - 1]
    sj = lambda x: hashlib.sha256(json.dumps(x, sort_keys=True).encode()).hexdigest()
    (d / 'heldout.json').write_text(json.dumps(dict(
        dataset='m2dgr', sequence=seq, role='transfer', selection_rule='zero_based_frame_index % 5 == 0 OR final frame',
        mapping_disjoint_required=True, frame_count=len(names), eval_count=len(views), all_input_uids_sha256=sj(names),
        eval_uids_sha256=sj([v['uid'] for v in views]), views=views), indent=1))
    v7 = yaml.safe_load((HERE.parents[1] / 'config/vigs_final_v7_aria.yaml').read_text()); v7['IMU'] = adapter['IMU']
    (d / 'mapping_v7.yaml').write_text('# vigs_final_v7_aria.yaml with the M2DGR IMU block (prepare_m2dgr.py)\n'
                                       + yaml.safe_dump(v7, sort_keys=False))
    (d / 'prep.json').write_text(json.dumps(dict(sequence=seq, frames=len(names), imu_samples=len(imu),
                                                 imu_rate_hz=rate, accel_norm_first200=float(acc), Tcb=Tcb.tolist()), indent=1))
    print('EXTRACTED', seq, len(names), 'frames', len(views), 'held-out', f'imu {rate:.1f} Hz |a|={acc:.2f}', flush=True)


def capture(seq, buffer):
    import prepare_selfaria
    prepare_selfaria.capture(seq, buffer, P=MP, dataset='m2dgr', undistort=True)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--sequences', nargs='+', default=list(MP.SEQUENCES))
    p.add_argument('--extract', action='store_true')
    p.add_argument('--execute', action='store_true')
    p.add_argument('--buffer', type=int, default=700)
    a = p.parse_args()
    for seq in a.sequences:
        if a.extract:
            extract(seq)
        if a.execute:
            capture(seq, a.buffer)


if __name__ == '__main__':
    main()
