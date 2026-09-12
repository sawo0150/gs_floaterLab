"""Preregistered development screen, original full-v2 budget unchanged."""
import json
import subprocess
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "outputs/exp77_coverage_screen_s0"

def main():
    OUT.mkdir(parents=True, exist_ok=False)
    jobs = []
    for scene in ("utmm_square1_full", "rpng_table01_full"):
        original = ROOT / "outputs/exp77_full_v2_seed0" / scene / "commands_s0.json"
        base = json.loads(original.read_text())["commands"][1]
        for arm in ("interval_base", "coverage1", "coverage2"):
            argv = list(base["argv"])
            argv[argv.index("--arm") + 1] = arm
            argv[argv.index("-m") + 1] = str(OUT / scene / (arm + "_s0"))
            jobs.append(dict(scene=scene, arm=arm, argv=argv, cwd=base["cwd"]))
    (OUT / "manifest.json").write_text(json.dumps({"scope": "development, not independent validation",
        "fixed_before_runs": True, "jobs": jobs}, indent=2))
    for job in jobs:
        if shutil.disk_usage(ROOT).free < 3 * 1024**3:
            raise RuntimeError("Disk reserve below 3 GiB")
        folder = OUT / job["scene"]
        folder.mkdir(exist_ok=True)
        print(job["scene"], job["arm"], "START", flush=True)
        with (folder / (job["arm"] + ".log")).open("x") as log:
            subprocess.run(job["argv"], cwd=job["cwd"], stdout=log, stderr=subprocess.STDOUT, check=True)
        print(job["scene"], job["arm"], "DONE", flush=True)

if __name__ == "__main__":
    main()
