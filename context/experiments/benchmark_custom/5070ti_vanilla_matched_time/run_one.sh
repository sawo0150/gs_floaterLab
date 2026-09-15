#!/usr/bin/env bash
# Run one custom unified-pool scene at vanilla's measured map-completion budget.
set -euo pipefail

family=${1:?usage: run_one.sh FAMILY SCENE SELECTOR [OUTPUT_DIR]}
scene=${2:?usage: run_one.sh FAMILY SCENE SELECTOR [OUTPUT_DIR]}
selector=${3:?usage: run_one.sh FAMILY SCENE SELECTOR [OUTPUT_DIR]}
admission=${MATCHED_ADMISSION:-arrival}
required_opportunities=${MATCHED_REQUIRED_OPPORTUNITIES:-4}
mapping_seed=${MAPPING_SEED:-0}
mapping_steps_per_packet=${MAPPING_STEPS_PER_PACKET:-0}
script_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
lab_root=/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab
repo_root=${VIGS_REPO_ROOT:-/home/wosas/Desktop/26-1_RPM/gsProjects/VIGS-SLAM-main-integration-20260828}
asset_root=${VIGS_ASSET_ROOT:-$repo_root}
rasterizer_root=${VIGS_RASTERIZER_ROOT:-$repo_root/thirdparty/diff-gaussian-rasterization}
conda_env=/home/wosas/miniconda3/envs/vigs-slam-5090
birth_downsample_multiplier=${MAPPING_BIRTH_DOWNSAMPLE_MULTIPLIER:-1.0}
prune_opacity_multiplier=${MAPPING_PRUNE_OPACITY_MULTIPLIER:-1.0}
mapping_pose_source=${MAPPING_DENSE_POSE_SOURCE:-imu_rotation_bridge}
mapping_gt_trajectory=${MAPPING_GT_TRAJECTORY:-}
mapping_gt_camera_frame=${MAPPING_GT_CAMERA_FRAME:-camera}
dense_gradient_scope=${MAPPING_DENSE_GRADIENT_SCOPE:-appearance_opacity}
frontend_trace_mode=${MAPPING_FRONTEND_TRACE_MODE:-off}
frontend_trace_dir=${MAPPING_FRONTEND_TRACE_DIR:-}
topology_trace_mode=${MAPPING_TOPOLOGY_TRACE_MODE:-off}
topology_trace_dir=${MAPPING_TOPOLOGY_TRACE_DIR:-}
trace_packet_driven_topology=${MAPPING_TRACE_PACKET_DRIVEN_TOPOLOGY:-0}
case "$admission" in
    arrival)
        admission_tag=arrival
        admission_args=()
        dense_membership_args=(
            --background_dense_stride 5
            --background_dense_offsets 2
            --background_dense_interval_max_views 1
        )
        ;;
    work_credit)
        if ! [[ "$required_opportunities" =~ ^[1-9][0-9]*$ ]]; then
            echo "MATCHED_REQUIRED_OPPORTUNITIES must be positive" >&2
            exit 2
        fi
        admission_tag="workcredit_cycle_r${required_opportunities}"
        admission_args=(
            --mapping_adaptive_viewset
            --mapping_work_credit_admission
            --mapping_viewset_required_opportunities "$required_opportunities"
        )
        dense_membership_args=(--background_dense_stride 0)
        ;;
    *) echo "unsupported MATCHED_ADMISSION: $admission" >&2; exit 2 ;;
esac
default_suffix="${selector}_unified_pool_seed${mapping_seed}"
if [ "$admission" != arrival ]; then
    default_suffix="${selector}_unified_pool_${admission_tag}_seed${mapping_seed}"
