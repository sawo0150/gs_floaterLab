#!/usr/bin/env bash
# Replay and evaluate one exp78 Lane-B arm from the same frozen tracker archive.
set -euo pipefail

if [ "$#" -ne 6 ]; then
    echo "usage: $0 <vanilla|vanilla_d1_render_matched|custom_vanilla|b2_rr|b2_birth|b2_birth_uniform2|b2_birth_rr|b2_birth_rr_consolidation|b2_birth_rr_consolidation_fullcap|b2_birth_rr_consolidation_rows|b2_birth_rr_consolidation_dedicated|d1_fixed_state_rr_imu|d1_fixed_state_rr_imu_minprune|d1_fixed_frontier_rr_imu|b3_core> <rpng|utmm> <sequence> <seed> <work|1.0|1.5> <output-dir>" >&2
    exit 2
fi

workspace_root='/home/intern/gs_floaterLab'
official_root='/home/intern/VIGS-SLAM-official-exp78'
custom_root='/home/intern/VIGS-SLAM-main-integration-20260828'
python_env='/home/colin/miniconda3/envs/vigs-slam-5090'
official_commit='22ffe24c6df81d0bf63bd20057565c00c51d2996'
custom_commit='2a3eeeb5b83743c642bbd7e5278817a4c76228ee'

method=$1
dataset=$2
sequence=$3
seed=$4
time_scale=$5
service_mode=$time_scale
replay_time_scale=$time_scale
output_dir=$(realpath -m "$6")

# The historical D1 provenance arms used a topology-freeze API whose trigger
# depended on event cadence.  It is not an admissible active recipe: current
# experiments must keep ordinary frontier topology or the observation-based
# unknown-horizon state machine.  Preserve old result directories, but refuse
# to create new runs with the deprecated arms.
case "$method" in
    b3_core_topology|b3_precarve|gsslam)
        echo "$method is provenance-only and disabled: topology-freeze phase controls are forbidden" >&2
        exit 2
        ;;
esac
common_deadline_reserve_ms=${EXP78B_COMMON_DEADLINE_RESERVE_MS:-50}
legacy_d1_reserve_split=${EXP78B_LEGACY_D1_RESERVE_SPLIT:-0}
d1_reference_runtime=''
archive="$workspace_root/results/experiments/exp78/b_strict_fair_comparison/frozen_tracker/official_22ffe24_trt/$dataset/$sequence/seed$seed"
archive_validation_cache="$archive/validation.json"
manifest="$workspace_root/context/experiments/exp78/b_strict_fair_comparison/manifests/${dataset}_${sequence}.json"
validator="$workspace_root/benchmarks/online_gs/validate_exp78b_frozen_tracker.py"
archive_reader="$workspace_root/benchmarks/online_gs/exp78b_frozen_archive.py"
timeline_scheduler="$workspace_root/benchmarks/online_gs/exp78b_timeline_scheduler.py"
admission_scheduler="$workspace_root/benchmarks/online_gs/exp78b_compute_paced_admission.py"
evaluator="$workspace_root/benchmarks/online_gs/exp78_evaluate_vigs_ply.py"

if ! [[ "$seed" =~ ^[0-9]+$ ]]; then
    echo "seed must be a non-negative integer" >&2
    exit 2
fi
if ! [[ "$common_deadline_reserve_ms" =~ ^[0-9]+([.][0-9]+)?$ ]]; then
    echo "EXP78B_COMMON_DEADLINE_RESERVE_MS must be non-negative" >&2
    exit 2
fi
case "$legacy_d1_reserve_split" in
    0|1) ;;
    *) echo "EXP78B_LEGACY_D1_RESERVE_SPLIT must be 0 or 1" >&2; exit 2 ;;
esac
case "$time_scale" in
    work) replay_time_scale=unbounded ;;
    1.0|1.5) ;;
    *) echo "service mode must be work, 1.0 or 1.5" >&2; exit 2 ;;
