#!/usr/bin/env bash
# Resume-safe serial queue for all available Aria, UTMM, and RPNG scenes.
set -euo pipefail

script_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
lab_root=/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab
results_root="$lab_root/results/benchmarks/benchmark_vanila/5070ti_1.5x_strict"

jobs=(
    "aria aria1253"
    "aria aria1253rot"
    "aria aria301_12F"
    "aria aria301_305"
    "utmm ego-centric-1"
    "utmm ego-centric-2"
    "utmm ego-drive"
    "utmm fast-straight"
    "utmm slow-straight-1"
    "utmm slow-straight-2"
    "utmm square-1"
    "utmm square-2"
    "rpng table_01"
    "rpng table_02"
    "rpng table_03"
    "rpng table_04"
    "rpng table_05"
    "rpng table_06"
    "rpng table_07"
    "rpng table_08"
)

failures=0
for job in "${jobs[@]}"; do
    read -r family scene <<< "$job"
    output="$results_root/$family/$scene/origin22ffe24_pure_online_strict15x"
    if [ -f "$output/psnr/after_opt/final_result.json" ] && \
       [ -f "$output/sensor_eos_audit.json" ]; then
        echo "SKIP complete $family/$scene"
        continue
    fi
    echo "RUN $family/$scene"
    if bash "$script_dir/run_one.sh" "$family" "$scene" "$output"; then
        echo "PASS process $family/$scene"
    else
        status=$?
        failures=$((failures + 1))
        echo "FAIL process $family/$scene exit=$status (preserved; continuing queue)"
    fi
    python "$script_dir/collect_metrics.py"
done

python "$script_dir/collect_metrics.py"
echo "QUEUE_DONE failures=$failures total=${#jobs[@]}"
exit "$failures"
