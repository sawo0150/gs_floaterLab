#!/usr/bin/env bash
set -euo pipefail

script_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
lab_root=/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab
root="$lab_root/results/ERCB_ablation/exp03-F_keyframe_role"

for spec in "rpng table_07 3" "utmm square-1 15"; do
    read -r family scene quota <<< "$spec"
    for selector in rr_role_stratified ercb_relative_floor_keyframe_stratified; do
        short=rr
        if [[ "$selector" == ercb_* ]]; then short=ercb_keyframe; fi
        output="$root/$family/$scene/q${quota}/${short}_s0"
        result="$output/psnr/online_final/final_result.json"
        audit="$output/sensor_eos_audit.json"
        if [ -f "$result" ] && [ -f "$audit" ]; then
            echo "SKIP_COMPLETE family=$family scene=$scene q=$quota selector=$selector"
            continue
        fi
        "$script_dir/run_one.sh" \
            "$family" "$scene" "$selector" "$quota" 0 "$output"
    done
done