esac
case "$method" in
    vanilla)
        replay="$workspace_root/benchmarks/online_gs/exp78b_replay_vanilla_mapping.py"
        replay_sha='7966c28409f20db051f9c4ba824d8ce1f5853929e7846f9f45cf92e547b278c2'
        config="$official_root/config/${dataset}.yaml"
        deadline_reserve_ms=$common_deadline_reserve_ms
        if [ "$legacy_d1_reserve_split" = 1 ]; then
            deadline_reserve_ms=50
        fi
        mapping_pythonpath="$official_root/vigs:$official_root/thirdparty/diff-gaussian-rasterization"
        extra_replay_args=()
        ;;
    vanilla_d1_render_matched)
        if [ "$service_mode" != work ]; then
            echo "vanilla_d1_render_matched is a B render-work arm" >&2
            exit 2
        fi
        if [ -z "${EXP78B_D1_REFERENCE_RUNTIME:-}" ]; then
            echo "EXP78B_D1_REFERENCE_RUNTIME is required" >&2
            exit 2
        fi
        d1_reference_runtime=$(realpath "$EXP78B_D1_REFERENCE_RUNTIME")
        replay="$workspace_root/benchmarks/online_gs/exp78b_replay_vanilla_mapping.py"
        replay_sha='7966c28409f20db051f9c4ba824d8ce1f5853929e7846f9f45cf92e547b278c2'
        config="$official_root/config/${dataset}.yaml"
        deadline_reserve_ms=$common_deadline_reserve_ms
        mapping_pythonpath="$official_root/vigs:$official_root/thirdparty/diff-gaussian-rasterization"
        extra_replay_args=(
            --reference-service-runtime "$d1_reference_runtime"
        )
        ;;
    custom_vanilla)
        replay="$workspace_root/benchmarks/online_gs/exp78b_replay_gsslam_mapping.py"
        replay_sha='a3f2771e1001a14de78380db641d76abd3eec0d0205402e5ef65cdf464c3bda3'
        config="$official_root/config/${dataset}.yaml"
        deadline_reserve_ms=$common_deadline_reserve_ms
        extra_replay_args=(
            --profile frontier_only
            --density-policy disabled
            --official-frontier-parity
        )
        mapping_pythonpath="$custom_root/thirdparty/diff-gaussian-rasterization"
        ;;
    b2_rr)
        if [ "$service_mode" != work ]; then
            echo "b2_rr is a fixed-work-only arm" >&2
            exit 2
        fi
        replay="$workspace_root/benchmarks/online_gs/exp78b_replay_gsslam_mapping.py"
        replay_sha='a3f2771e1001a14de78380db641d76abd3eec0d0205402e5ef65cdf464c3bda3'
        config="$official_root/config/${dataset}.yaml"
        deadline_reserve_ms=$common_deadline_reserve_ms
        extra_replay_args=(
            --profile dense_rr
            --density-policy disabled
            --official-frontier-parity
            --fixed-iteration-projected-dense-selector rr
            --fixed-iteration-projected-dense-iters 1
            --fixed-iteration-projected-dense-batch-size 4
            --fixed-iteration-projected-dense-norm-ratio 0.25
            --fixed-iteration-projected-dense-geometry-norm-ratio 0
        )
        mapping_pythonpath="$custom_root/thirdparty/diff-gaussian-rasterization"
        ;;
    b2_birth)
        if [ "$service_mode" != work ]; then
            echo "b2_birth is a fixed-iteration-only arm" >&2
            exit 2
        fi
        replay="$workspace_root/benchmarks/online_gs/exp78b_replay_gsslam_mapping.py"
        replay_sha='a3f2771e1001a14de78380db641d76abd3eec0d0205402e5ef65cdf464c3bda3'
        config="$official_root/config/${dataset}.yaml"
        deadline_reserve_ms=$common_deadline_reserve_ms
        extra_replay_args=(
            --profile frontier_only
            --density-policy online_rank
            --online-density-mean-multiplier 2.5
            --online-density-span 2.0
            --official-frontier-parity
        )
        mapping_pythonpath="$custom_root/thirdparty/diff-gaussian-rasterization"
        ;;
    b2_birth_uniform2)
        if [ "$service_mode" != work ]; then
            echo "b2_birth_uniform2 is a fixed-iteration-only arm" >&2
            exit 2
        fi
        replay="$workspace_root/benchmarks/online_gs/exp78b_replay_gsslam_mapping.py"
        replay_sha='a3f2771e1001a14de78380db641d76abd3eec0d0205402e5ef65cdf464c3bda3'
        config="$official_root/config/${dataset}.yaml"
        deadline_reserve_ms=$common_deadline_reserve_ms
        extra_replay_args=(
            --profile frontier_only
            --density-policy online_rank
            --online-density-mean-multiplier 2.0
            --online-density-span 0.0
            --official-frontier-parity
        )
        mapping_pythonpath="$custom_root/thirdparty/diff-gaussian-rasterization"
        ;;
    b2_birth_rr)
        if [ "$service_mode" != work ]; then
            echo "b2_birth_rr is a fixed-iteration-only arm" >&2
            exit 2
        fi
        replay="$workspace_root/benchmarks/online_gs/exp78b_replay_gsslam_mapping.py"
        replay_sha='a3f2771e1001a14de78380db641d76abd3eec0d0205402e5ef65cdf464c3bda3'
        config="$official_root/config/${dataset}.yaml"
        deadline_reserve_ms=$common_deadline_reserve_ms
        extra_replay_args=(
            --profile dense_rr
            --density-policy online_rank
            --online-density-mean-multiplier 2.5
            --online-density-span 2.0
            --official-frontier-parity
            --fixed-iteration-projected-dense-selector rr
            --fixed-iteration-projected-dense-iters 1
            --fixed-iteration-projected-dense-batch-size 4
            --fixed-iteration-projected-dense-norm-ratio 0.25
            --fixed-iteration-projected-dense-geometry-norm-ratio 0
        )
        mapping_pythonpath="$custom_root/thirdparty/diff-gaussian-rasterization"
        ;;
    b2_birth_rr_consolidation)
        if [ "$service_mode" != work ]; then
            echo "b2_birth_rr_consolidation is a fixed-iteration-only arm" >&2
            exit 2
        fi
        replay="$workspace_root/benchmarks/online_gs/exp78b_replay_gsslam_mapping.py"
        replay_sha='a3f2771e1001a14de78380db641d76abd3eec0d0205402e5ef65cdf464c3bda3'
        config="$official_root/config/${dataset}.yaml"
        deadline_reserve_ms=$common_deadline_reserve_ms
        extra_replay_args=(
            --profile dense_rr
            --density-policy online_rank
            --online-density-mean-multiplier 2.5
            --online-density-span 2.0
            --official-frontier-parity
            --fixed-iteration-projected-dense-selector rr
            --fixed-iteration-projected-dense-iters 1
            --fixed-iteration-projected-dense-batch-size 4
            --fixed-iteration-projected-dense-norm-ratio 0.25
            --fixed-iteration-projected-dense-geometry-norm-ratio 0
            --observation-conditioned-newborn-consolidation
        )
        mapping_pythonpath="$custom_root/thirdparty/diff-gaussian-rasterization"
        ;;
    b2_birth_rr_consolidation_fullcap)
        if [ "$service_mode" != work ]; then
            echo "b2_birth_rr_consolidation_fullcap is a fixed-iteration-only arm" >&2
            exit 2
        fi
        replay="$workspace_root/benchmarks/online_gs/exp78b_replay_gsslam_mapping.py"
        replay_sha='a3f2771e1001a14de78380db641d76abd3eec0d0205402e5ef65cdf464c3bda3'
        config="$official_root/config/${dataset}.yaml"
        deadline_reserve_ms=$common_deadline_reserve_ms
        extra_replay_args=(
            --profile dense_rr
            --density-policy online_rank
            --online-density-mean-multiplier 2.5
            --online-density-span 2.0
            --official-frontier-parity
            --fixed-iteration-projected-dense-selector rr
            --fixed-iteration-projected-dense-iters 1
            --fixed-iteration-projected-dense-batch-size 4
            --fixed-iteration-projected-dense-norm-ratio 1.0
            --fixed-iteration-projected-dense-geometry-norm-ratio 0
            --observation-conditioned-newborn-consolidation
        )
        mapping_pythonpath="$custom_root/thirdparty/diff-gaussian-rasterization"
        ;;
    b2_birth_rr_consolidation_rows)
        if [ "$service_mode" != work ]; then
            echo "b2_birth_rr_consolidation_rows is a fixed-iteration-only arm" >&2
            exit 2
        fi
        replay="$workspace_root/benchmarks/online_gs/exp78b_replay_gsslam_mapping.py"
        replay_sha='a3f2771e1001a14de78380db641d76abd3eec0d0205402e5ef65cdf464c3bda3'
        config="$official_root/config/${dataset}.yaml"
        deadline_reserve_ms=$common_deadline_reserve_ms
        extra_replay_args=(
            --profile dense_rr
            --density-policy online_rank
            --online-density-mean-multiplier 2.5
            --online-density-span 2.0
            --official-frontier-parity
            --fixed-iteration-projected-dense-selector rr
            --fixed-iteration-projected-dense-iters 1
            --fixed-iteration-projected-dense-batch-size 4
            --fixed-iteration-projected-dense-norm-ratio 1.0
            --fixed-iteration-projected-dense-geometry-norm-ratio 0
            --observation-conditioned-newborn-consolidation
        )
        mapping_pythonpath="$custom_root/thirdparty/diff-gaussian-rasterization"
        ;;
    b2_birth_rr_consolidation_dedicated)
        if [ "$service_mode" != work ]; then
            echo "b2_birth_rr_consolidation_dedicated is a fixed-iteration-only arm" >&2
            exit 2
        fi
        replay="$workspace_root/benchmarks/online_gs/exp78b_replay_gsslam_mapping.py"
        replay_sha='a3f2771e1001a14de78380db641d76abd3eec0d0205402e5ef65cdf464c3bda3'
        config="$official_root/config/${dataset}.yaml"
        deadline_reserve_ms=$common_deadline_reserve_ms
        extra_replay_args=(
            --profile dense_rr
            --density-policy online_rank
            --online-density-mean-multiplier 2.5
            --online-density-span 2.0
            --official-frontier-parity
            --fixed-iteration-dedicated-dense-selector rr
            --fixed-iteration-dedicated-dense-iters 3
            --fixed-iteration-dedicated-dense-batch-size 1
            --fixed-iteration-dedicated-dense-scope appearance
            --observation-conditioned-newborn-consolidation
        )
        mapping_pythonpath="$custom_root/thirdparty/diff-gaussian-rasterization"
        ;;
    d1_fixed_state_rr_imu|d1_fixed_state_rr_imu_minprune)
        if [ "$service_mode" != work ]; then
            echo "$method is a fixed-iteration-only arm" >&2
            exit 2
        fi
        replay="$workspace_root/benchmarks/online_gs/exp78b_replay_gsslam_mapping.py"
        replay_sha='a3f2771e1001a14de78380db641d76abd3eec0d0205402e5ef65cdf464c3bda3'
        config="$official_root/config/${dataset}.yaml"
        deadline_reserve_ms=$common_deadline_reserve_ms
        extra_replay_args=(
            --profile d1_fixed_state_rr_imu
            --density-policy online_rank
            --online-density-mean-multiplier 2.5
            --online-density-span 2.0
            --official-frontier-parity
            --dense-replay-scope appearance
        )
        if [ "$method" = d1_fixed_state_rr_imu_minprune ]; then
            extra_replay_args+=(--relative-capacity-prune-closure)
        fi
        mapping_pythonpath="$custom_root/thirdparty/diff-gaussian-rasterization"
        ;;
    d1_fixed_frontier_rr_imu)
        if [ "$service_mode" != work ]; then
            echo "$method is a fixed-iteration-only arm" >&2
            exit 2
        fi
        replay="$workspace_root/benchmarks/online_gs/exp78b_replay_gsslam_mapping.py"
        replay_sha='a3f2771e1001a14de78380db641d76abd3eec0d0205402e5ef65cdf464c3bda3'
        config="$official_root/config/${dataset}.yaml"
        deadline_reserve_ms=$common_deadline_reserve_ms
        extra_replay_args=(
            --profile d1_fixed_state_rr_imu
            --density-policy online_rank
            --online-density-mean-multiplier 2.5
            --online-density-span 2.0
            --official-frontier-parity
            --dense-replay-scope appearance
            --fixed-iteration-projected-dense-selector rr
            --fixed-iteration-projected-dense-iters 3
            --fixed-iteration-projected-dense-batch-size 1
            --fixed-iteration-projected-dense-norm-ratio 1.0
            --fixed-iteration-projected-dense-geometry-norm-ratio 0
            --d1-preserve-full-frontier
        )
        mapping_pythonpath="$custom_root/thirdparty/diff-gaussian-rasterization"
        ;;
    b3_core)
        if [ "$service_mode" != work ]; then
            echo "$method is a fixed-iteration-only arm" >&2
            exit 2
        fi
        replay="$workspace_root/benchmarks/online_gs/exp78b_replay_gsslam_mapping.py"
        replay_sha='a3f2771e1001a14de78380db641d76abd3eec0d0205402e5ef65cdf464c3bda3'
        config="$official_root/config/${dataset}.yaml"
        deadline_reserve_ms=$common_deadline_reserve_ms
        extra_replay_args=(
            --profile dense_rr_imu
            --density-policy disabled
            --official-frontier-parity
            --fixed-iteration-projected-dense-selector ercb
            --fixed-iteration-projected-dense-iters 1
            --fixed-iteration-projected-dense-batch-size 4
            --fixed-iteration-projected-dense-norm-ratio 0.25
            --fixed-iteration-projected-dense-geometry-norm-ratio 0
            --compute-paced-dense-admission
            --compute-paced-dense-token-cost 22
        )
        mapping_pythonpath="$custom_root/thirdparty/diff-gaussian-rasterization"
        ;;
    b3_precarve)
        if [ "$service_mode" != work ]; then
            echo "b3_precarve is a fixed-iteration-only arm" >&2
            exit 2
        fi
        replay="$workspace_root/benchmarks/online_gs/exp78b_replay_gsslam_mapping.py"
        replay_sha='a3f2771e1001a14de78380db641d76abd3eec0d0205402e5ef65cdf464c3bda3'
        config="$official_root/config/${dataset}.yaml"
        deadline_reserve_ms=$common_deadline_reserve_ms
        extra_replay_args=(
            --profile dense_rr_imu
            --density-policy online_rank
            --online-density-mean-multiplier 2.5
            --online-density-span 2.0
            --auto-topology-freeze
            --official-frontier-parity
            --fixed-iteration-projected-dense-selector ercb
            --fixed-iteration-projected-dense-iters 1
            --fixed-iteration-projected-dense-batch-size 4
            --fixed-iteration-projected-dense-norm-ratio 0.25
            --fixed-iteration-projected-dense-geometry-norm-ratio 0
            --compute-paced-dense-admission
            --compute-paced-dense-token-cost 22
        )
        mapping_pythonpath="$custom_root/thirdparty/diff-gaussian-rasterization"
        ;;
    gsslam)
        replay="$workspace_root/benchmarks/online_gs/exp78b_replay_gsslam_mapping.py"
        replay_sha='a3f2771e1001a14de78380db641d76abd3eec0d0205402e5ef65cdf464c3bda3'
        config="$workspace_root/benchmarks/online_gs/config/vigs_final_v7_${dataset}.yaml"
        case "$dataset" in
            rpng)
                config_sha='138fdd26a99be125fab900ba9e731d38660ee7d2dd8e5f6833496a16045ccf54'
                ;;
            utmm)
                config_sha='b68693bf2d91291af1b5bd8cbd5489427445b7ff6048722f5736d14e1a6516c4'
                ;;
            *) config_sha='' ;;
        esac
        deadline_reserve_ms=$common_deadline_reserve_ms
        if [ "$legacy_d1_reserve_split" = 1 ]; then
            deadline_reserve_ms=20
        fi
        # Frozen after the cross-dataset development sweep on RPNG table_01/06
        # and UTMM ego-drive/square-2.  The same dataset-name-independent recipe
        # is used for every validation sequence.
        extra_replay_args=(
            --profile dense_rr
            --dense-replay-scope adaptive_topology_maturation
            --density-policy online_rank
            --online-density-mean-multiplier 2.5
            --online-density-span 2.0
            --auto-topology-freeze
            --include-keyframes-in-replay
            --keyframe-replay-fraction 0.75
            --keyframe-replay-full-geometry
        )
        mapping_pythonpath="$custom_root/thirdparty/diff-gaussian-rasterization"
        ;;
    *) echo "unsupported method: $method" >&2; exit 2 ;;
