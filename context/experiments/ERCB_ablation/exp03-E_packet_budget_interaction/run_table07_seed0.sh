#!/usr/bin/env bash
# Resume-safe exact-service RPNG table_07 pair.
set -euo pipefail

script_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
lab_root=/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab
root="$lab_root/results/ERCB_ablation/exp03-E_packet_budget_interaction/rpng/table_07/q3_role_stratified"

for selector in rr_role_stratified ercb_relative_floor_role_stratified; do
    short=${selector%%_role_stratified}
    if [ "$short" = ercb_relative_floor ]; then short=ercb; fi
    output="$root/${short}_s0"
    result="$output/psnr/online_final/final_result.json"
    audit="$output/sensor_eos_audit.json"
    if [ -f "$result" ] && [ -f "$audit" ]; then
        echo "SKIP_COMPLETE selector=$selector"
        continue
    fi
    "$script_dir/run_one.sh" rpng table_07 "$selector" 3 0 "$output"
done
