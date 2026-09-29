import unittest
import torch
from protected_opacity_prune import old_low_opacity_mask


class MaskTest(unittest.TestCase):
    def test_bootstrap_protects_everything(self):
        mask = old_low_opacity_mask(torch.arange(20), torch.zeros(20), [0, 10], 10, .7)
        self.assertFalse(mask.any())

    def test_latest_ten_births_survive_even_zero_opacity(self):
        ids = torch.arange(110)
        mask = old_low_opacity_mask(ids, torch.zeros(110), list(range(0, 110, 10)), 10, .7)
        self.assertEqual(ids[mask].tolist(), list(range(10)))

    def test_old_high_opacity_survives(self):
        ids = torch.tensor([0, 1, 2, 20])
        opacity = torch.tensor([.69, .7, .95, .01])
        mask = old_low_opacity_mask(ids, opacity, list(range(0, 110, 10)), 10, .7)
        self.assertEqual(ids[mask].tolist(), [0])

    def test_sparse_ids_after_prior_prune(self):
        ids = torch.tensor([0, 12, 39, 40, 90, 130])
        mask = old_low_opacity_mask(ids, torch.zeros(6), list(range(30, 140, 10)), 10, .7)
        self.assertEqual(ids[mask].tolist(), [0, 12, 39])

    def test_new_generation_uses_its_own_birth_history(self):
        ids = torch.tensor([500, 501, 510])
        mask = old_low_opacity_mask(ids, torch.zeros(3), [500, 510], 10, .7)
        self.assertFalse(mask.any())


if __name__ == '__main__':
    unittest.main()
