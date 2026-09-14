#!/usr/bin/env bash
# exp86-D: isolate half-strength native opacity pruning under the adopted r4 contract.
set -euo pipefail

script_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
lab_root=/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab
repo_root=/home/wosas/Desktop/26-1_RPM/gsProjects/VIGS-SLAM-exp86-c-birth2x
asset_root=/home/wosas/Desktop/26-1_RPM/gsProjects/VIGS-SLAM-main-integration-20260828
results_root="$lab_root/results/benchmarks/benchmark_custom/5070ti_vanilla_matched_time/utmm"

export VIGS_REPO_ROOT="$repo_root"
export VIGS_ASSET_ROOT="$asset_root"
export VIGS_RASTERIZER_ROOT="$asset_root/thirdparty/diff-gaussian-rasterization"
export MATCHED_ADMISSION=work_credit
export MATCHED_REQUIRED_OPPORTUNITIES=4
export MAPPING_BIRTH_DOWNSAMPLE_MULTIPLIER=1.0
export MAPPING_PRUNE_OPACITY_MULTIPLIER=0.5

for scene in fast-straight ego-centric-1; do
    for selector in rr ercb_view_count_b002_k128; do
        output="$results_root/$scene/${selector}_unified_pool_workcredit_cycle_r4_pruneopacityhalf_seed0"
        echo "EXP86_D_RUN scene=$scene selector=$selector output=$output"
        "$script_dir/run_one.sh" utmm "$scene" "$selector" "$output"
    done
done
