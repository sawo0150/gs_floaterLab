#!/usr/bin/env bash
# Resume-safe representative panel. RR and ERCB share every setting but selector.
set -euo pipefail

script_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
lab_root=/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab
results_root="$lab_root/results/benchmarks/benchmark_custom/5070ti_vanilla_matched_time"
jobs=(
    "rpng table_01 rr"
    "rpng table_01 ercb_relative_floor"
    "utmm fast-straight rr"
    "utmm fast-straight ercb_relative_floor"
    "utmm ego-drive rr"
    "utmm ego-drive ercb_relative_floor"
    "utmm ego-centric-1 rr"
    "utmm ego-centric-1 ercb_relative_floor"
    "rpng table_04 rr"
    "rpng table_04 ercb_relative_floor"
)

failures=0
for job in "${jobs[@]}"; do
    read -r family scene selector <<< "$job"
    output="$results_root/$family/$scene/${selector}_unified_pool_seed0"
    if [ -f "$output/psnr/online_final/final_result.json" ] && \
       [ -f "$output/sensor_eos_audit.json" ]; then
        echo "SKIP complete $family/$scene/$selector"
        continue
    fi
    echo "RUN $family/$scene/$selector"
    if bash "$script_dir/run_one.sh" "$family" "$scene" "$selector" "$output"; then
        echo "PASS process $family/$scene/$selector"
    else
        status=$?
        failures=$((failures + 1))
        echo "FAIL process $family/$scene/$selector exit=$status (preserved; continuing)"
    fi
    python "$script_dir/collect_metrics.py"
done
python "$script_dir/collect_metrics.py"
echo "PANEL_DONE failures=$failures total=${#jobs[@]}"
exit "$failures"
