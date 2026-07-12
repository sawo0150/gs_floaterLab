#!/bin/bash
# exp44 held-out 검증: segment split(test.txt 유지 상태)로 44h/44f 재학습 + baseline 대조
REPO=/home/wosas/Desktop/26-1_RPM/gsProjects/3dgs-custom
LAB=/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab
RESULTS=$LAB/results/experiments
run_one() {
    local name=$1; local src=$2; local iters=$3; local duntil=$4; local cfg=$5
    local ts=$(date +%Y%m%d_%H%M%S)
    local outdir="$RESULTS/${name}_${ts}"
    local extra=(); [ -n "$cfg" ] && extra=(--carve_loss_config "$cfg")
    mkdir -p "$outdir"; cd "$REPO"
    echo "=== START: $name ==="
    conda run -n 3dgs python train.py \
        --source_path "$src" --iterations $iters --densify_until_iter $duntil --eval \
        --densification_interval 200 --densify_grad_threshold 0.0004 \
        --scaling_lr 0.0025 --min_opacity_prune_threshold 0.01 --optimizer_beta1 0.85 \
        --data_device cpu --test_iterations $iters --save_iterations $iters \
        --disable_viewer --quiet --model_path "$outdir" \
        "${extra[@]}" 2>&1 | tee "$RESULTS/${name}_${ts}.log" | tail -1
    echo "=== DONE: $name ==="
}
SNAP=$LAB/results/datasets/orb_dense_confmono_snap_refilt_scene
# snap scene에 test.txt 배치 (segment split 동일)
cp $LAB/data/03_rgb_3dgs_full/sparse/0/test.txt $SNAP/sparse/0/test.txt 2>/dev/null
run_one "exp44h_eval_seg_15k"  "$SNAP" 15000 3000 "$REPO/configs/carve_loss/exp44f_full.yaml"
run_one "exp44f_eval_seg_30k"  "$SNAP" 30000 7000 "$REPO/configs/carve_loss/exp44f_full.yaml"
