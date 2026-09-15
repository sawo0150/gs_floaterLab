#!/usr/bin/env bash
# Resume-safe UTMM ego-centric-1 strict 1.5x fixed-arrival pair.
set -euo pipefail

lab_root=/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab
runner="$lab_root/context/experiments/ERCB_ablation/exp03-B_strict_fixed_arrival/run_one.sh"
root="$lab_root/results/ERCB_ablation/exp03-D_strict_utmm_transfer/utmm/ego-centric-1/1p5x"

for selector in rr ercb_relative_floor; do
    output="$root/${selector}_arrival_s0"
    result="$output/psnr/online_final/final_result.json"
    audit="$output/sensor_eos_audit.json"
    if [ -f "$result" ] && [ -f "$audit" ]; then
        echo "SKIP_COMPLETE $selector"
        continue
    fi
    "$runner" utmm ego-centric-1 "$selector" 1.5 0 "$output"
done
