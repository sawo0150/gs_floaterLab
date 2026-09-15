#!/usr/bin/env python3

from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest


MODULE_PATH = Path(__file__).with_name("verify_exp78b_d1_render_match.py")
SPEC = importlib.util.spec_from_file_location("render_match_verifier", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
VERIFIER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VERIFIER)


class TrackingKeyframeIdentityTest(unittest.TestCase):
    def test_pruned_origin_does_not_erase_an_input_keyframe(self) -> None:
        d1 = {
            "mapped_frame_uids": [10, 11, 20, 21],
            "dense_selected_frame_uids": [20, 21],
            "gaussian_origin_uids": [10],
            "tracking_mapped_unique_views": 2,
        }
        vanilla = {"mapped_frame_uids": [10, 11]}

        valid, detail = VERIFIER.tracking_keyframe_identity(d1, vanilla)

        self.assertTrue(valid)
        self.assertEqual(
            detail["identity_source"],
            "legacy_mapped_union_minus_dense_selected",
        )
        self.assertEqual(detail["tracking_uids_without_surviving_origin"], [11])

    def test_legacy_decomposition_fails_closed_on_dense_tracking_overlap(self) -> None:
        d1 = {
            "mapped_frame_uids": [10, 11, 20],
            "dense_selected_frame_uids": [11, 20],
            "gaussian_origin_uids": [10, 11],
            "tracking_mapped_unique_views": 2,
        }
        vanilla = {"mapped_frame_uids": [10, 11]}

        valid, detail = VERIFIER.tracking_keyframe_identity(d1, vanilla)

        self.assertFalse(valid)
        self.assertEqual(detail["ambiguous_dense_tracking_overlap"], [11])

    def test_direct_tracking_list_takes_precedence(self) -> None:
        d1 = {
            "tracking_mapped_frame_uids": [10, 11],
            "mapped_frame_uids": [10, 11, 20],
            "dense_selected_frame_uids": [11, 20],
            "gaussian_origin_uids": [10],
            "tracking_mapped_unique_views": 2,
        }
        vanilla = {"mapped_frame_uids": [10, 11]}

        valid, detail = VERIFIER.tracking_keyframe_identity(d1, vanilla)

        self.assertTrue(valid)
        self.assertEqual(
            detail["identity_source"], "direct_tracking_mapped_frame_uids"
        )

    def test_direct_tracking_mismatch_fails(self) -> None:
        d1 = {
            "tracking_mapped_frame_uids": [10, 12],
            "mapped_frame_uids": [10, 12, 20],
            "dense_selected_frame_uids": [20],
            "gaussian_origin_uids": [10, 12],
            "tracking_mapped_unique_views": 2,
        }
        vanilla = {"mapped_frame_uids": [10, 11]}

        valid, detail = VERIFIER.tracking_keyframe_identity(d1, vanilla)

        self.assertFalse(valid)
        self.assertEqual(detail["missing_from_d1"], [11])
        self.assertEqual(detail["extra_in_d1"], [12])

    def test_declared_tracking_count_is_an_independent_guard(self) -> None:
        d1 = {
            "mapped_frame_uids": [10, 11, 20],
            "dense_selected_frame_uids": [20],
            "gaussian_origin_uids": [10, 11],
            "tracking_mapped_unique_views": 3,
        }
        vanilla = {"mapped_frame_uids": [10, 11]}

        valid, detail = VERIFIER.tracking_keyframe_identity(d1, vanilla)

        self.assertFalse(valid)
        self.assertFalse(detail["declared_tracking_count_valid"])


if __name__ == "__main__":
    unittest.main()
