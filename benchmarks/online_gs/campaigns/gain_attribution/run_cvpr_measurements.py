#!/usr/bin/env python3
"""Source-preserving CVPR measurement panel on the predeclared scene cohort.

The existing selected mapper and official comparison harness are executed with
their normal argv. Process-local adapters add scene paths, legacy IMU metadata,
and read-only snapshots; they do not change mapping losses or training policy.
"""
import argparse
import atexit
import hashlib
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys
import time
import traceback

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
import run_online_dense_training as trial
from collect_cvpr_assets import ROOT, RESULTS, MAIN, OUT, read, write, sha

GEOM = MAIN / "scripts/selected_mapping/geometry_merge"
FIXED_RASTER = RESULTS / "geometry_main_validation/raster_fixed"
INVENTORY = OUT / "scene_inventory.json"
CARD = ROOT / "context/experiments/campaigns/06_gain_attribution/cvpr_assets/README.md"


def scene_row(dataset, scene):
    return next(r for r in read(INVENTORY) if (r["dataset"], r["scene"]) == (dataset, scene))


def install_paths():
    old_paths = trial.BASE.sequence_paths
    def paths(dataset, scene):
        r = scene_row(dataset, scene)
        if not r["ready"]:
            raise FileNotFoundError(f"Input inventory not ready: {dataset}/{scene}")
        return {"archive": Path(r["archive"]), "fixed_manifest": Path(r["fixed_manifest"]),
                "custom_config": ROOT / f"benchmarks/online_gs/config/vigs_final_v7_{dataset}.yaml",
                "vanilla_config": Path(r["input_config"]), "image_dir": Path(r["image_dir"]),
                "calibration": Path(r["calibration"])}
    trial.BASE.sequence_paths = paths
    def evaluate(output, dataset, scene):
        x = paths(dataset, scene)
        cmd = [str(trial.BASE.PYTHON_ENV / "bin/python"), str(trial.BASE.EVALUATOR),
               "--run-dir", str(output), "--image-dir", str(x["image_dir"]),
               "--calib", str(x["calibration"]), "--manifest", str(x["fixed_manifest"]),
               "--rgb-file-in-nanoseconds", "--mapped-uids-json", str(output / "mapped_uids.json"),
               "--result-subdir", "strict_fixed_manifest"]
        return cmd + (["--undistort"] if dataset != "aria" else [])
    trial.BASE.evaluation_command = evaluate
    return paths


def environment(arm):
    custom = arm != "vanilla"
    env = trial.BASE.mapping_environment(custom)
    parts = [str(HERE), str(HERE.parents[1])]
    lock = read(MAIN / "scripts/selected_mapping/source_lock.json")
    if custom:
        ext = Path(lock["extensions"])
        parts = [str(FIXED_RASTER), str(ext / "vigs_backends"), str(ext / "lietorch_backends"),
                 str(MAIN / "vigs"), str(MAIN), str(MAIN / "scripts/selected_mapping"), str(GEOM)] + parts
        env.update(EXP78B_CUSTOM_ROOT=str(MAIN), FIXED40_KF_LOSS="d3" if arm == "d3" else "native",
                   FIXED40_DENSE_SCOPE="full", FR_WARP_BWD="1")
    # A CPU thread cap is common to both arms and prevents huge default pools.
    env.update(OMP_NUM_THREADS="4", MKL_NUM_THREADS="4", PYTHONUNBUFFERED="1")
    env["PYTHONPATH"] = ":".join(parts) + ":" + env.get("PYTHONPATH", "")
    return env


def install_legacy_imu_metadata():
    import exp78b_frozen_archive as frozen
    original = frozen.FrozenTrackerArchive.__init__
    def init(self, root):
        original(self, root)
        if "input_imu" not in self.manifest:
            r = next(r for r in read(INVENTORY) if Path(r["archive"]).resolve() == self.root)
            self.manifest["input_imu"] = r["imu"]
    frozen.FrozenTrackerArchive.__init__ = init


