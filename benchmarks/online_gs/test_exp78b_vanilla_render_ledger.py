#!/usr/bin/env python3

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest


TEST_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(TEST_DIR))

import run_exp78b_stage5_full_retention as runner

for component in reversed(
    runner.mapping_environment("vanilla")["PYTHONPATH"].split(":")
):
    if component:
        sys.path.insert(0, component)

import exp78b_replay_vanilla_mapping as vanilla


class FakeArchive:
    def __init__(self, root: Path):
        self.root = root


class VanillaRenderLedgerTest(unittest.TestCase):
    def write_case(
        self,
        root: Path,
        *,
        event_renders: int,
        event_steps: int,
    ) -> tuple[Path, FakeArchive]:
        archive = root / "archive"
        archive.mkdir()
        manifest = archive / "archive_manifest.json"
        manifest.write_text("{}\n", encoding="utf-8")
        manifest_hash = hashlib.sha256(manifest.read_bytes()).hexdigest()
        reference = root / "mapping_replay_runtime.json"
        reference.write_text(
            json.dumps(
                {
                    "archive_manifest_sha256": manifest_hash,
                    "post_eos_optimizer_updates": 0,
                    "heldout_mapping_overlap_count": 0,
                    "rasterized_view_updates": 120,
                    "optimizer_steps_completed": 8,
                    "events": [
                        {
                            "event_id": 10,
                            "kind": "keyframe_update",
                            "completed": True,
                            "rasterized_view_updates": event_renders,
                            "optimizer_steps_completed": event_steps,
                        }
                    ],
                    "mapping_replay_summary": {
                        "steps": 1,
                        "draw_count": 1,
                    },
                }
            ),
            encoding="utf-8",
        )
        return reference, FakeArchive(archive)

    def test_fixed_event_inclusive_ledger_does_not_double_count_dense(self):
        with tempfile.TemporaryDirectory() as temporary:
            reference, archive = self.write_case(
                Path(temporary), event_renders=120, event_steps=8
            )
            ledger = vanilla.build_d1_render_ledger(reference, archive)
        self.assertTrue(ledger["event_ledger_includes_dense_replay"])
        self.assertEqual(ledger["vanilla_native_render_target"], 120)
        self.assertEqual(sum(ledger["event_additional_native_render_credit"].values()), 0)

    def test_legacy_exclusive_ledger_still_adds_dense_render(self):
        with tempfile.TemporaryDirectory() as temporary:
            reference, archive = self.write_case(
                Path(temporary), event_renders=119, event_steps=7
            )
            ledger = vanilla.build_d1_render_ledger(reference, archive)
        self.assertFalse(ledger["event_ledger_includes_dense_replay"])
        self.assertEqual(ledger["vanilla_native_render_target"], 120)
        self.assertEqual(sum(ledger["event_additional_native_render_credit"].values()), 1)


if __name__ == "__main__":
    unittest.main()
