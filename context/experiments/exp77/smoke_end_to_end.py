"""Ephemeral synthetic integration fixture; no real dataset or quality claims."""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from prepare_run import audit_dataset


def main():
    here = Path(__file__).resolve().parent
    repo = here.parents[2] / ".codex-work/3dgs-custom-main"
    processes = subprocess.check_output(["nvidia-smi", "--query-compute-apps=pid", "--format=csv,noheader"], text=True)
    if processes.strip():
        raise RuntimeError("GPU compute process active; do not run smoke concurrently")
    from PIL import Image
    with tempfile.TemporaryDirectory(prefix="exp77-smoke-") as tmp:
        root = Path(tmp)
        source = root / "scene"
        (source / "images").mkdir(parents=True)
        sparse = source / "sparse/0"
        sparse.mkdir(parents=True)
        (sparse / "cameras.txt").write_text("1 PINHOLE 32 32 16 16 16 16\n")
        rows, mapping = [], {}
        for i in range(24):
            name = f"{i:04d}.png"
            Image.new("RGB", (32, 32), (30 + i, 45, 60)).save(source / "images" / name)
            rows.append(f"{i+1} 1 0 0 0 {-i*.002} 0 0 1 {name}\n\n")
            if i % 8:
                mapping[name] = 1 if i < 17 else 12
        (sparse / "images.txt").write_text("".join(rows))
        (sparse / "points3D.ply").write_text(
            "ply\nformat ascii 1.0\nelement vertex 4\nproperty float x\nproperty float y\nproperty float z\n"
            "property float nx\nproperty float ny\nproperty float nz\nproperty uchar red\nproperty uchar green\n"
            "property uchar blue\nend_header\n" +
            "\n".join(f"{x} {y} 2 0 0 1 100 80 60" for x, y in ((-.2,-.2),(.2,-.2),(-.2,.2),(.2,.2))) + "\n")
        arrival = root / "arrivals.json"
        arrival.write_text(json.dumps({"arrival_iteration_by_name": mapping, "total_iterations": 12}))
        provenance = root / "provenance.json"
        provenance.write_text(json.dumps({"pose_source": "synthetic", "init_source": "synthetic 4 points",
                                         "init_uses_future_training_rgb": False}))
        prepared = subprocess.run([sys.executable, str(here / "prepare_run.py"), "--source", str(source),
                                  "--arrivals", str(arrival), "--output", str(root / "runs"),
                                  "--copy-complete", "--provenance", str(provenance), "--resolution", "1"],
                                 text=True, capture_output=True)
        if prepared.returncode:
            raise RuntimeError(prepared.stdout + prepared.stderr)
        manifest = json.loads(Path(prepared.stdout.strip()).read_text())
        results = {}
        for command in manifest["commands"]:
            run = subprocess.run(command["argv"], cwd=command["cwd"], text=True, capture_output=True)
            if run.returncode:
                raise RuntimeError(f"{command['arm']} failed:\n{run.stdout}\n{run.stderr}")
            output = Path(command["argv"][command["argv"].index("-m") + 1])
            summary = json.loads((output / "view_scheduler_summary.json").read_text())
            curve = [json.loads(line) for line in (output / "evaluation_curve.jsonl").read_text().splitlines()]
            tests = [row for row in curve if row["split"] == "test"]
            assert summary["completed_updates_this_run"] == 12 == sum(summary["selection_count"].values())
            assert summary["post_update_reporting"]
            assert tests[-1]["iteration"] == 12
            assert set(tests[-1]["per_view_psnr"]) == set(manifest["audit"]["test_names"])
            assert (output / "point_cloud/iteration_12/point_cloud.ply").is_file()
            results[command["arm"]] = {"completed_updates": 12, "evaluation_steps": [r["iteration"] for r in tests],
                                      "heldout_count": len(tests[-1]["per_view_psnr"]),
                                      "outer_trace_sha256": summary["outer_trace_sha256"]}
            print(f"{command['arm']}: integration PASS", flush=True)
        assert results["ercb"]["outer_trace_sha256"] == results["packet"]["outer_trace_sha256"]
        summarized = subprocess.run([sys.executable, str(here / "summarize.py"), "--runs", str(root / "runs")],
                                    text=True, capture_output=True)
        if summarized.returncode:
            raise RuntimeError(summarized.stdout + summarized.stderr)
        # Negative preflight checks must fail before CUDA or training.
        mapping.pop(next(iter(mapping)))
        arrival.write_text(json.dumps({"arrival_iteration_by_name": mapping}))
        try:
            audit_dataset(source, arrival, repo)
        except ValueError:
            pass
        else:
            raise AssertionError("Missing train arrival was not rejected")
        evidence = {"status": "PASS_SYNTHETIC_INTEGRATION_NOT_QUALITY", "arms": results,
                    "outer_pairing": True, "missing_arrival_rejected": True,
                    "temporary_fixture_removed_on_exit": True}
        (here / "evidence").mkdir(exist_ok=True)
        (here / "evidence/integration_smoke.json").write_text(json.dumps(evidence, indent=2) + "\n")


if __name__ == "__main__":
    main()
