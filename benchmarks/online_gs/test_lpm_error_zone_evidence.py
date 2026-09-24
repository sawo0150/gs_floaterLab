from __future__ import annotations

import sys
from pathlib import Path
import unittest

import torch
import torch.nn.functional as F


HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from lpm_error_zone_evidence import (  # noqa: E402
    LpmErrorZoneEvidenceProbe,
    lpm_error_zone_map,
)


def downloaded_author_reference(
    image: torch.Tensor,
    gt_image: torch.Tensor,
) -> torch.Tensor:
    """Literal LPM get_errormap(diff), isolated from LightGlue imports."""

    image_adjust = image / (torch.mean(image) + 0.01)
    gt_adjust = gt_image / (torch.mean(gt_image) + 0.01)
    error_map = torch.sum(torch.abs(image_adjust - gt_adjust), dim=0)
    threshold = torch.quantile(error_map, 0.4)
    error_mask = error_map > threshold
    kernel_size = (16, 16)
    stride = (16, 16)
    padding = (
        (image.shape[1] + stride[0] - 1) // stride[0] * stride[0]
        - image.shape[1],
        (image.shape[2] + stride[1] - 1) // stride[1] * stride[1]
        - image.shape[2],
    )
    error_mask = F.pad(
        error_mask,
        (0, padding[1], 0, padding[0]),
        mode="constant",
        value=0,
    )
    patches = error_mask.unfold(0, 16, 16).unfold(1, 16, 16)
    patch_sums = patches.sum(dim=(2, 3))
    significant_patches = patch_sums > (16 * 16 * 0.85)
    output = significant_patches.repeat_interleave(
        16, dim=0
    ).repeat_interleave(16, dim=1)
    return output[: image.shape[1], : image.shape[2]].float()


class LpmErrorZoneEvidenceTest(unittest.TestCase):
    def test_matches_downloaded_author_operator_non_multiple_shape(self):
        generator = torch.Generator().manual_seed(104729)
        image = torch.rand((3, 35, 51), generator=generator)
        gt = torch.rand((3, 35, 51), generator=generator)
        expected = downloaded_author_reference(image, gt)
        actual = lpm_error_zone_map(image, gt)
        self.assertTrue(torch.equal(actual, expected))

    def test_rejects_mismatched_shape(self):
        with self.assertRaisesRegex(ValueError, "shape mismatch"):
            lpm_error_zone_map(
                torch.zeros((3, 16, 16)),
                torch.zeros((3, 16, 17)),
            )

    def test_probe_tracks_repeats_without_work_or_mutation(self):
        probe = LpmErrorZoneEvidenceProbe()
        probe.bind_generation(2)
        gt = torch.zeros((3, 32, 32))
        image = gt.clone()
        image[:, :16, :16] = 1.0
        probe.observe(7, image, gt)
        probe.observe(7, image * 0.9, gt)
        probe.observe(8, gt, gt)
        summary = probe.summary()
        self.assertEqual(summary["calls"], 3)
        self.assertEqual(summary["unique_generation_views"], 2)
        self.assertEqual(summary["repeat_calls"], 1)
        self.assertEqual(summary["views_observed_at_least_twice"], 1)
        self.assertEqual(summary["extra_renders"], 0)
        self.assertEqual(summary["extra_adam_steps"], 0)
        self.assertEqual(summary["mutation_rows"], 0)
        self.assertFalse(summary["future_frames_used"])


if __name__ == "__main__":
    unittest.main()