esac

if [ "$service_mode" = work ]; then
    extra_replay_args+=(--mapping-after-metric-init)
    if [ "$method" = vanilla_d1_render_matched ]; then
        runner_protocol='exp78b_matched_mapping_runner_v9_d1_native_render_budget'
    else
        runner_protocol='exp78b_matched_mapping_runner_v8_fixed_iteration_no_phase_cutoffs'
    fi
else
    runner_protocol='exp78b_matched_mapping_runner_v3_common_reserve'
fi

case "$dataset" in
    rpng)
        image_dir="$workspace_root/data/benchmarks/rpng/prepared/rpngar/$sequence/rgb"
        calibration="$official_root/calib/rpngar.txt"
        ;;
    utmm)
        image_dir="$workspace_root/data/benchmarks/utmm/prepared/UTMM_Dataset/$sequence/rgb_timestamp"
        calibration="$workspace_root/data/benchmarks/utmm/prepared/UTMM_Dataset/$sequence/intrinsics_ours.txt"
        ;;
    *) echo "dataset must be rpng or utmm" >&2; exit 2 ;;
esac

if [ -e "$output_dir" ]; then
    echo "refusing to overwrite existing output: $output_dir" >&2
    exit 2
fi
for path in "$archive/archive_manifest.json" "$manifest" "$config" "$image_dir" \
            "$calibration" "$validator" "$archive_reader" "$timeline_scheduler" \
            "$admission_scheduler" "$replay" "$evaluator"; do
    if [ ! -e "$path" ]; then
        echo "missing required input: $path" >&2
        exit 2
    fi