fi
output_dir=${4:-"$lab_root/results/benchmarks/benchmark_custom/5070ti_vanilla_matched_time/$family/$scene/$default_suffix"}
case "$output_dir" in
    /*) ;;
    *) output_dir="$(pwd)/$output_dir" ;;
esac
if ! [[ "$mapping_steps_per_packet" =~ ^[0-9]+$ ]]; then
    echo "MAPPING_STEPS_PER_PACKET must be a non-negative integer" >&2
    exit 2
fi
packet_budget_args=()
if [ "$mapping_steps_per_packet" -gt 0 ]; then
    packet_budget_args=(
        --mapping_replay_steps_per_packet "$mapping_steps_per_packet"
    )
fi

case "$selector" in
    rr) selector_args=() ;;
    rr_role_stratified) selector_args=(
        --mapping_interval_ercb_role_stratified
    ) ;;
    view_uniform_k128) selector_args=(
        --mapping_replay_count_softmax_beta 0
        --mapping_replay_count_softmax_block_size 128
    ) ;;
    ercb_view_count_b002_k128) selector_args=(
        --mapping_replay_count_softmax_beta 0.02
        --mapping_replay_count_softmax_block_size 128
    ) ;;
    ercb_view_count_b002_k32) selector_args=(
        --mapping_replay_count_softmax_beta 0.02
        --mapping_replay_count_softmax_block_size 32
    ) ;;
    ercb_view_count_b002_k8) selector_args=(
        --mapping_replay_count_softmax_beta 0.02
        --mapping_replay_count_softmax_block_size 8
    ) ;;
    ercb_base) selector_args=(--mapping_interval_ercb base) ;;
    ercb_relative_floor) selector_args=(--mapping_interval_ercb relative_floor) ;;
    ercb_relative_floor_role_stratified) selector_args=(
        --mapping_interval_ercb relative_floor
        --mapping_interval_ercb_role_stratified
    ) ;;
    ercb_relative_floor_keyframe_stratified) selector_args=(
        --mapping_interval_ercb relative_floor
        --mapping_interval_ercb_role_stratified
        --mapping_interval_ercb_target_role keyframe
    ) ;;
    ercb_coverage1) selector_args=(--mapping_interval_ercb coverage1) ;;
    *) echo "unsupported selector: $selector" >&2; exit 2 ;;
esac

case "$family:$scene" in
    utmm:ego-centric-1|utmm:ego-centric-2|utmm:ego-drive|utmm:fast-straight|utmm:slow-straight-1|utmm:slow-straight-2|utmm:square-1|utmm:square-2)
        dataset_root="$lab_root/data/benchmarks/utmm/prepared/UTMM_Dataset/$scene"
        image_dir="$dataset_root/rgb_timestamp"
        imu_file="$dataset_root/imu_ours.txt"
        calibration="$dataset_root/intrinsics_ours.txt"
        config_file="$script_dir/config/utmm_unified_pool.yaml"
        trt_dir="$asset_root/pretrained_models/generated_utmm_328x648"
        family_args=(--undistort --IMU_poseinit_after 15 --buffer 1200)
        ;;
    rpng:table_0[1-8])
        dataset_root="$lab_root/data/benchmarks/rpng/prepared/rpngar/$scene"
        image_dir="$dataset_root/rgb"
        imu_file="$dataset_root/imu.txt"
        calibration="$asset_root/calib/rpngar.txt"
        config_file="$script_dir/config/rpng_unified_pool.yaml"
        trt_dir="$asset_root/pretrained_models/generated_rpng_344x616"
        family_args=(--undistort --IMU_poseinit_after 20 --buffer 700)
        ;;
    *) echo "unsupported matched-time scene: $family/$scene" >&2; exit 2 ;;
esac
config_file=${MAPPING_CONFIG_OVERRIDE:-$config_file}

case "$dense_gradient_scope" in
    full|appearance|appearance_opacity) ;;
    *) echo "unsupported MAPPING_DENSE_GRADIENT_SCOPE: $dense_gradient_scope" >&2; exit 2 ;;
esac
frontend_trace_args=()
case "$frontend_trace_mode" in
    off) ;;
    record|replay)
        if [ -z "$frontend_trace_dir" ]; then
            echo "MAPPING_FRONTEND_TRACE_DIR is required for trace mode" >&2
            exit 2
        fi
        frontend_trace_args+=(--mapping_dense_prefrontier)
        if [ "$frontend_trace_mode" = record ]; then
            frontend_trace_args+=(--mapping_frontend_trace_record_dir "$frontend_trace_dir")
        else
            frontend_trace_args+=(--mapping_frontend_trace_replay_dir "$frontend_trace_dir")
        fi
        ;;
    *) echo "unsupported MAPPING_FRONTEND_TRACE_MODE: $frontend_trace_mode" >&2; exit 2 ;;
esac
topology_trace_args=()
case "$topology_trace_mode" in
    off) ;;
    record|replay)
        if [ "$frontend_trace_mode" != replay ] || [ -z "$topology_trace_dir" ]; then
            echo "topology trace mode requires frontend replay and MAPPING_TOPOLOGY_TRACE_DIR" >&2
            exit 2
        fi
        if [ "$topology_trace_mode" = record ]; then
            topology_trace_args+=(--mapping_topology_trace_record_dir "$topology_trace_dir")
        else
            topology_trace_args+=(--mapping_topology_trace_replay_dir "$topology_trace_dir")
        fi
        ;;
    *) echo "unsupported MAPPING_TOPOLOGY_TRACE_MODE: $topology_trace_mode" >&2; exit 2 ;;
esac
if [ "$trace_packet_driven_topology" = 1 ]; then
    topology_trace_args+=(--mapping_trace_packet_driven_topology)
elif [ "$trace_packet_driven_topology" != 0 ]; then
    echo "MAPPING_TRACE_PACKET_DRIVEN_TOPOLOGY must be 0 or 1" >&2
    exit 2
fi

pose_source_args=(--background_dense_pose_source "$mapping_pose_source")
case "$mapping_pose_source" in
    interpolate|trajectory_filler|imu_rotation_bridge|imu_pose_bridge) ;;
    gt_relative_bridge|gt_absolute)
        if [ -z "$mapping_gt_trajectory" ] || [ ! -f "$mapping_gt_trajectory" ]; then
            echo "GT mapping pose source requires an existing MAPPING_GT_TRAJECTORY" >&2
            exit 2
        fi
        if [[ "$mapping_gt_camera_frame" != camera && "$mapping_gt_camera_frame" != utmm_robot ]]; then
            echo "MAPPING_GT_CAMERA_FRAME must be camera or utmm_robot" >&2
            exit 2
        fi
        pose_source_args+=(
            --background_dense_gt_trajectory "$mapping_gt_trajectory"
            --background_dense_gt_camera_frame "$mapping_gt_camera_frame"
        )
        ;;
    *) echo "unsupported MAPPING_DENSE_POSE_SOURCE: $mapping_pose_source" >&2; exit 2 ;;
esac

matched_scale=$(python "$script_dir/build_budget_manifest.py" \
    --lookup "$family" "$scene" --field matched_replay_scale)
matched_elapsed=$(python "$script_dir/build_budget_manifest.py" \
    --lookup "$family" "$scene" --field vanilla_mapping_elapsed_s)
replay_scale=${MAPPING_REPLAY_SCALE_OVERRIDE:-$matched_scale}
budget_source=vanilla_map_done
if [ -n "${MAPPING_REPLAY_SCALE_OVERRIDE:-}" ]; then
    budget_source=fixed_replay_scale_override
fi

required=(
    "$image_dir" "$imu_file" "$calibration" "$config_file"
    "$conda_env/bin/python" "$trt_dir/droidnet_fnet_fp16.engine"
    "$trt_dir/update_module_partial_fp16.engine"
    "$trt_dir/update_module_partial_pgba_fp16.engine"
)
for path in "${required[@]}"; do
    if [ ! -e "$path" ]; then echo "missing required input: $path" >&2; exit 2; fi
done
if [ -d "$output_dir" ] && [ -n "$(find "$output_dir" -mindepth 1 -print -quit)" ]; then
    echo "non-empty output exists; refusing to overwrite: $output_dir" >&2
    exit 2
fi
gpu_jobs=$(nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv,noheader || true)
if [ -n "$gpu_jobs" ]; then
    echo "GPU already has compute work; leaving it untouched:" >&2
    echo "$gpu_jobs" >&2
    exit 3
fi

mkdir -p "$output_dir"
exec > >(tee "$output_dir/run.log") 2>&1
export VIGS_DEPTH_ANCHOR_LOG="$output_dir/points3D.txt"
export VIGS_DEPTH_ANCHOR_CAM_LOG="$output_dir/images.txt"
export VIGS_TIMING_LOG="$output_dir/timing.csv"
export VIGS_PIPELINE_TELEMETRY=1
export VIGS_SENSOR_EOS_ZERO_TAIL=1
export VIGS_SENSOR_EOS_MARGIN_SECONDS=0.05
unset VIGS_DISABLE_FNET_TRT VIGS_DISABLE_UPDATE_TRT
export VIGS_FNET_TRT_ENGINE="$trt_dir/droidnet_fnet_fp16.engine"
export VIGS_UPDATE_TRT_ENGINE="$trt_dir/update_module_partial_fp16.engine"
export VIGS_UPDATE_PGBA_TRT_ENGINE="$trt_dir/update_module_partial_pgba_fp16.engine"
export PYTHONPATH="$rasterizer_root${PYTHONPATH:+:$PYTHONPATH}"
export PYTHONUNBUFFERED=1

conda_root=${conda_env%%/envs/*}
source "$conda_root/etc/profile.d/conda.sh"
conda activate "$conda_env"

code_commit=$(git -C "$repo_root" rev-parse HEAD)
echo "MATCHED_TIME_CONTRACT family=$family scene=$scene selector=$selector admission=$admission_tag required_opportunities=$required_opportunities birth_downsample_multiplier=$birth_downsample_multiplier prune_opacity_multiplier=$prune_opacity_multiplier mapping_pose_source=$mapping_pose_source replay_scale=$replay_scale matched_scale_reference=$matched_scale matched_elapsed_s_reference=$matched_elapsed budget_source=$budget_source replay=uniform_scaled zero_tail=1 mapping_loop=one pool=kf+dense physical_batch=1 tracking_stride=1 kf_action=rgbd_normal_full_topology dense_action=rgb_${dense_gradient_scope} mapping_steps_per_packet=$mapping_steps_per_packet frontend_trace_mode=$frontend_trace_mode topology_trace_mode=$topology_trace_mode phase_cutoff=0 background_polish=0 code_commit=$code_commit seed=$mapping_seed output=$output_dir"
nvidia-smi --query-gpu=name,memory.used,memory.total --format=csv,noheader

cd "$asset_root"
exec /usr/bin/time -v python "$repo_root/demo.py" \
    --imagedir "$image_dir" \
    --imufile "$imu_file" \
    --calib "$calibration" \
    --config "$config_file" \
    --output "$output_dir" \
    --gsmapping --pure_online --realtime_replay \
    --replay_time_scale "$replay_scale" \
    --eval_online_final --eval_metrics_only \
    --mapping_exclude_fixed_eval_views --report_online_mapping_summary \
    --frontend_window 25 --frontend_radius 2 --motion_filter_thresh 2.4 \
    --frontend_iters1 4 --frontend_iters2 2 \
    --enable_isotropic_loss --mapping_after_imu_init \
    --mapping_birth_downsample_multiplier "$birth_downsample_multiplier" \
    --mapping_prune_opacity_multiplier "$prune_opacity_multiplier" \
    --tracking_stride 1 --seed "$mapping_seed" \
    --idle_map_rr --mapping_work_conserving --mapping_unified_pool \
    --mapping_replay_deadline_guard --gs_dedicated_stream \
    --mapping_replay_overlap_tracking --mapping_replay_pack_tracking_slack \
    --mapping_replay_iters 1 --mapping_replay_batch_size 1 \
    --mapping_idle_replay_batch_size 1 \
    --mapping_replay_dense_gradient_scope "$dense_gradient_scope" \
    --mapping_replay_seed "$mapping_seed" --mapping_idle_guard_ms 0 \
    --mapping_idle_fast_loop \
    --mapping_dense_preinit_interpolate \
    "${family_args[@]}" \
    "${pose_source_args[@]}" \
    "${dense_membership_args[@]}" \
    "${frontend_trace_args[@]}" \
    "${topology_trace_args[@]}" \
    "${admission_args[@]}" \
    "${selector_args[@]}" \
    "${packet_budget_args[@]}"
