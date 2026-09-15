#!/usr/bin/env python3

from __future__ import annotations

import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).with_name(
    "verify_exp78b_stage6r_r4_native_keyframe.py"
)
SPEC = importlib.util.spec_from_file_location("r4_verifier", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
VERIFIER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VERIFIER)


EMPTY_SHA = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"


def ledger_row(
    index: int,
    phase: str,
    pool: list[int],
    uniform: list[int],
    selected: list[int],
    ercb: bool,
) -> dict:
    return {
        "audit_index": index,
        "map_generation": 0,
        "mapping_iteration": index,
        "frontier_iteration_count_before": index + 10,
        "controller_phase": phase,
        "pool_uids": pool,
        "requested_slots": len(uniform),
        "uniform_shadow_uids": uniform,
        "selected_uids": selected,
        "ercb_active": ercb,
        "optimizer_committed": True,
        "selector_before": {} if ercb else None,
        "selector_after": {} if ercb else None,
    }


def runtime(candidate: bool) -> dict:
    frontier = ledger_row(
        0, "frontier", [1, 2, 3, 4, 5, 6], [1, 2, 3, 4, 5, 6],
        [1, 2, 3, 4, 5, 6], False,
    )
    balanced1 = ledger_row(
        1, "balanced", list(range(1, 9)), [1, 2, 3, 4, 5, 6],
        [1, 2, 3, 4, 5, 6], candidate,
    )
    balanced2 = ledger_row(
        2, "balanced", list(range(1, 9)), [1, 2, 3, 4, 5, 6],
        [7, 8, 1, 2, 3, 4] if candidate else [1, 2, 3, 4, 5, 6],
        candidate,
    )
    ledger = [frontier, balanced1, balanced2]
    queue = None
    if candidate:
        queue = {
            "protocol": "native_global_keyframe_ercb_v1",
            "service_shortfall_block_size": 8,
            "service_shortfall_relative_floor_ratio": 0.75,
            "service_shortfall_max_bonus": 1.5,
            "service_shortfall_global_epoch_no_repeat": 1,
            "service_shortfall_pending_draw_attempts": 0,
            "duplicate_within_batch_violations": 0,
            "cancelled_proposals": 0,
            "future_frames_used": False,
            "dataset_name_used": False,
            "stream_horizon_used": False,
        }
    selected_unique = len(
        {
            uid
            for row in ledger
            if row["controller_phase"] in {"balanced", "replay"}
            for uid in row["selected_uids"]
        }
    )
    return {
        "protocol": VERIFIER.EXPECTED_PROTOCOL,
        "work_contract": VERIFIER.EXPECTED_WORK,
        "comparison_contract": (
            VERIFIER.CANDIDATE_CONTRACT
            if candidate
            else VERIFIER.CONTROL_CONTRACT
        ),
        "stage6r_keyframe_appearance_replay": True,
        "stage6r_native_global_keyframe_selection_audit": True,
        "stage6r_native_global_keyframe_ercb": candidate,
        "c1_c2_global_residue_integration": True,
        "service_shortfall_ercb_requested": True,
        "compute_paced_dense_admission": True,
        "compute_paced_dense_token_cost": 1,
        "fixed_event_dense_opportunities_per_packet": 1,
        "mapping_profile": "dense_rr_imu",
        "observation_topology_gate_requested": True,
        "dense_replay_gradient_scope": "appearance",
        "include_keyframes_in_replay": False,
        "custom_commit": "paper-commit",
        "runtime_provenance": {
            "active_source_sha256": {"a": "b"},
            "custom_git_diff_sha256": EMPTY_SHA,
        },
        "archive_manifest_sha256": "archive",
        "config_sha256": "config",
        "effective_config_sha256": "effective",
        "dense_selected_frame_uids": [20],
        "mapped_frame_uids": [10, 11, 20],
        "events": [
            {
                "event_id": 1,
                "kind": "keyframe_update",
                "filtered_frame_uids": [],
                "completed": True,
                "frontier_optimizer_steps_completed": 10,
                "frontier_rasterized_view_updates": 100,
                "fixed_dense_optimizer_steps_completed": 1,
                "fixed_dense_rasterized_view_updates": 1,
                "fixed_keyframe_optimizer_steps_completed": 1,
                "fixed_keyframe_rasterized_view_updates": 1,
                "optimizer_steps_completed": 12,
                "rasterized_view_updates": 102,
            }
        ],
        "optimizer_steps_completed": 12,
        "main_gaussian_optimizer_steps_completed": 12,
        "auxiliary_adam_steps_completed": 0,
        "rasterized_view_updates": 102,
        "fixed_event_dense_opportunity_ledger": [{"event_id": 1}],
        "dense_admission_ledger": [{"uid": 20}],
        "dense_registered_frame_uids": [20],
        "mapping_replay_summary": {"draws": 1},
        "fixed_event_keyframe_opportunity_ledger": [{"event_id": 1}],
        "stage6r_keyframe_replay_summary": {"draws": 1},
        "stage6r_keyframe_selected_frame_uids": [10],
        "stage6r_source_lr_steps": {"dense": 1, "keyframe": 1},
        "effective_replay_source_scope_optimizer_steps": {
            "dense:appearance": 1,
            "keyframe:appearance": 1,
        },
        "stage6r_native_global_keyframe_selection_ledger": ledger,
        "stage6r_native_global_keyframe_selection_summary": {
            "audit_enabled": True,
            "ercb_after_balanced": candidate,
            "balanced_or_replay_entries": 2,
            "ercb_active_entries": 2 if candidate else 0,
            "balanced_selected_unique_views": selected_unique,
            "final_queue": queue,
        },
        "post_eos_optimizer_updates": 0,
        "heldout_mapping_overlap_count": 0,
        "heldout_gaussian_origin_overlap_count": 0,
        "final_ba_performed": False,
        "final_color_refinement_performed": False,
        "terminal_pruning_performed": False,
        "gaussians": 1000,
    }


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value) + "\n", encoding="utf-8")


