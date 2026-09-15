#!/usr/bin/env bash
# Resume-safe strict 1.5x square-1 fixed-arrival 3-seed panel.
set -euo pipefail

script_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
lab_root=/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab
root="$lab_root/results/ERCB_ablation/exp03-B_strict_fixed_arrival/utmm/square-1/1p5x"

for seed in 0 1 2; do
    for selector in rr ercb_relative_floor; do
        output="$root/${selector}_arrival_s${seed}"
        result="$output/psnr/online_final/final_result.json"
        audit="$output/sensor_eos_audit.json"
        if [ -f "$result" ] && [ -f "$audit" ]; then
            echo "SKIP_COMPLETE seed=$seed selector=$selector"
            continue
        fi
        "$script_dir/run_one.sh" utmm square-1 "$selector" 1.5 "$seed" "$output"
    done
done
