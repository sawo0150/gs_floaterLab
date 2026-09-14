#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path
import sys
import unittest


TEST_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(TEST_DIR))

import run_exp78b_stage5_full_retention as runner


class Stage5RunnerTest(unittest.TestCase):
    def setUp(self):
        self.root = Path("/tmp/stage5-synthetic")

    def test_mapper_seed_changes_but_tracker_archive_stays_seed_zero(self):
        output = runner.paths_for(self.root, 2)["rr"]
        command = runner.mapping_command("rr", 2, output, self.root)
        self.assertEqual(command[command.index("--seed") + 1], "2")
        archive = command[command.index("--archive") + 1]
        self.assertTrue(archive.endswith("/rpng/table_01/seed0"))

    def test_c2_adds_only_service_shortfall_selector_to_custom_flags(self):
        rr_output = runner.paths_for(self.root, 1)["rr"]
        c2_output = runner.paths_for(self.root, 1)["c2"]
        rr = runner.mapping_command("rr", 1, rr_output, self.root)
        c2 = runner.mapping_command("c2", 1, c2_output, self.root)
        self.assertNotIn("--service-shortfall-ercb", rr)
        self.assertIn("--service-shortfall-ercb", c2)
        normalized_rr = [str(c2_output) if value == str(rr_output) else value for value in rr]
        normalized_c2 = [
            value for value in c2 if value != "--service-shortfall-ercb"
        ]
        self.assertEqual(normalized_rr, normalized_c2)

    def test_vanilla_references_same_seed_c2_runtime(self):
        output = runner.paths_for(self.root, 3)["vanilla"]
        command = runner.mapping_command("vanilla", 3, output, self.root)
        reference = command[command.index("--reference-service-runtime") + 1]
        self.assertEqual(
            Path(reference),
            runner.paths_for(self.root, 3)["c2"]
            / "mapping_replay_runtime.json",
        )

    def test_only_predeclared_mapper_seeds_are_exposed(self):
        self.assertEqual(runner.EXPECTED_SEEDS, (1, 2, 3))
        self.assertNotIn(0, runner.EXPECTED_SEEDS)

    def test_custom_environment_exposes_compiled_backend_root(self):
        components = runner.mapping_environment("rr")["PYTHONPATH"].split(":")
        self.assertIn(str(runner.BUILT_THIRDPARTY_ROOT), components)


if __name__ == "__main__":
    unittest.main()
