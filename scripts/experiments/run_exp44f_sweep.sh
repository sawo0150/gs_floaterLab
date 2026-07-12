#!/bin/bash
REPO=/home/wosas/Desktop/26-1_RPM/gsProjects/3dgs-custom
LAB=/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab
RESULTS=$LAB/results/experiments
SRC=$LAB/results/datasets/orb_dense_confmono_cf50colored_scene
run_one() {
    local name=$1; local iters=$2; local duntil=$3; local cfg=$4
    local ts=$(date +%Y%m%d_%H%M%S)
    local outdir="$RESULTS/${name}_${ts}"
    mkdir -p "$outdir"; cd "$REPO"
    echo "=== START: $name ==="
    conda run -n 3dgs python train.py \
        --source_path "$SRC" --iterations $iters --densify_until_iter $duntil \
        --densification_interval 200 --densify_grad_threshold 0.0004 \
        --scaling_lr 0.0025 --min_opacity_prune_threshold 0.01 --optimizer_beta1 0.85 \
        --data_device cpu --test_iterations $iters --save_iterations $iters \
        --disable_viewer --quiet --model_path "$outdir" \
        --carve_loss_config "$cfg" \
        2>&1 | tee "$RESULTS/${name}_${ts}.log" | tail -1
    echo "=== DONE: $name ==="
}
# 44f: densify ON + carve 풀 레시피 (품질 기함)
run_one "exp44f_cf50color_densify_30k" 30000 7000 "$REPO/configs/carve_loss/exp44f_full.yaml"
# 스윕: no-densify 강필터+색 15k/30k
run_one "exp44app50_cf50color_15k" 15000 0 "$REPO/configs/carve_loss/exp44a_nodensify.yaml"
run_one "exp44app50_cf50color_30k" 30000 0 "$REPO/configs/carve_loss/exp44a_nodensify.yaml"
