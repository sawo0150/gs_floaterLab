#!/usr/bin/env bash
# Resume-safe RPNG table_01 strict 1.5x fixed-arrival pair.
set -euo pipefail

lab_root=/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab
runner="$lab_root/context/experiments/ERCB_ablation/exp03-B_strict_fixed_arrival/run_one.sh"
root="$lab_root/results/ERCB_ablation/exp03-C_strict_rpng_transfer/rpng/table_01/1p5x"

for selector in rr ercb_relative_floor; do
    output="$root/${selector}_arrival_s0"
    result="$output/psnr/online_final/final_result.json"
    audit="$output/sensor_eos_audit.json"
    if [ -f "$result" ] && [ -f "$audit" ]; then
        echo "SKIP_COMPLETE $selector"
        continue
    fi
    "$runner" rpng table_01 "$selector" 1.5 0 "$output"
done
