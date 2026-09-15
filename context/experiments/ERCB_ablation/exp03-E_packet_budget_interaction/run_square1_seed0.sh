#!/usr/bin/env bash
# Resume-safe role-matched UTMM packet-budget panel.
set -euo pipefail

script_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
lab_root=/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab
root="$lab_root/results/ERCB_ablation/exp03-E_packet_budget_interaction/utmm/square-1"

for quota in 5 15; do
    seeds=(0)
    if [ "$quota" -eq 15 ]; then seeds=(0 1 2); fi
    for seed in "${seeds[@]}"; do
        for selector in rr_role_stratified ercb_relative_floor_role_stratified; do
            short=${selector%%_role_stratified}
            if [ "$short" = ercb_relative_floor ]; then short=ercb; fi
            output="$root/q${quota}_role_stratified/${short}_s${seed}"
            result="$output/psnr/online_final/final_result.json"
            audit="$output/sensor_eos_audit.json"
            if [ -f "$result" ] && [ -f "$audit" ]; then
                echo "SKIP_COMPLETE q=$quota seed=$seed selector=$selector"
                continue
            fi
            "$script_dir/run_one.sh" \
                utmm square-1 "$selector" "$quota" "$seed" "$output"
        done
    done
done
