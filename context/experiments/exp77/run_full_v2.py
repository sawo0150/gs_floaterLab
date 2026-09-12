"""Sequential seed0 screen; stop on failure, no parameter search or deletion."""
import json
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = ROOT / "outputs/exp77_full_v2_seed0"

def main():
    OUT.mkdir(parents=True, exist_ok=False)
    repairs = []
    # Only rewrite broken image symlinks in the requested full v2 UTMM dataset.
    images = ROOT / "data/benchmarks/ercb_vigs_replay_v2/utmm_square1_full/images"
    for link in sorted(images.iterdir()):
        if not link.is_symlink() or link.exists():
            continue
        old = str(link.readlink())
        marker = "/data/benchmarks/"
        if marker not in old:
            raise ValueError(old)
        target = ROOT / "data/benchmarks" / old.split(marker, 1)[1]
        if not target.is_file():
            raise FileNotFoundError(target)
        repairs.append({"link": str(link), "old": old, "new": str(target)})
    (OUT / "link_repairs.json").write_text(json.dumps(repairs, indent=2))
    for item in repairs:
        link = Path(item["link"])
        link.unlink()
        link.symlink_to(item["new"])
    for scene in ("utmm_square1_full", "rpng_table01_full"):
        source = ROOT / "data/benchmarks/ercb_vigs_replay_v2" / scene
        md = json.loads((source / "vigs_replay_metadata.json").read_text())
        provenance = OUT / (scene + "_provenance.json")
        provenance.write_text(json.dumps({"pose_source": md["pose_source"],
            "init_source": md["initialization"], "init_uses_future_training_rgb": False,
            "offline_noncausal_fixed_pose_init": True, "original_metadata": md}, indent=2))
        runs = OUT / scene
        subprocess.run([sys.executable, str(HERE / "prepare_run.py"), "--source", str(source),
            "--arrivals", str(source / "causal_arrivals.json"), "--output", str(runs),
            "--provenance", str(provenance), "--copy-complete"], check=True)
        manifest = json.loads((runs / "commands_s0.json").read_text())
        for entry in manifest["commands"]:
            if shutil.disk_usage(ROOT).free < 3 * 1024**3:
                raise RuntimeError("Less than 3 GiB free; stopping without deletion")
            print(scene, entry["arm"], "START", flush=True)
            with (runs / (entry["arm"] + ".log")).open("x") as log:
                subprocess.run(entry["argv"], cwd=entry["cwd"], stdout=log,
                               stderr=subprocess.STDOUT, check=True)
            print(scene, entry["arm"], "DONE", flush=True)
        subprocess.run([sys.executable, str(HERE / "summarize.py"), "--runs", str(runs),
                        "--seed", "0"], check=True)
    print("SEED0_SCREEN_COMPLETE", flush=True)

if __name__ == "__main__":
    main()
