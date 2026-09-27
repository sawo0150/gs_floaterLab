import unittest
import numpy as np
from scipy.spatial.transform import Rotation
from snapshot_camera_alignment import align_camera_worlds, transform_evaluation_cameras


class AlignmentTests(unittest.TestCase):
    def cameras(self):
        c2w = np.repeat(np.eye(4)[None], 5, axis=0)
        c2w[:, :3, 3] = [[0, 0, 0], [1, 0, 0], [0, 2, 0], [1, 2, 1], [-1, 1, 2]]
        c2w[:, :3, :3] = Rotation.from_rotvec(np.arange(15).reshape(5, 3) * .01).as_matrix()
        return np.linalg.inv(c2w)

    def test_known_scale_rotation_translation_recovers_camera_poses(self):
        reference = self.cameras()
        expected = dict(scale=2.3, rotation=Rotation.from_rotvec([.2, -.3, .1]).as_matrix(),
                        translation=np.array([1., 2., -3.]))
        current = transform_evaluation_cameras(reference, expected)
        measured = align_camera_worlds(reference, current)
        self.assertAlmostEqual(measured['scale'], expected['scale'])
        np.testing.assert_allclose(measured['rotation'], expected['rotation'], atol=1e-12)
        np.testing.assert_allclose(measured['translation'], expected['translation'], atol=1e-12)
        np.testing.assert_allclose(transform_evaluation_cameras(reference, measured), current, atol=1e-12)
        self.assertLess(measured['center_rmse'], 1e-12)
        self.assertLess(measured['orientation_max_error_degrees'], 1e-5)

    def test_nonrigid_camera_changes_are_visible_in_residuals(self):
        reference = self.cameras(); current = reference.copy()
        current[0, 0, 3] += .2
        self.assertGreater(align_camera_worlds(reference, current)['center_rmse'], .01)
        current = reference.copy()
        current[0, :3, :3] = Rotation.from_rotvec([.2, 0, 0]).as_matrix()
        self.assertGreater(align_camera_worlds(reference, current)['orientation_max_error_degrees'], 1.)

    def test_degenerate_or_missing_pairs_are_not_silently_accepted(self):
        reference = self.cameras()
        with self.assertRaises(ValueError):
            align_camera_worlds(reference[:2], reference[:2])
        flat = np.repeat(np.eye(4)[None], 5, axis=0)
        flat[:, 0, 3] = np.arange(5)
        with self.assertRaises(ValueError):
            align_camera_worlds(flat, flat)


if __name__ == '__main__':
    unittest.main()
