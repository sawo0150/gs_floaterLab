"""Read-only contract checks and partial/final development comparison."""
import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

def read_run(path):
    s = json.loads((path / "view_scheduler_summary.json").read_text())
    rows = [json.loads(x) for x in (path / "evaluation_curve.jsonl").read_text().splitlines()]
    rows = [x for x in rows if x["split"] == "test"]
    assert s["post_update_reporting"]
    assert s["completed_updates_this_run"] == s["total_iterations"] == sum(s["selection_count"].values())
    assert max(s["arrival_iteration"].values()) == s["total_iterations"] == rows[-1]["iteration"]
    assert all(x >= 0 for x in s["first_service_delay_updates"].values())
    return s, rows

def main():
    for scene in ("utmm_square1_full", "rpng_table01_full"):
        base, ref = read_run(ROOT / "outputs/exp77_full_v2_seed0" / scene / "rr_s0")
        for arm in ("interval_base", "coverage1", "coverage2"):
            path = ROOT / "outputs/exp77_coverage_screen_s0" / scene / (arm + "_s0")
            if not (path / "view_scheduler_summary.json").exists():
                print(scene, arm, "PENDING")
                continue
            s, rows = read_run(path)
            assert s["arrival_iteration"] == base["arrival_iteration"]
            assert [r["iteration"] for r in rows] == [r["iteration"] for r in ref]
            assert all(set(a["per_view_psnr"]) == set(b["per_view_psnr"]) for a,b in zip(rows,ref))
            print(json.dumps({"scene": scene, "arm": arm, "contract": "PASS",
                "psnr": rows[-1]["psnr"], "delta_rr": rows[-1]["psnr"] - ref[-1]["psnr"],
                "curve_delta_rr": [a["psnr"]-b["psnr"] for a,b in zip(rows,ref)],
                "zero_service": s["zero_service"],
                "served_first_delay": statistics.fmean(s["first_service_delay_updates"].values())}))

if __name__ == "__main__":
    main()