def write_eval(run: Path, psnr_offset: float) -> None:
    rows = []
    for index in range(8):
        rows.append(
            {
                "frame_index": index,
                "uid": f"{index}.png",
                "predeclared_fixed_manifest_split": True,
                "psnr": 20.0 + index * 0.1 + psnr_offset,
            }
        )
    write_json(
        run / "psnr" / "strict_fixed_manifest" / "final_result.json",
        {
            "per_view": rows,
            "predeclared_fixed_manifest_posthoc": {
                "view_count": 8,
                "mapping_disjoint": True,
                "mean_psnr": sum(row["psnr"] for row in rows) / len(rows),
                "mean_ssim": 0.8 + psnr_offset * 0.01,
                "mean_lpips": 0.2 - psnr_offset * 0.01,
            },
        },
    )


class R4VerifierTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.control = self.root / "control"
        self.candidate = self.root / "candidate"
        write_json(self.control / "mapping_replay_runtime.json", runtime(False))
        write_json(self.candidate / "mapping_replay_runtime.json", runtime(True))

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_valid_structural_pair(self) -> None:
        report = VERIFIER.build_report(
            self.control, self.candidate, structural_only=True
        )
        self.assertTrue(report["valid"])
        self.assertEqual(
            report["structural_result"]["candidate_unique_minus_control"], 2
        )

    def test_repeat_before_residue_exhaustion_fails_closed(self) -> None:
        broken = runtime(True)
        broken["stage6r_native_global_keyframe_selection_ledger"][2][
            "selected_uids"
        ] = [1, 7, 8, 2, 3, 4]
        write_json(self.candidate / "mapping_replay_runtime.json", broken)
        report = VERIFIER.build_report(
            self.control, self.candidate, structural_only=True
        )
        self.assertFalse(report["valid"])
        self.assertFalse(
            report["checks"]["transactional_global_residue_ercb"]["passed"]
        )

    def test_positive_quality_and_coverage_promotes(self) -> None:
        write_eval(self.control, 0.0)
        write_eval(self.candidate, 0.1)
        render_report = self.root / "render.json"
        write_json(
            render_report,
            {"valid": True, "result": {"vanilla": {"psnr": 19.0}}},
        )
        report = VERIFIER.build_report(
            self.control,
            self.candidate,
            structural_only=False,
            render_match_report=render_report,
        )
        self.assertTrue(report["valid"])
        self.assertTrue(report["decision"]["promote_r4_into_full"])


if __name__ == "__main__":
    unittest.main()
