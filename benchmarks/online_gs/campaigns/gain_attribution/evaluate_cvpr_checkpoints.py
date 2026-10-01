#!/usr/bin/env python3
"""Evaluate real immutable checkpoints on a predeclared held-out subset.

The subset is uniform in the existing fixed cohort, never selected by scores.
Only post-run evaluation uses the final trajectory. Pose-gauge residuals remain
visible and unacceptable alignments cannot supply convergence/peak claims.
"""
import argparse
import gc
import importlib.util
import hashlib
import json
from pathlib import Path
import sys
import traceback

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
import run_online_dense_training as trial
from collect_cvpr_assets import ROOT, OUT, read, write, sha


def load_evaluator():
    spec = importlib.util.spec_from_file_location("cvpr_original_ply_evaluator", trial.BASE.EVALUATOR)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def evaluate(directory, inventory, subset, save_indices):
    import numpy as np
    import torch
    from PIL import Image
    module = load_evaluator()
    selected = {int(r["frame_index"]) for r in read(subset)["views"]}
    old_tqdm = module.tqdm
    module.tqdm = lambda rows, **kw: old_tqdm([i for i in rows if i in selected], **kw)
    original_render = module.render
    images = directory / "images"
    images.mkdir(exist_ok=True)
    def render(camera, *args, **kwargs):
        result = original_render(camera, *args, **kwargs)
        uid = int(camera.uid)
        if uid in save_indices:
            for name, tensor in [("render", result["render"]), ("gt", camera.original_image)]:
                array = torch.clamp(tensor.detach(), 0, 1).cpu().permute(1, 2, 0).numpy()
                Image.fromarray(np.rint(array * 255).astype(np.uint8)).save(images / f"{uid:06d}_{name}.png")
        return result
    module.render = render
    sys.argv = [str(trial.BASE.EVALUATOR), "--run-dir", str(directory), "--image-dir", inventory["image_dir"],
                "--calib", inventory["calibration"], "--manifest", str(subset), "--rgb-file-in-nanoseconds",
                "--mapped-uids-json", str(directory / "mapped_uids.json"), "--result-subdir", "curve_fixed_subset",
                "--evaluation-state", "immutable_checkpoint_postrun_evaluation_only"]
    if inventory["dataset"] != "aria":
        sys.argv += ["--undistort"]
    assert module.main() == 0
    result = read(directory / "psnr/curve_fixed_subset/final_result.json")
    q = result["predeclared_fixed_manifest_posthoc"]
    assert q["mapping_disjoint"] and q["view_count"] == len(selected)
    del module
    gc.collect()
    torch.cuda.empty_cache()
    return q


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--run", type=Path, required=True)
    p.add_argument("--dataset", required=True)
    p.add_argument("--scene", required=True)
    p.add_argument("--max-views", type=int, default=64)
    p.add_argument("--check-only", action="store_true")
    a = p.parse_args()
    import numpy as np
    inventory = next(r for r in read(OUT / "scene_inventory.json") if (r["dataset"], r["scene"]) == (a.dataset, a.scene))
    full = read(Path(inventory["fixed_manifest"]))
    indices = np.linspace(0, len(full["views"])-1, min(a.max_views, len(full["views"])), dtype=int)
    views = [full["views"][int(i)] for i in indices]
    directory = a.run / "curve_evaluation"
    directory.mkdir(exist_ok=True)
    subset = directory / "fixed_subset_manifest.json"
    declaration = {**full, "eval_count": len(views), "views": views,
                   "eval_uids_sha256": hashlib.sha256(json.dumps(sorted(v["uid"] for v in views)).encode()).hexdigest(),
                   "eval_uids_hash_encoding": "UTF-8 json.dumps(sorted(UID strings)); default separators",
                   "parent_manifest": inventory["fixed_manifest"], "parent_manifest_sha256": sha(Path(inventory["fixed_manifest"])),
                   "curve_subset_rule": "uniform indices in predeclared fixed heldout cohort; chosen without reading quality scores"}
    if subset.exists():
        previous = read(subset)
        if previous != declaration:
            # Only a former CPU dry-run declaration may be corrected in place.
            # A completed evaluation keeps its original immutable split.
            assert not (directory / "summary.json").exists()
            assert previous["views"] == declaration["views"]
            write(subset.with_name("fixed_subset_manifest_before_hash_correction.json"), previous)
            write(subset, declaration)
    else:
        write(subset, declaration)
    checkpoints = read(a.run / "snapshots/manifest.json")["snapshots"] if (a.run / "snapshots/manifest.json").exists() else []
    if a.check_only:
        print(json.dumps({"run": str(a.run), "subset_views": len(views), "checkpoint_count": len(checkpoints), "map_exists": (a.run / "3dgs_before_final.ply").exists(), "trajectory_exists": (a.run / "traj_full_beforeBA.txt").exists()}))
        return
    from selected_mapping_check import gpu_idle
    gpu_idle()
    import torch
    from export_online_snapshot import export
    rows = read(directory / "summary.json") if (directory / "summary.json").exists() else []
    trajectory = np.loadtxt(a.run / "traj_full_beforeBA.txt")
    saved_indices = {int(views[int(i)]["frame_index"]) for i in np.linspace(0, len(views)-1, min(8, len(views)), dtype=int)}
    for c in checkpoints + [{"file": "final", "final": True}]:
        name = Path(c["file"]).stem
        if any(r["name"] == name for r in rows):
            continue
        output = directory / name
        row = {"name": name, "status": "failed", "output": str(output), "checkpoint": c}
        try:
            if c.get("final"):
                output.mkdir(exist_ok=False)
                for f in ["3dgs_before_final.ply", "traj_full_beforeBA.txt", "traj_kf_beforeBA.txt", "mapped_uids.json"]:
                    (output / f).symlink_to((a.run / f).resolve())
                accepted = True
                save_indices = {int(v["frame_index"]) for v in views}
            else:
                state = torch.load(a.run / "snapshots" / c["file"], map_location="cpu", weights_only=True)
                alignment = export(state, trajectory, output)
                ratio = alignment["center_rmse"] / max(alignment["reference_center_rms_radius"], 1e-8)
                accepted = ratio <= .03 and alignment["orientation_max_error_degrees"] <= 5
                row["alignment"] = alignment
                row["relative_center_rmse"] = ratio
                save_indices = saved_indices
                del state
            q = evaluate(output, inventory, subset, save_indices)
            row.update(status="evaluated", quality=q, alignment_accepted=accepted,
                       usable_for_convergence_claim=accepted, evaluator_inputs_used_by_mapper=False)
        except Exception:
            row["error"] = traceback.format_exc()
        rows.append(row)
        write(directory / "summary.json", rows)
        print("CHECKPOINT", a.scene, name, row["status"], row.get("quality", {}).get("mean_psnr"), flush=True)
    write(directory / "provenance.json", {"script": str(Path(__file__)), "script_sha256": sha(Path(__file__)),
        "original_evaluator": str(trial.BASE.EVALUATOR), "original_evaluator_sha256": sha(trial.BASE.EVALUATOR),
        "subset_manifest": str(subset), "subset_sha256": sha(subset), "image_selection_uses_scores": False,
        "postrun_evaluation_only": True, "pose_alignment_gate": {"relative_center_rmse_max": .03, "orientation_max_degrees": 5},
        "changes_to_original_evaluator": "read-only wrappers filter its tqdm indices to the fixed subset and save actual prediction/GT tensors"})


if __name__ == "__main__":
    sys.path.insert(0, "/home/intern/VIGS-SLAM-custom/scripts/selected_mapping")
    main()
