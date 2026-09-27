import ast
import sys
from pathlib import Path
import unittest
from types import SimpleNamespace, MethodType
import numpy as np
import torch
from scipy.spatial.transform import Rotation

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from dense_pose_refresh_repair import bracket, residuals, install


class View:
    def __init__(self):
        self.R = torch.tensor(Rotation.from_rotvec([.1, 0, 0]).as_matrix(), dtype=torch.float64)
        self.T = torch.tensor([.2, .3, .4], dtype=torch.float64)
        self.causal_admission_left_keyframe = 0
        self.causal_admission_right_keyframe = 20

    def update_RT(self, R, T):
        self.R, self.T = R.clone(), T.clone()


class RepairTest(unittest.TestCase):
    def setUp(self):
        t = np.linspace(0, 5, 501)
        imu = np.zeros((len(t), 7)); imu[:, 0] = t; imu[:, 3] = .2*t*t
        self.shaper = SimpleNamespace(imu=imu, timestamps={i: i/10 for i in range(51)},
            r_cb=np.eye(3), r_bc=np.eye(3), left_residual_by_uid={5: None, 15: None, 30: None})
        self.mapper = SimpleNamespace(viewpoints={10: None, 20: None, 40: None},
            polish_viewpoints={i: View() for i in (5, 15, 30)})
        def original():
            n = 0
            for uid, view in self.mapper.polish_viewpoints.items():
                if bracket(sorted(self.mapper.viewpoints), uid) is not None:
                    view.update_RT(torch.eye(3, dtype=torch.float64), torch.zeros(3, dtype=torch.float64))
                    n += 1
            return n
        self.mapper._refresh_causal_dense_poses = original
        self.original_refresh = original
        install(self.mapper, self.shaper)

    def install_legacy_refresh(self):
        # Execute the actual legacy function without importing its CUDA backend.
        path = Path(__file__).resolve().parents[2] / 'exp78b_replay_gsslam_mapping.py'
        tree = ast.parse(path.read_text())
        node = next(n for n in tree.body if isinstance(n, ast.FunctionDef)
                    and n.name == 'install_dense_imu_pose_refresh')
        namespace = {'torch': torch, 'MethodType': MethodType,
                     'GSBackEnd': object, 'CausalImuDensePoseShaper': object}
        exec(compile(ast.Module(body=[node], type_ignores=[]), str(path), 'exec'), namespace)
        for uid in self.shaper.left_residual_by_uid:
            left, right = (0, 20) if uid < 20 else (20, 40)
            value = torch.eye(4, dtype=torch.float64)
            value[:3, :3] = torch.as_tensor(residuals(self.shaper, left, right, [uid])[uid])
            self.shaper.left_residual_by_uid[uid] = value
        self.mapper._refresh_causal_dense_poses = self.original_refresh
        namespace['install_dense_imu_pose_refresh'](self.mapper, self.shaper)

    def test_actual_legacy_code_compounds_unbracketed_rotation(self):
        self.install_legacy_refresh()
        self.mapper._refresh_causal_dense_poses()
        before = self.mapper.polish_viewpoints[5].R.clone()
        self.mapper._refresh_causal_dense_poses()
        self.assertFalse(torch.allclose(before, self.mapper.polish_viewpoints[5].R))

    def test_actual_legacy_code_uses_stale_bracket(self):
        self.install_legacy_refresh()
        self.mapper._refresh_causal_dense_poses()
        old = self.mapper.polish_viewpoints[15].R.clone()
        expected = torch.as_tensor(residuals(self.shaper, 10, 20, [15])[15])
        self.assertFalse(torch.allclose(old, expected))
        self.mapper._refresh_causal_dense_poses = self.original_refresh
        install(self.mapper, self.shaper)
        self.mapper._refresh_causal_dense_poses()
        self.assertTrue(torch.allclose(self.mapper.polish_viewpoints[15].R, expected))

    def test_repeated_refresh_is_idempotent_including_unbracketed(self):
        self.mapper._refresh_causal_dense_poses()
        before = {i: (v.R.clone(), v.T.clone()) for i,v in self.mapper.polish_viewpoints.items()}
        for _ in range(8): self.mapper._refresh_causal_dense_poses()
        for i,v in self.mapper.polish_viewpoints.items():
            self.assertTrue(torch.equal(before[i][0],v.R)); self.assertTrue(torch.equal(before[i][1],v.T))

    def test_changed_bracket_recomputes_residual_without_rewriting_admission(self):
        self.mapper._refresh_causal_dense_poses()
        before = self.mapper.polish_viewpoints[15].R.clone()
        del self.mapper.viewpoints[20]
        self.mapper._refresh_causal_dense_poses()
        view = self.mapper.polish_viewpoints[15]
        self.assertFalse(torch.allclose(view.R,before))
        self.assertTrue(np.allclose(view.R.numpy(),residuals(self.shaper,10,40,[15])[15]))
        self.assertEqual((view.causal_admission_left_keyframe,view.causal_admission_right_keyframe),(0,20))

    def test_future_imu_does_not_change_residual(self):
        before = residuals(self.shaper,10,20,[15])[15]
        self.shaper.imu[self.shaper.imu[:,0]>2,1:4] = 1e8
        self.assertTrue(np.array_equal(before,residuals(self.shaper,10,20,[15])[15]))

    def test_no_future_bracket_extrapolation(self):
        self.assertIsNone(bracket([10,20],30)); self.assertIsNone(bracket([10,20],5))
        self.assertIsNone(bracket([10,20],20))
        self.assertEqual(bracket([10,20],15),(10,20))


if __name__ == '__main__': unittest.main()
