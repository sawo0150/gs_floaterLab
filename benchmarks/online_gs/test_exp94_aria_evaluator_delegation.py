#!/usr/bin/env python3
"""Prevent Aria's evaluator adapter from disabling RPNG/UTMM undistortion."""

from pathlib import Path
import unittest

import run_exp78b_stage6rx4_cross_sequence as base
import run_exp78b_r4_all_scenes as all_scenes
import run_exp78b_r4_aria as aria


class AriaEvaluatorDelegationTest(unittest.TestCase):
    def test_mixed_inventory_preserves_non_aria_evaluation_contract(self):
        all_scenes.install_extension()
        aria.install_extension()
        for dataset, scene in (("rpng", "table_01"), ("utmm", "square-1")):
            with self.subTest(dataset=dataset, scene=scene):
                output = Path("/tmp/exp94-eval-command-only")
                expected = aria.ORIGINAL_EVALUATION_COMMAND(output, dataset, scene)
                actual = base.evaluation_command(output, dataset, scene)
                self.assertEqual(actual, expected)
                self.assertIn("--undistort", actual)

    def test_aria_keeps_its_own_calibration_contract(self):
        all_scenes.install_extension()
        aria.install_extension()
        command = base.evaluation_command(Path("/tmp/exp94-eval-command-only"), "aria", "aria1253")
        self.assertNotIn("--undistort", command)
        self.assertIn("aria1253.txt", command[command.index("--calib") + 1])


if __name__ == "__main__":
    unittest.main()
