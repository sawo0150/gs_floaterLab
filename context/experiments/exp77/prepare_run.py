"""Validate completed dataset and write commands; never start training here."""
import argparse
import json
import math
import shlex
import hashlib
import runpy
from pathlib import Path


def audit_dataset(source, arrivals, repo):
    """Read COLMAP metadata without importing CUDA/Scene or modifying input."""
    loader = runpy.run_path(str(repo / "scene/colmap_loader.py"))
    sparse = source / "sparse/0"
    binary = (sparse / "images.bin").is_file() and (sparse / "cameras.bin").is_file()
    suffix = "binary" if binary else "text"
    extension = "bin" if binary else "txt"
    extrinsics = loader[f"read_extrinsics_{suffix}"](str(sparse / f"images.{extension}"))
    intrinsics = loader[f"read_intrinsics_{suffix}"](str(sparse / f"cameras.{extension}"))
    names = sorted(image.name for image in extrinsics.values())
    if len(names) != len(set(names)) or len(names) < 2:
        raise ValueError("Need unique COLMAP image names and nonempty train/test splits")
    if any(camera.model not in ("PINHOLE", "SIMPLE_PINHOLE") for camera in intrinsics.values()):
        raise ValueError("Undistorted PINHOLE/SIMPLE_PINHOLE cameras required")
    from PIL import Image
    for image in extrinsics.values():
        if image.camera_id not in intrinsics:
            raise ValueError(f"Missing camera for {image.name}")
        path = source / "images" / image.name
        if Path(image.name).is_absolute() or ".." in Path(image.name).parts:
            raise ValueError("Image paths must stay inside images directory")
        with Image.open(path) as rgb:
            camera = intrinsics[image.camera_id]
            if rgb.size != (camera.width, camera.height):
                raise ValueError(f"Image/camera dimensions differ: {path}")
            rgb.verify()
    # Require prepared PLY; legacy Scene would otherwise create it in the input.
    from plyfile import PlyData
    import numpy as np
    ply = sparse / "points3D.ply"
    vertices = PlyData.read(str(ply))["vertex"].data
    if len(vertices) < 4 or not all(name in vertices.dtype.names for name in ("x", "y", "z", "red", "green", "blue")):
        raise ValueError("Prepared points3D.ply needs >=4 points with xyz/RGB")
    if any(not np.isfinite(vertices[name]).all() for name in ("x", "y", "z")):
        raise ValueError("Nonfinite initialization points")
    payload = json.loads(arrivals.read_text())
    mapping = payload.get("arrival_iteration_by_name", payload)
    train, test = [name for i, name in enumerate(names) if i % 8], names[::8]
    if set(mapping) - set(names) or set(train) - set(mapping):
        raise ValueError("Arrival image names differ from COLMAP names (extensions must match)")
    values = [mapping[name] for name in train]
    if any(type(v) is not int or v < 1 for v in values) or values != sorted(values):
        raise ValueError("Training arrivals must be positive integers in sorted image order")
    if values[0] != 1:
        raise ValueError("No training bootstrap at iteration 1 after held-out exclusion")
    total = max(values)
    if "total_iterations" in payload and payload["total_iterations"] != total:
        raise ValueError("total_iterations differs from last training arrival: tail forbidden")
    return {"train_names": train, "test_names": test, "total_updates": total,
            "schedule_sha256": hashlib.sha256(arrivals.read_bytes()).hexdigest(),
            "init_ply_sha256": hashlib.sha256(ply.read_bytes()).hexdigest(),
            "initial_points": len(vertices), "split": "sorted COLMAP names, index % 8 == 0 held out"}


def main():
    here = Path(__file__).resolve().parent
    root = here.parents[2]
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--arrivals", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--resolution", type=int, default=4)
    p.add_argument("--copy-complete", action="store_true", required=True)
    p.add_argument("--provenance", type=Path, required=True,
                   help="JSON with pose_source, init_source, init_uses_future_training_rgb=false; not a strict-SLAM certificate")
    args = p.parse_args()
    source, arrivals = args.source.resolve(), args.arrivals.resolve()
    if not (source / "images").is_dir() or not (source / "sparse" / "0").is_dir():
        p.error("Expected completed COLMAP images/ and sparse/0/; no automatic conversion")
    repo = root / ".codex-work/3dgs-custom-main"
    provenance = json.loads(args.provenance.read_text())
    if not provenance.get("pose_source") or not provenance.get("init_source") or provenance.get("init_uses_future_training_rgb") is not False:
        p.error("Describe pose/init origin and exclude future-training-RGB initialization")
    audit = audit_dataset(source, arrivals, repo)
    total = audit["total_updates"]
    milestones = sorted(set([max(1, total // 4), max(1, total // 2), total]))
    commands = []
    for arm in ("rr", "ercb", "packet"):
        out = args.output.resolve() / f"{arm}_s{args.seed}"
        if out.exists():
            p.error(f"Refusing existing run output: {out}")
        cmd = ["/home/wosasa/miniconda3/envs/3dgs/bin/python", str(here / "run_training.py"),
               "--repo", str(repo), "--arm", arm, "--", "-s", str(source), "-m", str(out),
               "--eval", "--disable_viewer", "--data_device", "cpu", "-r", str(args.resolution),
               "--iterations", str(total), "--position_lr_max_steps", str(total),
               "--densify_until_iter", "0", "--depth_l1_weight_init", "0", "--depth_l1_weight_final", "0",
               "--view_schedule", str(arrivals), "--view_scheduler",
               "causal_rr" if arm == "rr" else "relative_floor_interval_softmax_rr",
               "--scheduler_seed", str(args.seed), "--scheduler_beta", str(math.log(3)),
               "--scheduler_block_size", "8", "--fixed_topology_step_before_report",
               "--gaussian_metrics_log_interval", "0",
               "--test_iterations", *map(str, milestones), "--save_iterations", str(total)]
        commands.append({"arm": arm, "cwd": str(repo), "argv": cmd, "shell": shlex.join(cmd)})
    args.output.mkdir(parents=True, exist_ok=True)
    dest = args.output / f"commands_s{args.seed}.json"
    with dest.open("x") as stream:
        json.dump({"status": "PREPARED_NOT_RUN", "total_updates": total,
                   "audit": audit, "provenance": provenance, "source": str(source), "arrivals": str(arrivals),
                   "scope": "fixed-pose/init scheduler isolation; not strict online SLAM",
                   "commands": commands}, stream, indent=2)
    print(dest)


if __name__ == "__main__":
    main()
