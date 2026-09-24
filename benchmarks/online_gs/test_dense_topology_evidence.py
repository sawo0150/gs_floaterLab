import pathlib
import sys
import unittest

import torch


sys.path.insert(0, str(pathlib.Path(__file__).parent))
from dense_topology_evidence import DenseTopologyEvidenceProbe


class _Gaussians:
    def __init__(self, count):
        self._xyz = torch.zeros((count, 3))
        self.point_ids = torch.arange(100, 100 + count, dtype=torch.int64)

    @property
    def get_xyz(self):
        return self._xyz


class DenseTopologyEvidenceProbeTest(unittest.TestCase):
    def test_records_gradient_mass_and_persistence_without_mutation(self):
        gaussians = _Gaussians(6)
        probe = DenseTopologyEvidenceProbe()
        first = torch.tensor(
            [[[0.0]], [[1.0]], [[2.0]], [[3.0]], [[0.0]], [[4.0]]]
        )
        second = torch.tensor(
            [[[0.0]], [[1.0]], [[2.0]], [[0.0]], [[0.0]], [[5.0]]]
        )
        probe.observe(gaussians, 10, first)
        probe.observe(gaussians, 11, second)
        summary = probe.summary(gaussians.point_ids)

        self.assertEqual(summary["opportunities"], 2)
        self.assertEqual(summary["unique_dense_uids"], 2)
        self.assertEqual(summary["extra_renders"], 0)
        self.assertEqual(summary["mutation_rows"], 0)
        self.assertEqual(summary["records"][0]["positive_gradient_rows"], 4)
        self.assertEqual(
            summary["persistent_nominations"]["256"][
                "nominated_at_least_2"
            ],
            3,
        )

    def test_rejects_row_mismatch(self):
        probe = DenseTopologyEvidenceProbe()
        with self.assertRaises(ValueError):
            probe.observe(_Gaussians(3), 1, torch.ones((2, 1, 1)))


if __name__ == "__main__":
    unittest.main()
