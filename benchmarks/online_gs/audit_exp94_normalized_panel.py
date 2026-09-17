#!/usr/bin/env python3
"""Read-only completion audit for the source-locked exp94 B-track panel."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


WORKSPACE = Path(__file__).resolve().parents[2]
ROOT = WORKSPACE / "results/experiments/exp94_normalized_metric_v2_fixed_eval"
INVENTORY = (
    WORKSPACE
    / "context/experiments/benchmark_custom/r4_all_scenes_fixed_work_20260915/provenance.json"
)


def read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def audit_pair(dataset: str, scene: str) -> tuple[dict | None, list[str]]:
    root = ROOT / dataset / scene
    result_path = root / "pair_result.json"
    if not result_path.exists():
        return None, []
    result = read(result_path)
    gate = read(root / "quality_gate.json")
    verifier = read(root / "pair_verification.json")
    candidate = root / "normalized_variance_s0"
    vanilla = root / "native_vanilla_render_matched_s0"
    evals = {
        arm: read(path / "evaluation_consistency.json")
        for arm, path in (("normalized", candidate), ("vanilla", vanilla))
    }
    runtime = {
        arm: read(path / "mapping_replay_runtime.json")
        for arm, path in (("normalized", candidate), ("vanilla", vanilla))
    }
    evaluations = {
        arm: read(path / "psnr/strict_fixed_manifest/final_result.json")
        for arm, path in (("normalized", candidate), ("vanilla", vanilla))
    }
    fixed = {
        arm: evaluation["predeclared_fixed_manifest_posthoc"]["mean_psnr"]
        for arm, evaluation in evaluations.items()
    }
    errors = []
    if (result["dataset"], result["scene"]) != (dataset, scene):
        errors.append("pair identity")
    if gate["stop"] or not all(gate["checks"].values()):
        errors.append("R4 drop or structural gate")
    if gate["r4_drop_db"] > 0.5:
        errors.append("predeclared R4 drop >0.5 dB")
    if not verifier["valid"] or not all(
        check["passed"] for check in verifier["checks"].values()
    ):
        errors.append("render-match fairness")
    if not result["fairness_pass"] or not result["double_evaluation_pass"]:
        errors.append("pair result validation flags")
    for arm in ("normalized", "vanilla"):
        report = evals[arm]
        if not report["pass"] or not all(report["checks"].values()):
            errors.append(f"{arm} double evaluation")
        if abs(report["fixed_psnr_first"] - fixed[arm]) > 1e-9:
            errors.append(f"{arm} consistency/held-out PSNR")
        if abs(result[f"{arm}_psnr"] - fixed[arm]) > 1e-9:
            errors.append(f"{arm} pair/held-out PSNR")
        if result[f"{arm}_renders"] != runtime[arm]["rasterized_view_updates"]:
            errors.append(f"{arm} physical render count")
        if result[f"{arm}_adam"] != runtime[arm]["optimizer_steps_completed"]:
            errors.append(f"{arm} Adam step count")
        if (
            result[f"{arm}_gaussians"] != runtime[arm]["gaussians"]
            or result[f"{arm}_gaussians"] != evaluations[arm]["gaussians"]
        ):
            errors.append(f"{arm} Gaussian count")
        if runtime[arm]["post_eos_optimizer_updates"] != 0:
            errors.append(f"{arm} nonzero tail")
        if (
            runtime[arm]["heldout_mapping_overlap_count"] != 0
            or runtime[arm]["heldout_gaussian_origin_overlap_count"] != 0
        ):
            errors.append(f"{arm} held-out mapping overlap")
    if result["normalized_renders"] != result["vanilla_renders"]:
        errors.append("unequal physical renders")
    if abs(
        result["delta_psnr"]
        - (result["normalized_psnr"] - result["vanilla_psnr"])
    ) > 1e-9:
        errors.append("delta PSNR arithmetic")
    return result, errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-complete", action="store_true")
    args = parser.parse_args()
    inventory = read(INVENTORY)["pairs"]
    if len(inventory) != 17 or len({(x["dataset"], x["scene"]) for x in inventory}) != 17:
        raise RuntimeError("predeclared inventory is not 17 unique scenes")
    lock = read(ROOT / "source_lock.json")["sha256"]
    hash_errors = [
        path for path, digest in lock.items()
        if not Path(path).exists()
        or hashlib.sha256(Path(path).read_bytes()).hexdigest() != digest
    ]
    results = []
    pending = []
    failures = []
    for row in inventory:
        dataset, scene = row["dataset"], row["scene"]
        result, errors = audit_pair(dataset, scene)
        if result is None:
            pending.append(f"{dataset}/{scene}")
            continue
        results.append(result)
        failures.extend(f"{dataset}/{scene}: {error}" for error in errors)
    mean = sum(x["delta_psnr"] for x in results) / len(results) if results else None
    wins = sum(x["delta_psnr"] > 0 for x in results)
    print(f"complete={len(results)}/17 pending={len(pending)} wins={wins}")
    print(f"partial_mean_delta={mean:+.6f} dB" if mean is not None else "partial_mean_delta=N/A")
    if pending:
        print("pending:", ", ".join(pending))
    if hash_errors:
        print("source_lock_mismatch:", ", ".join(hash_errors))
    if failures:
        print("failures:", "; ".join(failures))
    if len(results) == 17:
        minimum = mean >= 0.5 and wins >= 9 and not failures and not hash_errors
        stretch = wins == 17 and mean >= 1.2609 and not failures and not hash_errors
        print(f"minimum_acceptance={'PASS' if minimum else 'FAIL'}")
        print(f"historical_R4_stretch={'PASS' if stretch else 'FAIL'}")
    return int(bool(failures or hash_errors or (args.require_complete and pending)))


if __name__ == "__main__":
    raise SystemExit(main())