done
if [ -n "$d1_reference_runtime" ] && [ ! -f "$d1_reference_runtime" ]; then
    echo "missing D1 reference runtime: $d1_reference_runtime" >&2
    exit 2
fi

require_sha() {
    local path=$1
    local expected=$2
    local actual
    actual=$(sha256sum "$path" | cut -d' ' -f1)
    if [ "$actual" != "$expected" ]; then
        echo "source hash mismatch for $path: $actual" >&2
        exit 2
    fi
}

if [ "$(git -C "$official_root" rev-parse HEAD)" != "$official_commit" ]; then
    echo "official source commit mismatch" >&2
    exit 2
fi
git -C "$official_root" diff --quiet --ignore-submodules=dirty
git -C "$official_root" diff --cached --quiet --ignore-submodules=dirty
if [ "$method" = gsslam ] || [ "$method" = custom_vanilla ] \
    || [ "$method" = b2_rr ] || [ "$method" = b2_birth ] \
    || [ "$method" = b2_birth_uniform2 ] \
    || [ "$method" = b2_birth_rr ] \
    || [ "$method" = b2_birth_rr_consolidation ] \
    || [ "$method" = b2_birth_rr_consolidation_fullcap ] \
    || [ "$method" = b2_birth_rr_consolidation_rows ] \
    || [ "$method" = b2_birth_rr_consolidation_dedicated ] \
    || [ "$method" = d1_fixed_state_rr_imu ] \
    || [ "$method" = d1_fixed_state_rr_imu_minprune ] \
    || [ "$method" = d1_fixed_frontier_rr_imu ] \
    || [ "$method" = b3_core ] \
    || [ "$method" = b3_core_topology ] \
    || [ "$method" = b3_precarve ]; then
    if [ "$(git -C "$custom_root" rev-parse HEAD)" != "$custom_commit" ]; then
        echo "custom source commit mismatch" >&2
        exit 2
    fi
    require_sha "$custom_root/demo.py" '7ddbda09e22d2cac428a3f685c32cf0e11eb17e06b3192d4b4bd0916207081c0'
    require_sha "$custom_root/vigs/gaussian/scene/gaussian_model.py" '7e2ab73fa07289ae478a08ffb48b6ab8c30ebc4ca7072476e70a02e2cd84d41a'
    require_sha "$custom_root/vigs/gaussian/utils/content_budget.py" '00bbb17c9acd503ac3391e7b3b8d655345c82a67a73ae5950508fb375c905aa1'
    require_sha "$custom_root/vigs/gs_backend.py" '89bc3c2c2aba4610165e0d0bb4919c699b1cc3d69079cff57566b9ce8d6c485d'
    require_sha "$custom_root/vigs/map_scheduler.py" 'ce110c1f9aa467a5dca1734089ab00f2cdfe73a30ae51fcdc796b225a6e660ac'
    require_sha "$workspace_root/benchmarks/online_gs/exp78b_newborn_consolidation.py" '80a5787281c8740a31b942cf74ee826687da364f09b2b129f8a7dc7181c87796'
    if [ "$method" = gsslam ]; then
        require_sha "$config" "$config_sha"
    fi
