#!/bin/bash
# exp43: rot 장면 2연전 — ① hybrid init 이식(예방) ② maxop 보호 해제(치료 확장)
REPO=/home/wosas/Desktop/26-1_RPM/gsProjects/3dgs-custom
LAB=/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab
RESULTS=$LAB/results/experiments
run_one () {  # $1=tag $2=source $3=config
    until [ "$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits)" -lt 1000 ]; do sleep 30; done
    ts=$(date +%Y%m%d_%H%M%S)
    outdir="$RESULTS/${1}_${ts}"
    mkdir -p "$outdir"; cd "$REPO"
    conda run -n 3dgs python train.py \
        --source_path "$2" \
        --iterations 30000 --densify_until_iter 7000 \
        --densification_interval 200 --densify_grad_threshold 0.0004 \
        --scaling_lr 0.0025 --min_opacity_prune_threshold 0.01 --optimizer_beta1 0.85 \
        --data_device cpu --test_iterations 30000 --save_iterations 30000 \
        --disable_viewer --quiet --model_path "$outdir" \
        --carve_loss_config "$REPO/configs/carve_loss/$3" \
        2>&1 | tee "$RESULTS/${1}_${ts}.log" | tail -1
    sleep 30
}
run_one exp43rot_hyb_30k    "$LAB/data/scenes/301_1253_rot/03_rgb_3dgs_hyb" exp43rot_static.yaml
run_one exp43rot_nomaxop_30k "$LAB/data/scenes/301_1253_rot/03_rgb_3dgs"     exp43rot_nomaxop.yaml
echo ALL-DONE
