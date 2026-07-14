#!/bin/bash
# exp46 배치: 축7b(max-dist)·B(footprint carve)·6(no-densify)·3(surfconf opacity)·A(budget init)
REPO=/home/wosas/Desktop/26-1_RPM/gsProjects/3dgs-custom
LAB=/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab
RESULTS=$LAB/results/experiments
GPUFREE(){ until [ "$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits)" -lt 1000 ]; do sleep 20; done; }
run(){  # $1=tag $2=source $3=carvecfg $4=extra_args $5=env
    GPUFREE; ts=$(date +%Y%m%d_%H%M%S); out="$RESULTS/${1}_${ts}"; mkdir -p "$out"; cd "$REPO"
    env $5 conda run -n 3dgs python train.py \
        --source_path "$2" --iterations 30000 --densify_until_iter 7000 \
        --densification_interval 200 --densify_grad_threshold 0.0004 \
        --scaling_lr 0.0025 --min_opacity_prune_threshold 0.01 --optimizer_beta1 0.85 \
        --data_device cpu --test_iterations 30000 --save_iterations 30000 \
        --disable_viewer --quiet --model_path "$out" \
        --carve_loss_config "$REPO/configs/carve_loss/$3" $4 \
        2>&1 | tee "$RESULTS/${1}_${ts}.log" | tail -1
    echo "== ${1} done =="; sleep 15
}
H12=$LAB/data/scenes/301_12F/03_rgb_3dgs_hyb
# 축7b: max-dist 하드 컷오프 (z_max=12m, 12F round9 Q3 9.3~p95 14.4 사이)
run exp46_ax7b_12F_zmax12 "$H12" exp43_12F_ctrl.yaml "" "FAR_ATTEN_ZMAX=12"
# 축B: footprint 스케일 carve (×3.1)
run exp46_axB_12F_fpscale "$H12" exp46_12F_fpscale.yaml "" ""
# 축6: no-densify + hybrid + carve
run exp46_ax6_12F_nodensify "$H12" exp43_12F_ctrl.yaml "--densify_until_iter 0" ""
# 축3: 표면-확신 opacity init
run exp46_ax3_12F_surfconf "$H12" exp43_12F_ctrl.yaml "" "CARVE_INIT_ATTRS=$LAB/data/scenes/301_12F/init_attrs_surfconf.npz"
# 축A: 305 budget init(122k) + carve
run exp46_axA_305_budget "$LAB/data/scenes/301_305/03_rgb_3dgs_hyb_budget" exp43_305_depth.yaml "" ""
echo BATCH1-DONE
