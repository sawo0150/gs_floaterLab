"""exp56 Phase 5 (2026-07-27): fit per-part timing vs. (iters, n_view, n_gauss, resolution)
using the map_call opt-in log (VIGS_TIMING_LOG, "map_call,<metric>,<ms>,iters=..,n_view=..,
n_gauss=.." rows -- already emitted by gs_backend.py, never aggregated across runs before this).
Least-squares fit per _Sect metric (rasterize/loss_compute/backward/optimizer_step), separately
for serial (uncontended) vs parallel (GPU-contended) runs, to isolate which VIGS knobs actually
drive per-call cost vs. which are noise. See exp56_mapping_fixedcost_reduction.md Phase 5 for the
written-up coefficients, validation, and interpretation (why n_view dominates).
"""
import re
import numpy as np

RESULTS = "/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab/results/experiments"

# (run_dir under results/experiments/, render_downsample factor used for that run, parallel/serial)
RUNS = [
    ("exp55_serial_final",        1, "serial"),
    ("exp56_serial_iters7_nods",  1, "serial"),
    ("exp56_serial_iters7_ds2",   2, "serial"),
    ("exp56_iters7",              1, "parallel"),
    ("exp56_iters5",              1, "parallel"),
    ("exp56_renderds2_iters7",    2, "parallel"),
    ("exp56_queue4_iters7",       1, "parallel"),
    ("exp56_initnum300",          1, "parallel"),
    ("exp56_initnum600",          1, "parallel"),
    ("exp55_final_confirm",       1, "parallel"),
    ("exp55_carveon_anchors",     1, "parallel"),
]


def parse(run, ds, mode):
    """Group consecutive map_call rows (rasterize,loss_compute,backward,optimizer_step[,densify_prune])
    into one dict per actual map() call, tagged with that call's (iters, n_view, n_gauss)."""
    path = f"{RESULTS}/{run}/timing.csv"
    calls = []
    cur, cur_meta = None, None
    with open(path) as f:
        for line in f:
            if not line.startswith("map_call,"):
                continue
            parts = line.strip().split(",")
            metric, val = parts[1], float(parts[2])
            meta = ",".join(parts[3:])
            iters = int(re.search(r"iters=(\d+)", meta).group(1))
            nview = int(re.search(r"n_view=(\d+)", meta).group(1))
            ngauss = int(re.search(r"n_gauss=(\d+)", meta).group(1))
            if metric == "rasterize":  # first metric written per call -> start a new call group
                if cur is not None:
                    calls.append((cur_meta, cur))
                cur, cur_meta = {}, (iters, nview, ngauss)
            if cur is None:
                cur, cur_meta = {}, (iters, nview, ngauss)
            cur[metric] = val
        if cur is not None:
            calls.append((cur_meta, cur))

    pixels_ratio = 1.0 / (ds ** 2)
    out = []
    for (iters, nview_raw, ngauss), metrics in calls:
        # PGBA calls pass max_viewpoints=12 and n_view logged is the full candidate pool
        # (packet['tstamp'][packet['viz_idx']], can be 90-110+) -- the ACTUAL per-iteration
        # render count is capped at max_viewpoints. Regular/init calls never exceed the
        # default cap (20) so n_view_raw == n_view_eff for them.
        is_pgba = (nview_raw > 15)
        max_vp = 12 if is_pgba else 20
        nview_eff = min(nview_raw, max_vp)
        out.append(dict(run=run, mode=mode, ds=ds, pixels_ratio=pixels_ratio,
                         iters=iters, n_view_raw=nview_raw, n_view=nview_eff, n_gauss=ngauss,
                         is_pgba=is_pgba,
                         rasterize=metrics.get("rasterize", 0.0),
                         loss_compute=metrics.get("loss_compute", 0.0),
                         backward=metrics.get("backward", 0.0),
                         optimizer_step=metrics.get("optimizer_step", 0.0)))
    return out


def fit(rows, ycol, features, names, label):
    X = np.array([[f(r) for f in features] for r in rows], dtype=np.float64)
    y = np.array([r[ycol] for r in rows], dtype=np.float64)
    coef, *_ = np.linalg.lstsq(X, y, rcond=None)
    pred = X @ coef
    ss_res = np.sum((y - pred) ** 2)
    ss_tot = np.sum((y - y.mean()) ** 2)
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else float("nan")
    print(f"\n=== {label} (n={len(rows)}) R^2={r2:.4f} ===")
    for n, c in zip(names, coef):
        print(f"  {n:45s} = {c:.5f}")
    return coef, r2


# Feature basis for rasterize/loss_compute: these run INSIDE the per-viewpoint python for-loop,
# so their natural unit is "one view-op" = one iteration's processing of one camera.
f_ncalls       = lambda r: r["iters"] * r["n_view"]
f_ncalls_gauss = lambda r: r["iters"] * r["n_view"] * r["n_gauss"] / 1000.0
f_ncalls_pix   = lambda r: r["iters"] * r["n_view"] * r["pixels_ratio"]

# backward/optimizer_step run ONCE per iteration (outside the per-viewpoint loop, on the
# accumulated loss over all views), so their unit is "one iteration", with n_view/n_gauss
# affecting the size of the autograd graph / parameter count that single call touches.
f_iters        = lambda r: r["iters"]
f_iters_view   = lambda r: r["iters"] * r["n_view"]
f_iters_gauss  = lambda r: r["iters"] * r["n_gauss"] / 1000.0

if __name__ == "__main__":
    rows = []
    for run, ds, mode in RUNS:
        rows += parse(run, ds, mode)
    print(f"total calls parsed: {len(rows)}  (pgba: {sum(r['is_pgba'] for r in rows)})")

    serial_rows = [r for r in rows if r["mode"] == "serial"]
    print(f"\n########## SERIAL-ONLY FIT (n={len(serial_rows)}, no GPU contention) ##########")
    for metric in ["rasterize", "loss_compute"]:
        fit(serial_rows, metric, [f_ncalls, f_ncalls_gauss, f_ncalls_pix],
            ["a: ms per (iters*n_view) [fixed launch cost/view-op]",
             "b: ms per (iters*n_view*n_gauss/1000) [gaussian-scaling]",
             "c: ms per (iters*n_view*pixels_ratio) [pixel-scaling]"],
            f"{metric} ~ a*ncalls + b*ncalls*ngauss/1k + c*ncalls*pixratio")
    for metric in ["backward", "optimizer_step"]:
        fit(serial_rows, metric, [f_iters, f_iters_view, f_iters_gauss],
            ["a: ms per iters [fixed per-iter cost]",
             "b: ms per (iters*n_view) [per-view-in-graph cost]",
             "c: ms per (iters*n_gauss/1000) [param-count cost]"],
            f"{metric} ~ a*iters + b*iters*n_view + c*iters*ngauss/1k")

    parallel_rows = [r for r in rows if r["mode"] == "parallel" and not r["is_pgba"]]
    print(f"\n########## PARALLEL-ONLY FIT (n={len(parallel_rows)}, WITH GPU contention) ##########")
    for metric in ["rasterize", "loss_compute"]:
        fit(parallel_rows, metric, [f_ncalls, f_ncalls_gauss, f_ncalls_pix],
            ["a", "b", "c"], f"{metric} ~ a*ncalls + b*ncalls*ngauss/1k + c*ncalls*pixratio")
    for metric in ["backward"]:
        fit(parallel_rows, metric, [f_iters, f_iters_view, f_iters_gauss],
            ["a", "b", "c"], f"{metric} ~ a*iters + b*iters*n_view + c*iters*ngauss/1k")