fi
require_sha "$replay" "$replay_sha"
require_sha "$evaluator" 'f854084b249cea724b7be65a1655088ce8906203110f52c6503b052ec3b51c3c'
require_sha "$validator" 'b2c2e050ddff373cd5e4062460fa021a141d206673a98d87fe531d3b917afccc'
require_sha "$archive_reader" '33f0b1564e30052cc3c930672a11937d3adedb12e80acf2e2d51a4d16c017b52'
require_sha "$timeline_scheduler" 'f435d11591058cbd822bc44a69e47e74f1bf434ba599371f90806d508670637e'
require_sha "$admission_scheduler" 'ad40a607b8466d6fc7744b53ecbc07b64a24311c0944c3363cd4041a8b314224'

mkdir -p "$output_dir"
export PYTHONUNBUFFERED=1
export LD_LIBRARY_PATH="$python_env/lib/python3.11/site-packages/torch/lib:$python_env/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"

{
    echo "protocol=$runner_protocol"
    echo "method=$method"
    echo "dataset=$dataset"
    echo "sequence=$sequence"
    echo "seed=$seed"
    echo "service_mode=$service_mode"
    echo "replay_time_scale=$replay_time_scale"
    if [ "$method" = vanilla_d1_render_matched ]; then
        echo 'work_contract=d1_native_total_render_budget_v2'
        echo "d1_reference_runtime=$d1_reference_runtime"
        sha256sum "$d1_reference_runtime"
    else
        echo "work_contract=$([ "$service_mode" = work ] && echo official_event_adam_v1 || echo none)"
    fi
    echo "archive=$archive"
    echo "official_commit=$official_commit"
    echo "custom_commit=$custom_commit"
    echo 'tracker_runtime=official_readme_dynamic_rtx5090_tensorrt'
    echo 'final_ba=off'
    echo 'final_color_refinement=off'
    echo 'post_eos_optimizer_updates_required=0'
    echo "deadline_reserve_ms=$deadline_reserve_ms"
    echo "legacy_d1_reserve_split=$legacy_d1_reserve_split"
    sha256sum "$replay" "$evaluator" "$validator" "$archive_reader" \
        "$timeline_scheduler" "$admission_scheduler" "$config" "$manifest" \
        "$archive/archive_manifest.json"
    nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader
} > "$output_dir/source_manifest.txt"

