#!/bin/bash
# exp47 속도 배치: S3(iter)·S5(budget)·S2(cheapcarve)·S4(keyframe)·S6(res)·S1+S4(cuda)·TARGET
REPO=/home/wosas/Desktop/26-1_RPM/gsProjects/3dgs-custom
LAB=/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab
RESULTS=$LAB/results/experiments
CH=$LAB/data/scenes/301_12F
GPUFREE(){ until [ "$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits)" -lt 1000 ]; do sleep 20; done; }
run(){  # $1=tag $2=source $3=carvecfg $4=extra
    GPUFREE; ts=$(date +%Y%m%d_%H%M%S); out="$RESULTS/${1}_${ts}"; mkdir -p "$out"; cd "$REPO"
    /usr/bin/time -v conda run -n 3dgs python train.py \
        --source_path "$2" --iterations ${ITERS:-30000} --densify_until_iter 7000 \
        --densification_interval 200 --densify_grad_threshold 0.0004 \
        --scaling_lr 0.0025 --min_opacity_prune_threshold 0.01 --optimizer_beta1 0.85 \
        --data_device ${DDEV:-cpu} --test_iterations ${ITERS:-30000} --save_iterations ${ITERS:-30000} \
        --disable_viewer --quiet --model_path "$out" \
        --carve_loss_config "$REPO/configs/carve_loss/$3" $4 \
        > "$RESULTS/${1}_${ts}.log" 2>&1
    echo "== ${1} done =="; sleep 15
}
HYB=$CH/03_rgb_3dgs_hyb
# S3: 15k iter
ITERS=15000 DDEV=cpu run exp47_S3_12F_15k "$HYB" exp43_12F_ctrl.yaml ""
# S5: budget 235k
ITERS=30000 DDEV=cpu run exp47_S5_12F_budget235k "$CH/03_rgb_3dgs_hyb_budget" exp43_12F_ctrl.yaml ""
# S2: cheap carve (coarse voxel/cam_stride/refresh)
ITERS=30000 DDEV=cpu run exp47_S2_12F_cheapcarve "$HYB" exp47_12F_cheapcarve.yaml ""
# S4: keyframe 300
ITERS=30000 DDEV=cpu run exp47_S4_12F_kf300 "$CH/03_rgb_3dgs_hyb_kf300" exp43_12F_ctrl.yaml ""
# S6: resolution /2
ITERS=30000 DDEV=cpu run exp47_S6_12F_r2 "$HYB" exp43_12F_ctrl.yaml "-r 2"
# S1+S4: keyframe 300 + cuda
ITERS=30000 DDEV=cuda run exp47_S1S4_12F_kf300cuda "$CH/03_rgb_3dgs_hyb_kf300" exp43_12F_ctrl.yaml ""
# TARGET: budget235k + kf300 + cuda + cheapcarve + 15k
ITERS=15000 DDEV=cuda run exp47_TARGET_12F "$CH/03_rgb_3dgs_hyb_budget_kf300" exp47_12F_cheapcarve.yaml ""
# 폴더뷰 인덱스 갱신 (forward 관례)
/home/wosas/miniconda3/envs/3dgs/bin/python $LAB/scripts/experiments/index_runs_by_exp.py
echo EXP47-BATCH-DONE
