#!/usr/bin/env python3
"""Generalize existing live FIFO probes through explicit AST-only adapters.

Production and historical measurement files remain untouched. Both systems use
the official dataset Tracking configuration. Sensor arrivals, bounded waiting
FIFO, full training history, and zero optimizer tail retain the original probe.
"""
import argparse
import ast
import inspect
import json
from pathlib import Path
import subprocess
import sys
import traceback

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
import run_online_dense_training as trial
import run_cvpr_measurements as fixed
from collect_cvpr_assets import ROOT, RESULTS, MAIN, OUT, read, write, sha


def env(arm):
    import run_fifo_live_comparison as legacy
    e = legacy.environment(arm)
    e.update(OMP_NUM_THREADS="4", MKL_NUM_THREADS="4", VIGS_PIPELINE_TELEMETRY="1")
    return e


def adapted_main(legacy, args):
    source = inspect.getsource(legacy.main)
    tree = ast.parse(source)
    edits = []
    class Adapter(ast.NodeTransformer):
        def visit_Assign(self, node):
            if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                name = node.targets[0].id
                if name == "result" and isinstance(node.value, ast.Dict) and any(
                        isinstance(key, ast.Constant) and key.value == "tracked_frames" for key in node.value.keys):
                    node.value.keys.append(ast.Constant("stream_start_monotonic_time"))
                    node.value.values.append(ast.Name(id="started", ctx=ast.Load()))
                    edits.append("observed_stream_origin")
                replacements = {"scene": repr(args.scene), "dataset": repr(args.dataset)}
                if args.arm == "ours":
                    replacements["setup_dir"] = repr(str(args.setup))
                else:
                    replacements["setup"] = repr(str(args.setup))
                if name in replacements:
                    edits.append(name)
                    value = replacements[name]
                    if name in {"setup_dir", "setup"}:
                        value = "Path(" + value + ")"
                    return ast.copy_location(ast.parse(name + "=" + value).body[0], node)
            if args.arm == "ours" and len(node.targets) == 1:
                target = node.targets[0]
                if isinstance(target, ast.Subscript) and isinstance(target.value, ast.Name) and target.value.id == "config" and isinstance(target.slice, ast.Constant) and target.slice.value == "IMU":
                    edits.append("shared_official_tracking")
                    return [node, ast.parse("config['Tracking'] = copy.deepcopy(sensor['Tracking'])").body[0]]
            return self.generic_visit(node)
    tree = ast.fix_missing_locations(Adapter().visit(tree))
    required = {"scene", "dataset", "setup_dir", "shared_official_tracking", "observed_stream_origin"} if args.arm == "ours" else {"scene", "dataset", "setup", "observed_stream_origin"}
    if set(edits) != required:
        raise RuntimeError("Legacy adapter anchors changed: " + repr(edits))
    scope = dict(vars(legacy))
    exec(compile(tree, "<cvpr-live-scene-and-shared-tracking-adapter>", "exec"), scope)
    return scope["main"], {"original": legacy.__file__, "original_sha256": sha(Path(legacy.__file__)), "edits": edits, "effective_main_ast_sha256": __import__("hashlib").sha256(ast.dump(tree).encode()).hexdigest()}


def snapshots(args):
    # Add an absolute timestamp for post-run wall-clock curves, without touching
    # the fixed-work runner that is source-locked by a currently running panel.
    tree = ast.parse(inspect.getsource(fixed.install_snapshots))
    changed = 0
    class Stamp(ast.NodeTransformer):
        def visit_Assign(self, node):
            nonlocal changed
            if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name) and node.targets[0].id == "metadata" and isinstance(node.value, ast.Dict):
                node.value.keys.append(ast.Constant("capture_monotonic_time"))
                node.value.values.append(ast.parse("time.monotonic()", mode="eval").body)
                changed += 1
            return self.generic_visit(node)
    tree = ast.fix_missing_locations(Stamp().visit(tree))
    assert changed == 1
    scope = dict(vars(fixed))
    exec(compile(tree, "<cvpr-live-readonly-snapshot-timestamp>", "exec"), scope)
    scope["install_snapshots"](args)


def worker(args):
    fixed.install_paths()
    fixed.install_legacy_imu_metadata()
    legacy = __import__("measure_fifo_live_" + args.arm)
    fn, provenance = adapted_main(legacy, args)
    write(args.output / "adapter_provenance.json", {**provenance, "adapter": str(Path(__file__).resolve()), "adapter_sha256": sha(Path(__file__).resolve()), "tracking_recipe": "shared_official_dataset_config"})
    if args.snapshots:
        snapshots(args)
    sys.argv = [legacy.__file__, "--worker", "--dataset", args.dataset, "--time-scale", str(args.scale), "--queue-size", "2", "--renders-per-kf", "40", "--output", str(args.output)]
    if args.arm == "ours":
        sys.argv += ["--frontend-iters", "official"]
    fn()


