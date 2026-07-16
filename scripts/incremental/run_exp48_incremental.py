#!/usr/bin/env python3
import argparse
import json
import subprocess
import sys
from pathlib import Path
import torch

def parse_args():
    parser = argparse.ArgumentParser(description="Orchestrator for exp48 Incremental 3DGS pipeline")
    parser.add_argument("--phase", type=str, default="0a", choices=["0a", "0b"],
                        help="phase0a: 2 chunks for fast code validation. phase0b: 57 chunks full run.")
    parser.add_argument("--iters-per-chunk", type=int, default=200,
                        help="number of iterations to train per keyframe chunk")
    return parser.parse_args()

def main():
    args = parse_args()
    
    # Paths
    lab_dir = Path("/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab")
    repo_dir = Path("/home/wosas/Desktop/26-1_RPM/gsProjects/3dgs-custom")
    vrs_path = Path("/home/wosas/Desktop/26-1_RPM/Datas/CustomData/0416_Data/0416_301-1253/0416_301-1253.vrs")
    orb_export_dir = lab_dir / "data/02_openmavis_output/orb_export"
    output_dataset_dir = lab_dir / "data/scenes/301_1253/04_incremental"
    results_dir = lab_dir / f"results/experiments/exp48_incremental_phase{args.phase}"
    
    results_dir.mkdir(parents=True, exist_ok=True)
    
    # Step 1: Build the incremental chunks dataset if not already built
    manifest_path = output_dataset_dir / "manifest.json"
    if manifest_path.exists() and manifest_path.stat().st_size > 0:
        print("=== [exp48] Step 1: Chunks dataset already exists, skipping build ===")
    else:
        print("=== [exp48] Step 1: Building incremental chunks dataset ===")
        build_script = lab_dir / "scripts/incremental/build_incremental_chunks.py"
        
        build_cmd = [
            "conda", "run", "-n", "aria", "python", str(build_script),
            "--orb-export", str(orb_export_dir),
            "--vrs", str(vrs_path),
            "--output", str(output_dataset_dir)
        ]
        
        print(f"Running: {' '.join(build_cmd)}")
        import os
        sub_env = os.environ.copy()
        for k in list(sub_env.keys()):
            if k.startswith("CONDA_") or k.startswith("_CONDA"):
                sub_env.pop(k)
        res = subprocess.run(build_cmd, env=sub_env, capture_output=True, text=True)
        if res.returncode != 0:
            print("Dataset building failed!")
            print(res.stderr)
            sys.exit(1)
        print(res.stdout)
    
    # Load manifest to get chunk information
    manifest_path = output_dataset_dir / "manifest.json"
    with manifest_path.open("r", encoding="utf-8") as f:
        chunks = json.load(f)
        
    if args.phase == "0a":
        # Phase 0a: Only run first 2 chunks
        chunks = chunks[:2]
        print(f"=== Running Phase 0a: 2 chunks validation (chunk_000 to chunk_001) ===")
    else:
        print(f"=== Running Phase 0b: Full {len(chunks)} chunks run ===")
        
    prev_chkpnt = None
    stats_history = []
    
    # Step 2: Sequential Training loop
    for i, chunk in enumerate(chunks):
        chunk_idx = chunk["chunk_idx"]
        kf_id = chunk["kf_id"]
        num_new_pts = chunk["num_new_map_points"]
        
        chunk_dataset_path = output_dataset_dir / f"chunk_{chunk_idx:03d}"
        chunk_model_path = results_dir / f"chunk_{chunk_idx:03d}"
        chunk_model_path.mkdir(parents=True, exist_ok=True)
        
        target_iterations = (chunk_idx + 1) * args.iters_per_chunk
        
        print(f"\n--- [Chunk {chunk_idx:03d} / Keyframe {kf_id}] Target Iterations: {target_iterations} ---")
        print(f"New map points to seed: {num_new_pts}")
        
        densify_until = target_iterations - args.iters_per_chunk // 2
        # Build command
        cmd = [
            "conda", "run", "-n", "3dgs", "--no-capture-output", "python", "train.py",
            "--source_path", str(chunk_dataset_path),
            "--model_path", str(chunk_model_path),
            "--iterations", str(target_iterations),
            "--densify_until_iter", str(densify_until),
            "--densification_interval", "50",
            "--data_device", "cpu",
            "--disable_viewer", "--quiet",
            "--save_iterations", str(target_iterations),
            "--test_iterations", str(target_iterations),
            "--checkpoint_iterations", str(target_iterations)
        ]
        
        if prev_chkpnt is not None:
            cmd += [
                "--start_checkpoint", str(prev_chkpnt),
                "--extra_init_points", str(chunk_dataset_path / "sparse/0/extra_points3D.txt")
            ]
            
        print(f"Executing: {' '.join(cmd)}")
        # Sanitize env to prevent nested conda run issues
        import os
        sub_env = os.environ.copy()
        for k in list(sub_env.keys()):
            if k.startswith("CONDA_") or k.startswith("_CONDA"):
                sub_env.pop(k)
        res = subprocess.run(cmd, cwd=str(repo_dir), env=sub_env)
        
        if res.returncode != 0:
            print(f"Training failed at chunk {chunk_idx}!")
            sys.exit(1)
            
        # Expected checkpoint path
        chkpnt_path = chunk_model_path / f"chkpnt{target_iterations}.pth"
        if not chkpnt_path.exists():
            print(f"Expected checkpoint not found at: {chkpnt_path}")
            sys.exit(1)
            
        # Load checkpoint parameters to inspect Gaussian count
        checkpoint_data = torch.load(chkpnt_path, map_location="cpu", weights_only=False)
        model_params = checkpoint_data[0] # model_params, iteration tuple
        xyz_tensor = model_params[1] # (active_sh_degree, _xyz, _features_dc, ...)
        num_gaussians = xyz_tensor.shape[0]
        
        print(f"Chunk {chunk_idx:03d} finished successfully. Checkpoint saved: {chkpnt_path}")
        print(f"Gaussian count: {num_gaussians}")
        
        stats_history.append({
            "chunk_idx": chunk_idx,
            "kf_id": kf_id,
            "target_iterations": target_iterations,
            "num_gaussians": num_gaussians,
            "num_new_mps": num_new_pts
        })
        
        prev_chkpnt = chkpnt_path

    # Final summary printing
    print("\n================ exp48 Run Summary ================")
    print("Index | KF_ID | Target_Iter | New_MPs | Gaussian_Count")
    print("-" * 55)
    for stat in stats_history:
        print(f"{stat['chunk_idx']:5d} | {stat['kf_id']:5d} | {stat['target_iterations']:11d} | {stat['num_new_mps']:7d} | {stat['num_gaussians']:14d}")
        
    print("\nWarm-start Pipeline Verification completed successfully!")

    # Step 3: Run final rendering to verify results visually
    print("\n=== [exp48] Step 3: Running final rendering on test split ===")
    final_chunk_idx = chunks[-1]["chunk_idx"]
    final_target_iterations = (final_chunk_idx + 1) * args.iters_per_chunk
    final_model_dir = results_dir / f"chunk_{final_chunk_idx:03d}"
    
    render_cmd = [
        "conda", "run", "-n", "3dgs", "--no-capture-output", "python", "render.py",
        "--model_path", str(final_model_dir),
        "--source_path", str(lab_dir / "data/03_rgb_3dgs_full"),
        "--eval",
        "--skip_train"
    ]
    print(f"Executing rendering: {' '.join(render_cmd)}")
    import os
    sub_env = os.environ.copy()
    for k in list(sub_env.keys()):
        if k.startswith("CONDA_") or k.startswith("_CONDA"):
            sub_env.pop(k)
            
    res_render = subprocess.run(render_cmd, cwd=str(repo_dir), env=sub_env)
    if res_render.returncode != 0:
        print("Rendering failed!")
    else:
        print(f"Rendering complete! Images saved to Ours validation folders in: {final_model_dir}")

if __name__ == "__main__":
    main()
