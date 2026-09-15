#!/usr/bin/env bash
# Resume-safe first strict pair. Completed outputs are preserved and skipped.
set -euo pipefail

script_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
lab_root=/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab
root="$lab_root/results/ERCB_ablation/exp03-A_strict_e2e/utmm/fast-straight/1p5x"

for selector in rr ercb_relative_floor; do
    output="$root/${selector}_workcredit_r4_s0"
    result="$output/psnr/online_final/final_result.json"
    audit="$output/sensor_eos_audit.json"
    if [ -f "$result" ] && [ -f "$audit" ]; then
        echo "SKIP_COMPLETE $selector"
        continue
    fi
    "$script_dir/run_one.sh" utmm fast-straight "$selector" 1.5 0 "$output"
done
