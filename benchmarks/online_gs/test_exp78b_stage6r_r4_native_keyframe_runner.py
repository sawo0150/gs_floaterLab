#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path
import sys
import unittest


TEST_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(TEST_DIR))

import run_exp78b_stage6r_r4_native_keyframe as runner


class R4RunnerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path("/tmp/stage6r-r4-synthetic")

    def test_selector_pair_differs_only_by_candidate_flag(self) -> None:
        control_output = runner.paths_for(self.root)["control"]
        candidate_output = runner.paths_for(self.root)["candidate"]
        control = runner.mapping_command("control", control_output, self.root)
        candidate = runner.mapping_command("candidate", candidate_output, self.root)
        self.assertIn(
            "--stage6r-native-global-keyframe-selection-audit", control
        )
        self.assertNotIn("--stage6r-native-global-keyframe-ercb", control)
        self.assertIn("--stage6r-native-global-keyframe-ercb", candidate)
        normalized_control = [
            str(candidate_output) if value == str(control_output) else value
            for value in control
        ]
        normalized_candidate = [
            value
            for value in candidate
            if value != "--stage6r-native-global-keyframe-ercb"
        ]
        self.assertEqual(normalized_control, normalized_candidate)

    def test_pair_keeps_full_r3_dense_and_auxiliary_keyframe_flags(self) -> None:
        command = runner.mapping_command(
            "control", runner.paths_for(self.root)["control"], self.root
        )
        for flag in (
            "--compute-paced-dense-admission",
            "--c1-c2-global-residue-integration",
            "--service-shortfall-ercb",
            "--stage6r-keyframe-appearance-replay",
            "--observation-topology-gate",
        ):
            self.assertIn(flag, command)
        token_index = command.index("--compute-paced-dense-token-cost")
        self.assertEqual(command[token_index + 1], "1")

    def test_vanilla_is_render_matched_to_r4_candidate(self) -> None:
        output = runner.paths_for(self.root)["vanilla"]
        command = runner.mapping_command("vanilla", output, self.root)
        reference = command[command.index("--reference-service-runtime") + 1]
        self.assertEqual(
            Path(reference),
            runner.paths_for(self.root)["candidate"]
            / "mapping_replay_runtime.json",
        )
        self.assertIn("--mapping-after-metric-init", command)

    def test_custom_environment_uses_paper_source_and_compiled_extensions(self) -> None:
        environment = runner.mapping_environment("candidate")
        components = environment["PYTHONPATH"].split(":")
        self.assertIn(str(runner.PAPER_ROOT), components)
        self.assertIn(str(runner.BUILT_THIRDPARTY_ROOT), components)
        self.assertEqual(environment["EXP78B_CUSTOM_ROOT"], str(runner.PAPER_ROOT))


if __name__ == "__main__":
    unittest.main()
