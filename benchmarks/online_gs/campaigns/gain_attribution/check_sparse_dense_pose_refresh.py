#!/usr/bin/env python3
"""Compare sparse interpolation with the frozen v12 backend + causal IMU repair."""
import ast
import json
from pathlib import Path
import sys
import time
from types import SimpleNamespace, MethodType

import numpy as np
import torch
from lietorch import SE3
from util.poses import to_se3_vec
from dense_pose_sparse_refresh import refresh_dense_poses
from dense_pose_lazy_refresh import install as lazy

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from dense_pose_refresh_repair import install as repair


def reference():
    workspace = Path(__file__).resolve().parents[4]
    index = json.loads((workspace / 'results/campaigns/gain_attribution/online_dense_training/source_v12/index.json').read_text())
    path = workspace / index['/home/intern/VIGS-SLAM-online-view-training/vigs/gs_backend.py']
    cls = next(n for n in ast.parse(path.read_text()).body if isinstance(n, ast.ClassDef) and n.name == 'GSBackEnd')
    node = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == '_refresh_causal_dense_poses')
    ns = dict(torch=torch, np=np, SE3=SE3, to_se3_vec=to_se3_vec, Log=lambda *a: None)
    exec(compile(ast.Module(body=[node], type_ignores=[]), str(path), 'exec'), ns)
    return ns['_refresh_causal_dense_poses']


class View:
    def __init__(self, uid):
        self.uid, self.sensor_type = uid, 'rgb_dense'
        self.R, self.T = torch.eye(3, device='cuda'), torch.tensor([-uid / 1000, 0., 0.], device='cuda')

    def update_RT(self, r, t):
        self.R, self.T = r.clone(), t.clone()


def build(sparse, wrapped=True):
    m = SimpleNamespace(viewpoints={i: View(i) for i in range(0, 1000, 10)},
        polish_viewpoints={i: View(i) for i in (5, 155, 365, 1005)},
        _dense_pose_optimizers={}, _scaled_viewpoint_cache={}, _training_viewpoint_cache={},
        online_view_trainer=object())
    m._refresh_causal_dense_poses = MethodType(refresh_dense_poses if sparse else reference(), m)
    m._training_viewpoint = lambda v: (v.R.clone(), v.T.clone())
    if wrapped:
        times = np.linspace(0, 11, 1101)
        imu = np.zeros((len(times), 7)); imu[:, 0] = times; imu[:, 3] = .1 * np.sin(times)
        shaper = SimpleNamespace(imu=imu, timestamps={i: i / 100 for i in range(1101)},
            r_cb=np.eye(3), r_bc=np.eye(3), left_residual_by_uid={i: None for i in m.polish_viewpoints})
        repair(m, shaper)
        lazy(m)
    return m


def main():
    old, new = build(False), build(True)
    errors = []
    for event, selected in enumerate((5, 155, 365, 5, 1005)):
        for m in (old, new):
            for uid, view in m.viewpoints.items():
                tangent = torch.tensor([[uid * .0001, event * .001, 0., .02, uid * .0001, 0.]], device='cuda')
                pose = SE3.exp(tangent).matrix()[0]
                view.update_RT(pose[:3, :3], pose[:3, 3])
            if event == 2:
                del m.viewpoints[150]
            m._refresh_causal_dense_poses()
        expected = old._training_viewpoint(old.polish_viewpoints[selected])
        actual = new._training_viewpoint(new.polish_viewpoints[selected])
        error = max(float((x - y).abs().max()) for x, y in zip(expected, actual))
        assert error < 1e-6, (event, error)
        assert set(old.viewpoints) == set(new.viewpoints)
        for uid in old.viewpoints:
            assert torch.equal(old.viewpoints[uid].R, new.viewpoints[uid].R)
            assert torch.equal(old.viewpoints[uid].T, new.viewpoints[uid].T)
        again = new._training_viewpoint(new.polish_viewpoints[selected])
        assert all(torch.equal(x, y) for x, y in zip(actual, again))
        errors.append(error)
    # Preserve the original right-multiplied residual path outside IMU repair.
    a, b = build(False, False), build(True, False)
    for m in (a, b):
        residual = torch.eye(4); residual[0, 3] = .02
        m.polish_viewpoints[5].causal_pose_residual = residual
        assert m._refresh_causal_dense_poses() == 3
    assert torch.equal(a.polish_viewpoints[5].T, b.polish_viewpoints[5].T)
    timing = {}
    for name, m in [('all_keyframes', a), ('needed_keyframes', b)]:
        m.polish_viewpoints = {155: m.polish_viewpoints[155]}
        for _ in range(3): m._refresh_causal_dense_poses()
        torch.cuda.synchronize(); start = time.perf_counter()
        for _ in range(30): m._refresh_causal_dense_poses()
        torch.cuda.synchronize(); timing[name] = (time.perf_counter() - start) / 30
    print(json.dumps({'pose_equivalence_passed': True, 'max_abs_errors': errors,
        'changed_bracket_and_unbracketed_checked': True, 'right_residual_checked': True,
        'keyframes_preserved': True, 'lazy_audit': new._lazy_dense_refresh_audit,
        'sparse_audit': new._sparse_dense_refresh_audit,
        'seconds_per_single_dense_refresh_100_keyframes': timing, 'quality_claim': False}, indent=2))


if __name__ == '__main__':
    main()