def panel(args):
    fixed.install_paths()
    sys.path.insert(0, str(MAIN / "scripts/selected_mapping"))
    from selected_mapping_check import gpu_idle, verify_files
    lock = read(MAIN / "scripts/selected_mapping/source_lock.json")
    verify_files(lock["sources"])
    verify_files(lock["extension_files"])
    args.output.mkdir(parents=True, exist_ok=True)
    rows = read(args.output / "summary.json") if (args.output / "summary.json").exists() else []
    inventory = [r for r in read(OUT / "scene_inventory.json") if not args.scenes or r["scene"] in args.scenes]
    write(args.output / "protocol.json", {"tracking_recipe": "shared_official_dataset_config", "time_scales": args.scales, "training_render_cap_per_mapper_kf": 40, "fifo_pending_capacity": 2, "retained_history": "full", "optimizer_tail": 0, "snapshots": args.snapshots, "candidate_scenes": [r["scene"] for r in inventory], "source_sha256": sha(Path(__file__))})
    py = str(trial.BASE.PYTHON_ENV / "bin/python")
    cwd = ROOT / "results/experiments/exp78/a_paper_reproduction/trt_profiles/official_readme_dynamic_rtx5090"
    for r in inventory:
        dataset, scene = r["dataset"], r["scene"]
        setup = RESULTS / f"cvpr_assets/fixed_work_v1/inputs/{dataset}/{scene}/setup"
        if scene == "aria301_12F":
            setup = RESULTS / f"cvpr_assets/fixed_work_12f_v1/inputs/{dataset}/{scene}/setup"
        for scale in args.scales:
            for arm in ["ours", "vanilla"]:
                out = args.output / ("scale" + format(scale, "g").replace(".", "p")) / dataset / scene / arm
                if any(x["output"] == str(out) for x in rows):
                    continue
                row = {"dataset": dataset, "scene": scene, "time_scale": scale, "arm": arm, "output": str(out), "budget": 40, "status": "failed"}
                print("LIVE_START", dataset, scene, scale, arm, flush=True)
                try:
                    if not r["ready"]:
                        raise FileNotFoundError("Missing raw/archive metadata")
                    if arm == "ours" and not (setup / "native_setup.json").exists():
                        fixed.run([py, str(Path(fixed.__file__)), "--stage", "setup", "--dataset", dataset, "--scene", scene, "--output", str(setup)], setup.parent / "live_capture.log", "native")
                    gpu_idle()
                    out.mkdir(parents=True, exist_ok=False)
                    cmd = [py, str(Path(__file__)), "--stage", "worker", "--dataset", dataset, "--scene", scene, "--scale", str(scale), "--arm", arm, "--setup", str(setup), "--output", str(out)]
                    if args.snapshots:
                        cmd += ["--snapshots"]
                    write(out / "command.json", cmd)
                    with (out / "run.log").open("x") as log:
                        subprocess.run(cmd, env=env(arm), cwd=cwd, stdout=log, stderr=subprocess.STDOUT, check=True)
                    x = read(out / "result.json")
                    assert not x["error"] and x["source_unchanged"] and x["zero_tail_observed"]
                    assert x["tracked_frames"] == x["input_frames"] and not x["worker"]["error"]
                    assert read(out / "export.json")["finite"]
                    ev = trial.common.evaluation.panel.run_evaluation_twice(out, dataset, scene, Path(r["fixed_manifest"]))
                    assert ev["pass"], ev
                    if arm == "vanilla" and (out.parent / "ours/effective_config.json").exists():
                        ours = read(out.parent / "ours/effective_config.json")["config"]["Tracking"]
                        vanilla = read(out / "effective_config.json")["config"]["Tracking"]
                        assert ours == vanilla, {"ours": ours, "vanilla": vanilla}
                        q = lambda p: [v["uid"] for v in read(p / "psnr/strict_fixed_manifest/final_result.json")["per_view"] if v["predeclared_fixed_manifest_split"]]
                        assert q(out) == q(out.parent / "ours")
                    row.update(status="passed", psnr=ev["fixed_psnr_first"], runtime=x, evaluation=ev)
                except Exception:
                    row["error"] = traceback.format_exc()
                rows.append(row)
                write(args.output / "summary.json", rows)
                fixed.journal({**row, "arm": f"live_{arm}_{scale:g}x"})
                print("LIVE_DONE", dataset, scene, scale, arm, row["status"], row.get("psnr"), flush=True)
    print("LIVE_PANEL_FINISHED", flush=True)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--stage", choices=["panel", "worker", "check"], default="panel")
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--dataset")
    p.add_argument("--scene")
    p.add_argument("--scenes", nargs="+")
    p.add_argument("--scales", nargs="+", type=float, default=[1, 1.5])
    p.add_argument("--scale", type=float, default=1)
    p.add_argument("--arm", choices=["ours", "vanilla"], default="ours")
    p.add_argument("--setup", type=Path)
    p.add_argument("--snapshots", action="store_true")
    a = p.parse_args()
    if a.stage == "check":
        legacy = __import__("measure_fifo_live_" + a.arm)
        _, provenance = adapted_main(legacy, a)
        print(json.dumps(provenance, indent=2))
        return
    worker(a) if a.stage == "worker" else panel(a)


if __name__ == "__main__":
    main()
