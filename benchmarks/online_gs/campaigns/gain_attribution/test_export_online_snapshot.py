from pathlib import Path
import tempfile
import unittest
import numpy as np
from plyfile import PlyData
from scipy.spatial.transform import Rotation
import torch
from export_online_snapshot import export
from snapshot_camera_alignment import transform_evaluation_cameras


class ExportTests(unittest.TestCase):
    def test_active_sh_and_coordinate_state_survive_export(self):
        c2w = np.repeat(np.eye(4)[None], 4, axis=0)
        c2w[:, :3, 3] = [[0, 0, 0], [1, 0, 0], [0, 1, 0], [1, 1, 1]]
        ref = np.concatenate([np.arange(4)[:, None], c2w[:, :3, 3],
                              Rotation.from_matrix(c2w[:, :3, :3]).as_quat()], axis=1)
        alignment = dict(scale=2., rotation=Rotation.from_rotvec([.1, .2, .3]).as_matrix(),
                         translation=np.array([1., 2., 3.]))
        current = transform_evaluation_cameras(np.linalg.inv(c2w), alignment)
        state = dict(parameters=dict(xyz=torch.arange(6.).reshape(2, 3),
            features_dc=torch.arange(6.).reshape(2, 1, 3),
            features_rest=torch.arange(90.).reshape(2, 15, 3),
            opacity=torch.ones(2, 1), scaling=torch.zeros(2, 3), rotation=torch.ones(2, 4)),
            keyframe_w2c={i: torch.tensor(pose) for i, pose in enumerate(current)},
            active_sh_degree=1, training_uids=[0, 1, 2, 3], metadata={'state_seconds': 12.})
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory) / 'export'
            report = export(state, ref, out)
            vertices = PlyData.read(out / '3dgs_before_final.ply')['vertex']
            self.assertIn('f_rest_8', vertices.data.dtype.names)
            self.assertNotIn('f_rest_9', vertices.data.dtype.names)
            np.testing.assert_array_equal(vertices['x'], [0, 3])
            np.testing.assert_array_equal(vertices['f_rest_1'], [3, 48])
            trajectory = np.loadtxt(out / 'traj_full_beforeBA.txt')
            np.testing.assert_allclose(trajectory[:, 1:4], np.linalg.inv(current)[:, :3, 3], atol=1e-10)
            self.assertLess(report['center_rmse'], 1e-12)
            self.assertFalse(report['alignment_quality_accepted'])
            with self.assertRaises(FileExistsError):
                export(state, ref, out)


if __name__ == '__main__':
    unittest.main()
