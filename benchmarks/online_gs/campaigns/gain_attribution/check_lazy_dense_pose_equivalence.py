#!/usr/bin/env python3
"""Compare actual backend interpolation + IMU repair, eager versus deferred."""
import ast
import json
import sys
from pathlib import Path
from types import SimpleNamespace, MethodType
import numpy as np
import torch
from lietorch import SE3
from util.poses import to_se3_vec
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from dense_pose_refresh_repair import install as repair
from dense_pose_lazy_refresh import install as lazy


class View:
    def __init__(self, uid, tx=0.):
        self.uid = uid
        self.R = torch.eye(3, device='cuda')
        self.T = torch.tensor([tx, 0., 0.], device='cuda')
        self.sensor_type = 'rgb_dense'

    def update_RT(self, r, t):
        self.R, self.T = r.clone(), t.clone()


def build(deferred):
    path = Path('/home/intern/VIGS-SLAM-online-view-training/vigs/gs_backend.py')
    cls = next(n for n in ast.parse(path.read_text()).body
               if isinstance(n, ast.ClassDef) and n.name == 'GSBackEnd')
    node = next(n for n in cls.body if isinstance(n, ast.FunctionDef)
                and n.name == '_refresh_causal_dense_poses')
    ns = dict(torch=torch, np=np, SE3=SE3, to_se3_vec=to_se3_vec, Log=lambda *a: None)
    exec(compile(ast.Module(body=[node], type_ignores=[]), str(path), 'exec'), ns)
    m = SimpleNamespace(viewpoints={i: View(i, -i / 100) for i in (0, 20, 40)},
        polish_viewpoints={i: View(i) for i in (5, 15, 30)},
        _dense_pose_optimizers={}, _scaled_viewpoint_cache={},
        _training_viewpoint_cache={}, online_view_trainer=object())
    m._refresh_causal_dense_poses = MethodType(ns['_refresh_causal_dense_poses'], m)
    m._training_viewpoint = lambda v: (v.R.clone(), v.T.clone())
    time = np.linspace(0, 5, 501)
    imu = np.zeros((501, 7)); imu[:, 0] = time; imu[:, 3] = .2 * time ** 2
    shaper = SimpleNamespace(imu=imu, timestamps={i: i / 10 for i in range(51)},
        r_cb=np.eye(3), r_bc=np.eye(3), left_residual_by_uid={5: None, 15: None, 30: None})
    repair(m, shaper)
    if deferred:
        lazy(m)
    return m


def main():
    eager, deferred = build(False), build(True)
    errors = []
    for event, selected in enumerate((5, 15, 30, 5)):
        for m in (eager, deferred):
            for k, v in m.viewpoints.items():
                v.T[0] = -k * (1 + event * .2) / 100
            if event == 2:
                del m.viewpoints[20]
            m._refresh_causal_dense_poses()
        expected = eager._training_viewpoint(eager.polish_viewpoints[selected])
        actual = deferred._training_viewpoint(deferred.polish_viewpoints[selected])
        error = max(float((x - y).abs().max()) for x, y in zip(expected, actual))
        assert error < 1e-6, (event, error)
        assert len(deferred.polish_viewpoints) == 3
        again = deferred._training_viewpoint(deferred.polish_viewpoints[selected])
        assert all(torch.equal(x, y) for x, y in zip(actual, again))
        errors.append(error)
    assert eager._dense_pose_refresh_repair_audit['refreshed_views'] == 12
    assert deferred._dense_pose_refresh_repair_audit['refreshed_views'] == 4
    print(json.dumps({'pose_equivalence_passed': True, 'max_abs_errors': errors,
        'eager_view_refreshes': 12, 'deferred_view_refreshes': 4,
        'lazy_audit': deferred._lazy_dense_refresh_audit, 'quality_claim': False}, indent=2))


if __name__ == '__main__':
    main()
