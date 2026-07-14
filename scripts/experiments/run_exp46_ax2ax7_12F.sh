#!/bin/bash
# exp46 축2(12F 좋은 init 진단) + 축7(원거리 photometric 감쇠) — 축1 뒤 체인
REPO=/home/wosas/Desktop/26-1_RPM/gsProjects/3dgs-custom
LAB=/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab
RESULTS=$LAB/results/experiments
SPD=/tmp/claude-1000/-home-wosas-Desktop-Incremental-mapping-test-gs-floaterLab/a18dbc8f-4cce-4ad0-a1ea-8f9bb38b1ea6/scratchpad
GPUFREE(){ until [ "$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits)" -lt 1000 ]; do sleep 20; done; }
# 축1 완료 대기
until grep -q AX1-DONE $SPD/ax1_chain.log 2>/dev/null; do sleep 60; done

train12F(){  # $1=tag  $2=source  $3=extra_args  $4=env
    GPUFREE; ts=$(date +%Y%m%d_%H%M%S); outdir="$RESULTS/${1}_${ts}"; mkdir -p "$outdir"; cd "$REPO"
    env $4 conda run -n 3dgs python train.py \
        --source_path "$2" --iterations 30000 \
        --densification_interval 200 --densify_grad_threshold 0.0004 \
        --densify_until_iter 7000 --scaling_lr 0.0025 \
        --min_opacity_prune_threshold 0.01 --optimizer_beta1 0.85 \
        --data_device cpu --test_iterations 30000 --save_iterations 30000 \
        --disable_viewer --quiet --model_path "$outdir" $3 \
        2>&1 | tee "$RESULTS/${1}_${ts}.log" | tail -1
    sleep 20
}

# ── 축2: 12F hybrid init (carve 없음 — 좋은 init만으로 천장 오르나) ──
cd $LAB
rm -rf data/scenes/301_12F/03_rgb_3dgs_hyb
/home/wosas/miniconda3/envs/3dgs/bin/python scripts/anchors/build_hybrid_init_scene.py --scene 301_12F
train12F exp46_ax2_12Fhyb_30k "$LAB/data/scenes/301_12F/03_rgb_3dgs_hyb" "" ""

# ── 축7: 12F baseline 대조군 + 원거리 감쇠(z0=9.3=round9 Q3, k=4) ──
train12F exp46_ax7_12Fctrl_30k  "$LAB/data/scenes/301_12F/03_rgb_3dgs" "" ""
train12F exp46_ax7_12Fatten_30k "$LAB/data/scenes/301_12F/03_rgb_3dgs" "" "FAR_ATTEN_Z0=9.3 FAR_ATTEN_K=4"
echo AX2AX7-DONE
