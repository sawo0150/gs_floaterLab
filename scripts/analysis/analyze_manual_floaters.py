#!/usr/bin/env python3
"""
analyze_manual_floaters.py
Compares the original 3DGS point cloud and the human-cleaned (SuperSplat edited) point cloud,
extracts the exact floaters deleted by the user, and analyzes their lineage and decoupled gradient history.
"""
import numpy as np
from pathlib import Path
from plyfile import PlyData
import argparse
import json

def load_ply_vertex_data(ply_path):
    print(f"[Load] Reading {ply_path}...")
    ply_data = PlyData.read(str(ply_path))
    return ply_data["vertex"]

def build_matching_key(v):
    # Generates a unique key for each Gaussian based on coordinates (and potentially identifier attributes)
    x, y, z = np.array(v["x"]), np.array(v["y"]), np.array(v["z"])
    # We stack coordinates as a numpy array for spatial lookup
    return np.stack([x, y, z], axis=1).astype(np.float32)

def main():
    parser = argparse.ArgumentParser(description="Analyze manually labeled floaters from edited PLY.")
    parser.add_argument("--orig", type=str, required=True, 
                        help="Path to the original point_cloud.ply (containing lineage/grad attributes)")
    parser.add_argument("--cleaned", type=str, required=True, 
                        help="Path to the cleaned (SuperSplat edited) point_cloud.ply")
    parser.add_argument("--out", type=str, default=None, 
                        help="Path to save the output JSON analysis report")
    args = parser.parse_args()

    orig_path = Path(args.orig)
    cleaned_path = Path(args.cleaned)

    if not orig_path.exists() or not cleaned_path.exists():
        print("Error: Input PLY paths must exist.")
        return

    # Load PLYs
    v_orig = load_ply_vertex_data(orig_path)
    v_clean = load_ply_vertex_data(cleaned_path)

    n_orig = len(v_orig)
    n_clean = len(v_clean)
    n_deleted = n_orig - n_clean

    print(f"Original Gaussians: {n_orig:,}")
    print(f"Cleaned Gaussians: {n_clean:,}")
    print(f"Deleted Gaussians (Labeled Floaters): {n_deleted:,} ({100*n_deleted/n_orig:.2f}%)")

    if n_deleted <= 0:
        print("No floaters were deleted. Please edit the PLY in SuperSplat and delete some floaters first.")
        return

    # To trace which gaussians were deleted:
    # Since SuperSplat may apply rotations or scale offsets to coordinates and shuffle order,
    # we match points using color features (f_dc_0, f_dc_1, f_dc_2) which remain perfectly invariant.
    from scipy.spatial import KDTree
    
    print("[Matching] Querying semantic indices using Color-feature KD-Tree...")
    feat_orig = np.stack([np.array(v_orig["f_dc_0"]), np.array(v_orig["f_dc_1"]), np.array(v_orig["f_dc_2"])], axis=1).astype(np.float32)
    feat_clean = np.stack([np.array(v_clean["f_dc_0"]), np.array(v_clean["f_dc_1"]), np.array(v_clean["f_dc_2"])], axis=1).astype(np.float32)

    tree = KDTree(feat_clean)
    distances, _ = tree.query(feat_orig, workers=-1)
    
    # Points in original that are further than 1e-5 in color-space are considered deleted
    deleted_mask = distances > 1e-5
    surface_mask = ~deleted_mask

    actual_deleted_count = int(deleted_mask.sum())
    print(f"Double-checking deleted points count: {actual_deleted_count:,}")

    # Check if original ply has our custom lineage/grad tracking fields
    prop_names = [p.name for p in v_orig.properties]
    has_tracking = 'ancestor_idx' in prop_names

    if not has_tracking:
        print("Error: The original PLY does not contain lineage tracking attributes ('ancestor_idx', etc.).")
        print("Please ensure you optimized the scene with the modified training code.")
        return

    # Extract original attributes for analysis
    ancestor_idx = np.array(v_orig["ancestor_idx"]).astype(np.int64)
    birth_step = np.array(v_orig["birth_step"]).astype(np.int32)
    generation = np.array(v_orig["generation"]).astype(np.int32)
    num_splits = np.array(v_orig["num_splits"]).astype(np.int32)
    num_clones = np.array(v_orig["num_clones"]).astype(np.int32)
    accum_visibility = np.array(v_orig["accum_visibility"]).astype(np.int32)
    accum_rgb_grad = np.array(v_orig["accum_rgb_grad"]).astype(np.float32)
    accum_plateau_grad = np.array(v_orig["accum_plateau_grad"]).astype(np.float32)
    opacities = 1.0 / (1.0 + np.exp(-np.array(v_orig["opacity"], dtype=np.float64)))

    # Gather profiles for manually labeled floaters
    f_births = birth_step[deleted_mask]
    f_ancestors = ancestor_idx[deleted_mask]
    f_generations = generation[deleted_mask]
    f_splits = num_splits[deleted_mask]
    f_clones = num_clones[deleted_mask]
    f_vis = accum_visibility[deleted_mask]
    f_rgb_grad = accum_rgb_grad[deleted_mask]
    f_plat_grad = accum_plateau_grad[deleted_mask]
    f_opacities = opacities[deleted_mask]

    # Gather profiles for remaining surface points
    s_rgb_grad = accum_rgb_grad[surface_mask]
    s_plat_grad = accum_plateau_grad[surface_mask]
    s_opacities = opacities[surface_mask]

    # Compute Statistics
    report = {
        "summary": {
            "original_count": n_orig,
            "cleaned_count": n_clean,
            "manually_deleted_floaters": actual_deleted_count,
            "ratio_deleted": float(actual_deleted_count / n_orig)
        },
        "labeled_floaters": {
            "opacity": {
                "mean": float(f_opacities.mean()),
                "median": float(np.median(f_opacities)),
                "min": float(f_opacities.min()),
                "max": float(f_opacities.max())
            },
            "birth_step": {
                "mean": float(f_births.mean()),
                "median": float(np.median(f_births)),
                "min": int(f_births.min()),
                "max": int(f_births.max()),
                "histogram_stage": list(map(int, np.histogram(f_births, bins=[0, 1000, 3000, 5000, 7000, 15000, 30000])[0]))
            },
            "generation": {
                "mean": float(f_generations.mean()),
                "median": float(np.median(f_generations)),
                "max": int(f_generations.max())
            },
            "splits": {
                "mean": float(f_splits.mean()),
                "median": float(np.median(f_splits)),
                "max": int(f_splits.max())
            },
            "clones": {
                "mean": float(f_clones.mean()),
                "median": float(np.median(f_clones)),
                "max": int(f_clones.max())
            },
            "accum_visibility": {
                "mean": float(f_vis.mean()),
                "median": float(np.median(f_vis)),
                "max": int(f_vis.max()),
                "never_visible_count": int((f_vis == 0).sum()),
                "never_visible_ratio": float((f_vis == 0).sum() / actual_deleted_count)
            },
            "accum_rgb_grad": {
                "mean": float(f_rgb_grad.mean()),
                "median": float(np.median(f_rgb_grad)),
                "max": float(f_rgb_grad.max())
            },
            "accum_plateau_grad": {
                "mean": float(f_plat_grad.mean()),
                "median": float(np.median(f_plat_grad)),
                "max": float(f_plat_grad.max())
            }
        },
        "remaining_geometry": {
            "opacity": {
                "mean": float(s_opacities.mean()),
                "median": float(np.median(s_opacities))
            },
            "accum_rgb_grad": {
                "mean": float(s_rgb_grad.mean()),
                "median": float(np.median(s_rgb_grad))
            },
            "accum_plateau_grad": {
                "mean": float(s_plat_grad.mean()),
                "median": float(np.median(s_plat_grad))
            }
        }
    }

    # Top ancestors
    ancestors, counts = np.unique(f_ancestors, return_counts=True)
    sort_idx = np.argsort(-counts)
    top_ancestors = []
    for idx_rank in range(min(15, len(sort_idx))):
        top_ancestors.append({
            "ancestor_idx": int(ancestors[sort_idx[idx_rank]]),
            "count": int(counts[sort_idx[idx_rank]]),
            "ratio_of_floaters": float(counts[sort_idx[idx_rank]] / actual_deleted_count)
        })
    report["top_floaters_ancestors"] = top_ancestors

    # Print report summary
    print("\n" + "="*50)
    print("      MANUALLY LABELED FLOATER ANALYSIS REPORT      ")
    print("="*50)
    print(f"Decoupled Gradient Profile:")
    print(f"  RGB (Photometric) Grad Magnitude:")
    print(f"    - Labeled Floaters Mean: {report['labeled_floaters']['accum_rgb_grad']['mean']:.4e}")
    print(f"    - Remaining Surface Mean: {report['remaining_geometry']['accum_rgb_grad']['mean']:.4e}")
    print(f"    - Ratio (Floater/Surface): {report['labeled_floaters']['accum_rgb_grad']['mean'] / (report['remaining_geometry']['accum_rgb_grad']['mean'] + 1e-12):.4f}x")
    print(f"  Plateau Loss Grad Magnitude:")
    print(f"    - Labeled Floaters Mean: {report['labeled_floaters']['accum_plateau_grad']['mean']:.4e}")
    print(f"    - Remaining Surface Mean: {report['remaining_geometry']['accum_plateau_grad']['mean']:.4e}")
    print(f"    - Ratio (Floater/Surface): {report['labeled_floaters']['accum_plateau_grad']['mean'] / (report['remaining_geometry']['accum_plateau_grad']['mean'] + 1e-12):.4f}x")
    
    print(f"\nLineage & Densification Profile:")
    print(f"  - Mean Generation (split/clone depth): {report['labeled_floaters']['generation']['mean']:.2f}")
    print(f"  - Mean Splits: {report['labeled_floaters']['splits']['mean']:.2f}, Mean Clones: {report['labeled_floaters']['clones']['mean']:.2f}")
    print(f"  - Birth Steps [0-1k, 1-3k, 3-5k, 5-7k, 7-15k, 15k-30k]: {report['labeled_floaters']['birth_step']['histogram_stage']}")
    
    print(f"\nVisibility Profile:")
    print(f"  - Mean Viewspace Accum Visibility: {report['labeled_floaters']['accum_visibility']['mean']:.1f} frames")
    print(f"  - Never-Visible Floaters (accum_vis == 0): {report['labeled_floaters']['accum_visibility']['never_visible_count']} ({report['labeled_floaters']['accum_visibility']['never_visible_ratio']*100:.2f}%)")

    print(f"\nTop 5 Ancestor Seed Seeds:")
    for i, anc in enumerate(top_ancestors[:5]):
        print(f"  Rank {i+1}: Seed index {anc['ancestor_idx']} generated {anc['count']} floaters ({anc['ratio_of_floaters']*100:.1f}%)")
    print("="*50)

    # Save to JSON
    if args.out:
        out_path = Path(args.out)
        with open(out_path, "w") as f:
            json.dump(report, f, indent=4)
        print(f"\n[Saved] Detailed JSON report saved to {out_path}")

if __name__ == "__main__":
    main()
