#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path
import sys
import unittest


TEST_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(TEST_DIR))

import run_exp78b_stage6rx4_cross_sequence as runner


class Stage6RX4RunnerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path("/tmp/stage6rx4-synthetic")

    def test_exact_confirmation_cohort_and_sentinel_order_are_frozen(self):
        self.assertEqual(len(runner.SEQUENCES), 11)
        self.assertNotIn(("rpng", "table_01"), runner.SEQUENCES)
        self.assertNotIn(("rpng", "table_02"), runner.SEQUENCES)
        self.assertEqual(
            runner.SENTINELS,
            (("utmm", "fast-straight"), ("rpng", "table_07")),
        )

    def test_candidate_has_complete_r4_full_flags(self):
        command = runner.mapping_command(
            "candidate", "utmm", "fast-straight", self.root
        )
        for flag in (
            "--compute-paced-dense-admission",
            "--c1-c2-global-residue-integration",
            "--service-shortfall-ercb",
            "--stage6r-keyframe-appearance-replay",
            "--stage6r-native-global-keyframe-selection-audit",
            "--stage6r-native-global-keyframe-ercb",
            "--observation-topology-gate",
        ):
            self.assertIn(flag, command)
        token = command.index("--compute-paced-dense-token-cost")
        self.assertEqual(command[token + 1], "1")

    def test_vanilla_is_render_matched_to_same_sequence_candidate(self):
        command = runner.mapping_command(
            "vanilla", "rpng", "table_07", self.root
        )
        reference = command[command.index("--reference-service-runtime") + 1]
        self.assertEqual(
            Path(reference),
            runner.run_paths(self.root, "rpng", "table_07")["candidate"]
            / "mapping_replay_runtime.json",
        )
        self.assertIn("--mapping-after-metric-init", command)

    def test_candidate_structure_precedes_quality_in_dry_run_payload(self):
        output = runner.run_paths(
            self.root, "utmm", "fast-straight"
        )["candidate"]
        command = runner.structure_command(
            output,
            runner.run_paths(self.root, "utmm", "fast-straight")["structure"],
        )
        self.assertIn(str(runner.STRUCTURE_VERIFIER), command)
        self.assertIn("--run", command)

    def test_entries_cover_only_the_frozen_cohort(self):
        entries = runner.cohort_entries(self.root)
        self.assertEqual(
            {(row["dataset"], row["sequence"]) for row in entries},
            set(runner.SEQUENCES),
        )
        self.assertTrue(
            all("stage6rx4" in row["candidate_run"] for row in entries)
        )

    def test_repaired_report_is_additive_and_preferred(self):
        paths = runner.run_paths(self.root, "rpng", "table_07")
        paths["render"].parent.mkdir(parents=True, exist_ok=True)
        paths["render"].unlink(missing_ok=True)
        paths["render_repaired"].unlink(missing_ok=True)
        paths["render"].write_text("{}\n", encoding="utf-8")
        self.assertEqual(runner.active_render_report(paths), paths["render"])
        paths["render_repaired"].write_text("{}\n", encoding="utf-8")
        self.assertEqual(
            runner.active_render_report(paths), paths["render_repaired"]
        )

    def test_source_neutral_reverification_is_fail_closed(self):
        tracking_only_failure = {
            "valid": False,
            "checks": {
                "same_tracking_kf_uids": {"passed": False},
                "same_frozen_archive": {"passed": True},
            },
        }
        valid_legacy = {
            "valid": True,
            "checks": {"same_frozen_archive": {"passed": True}},
        }
        unrelated_failure = {
            "valid": False,
            "checks": {"same_frozen_archive": {"passed": False}},
        }
        self.assertTrue(
            runner._eligible_for_source_neutral_reverification(
                tracking_only_failure
            )
        )
        self.assertTrue(
            runner._eligible_for_source_neutral_reverification(valid_legacy)
        )
        self.assertFalse(
            runner._eligible_for_source_neutral_reverification(
                unrelated_failure
            )
        )

    def test_custom_environment_uses_paper_source(self):
        environment = runner.mapping_environment(True)
        self.assertEqual(environment["EXP78B_CUSTOM_ROOT"], str(runner.PAPER_ROOT))
        self.assertIn(str(runner.PAPER_ROOT), environment["PYTHONPATH"].split(":"))

    def test_archive_reader_is_hash_pinned_and_git_critical(self):
        self.assertIn(runner.ARCHIVE_READER, runner.EXPECTED_HASHES)
        self.assertEqual(
            runner.sha256(runner.ARCHIVE_READER),
            runner.EXPECTED_HASHES[runner.ARCHIVE_READER],
        )


if __name__ == "__main__":
    unittest.main()