def install_snapshots(args):
    """Observe successful Gaussian Adam steps. No training inputs are changed."""
    import torch
    import gs_backend
    import render_work_audit
    # Import only the read-only utility from main, even for the official mapper.
    spec = __import__("importlib.util", fromlist=["spec_from_file_location"])
    module_spec = spec.spec_from_file_location("cvpr_readonly_snapshots", MAIN / "vigs/online_map_snapshots.py")
    module = spec.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    r = scene_row(args.dataset, args.scene)
    fractions = [.1, .25, .4, .55, .7, .85]
    targets = [int((r["input_frames"] - 1) * f) for f in fractions]
    state = {"mapper": None, "audit": None, "next": 0, "snapshots": [], "copy_seconds": 0., "optimizer_steps": 0}
    ctor = gs_backend.GSBackEnd.__init__
    def construct(self, *a, **kw):
        ctor(self, *a, **kw)
        state["mapper"] = self
    gs_backend.GSBackEnd.__init__ = construct
    audit_ctor = render_work_audit.RenderWorkAudit.__init__
    def audit_init(self, *a, **kw):
        audit_ctor(self, *a, **kw)
        state["audit"] = self
    render_work_audit.RenderWorkAudit.__init__ = audit_init
    def post_hook(optimizer, unused_args, unused_kw):
        mapper, audit = state["mapper"], state["audit"]
        if mapper is None or audit is None or optimizer is not mapper.gaussians.optimizer:
            return
        state["optimizer_steps"] += 1
        uid = audit.context.get("arrival_uid", -1)
        n = state["next"]
        if n == len(targets) or uid < targets[n] or not mapper.initialized or not mapper.viewpoints:
            return
        start = time.monotonic()
        snapshot = module.capture(mapper)
        elapsed = time.monotonic() - start
        # One real state per observation, even if initialization skipped targets.
        state["next"] += 1
        while state["next"] < len(targets) and targets[state["next"]] <= uid:
            state["next"] += 1
        metadata = {"arrival_uid": uid, "training_renders": audit.training,
                    "optimizer_steps": state["optimizer_steps"], "gaussians": len(snapshot["parameters"]["xyz"]),
                    "copy_seconds": elapsed, "target_frame": targets[n], "target_fraction": fractions[n]}
        snapshot["metadata"] = metadata
        state["snapshots"].append(snapshot)
        state["copy_seconds"] += elapsed
    from torch.optim.optimizer import register_optimizer_step_post_hook
    handle = register_optimizer_step_post_hook(post_hook)
    def dump():
        if not args.output.exists():
            return
        directory = args.output / "snapshots"
        directory.mkdir(exist_ok=True)
        rows = []
        for i, snapshot in enumerate(state["snapshots"]):
            name = f"snapshot_{i:02d}.pt"
            torch.save(snapshot, directory / name)
            rows.append({"file": name, **snapshot["metadata"]})
        write(directory / "manifest.json", {"protocol": "cvpr_readonly_prefix_snapshots_v1", "copy_seconds": state["copy_seconds"], "schedule_controls_mapping_policy": False, "evaluator_inputs_used_by_mapper": False, "snapshots": rows})
        handle.remove()
    atexit.register(dump)


def worker(args):
    install_paths()
    install_legacy_imu_metadata()
    if args.stage == "setup":
        import capture_online_worker_setup as capture
        sys.argv = [capture.__file__, "--dataset", args.dataset, "--scene", args.scene, "--output", str(args.output)]
        return capture.main()
    if args.snapshots:
        install_snapshots(args)
    if args.arm == "vanilla":
        path = HERE / "run_kf15_vanilla.py"
        sys.argv = [str(path), "--dataset", args.dataset, "--scene", args.scene, "--reference", str(args.reference), "--output", str(args.output), "--renders-per-kf", str(args.budget), "--seed", "0"]
    else:
        import fixed40_geometry as geometry
        cfg = geometry.install()
        def dump_geometry():
            if args.output.exists():
                write(args.output / "geometry_runtime.json", {"config": cfg, "stats": geometry.STATS})
        atexit.register(dump_geometry)
        path = MAIN / "scripts/selected_mapping/run_kf15_render_worker.py"
        argv = read(MAIN / "configs/selected_mapping_fixed40.json")["worker_args"]
        argv[argv.index("--renders-per-kf") + 1] = str(args.budget)
        if args.selector:
            argv[argv.index("--selector") + 1] = args.selector
        if args.auxiliary_mode:
            argv += ["--auxiliary-mode", args.auxiliary_mode]
        sys.argv = [str(path), *argv, "--setup", str(args.setup), "--extensions", read(MAIN / "scripts/selected_mapping/source_lock.json")["extensions"], "--output", str(args.output)]
    runpy.run_path(str(path), run_name="__main__")


def run(cmd, log, arm):
    from selected_mapping_check import gpu_idle
    gpu_idle()
    log.parent.mkdir(parents=True, exist_ok=True)
    write(log.with_suffix(".command.json"), cmd)
    with log.open("x") as f:
        subprocess.run(cmd, env=environment(arm), stdout=f, stderr=subprocess.STDOUT, check=True)


def journal(row):
    msg = f"2026-10-01 CVPR {row['dataset']}/{row['scene']} {row['budget']}renders/KF {row['arm']}: status={row['status']}, PSNR={row.get('psnr')}; {row['output']}"
    with CARD.open("a") as f:
        f.write("\n- " + msg + "\n")
    for name, heading, link in [("context/STATUS.md", "## 최근 흐름 (최신순)\n", "experiments/campaigns/06_gain_attribution/cvpr_assets/README.md"), ("context/experiments/INDEX.md", "# Experiment Index\n", "campaigns/06_gain_attribution/cvpr_assets/README.md")]:
        p = ROOT / name
        s = p.read_text()
        assert heading in s
        p.write_text(s.replace(heading, heading + "\n- " + msg + f" → [card]({link})\n", 1))


