#!/usr/bin/env bash
# Compare arrival admission against work-credit admission without changing RR/ERCB.
set -euo pipefail

script_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
lab_root=/home/wosas/Desktop/Incremental_mapping_test/gs_floaterLab
results_root="$lab_root/results/benchmarks/benchmark_custom/5070ti_vanilla_matched_time"
required_opportunities=${MATCHED_REQUIRED_OPPORTUNITIES:-4}
jobs=(
    "utmm ego-centric-1 rr"
    "utmm ego-centric-1 ercb_relative_floor"
    "rpng table_01 rr"
    "rpng table_01 ercb_relative_floor"
)

failures=0
for job in "${jobs[@]}"; do
    read -r family scene selector <<< "$job"
    output="$results_root/$family/$scene/${selector}_unified_pool_workcredit_cycle_r${required_opportunities}_seed0"
    if [ -f "$output/psnr/online_final/final_result.json" ] && \
       [ -f "$output/sensor_eos_audit.json" ]; then
        echo "SKIP complete $family/$scene/$selector workcredit_r$required_opportunities"
        continue
    fi
    echo "RUN $family/$scene/$selector workcredit_r$required_opportunities"
    if MATCHED_ADMISSION=work_credit \
       MATCHED_REQUIRED_OPPORTUNITIES="$required_opportunities" \
       bash "$script_dir/run_one.sh" "$family" "$scene" "$selector" "$output"; then
        echo "PASS process $family/$scene/$selector workcredit_r$required_opportunities"
    else
        status=$?
        failures=$((failures + 1))
        echo "FAIL process $family/$scene/$selector exit=$status (preserved; continuing)"
    fi
    python "$script_dir/collect_metrics.py"
done
python "$script_dir/collect_metrics.py"
echo "ADMISSION_PANEL_DONE failures=$failures total=${#jobs[@]}"
exit "$failures"