archive_manifest_sha=$(sha256sum "$archive/archive_manifest.json" | cut -d' ' -f1)
cached_manifest_sha=''
cached_valid='false'
if [ -f "$archive_validation_cache" ]; then
    cached_manifest_sha=$(jq -r '.archive_manifest_sha256 // ""' "$archive_validation_cache")
    cached_valid=$(jq -r '.valid // false' "$archive_validation_cache")
fi
if [ "$cached_valid" != true ] || [ "$cached_manifest_sha" != "$archive_manifest_sha" ]; then
    "$python_env/bin/python" "$validator" "$archive" \
        --output "$archive_validation_cache" \
        2>&1 | tee "$output_dir/archive_validation.log"
else
    echo "reusing validated frozen archive: $archive_validation_cache" \
        | tee "$output_dir/archive_validation.log"
fi
cp "$archive_validation_cache" "$output_dir/frozen_archive_validation.json"

PYTHONPATH="$mapping_pythonpath" "$python_env/bin/python" "$replay" \
    --archive "$archive" \
    --config "$config" \
    --output "$output_dir" \
    --seed "$seed" \
    --time-scale "$replay_time_scale" \
    --deadline-reserve-ms "$deadline_reserve_ms" \
    "${extra_replay_args[@]}" \
    2>&1 | tee "$output_dir/mapping.log"

if [ "$(jq -r '.post_eos_optimizer_updates' "$output_dir/mapping_replay_runtime.json")" != 0 ]; then
    echo "invalid zero-tail run: post-EOS optimizer work detected" >&2
    exit 3
fi

PYTHONPATH="$official_root/vigs:$official_root/thirdparty/diff-gaussian-rasterization" \
    "$python_env/bin/python" "$evaluator" \
    --run-dir "$output_dir" \
    --image-dir "$image_dir" \
    --calib "$calibration" \
    --manifest "$manifest" \
    --rgb-file-in-nanoseconds \
    --undistort \
    --mapped-uids-json "$output_dir/mapped_uids.json" \
    --result-subdir strict_fixed_manifest \
    2>&1 | tee "$output_dir/evaluation.log"