def panel(args):
    install_paths()
    sys.path.insert(0, str(MAIN / "scripts/selected_mapping"))
    from selected_mapping_check import verify_files
    lock = read(MAIN / "scripts/selected_mapping/source_lock.json")
    verify_files(lock["sources"])
    verify_files(lock["extension_files"])
    args.output.mkdir(parents=True, exist_ok=True)
    selected = [r for r in read(INVENTORY) if not args.scenes or r["scene"] in args.scenes]
    py = str(trial.BASE.PYTHON_ENV / "bin/python")
    rows = read(args.output / "summary.json") if (args.output / "summary.json").exists() else []
    source = {str(p): sha(p) for p in [*MAIN.glob("vigs/**/*.py"), *GEOM.glob("*.py"), Path(__file__).resolve()]}
    source_path = args.output / "source_lock.json"
    if source_path.exists() and read(source_path) != source:
        raise RuntimeError("Source changed from this panel's original lock")
    write(source_path, source)
    write(args.output / "protocol.json", {"custom_head": subprocess.check_output(["git", "-C", str(MAIN), "rev-parse", "HEAD"], text=True).strip(), "scenes": [r["scene"] for r in selected], "budgets": args.budgets, "arms": args.arms, "extra_proxy_render_budget": True, "equal_total_work_claim": False, "snapshots": args.snapshots, "seed": 0})
    for r in selected:
        d, s = r["dataset"], r["scene"]
        setup = args.output / "inputs" / d / s / "setup"
        if not r["ready"]:
            rows.append({"dataset": d, "scene": s, "budget": None, "arm": None, "status": "input_missing", "output": str(setup)})
            write(args.output / "summary.json", rows)
            continue
        for budget in args.budgets:
            for arm in args.arms:
                out = args.output / f"render{budget}" / d / s / arm
                if any(x.get("output") == str(out) for x in rows):
                    continue
                row = {"dataset": d, "scene": s, "budget": budget, "arm": arm, "output": str(out), "status": "failed"}
                print("START", d, s, budget, arm, flush=True)
                try:
                    if arm != "vanilla" and not (setup / "native_setup.pt").exists():
                        run([py, str(Path(__file__)), "--stage", "setup", "--dataset", d, "--scene", s, "--output", str(setup)], setup.parent / "capture.log", "native")
                    cmd = [py, str(Path(__file__)), "--stage", "worker", "--dataset", d, "--scene", s, "--budget", str(budget), "--arm", arm, "--setup", str(setup), "--output", str(out)]
                    if arm == "vanilla":
                        cmd += ["--reference", str(out.parent / "d3/render_result.json")]
                    if args.snapshots:
                        cmd += ["--snapshots"]
                    run(cmd, out.parent / f"{arm}.log", arm)
                    x = read(out / "render_result.json")
                    assert x["valid_execution"] and all(x["checks"].values()), x.get("error_traceback")
                    ev = trial.common.evaluation.panel.run_evaluation_twice(out, d, s, Path(r["fixed_manifest"]))
                    assert ev["pass"], ev
                    if arm == "vanilla":
                        ref = read(out.parent / "d3/render_result.json")
                        assert [(z["uid"], z["training_renders"]) for z in x["render_prefixes"]] == [(z["uid"], z["training_renders"]) for z in ref["render_prefixes"]]
                        for name in ["traj_full_beforeBA.txt", "traj_kf_beforeBA.txt"]:
                            assert sha(out / name) == sha(out.parent / "d3" / name)
                    assert all(sha(Path(p)) == h for p, h in source.items()), "Source changed during experiment"
                    row.update(status="passed", psnr=ev["fixed_psnr_first"], gaussians=x["gaussians"], training_renders=x["render_counts"]["training"], mapping_seconds=x["mapping_seconds"])
                except Exception:
                    row["error"] = traceback.format_exc()
                rows.append(row)
                write(args.output / "summary.json", rows)
                journal(row)
                print("DONE", d, s, budget, arm, row["status"], row.get("psnr"), flush=True)
    print("PANEL_FINISHED", flush=True)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--stage", choices=["panel", "setup", "worker"], default="panel")
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--dataset")
    p.add_argument("--scene")
    p.add_argument("--scenes", nargs="+")
    p.add_argument("--budgets", nargs="+", type=int, default=[15, 40])
    p.add_argument("--budget", type=int, default=15)
    p.add_argument("--arms", nargs="+", choices=["d3", "vanilla", "native"], default=["d3", "vanilla"])
    p.add_argument("--arm", choices=["d3", "vanilla", "native"], default="d3")
    p.add_argument("--setup", type=Path)
    p.add_argument("--reference", type=Path)
    p.add_argument("--selector", choices=["ervs", "rr"])
    p.add_argument("--auxiliary-mode", choices=["dense_rgb", "kf_rgb", "kf_native"])
    p.add_argument("--snapshots", action="store_true")
    a = p.parse_args()
    worker(a) if a.stage != "panel" else panel(a)


if __name__ == "__main__":
    main()
