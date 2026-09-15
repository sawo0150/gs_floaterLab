#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path
import sys
import unittest


sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_exp78b_stage6_cross_sequence as runner


class Stage6RunnerTest(unittest.TestCase):
    def setUp(self):
        self.root = Path("/tmp/stage6-runner-test")

    def test_complete_benchmark_and_validation_partition(self):
        self.assertEqual(len(runner.SEQUENCES), 16)
        self.assertEqual(
            sum(spec[0] == "validation" for spec in runner.SEQUENCES.values()),
            12,
        )
        self.assertEqual(
            sum(spec[0] == "development" for spec in runner.SEQUENCES.values()),
            4,
        )

    def test_full_enables_c1_and_global_residue_c2(self):
        command = runner.mapping_command(
            "full", "full", "rpng", "table_02", self.root
        )
        self.assertIn("--compute-paced-dense-admission", command)
        self.assertIn("--c1-c2-global-residue-integration", command)
        self.assertIn("--service-shortfall-ercb", command)
        self.assertNotIn("--c2-global-residue-isolation", command)

    def test_c2_pair_disables_c1_and_changes_only_selector_flag(self):
        rr = runner.mapping_command("c2", "rr", "utmm", "ego-centric-1", self.root)
        c2 = runner.mapping_command("c2", "c2", "utmm", "ego-centric-1", self.root)
        self.assertIn("--c2-global-residue-isolation", rr)
        self.assertNotIn("--compute-paced-dense-admission", rr)
        self.assertNotIn("--service-shortfall-ercb", rr)
        c2_without_selector = c2[:-1]
        output_index = rr.index("--output") + 1
        c2_without_selector[output_index] = rr[output_index]
        self.assertEqual(c2_without_selector, rr)
        self.assertEqual(c2[-1], "--service-shortfall-ercb")

    def test_vanilla_uses_full_runtime_as_render_reference(self):
        command = runner.mapping_command(
            "full", "vanilla", "rpng", "table_02", self.root
        )
        reference = command[command.index("--reference-service-runtime") + 1]
        expected = (
            runner.run_paths(self.root, "rpng", "table_02")["full"]
            / "mapping_replay_runtime.json"
        )
        self.assertEqual(Path(reference), expected)

    def test_dataset_specific_paths(self):
        rpng = runner.sequence_paths("rpng", "table_02")
        utmm = runner.sequence_paths("utmm", "ego-centric-1")
        self.assertEqual(rpng["custom_config"].name, "vigs_final_v7_rpng.yaml")
        self.assertEqual(utmm["custom_config"].name, "vigs_final_v7_utmm.yaml")
        self.assertEqual(rpng["calibration"].name, "rpngar.txt")
        self.assertEqual(utmm["calibration"].name, "intrinsics_ours.txt")
        self.assertEqual(rpng["image_dir"].name, "rgb")
        self.assertEqual(utmm["image_dir"].name, "rgb_timestamp")

    def test_validation_entries_exclude_development_rows(self):
        for panel in ("full", "c2"):
            entries = runner.validation_entries(self.root, panel)
            self.assertEqual(len(entries), 12)
            self.assertNotIn(
                ("rpng", "table_01"),
                {(entry["dataset"], entry["sequence"]) for entry in entries},
            )

    def test_invalid_panel_arm_pair_fails(self):
        with self.assertRaises(ValueError):
            runner.mapping_command(
                "c2", "vanilla", "rpng", "table_02", self.root
            )


if __name__ == "__main__":
    unittest.main()
